"""Equipment CRUD — repository-backed, auth-gated."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.permissions import (
    PERM_EQUIPMENT_CREATE,
    PERM_EQUIPMENT_DELETE_OWN,
    PERM_EQUIPMENT_READ,
    PERM_EQUIPMENT_UPDATE_OWN,
)
from app.db.models import User
from app.repositories.base import NotFoundError
from app.repositories.equipment import EquipmentRepository
from app.schemas.equipment import Equipment, EquipmentCreate, EquipmentUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/equipment", tags=["equipment"])


def _repo(db: AsyncSession = Depends(get_db)) -> EquipmentRepository:
    return EquipmentRepository(db)


@router.get("", response_model=list[Equipment])
async def list_equipment(
    user: User = Depends(requires(PERM_EQUIPMENT_READ)),
    repo: EquipmentRepository = Depends(_repo),
):
    rows = await repo.list_for_user(user.id)
    return [Equipment.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Equipment, status_code=201)
async def create_equipment(
    payload: EquipmentCreate,
    user: User = Depends(requires(PERM_EQUIPMENT_CREATE)),
    repo: EquipmentRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    row = await repo.create(user_id=user.id, **payload.model_dump())
    await write_audit(
        db, user_id=user.id, action="EQUIPMENT_CREATE", status="OK",
        resource_type="equipment", resource_id=row.id,
    )
    await db.commit()
    return Equipment.model_validate(row, from_attributes=True)


@router.get("/{equipment_id}", response_model=Equipment)
async def get_equipment(
    equipment_id: UUID,
    user: User = Depends(requires(PERM_EQUIPMENT_READ)),
    repo: EquipmentRepository = Depends(_repo),
):
    try:
        row = await repo.get_for_user(equipment_id, user.id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    return Equipment.model_validate(row, from_attributes=True)


@router.patch("/{equipment_id}", response_model=Equipment)
async def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    user: User = Depends(requires(PERM_EQUIPMENT_UPDATE_OWN)),
    repo: EquipmentRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        row = await repo.get_for_user(equipment_id, user.id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")

    # Merge current DB state with incoming partial update, then re-validate
    # the full Equipment schema so cross-field constraints are enforced.
    current = Equipment.model_validate(row, from_attributes=True)
    updates = payload.model_dump(exclude_unset=True)
    try:
        merged = Equipment.model_validate({**current.model_dump(), **updates})
    except ValidationError as exc:
        raise HTTPException(
            422,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc

    try:
        updated_row = await repo.update(equipment_id, **merged.model_dump(exclude={"id"}))
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await write_audit(
        db, user_id=user.id, action="EQUIPMENT_UPDATE", status="OK",
        resource_type="equipment", resource_id=updated_row.id,
    )
    await db.commit()
    return Equipment.model_validate(updated_row, from_attributes=True)


@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(
    equipment_id: UUID,
    user: User = Depends(requires(PERM_EQUIPMENT_DELETE_OWN)),
    repo: EquipmentRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        await repo.get_for_user(equipment_id, user.id)
        await repo.delete(equipment_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await write_audit(
        db, user_id=user.id, action="EQUIPMENT_DELETE", status="OK",
        resource_type="equipment", resource_id=equipment_id,
    )
    await db.commit()
