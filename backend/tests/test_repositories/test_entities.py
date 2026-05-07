"""Entity-specific repository tests — covers cross-entity FK behaviour."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.beans import BeanRepository
from app.repositories.brewlogs import BrewlogRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.roasters import RoasterRepository


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_bean_roaster_setnull_cascade(db: AsyncSession, user: User) -> None:
    roasters = RoasterRepository(db)
    beans = BeanRepository(db)
    r = await roasters.create(user_id=user.id, name="Onyx")
    b = await beans.create(
        user_id=user.id, roaster_id=r.id, name="Esperanza",
        origin_country="CO", process="Washed", roast_level="Light",
    )
    await roasters.delete(r.id)
    fetched = await beans.get(b.id)
    assert fetched.roaster_id is None  # ON DELETE SET NULL


async def test_brewlog_user_restrict(db: AsyncSession, user: User) -> None:
    """Deleting a user with brewlogs raises IntegrityError (RESTRICT)."""
    eqs = EquipmentRepository(db)
    beans = BeanRepository(db)
    brewlogs = BrewlogRepository(db)

    bean = await beans.create(
        user_id=user.id, name="X", origin_country="CO",
        process="Washed", roast_level="Light",
    )
    brewer = await eqs.create(user_id=user.id, name="V60", type="Brewer", brand="Hario")
    grinder = await eqs.create(user_id=user.id, name="C40", type="Grinder", brand="Comandante")
    await brewlogs.create(
        user_id=user.id, bean_id=bean.id, equipment_id=brewer.id, grinder_id=grinder.id,
        date=datetime.now(timezone.utc), grind_setting="20", method="V60",
        dose_g=Decimal("15"), water_g=Decimal("250"),
        water_temp_c=93, brew_time_s=180, rating=4,
    )
    await db.flush()

    await db.delete(user)
    with pytest.raises(IntegrityError):
        await db.flush()
