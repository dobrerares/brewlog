"""Roaster CRUD — repository-backed, auth-gated."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.permissions import (
    PERM_ROASTER_CREATE,
    PERM_ROASTER_DELETE_OWN,
    PERM_ROASTER_READ,
    PERM_ROASTER_UPDATE_OWN,
)
from app.db.models import User
from app.repositories.base import NotFoundError
from app.repositories.roasters import RoasterRepository
from app.schemas.roaster import Roaster, RoasterCreate, RoasterUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/roasters", tags=["roasters"])


def _repo(db: AsyncSession = Depends(get_db)) -> RoasterRepository:
    return RoasterRepository(db)


@router.get("", response_model=list[Roaster])
async def list_roasters(
    user: User = Depends(requires(PERM_ROASTER_READ)),
    repo: RoasterRepository = Depends(_repo),
):
    rows = await repo.list_for_user(user.id)
    return [Roaster.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Roaster, status_code=201)
async def create_roaster(
    payload: RoasterCreate,
    user: User = Depends(requires(PERM_ROASTER_CREATE)),
    repo: RoasterRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    row = await repo.create(user_id=user.id, **payload.model_dump())
    await write_audit(
        db, user_id=user.id, action="ROASTER_CREATE", status="OK",
        resource_type="roaster", resource_id=row.id,
    )
    await db.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.get("/{roaster_id}", response_model=Roaster)
async def get_roaster(
    roaster_id: UUID,
    user: User = Depends(requires(PERM_ROASTER_READ)),
    repo: RoasterRepository = Depends(_repo),
):
    try:
        row = await repo.get_for_user(roaster_id, user.id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    return Roaster.model_validate(row, from_attributes=True)


@router.patch("/{roaster_id}", response_model=Roaster)
async def update_roaster(
    roaster_id: UUID,
    payload: RoasterUpdate,
    user: User = Depends(requires(PERM_ROASTER_UPDATE_OWN)),
    repo: RoasterRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        await repo.get_for_user(roaster_id, user.id)
        row = await repo.update(roaster_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await write_audit(
        db, user_id=user.id, action="ROASTER_UPDATE", status="OK",
        resource_type="roaster", resource_id=row.id,
    )
    await db.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.delete("/{roaster_id}", status_code=204)
async def delete_roaster(
    roaster_id: UUID,
    user: User = Depends(requires(PERM_ROASTER_DELETE_OWN)),
    repo: RoasterRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        await repo.get_for_user(roaster_id, user.id)
        await repo.delete(roaster_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await write_audit(
        db, user_id=user.id, action="ROASTER_DELETE", status="OK",
        resource_type="roaster", resource_id=roaster_id,
    )
    await db.commit()
