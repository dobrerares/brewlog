"""TOTP and backup-code helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time

from app.auth.passwords import hash_password, verify_password


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def new_backup_codes(count: int = 8) -> list[str]:
    return [f"{secrets.randbelow(10**8):08d}" for _ in range(count)]


def hash_backup_code(code: str) -> str:
    return hash_password(code)


def verify_backup_code(code: str, hashed: str) -> bool:
    return verify_password(code, hashed)


def totp_uri(*, email: str, secret: str, issuer: str = "BrewLog") -> str:
    return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


def _secret_bytes(secret: str) -> bytes:
    return base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)


def _totp_at(secret: str, for_time: int) -> str:
    counter = int(for_time / 30)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(_secret_bytes(secret), msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1_000_000:06d}"


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    if not code.isdigit():
        return False
    now = int(time.time())
    return any(hmac.compare_digest(_totp_at(secret, now + step * 30), code) for step in range(-window, window + 1))


def dev_totp_code(secret: str) -> str:
    if os.environ.get("ALLOW_DEV_TOTP_CODE", "true").lower() in {"1", "true", "yes"}:
        return _totp_at(secret, int(time.time()))
    return ""
