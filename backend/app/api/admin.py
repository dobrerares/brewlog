"""Admin-only endpoints — observation list + audit log explorer."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.permissions import PERM_LOG_READ, PERM_USER_OBSERVE
from app.db.models import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.users import UserRepository
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class ObservedUserOut(BaseModel):
    id: UUID
    email: EmailStr
    observed_reason: str | None
    observed_at: datetime | None
    recent_actions: list[dict]


class AuditRowOut(BaseModel):
    id: int
    user_id: UUID | None
    role_snapshot: str | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    status: str
    metadata: dict
    created_at: datetime


@router.get("/observed-users", response_model=list[ObservedUserOut])
async def list_observed(
    user: User = Depends(requires(PERM_USER_OBSERVE)),
    db: AsyncSession = Depends(get_db),
):
    users = await UserRepository(db).list_observed()
    audit = AuditLogRepository(db)
    out: list[ObservedUserOut] = []
    for u in users:
        recent = await audit.recent_for_user(u.id, limit=50)
        out.append(
            ObservedUserOut(
                id=u.id, email=u.email,
                observed_reason=u.observed_reason, observed_at=u.observed_at,
                recent_actions=[
                    {"action": r.action, "status": r.status, "created_at": r.created_at.isoformat()}
                    for r in recent
                ],
            )
        )
    return out


@router.post("/observed-users/{user_id}/clear", status_code=204)
async def clear_observation(
    user_id: UUID,
    user: User = Depends(requires(PERM_USER_OBSERVE)),
    db: AsyncSession = Depends(get_db),
):
    try:
        await UserRepository(db).clear_observation(user_id)
    except Exception:
        raise HTTPException(404, detail="user not found")
    await write_audit(
        db, user_id=user.id, action="OBSERVATION_CLEARED", status="OK",
        resource_type="user", resource_id=user_id,
    )
    await db.commit()


@router.get("/audit-log", response_model=list[AuditRowOut])
async def list_audit_log(
    user_id: UUID | None = None,
    action: str | None = None,
    since: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    user: User = Depends(requires(PERM_LOG_READ)),
    db: AsyncSession = Depends(get_db),
):
    rows = await AuditLogRepository(db).filter(
        user_id=user_id, action=action, since=since,
        limit=page_size, offset=(page - 1) * page_size,
    )
    return [
        AuditRowOut(
            id=r.id, user_id=r.user_id, role_snapshot=r.role_snapshot,
            action=r.action, resource_type=r.resource_type, resource_id=r.resource_id,
            status=r.status, metadata=r.audit_metadata, created_at=r.created_at,
        )
        for r in rows
    ]
