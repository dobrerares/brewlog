"""Roaster CRUD — repository-backed."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.base import NotFoundError
from app.repositories.roasters import RoasterRepository
from app.schemas.roaster import Roaster, RoasterCreate, RoasterUpdate

router = APIRouter(prefix="/roasters", tags=["roasters"])


def _repo(db: AsyncSession = Depends(get_db)) -> RoasterRepository:
    return RoasterRepository(db)


@router.get("", response_model=list[Roaster])
async def list_roasters(repo: RoasterRepository = Depends(_repo)):
    rows = await repo.list()
    return [Roaster.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Roaster, status_code=201)
async def create_roaster(payload: RoasterCreate, repo: RoasterRepository = Depends(_repo)):
    # Note: user_id wiring comes in Phase 3 (auth). For now use a fixed dev user.
    from os import environ
    from uuid import UUID as _UUID
    dev_user = _UUID(environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))
    row = await repo.create(user_id=dev_user, **payload.model_dump())
    await repo.session.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.get("/{roaster_id}", response_model=Roaster)
async def get_roaster(roaster_id: UUID, repo: RoasterRepository = Depends(_repo)):
    try:
        row = await repo.get(roaster_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    return Roaster.model_validate(row, from_attributes=True)


@router.patch("/{roaster_id}", response_model=Roaster)
async def update_roaster(roaster_id: UUID, payload: RoasterUpdate, repo: RoasterRepository = Depends(_repo)):
    try:
        row = await repo.update(roaster_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await repo.session.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.delete("/{roaster_id}", status_code=204)
async def delete_roaster(roaster_id: UUID, repo: RoasterRepository = Depends(_repo)):
    try:
        await repo.delete(roaster_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await repo.session.commit()
