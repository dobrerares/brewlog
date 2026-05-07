"""FastAPI dependencies."""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db as _get_db


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in _get_db():
        yield session
