"""Unit tests for app.auth.sessions lifecycle helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import create_session, lookup_session, revoke_session
from app.repositories.users import UserRepository


async def test_create_session_stores_with_ttl(db: AsyncSession) -> None:
    user = await UserRepository(db).create(email="ttl@test.com", password_hash="x")
    before = datetime.now(timezone.utc)
    row = await create_session(db, user.id)
    after = datetime.now(timezone.utc)

    assert row.id is not None
    assert row.user_id == user.id

    expected_min = before + timedelta(hours=24) - timedelta(seconds=1)
    expected_max = after + timedelta(hours=24) + timedelta(seconds=1)
    assert expected_min <= row.expires_at <= expected_max


async def test_lookup_session_returns_active(db: AsyncSession) -> None:
    user = await UserRepository(db).create(email="lookup@test.com", password_hash="x")
    row = await create_session(db, user.id)

    found = await lookup_session(db, row.id)

    assert found is not None
    assert found.id == row.id
    assert found.user_id == user.id


async def test_revoke_session_deletes(db: AsyncSession) -> None:
    user = await UserRepository(db).create(email="revoke@test.com", password_hash="x")
    row = await create_session(db, user.id)

    await revoke_session(db, row.id)

    result = await lookup_session(db, row.id)
    assert result is None
