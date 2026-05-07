"""Audit middleware writes FAIL/DENIED rows; helper writes OK rows; trigger fires."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def test_helper_writes_ok_row(db: AsyncSession) -> None:
    from app.services.audit import write_audit
    await write_audit(db, user_id=None, action="TEST_ACTION", status="OK")
    rows = (await db.execute(select(AuditLog).where(AuditLog.action == "TEST_ACTION"))).scalars().all()
    assert len(rows) == 1 and rows[0].status == "OK"
