"""Session lifecycle — thin wrapper over SessionRepository.

Session ids are opaque UUIDs. The cookie carries only the id; the user_id
and expiry are server-side only.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as SessionRow
from app.repositories.sessions import SessionRepository


def _ttl_hours() -> int:
    return int(os.environ.get("SESSION_TTL_HOURS", "24"))


async def create_session(db: AsyncSession, user_id: UUID) -> SessionRow:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_ttl_hours())
    return await SessionRepository(db).create_session(user_id=user_id, expires_at=expires_at)


async def lookup_session(db: AsyncSession, session_id: UUID) -> SessionRow | None:
    return await SessionRepository(db).lookup_active(session_id)


async def revoke_session(db: AsyncSession, session_id: UUID) -> None:
    await SessionRepository(db).revoke(session_id)
