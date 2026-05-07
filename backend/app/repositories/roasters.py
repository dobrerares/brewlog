"""Roaster repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Roaster
from app.repositories.base import AsyncRepository


class RoasterRepository(AsyncRepository[Roaster]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Roaster, session)
