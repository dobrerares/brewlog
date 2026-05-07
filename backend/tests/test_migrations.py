"""Migration round-trip and table presence tests."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


EXPECTED_TABLES = {
    "users", "roles", "permissions", "user_roles", "role_permissions", "sessions",
    "roasters", "beans", "equipment", "brewlogs",
    "tasting_notes", "bean_tasting_notes", "brewlog_tasting_notes",
    "audit_log",
}


async def test_all_14_tables_present(db: AsyncSession) -> None:
    rows = (await db.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    )).scalars().all()
    found = set(rows)
    missing = EXPECTED_TABLES - found
    assert not missing, f"missing tables: {missing}"


async def test_detection_function_present(db: AsyncSession) -> None:
    row = (await db.execute(
        text("SELECT proname FROM pg_proc WHERE proname = 'detect_malicious'")
    )).scalar_one_or_none()
    assert row == "detect_malicious"


async def test_audit_trigger_present(db: AsyncSession) -> None:
    row = (await db.execute(
        text("SELECT tgname FROM pg_trigger WHERE tgname = 'audit_log_after_insert'")
    )).scalar_one_or_none()
    assert row == "audit_log_after_insert"


async def test_partial_indexes_present(db: AsyncSession) -> None:
    rows = (await db.execute(
        text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
    )).scalars().all()
    assert "ix_users_observed_partial" in rows
    assert "ix_audit_action_time_failed" in rows
