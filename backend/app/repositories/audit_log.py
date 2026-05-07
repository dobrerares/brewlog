"""Audit-log repository — write + filtered read."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.repositories.base import AsyncRepository


class AuditLogRepository(AsyncRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AuditLog, session)

    async def write(
        self,
        *,
        user_id: UUID | None,
        action: str,
        status: str = "OK",
        role_snapshot: str | None = None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        row = AuditLog(
            user_id=user_id,
            action=action,
            status=status,
            role_snapshot=role_snapshot,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            audit_metadata=metadata or {},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def filter(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if since is not None:
            stmt = stmt.where(AuditLog.created_at >= since)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def recent_for_user(self, user_id: UUID, limit: int = 50) -> list[AuditLog]:
        rows = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())
