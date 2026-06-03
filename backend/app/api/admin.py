"""Admin-only endpoints — observation list + audit log explorer."""

from __future__ import annotations

import secrets
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from faker import Faker
import httpx
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.passwords import hash_password
from app.auth.permissions import (
    PERM_GENERATOR,
    PERM_LOG_READ,
    PERM_SECURITY_ANALYZE,
    PERM_USER_OBSERVE,
    PERM_USER_RESET,
)
from app.auth.tokens import token_hash
from app.db.models import (
    AuditLog,
    Bean,
    BeanTastingNote,
    Brewlog,
    BrewlogTastingNote,
    Equipment,
    PasswordResetToken,
    Roaster,
    TastingNote,
    User,
)
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


class AdminUserOut(BaseModel):
    id: UUID
    email: str
    roles: list[str]
    mfa_enabled: bool
    is_observed: bool


class PasswordResetOut(BaseModel):
    token: str
    expires_at: datetime


class DemoDataIn(BaseModel):
    users: int = Field(10, ge=1, le=500)
    brewlogs_per_user: int = Field(20, ge=1, le=1000)


class DemoDataOut(BaseModel):
    users: int
    roasters: int
    beans: int
    equipment: int
    brewlogs: int


class SecurityAnalysisOut(BaseModel):
    user_id: UUID
    risk: str
    observed: bool
    reason: str
    source: str


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


@router.get("/users", response_model=list[AdminUserOut])
async def list_users_for_admin(
    q: str | None = Query(default=None, max_length=120),
    admin: User = Depends(requires(PERM_USER_RESET)),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserOut]:
    stmt = select(User).order_by(User.email).limit(100)
    if q:
        stmt = select(User).where(User.email.ilike(f"%{q}%")).order_by(User.email).limit(100)
    rows = (await db.execute(stmt)).scalars().all()
    out: list[AdminUserOut] = []
    for user in rows:
        loaded = await UserRepository(db).get_with_perms(user.id)
        if loaded is None:
            continue
        out.append(
            AdminUserOut(
                id=loaded.id,
                email=loaded.email,
                roles=[role.name for role in loaded.roles],
                mfa_enabled=loaded.mfa_enabled,
                is_observed=loaded.is_observed,
            )
        )
    return out


@router.post("/users/{user_id}/password-reset", response_model=PasswordResetOut)
async def issue_password_reset(
    user_id: UUID,
    admin: User = Depends(requires(PERM_USER_RESET)),
    db: AsyncSession = Depends(get_db),
) -> PasswordResetOut:
    user = await UserRepository(db).get(user_id)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash(token),
            created_by_user_id=admin.id,
            expires_at=expires_at,
        )
    )
    await write_audit(
        db,
        user_id=admin.id,
        action="PASSWORD_RESET_ISSUE",
        status="OK",
        resource_type="user",
        resource_id=user.id,
    )
    await db.commit()
    return PasswordResetOut(token=token, expires_at=expires_at)


