"""Roaster API tests — repository-backed."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_create_roaster_201(client: AsyncClient) -> None:
    r = await client.post("/api/v1/roasters", json={"name": "Onyx", "location": "Boston"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Onyx" and body["id"]


async def test_list_roasters_returns_created(client: AsyncClient) -> None:
    await client.post("/api/v1/roasters", json={"name": "A"})
    await client.post("/api/v1/roasters", json={"name": "B"})
    r = await client.get("/api/v1/roasters")
    assert r.status_code == 200
    assert {row["name"] for row in r.json()} >= {"A", "B"}


async def test_get_roaster_404_when_missing(client: AsyncClient) -> None:
    r = await client.get("/api/v1/roasters/00000000-0000-0000-0000-000000000abc")
    assert r.status_code == 404


async def test_update_roaster(client: AsyncClient) -> None:
    created = await client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await client.patch(f"/api/v1/roasters/{rid}", json={"location": "NYC"})
    assert r.status_code == 200 and r.json()["location"] == "NYC"


async def test_delete_roaster_204(client: AsyncClient) -> None:
    created = await client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await client.delete(f"/api/v1/roasters/{rid}")
    assert r.status_code == 204
