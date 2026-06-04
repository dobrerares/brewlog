"""Auth API tests — register, login, logout, me."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_register_creates_user(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "a@x.com"


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter3"})
    assert r.status_code == 409


async def test_login_sets_jwt_cookies(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 200
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies


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


async def test_refresh_rotates_access_and_updates_session(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    old_access = client.cookies.get("access_token")
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 200, r.text
    assert client.cookies.get("access_token")
    assert client.cookies.get("access_token") != old_access


async def test_logout_clears_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 204
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401


async def test_mfa_login_requires_totp_and_magic_link(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})

    setup = await client.post("/api/v1/auth/mfa/setup")
    assert setup.status_code == 200, setup.text
    totp_code = setup.json()["dev_code"]
    enabled = await client.post("/api/v1/auth/mfa/verify-setup", json={"code": totp_code})
    assert enabled.status_code == 200, enabled.text
    backup_code = enabled.json()["backup_codes"][0]
    await client.post("/api/v1/auth/logout")

    login = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    assert login.status_code == 200, login.text
    assert login.json()["mfa_required"] is True
    magic_link = login.json()["dev_magic_link"]
    email_token = magic_link.split("token=", 1)[1]
    assert "access_token" not in login.cookies

    missing_magic_link = await client.post(
        "/api/v1/auth/login/verify-mfa",
        json={"totp_code": totp_code, "email_token": "wrong-token-value-that-is-long-enough"},
    )
    assert missing_magic_link.status_code == 401

    verified = await client.post(
        "/api/v1/auth/login/verify-mfa",
        json={"totp_code": totp_code, "email_token": email_token},
    )
    assert verified.status_code == 200, verified.text
    assert "access_token" in verified.cookies
    assert verified.json()["email"] == "a@x.com"

    await client.post("/api/v1/auth/logout")
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    reused = await client.post(
        "/api/v1/auth/login/verify-mfa",
        json={"totp_code": totp_code, "email_token": email_token},
    )
    assert reused.status_code == 401

    resent = await client.post("/api/v1/auth/login/resend-magic-link")
    assert resent.status_code == 200, resent.text
    backup_email_token = resent.json()["dev_magic_link"].split("token=", 1)[1]
    backup_verified = await client.post(
        "/api/v1/auth/login/verify-mfa",
        json={"totp_code": backup_code, "email_token": backup_email_token},
    )
    assert backup_verified.status_code == 200, backup_verified.text


async def test_password_reset_request_sends_email_and_changes_password(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[tuple[str, str, int]] = []

    async def fake_send(user, reset_link: str, expires_minutes: int) -> None:
        sent.append((user.email, reset_link, expires_minutes))

    monkeypatch.setattr("app.api.auth._new_email_token", lambda: "reset-token-123")
    monkeypatch.setattr("app.api.auth._send_password_reset_email", fake_send)

    await client.post("/api/v1/auth/register", json={"email": "reset@x.com", "password": "hunter2"})
    requested = await client.post("/api/v1/auth/password-reset/request", json={"email": "reset@x.com"})

    assert requested.status_code == 202, requested.text
    assert requested.json() == {"email_sent": True}
    assert sent == [("reset@x.com", "http://test/password-reset/confirm?token=reset-token-123", 60)]

    confirmed = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "reset-token-123", "new_password": "hunter3"},
    )
    assert confirmed.status_code == 204, confirmed.text

    old_login = await client.post("/api/v1/auth/login", json={"email": "reset@x.com", "password": "hunter2"})
    assert old_login.status_code == 401
    new_login = await client.post("/api/v1/auth/login", json={"email": "reset@x.com", "password": "hunter3"})
    assert new_login.status_code == 200, new_login.text

    reused = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "reset-token-123", "new_password": "hunter4"},
    )
    assert reused.status_code == 400


async def test_password_reset_request_for_unknown_email_is_generic(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []

    async def fake_send(user, reset_link: str, expires_minutes: int) -> None:
        sent.append(reset_link)

    monkeypatch.setattr("app.api.auth._send_password_reset_email", fake_send)

    requested = await client.post("/api/v1/auth/password-reset/request", json={"email": "missing@x.com"})

    assert requested.status_code == 202, requested.text
    assert requested.json() == {"email_sent": True}
    assert sent == []
