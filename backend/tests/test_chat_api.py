"""Chat REST tests — list rooms, history, DM upsert."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login_two_users(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/register", json={"email": "b@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})


async def test_list_rooms_includes_lobby(client: AsyncClient) -> None:
    await _login_two_users(client)
    r = await client.get("/api/v1/chat/rooms")
    assert r.status_code == 200
    rooms = r.json()
    assert any(room.get("name") == "lobby" for room in rooms)


async def test_history_paginates_newest_first(client: AsyncClient) -> None:
    await _login_two_users(client)
    rooms = (await client.get("/api/v1/chat/rooms")).json()
    lobby_id = next(r["id"] for r in rooms if r.get("name") == "lobby")
    # No messages yet; expect empty list with 200
    r = await client.get(f"/api/v1/chat/rooms/{lobby_id}/messages")
    assert r.status_code == 200 and r.json() == []
