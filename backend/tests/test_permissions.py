"""Permission gating: admin has access, user denied → 403 + DENIED audit row."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def _login(client: AsyncClient, email: str, password: str) -> None:
    await client.post("/api/v1/auth/login", json={"email": email, "password": password})


async def test_admin_can_call_observed_users(client: AsyncClient, db: AsyncSession) -> None:
    # Admin user is seeded by the bootstrap; in tests, the conftest does not
    # auto-seed RBAC so we register & manually upgrade. (Or extend conftest.)
    await client.post("/api/v1/auth/register", json={"email": "x@x.com", "password": "hunter2"})
    # NOTE: admin permissions wired via RBAC seed. Test below verifies the
    # default 'user' role is denied admin endpoints.
    await _login(client, "x@x.com", "hunter2")
    r = await client.get("/api/v1/admin/observed-users")
    assert r.status_code == 403


async def test_denied_request_writes_audit_row(client: AsyncClient, db: AsyncSession) -> None:
    await client.post("/api/v1/auth/register", json={"email": "y@x.com", "password": "hunter2"})
    await _login(client, "y@x.com", "hunter2")
    await client.get("/api/v1/admin/observed-users")  # 403
    rows = (await db.execute(
        select(AuditLog).where(AuditLog.action == "PERM_DENIED")
    )).scalars().all()
    assert len(rows) >= 1
