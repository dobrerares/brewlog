"""Auth API tests — register, login, logout, me."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_register_creates_user(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "a@x.com"


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter3"})
    assert r.status_code == 409


async def test_login_sets_session_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 200
    assert "session_id" in r.cookies


async def test_login_wrong_password_401(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "wrong"})
    assert r.status_code == 401


async def test_login_unknown_user_401(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/login", json={"email": "ghost@x.com", "password": "x"})
    assert r.status_code == 401


async def test_me_requires_login(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200 and r.json()["email"] == "a@x.com"


async def test_logout_clears_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 204
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401
