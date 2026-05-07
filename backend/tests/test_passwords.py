"""Password hashing tests — bcrypt round-trip + tampering rejection."""

from __future__ import annotations

from app.auth.passwords import hash_password, verify_password


def test_hash_then_verify_succeeds() -> None:
    h = hash_password("hunter2")
    assert verify_password("hunter2", h)


def test_verify_fails_on_wrong_password() -> None:
    h = hash_password("hunter2")
    assert not verify_password("hunter3", h)


def test_hash_is_not_plaintext() -> None:
    h = hash_password("hunter2")
    assert "hunter2" not in h and len(h) > 30


def test_two_hashes_for_same_password_differ() -> None:
    """bcrypt salts each hash."""
    assert hash_password("x") != hash_password("x")
