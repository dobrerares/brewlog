"""Integration tests for /api/v1/beans — repository-backed."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── helpers ──────────────────────────────────────────────────────────────────


async def _make_roaster(client: AsyncClient, **overrides: object) -> dict:
    payload = {"name": "Nomad Coffee", "location": "Barcelona"}
    payload.update(overrides)
    r = await client.post("/api/v1/roasters", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def _make_bean(
    client: AsyncClient,
    roaster_id: str | None = None,
    **overrides: object,
) -> dict:
    payload: dict[str, object] = {
        "name": "Finca La Esperanza",
        "roaster_id": roaster_id,
        "origin_country": "Colombia",
        "origin_region": "Huila",
        "process": "Washed",
        "roast_level": "Light",
        "variety": "Caturra",
        "elevation_m": 1800,
        "tasting_notes": ["chocolate", "citrus"],
        "purchase_date": "2026-03-01",
        "price": "18.50",
    }
    payload.update(overrides)
    r = await client.post("/api/v1/beans", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


# ── CRUD round-trip ──────────────────────────────────────────────────────────


async def test_create_bean_without_roaster(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    assert bean["roaster_id"] is None
    assert bean["id"]
    assert bean["name"] == "Finca La Esperanza"


async def test_create_bean_with_roaster(client: AsyncClient) -> None:
    roaster = await _make_roaster(client)
    bean = await _make_bean(client, roaster_id=roaster["id"])
    assert bean["roaster_id"] == roaster["id"]


async def test_create_bean_tasting_notes_round_trip(client: AsyncClient) -> None:
    bean = await _make_bean(client, tasting_notes=["caramel", "nutty"])
    assert set(bean["tasting_notes"]) == {"caramel", "nutty"}


async def test_get_bean(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.get(f"/api/v1/beans/{bean['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == bean["id"]


async def test_list_beans_returns_created(client: AsyncClient) -> None:
    await _make_bean(client, name="Alpha")
    await _make_bean(client, name="Beta")
    r = await client.get("/api/v1/beans")
    assert r.status_code == 200
    names = {b["name"] for b in r.json()}
    assert {"Alpha", "Beta"} <= names


async def test_delete_bean(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.delete(f"/api/v1/beans/{bean['id']}")
    assert r.status_code == 204
    assert (await client.get(f"/api/v1/beans/{bean['id']}")).status_code == 404


# ── 404 cases ─────────────────────────────────────────────────────────────────


async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    r = await client.get("/api/v1/beans/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_update_unknown_bean_returns_404(client: AsyncClient) -> None:
    r = await client.patch(
        "/api/v1/beans/00000000-0000-0000-0000-000000000000",
        json={"roast_level": "Dark"},
    )
    assert r.status_code == 404


async def test_delete_unknown_returns_404(client: AsyncClient) -> None:
    r = await client.delete("/api/v1/beans/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


# ── 422 — bad payload ─────────────────────────────────────────────────────────


async def test_create_bean_rejects_invalid_process(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Mystery",
            "roast_level": "Light",
        },
    )
    assert r.status_code == 422


async def test_create_bean_rejects_negative_elevation(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "elevation_m": -1,
        },
    )
    assert r.status_code == 422


async def test_create_bean_rejects_too_many_tasting_notes(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "tasting_notes": [f"n{i}" for i in range(40)],
        },
    )
    assert r.status_code == 422


# ── 422 — bad roaster_id ──────────────────────────────────────────────────────


async def test_create_bean_rejects_invalid_roaster(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": "00000000-0000-0000-0000-000000000000",
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "tasting_notes": [],
        },
    )
    assert r.status_code == 422


async def test_update_bean_into_unknown_roaster_is_rejected(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"roaster_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 422


# ── partial PATCH ─────────────────────────────────────────────────────────────


async def test_update_bean_partial_roast_level(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.patch(f"/api/v1/beans/{bean['id']}", json={"roast_level": "Medium"})
    assert r.status_code == 200
    body = r.json()
    assert body["roast_level"] == "Medium"
    assert body["name"] == bean["name"]  # unchanged


async def test_update_bean_replaces_tasting_notes(client: AsyncClient) -> None:
    bean = await _make_bean(client, tasting_notes=["chocolate"])
    r = await client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"tasting_notes": ["berry", "floral"]},
    )
    assert r.status_code == 200
    assert set(r.json()["tasting_notes"]) == {"berry", "floral"}


async def test_update_bean_with_invalid_field_returns_422(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.patch(f"/api/v1/beans/{bean['id']}", json={"elevation_m": -5})
    assert r.status_code == 422


async def test_update_bean_that_nulls_required_field_returns_422(client: AsyncClient) -> None:
    bean = await _make_bean(client)
    r = await client.patch(f"/api/v1/beans/{bean['id']}", json={"origin_country": None})
    assert r.status_code == 422
