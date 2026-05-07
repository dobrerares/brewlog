"""Equipment repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Equipment
from app.repositories.base import AsyncRepository


class EquipmentRepository(AsyncRepository[Equipment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Equipment, session)
