"""Integration tests for /api/v1/brewlogs — repository-backed.

FK dependencies (beans, equipment) are inserted directly into the test DB
session because those handlers are ported by parallel agents and may not yet
be DB-backed in this worktree.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_DEV_USER = UUID("00000000-0000-0000-0000-000000000001")


async def _insert_bean(db: AsyncSession, **overrides) -> dict:
    """Insert a bean row directly into the DB and return it as a dict."""
    from app.db.models import Bean

    fields = {
        "id": uuid4(),
        "user_id": _DEV_USER,
        "name": "Finca La Esperanza",
        "origin_country": "Colombia",
        "process": "Washed",
        "roast_level": "Light",
        "roaster_id": None,
    }
    fields.update(overrides)
    row = Bean(**fields)
    db.add(row)
    await db.flush()
    return {"id": str(row.id)}


async def _insert_equipment(db: AsyncSession, **overrides) -> dict:
    """Insert an equipment row directly into the DB and return it as a dict."""
    from app.db.models import Equipment

    fields = {
        "id": uuid4(),
        "user_id": _DEV_USER,
        "name": "Hario V60",
        "type": "Brewer",
        "brand": "Hario",
        "model": "02",
    }
    fields.update(overrides)
    row = Equipment(**fields)
    db.add(row)
    await db.flush()
    return {"id": str(row.id)}


async def _make_brewlog(
    client: AsyncClient,
    bean_id: str,
    equipment_id: str,
    grinder_id: str,
    **overrides,
) -> dict:
    payload: dict = {
        "date": "2026-04-01T08:30:00",
        "bean_id": bean_id,
        "equipment_id": equipment_id,
        "grinder_id": grinder_id,
        "grind_setting": "22 clicks",
        "method": "V60",
        "dose_g": "15",
        "water_g": "250",
        "water_temp_c": 94,
        "brew_time_s": 150,
        "yield_g": None,
        "rating": 4,
        "taste_result": "Balanced",
        "grind_adjustment": None,
        "tasting_notes": ["chocolate"],
        "notes": "Solid pourover.",
        "photo_url": None,
    }
    payload.update(overrides)
    r = await client.post("/api/v1/brewlogs", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
async def refs(client: AsyncClient, db: AsyncSession) -> dict[str, str]:
    bean = await _insert_bean(db)
    brewer = await _insert_equipment(db, name="Hario V60", type="Brewer")
    grinder = await _insert_equipment(db, name="Comandante C40", type="Grinder")
    return {
        "bean_id": bean["id"],
        "equipment_id": brewer["id"],
        "grinder_id": grinder["id"],
    }


async def test_create_and_get_brewlog(client: AsyncClient, refs: dict[str, str]) -> None:
    brew = await _make_brewlog(client, **refs)
    got = await client.get(f"/api/v1/brewlogs/{brew['id']}")
    assert got.status_code == 200
    assert got.json()["method"] == "V60"


async def test_create_espresso_requires_yield(client: AsyncClient, refs: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "fine",
            "method": "Espresso",
            "dose_g": "18",
            "water_g": "36",
            "water_temp_c": 93,
            "brew_time_s": 30,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "yield_g" in r.text


async def test_create_espresso_with_yield(client: AsyncClient, refs: dict[str, str]) -> None:
    brew = await _make_brewlog(
        client,
        **refs,
        method="Espresso",
        dose_g="18",
        water_g="36",
        water_temp_c=93,
        brew_time_s=30,
        yield_g="34",
    )
    assert brew["method"] == "Espresso"
    assert brew["yield_g"] == "34"


async def test_create_rejects_bad_ratio(client: AsyncClient, refs: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "100",  # ratio ~6.6x — too low
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "ratio" in r.text


async def test_create_rejects_bad_temp_for_method(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 75,  # way below V60's 90–96 band
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "water_temp_c" in r.text


async def test_create_rejects_low_rating_without_notes(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 2,
            "taste_result": "Sour",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "notes" in r.text


async def test_low_rating_with_notes_is_accepted(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    brew = await _make_brewlog(
        client, **refs, rating=2, taste_result="Sour", notes="Too sharp, go finer."
    )
    assert brew["rating"] == 2


async def test_create_rejects_unknown_bean(client: AsyncClient, refs: dict[str, str]) -> None:
    bad = {**refs, "bean_id": "00000000-0000-0000-0000-000000000000"}
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "bean_id" in r.text


async def test_create_rejects_unknown_equipment(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    bad = {**refs, "equipment_id": "00000000-0000-0000-0000-000000000000"}
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "equipment_id" in r.text


async def test_create_rejects_unknown_grinder(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    bad = {**refs, "grinder_id": "00000000-0000-0000-0000-000000000000"}
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert r.status_code == 422
    assert "grinder_id" in r.text


async def test_list_brewlogs_sorted_newest_first(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    dates = [
        "2026-04-01T08:00:00",
        "2026-04-02T08:00:00",
        "2026-04-03T08:00:00",
        "2026-04-04T08:00:00",
        "2026-04-05T08:00:00",
    ]
    for d in dates:
        await _make_brewlog(client, **refs, date=d)

    r = await client.get("/api/v1/brewlogs")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 5
    # newest first
    returned_dates = [item["date"] for item in items]
    assert returned_dates == sorted(returned_dates, reverse=True)


async def test_list_filters_by_method(client: AsyncClient, refs: dict[str, str]) -> None:
    await _make_brewlog(client, **refs, method="V60")
    await _make_brewlog(
        client,
        **refs,
        method="Espresso",
        dose_g="18",
        water_g="36",
        water_temp_c=93,
        brew_time_s=30,
        yield_g="34",
    )
    r = await client.get("/api/v1/brewlogs", params={"method": "Espresso"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["method"] == "Espresso"


async def test_list_filters_by_taste_and_rating_range(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    await _make_brewlog(client, **refs, rating=5, taste_result="Balanced")
    await _make_brewlog(
        client,
        **refs,
        rating=2,
        taste_result="Sour",
        notes="under-extracted",
    )

    r = await client.get("/api/v1/brewlogs", params={"min_rating": 4, "taste_result": "Balanced"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get("/api/v1/brewlogs", params={"max_rating": 3})
    assert r.status_code == 200
    low = r.json()
    assert len(low) == 1
    assert low[0]["rating"] == 2


async def test_list_filters_by_bean_id(
    client: AsyncClient, refs: dict[str, str], db: AsyncSession
) -> None:
    other_bean = await _insert_bean(db, name="Other Bean")
    await _make_brewlog(client, **refs)
    await _make_brewlog(client, **{**refs, "bean_id": other_bean["id"]})
    r = await client.get("/api/v1/brewlogs", params={"bean_id": other_bean["id"]})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["bean_id"] == other_bean["id"]


async def test_list_filters_by_date_range(client: AsyncClient, refs: dict[str, str]) -> None:
    await _make_brewlog(client, **refs, date="2026-03-01T08:00:00")
    await _make_brewlog(client, **refs, date="2026-04-01T08:00:00")
    r = await client.get(
        "/api/v1/brewlogs",
        params={"date_from": "2026-03-15T00:00:00", "date_to": "2026-05-01T00:00:00"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_update_brewlog(client: AsyncClient, refs: dict[str, str]) -> None:
    brew = await _make_brewlog(client, **refs)
    r = await client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"rating": 5, "notes": "Revisited and loved it."},
    )
    assert r.status_code == 200
    assert r.json()["rating"] == 5


async def test_update_brewlog_revalidates_business_rules(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    brew = await _make_brewlog(client, **refs, rating=4, taste_result="Balanced")
    # Rating < 3 without notes must fail the cross-field rule.
    r = await client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"rating": 2, "notes": None},
    )
    assert r.status_code == 422


async def test_update_brewlog_can_change_bean(
    client: AsyncClient, refs: dict[str, str], db: AsyncSession
) -> None:
    brew = await _make_brewlog(client, **refs)
    other_bean = await _insert_bean(db, name="Another Bean")
    r = await client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"bean_id": other_bean["id"]},
    )
    assert r.status_code == 200
    assert r.json()["bean_id"] == other_bean["id"]


async def test_update_brewlog_rejects_unknown_ref(
    client: AsyncClient, refs: dict[str, str]
) -> None:
    brew = await _make_brewlog(client, **refs)
    r = await client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"bean_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 422


async def test_update_unknown_brewlog_returns_404(client: AsyncClient) -> None:
    r = await client.patch(
        "/api/v1/brewlogs/00000000-0000-0000-0000-000000000000",
        json={"rating": 5, "notes": "x"},
    )
    assert r.status_code == 404


async def test_delete_brewlog(client: AsyncClient, refs: dict[str, str]) -> None:
    brew = await _make_brewlog(client, **refs)
    r = await client.delete(f"/api/v1/brewlogs/{brew['id']}")
    assert r.status_code == 204
    assert (await client.get(f"/api/v1/brewlogs/{brew['id']}")).status_code == 404


async def test_delete_unknown_returns_404(client: AsyncClient) -> None:
    r = await client.delete("/api/v1/brewlogs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/brewlogs/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_create_rejects_extra_field(client: AsyncClient, refs: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
            "mystery": "x",
        },
    )
    assert r.status_code == 422


async def test_tasting_notes_round_trip(client: AsyncClient, refs: dict[str, str]) -> None:
    brew = await _make_brewlog(client, **refs, tasting_notes=["caramel", "floral"])
    got = await client.get(f"/api/v1/brewlogs/{brew['id']}")
    assert got.status_code == 200
    assert set(got.json()["tasting_notes"]) == {"caramel", "floral"}


async def test_tasting_notes_patch_adds(client: AsyncClient, refs: dict[str, str]) -> None:
    """PATCH with tasting_notes appends new labels (on_conflict_do_nothing semantics)."""
    brew = await _make_brewlog(client, **refs, tasting_notes=["chocolate"])
    r = await client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"tasting_notes": ["caramel", "citrus"]},
    )
    assert r.status_code == 200
    # After patch, new notes should be present (additive — on_conflict_do_nothing)
    got = await client.get(f"/api/v1/brewlogs/{brew['id']}")
    notes = set(got.json()["tasting_notes"])
    assert {"caramel", "citrus"} <= notes
