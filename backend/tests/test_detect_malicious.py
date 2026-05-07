"""Detection trigger — four heuristic scenarios at threshold and threshold+1."""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, User


async def _make_user(db: AsyncSession, email: str = "t@x.com") -> User:
    u = User(email=email, password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def _insert_audit(
    db: AsyncSession, user_id, action: str, status: str = "OK"
) -> None:
    await db.execute(
        text(
            "INSERT INTO audit_log (user_id, action, status) "
            "VALUES (:uid, :action, :status)"
        ),
        {"uid": str(user_id), "action": action, "status": status},
    )


async def _refresh(db: AsyncSession, user_id) -> User:
    return (
        await db.execute(
            select(User).where(User.id == user_id).execution_options(populate_existing=True)
        )
    ).scalar_one()


async def test_failed_login_burst_just_below_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(4):
        await _insert_audit(db, u.id, "LOGIN_FAIL", "FAIL")
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is False


async def test_failed_login_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(5):
        await _insert_audit(db, u.id, "LOGIN_FAIL", "FAIL")
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is True
    assert "failed-login-burst" in fresh.observed_reason


async def test_perm_denied_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(5):
        await _insert_audit(db, u.id, "PERM_DENIED", "DENIED")
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is True
    assert "permission-denied-burst" in fresh.observed_reason


async def test_mass_mutate_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for i in range(20):
        await _insert_audit(db, u.id, "BREWLOG_CREATE", "OK")
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is True
    assert "mass-mutation-burst" in fresh.observed_reason


async def test_mass_delete_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(10):
        await _insert_audit(db, u.id, "BREWLOG_DELETE", "OK")
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is True


async def test_observed_user_does_not_re_trigger(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(5):
        await _insert_audit(db, u.id, "LOGIN_FAIL", "FAIL")
    await db.commit()
    first = await _refresh(db, u.id)
    first_reason = first.observed_reason

    # Now flood with mass-deletes; reason should NOT change
    for _ in range(10):
        await _insert_audit(db, u.id, "BREWLOG_DELETE", "OK")
    await db.commit()
    second = await _refresh(db, u.id)
    assert second.observed_reason == first_reason  # idempotent observation


async def test_system_row_does_not_recurse(db: AsyncSession) -> None:
    u = await _make_user(db)
    # Direct SYSTEM insert — must not fire the trigger
    await db.execute(
        text(
            "INSERT INTO audit_log (user_id, action, status, metadata) "
            "VALUES (:uid, 'OBSERVED_AUTO', 'SYSTEM', '{}')"
        ),
        {"uid": str(u.id)},
    )
    await db.commit()
    fresh = await _refresh(db, u.id)
    assert fresh.is_observed is False
