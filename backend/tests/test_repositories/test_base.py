"""Tests for the generic AsyncRepository."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Roaster, User
from app.repositories.base import AsyncRepository, NotFoundError


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_create_returns_row_with_id(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    assert r.id is not None and r.name == "Onyx"


async def test_get_returns_existing(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    fetched = await repo.get(r.id)
    assert fetched.id == r.id


async def test_get_raises_not_found(db: AsyncSession) -> None:
    repo = AsyncRepository(Roaster, db)
    with pytest.raises(NotFoundError):
        await repo.get(uuid4())


async def test_list_returns_only_scoped_rows(db: AsyncSession, user: User) -> None:
    other = User(email="o@x.com", password_hash="x")
    db.add(other)
    await db.flush()
    repo = AsyncRepository(Roaster, db)
    await repo.create(user_id=user.id, name="A")
    await repo.create(user_id=other.id, name="B")
    mine = await repo.list_for_user(user_id=user.id)
    assert {r.name for r in mine} == {"A"}


async def test_delete_removes_row(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    await repo.delete(r.id)
    with pytest.raises(NotFoundError):
        await repo.get(r.id)
