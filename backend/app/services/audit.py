"""Audit-log helper + FastAPI middleware.

Two writers, no overlap (per design §7.3):
- write_audit() — explicit, semantic OK rows from endpoint code.
- AuditFailuresMiddleware — automatic FAIL/DENIED rows from response status codes.

USER CONTRIBUTION CHECKPOINT:
EXEMPT_PATHS controls which paths the failure middleware ignores. Health
checks, docs, metrics, and the WebSocket handshake should typically be
exempt — populate the list according to the routes you don't want polluting
the audit log.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.db.base import session_factory
from app.repositories.audit_log import AuditLogRepository

EXEMPT_PATHS: tuple[str, ...] = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/ws",
)


async def write_audit(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    action: str,
    status: str = "OK",
    role_snapshot: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Convenience wrapper. Endpoint code should call this AFTER the operation succeeds."""
    await AuditLogRepository(db).write(
        user_id=user_id, action=action, status=status,
        role_snapshot=role_snapshot, resource_type=resource_type, resource_id=resource_id,
        ip_address=ip_address, metadata=metadata,
    )


class AuditFailuresMiddleware(BaseHTTPMiddleware):
    """Writes audit rows for 401 and 403 responses."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        for prefix in EXEMPT_PATHS:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        response = await call_next(request)

        if response.status_code in (401, 403):
            status = "FAIL" if response.status_code == 401 else "DENIED"
            user = getattr(request.state, "user", None)
            user_id = getattr(user, "id", None)
            try:
                async with session_factory()() as session:
                    await AuditLogRepository(session).write(
                        user_id=user_id,
                        action=f"HTTP_{request.method}",
                        status=status,
                        ip_address=request.client.host if request.client else None,
                        metadata={"path": request.url.path, "code": response.status_code},
                    )
                    await session.commit()
            except Exception:  # noqa: BLE001
                # Audit writes must never break the response chain.
                pass

        return response
