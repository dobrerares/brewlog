"""Brewlog repository — adds bean/equipment scoped queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Brewlog
from app.repositories.base import AsyncRepository


class BrewlogRepository(AsyncRepository[Brewlog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Brewlog, session)

    async def list_for_user_and_bean(self, user_id: UUID, bean_id: UUID) -> list[Brewlog]:
        rows = await self.session.execute(
            select(Brewlog).where(
                Brewlog.user_id == user_id, Brewlog.bean_id == bean_id
            ).order_by(Brewlog.date.desc())
        )
        return list(rows.scalars().all())