@router.post("/demo-data/generate", response_model=DemoDataOut)
async def generate_demo_data(
    payload: DemoDataIn,
    admin: User = Depends(requires(PERM_GENERATOR)),
    db: AsyncSession = Depends(get_db),
) -> DemoDataOut:
    fake = Faker()
    notes = ["chocolate", "citrus", "berry", "floral", "honey", "nutty", "tea", "stone fruit"]
    note_rows: dict[str, TastingNote] = {}
    for label in notes:
        row = (await db.execute(select(TastingNote).where(TastingNote.label == label))).scalar_one_or_none()
        if row is None:
            row = TastingNote(label=label)
            db.add(row)
            await db.flush()
        note_rows[label] = row

    counts = DemoDataOut(users=0, roasters=0, beans=0, equipment=0, brewlogs=0)
    for i in range(payload.users):
        user = User(email=f"demo-{secrets.token_hex(4)}@brewlog.ro", password_hash=hash_password("demo1234"))
        db.add(user)
        await db.flush()
        counts.users += 1

        roaster = Roaster(user_id=user.id, name=f"{fake.company()} Coffee", location=fake.city())
        brewer = Equipment(user_id=user.id, name="Hario V60", type="Brewer", brand="Hario", model="02")
        grinder = Equipment(
            user_id=user.id,
            name="Comandante C40",
            type="Grinder",
            brand="Comandante",
            model="MK4",
            grind_type="Stepped",
            grind_range="clicks 0-40",
            grind_unit="click",
        )
        db.add_all([roaster, brewer, grinder])
        await db.flush()
        counts.roasters += 1
        counts.equipment += 2

        bean = Bean(
            user_id=user.id,
            roaster_id=roaster.id,
            name=f"{fake.city()} Lot {i + 1}",
            origin_country=fake.country(),
            process="Washed",
            roast_level="Light",
            elevation_m=1600,
        )
        db.add(bean)
        await db.flush()
        counts.beans += 1
        for label in notes[:3]:
            db.add(BeanTastingNote(bean_id=bean.id, tasting_note_id=note_rows[label].id))

        for _ in range(payload.brewlogs_per_user):
            brew = Brewlog(
                user_id=user.id,
                bean_id=bean.id,
                equipment_id=brewer.id,
                grinder_id=grinder.id,
                date=fake.date_time_between(start_date="-60d", end_date="now", tzinfo=timezone.utc),
                grind_setting=f"{secrets.randbelow(20) + 12} clicks",
                method="V60",
                dose_g=15,
                water_g=250,
                water_temp_c=94,
                brew_time_s=secrets.randbelow(140) + 120,
                rating=secrets.randbelow(3) + 3,
                taste_result="Balanced",
                notes=fake.sentence(),
            )
            db.add(brew)
            await db.flush()
            counts.brewlogs += 1
            for label in notes[3:6]:
                db.add(BrewlogTastingNote(brewlog_id=brew.id, tasting_note_id=note_rows[label].id))

    await write_audit(db, user_id=admin.id, action="DEMO_DATA_GENERATE", status="OK", metadata=counts.model_dump())
    await db.commit()
    return counts


@router.post("/security/analyze-user/{user_id}", response_model=SecurityAnalysisOut)
async def analyze_user(
    user_id: UUID,
    admin: User = Depends(requires(PERM_SECURITY_ANALYZE)),
    db: AsyncSession = Depends(get_db),
) -> SecurityAnalysisOut:
    user = await UserRepository(db).get(user_id)
    failed = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == user_id,
            AuditLog.status.in_(["FAIL", "DENIED"]),
            AuditLog.created_at > datetime.now(timezone.utc) - timedelta(minutes=15),
        )
    ) or 0
    deletes = await db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == user_id,
            AuditLog.action.like("%DELETE"),
            AuditLog.created_at > datetime.now(timezone.utc) - timedelta(minutes=15),
        )
    ) or 0
    risk = "high" if failed >= 5 or deletes >= 10 else "medium" if failed >= 2 else "low"
    reason = f"fallback rules: {failed} recent failed/denied requests, {deletes} deletes"
    source = "rules"
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": os.environ.get("OLLAMA_MODEL", "llama3.2"),
                    "stream": False,
                    "prompt": (
                        "Classify user security risk as low, medium, or high. "
                        f"Failed/denied in 15m: {failed}. Deletes in 15m: {deletes}. "
                        "Answer with one word and a short reason."
                    ),
                },
            )
        if resp.is_success:
            text = str(resp.json().get("response", "")).strip()
            lowered = text.lower()
            if "high" in lowered:
                risk = "high"
            elif "medium" in lowered:
                risk = "medium"
            elif "low" in lowered:
                risk = "low"
            if text:
                reason = text[:500]
                source = "ollama"
    except Exception:
        pass
    if risk in {"high", "medium"}:
        user.is_observed = True
        user.observed_reason = reason
        user.observed_at = datetime.now(timezone.utc)
    await write_audit(
        db,
        user_id=admin.id,
        action="SECURITY_ANALYZE_USER",
        status="OK",
        resource_type="user",
        resource_id=user_id,
        metadata={"risk": risk, "source": source},
    )
    await db.commit()
    return SecurityAnalysisOut(user_id=user_id, risk=risk, observed=user.is_observed, reason=reason, source=source)
