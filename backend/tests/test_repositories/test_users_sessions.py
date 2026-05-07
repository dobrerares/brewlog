"""User, session, audit-log repository tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, Role, User, UserRole
from app.repositories.audit_log import AuditLogRepository
from app.repositories.sessions import SessionRepository
from app.repositories.users import UserRepository


async def test_user_lookup_by_email(db: AsyncSession) -> None:
    repo = UserRepository(db)
    u = await repo.create(email="a@b.com", password_hash="x")
    found = await repo.find_by_email("a@b.com")
    assert found is not None and found.id == u.id


async def test_user_lookup_unknown_email_returns_none(db: AsyncSession) -> None:
    repo = UserRepository(db)
    assert await repo.find_by_email("nobody@x.com") is None


async def test_session_create_and_lookup(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    s = await session_repo.create_session(user_id=u.id, expires_at=expires)
    fetched = await session_repo.lookup_active(s.id)
    assert fetched is not None and fetched.user_id == u.id


async def test_session_lookup_expired_returns_none(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    expires = datetime.now(timezone.utc) - timedelta(seconds=1)
    s = await session_repo.create_session(user_id=u.id, expires_at=expires)
    assert await session_repo.lookup_active(s.id) is None


async def test_audit_log_insert_records_row(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    audit_repo = AuditLogRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    await audit_repo.write(user_id=u.id, action="LOGIN", status="OK")
    rows = (await db.execute(select(AuditLog).where(AuditLog.user_id == u.id))).scalars().all()
    assert len(rows) == 1 and rows[0].action == "LOGIN"
