"""3NF round-trip — catalog reuse + junctions."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Bean, BeanTastingNote, BrewlogTastingNote, TastingNote, User,
)
from app.repositories.beans import BeanRepository
from app.repositories.tasting_notes import TastingNoteRepository


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_attach_creates_catalog_rows_once(db: AsyncSession, user: User) -> None:
    beans = BeanRepository(db)
    tn = TastingNoteRepository(db)
    b1 = await beans.create(user_id=user.id, name="A", origin_country="CO",
                            process="Washed", roast_level="Light")
    b2 = await beans.create(user_id=user.id, name="B", origin_country="CO",
                            process="Washed", roast_level="Light")
    await tn.attach_to_bean(bean_id=b1.id, labels=["citrus", "chocolate"])
    await tn.attach_to_bean(bean_id=b2.id, labels=["citrus", "floral"])

    catalog = (await db.execute(select(TastingNote))).scalars().all()
    junctions = (await db.execute(select(BeanTastingNote))).scalars().all()
    assert {c.label for c in catalog} == {"citrus", "chocolate", "floral"}  # 3 catalog rows, not 4
    assert len(junctions) == 4  # b1×2 + b2×2
