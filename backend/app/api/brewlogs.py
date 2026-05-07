"""Brew-log endpoints — repository-backed, auth-gated."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.permissions import (
    PERM_BREWLOG_CREATE,
    PERM_BREWLOG_DELETE_OWN,
    PERM_BREWLOG_READ,
    PERM_BREWLOG_UPDATE_OWN,
)
from app.db.models import User
from app.repositories.base import NotFoundError
from app.repositories.beans import BeanRepository
from app.repositories.brewlogs import BrewlogRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.tasting_notes import TastingNoteRepository
from app.schemas.brewlog import BrewLog, BrewLogCreate, BrewLogUpdate
from app.schemas.common import BrewMethod, TasteResult
from app.services.audit import write_audit

router = APIRouter(prefix="/brewlogs", tags=["brewlogs"])


def _repo(db: AsyncSession = Depends(get_db)) -> BrewlogRepository:
    return BrewlogRepository(db)


def _bean_repo(db: AsyncSession = Depends(get_db)) -> BeanRepository:
    return BeanRepository(db)


def _equip_repo(db: AsyncSession = Depends(get_db)) -> EquipmentRepository:
    return EquipmentRepository(db)


def _tn_repo(db: AsyncSession = Depends(get_db)) -> TastingNoteRepository:
    return TastingNoteRepository(db)


async def _check_refs(
    bean_id: UUID,
    equipment_id: UUID,
    grinder_id: UUID,
    bean_repo: BeanRepository,
    equip_repo: EquipmentRepository,
) -> None:
    """Validate FK references exist — raises 422 for any missing ref."""
    try:
        await bean_repo.get(bean_id)
    except NotFoundError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"bean_id {bean_id} does not exist",
        )
    try:
        await equip_repo.get(equipment_id)
    except NotFoundError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"equipment_id {equipment_id} does not exist",
        )
    try:
        await equip_repo.get(grinder_id)
    except NotFoundError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"grinder_id {grinder_id} does not exist",
        )


def _row_to_dict(row) -> dict:
    return {c.key: getattr(row, c.key) for c in row.__table__.columns}


def _build_brewlog_schema(row, tasting_notes: list[str]) -> BrewLog:
    """Build a BrewLog Pydantic schema from an ORM row + tasting note labels.

    We use from_attributes=True so that extra ORM columns (user_id, created_at)
    are silently ignored instead of triggering the extra="forbid" validator.
    """
    class _WithNotes:
        pass

    obj = _WithNotes()
    for col in row.__table__.columns:
        setattr(obj, col.key, getattr(row, col.key))
    obj.tasting_notes = tasting_notes
    return BrewLog.model_validate(obj, from_attributes=True)


@router.get("", response_model=list[BrewLog])
async def list_brewlogs(
    method: BrewMethod | None = Query(None, description="Filter by brew method"),
    taste_result: TasteResult | None = Query(None, description="Filter by taste"),
    bean_id: UUID | None = Query(None, description="Filter by bean"),
    min_rating: int | None = Query(None, ge=1, le=5),
    max_rating: int | None = Query(None, ge=1, le=5),
    date_from: datetime | None = Query(None, description="Inclusive lower bound"),
    date_to: datetime | None = Query(None, description="Inclusive upper bound"),
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    repo: BrewlogRepository = Depends(_repo),
    tn_repo: TastingNoteRepository = Depends(_tn_repo),
) -> list[BrewLog]:
    rows = await repo.list_for_user(user.id)

    # Apply in-memory filters (simple; SQL filtering is a Phase 2 optimisation).
    if method is not None:
        rows = [r for r in rows if r.method == method.value]
    if taste_result is not None:
        rows = [r for r in rows if r.taste_result == taste_result.value]
    if bean_id is not None:
        rows = [r for r in rows if r.bean_id == bean_id]
    if min_rating is not None:
        rows = [r for r in rows if r.rating >= min_rating]
    if max_rating is not None:
        rows = [r for r in rows if r.rating <= max_rating]

    def _naive(dt: datetime) -> datetime:
        """Strip timezone so naive and tz-aware datetimes compare without TypeError."""
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

    if date_from is not None:
        from_dt = _naive(date_from)
        rows = [r for r in rows if _naive(r.date) >= from_dt]
    if date_to is not None:
        to_dt = _naive(date_to)
        rows = [r for r in rows if _naive(r.date) <= to_dt]

    # newest first
    rows.sort(key=lambda r: _naive(r.date), reverse=True)

    result = []
    for row in rows:
        notes = await tn_repo.labels_for_brewlog(row.id)
        result.append(_build_brewlog_schema(row, notes))
    return result


@router.post("", response_model=BrewLog, status_code=status.HTTP_201_CREATED)
async def create_brewlog(
    payload: BrewLogCreate,
    user: User = Depends(requires(PERM_BREWLOG_CREATE)),
    repo: BrewlogRepository = Depends(_repo),
    bean_repo: BeanRepository = Depends(_bean_repo),
    equip_repo: EquipmentRepository = Depends(_equip_repo),
    tn_repo: TastingNoteRepository = Depends(_tn_repo),
    db: AsyncSession = Depends(get_db),
) -> BrewLog:
    data = payload.model_dump()
    tasting_notes: list[str] = data.pop("tasting_notes", []) or []

    await _check_refs(data["bean_id"], data["equipment_id"], data["grinder_id"], bean_repo, equip_repo)

    row = await repo.create(user_id=user.id, **data)
    if tasting_notes:
        await tn_repo.attach_to_brewlog(row.id, tasting_notes)
    await write_audit(
        db, user_id=user.id, action="BREWLOG_CREATE", status="OK",
        resource_type="brewlog", resource_id=row.id,
    )
    await db.commit()

    return _build_brewlog_schema(row, tasting_notes)


@router.get("/{brewlog_id}", response_model=BrewLog)
async def get_brewlog(
    brewlog_id: UUID,
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    repo: BrewlogRepository = Depends(_repo),
    tn_repo: TastingNoteRepository = Depends(_tn_repo),
) -> BrewLog:
    try:
        row = await repo.get_for_user(brewlog_id, user.id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found")
    notes = await tn_repo.labels_for_brewlog(row.id)
    return _build_brewlog_schema(row, notes)


@router.patch("/{brewlog_id}", response_model=BrewLog)
async def update_brewlog(
    brewlog_id: UUID,
    payload: BrewLogUpdate,
    user: User = Depends(requires(PERM_BREWLOG_UPDATE_OWN)),
    repo: BrewlogRepository = Depends(_repo),
    bean_repo: BeanRepository = Depends(_bean_repo),
    equip_repo: EquipmentRepository = Depends(_equip_repo),
    tn_repo: TastingNoteRepository = Depends(_tn_repo),
    db: AsyncSession = Depends(get_db),
) -> BrewLog:
    try:
        current = await repo.get_for_user(brewlog_id, user.id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found")

    updates = payload.model_dump(exclude_unset=True)
    tasting_notes_update = updates.pop("tasting_notes", None)

    current_dict = _row_to_dict(current)
    merged_dict = {**current_dict, **updates}

    # Validate FK refs if any FK is being changed.
    ref_keys = {"bean_id", "equipment_id", "grinder_id"}
    if ref_keys & set(updates):
        await _check_refs(
            merged_dict["bean_id"],
            merged_dict["equipment_id"],
            merged_dict["grinder_id"],
            bean_repo,
            equip_repo,
        )

    # Re-validate merged entity with full BrewLogBase rules.
    current_notes = await tn_repo.labels_for_brewlog(current.id)

    class _MergedBrewlog:
        pass

    merged_obj = _MergedBrewlog()
    for k, v in merged_dict.items():
        setattr(merged_obj, k, v)
    merged_obj.tasting_notes = current_notes
    try:
        BrewLog.model_validate(merged_obj, from_attributes=True)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc

    if updates:
        await repo.update(brewlog_id, **updates)

    if tasting_notes_update is not None:
        await tn_repo.attach_to_brewlog(current.id, tasting_notes_update)

    await write_audit(
        db, user_id=user.id, action="BREWLOG_UPDATE", status="OK",
        resource_type="brewlog", resource_id=brewlog_id,
    )
    await db.commit()

    row = await repo.get(brewlog_id)
    final_notes = await tn_repo.labels_for_brewlog(row.id)
    return _build_brewlog_schema(row, final_notes)


@router.delete("/{brewlog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brewlog(
    brewlog_id: UUID,
    user: User = Depends(requires(PERM_BREWLOG_DELETE_OWN)),
    repo: BrewlogRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        await repo.get_for_user(brewlog_id, user.id)
        await repo.delete(brewlog_id)
    except NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found")
    await write_audit(
        db, user_id=user.id, action="BREWLOG_DELETE", status="OK",
        resource_type="brewlog", resource_id=brewlog_id,
    )
    await db.commit()
