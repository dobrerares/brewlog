"""Session lifecycle — thin wrapper over SessionRepository.

Session ids are opaque UUIDs. The cookie carries only the id; the user_id
and expiry are server-side only.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import idle_minutes, make_refresh_token, token_hash
from app.db.models import RefreshSession, Session as SessionRow, User
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


async def create_refresh_session(
    db: AsyncSession,
    user: User,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[RefreshSession, str]:
    session = RefreshSession(
        user_id=user.id,
        refresh_token_hash="pending",
        expires_at=datetime.now(timezone.utc),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()
    refresh_token, expires_at = make_refresh_token(user_id=user.id, session_id=session.id)
    session.refresh_token_hash = token_hash(refresh_token)
    session.expires_at = expires_at
    session.last_seen_at = datetime.now(timezone.utc)
    await db.flush()
    return session, refresh_token


async def lookup_refresh_session(db: AsyncSession, refresh_token: str) -> RefreshSession | None:
    from sqlalchemy import select

    rows = await db.execute(
        select(RefreshSession).where(RefreshSession.refresh_token_hash == token_hash(refresh_token))
    )
    session = rows.scalar_one_or_none()
    if session is None or session.revoked_at is not None:
        return None
    now = datetime.now(timezone.utc)
    if session.expires_at <= now:
        session.revoked_at = now
        await db.flush()
        return None
    if session.last_seen_at + timedelta(minutes=idle_minutes()) <= now:
        session.revoked_at = now
        await db.flush()
        return None
    return session


async def touch_refresh_session(db: AsyncSession, session: RefreshSession) -> None:
    session.last_seen_at = datetime.now(timezone.utc)
    await db.flush()


async def revoke_refresh_session(db: AsyncSession, session: RefreshSession) -> None:
    session.revoked_at = datetime.now(timezone.utc)
    await db.flush()
