"""Roaster API tests — repository-backed, auth-gated."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_create_roaster_201(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.post("/api/v1/roasters", json={"name": "Onyx", "location": "Boston"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Onyx" and body["id"]


async def test_list_roasters_returns_created(logged_in_client: AsyncClient) -> None:
    await logged_in_client.post("/api/v1/roasters", json={"name": "A"})
    await logged_in_client.post("/api/v1/roasters", json={"name": "B"})
    r = await logged_in_client.get("/api/v1/roasters")
    assert r.status_code == 200
    assert {row["name"] for row in r.json()} >= {"A", "B"}


async def test_get_roaster_404_when_missing(logged_in_client: AsyncClient) -> None:
    r = await logged_in_client.get("/api/v1/roasters/00000000-0000-0000-0000-000000000abc")
    assert r.status_code == 404


async def test_update_roaster(logged_in_client: AsyncClient) -> None:
    created = await logged_in_client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await logged_in_client.patch(f"/api/v1/roasters/{rid}", json={"location": "NYC"})
    assert r.status_code == 200 and r.json()["location"] == "NYC"


async def test_delete_roaster_204(logged_in_client: AsyncClient) -> None:
    created = await logged_in_client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await logged_in_client.delete(f"/api/v1/roasters/{rid}")
    assert r.status_code == 204
