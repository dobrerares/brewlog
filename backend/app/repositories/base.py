"""Generic async CRUD repository keyed by UUID PK + user_id scoping."""

from __future__ import annotations

from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class NotFoundError(LookupError):
    """Raised when a primary-key lookup fails."""


ModelT = TypeVar("ModelT", bound=Base)


class AsyncRepository(Generic[ModelT]):
    """Generic CRUD over any ORM model with a UUID primary key.

    Scoping helpers (list_for_user, get_for_user) assume the model has a
    `user_id` column — the entity tables in this app all do.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **fields: object) -> ModelT:
        instance = self.model(**fields)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, pk: UUID) -> ModelT:
        instance = await self.session.get(self.model, pk, populate_existing=True)
        if instance is None:
            raise NotFoundError(f"{self.model.__tablename__}:{pk}")
        return instance

    async def get_for_user(self, pk: UUID, user_id: UUID) -> ModelT:
        instance = await self.get(pk)
        if getattr(instance, "user_id", None) != user_id:
            raise NotFoundError(f"{self.model.__tablename__}:{pk}")
        return instance

    async def list(self) -> list[ModelT]:
        rows = await self.session.execute(select(self.model))
        return list(rows.scalars().all())

    async def list_for_user(self, user_id: UUID) -> list[ModelT]:
        rows = await self.session.execute(
            select(self.model).where(self.model.user_id == user_id)  # type: ignore[attr-defined]
        )
        return list(rows.scalars().all())

    async def update(self, pk: UUID, **fields: object) -> ModelT:
        instance = await self.get(pk)
        for k, v in fields.items():
            setattr(instance, k, v)
        await self.session.flush()
        return instance

    async def delete(self, pk: UUID) -> None:
        instance = await self.get(pk)
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self) -> int:
        from sqlalchemy import func as f

        rows = await self.session.execute(select(f.count()).select_from(self.model))
        return int(rows.scalar_one())
