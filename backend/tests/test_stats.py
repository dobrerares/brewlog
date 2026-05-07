"""Integration tests for /api/v1/stats/brewlogs — SQL-aggregation backed."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bean, Brewlog, Equipment

# Dev user seeded by the `client` fixture in conftest.py
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def test_stats_empty_state(client: AsyncClient) -> None:
    """With no brewlogs present the endpoint returns zeroed/null fields."""
    r = await client.get("/api/v1/stats/brewlogs")
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "total_brews": 0,
        "average_rating": None,
        "most_used_method": None,
        "by_method": [],
        "by_taste": [],
        "balanced_ratio": None,
    }


# ────────────────────────── helpers ──────────────────────────────────────────


async def _insert_bean(db: AsyncSession) -> UUID:
    bean = Bean(
        user_id=DEV_USER_ID,
        name="Test Bean",
        origin_country="Colombia",
        process="Washed",
        roast_level="Light",
    )
    db.add(bean)
    await db.flush()
    return bean.id


async def _insert_equipment(db: AsyncSession, eq_type: str, name: str) -> UUID:
    eq = Equipment(
        user_id=DEV_USER_ID,
        name=name,
        type=eq_type,
        brand="TestBrand",
        model="X1",
    )
    db.add(eq)
    await db.flush()
    return eq.id


def _brewlog(
    bean_id: UUID,
    equipment_id: UUID,
    grinder_id: UUID,
    *,
    method: str,
    rating: int,
    taste_result: str | None = None,
) -> Brewlog:
    return Brewlog(
        user_id=DEV_USER_ID,
        bean_id=bean_id,
        equipment_id=equipment_id,
        grinder_id=grinder_id,
        date=datetime(2026, 4, 1, 8, 30, tzinfo=timezone.utc),
        grind_setting="22 clicks",
        method=method,
        dose_g=Decimal("15.0"),
        water_g=Decimal("250.0"),
        water_temp_c=94,
        brew_time_s=150,
        rating=rating,
        taste_result=taste_result,
    )


# ────────────────────────── aggregation tests ────────────────────────────────


async def test_stats_aggregates_correctly(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Stats endpoint aggregates method/taste counts and ratios correctly."""
    bean_id = await _insert_bean(db)
    brewer_id = await _insert_equipment(db, "Brewer", "Hario V60")
    grinder_id = await _insert_equipment(db, "Grinder", "Comandante C40")

    # 3× V60, 1× Espresso; tastes: Balanced×2, Sour×1, Astringent×1
    rows = [
        _brewlog(bean_id, brewer_id, grinder_id, method="V60", rating=4, taste_result="Balanced"),
        _brewlog(bean_id, brewer_id, grinder_id, method="V60", rating=5, taste_result="Balanced"),
        _brewlog(bean_id, brewer_id, grinder_id, method="V60", rating=2, taste_result="Sour"),
        _brewlog(
            bean_id, brewer_id, grinder_id,
            method="Espresso", rating=3, taste_result="Astringent",
        ),
    ]
    for row in rows:
        db.add(row)
    await db.flush()

    r = await client.get("/api/v1/stats/brewlogs")
    assert r.status_code == 200
    body = r.json()

    assert body["total_brews"] == 4
    assert body["most_used_method"] == "V60"
    # (4 + 5 + 2 + 3) / 4 == 3.5
    assert body["average_rating"] == 3.5

    methods = {entry["method"]: entry["count"] for entry in body["by_method"]}
    assert methods == {"V60": 3, "Espresso": 1}

    tastes = {entry["taste_result"]: entry["count"] for entry in body["by_taste"]}
    assert tastes == {"Balanced": 2, "Sour": 1, "Astringent": 1}

    # 2 balanced out of 4 rated
    assert body["balanced_ratio"] == 0.5


async def test_stats_no_taste_results(
    client: AsyncClient, db: AsyncSession
) -> None:
    """When no brewlog has a taste_result, by_taste is empty and balanced_ratio is None."""
    bean_id = await _insert_bean(db)
    brewer_id = await _insert_equipment(db, "Brewer", "AeroPress Brewer")
    grinder_id = await _insert_equipment(db, "Grinder", "Hand Grinder")

    db.add(_brewlog(bean_id, brewer_id, grinder_id, method="AeroPress", rating=4, taste_result=None))
    db.add(_brewlog(bean_id, brewer_id, grinder_id, method="AeroPress", rating=3, taste_result=None))
    await db.flush()

    r = await client.get("/api/v1/stats/brewlogs")
    assert r.status_code == 200
    body = r.json()

    assert body["total_brews"] == 2
    assert body["by_taste"] == []
    assert body["balanced_ratio"] is None
    assert body["most_used_method"] == "AeroPress"


async def test_stats_all_balanced(
    client: AsyncClient, db: AsyncSession
) -> None:
    """When all rated brews are Balanced the ratio is 1.0."""
    bean_id = await _insert_bean(db)
    brewer_id = await _insert_equipment(db, "Brewer", "Chemex")
    grinder_id = await _insert_equipment(db, "Grinder", "Baratza")

    for _ in range(3):
        db.add(
            _brewlog(bean_id, brewer_id, grinder_id, method="Chemex", rating=5, taste_result="Balanced")
        )
    await db.flush()

    r = await client.get("/api/v1/stats/brewlogs")
    assert r.status_code == 200
    body = r.json()

    assert body["total_brews"] == 3
    assert body["balanced_ratio"] == 1.0
    assert body["average_rating"] == 5.0
