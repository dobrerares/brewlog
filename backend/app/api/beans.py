"""Bean CRUD — repository-backed."""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import BeanTastingNote
from app.repositories.base import NotFoundError
from app.repositories.beans import BeanRepository
from app.repositories.roasters import RoasterRepository
from app.repositories.tasting_notes import TastingNoteRepository
from app.schemas.bean import Bean, BeanCreate, BeanUpdate

router = APIRouter(prefix="/beans", tags=["beans"])

_DEV_USER = UUID(os.environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))


def _repo(db: AsyncSession = Depends(get_db)) -> BeanRepository:
    return BeanRepository(db)


async def _ensure_roaster(roaster_id: UUID | None, db: AsyncSession) -> None:
    if roaster_id is None:
        return
    try:
        await RoasterRepository(db).get(roaster_id)
    except NotFoundError:
        raise HTTPException(422, f"roaster_id {roaster_id} does not exist")


async def _build_response(row, tn_repo: TastingNoteRepository) -> Bean:
    """Assemble a Bean Pydantic model from ORM row + junction-table tasting notes."""
    notes = await tn_repo.labels_for_bean(row.id)
    return Bean.model_validate(
        {
            "id": row.id,
            "name": row.name,
            "roaster_id": row.roaster_id,
            "origin_country": row.origin_country,
            "origin_region": row.origin_region,
            "process": row.process,
            "roast_level": row.roast_level,
            "variety": row.variety,
            "elevation_m": row.elevation_m,
            "tasting_notes": notes,
            "purchase_date": row.purchase_date,
            "price": row.price,
        }
    )


@router.get("", response_model=list[Bean])
async def list_beans(repo: BeanRepository = Depends(_repo)) -> list[Bean]:
    rows = await repo.list()
    tn_repo = TastingNoteRepository(repo.session)
    return [await _build_response(row, tn_repo) for row in rows]


@router.post("", response_model=Bean, status_code=201)
async def create_bean(
    payload: BeanCreate,
    db: AsyncSession = Depends(get_db),
) -> Bean:
    dev_user = UUID(os.environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))
    await _ensure_roaster(payload.roaster_id, db)

    repo = BeanRepository(db)
    data = payload.model_dump(exclude={"tasting_notes"})
    row = await repo.create(user_id=dev_user, **data)

    tn_repo = TastingNoteRepository(db)
    if payload.tasting_notes:
        await tn_repo.attach_to_bean(row.id, payload.tasting_notes)

    await repo.session.commit()
    return await _build_response(row, tn_repo)


@router.get("/{bean_id}", response_model=Bean)
async def get_bean(
    bean_id: UUID,
    repo: BeanRepository = Depends(_repo),
) -> Bean:
    try:
        row = await repo.get(bean_id)
    except NotFoundError:
        raise HTTPException(404, detail="bean not found")
    tn_repo = TastingNoteRepository(repo.session)
    return await _build_response(row, tn_repo)


@router.patch("/{bean_id}", response_model=Bean)
async def update_bean(
    bean_id: UUID,
    payload: BeanUpdate,
    db: AsyncSession = Depends(get_db),
) -> Bean:
    repo = BeanRepository(db)
    tn_repo = TastingNoteRepository(db)

    try:
        current_row = await repo.get(bean_id)
    except NotFoundError:
        raise HTTPException(404, detail="bean not found")

    updates = payload.model_dump(exclude_unset=True)

    # Pre-check roaster FK if being changed.
    if "roaster_id" in updates:
        await _ensure_roaster(updates["roaster_id"], db)

    # Separate tasting_notes from scalar updates.
    new_notes: list[str] | None = updates.pop("tasting_notes", None)

    # Fetch current tasting notes to build merged state for cross-field validation.
    current_notes = await tn_repo.labels_for_bean(bean_id)

    # Build merged dict and run full Bean validation to catch cross-field errors.
    current_dict = {
        "id": current_row.id,
        "name": current_row.name,
        "roaster_id": current_row.roaster_id,
        "origin_country": current_row.origin_country,
        "origin_region": current_row.origin_region,
        "process": current_row.process,
        "roast_level": current_row.roast_level,
        "variety": current_row.variety,
        "elevation_m": current_row.elevation_m,
        "tasting_notes": current_notes,
        "purchase_date": current_row.purchase_date,
        "price": current_row.price,
    }
    merged_dict = {**current_dict, **updates}
    if new_notes is not None:
        merged_dict["tasting_notes"] = new_notes

    try:
        Bean.model_validate(merged_dict)
    except ValidationError as exc:
        raise HTTPException(
            422,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc

    # Apply scalar field updates to ORM row.
    if updates:
        await repo.update(bean_id, **updates)

    # Replace tasting notes if provided.
    if new_notes is not None:
        await db.execute(sa_delete(BeanTastingNote).where(BeanTastingNote.bean_id == bean_id))
        await db.flush()
        if new_notes:
            await tn_repo.attach_to_bean(bean_id, new_notes)

    await repo.session.commit()

    # Re-fetch to return committed state.
    updated_row = await repo.get(bean_id)
    return await _build_response(updated_row, tn_repo)


@router.delete("/{bean_id}", status_code=204, response_class=Response)
async def delete_bean(
    bean_id: UUID,
    repo: BeanRepository = Depends(_repo),
) -> Response:
    try:
        await repo.delete(bean_id)
    except NotFoundError:
        raise HTTPException(404, detail="bean not found")
    await repo.session.commit()
    return Response(status_code=204)
