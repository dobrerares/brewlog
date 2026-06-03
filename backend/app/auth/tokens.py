"""Small HS256 JWT helper for auth cookies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID


class TokenError(ValueError):
    pass


def access_minutes() -> int:
    return int(os.environ.get("ACCESS_TOKEN_MINUTES", "10"))


def refresh_hours() -> int:
    return int(os.environ.get("REFRESH_TOKEN_HOURS", "24"))


def idle_minutes() -> int:
    return int(os.environ.get("REFRESH_IDLE_MINUTES", "15"))


def cookie_secure() -> bool:
    return os.environ.get("AUTH_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}


def cookie_samesite() -> str:
    value = os.environ.get("AUTH_COOKIE_SAMESITE", "lax").lower()
    if value not in {"lax", "strict", "none"}:
        return "lax"
    return value


def _secret() -> bytes:
    return os.environ.get("JWT_SECRET", os.environ.get("SESSION_SECRET", "dev-secret-change-me")).encode()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64url(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def jwt_encode(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    head = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str).encode())
    signing_input = f"{head}.{body}".encode()
    sig = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    return f"{head}.{body}.{_b64url(sig)}"


def jwt_decode(token: str, expected_type: str) -> dict[str, Any]:
    try:
        head, body, sig = token.split(".")
    except ValueError as exc:
        raise TokenError("malformed token") from exc
    signing_input = f"{head}.{body}".encode()
    expected_sig = _b64url(hmac.new(_secret(), signing_input, hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected_sig):
        raise TokenError("bad signature")
    try:
        payload = json.loads(_unb64url(body))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("malformed payload") from exc
    if payload.get("type") != expected_type:
        raise TokenError("wrong token type")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("token expired")
    return payload


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def make_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    email: str,
    roles: list[str],
    permissions: list[str],
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=access_minutes())
    return jwt_encode(
        {
            "sub": str(user_id),
            "sid": str(session_id),
            "email": email,
            "roles": roles,
            "permissions": permissions,
            "jti": secrets.token_urlsafe(12),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "type": "access",
        }
    )


def make_refresh_token(*, user_id: UUID, session_id: UUID) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=refresh_hours())
    token = jwt_encode(
        {
            "sub": str(user_id),
            "sid": str(session_id),
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "type": "refresh",
        }
    )
    return token, exp
