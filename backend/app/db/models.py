"""SQLAlchemy ORM classes mirroring the schema in docs/plans/2026-05-06-…design.md §4.1.

One class per table. No business logic here — that lives in repositories and Pydantic
schemas. Indexes and constraints declared inline so Alembic autogenerate picks them up.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ─── Auth ──────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_observed: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    observed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", lazy="selectin")

    __table_args__ = (
        Index("ix_users_observed_partial", "id", postgresql_where="is_observed = true"),
    )


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_expires_at", "expires_at"),
    )


# ─── Entities ──────────────────────────────────────────────────────

class Roaster(Base):
    __tablename__ = "roasters"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Bean(Base):
    __tablename__ = "beans"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    roaster_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("roasters.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    origin_country: Mapped[str] = mapped_column(String(80), nullable=False)
    origin_region: Mapped[str | None] = mapped_column(String(80), nullable=True)
    process: Mapped[str] = mapped_column(String(40), nullable=False)
    roast_level: Mapped[str] = mapped_column(String(40), nullable=False)
    variety: Mapped[str | None] = mapped_column(String(80), nullable=True)
    elevation_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_date: Mapped["datetime | None"] = mapped_column(Date, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_beans_user_name", "user_id", "name"),
        Index("ix_beans_roaster", "roaster_id"),
    )


class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    grind_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    grind_range: Mapped[str | None] = mapped_column(String(80), nullable=True)
    grind_unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Brewlog(Base):
    __tablename__ = "brewlogs"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    bean_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("beans.id", ondelete="RESTRICT"), nullable=False
    )
    equipment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False
    )
    grinder_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grind_setting: Mapped[str] = mapped_column(String(40), nullable=False)
    method: Mapped[str] = mapped_column(String(40), nullable=False)
    dose_g: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    water_g: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    water_temp_c: Mapped[int] = mapped_column(Integer, nullable=False)
    brew_time_s: Mapped[int] = mapped_column(Integer, nullable=False)
    yield_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    taste_result: Mapped[str | None] = mapped_column(String(40), nullable=True)
    grind_adjustment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_brewlogs_user_date", "user_id", "date"),
        Index("ix_brewlogs_bean", "bean_id"),
        Index("ix_brewlogs_equipment", "equipment_id"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_brewlogs_rating_range"),
    )


# ─── Tasting notes ────────────────────────────────────────────────

class TastingNote(Base):
    __tablename__ = "tasting_notes"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    label: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)


class BeanTastingNote(Base):
    __tablename__ = "bean_tasting_notes"
    bean_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("beans.id", ondelete="CASCADE"), primary_key=True
    )
    tasting_note_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tasting_notes.id", ondelete="CASCADE"), primary_key=True
    )


class BrewlogTastingNote(Base):
    __tablename__ = "brewlog_tasting_notes"
    brewlog_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("brewlogs.id", ondelete="CASCADE"), primary_key=True
    )
    tasting_note_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tasting_notes.id", ondelete="CASCADE"), primary_key=True
    )


# ─── Audit ────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    role_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    resource_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    audit_metadata: Mapped[dict] = mapped_column("metadata", JSONB, server_default="{}", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_user_time", "user_id", "created_at"),
        Index(
            "ix_audit_action_time_failed",
            "action",
            "created_at",
            postgresql_where="status IN ('FAIL','DENIED')",
        ),
    )
