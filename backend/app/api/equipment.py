"""Equipment CRUD — repository-backed."""

from __future__ import annotations

from os import environ
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.base import NotFoundError
from app.repositories.equipment import EquipmentRepository
from app.schemas.equipment import Equipment, EquipmentCreate, EquipmentUpdate

router = APIRouter(prefix="/equipment", tags=["equipment"])

_DEV_USER = UUID(environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))


def _repo(db: AsyncSession = Depends(get_db)) -> EquipmentRepository:
    return EquipmentRepository(db)


@router.get("", response_model=list[Equipment])
async def list_equipment(repo: EquipmentRepository = Depends(_repo)):
    rows = await repo.list()
    return [Equipment.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Equipment, status_code=201)
async def create_equipment(
    payload: EquipmentCreate,
    repo: EquipmentRepository = Depends(_repo),
):
    row = await repo.create(user_id=_DEV_USER, **payload.model_dump())
    await repo.session.commit()
    return Equipment.model_validate(row, from_attributes=True)


@router.get("/{equipment_id}", response_model=Equipment)
async def get_equipment(
    equipment_id: UUID,
    repo: EquipmentRepository = Depends(_repo),
):
    try:
        row = await repo.get(equipment_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    return Equipment.model_validate(row, from_attributes=True)


@router.patch("/{equipment_id}", response_model=Equipment)
async def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    repo: EquipmentRepository = Depends(_repo),
):
    try:
        row = await repo.get(equipment_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")

    # Merge current DB state with incoming partial update, then re-validate
    # the full Equipment schema so cross-field constraints (e.g. Brewer cannot
    # have grind_type) are enforced before we persist anything.
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
    await repo.session.commit()
    return Equipment.model_validate(updated_row, from_attributes=True)


@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(
    equipment_id: UUID,
    repo: EquipmentRepository = Depends(_repo),
):
    try:
        await repo.delete(equipment_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await repo.session.commit()
