"""Server-side session repository — opaque cookie ids."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as SessionRow
from app.repositories.base import AsyncRepository


class SessionRepository(AsyncRepository[SessionRow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SessionRow, session)

    async def create_session(self, user_id: UUID, expires_at: datetime) -> SessionRow:
        s = SessionRow(user_id=user_id, expires_at=expires_at)
        self.session.add(s)
        await self.session.flush()
        return s

    async def lookup_active(self, session_id: UUID) -> SessionRow | None:
        rows = await self.session.execute(
            select(SessionRow).where(
                SessionRow.id == session_id,
                SessionRow.expires_at > datetime.now(timezone.utc),
            )
        )
        return rows.scalar_one_or_none()

    async def revoke(self, session_id: UUID) -> None:
        await self.session.execute(delete(SessionRow).where(SessionRow.id == session_id))
        await self.session.flush()
