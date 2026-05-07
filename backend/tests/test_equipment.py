"""Equipment API tests — repository-backed, auth-gated."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ─── inline helpers ────────────────────────────────────────────────────────────


async def _make_brewer(client: AsyncClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Hario V60",
        "type": "Brewer",
        "brand": "Hario",
        "model": "02",
        "grind_type": None,
        "grind_range": None,
        "grind_unit": None,
        "notes": None,
    }
    payload.update(overrides)
    r = await client.post("/api/v1/equipment", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def _make_grinder(client: AsyncClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Comandante C40",
        "type": "Grinder",
        "brand": "Comandante",
        "model": "MK4",
        "grind_type": "Stepped",
        "grind_range": "clicks 0-40",
        "grind_unit": "1 click",
        "notes": None,
    }
    payload.update(overrides)
    r = await client.post("/api/v1/equipment", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ─── tests ─────────────────────────────────────────────────────────────────────


async def test_create_brewer(logged_in_client: AsyncClient) -> None:
    brewer = await _make_brewer(logged_in_client)
    assert brewer["type"] == "Brewer"
    assert brewer["grind_type"] is None
    assert brewer["id"]


async def test_create_grinder(logged_in_client: AsyncClient) -> None:
    grinder = await _make_grinder(logged_in_client)
    assert grinder["type"] == "Grinder"
    assert grinder["grind_type"] == "Stepped"
    assert grinder["id"]


async def test_get_equipment(logged_in_client: AsyncClient) -> None:
    brewer = await _make_brewer(logged_in_client, name="V60 Special")
    r = await logged_in_client.get(f"/api/v1/equipment/{brewer['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "V60 Special"


async def test_get_unknown_returns_404(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.get("/api/v1/equipment/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_equipment(logged_in_client: AsyncClient) -> None:
    await _make_brewer(logged_in_client, name="Alpha")
    await _make_brewer(logged_in_client, name="Beta")
    r = await logged_in_client.get("/api/v1/equipment")
    assert r.status_code == 200
    names = {e["name"] for e in r.json()}
    assert {"Alpha", "Beta"} <= names


async def test_grinder_requires_grind_type(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.post(
        "/api/v1/equipment",
        json={
            "name": "Orphan",
            "type": "Grinder",
            "brand": "X",
            "model": None,
            "grind_type": None,
            "grind_range": None,
            "grind_unit": None,
            "notes": None,
        },
    )
    assert r.status_code == 422
    assert "grind_type" in r.text


async def test_brewer_cannot_have_grinder_fields(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.post(
        "/api/v1/equipment",
        json={
            "name": "Weirdbrewer",
            "type": "Brewer",
            "brand": "X",
            "model": None,
            "grind_type": "Stepless",
            "grind_range": None,
            "grind_unit": None,
            "notes": None,
        },
    )
    assert r.status_code == 422


async def test_update_equipment_partial(logged_in_client: AsyncClient) -> None:
    brewer = await _make_brewer(logged_in_client)
    r = await logged_in_client.patch(
        f"/api/v1/equipment/{brewer['id']}",
        json={"model": "Ceramic"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "Ceramic"
    assert body["name"] == brewer["name"]  # unchanged


async def test_update_into_invalid_grinder_combo_is_rejected(logged_in_client: AsyncClient) -> None:
    brewer = await _make_brewer(logged_in_client)
    r = await logged_in_client.patch(
        f"/api/v1/equipment/{brewer['id']}",
        json={"grind_type": "Stepped"},
    )
    # Brewer can't get a grind_type — re-validation must catch it.
    assert r.status_code == 422


async def test_update_unknown_equipment_returns_404(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.patch(
        "/api/v1/equipment/00000000-0000-0000-0000-000000000000",
        json={"model": "X"},
    )
    assert r.status_code == 404


async def test_delete_equipment(logged_in_client: AsyncClient) -> None:
    brewer = await _make_brewer(logged_in_client)
    r = await logged_in_client.delete(f"/api/v1/equipment/{brewer['id']}")
    assert r.status_code == 204
    assert (await logged_in_client.get(f"/api/v1/equipment/{brewer['id']}")).status_code == 404


async def test_delete_unknown_returns_404(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.delete("/api/v1/equipment/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
