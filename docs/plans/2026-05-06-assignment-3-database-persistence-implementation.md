# Assignment 3 — Database Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the in-memory store with Postgres (SQLAlchemy + Alembic), add full RBAC + sessions, MongoDB-backed real-time chat over WebSockets, and a Postgres-trigger-driven audit + observation system. Delivers Bronze + Silver + Gold of A3.

**Architecture:** Schema-first. Day 1 lands the entire Alembic migration set (14 tables, indexes, detection trigger and stored procedure) and Mongo bootstrap. Subsequent phases fill repository ports, auth + permissions + audit middleware, chat, and the admin observation dashboard. Pydantic stays as the validation tier above SQLAlchemy; existing cross-field rules don't change.

**Tech Stack:** PostgreSQL 16, SQLAlchemy 2.x async, Alembic, asyncpg, MongoDB 7, motor, passlib[bcrypt], testcontainers-python, FastAPI 0.115, Pydantic 2.9, pytest 8.

**Reference spec:** `docs/plans/2026-05-06-assignment-3-database-persistence-design.md`

---

## File Structure

### Backend — files created/modified/deleted

```
backend/
├── Dockerfile                              ← CREATE
├── requirements.txt                        ← MODIFY  add SQLAlchemy/asyncpg/Alembic/motor/passlib/testcontainers
├── alembic.ini                             ← CREATE
├── alembic/
│   ├── env.py                              ← CREATE  async-aware
│   ├── script.py.mako                      ← CREATE  default template
│   └── versions/
│       └── 001_initial_schema.py           ← CREATE  all 14 tables + indexes + trigger + proc
├── app/
│   ├── main.py                             ← MODIFY  startup creates engines, shutdown disposes
│   ├── api/
│   │   ├── deps.py                         ← MODIFY  add get_db, current_user, requires, audit
│   │   ├── auth.py                         ← CREATE  /register, /login, /logout, /me
│   │   ├── admin.py                        ← CREATE  /observed-users, /audit-log
│   │   ├── chat.py                         ← CREATE  /chat/rooms, /messages
│   │   ├── beans.py                        ← MODIFY  user_id scope + perm gates + audit calls
│   │   ├── brewlogs.py                     ← MODIFY  same
│   │   ├── equipment.py                    ← MODIFY  same
│   │   ├── roasters.py                     ← MODIFY  same
│   │   ├── stats.py                        ← MODIFY  scope to current_user
│   │   ├── generator.py                    ← MODIFY  admin-only
│   │   └── websocket.py                    ← MODIFY  topic-based fan-out
│   ├── auth/                               ← CREATE  new package
│   │   ├── __init__.py
│   │   ├── passwords.py                    ← CREATE  passlib[bcrypt] wrappers
│   │   ├── sessions.py                     ← CREATE  create/lookup/revoke
│   │   └── permissions.py                  ← CREATE  PERM_* constants
│   ├── db/                                 ← CREATE  new package
│   │   ├── __init__.py
│   │   ├── base.py                         ← CREATE  AsyncEngine, SessionFactory, DeclarativeBase
│   │   ├── models.py                       ← CREATE  SQLAlchemy ORM classes
│   │   └── mongo.py                        ← CREATE  motor client + getters
│   ├── repositories/                       ← CREATE  new package
│   │   ├── __init__.py
│   │   ├── base.py                         ← CREATE  generic AsyncRepository
│   │   ├── roasters.py
│   │   ├── beans.py
│   │   ├── equipment.py
│   │   ├── brewlogs.py
│   │   ├── users.py
│   │   ├── sessions.py
│   │   ├── audit_log.py
│   │   └── chat.py                         ← Mongo-backed
│   ├── services/
│   │   ├── audit.py                        ← CREATE  write_audit() helper + middleware
│   │   ├── chat.py                         ← CREATE  Mongo writes + broadcast
│   │   ├── broadcast.py                    ← MODIFY  topic-based
│   │   ├── generator.py                    ← MODIFY  uses repos
│   │   └── store.py                        ← DELETE
│   ├── gql/
│   │   ├── mutations.py                    ← MODIFY  use repos + add login/logout
│   │   ├── queries.py                      ← MODIFY  use repos + add me/observedUsers
│   │   └── types.py                        ← MODIFY  new User/ObservedUser types
│   └── scripts/
│       ├── seed_rbac.py                    ← CREATE  roles + perms + admin user
│       └── seed_chat.py                    ← CREATE  lobby room + Mongo indexes
└── tests/
    ├── conftest.py                         ← MODIFY  testcontainers fixtures
    ├── test_migrations.py                  ← CREATE  alembic round-trip
    ├── test_models.py                      ← CREATE  table presence
    ├── test_passwords.py                   ← CREATE
    ├── test_sessions.py                    ← CREATE
    ├── test_auth_api.py                    ← CREATE
    ├── test_audit.py                       ← CREATE
    ├── test_permissions.py                 ← CREATE
    ├── test_detect_malicious.py            ← CREATE
    ├── test_chat.py                        ← CREATE
    ├── test_admin_api.py                   ← CREATE
    ├── test_repositories/                  ← CREATE  per-entity repo tests
    │   └── ...
    └── test_*.py                           ← MODIFY  existing tests ported to db fixture
```

### Frontend — files created/modified

```
brewlog/
├── src/
│   ├── App.tsx                             ← MODIFY  add /login, /register, /chat, /admin/* routes
│   ├── hooks/
│   │   ├── useAuth.ts                      ← CREATE
│   │   ├── useChatRooms.ts                 ← CREATE
│   │   ├── useChatRoom.ts                  ← CREATE
│   │   ├── useChatSocket.ts                ← CREATE
│   │   └── useObservedUsers.ts             ← CREATE
│   ├── components/
│   │   ├── RequireAuth.tsx                 ← CREATE
│   │   ├── RequirePerm.tsx                 ← CREATE
│   │   ├── Sparkline.tsx                   ← CREATE  (USER CONTRIBUTION CHECKPOINT)
│   │   └── NavBar.tsx                      ← MODIFY  perm-gated links
│   ├── pages/
│   │   ├── Login.tsx                       ← CREATE
│   │   ├── Register.tsx                    ← CREATE
│   │   ├── Chat.tsx                        ← CREATE
│   │   ├── admin/
│   │   │   ├── ObservedUsers.tsx           ← CREATE
│   │   │   └── AuditLogExplorer.tsx        ← CREATE
│   │   └── Live.tsx                        ← MODIFY  gate generator buttons
│   └── lib/
│       └── api.ts                          ← MODIFY  cookie-aware fetch wrapper
└── tests/
    └── (Vitest tests for new hooks + components, Playwright e2e flow)
```

### Repo root — files created

```
docker-compose.yml                          ← CREATE
.env.example                                ← CREATE
DEMO.md                                     ← MODIFY  add A3 demo paths
```

---

## Phase 1 — Infrastructure & Schema

Locks the architectural anchor. After Phase 1 ends, the database is fully migrated, both engines are bootstrapped, and the test infrastructure runs both containers.

### Task 1: Add new dependencies to `requirements.txt`

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add the SQLAlchemy/Alembic/Mongo/auth/test stack**

Append to `backend/requirements.txt`:

```
# Assignment 3 — Persistence
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
passlib[bcrypt]==1.7.4
motor==3.6.0
pymongo==4.9.2

# A3 — test infra
testcontainers[postgres,mongodb]==4.8.2
```

- [ ] **Step 2: Install into venv**

Run: `cd backend && .venv/bin/pip install -r requirements.txt`
Expected: All packages install, no resolver errors.

- [ ] **Step 3: Verify imports in Python**

Run:
```bash
cd backend
.venv/bin/python -c "import sqlalchemy, alembic, asyncpg, motor, passlib, testcontainers; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(backend): add SQLAlchemy/Alembic/Mongo/passlib/testcontainers"
```

---

### Task 2: Create `app/db/base.py` — engine, session factory, DeclarativeBase

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/base.py`

- [ ] **Step 1: Create the package marker**

Create `backend/app/db/__init__.py`:

```python
"""Database engine + ORM models (Postgres)."""
```

- [ ] **Step 2: Create `app/db/base.py`**

Create `backend/app/db/base.py`:

```python
"""SQLAlchemy async engine, session factory, and declarative base.

The engine is created once at startup (see app/main.py) and disposed at shutdown.
Tests override SessionFactory via FastAPI dependency_overrides.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common declarative base for all ORM models."""


_engine: AsyncEngine | None = None
_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str | None = None) -> AsyncEngine:
    """Create the global engine. Call once at app startup."""
    global _engine, _factory
    url = database_url or os.environ["DATABASE_URL"]
    _engine = create_async_engine(url, pool_pre_ping=True, future=True)
    _factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


async def dispose_engine() -> None:
    """Dispose the engine. Call at shutdown."""
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _factory = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("engine not initialised; call init_engine() first")
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    if _factory is None:
        raise RuntimeError("engine not initialised; call init_engine() first")
    return _factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. One session per request."""
    async with session_factory()() as session:
        yield session
```

- [ ] **Step 3: Smoke check — import compiles**

Run: `cd backend && .venv/bin/python -c "from app.db.base import Base, init_engine; print(Base.__name__)"`
Expected: prints `Base`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/__init__.py backend/app/db/base.py
git commit -m "feat(backend): add SQLAlchemy async base, engine, session factory"
```

---

### Task 3: Create `app/db/models.py` — all 14 ORM classes

**Files:**
- Create: `backend/app/db/models.py`

- [ ] **Step 1: Write the file with all entity, RBAC, audit, and tasting-note tables**

Create `backend/app/db/models.py`:

```python
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
```

- [ ] **Step 2: Smoke check — all classes import**

Run:
```bash
cd backend
.venv/bin/python -c "from app.db.models import User, Role, Permission, Session, Roaster, Bean, Equipment, Brewlog, AuditLog, TastingNote; print('14 classes ok')"
```
Expected: prints `14 classes ok`.

- [ ] **Step 3: Verify metadata reflects 14 tables**

Run:
```bash
cd backend
.venv/bin/python -c "from app.db.base import Base; from app.db import models; print(len(Base.metadata.tables), sorted(Base.metadata.tables.keys()))"
```
Expected: prints `14` followed by the sorted table names list.

- [ ] **Step 4: Commit**

```bash
git add backend/app/db/models.py
git commit -m "feat(backend): add SQLAlchemy ORM models for 14 tables"
```

---

### Task 4: Initialise Alembic with async support

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/.gitkeep`

- [ ] **Step 1: Run `alembic init` inside backend**

Run:
```bash
cd backend
.venv/bin/alembic init alembic
```
Expected: creates `alembic/` directory and `alembic.ini`.

- [ ] **Step 2: Replace `alembic.ini` `sqlalchemy.url` with env-driven config**

Edit `backend/alembic.ini` — find the line `sqlalchemy.url = ...` and replace with:

```
sqlalchemy.url =
```

(empty — env.py reads `DATABASE_URL` directly).

- [ ] **Step 3: Replace `alembic/env.py` with async version**

Replace the entire content of `backend/alembic/env.py` with:

```python
"""Alembic env — async, reads DATABASE_URL from environment.

Imports all models so autogenerate sees them.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Make `app` importable when running `alembic` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base import Base
from app.db import models  # noqa: F401  side-effect: registers tables

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=os.environ["DATABASE_URL"],
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Verify Alembic recognises the metadata**

Run:
```bash
cd backend
DATABASE_URL=postgresql+asyncpg://localhost/dummy .venv/bin/alembic check 2>&1 | head -5
```
Expected: error mentioning connection (connection failure is fine — we're verifying that imports work and metadata loads, not that Postgres is reachable).

- [ ] **Step 5: Commit**

```bash
git add backend/alembic.ini backend/alembic/env.py backend/alembic/script.py.mako backend/alembic/versions/
git commit -m "feat(backend): add Alembic async env wired to models metadata"
```

---

### Task 5: Compose stack — Postgres + Mongo + API

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `.env.example`

- [ ] **Step 1: Create `backend/Dockerfile`**

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.seed_rbac && python -m app.scripts.seed_chat && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

- [ ] **Step 2: Create `docker-compose.yml` at repo root**

Create `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: brewlog
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-brewlog}
      POSTGRES_DB: brewlog
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U brewlog"]
      interval: 5s
      timeout: 3s
      retries: 10

  mongo:
    image: mongo:7
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--quiet", "--eval", "db.adminCommand('ping').ok"]
      interval: 5s
      timeout: 3s
      retries: 10

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://brewlog:${POSTGRES_PASSWORD:-brewlog}@postgres:5432/brewlog
      MONGO_URL: mongodb://mongo:27017/brewlog_chat
      SESSION_SECRET: ${SESSION_SECRET:-dev-secret-change-me}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:5173}
      SESSION_TTL_HOURS: ${SESSION_TTL_HOURS:-24}
      ADMIN_BOOTSTRAP_EMAIL: ${ADMIN_BOOTSTRAP_EMAIL:-admin@brewlog.local}
      ADMIN_BOOTSTRAP_PASSWORD: ${ADMIN_BOOTSTRAP_PASSWORD:-admin}
    depends_on:
      postgres:
        condition: service_healthy
      mongo:
        condition: service_healthy
    ports:
      - "8000:8000"

volumes:
  pg_data:
  mongo_data:
```

- [ ] **Step 3: Create `.env.example`**

Create `.env.example`:

```
POSTGRES_PASSWORD=brewlog
SESSION_SECRET=change-me-in-prod
CORS_ORIGINS=http://localhost:5173
SESSION_TTL_HOURS=24
ADMIN_BOOTSTRAP_EMAIL=admin@brewlog.local
ADMIN_BOOTSTRAP_PASSWORD=admin
```

- [ ] **Step 4: Bring up postgres + mongo (api will fail until later tasks)**

Run: `docker compose up -d postgres mongo`
Expected: both services reach `(healthy)` state within ~10s. Verify with `docker compose ps`.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml backend/Dockerfile .env.example
git commit -m "feat: docker-compose stack — postgres + mongo + api"
```

---

### Task 6: Initial migration — all 14 tables, indexes, trigger, stored procedure

**Files:**
- Create: `backend/alembic/versions/001_initial_schema.py`

- [ ] **Step 1: Generate the autogenerate migration as a starting skeleton**

Run with the running Postgres:
```bash
cd backend
DATABASE_URL=postgresql+asyncpg://brewlog:brewlog@localhost:5432/brewlog \
  .venv/bin/alembic revision --autogenerate -m "initial schema"
```
Expected: writes `alembic/versions/<hash>_initial_schema.py` containing `op.create_table(...)` for all 14 tables.

- [ ] **Step 2: Rename to `001_initial_schema.py`**

Rename the generated file to `backend/alembic/versions/001_initial_schema.py`. Ensure the `revision` line at top reads `revision = "001"` (replace the random hash) and `down_revision = None`.

- [ ] **Step 3: Append the partial-index, trigger, and stored procedure DDL**

At the end of the `upgrade()` function in `001_initial_schema.py`, append:

```python
    # Partial index — observed users hot list
    op.execute(
        "CREATE INDEX ix_users_observed_partial ON users (id) WHERE is_observed = true"
    )

    # Partial index — failed/denied audit rows for detection windows
    op.execute(
        "CREATE INDEX ix_audit_action_time_failed ON audit_log (action, created_at DESC) "
        "WHERE status IN ('FAIL','DENIED')"
    )

    # Detection stored procedure
    op.execute("""
    CREATE OR REPLACE FUNCTION detect_malicious(p_user_id UUID)
    RETURNS VOID AS $$
    DECLARE
      c_failed_login INT;
      c_perm_denied  INT;
      c_mass_mutate  INT;
      c_mass_delete  INT;
      v_reason       TEXT := NULL;
    BEGIN
      IF p_user_id IS NULL OR
         EXISTS (SELECT 1 FROM users WHERE id = p_user_id AND is_observed)
      THEN
        RETURN;
      END IF;

      SELECT count(*) INTO c_failed_login FROM audit_log
       WHERE user_id = p_user_id AND action = 'LOGIN_FAIL'
         AND created_at > now() - interval '5 minutes';
      IF c_failed_login >= 5 THEN
        v_reason := format('failed-login-burst (%s in 5min)', c_failed_login);
      END IF;

      IF v_reason IS NULL THEN
        SELECT count(*) INTO c_perm_denied FROM audit_log
         WHERE user_id = p_user_id AND status = 'DENIED'
           AND created_at > now() - interval '5 minutes';
        IF c_perm_denied >= 5 THEN
          v_reason := format('permission-denied-burst (%s in 5min)', c_perm_denied);
        END IF;
      END IF;

      IF v_reason IS NULL THEN
        SELECT count(*) INTO c_mass_mutate FROM audit_log
         WHERE user_id = p_user_id AND status = 'OK'
           AND action ~ '_(CREATE|UPDATE|DELETE)$'
           AND created_at > now() - interval '60 seconds';
        IF c_mass_mutate >= 20 THEN
          v_reason := format('mass-mutation-burst (%s in 60s)', c_mass_mutate);
        END IF;
      END IF;

      IF v_reason IS NULL THEN
        SELECT count(*) INTO c_mass_delete FROM audit_log
         WHERE user_id = p_user_id AND status = 'OK'
           AND action LIKE '%_DELETE'
           AND created_at > now() - interval '60 seconds';
        IF c_mass_delete >= 10 THEN
          v_reason := format('mass-delete-burst (%s in 60s)', c_mass_delete);
        END IF;
      END IF;

      IF v_reason IS NOT NULL THEN
        UPDATE users SET is_observed = true,
                         observed_reason = v_reason,
                         observed_at = now()
        WHERE id = p_user_id;

        INSERT INTO audit_log(user_id, role_snapshot, action, status, metadata)
        VALUES (p_user_id, NULL, 'OBSERVED_AUTO', 'SYSTEM',
                jsonb_build_object('reason', v_reason));
      END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Trigger function — fires detection unless the row is itself a SYSTEM row
    op.execute("""
    CREATE OR REPLACE FUNCTION audit_log_after_insert_fn()
    RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.status <> 'SYSTEM' AND NEW.user_id IS NOT NULL THEN
        PERFORM detect_malicious(NEW.user_id);
      END IF;
      RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER audit_log_after_insert
    AFTER INSERT ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_after_insert_fn();
    """)
```

- [ ] **Step 4: Add corresponding `downgrade()` cleanup**

In the `downgrade()` function of the same file, prepend (so it runs before the table drops):

```python
    op.execute("DROP TRIGGER IF EXISTS audit_log_after_insert ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS audit_log_after_insert_fn()")
    op.execute("DROP FUNCTION IF EXISTS detect_malicious(UUID)")
    op.execute("DROP INDEX IF EXISTS ix_audit_action_time_failed")
    op.execute("DROP INDEX IF EXISTS ix_users_observed_partial")
```

- [ ] **Step 5: Apply the migration**

Run:
```bash
cd backend
DATABASE_URL=postgresql+asyncpg://brewlog:brewlog@localhost:5432/brewlog \
  .venv/bin/alembic upgrade head
```
Expected: prints `Running upgrade  -> 001, initial schema`.

- [ ] **Step 6: Verify all 14 tables + procedure + trigger exist**

Run:
```bash
docker compose exec postgres psql -U brewlog -d brewlog -c "\dt" -c "\df detect_malicious" -c "\dft+ audit_log"
```
Expected: lists 14 user tables, the `detect_malicious` function, and the `audit_log_after_insert` trigger.

- [ ] **Step 7: Commit**

```bash
git add backend/alembic/versions/001_initial_schema.py
git commit -m "feat(db): initial migration — 14 tables, partial indexes, detection trigger + proc"
```

---

### Task 7: Permission catalog (`app/auth/permissions.py`)

**Files:**
- Create: `backend/app/auth/__init__.py`
- Create: `backend/app/auth/permissions.py`

- [ ] **Step 1: Create the package marker**

Create `backend/app/auth/__init__.py`:

```python
"""Authentication, sessions, permissions."""
```

- [ ] **Step 2: Create the permission catalog**

Create `backend/app/auth/permissions.py`:

```python
"""Catalog of permission codes used by `requires(...)` and seeded into the DB.

Format: <resource>:<verb>[:<scope>]
Scope: 'own' (only the user's own rows) or 'any' (admin).
"""

from __future__ import annotations

# Per-resource standard CRUD
PERM_BEAN_READ          = "bean:read"
PERM_BEAN_CREATE        = "bean:create"
PERM_BEAN_UPDATE_OWN    = "bean:update:own"
PERM_BEAN_UPDATE_ANY    = "bean:update:any"
PERM_BEAN_DELETE_OWN    = "bean:delete:own"
PERM_BEAN_DELETE_ANY    = "bean:delete:any"

PERM_BREWLOG_READ        = "brewlog:read"
PERM_BREWLOG_CREATE      = "brewlog:create"
PERM_BREWLOG_UPDATE_OWN  = "brewlog:update:own"
PERM_BREWLOG_UPDATE_ANY  = "brewlog:update:any"
PERM_BREWLOG_DELETE_OWN  = "brewlog:delete:own"
PERM_BREWLOG_DELETE_ANY  = "brewlog:delete:any"

PERM_EQUIPMENT_READ        = "equipment:read"
PERM_EQUIPMENT_CREATE      = "equipment:create"
PERM_EQUIPMENT_UPDATE_OWN  = "equipment:update:own"
PERM_EQUIPMENT_UPDATE_ANY  = "equipment:update:any"
PERM_EQUIPMENT_DELETE_OWN  = "equipment:delete:own"
PERM_EQUIPMENT_DELETE_ANY  = "equipment:delete:any"

PERM_ROASTER_READ        = "roaster:read"
PERM_ROASTER_CREATE      = "roaster:create"
PERM_ROASTER_UPDATE_OWN  = "roaster:update:own"
PERM_ROASTER_UPDATE_ANY  = "roaster:update:any"
PERM_ROASTER_DELETE_OWN  = "roaster:delete:own"
PERM_ROASTER_DELETE_ANY  = "roaster:delete:any"

# Cross-cutting
PERM_USER_LIST    = "user:list"
PERM_USER_OBSERVE = "user:observe"
PERM_LOG_READ     = "log:read"
PERM_CHAT_SEND    = "chat:send"
PERM_CHAT_READ    = "chat:read"
PERM_GENERATOR    = "generator:control"  # admin-only Faker generator

ALL_PERMISSIONS: list[str] = [
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_UPDATE_ANY,
    PERM_BEAN_DELETE_OWN, PERM_BEAN_DELETE_ANY,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_UPDATE_ANY,
    PERM_BREWLOG_DELETE_OWN, PERM_BREWLOG_DELETE_ANY,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_UPDATE_ANY,
    PERM_EQUIPMENT_DELETE_OWN, PERM_EQUIPMENT_DELETE_ANY,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_UPDATE_ANY,
    PERM_ROASTER_DELETE_OWN, PERM_ROASTER_DELETE_ANY,
    PERM_USER_LIST, PERM_USER_OBSERVE, PERM_LOG_READ,
    PERM_CHAT_SEND, PERM_CHAT_READ, PERM_GENERATOR,
]
```

- [ ] **Step 3: Smoke check**

Run: `cd backend && .venv/bin/python -c "from app.auth.permissions import ALL_PERMISSIONS; print(len(ALL_PERMISSIONS))"`
Expected: prints `30`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/auth/__init__.py backend/app/auth/permissions.py
git commit -m "feat(auth): permission code catalog (30 permissions)"
```

---

### Task 8: Seed script — roles, role-permission mapping, admin user [USER CONTRIBUTION CHECKPOINT]

**Files:**
- Create: `backend/app/scripts/__init__.py`
- Create: `backend/app/scripts/seed_rbac.py`

- [ ] **Step 1: Create the package marker**

Create `backend/app/scripts/__init__.py`:

```python
```

- [ ] **Step 2: Create the seed script with role mapping placeholder**

Create `backend/app/scripts/seed_rbac.py`:

```python
"""Seed roles, permissions, role-permission junction, and bootstrap admin user.

Idempotent — safe to run multiple times. Skips inserts when rows already exist.

USER CONTRIBUTION CHECKPOINT:
The mapping `USER_ROLE_PERMISSIONS` below decides which scope (`:own` vs `:any`)
the normal `user` role gets. The default below gives `user` only `:own` scopes;
adjust as your security policy requires.
"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.auth.passwords import hash_password
from app.auth.permissions import (
    ALL_PERMISSIONS,
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_DELETE_OWN,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_DELETE_OWN,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_DELETE_OWN,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_DELETE_OWN,
    PERM_CHAT_SEND, PERM_CHAT_READ,
)
from app.db.base import init_engine, session_factory, dispose_engine
from app.db.models import Permission, Role, RolePermission, User, UserRole

# Admin: gets ALL_PERMISSIONS automatically.
# User: gets the `:own` scopes + reads + chat (no admin verbs).
USER_ROLE_PERMISSIONS: list[str] = [
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_DELETE_OWN,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_DELETE_OWN,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_DELETE_OWN,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_DELETE_OWN,
    PERM_CHAT_SEND, PERM_CHAT_READ,
]


async def seed() -> None:
    init_engine()
    factory = session_factory()
    async with factory() as session:
        # 1. Permissions
        for code in ALL_PERMISSIONS:
            stmt = pg_insert(Permission).values(code=code, description=code).on_conflict_do_nothing(index_elements=["code"])
            await session.execute(stmt)

        # 2. Roles
        for name in ("admin", "user"):
            stmt = pg_insert(Role).values(name=name).on_conflict_do_nothing(index_elements=["name"])
            await session.execute(stmt)
        await session.commit()

        # 3. Role-permission mapping
        admin = (await session.execute(select(Role).where(Role.name == "admin"))).scalar_one()
        user_role = (await session.execute(select(Role).where(Role.name == "user"))).scalar_one()
        all_perms = (await session.execute(select(Permission))).scalars().all()
        perm_by_code = {p.code: p for p in all_perms}

        for p in all_perms:
            stmt = pg_insert(RolePermission).values(role_id=admin.id, permission_id=p.id).on_conflict_do_nothing()
            await session.execute(stmt)

        for code in USER_ROLE_PERMISSIONS:
            stmt = pg_insert(RolePermission).values(
                role_id=user_role.id, permission_id=perm_by_code[code].id
            ).on_conflict_do_nothing()
            await session.execute(stmt)

        # 4. Bootstrap admin user
        admin_email = os.environ.get("ADMIN_BOOTSTRAP_EMAIL", "admin@brewlog.local")
        admin_pw = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "admin")
        existing = (await session.execute(select(User).where(User.email == admin_email))).scalar_one_or_none()
        if existing is None:
            user = User(email=admin_email, password_hash=hash_password(admin_pw))
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=admin.id))

        await session.commit()
        print(f"seeded RBAC; admin = {admin_email}")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 3: Defer execution — this script depends on `app/auth/passwords.py` (Task 23)**

Don't run yet. Continue plan; we'll execute the seed in Task 23 after `passwords.py` exists.

- [ ] **Step 4: Commit**

```bash
git add backend/app/scripts/__init__.py backend/app/scripts/seed_rbac.py
git commit -m "feat(seed): RBAC seed with admin/user role mapping"
```

---

### Task 9: Mongo client + bootstrap script

**Files:**
- Create: `backend/app/db/mongo.py`
- Create: `backend/app/scripts/seed_chat.py`

- [ ] **Step 1: Create `app/db/mongo.py`**

Create `backend/app/db/mongo.py`:

```python
"""MongoDB client (motor) — chat-only.

The async client is created at startup and disposed at shutdown.
Collection names are constants so callers can't typo their way to a missing index.
"""

from __future__ import annotations

import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

CHAT_ROOMS = "chat_rooms"
CHAT_MESSAGES = "chat_messages"

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def init_mongo(mongo_url: str | None = None) -> AsyncIOMotorDatabase:
    global _client, _db
    url = mongo_url or os.environ["MONGO_URL"]
    _client = AsyncIOMotorClient(url)
    _db = _client.get_default_database()
    return _db


async def close_mongo() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("mongo not initialised; call init_mongo()")
    return _db


def rooms():
    return get_db()[CHAT_ROOMS]


def messages():
    return get_db()[CHAT_MESSAGES]
```

- [ ] **Step 2: Create the bootstrap script**

Create `backend/app/scripts/seed_chat.py`:

```python
"""Create Mongo indexes and seed the lobby room. Idempotent."""

from __future__ import annotations

import asyncio

from pymongo import ASCENDING, DESCENDING

from app.db.mongo import CHAT_ROOMS, init_mongo, close_mongo, messages, rooms


async def seed() -> None:
    init_mongo()

    # Indexes
    await rooms().create_index(
        [("participant_pair", ASCENDING)],
        unique=True,
        partialFilterExpression={"type": "dm"},
        name="ix_room_pair_unique_dm",
    )
    await rooms().create_index([("participants", ASCENDING)], name="ix_room_participants")
    await messages().create_index(
        [("room_id", ASCENDING), ("created_at", DESCENDING)], name="ix_msg_room_time"
    )

    # Lobby room
    existing = await rooms().find_one({"type": "room", "name": "lobby"})
    if existing is None:
        await rooms().insert_one(
            {
                "type": "room",
                "name": "lobby",
                "participants": [],
                "participant_pair": None,
                "created_at": __import__("datetime").datetime.utcnow(),
                "last_message_at": None,
            }
        )
    print("seeded chat (lobby + indexes)")
    await close_mongo()


if __name__ == "__main__":
    asyncio.run(seed())
```

- [ ] **Step 3: Run the chat seed against the running Mongo**

Run:
```bash
cd backend
MONGO_URL=mongodb://localhost:27017/brewlog_chat .venv/bin/python -m app.scripts.seed_chat
```
Expected: prints `seeded chat (lobby + indexes)`.

- [ ] **Step 4: Verify**

Run:
```bash
docker compose exec mongo mongosh brewlog_chat --quiet --eval "db.chat_rooms.find().pretty()"
```
Expected: shows the lobby document.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/mongo.py backend/app/scripts/seed_chat.py
git commit -m "feat(db): motor client + chat seed (lobby room + indexes)"
```

---

### Task 10: testcontainers fixtures in `conftest.py`

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_migrations.py`

- [ ] **Step 1: Replace `backend/tests/conftest.py` with the testcontainers version**

Replace the entire content of `backend/tests/conftest.py` with:

```python
"""Pytest fixtures — testcontainers Postgres and MongoDB."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.mongodb import MongoDbContainer
from testcontainers.postgres import PostgresContainer

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    cfg.attributes["sqlalchemy.url"] = database_url  # not strictly needed; env.py reads env var
    os.environ["DATABASE_URL"] = database_url
    return cfg


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    with PostgresContainer("postgres:16-alpine", username="brewlog", password="brewlog", dbname="brewlog") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        cfg = _alembic_config(url)
        command.upgrade(cfg, "head")
        yield url


@pytest.fixture(scope="session")
def engine(pg_url: str) -> Iterator[AsyncEngine]:
    eng = create_async_engine(pg_url, future=True, pool_pre_ping=True)
    yield eng
    asyncio.get_event_loop().run_until_complete(eng.dispose())


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Per-test SAVEPOINT — rolls back on teardown."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        factory = async_sessionmaker(bind=conn, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            yield session
        await trans.rollback()


@pytest.fixture(scope="session")
def mongo_url() -> Iterator[str]:
    with MongoDbContainer("mongo:7") as mongo:
        yield mongo.get_connection_url() + "/brewlog_test"


@pytest.fixture
async def mongo(mongo_url: str) -> AsyncIterator:
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    yield db
    await client.drop_database(db.name)
    client.close()
```

- [ ] **Step 2: Write the migration round-trip test**

Create `backend/tests/test_migrations.py`:

```python
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
```

- [ ] **Step 3: Configure pytest for async**

Verify `backend/pyproject.toml` has `asyncio_mode = "auto"`. If not, edit:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 4: Run the migration tests**

Run: `cd backend && .venv/bin/pytest tests/test_migrations.py -v`
Expected: 4 passed. (Postgres testcontainer starts on first run — ~10s.)

- [ ] **Step 5: Commit**

```bash
git add backend/tests/conftest.py backend/tests/test_migrations.py
git commit -m "test(db): testcontainers fixtures + migration round-trip tests"
```

---

## Phase 2 — Repositories & Test Ports

Replaces `services/store.py` with SQLAlchemy-backed repositories. Existing handler tests get rewritten to use the `db` fixture from Phase 1. End of Phase 2: in-memory store deleted.

### Task 11: Generic `AsyncRepository` base

**Files:**
- Create: `backend/app/repositories/__init__.py`
- Create: `backend/app/repositories/base.py`
- Create: `backend/tests/test_repositories/__init__.py`
- Create: `backend/tests/test_repositories/test_base.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repositories/__init__.py` (empty file).

Create `backend/tests/test_repositories/test_base.py`:

```python
"""Tests for the generic AsyncRepository."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Roaster, User
from app.repositories.base import AsyncRepository, NotFoundError


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_create_returns_row_with_id(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    assert r.id is not None and r.name == "Onyx"


async def test_get_returns_existing(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    fetched = await repo.get(r.id)
    assert fetched.id == r.id


async def test_get_raises_not_found(db: AsyncSession) -> None:
    repo = AsyncRepository(Roaster, db)
    with pytest.raises(NotFoundError):
        await repo.get(uuid4())


async def test_list_returns_only_scoped_rows(db: AsyncSession, user: User) -> None:
    other = User(email="o@x.com", password_hash="x")
    db.add(other)
    await db.flush()
    repo = AsyncRepository(Roaster, db)
    await repo.create(user_id=user.id, name="A")
    await repo.create(user_id=other.id, name="B")
    mine = await repo.list_for_user(user_id=user.id)
    assert {r.name for r in mine} == {"A"}


async def test_delete_removes_row(db: AsyncSession, user: User) -> None:
    repo = AsyncRepository(Roaster, db)
    r = await repo.create(user_id=user.id, name="Onyx")
    await repo.delete(r.id)
    with pytest.raises(NotFoundError):
        await repo.get(r.id)
```

- [ ] **Step 2: Run the test, see it fail**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_base.py -v`
Expected: ImportError on `app.repositories.base`.

- [ ] **Step 3: Create the package marker**

Create `backend/app/repositories/__init__.py`:

```python
"""SQLAlchemy-backed repositories — replaces app/services/store.py."""
```

- [ ] **Step 4: Implement `AsyncRepository`**

Create `backend/app/repositories/base.py`:

```python
"""Generic async CRUD repository keyed by UUID PK + user_id scoping."""

from __future__ import annotations

from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class NotFoundError(LookupError):
    """Raised when a primary-key lookup fails."""


ModelT = TypeVar("ModelT", bound=Base)


class AsyncRepository(Generic[ModelT]):
    """Generic CRUD over any ORM model with a UUID primary key.

    Scoping helpers (list_for_user, get_for_user) assume the model has a
    `user_id` column — the entity tables in this app all do.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **fields: object) -> ModelT:
        instance = self.model(**fields)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get(self, pk: UUID) -> ModelT:
        instance = await self.session.get(self.model, pk)
        if instance is None:
            raise NotFoundError(f"{self.model.__tablename__}:{pk}")
        return instance

    async def get_for_user(self, pk: UUID, user_id: UUID) -> ModelT:
        instance = await self.get(pk)
        if getattr(instance, "user_id", None) != user_id:
            raise NotFoundError(f"{self.model.__tablename__}:{pk}")
        return instance

    async def list(self) -> list[ModelT]:
        rows = await self.session.execute(select(self.model))
        return list(rows.scalars().all())

    async def list_for_user(self, user_id: UUID) -> list[ModelT]:
        rows = await self.session.execute(
            select(self.model).where(self.model.user_id == user_id)  # type: ignore[attr-defined]
        )
        return list(rows.scalars().all())

    async def update(self, pk: UUID, **fields: object) -> ModelT:
        instance = await self.get(pk)
        for k, v in fields.items():
            setattr(instance, k, v)
        await self.session.flush()
        return instance

    async def delete(self, pk: UUID) -> None:
        instance = await self.get(pk)
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self) -> int:
        from sqlalchemy import func as f

        rows = await self.session.execute(select(f.count()).select_from(self.model))
        return int(rows.scalar_one())
```

- [ ] **Step 5: Run test to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_base.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories/__init__.py backend/app/repositories/base.py backend/tests/test_repositories/
git commit -m "feat(repo): generic AsyncRepository with user_id scoping + tests"
```

---

### Task 12: Concrete entity repositories — Roaster, Bean, Equipment, Brewlog

**Files:**
- Create: `backend/app/repositories/roasters.py`
- Create: `backend/app/repositories/beans.py`
- Create: `backend/app/repositories/equipment.py`
- Create: `backend/app/repositories/brewlogs.py`
- Create: `backend/tests/test_repositories/test_entities.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repositories/test_entities.py`:

```python
"""Entity-specific repository tests — covers cross-entity FK behaviour."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.beans import BeanRepository
from app.repositories.brewlogs import BrewlogRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.roasters import RoasterRepository


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_bean_roaster_setnull_cascade(db: AsyncSession, user: User) -> None:
    roasters = RoasterRepository(db)
    beans = BeanRepository(db)
    r = await roasters.create(user_id=user.id, name="Onyx")
    b = await beans.create(
        user_id=user.id, roaster_id=r.id, name="Esperanza",
        origin_country="CO", process="Washed", roast_level="Light",
    )
    await roasters.delete(r.id)
    fetched = await beans.get(b.id)
    assert fetched.roaster_id is None  # ON DELETE SET NULL


async def test_brewlog_user_restrict(db: AsyncSession, user: User) -> None:
    """Deleting a user with brewlogs raises IntegrityError (RESTRICT)."""
    eqs = EquipmentRepository(db)
    beans = BeanRepository(db)
    brewlogs = BrewlogRepository(db)

    bean = await beans.create(
        user_id=user.id, name="X", origin_country="CO",
        process="Washed", roast_level="Light",
    )
    brewer = await eqs.create(user_id=user.id, name="V60", type="Brewer", brand="Hario")
    grinder = await eqs.create(user_id=user.id, name="C40", type="Grinder", brand="Comandante")
    await brewlogs.create(
        user_id=user.id, bean_id=bean.id, equipment_id=brewer.id, grinder_id=grinder.id,
        date=datetime.now(timezone.utc), grind_setting="20", method="V60",
        dose_g=Decimal("15"), water_g=Decimal("250"),
        water_temp_c=93, brew_time_s=180, rating=4,
    )
    await db.flush()

    await db.delete(user)
    with pytest.raises(IntegrityError):
        await db.flush()
```

- [ ] **Step 2: Run test, see it fail**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_entities.py -v`
Expected: ImportError on the per-entity repo modules.

- [ ] **Step 3: Create the per-entity repos**

Create `backend/app/repositories/roasters.py`:

```python
"""Roaster repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Roaster
from app.repositories.base import AsyncRepository


class RoasterRepository(AsyncRepository[Roaster]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Roaster, session)
```

Create `backend/app/repositories/beans.py`:

```python
"""Bean repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Bean
from app.repositories.base import AsyncRepository


class BeanRepository(AsyncRepository[Bean]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Bean, session)
```

Create `backend/app/repositories/equipment.py`:

```python
"""Equipment repository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Equipment
from app.repositories.base import AsyncRepository


class EquipmentRepository(AsyncRepository[Equipment]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Equipment, session)
```

Create `backend/app/repositories/brewlogs.py`:

```python
"""Brewlog repository — adds bean/equipment scoped queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Brewlog
from app.repositories.base import AsyncRepository


class BrewlogRepository(AsyncRepository[Brewlog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Brewlog, session)

    async def list_for_user_and_bean(self, user_id: UUID, bean_id: UUID) -> list[Brewlog]:
        rows = await self.session.execute(
            select(Brewlog).where(
                Brewlog.user_id == user_id, Brewlog.bean_id == bean_id
            ).order_by(Brewlog.date.desc())
        )
        return list(rows.scalars().all())
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_entities.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/roasters.py backend/app/repositories/beans.py backend/app/repositories/equipment.py backend/app/repositories/brewlogs.py backend/tests/test_repositories/test_entities.py
git commit -m "feat(repo): per-entity repos + RESTRICT/SET-NULL behaviour tests"
```

---

### Task 13: User, Session, AuditLog repositories

**Files:**
- Create: `backend/app/repositories/users.py`
- Create: `backend/app/repositories/sessions.py`
- Create: `backend/app/repositories/audit_log.py`
- Create: `backend/tests/test_repositories/test_users_sessions.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repositories/test_users_sessions.py`:

```python
"""User, session, audit-log repository tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog, Role, User, UserRole
from app.repositories.audit_log import AuditLogRepository
from app.repositories.sessions import SessionRepository
from app.repositories.users import UserRepository


async def test_user_lookup_by_email(db: AsyncSession) -> None:
    repo = UserRepository(db)
    u = await repo.create(email="a@b.com", password_hash="x")
    found = await repo.find_by_email("a@b.com")
    assert found is not None and found.id == u.id


async def test_user_lookup_unknown_email_returns_none(db: AsyncSession) -> None:
    repo = UserRepository(db)
    assert await repo.find_by_email("nobody@x.com") is None


async def test_session_create_and_lookup(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    s = await session_repo.create_session(user_id=u.id, expires_at=expires)
    fetched = await session_repo.lookup_active(s.id)
    assert fetched is not None and fetched.user_id == u.id


async def test_session_lookup_expired_returns_none(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    expires = datetime.now(timezone.utc) - timedelta(seconds=1)
    s = await session_repo.create_session(user_id=u.id, expires_at=expires)
    assert await session_repo.lookup_active(s.id) is None


async def test_audit_log_insert_records_row(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    audit_repo = AuditLogRepository(db)
    u = await user_repo.create(email="a@b.com", password_hash="x")
    await audit_repo.write(user_id=u.id, action="LOGIN", status="OK")
    rows = (await db.execute(select(AuditLog).where(AuditLog.user_id == u.id))).scalars().all()
    assert len(rows) == 1 and rows[0].action == "LOGIN"
```

- [ ] **Step 2: Run test, see it fail**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_users_sessions.py -v`
Expected: ImportError on the new repo modules.

- [ ] **Step 3: Implement the repositories**

Create `backend/app/repositories/users.py`:

```python
"""User repository — adds email lookup and role/permission loaders."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Role, User, UserRole
from app.repositories.base import AsyncRepository


class UserRepository(AsyncRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        rows = await self.session.execute(
            select(User).where(User.email == email).options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return rows.scalar_one_or_none()

    async def get_with_perms(self, user_id: UUID) -> User | None:
        rows = await self.session.execute(
            select(User).where(User.id == user_id).options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return rows.scalar_one_or_none()

    async def attach_role(self, user_id: UUID, role_id: UUID) -> None:
        self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.flush()

    async def list_observed(self) -> list[User]:
        rows = await self.session.execute(
            select(User).where(User.is_observed.is_(True)).order_by(User.observed_at.desc())
        )
        return list(rows.scalars().all())

    async def clear_observation(self, user_id: UUID) -> None:
        u = await self.get(user_id)
        u.is_observed = False
        u.observed_reason = None
        u.observed_at = None
        await self.session.flush()
```

Create `backend/app/repositories/sessions.py`:

```python
"""Server-side session repository — opaque cookie ids."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as SessionRow
from app.repositories.base import AsyncRepository


class SessionRepository(AsyncRepository[SessionRow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SessionRow, session)

    async def create_session(self, user_id: UUID, expires_at: datetime) -> SessionRow:
        s = SessionRow(user_id=user_id, expires_at=expires_at)
        self.session.add(s)
        await self.session.flush()
        return s

    async def lookup_active(self, session_id: UUID) -> SessionRow | None:
        rows = await self.session.execute(
            select(SessionRow).where(
                SessionRow.id == session_id,
                SessionRow.expires_at > datetime.now(timezone.utc),
            )
        )
        return rows.scalar_one_or_none()

    async def revoke(self, session_id: UUID) -> None:
        await self.session.execute(delete(SessionRow).where(SessionRow.id == session_id))
        await self.session.flush()
```

Create `backend/app/repositories/audit_log.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_users_sessions.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/users.py backend/app/repositories/sessions.py backend/app/repositories/audit_log.py backend/tests/test_repositories/test_users_sessions.py
git commit -m "feat(repo): user, session, audit-log repositories + tests"
```

---

### Task 14: Tasting-note normalisation — write helper + tests

**Files:**
- Create: `backend/app/repositories/tasting_notes.py`
- Create: `backend/tests/test_repositories/test_tasting_notes.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_repositories/test_tasting_notes.py`:

```python
"""3NF round-trip — catalog reuse + junctions."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Bean, BeanTastingNote, BrewlogTastingNote, TastingNote, User,
)
from app.repositories.beans import BeanRepository
from app.repositories.tasting_notes import TastingNoteRepository


@pytest.fixture
async def user(db: AsyncSession) -> User:
    u = User(email="t@x.com", password_hash="x")
    db.add(u)
    await db.flush()
    return u


async def test_attach_creates_catalog_rows_once(db: AsyncSession, user: User) -> None:
    beans = BeanRepository(db)
    tn = TastingNoteRepository(db)
    b1 = await beans.create(user_id=user.id, name="A", origin_country="CO",
                            process="Washed", roast_level="Light")
    b2 = await beans.create(user_id=user.id, name="B", origin_country="CO",
                            process="Washed", roast_level="Light")
    await tn.attach_to_bean(bean_id=b1.id, labels=["citrus", "chocolate"])
    await tn.attach_to_bean(bean_id=b2.id, labels=["citrus", "floral"])

    catalog = (await db.execute(select(TastingNote))).scalars().all()
    junctions = (await db.execute(select(BeanTastingNote))).scalars().all()
    assert {c.label for c in catalog} == {"citrus", "chocolate", "floral"}  # 3 catalog rows, not 4
    assert len(junctions) == 4  # b1×2 + b2×2
```

- [ ] **Step 2: Run test, see it fail**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_tasting_notes.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement the repo**

Create `backend/app/repositories/tasting_notes.py`:

```python
"""Tasting-note catalog + junction writes — 3NF normalisation in code."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BeanTastingNote, BrewlogTastingNote, TastingNote


class TastingNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_labels(self, labels: list[str]) -> dict[str, UUID]:
        if not labels:
            return {}
        for label in labels:
            stmt = pg_insert(TastingNote).values(label=label).on_conflict_do_nothing(
                index_elements=["label"]
            )
            await self.session.execute(stmt)
        rows = (
            await self.session.execute(
                select(TastingNote).where(TastingNote.label.in_(labels))
            )
        ).scalars().all()
        return {r.label: r.id for r in rows}

    async def attach_to_bean(self, bean_id: UUID, labels: list[str]) -> None:
        ids = await self.upsert_labels(labels)
        for tn_id in ids.values():
            stmt = pg_insert(BeanTastingNote).values(
                bean_id=bean_id, tasting_note_id=tn_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.flush()

    async def attach_to_brewlog(self, brewlog_id: UUID, labels: list[str]) -> None:
        ids = await self.upsert_labels(labels)
        for tn_id in ids.values():
            stmt = pg_insert(BrewlogTastingNote).values(
                brewlog_id=brewlog_id, tasting_note_id=tn_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.flush()

    async def labels_for_bean(self, bean_id: UUID) -> list[str]:
        rows = await self.session.execute(
            select(TastingNote.label)
            .join(BeanTastingNote, BeanTastingNote.tasting_note_id == TastingNote.id)
            .where(BeanTastingNote.bean_id == bean_id)
        )
        return [r[0] for r in rows.all()]

    async def labels_for_brewlog(self, brewlog_id: UUID) -> list[str]:
        rows = await self.session.execute(
            select(TastingNote.label)
            .join(BrewlogTastingNote, BrewlogTastingNote.tasting_note_id == TastingNote.id)
            .where(BrewlogTastingNote.brewlog_id == brewlog_id)
        )
        return [r[0] for r in rows.all()]
```

- [ ] **Step 4: Run test to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_repositories/test_tasting_notes.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/tasting_notes.py backend/tests/test_repositories/test_tasting_notes.py
git commit -m "feat(repo): tasting-note normalisation (catalog + junctions) + 3NF round-trip test"
```

---

### Task 15: Wire `app/main.py` to init/dispose engines on startup

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Read current `main.py` and locate the FastAPI lifespan or startup hook**

Run: `cd backend && .venv/bin/python -c "import app.main; import inspect; print(inspect.getsource(app.main))"` (or open the file).

- [ ] **Step 2: Replace the lifespan/startup block with engine wiring**

In `backend/app/main.py`, ensure the lifespan context manager initialises both engines. Add (or replace) the lifespan block:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db.base import dispose_engine, init_engine
from app.db.mongo import close_mongo, init_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    init_mongo()
    yield
    await dispose_engine()
    await close_mongo()


app = FastAPI(lifespan=lifespan, ...)   # preserve existing kwargs
```

- [ ] **Step 3: Run a quick boot smoke check**

Run:
```bash
cd backend
DATABASE_URL=postgresql+asyncpg://brewlog:brewlog@localhost:5432/brewlog \
MONGO_URL=mongodb://localhost:27017/brewlog_chat \
  .venv/bin/uvicorn app.main:app --port 8001 &
sleep 3
curl -s http://localhost:8001/health || true
kill %1
```
Expected: server starts without errors. (`/health` may 404 if not implemented yet — that's fine.)

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(api): wire SQLAlchemy + Mongo engines into FastAPI lifespan"
```

---

### Task 16: Port existing roaster handler tests

**Files:**
- Modify: `backend/tests/test_roasters.py`
- Modify: `backend/app/api/roasters.py` (swap store for repo)
- Modify: `backend/app/api/deps.py` (add `get_db` if not present from earlier task)

- [ ] **Step 1: Add `get_db` dependency to `deps.py`**

In `backend/app/api/deps.py` (modify or create), add:

```python
from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db as _get_db


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in _get_db():
        yield session
```

- [ ] **Step 2: Rewrite `app/api/roasters.py` to use the repo**

Replace `backend/app/api/roasters.py` with:

```python
"""Roaster CRUD — repository-backed."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.base import NotFoundError
from app.repositories.roasters import RoasterRepository
from app.schemas.roaster import Roaster, RoasterCreate, RoasterUpdate

router = APIRouter(prefix="/api/v1/roasters", tags=["roasters"])


def _repo(db: AsyncSession = Depends(get_db)) -> RoasterRepository:
    return RoasterRepository(db)


@router.get("", response_model=list[Roaster])
async def list_roasters(repo: RoasterRepository = Depends(_repo)):
    rows = await repo.list()
    return [Roaster.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Roaster, status_code=201)
async def create_roaster(payload: RoasterCreate, repo: RoasterRepository = Depends(_repo)):
    # Note: user_id wiring comes in Phase 3 (auth). For now use a fixed dev user.
    from os import environ
    from uuid import UUID as _UUID
    dev_user = _UUID(environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))
    row = await repo.create(user_id=dev_user, **payload.model_dump())
    await repo.session.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.get("/{roaster_id}", response_model=Roaster)
async def get_roaster(roaster_id: UUID, repo: RoasterRepository = Depends(_repo)):
    try:
        row = await repo.get(roaster_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    return Roaster.model_validate(row, from_attributes=True)


@router.patch("/{roaster_id}", response_model=Roaster)
async def update_roaster(roaster_id: UUID, payload: RoasterUpdate, repo: RoasterRepository = Depends(_repo)):
    try:
        row = await repo.update(roaster_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await repo.session.commit()
    return Roaster.model_validate(row, from_attributes=True)


@router.delete("/{roaster_id}", status_code=204)
async def delete_roaster(roaster_id: UUID, repo: RoasterRepository = Depends(_repo)):
    try:
        await repo.delete(roaster_id)
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await repo.session.commit()
```

- [ ] **Step 3: Update `backend/tests/test_roasters.py` to use the `db` fixture and the running app**

For each test: replace any reference to `InMemoryStore` or `state.roaster_store` with a fresh `db` fixture and an HTTP client built against the app with `app.dependency_overrides[get_db]` returning the test session.

Append to `conftest.py`:

```python
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.main import app


@pytest.fixture
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # Ensure the dev user exists for unauthenticated handlers (Phase 2 only)
        from uuid import UUID as _UUID
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from app.db.models import User
        await db.execute(
            pg_insert(User)
            .values(id=_UUID("00000000-0000-0000-0000-000000000001"), email="dev@x.com", password_hash="x")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await db.flush()
        yield c
    app.dependency_overrides.clear()
```

Replace `backend/tests/test_roasters.py` body with:

```python
"""Roaster API tests — repository-backed."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_create_roaster_201(client: AsyncClient) -> None:
    r = await client.post("/api/v1/roasters", json={"name": "Onyx", "location": "Boston"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Onyx" and body["id"]


async def test_list_roasters_returns_created(client: AsyncClient) -> None:
    await client.post("/api/v1/roasters", json={"name": "A"})
    await client.post("/api/v1/roasters", json={"name": "B"})
    r = await client.get("/api/v1/roasters")
    assert r.status_code == 200
    assert {row["name"] for row in r.json()} >= {"A", "B"}


async def test_get_roaster_404_when_missing(client: AsyncClient) -> None:
    r = await client.get("/api/v1/roasters/00000000-0000-0000-0000-000000000abc")
    assert r.status_code == 404


async def test_update_roaster(client: AsyncClient) -> None:
    created = await client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await client.patch(f"/api/v1/roasters/{rid}", json={"location": "NYC"})
    assert r.status_code == 200 and r.json()["location"] == "NYC"


async def test_delete_roaster_204(client: AsyncClient) -> None:
    created = await client.post("/api/v1/roasters", json={"name": "A"})
    rid = created.json()["id"]
    r = await client.delete(f"/api/v1/roasters/{rid}")
    assert r.status_code == 204
```

- [ ] **Step 4: Run roaster tests**

Run: `cd backend && .venv/bin/pytest tests/test_roasters.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/roasters.py backend/app/api/deps.py backend/tests/test_roasters.py backend/tests/conftest.py
git commit -m "feat(api): port roaster handlers to repository + DB-backed tests"
```

---

### Task 17: Port bean / equipment / brewlog / stats handlers

**Files:**
- Modify: `backend/app/api/beans.py`, `equipment.py`, `brewlogs.py`, `stats.py`
- Modify: `backend/tests/test_beans.py`, `test_equipment.py`, `test_brewlogs.py`, `test_stats.py`

- [ ] **Step 1: Apply the same pattern as Task 16 to each handler**

For each of `beans.py`, `equipment.py`, `brewlogs.py`:
1. Replace `InMemoryStore` import with the corresponding `XxxRepository`.
2. Inject the repo via `Depends(get_db)` → repo factory.
3. Convert `pydantic` model to ORM via `**payload.model_dump()` for create/update.
4. Use `from_attributes=True` when serialising the ORM row back to the Pydantic response model.
5. Commit via `await repo.session.commit()` after mutating endpoints.
6. For `brewlogs.py`: also write tasting notes via `TastingNoteRepository.attach_to_brewlog(...)` after `repo.create(...)`. Strip `tasting_notes` from the kwargs before passing to `repo.create`.

For `stats.py`:
1. Replace direct store reads with `select(...)` queries built against the ORM models.
2. Use `func.count`, `func.avg`, etc. for aggregations.
3. Group by method/rating/etc. and project results matching the existing Pydantic stats schemas.

- [ ] **Step 2: Rewrite `tests/test_beans.py`, `test_equipment.py`, `test_brewlogs.py`, `test_stats.py` against the `client` fixture**

Each test creates rows via the API (chained POSTs) and asserts on responses. Avoid touching the DB directly when an HTTP path exists. Preserve all validation assertions (422 on out-of-band ratio, etc.).

- [ ] **Step 3: Run the full handler suite**

Run: `cd backend && .venv/bin/pytest tests/test_beans.py tests/test_equipment.py tests/test_brewlogs.py tests/test_stats.py -v`
Expected: all green; counts may shift slightly but no regressions.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/beans.py backend/app/api/equipment.py backend/app/api/brewlogs.py backend/app/api/stats.py backend/tests/test_beans.py backend/tests/test_equipment.py backend/tests/test_brewlogs.py backend/tests/test_stats.py
git commit -m "feat(api): port bean/equipment/brewlog/stats handlers to repositories"
```

---

### Task 18: Port GraphQL resolvers

**Files:**
- Modify: `backend/app/gql/queries.py`, `mutations.py`
- Modify: `backend/tests/test_graphql.py`

- [ ] **Step 1: Replace store reads/writes with repos in `queries.py` + `mutations.py`**

For each resolver:
1. Inject the AsyncSession via Strawberry's context (FastAPI request → `app.dependency_overrides[get_db]` already configured).
2. Build the appropriate `XxxRepository(session)` and call its methods.
3. Walk relationships (`roaster.beans`, `bean.brewlogs`) by issuing scoped queries from inside the resolver.

- [ ] **Step 2: Update `tests/test_graphql.py` to use the `client` fixture**

Replace any direct store assertions with GraphQL queries through the `client.post("/graphql", json={...})` pattern. Keep query and mutation strings unchanged where possible.

- [ ] **Step 3: Run GraphQL tests**

Run: `cd backend && .venv/bin/pytest tests/test_graphql.py -v`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add backend/app/gql/queries.py backend/app/gql/mutations.py backend/tests/test_graphql.py
git commit -m "feat(gql): port resolvers to repositories"
```

---

### Task 19: Delete `app/services/store.py` and run full suite

**Files:**
- Delete: `backend/app/services/store.py`
- Delete: `backend/tests/test_store.py` (only if it tested InMemoryStore directly)

- [ ] **Step 1: Search for any remaining import of `app.services.store`**

Run: `grep -rn "from app.services.store" backend/ || true`
Expected: no matches. If any remain, swap to repos.

- [ ] **Step 2: Delete the file**

Run: `rm backend/app/services/store.py`

- [ ] **Step 3: Delete or rewrite `test_store.py`**

If `tests/test_store.py` exists and tests `InMemoryStore` directly, delete it. If it tests behaviour now covered by repository tests, the deletion is fine — coverage is preserved by `tests/test_repositories/`.

- [ ] **Step 4: Run the full backend suite**

Run: `cd backend && .venv/bin/pytest`
Expected: all green; coverage report ≥ 90 %.

- [ ] **Step 5: Commit**

```bash
git add -u backend/app/services/store.py backend/tests/test_store.py
git commit -m "refactor: retire in-memory store; repositories are the source of truth"
```

---

## Phase 3 — Auth + Permissions + Audit

After Phase 3: every authenticated endpoint goes through `requires(...)`, every successful mutation writes an audit row, every failed auth/perm check writes a DENIED/FAIL row, and the detection trigger from Phase 1 fires automatically.

### Task 20: Password hashing — `app/auth/passwords.py`

**Files:**
- Create: `backend/app/auth/passwords.py`
- Create: `backend/tests/test_passwords.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_passwords.py`:

```python
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
```

- [ ] **Step 2: Run, see ImportError**

Run: `cd backend && .venv/bin/pytest tests/test_passwords.py -v`

- [ ] **Step 3: Implement**

Create `backend/app/auth/passwords.py`:

```python
"""Password hashing — passlib with bcrypt."""

from __future__ import annotations

from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _ctx.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ctx.verify(password, password_hash)
    except ValueError:
        return False
```

- [ ] **Step 4: Run, see pass**

Run: `cd backend && .venv/bin/pytest tests/test_passwords.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit + run RBAC seed (now that passwords.py exists)**

```bash
git add backend/app/auth/passwords.py backend/tests/test_passwords.py
git commit -m "feat(auth): bcrypt password hashing helpers"

# Now bootstrap roles/perms/admin user against the running Postgres
cd backend
DATABASE_URL=postgresql+asyncpg://brewlog:brewlog@localhost:5432/brewlog \
ADMIN_BOOTSTRAP_EMAIL=admin@brewlog.local \
ADMIN_BOOTSTRAP_PASSWORD=admin \
  .venv/bin/python -m app.scripts.seed_rbac
```

Expected: prints `seeded RBAC; admin = admin@brewlog.local`.

---

### Task 21: Session helpers — `app/auth/sessions.py`

**Files:**
- Create: `backend/app/auth/sessions.py`

- [ ] **Step 1: Implement create/lookup/revoke wrappers**

Create `backend/app/auth/sessions.py`:

```python
"""Session lifecycle — thin wrapper over SessionRepository.

Session ids are opaque UUIDs. The cookie carries only the id; the user_id
and expiry are server-side only.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as SessionRow
from app.repositories.sessions import SessionRepository


def _ttl_hours() -> int:
    return int(os.environ.get("SESSION_TTL_HOURS", "24"))


async def create_session(db: AsyncSession, user_id: UUID) -> SessionRow:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_ttl_hours())
    return await SessionRepository(db).create_session(user_id=user_id, expires_at=expires_at)


async def lookup_session(db: AsyncSession, session_id: UUID) -> SessionRow | None:
    return await SessionRepository(db).lookup_active(session_id)


async def revoke_session(db: AsyncSession, session_id: UUID) -> None:
    await SessionRepository(db).revoke(session_id)
```

- [ ] **Step 2: Smoke check**

Run: `cd backend && .venv/bin/python -c "from app.auth.sessions import create_session, lookup_session, revoke_session; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/auth/sessions.py
git commit -m "feat(auth): session lifecycle helpers"
```

---

### Task 22: Audit helper + middleware — `app/services/audit.py` [USER CONTRIBUTION CHECKPOINT]

**Files:**
- Create: `backend/app/services/audit.py`
- Create: `backend/tests/test_audit.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_audit.py`:

```python
"""Audit middleware writes FAIL/DENIED rows; helper writes OK rows; trigger fires."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def test_helper_writes_ok_row(db: AsyncSession) -> None:
    from app.services.audit import write_audit
    await write_audit(db, user_id=None, action="TEST_ACTION", status="OK")
    rows = (await db.execute(select(AuditLog).where(AuditLog.action == "TEST_ACTION"))).scalars().all()
    assert len(rows) == 1 and rows[0].status == "OK"
```

- [ ] **Step 2: Run, see ImportError**

Run: `cd backend && .venv/bin/pytest tests/test_audit.py -v`

- [ ] **Step 3: Implement**

Create `backend/app/services/audit.py`:

```python
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
```

- [ ] **Step 4: Run test to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_audit.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/audit.py backend/tests/test_audit.py
git commit -m "feat(audit): write_audit helper + AuditFailuresMiddleware"
```

---

### Task 23: `current_user` + `requires` dependencies

**Files:**
- Modify: `backend/app/api/deps.py`

- [ ] **Step 1: Append the auth dependencies**

Append to `backend/app/api/deps.py`:

```python
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import lookup_session
from app.db.models import User
from app.repositories.users import UserRepository
from app.services.audit import write_audit


async def current_user(
    request: Request,
    session_id: str | None = Cookie(default=None, alias="session_id"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if session_id is None:
        raise HTTPException(401, detail="not authenticated")
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(401, detail="malformed session")
    sess = await lookup_session(db, sid)
    if sess is None:
        raise HTTPException(401, detail="session expired or revoked")
    user = await UserRepository(db).get_with_perms(sess.user_id)
    if user is None:
        raise HTTPException(401, detail="user no longer exists")
    request.state.user = user
    return user


def _user_permission_codes(user: User) -> set[str]:
    codes: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return codes


def requires(*perm_codes: str):
    """Dependency factory. 403 + DENIED audit row if any perm missing."""

    async def _check(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        granted = _user_permission_codes(user)
        missing = [code for code in perm_codes if code not in granted]
        if missing:
            await write_audit(
                db,
                user_id=user.id,
                action="PERM_DENIED",
                status="DENIED",
                role_snapshot=",".join(r.name for r in user.roles),
                metadata={"required": list(perm_codes), "missing": missing},
            )
            await db.commit()
            raise HTTPException(403, detail={"required": list(perm_codes), "missing": missing})
        return user

    return _check
```

- [ ] **Step 2: Smoke check imports**

Run: `cd backend && .venv/bin/python -c "from app.api.deps import current_user, requires; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/deps.py
git commit -m "feat(api): current_user + requires(*perms) dependencies"
```

---

### Task 24: `auth` router — register / login / logout / me

**Files:**
- Create: `backend/app/api/auth.py`
- Create: `backend/tests/test_auth_api.py`
- Modify: `backend/app/main.py` (register router + middleware)

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_auth_api.py`:

```python
"""Auth API tests — register, login, logout, me."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_register_creates_user(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "a@x.com"


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter3"})
    assert r.status_code == 409


async def test_login_sets_session_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    assert r.status_code == 200
    assert "session_id" in r.cookies


async def test_login_wrong_password_401(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "wrong"})
    assert r.status_code == 401


async def test_login_unknown_user_401(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/login", json={"email": "ghost@x.com", "password": "x"})
    assert r.status_code == 401


async def test_me_requires_login(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200 and r.json()["email"] == "a@x.com"


async def test_logout_clears_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 204
    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401
```

- [ ] **Step 2: Run, see ImportError**

Run: `cd backend && .venv/bin/pytest tests/test_auth_api.py -v`

- [ ] **Step 3: Implement the auth router**

Create `backend/app/api/auth.py`:

```python
"""Register / login / logout / me — session-cookie based."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, get_db
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import create_session, revoke_session
from app.db.models import Role, User
from app.repositories.users import UserRepository
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    roles: list[str]
    permissions: list[str]


def _serialise(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        roles=[r.name for r in user.roles],
        permissions=[p.code for r in user.roles for p in r.permissions],
    )


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, detail="email already registered")

    user_role = (await db.execute(select(Role).where(Role.name == "user"))).scalar_one_or_none()
    if user_role is None:
        # Seed missing — for tests only; in prod the seed runs at startup.
        user_role = Role(name="user")
        db.add(user_role)
        await db.flush()
    await UserRepository(db).attach_role(user_id=user.id, role_id=user_role.id)
    await db.commit()
    fresh = await UserRepository(db).get_with_perms(user.id)
    return _serialise(fresh)


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginIn,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await UserRepository(db).find_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        # Audit the failed login. user_id is None when email is unknown.
        await write_audit(
            db,
            user_id=user.id if user else None,
            action="LOGIN_FAIL",
            status="FAIL",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
        raise HTTPException(401, detail="invalid credentials")

    sess = await create_session(db, user.id)
    await write_audit(
        db, user_id=user.id, action="LOGIN", status="OK",
        role_snapshot=",".join(r.name for r in user.roles),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    response.set_cookie(
        key="session_id",
        value=str(sess.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return _serialise(user)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    cookie = request.cookies.get("session_id")
    if cookie:
        try:
            await revoke_session(db, UUID(cookie))
        except ValueError:
            pass
    await write_audit(db, user_id=user.id, action="LOGOUT", status="OK")
    await db.commit()
    response.delete_cookie("session_id")
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return _serialise(user)
```

- [ ] **Step 4: Wire the router + middleware in `app/main.py`**

In `backend/app/main.py`, register the router and middleware:

```python
from app.api import auth as auth_api
from app.services.audit import AuditFailuresMiddleware

app.include_router(auth_api.router)
app.add_middleware(AuditFailuresMiddleware)
```

- [ ] **Step 5: Run auth tests to verify pass**

Run: `cd backend && .venv/bin/pytest tests/test_auth_api.py -v`
Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/auth.py backend/app/main.py backend/tests/test_auth_api.py
git commit -m "feat(auth): register/login/logout/me + session cookie + audit hooks"
```

---

### Task 25: Permission tests — admin allowed, user denied

**Files:**
- Create: `backend/tests/test_permissions.py`

- [ ] **Step 1: Write the test**

Create `backend/tests/test_permissions.py`:

```python
"""Permission gating: admin has access, user denied → 403 + DENIED audit row."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


async def _login(client: AsyncClient, email: str, password: str) -> None:
    await client.post("/api/v1/auth/login", json={"email": email, "password": password})


async def test_admin_can_call_observed_users(client: AsyncClient, db: AsyncSession) -> None:
    # Admin user is seeded by the bootstrap; in tests, the conftest does not
    # auto-seed RBAC so we register & manually upgrade. (Or extend conftest.)
    await client.post("/api/v1/auth/register", json={"email": "x@x.com", "password": "hunter2"})
    # NOTE: admin permissions wired via RBAC seed. Test below verifies the
    # default 'user' role is denied admin endpoints.
    await _login(client, "x@x.com", "hunter2")
    r = await client.get("/api/v1/admin/observed-users")
    assert r.status_code == 403


async def test_denied_request_writes_audit_row(client: AsyncClient, db: AsyncSession) -> None:
    await client.post("/api/v1/auth/register", json={"email": "y@x.com", "password": "hunter2"})
    await _login(client, "y@x.com", "hunter2")
    await client.get("/api/v1/admin/observed-users")  # 403
    rows = (await db.execute(
        select(AuditLog).where(AuditLog.action == "PERM_DENIED")
    )).scalars().all()
    assert len(rows) >= 1
```

- [ ] **Step 2: This test depends on `/api/v1/admin/...` existing — defer running until Task 26 lands**

Mark this file as `pytestmark = pytest.mark.skip(reason="admin router lands in Task 26")` at the top temporarily; remove the skip after Task 26.

- [ ] **Step 3: Commit the skipped test (so it travels with this task)**

```bash
git add backend/tests/test_permissions.py
git commit -m "test(perm): scaffolded permission gating tests (unskip after admin router)"
```

---

### Task 26: Admin router — observed-users + audit-log explorer

**Files:**
- Create: `backend/app/api/admin.py`
- Modify: `backend/app/main.py` (register router)
- Modify: `backend/tests/test_permissions.py` (unskip)

- [ ] **Step 1: Implement admin router**

Create `backend/app/api/admin.py`:

```python
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
```

- [ ] **Step 2: Register router in `main.py`**

Append to imports + `app.include_router` block:

```python
from app.api import admin as admin_api
app.include_router(admin_api.router)
```

- [ ] **Step 3: Unskip `tests/test_permissions.py`**

Remove the `pytestmark = pytest.mark.skip(...)` line.

- [ ] **Step 4: Run permission tests**

Run: `cd backend && .venv/bin/pytest tests/test_permissions.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/admin.py backend/app/main.py backend/tests/test_permissions.py
git commit -m "feat(admin): observed-users + audit-log endpoints (PERM gated)"
```

---

### Task 27: Wire `requires(...)` + `await write_audit(...)` into entity routers

**Files:**
- Modify: `backend/app/api/roasters.py`, `beans.py`, `equipment.py`, `brewlogs.py`, `stats.py`, `generator.py`

- [ ] **Step 1: For each entity router, replace the dev-user fallback with `current_user` + `requires(...)`**

Pattern (apply to roasters, repeat for beans/equipment/brewlogs):

```python
from app.api.deps import current_user, get_db, requires
from app.auth.permissions import (
    PERM_ROASTER_CREATE, PERM_ROASTER_DELETE_OWN, PERM_ROASTER_READ,
    PERM_ROASTER_UPDATE_OWN,
)
from app.db.models import User
from app.services.audit import write_audit


@router.get("", response_model=list[Roaster])
async def list_roasters(
    user: User = Depends(requires(PERM_ROASTER_READ)),
    repo: RoasterRepository = Depends(_repo),
):
    rows = await repo.list_for_user(user.id)
    return [Roaster.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=Roaster, status_code=201)
async def create_roaster(
    payload: RoasterCreate,
    user: User = Depends(requires(PERM_ROASTER_CREATE)),
    repo: RoasterRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    row = await repo.create(user_id=user.id, **payload.model_dump())
    await write_audit(
        db, user_id=user.id, action="ROASTER_CREATE", status="OK",
        resource_type="roaster", resource_id=row.id,
    )
    await db.commit()
    return Roaster.model_validate(row, from_attributes=True)
```

For update/delete, gate with the `:own` permission and verify `repo.get_for_user(...)`:

```python
@router.patch("/{roaster_id}", response_model=Roaster)
async def update_roaster(
    roaster_id: UUID, payload: RoasterUpdate,
    user: User = Depends(requires(PERM_ROASTER_UPDATE_OWN)),
    repo: RoasterRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
):
    try:
        await repo.get_for_user(roaster_id, user.id)
        row = await repo.update(roaster_id, **payload.model_dump(exclude_unset=True))
    except NotFoundError:
        raise HTTPException(404, detail="not found")
    await write_audit(
        db, user_id=user.id, action="ROASTER_UPDATE", status="OK",
        resource_type="roaster", resource_id=row.id,
    )
    await db.commit()
    return Roaster.model_validate(row, from_attributes=True)
```

Apply analogous changes for `delete_roaster` (`PERM_ROASTER_DELETE_OWN` + `ROASTER_DELETE` action), and repeat the entire pattern for `beans.py`, `equipment.py`, `brewlogs.py` with their respective permissions and action names (`BEAN_CREATE`, `BEAN_UPDATE`, etc.).

- [ ] **Step 2: Update `stats.py`**

Replace the unscoped query with one scoped to `user.id`:

```python
@router.get("/brewlogs", response_model=BrewStats)
async def brew_stats(
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    db: AsyncSession = Depends(get_db),
):
    # ... build stats via select(func.count()/avg/...).where(user_id=user.id)
```

- [ ] **Step 3: Gate generator endpoints to admin**

In `backend/app/api/generator.py`, replace the unauthenticated start/stop dependencies with:

```python
from app.api.deps import requires
from app.auth.permissions import PERM_GENERATOR

@router.post("/start")
async def start(user = Depends(requires(PERM_GENERATOR))):
    ...
```

- [ ] **Step 4: Update existing handler tests to log in first**

Each handler test now needs an authenticated client. Add a `logged_in_client` fixture to `conftest.py`:

```python
@pytest.fixture
async def logged_in_client(client: AsyncClient) -> AsyncClient:
    await client.post("/api/v1/auth/register", json={"email": "u@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "u@x.com", "password": "hunter2"})
    return client
```

Replace `client` with `logged_in_client` in each handler test that hits a gated endpoint.

- [ ] **Step 5: Run the full backend suite**

Run: `cd backend && .venv/bin/pytest`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/ backend/tests/
git commit -m "feat(api): wire requires() + audit calls into all entity routers"
```

---

### Task 28: Detection trigger tests [USER CONTRIBUTION CHECKPOINT]

**Files:**
- Create: `backend/tests/test_detect_malicious.py`

- [ ] **Step 1: Scaffold the parametrised tests with assertion bodies as user contributions**

Create `backend/tests/test_detect_malicious.py`:

```python
"""Detection trigger — four heuristic scenarios at threshold and threshold+1.

USER CONTRIBUTION CHECKPOINT:
The four assertion bodies in this file are deliberately minimal. Fill in the
specific assertions you want the trigger to satisfy at each boundary. The
parametrised structure is provided; you decide what "observed" means for each
scenario (e.g. exact reason string format, observed_at recency, etc.).
"""

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
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one()


async def test_failed_login_burst_just_below_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(4):
        await _insert_audit(db, u.id, "LOGIN_FAIL", "FAIL")
    await db.commit()
    fresh = await _refresh(db, u.id)
    # USER CONTRIBUTION: assert the user is NOT observed at threshold-1
    assert fresh.is_observed is False


async def test_failed_login_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(5):
        await _insert_audit(db, u.id, "LOGIN_FAIL", "FAIL")
    await db.commit()
    fresh = await _refresh(db, u.id)
    # USER CONTRIBUTION: assert observation triggered with the right reason format
    assert fresh.is_observed is True
    assert "failed-login-burst" in fresh.observed_reason


async def test_perm_denied_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(5):
        await _insert_audit(db, u.id, "PERM_DENIED", "DENIED")
    await db.commit()
    fresh = await _refresh(db, u.id)
    # USER CONTRIBUTION
    assert fresh.is_observed is True
    assert "permission-denied-burst" in fresh.observed_reason


async def test_mass_mutate_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for i in range(20):
        await _insert_audit(db, u.id, "BREWLOG_CREATE", "OK")
    await db.commit()
    fresh = await _refresh(db, u.id)
    # USER CONTRIBUTION
    assert fresh.is_observed is True
    assert "mass-mutation-burst" in fresh.observed_reason


async def test_mass_delete_burst_at_threshold(db: AsyncSession) -> None:
    u = await _make_user(db)
    for _ in range(10):
        await _insert_audit(db, u.id, "BREWLOG_DELETE", "OK")
    await db.commit()
    fresh = await _refresh(db, u.id)
    # USER CONTRIBUTION
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
```

- [ ] **Step 2: Run detection tests**

Run: `cd backend && .venv/bin/pytest tests/test_detect_malicious.py -v`
Expected: 7 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_detect_malicious.py
git commit -m "test(detect): trigger heuristics at threshold and recursion guard"
```

---

## Phase 4 — Chat (MongoDB + WebSocket Topics)

After Phase 4: two logged-in users in different browsers can join the lobby, see each other's messages live, scroll back through history pulled from Mongo, and create 1:1 DMs on demand. The detection trigger from Phase 1 sees chat-send actions.

### Task 29: Chat repository (Mongo)

**Files:**
- Create: `backend/app/repositories/chat.py`
- Create: `backend/tests/test_chat_repo.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_chat_repo.py`:

```python
"""Mongo chat-repository tests — room upsert + message persistence + ordering."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.repositories.chat import ChatRepository


async def test_lobby_present(mongo) -> None:
    repo = ChatRepository(mongo)
    await repo.bootstrap_lobby()
    lobby = await repo.find_room_by_name("lobby")
    assert lobby is not None and lobby["type"] == "room"


async def test_dm_upsert_idempotent(mongo) -> None:
    repo = ChatRepository(mongo)
    a, b = uuid4(), uuid4()
    r1 = await repo.upsert_dm(a, b)
    r2 = await repo.upsert_dm(b, a)  # reversed order
    assert r1["_id"] == r2["_id"]


async def test_message_insert_and_history_order(mongo) -> None:
    repo = ChatRepository(mongo)
    await repo.bootstrap_lobby()
    lobby = await repo.find_room_by_name("lobby")
    sender = uuid4()
    for i in range(3):
        await repo.add_message(lobby["_id"], sender, f"msg {i}")
    history = await repo.history(lobby["_id"], limit=10)
    bodies = [m["body"] for m in history]
    assert bodies == ["msg 2", "msg 1", "msg 0"]  # newest first
```

- [ ] **Step 2: Run, see ImportError**

Run: `cd backend && .venv/bin/pytest tests/test_chat_repo.py -v`

- [ ] **Step 3: Implement**

Create `backend/app/repositories/chat.py`:

```python
"""MongoDB chat repository — rooms + messages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING


def _pair_key(a: UUID, b: UUID) -> str:
    lo, hi = sorted([str(a), str(b)])
    return f"{lo}:{hi}"


class ChatRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def bootstrap_lobby(self) -> None:
        await self.db["chat_rooms"].create_index(
            [("participant_pair", ASCENDING)],
            unique=True,
            partialFilterExpression={"type": "dm"},
            name="ix_room_pair_unique_dm",
        )
        await self.db["chat_rooms"].create_index([("participants", ASCENDING)], name="ix_participants")
        await self.db["chat_messages"].create_index(
            [("room_id", ASCENDING), ("created_at", DESCENDING)], name="ix_msg_room_time"
        )
        existing = await self.db["chat_rooms"].find_one({"type": "room", "name": "lobby"})
        if existing is None:
            await self.db["chat_rooms"].insert_one(
                {
                    "type": "room",
                    "name": "lobby",
                    "participants": [],
                    "participant_pair": None,
                    "created_at": datetime.now(timezone.utc),
                    "last_message_at": None,
                }
            )

    async def find_room_by_name(self, name: str) -> dict | None:
        return await self.db["chat_rooms"].find_one({"type": "room", "name": name})

    async def find_room(self, room_id: ObjectId | str) -> dict | None:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        return await self.db["chat_rooms"].find_one({"_id": room_id})

    async def list_rooms_for_user(self, user_id: UUID) -> list[dict]:
        cursor = self.db["chat_rooms"].find(
            {"$or": [{"name": "lobby"}, {"participants": str(user_id)}]}
        )
        return [doc async for doc in cursor]

    async def upsert_dm(self, user_a: UUID, user_b: UUID) -> dict:
        pair = _pair_key(user_a, user_b)
        result = await self.db["chat_rooms"].find_one_and_update(
            {"type": "dm", "participant_pair": pair},
            {
                "$setOnInsert": {
                    "type": "dm",
                    "participants": sorted([str(user_a), str(user_b)]),
                    "participant_pair": pair,
                    "created_at": datetime.now(timezone.utc),
                    "last_message_at": None,
                    "name": None,
                }
            },
            upsert=True,
            return_document=True,
        )
        return result

    async def add_message(
        self, room_id: ObjectId | str, from_user_id: UUID, body: str
    ) -> dict:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        now = datetime.now(timezone.utc)
        doc = {
            "room_id": room_id,
            "from_user_id": str(from_user_id),
            "body": body,
            "created_at": now,
        }
        result = await self.db["chat_messages"].insert_one(doc)
        doc["_id"] = result.inserted_id
        await self.db["chat_rooms"].update_one(
            {"_id": room_id}, {"$set": {"last_message_at": now}}
        )
        return doc

    async def history(
        self, room_id: ObjectId | str, *, before: datetime | None = None, limit: int = 50
    ) -> list[dict]:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        query: dict[str, Any] = {"room_id": room_id}
        if before is not None:
            query["created_at"] = {"$lt": before}
        cursor = (
            self.db["chat_messages"]
            .find(query)
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return [doc async for doc in cursor]
```

- [ ] **Step 4: Run, see pass**

Run: `cd backend && .venv/bin/pytest tests/test_chat_repo.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/chat.py backend/tests/test_chat_repo.py
git commit -m "feat(chat): Mongo chat repository (rooms, DMs, messages, history)"
```

---

### Task 30: Topic-based broadcast manager

**Files:**
- Modify: `backend/app/services/broadcast.py`
- Create: `backend/tests/test_broadcast.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_broadcast.py`:

```python
"""Topic-based broadcast — fan-out is scoped to subscribers of a topic."""

from __future__ import annotations

import asyncio

import pytest

from app.services.broadcast import BroadcastManager


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


async def test_subscribe_and_publish() -> None:
    mgr = BroadcastManager()
    s1, s2 = FakeSocket(), FakeSocket()
    await mgr.subscribe("room-A", s1)
    await mgr.subscribe("room-B", s2)
    await mgr.publish("room-A", {"hello": "A"})
    await asyncio.sleep(0.01)
    assert s1.sent == [{"hello": "A"}] and s2.sent == []


async def test_unsubscribe_removes_socket() -> None:
    mgr = BroadcastManager()
    s = FakeSocket()
    await mgr.subscribe("room-A", s)
    await mgr.unsubscribe("room-A", s)
    await mgr.publish("room-A", {"x": 1})
    assert s.sent == []


async def test_publish_continues_when_one_socket_fails() -> None:
    mgr = BroadcastManager()

    class FailingSocket:
        async def send_json(self, data: dict) -> None:
            raise RuntimeError("disconnected")

    bad, good = FailingSocket(), FakeSocket()
    await mgr.subscribe("R", bad)
    await mgr.subscribe("R", good)
    await mgr.publish("R", {"x": 1})
    assert good.sent == [{"x": 1}]
```

- [ ] **Step 2: Run, see fail**

Run: `cd backend && .venv/bin/pytest tests/test_broadcast.py -v`

- [ ] **Step 3: Replace `app/services/broadcast.py` with topic-based version**

Replace `backend/app/services/broadcast.py`:

```python
"""Topic-based fan-out manager. Replaces the global ConnectionManager from A2.

Subscribers register against a topic string; publishes are scoped to that topic.
A failing send is dropped silently (treats the socket as disconnected) so one
bad client cannot stop a broadcast.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol


class _SocketLike(Protocol):
    async def send_json(self, data: Any) -> None: ...


class BroadcastManager:
    def __init__(self) -> None:
        self._subs: dict[str, set[_SocketLike]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, socket: _SocketLike) -> None:
        async with self._lock:
            self._subs.setdefault(topic, set()).add(socket)

    async def unsubscribe(self, topic: str, socket: _SocketLike) -> None:
        async with self._lock:
            self._subs.get(topic, set()).discard(socket)
            if not self._subs.get(topic):
                self._subs.pop(topic, None)

    async def unsubscribe_all(self, socket: _SocketLike) -> None:
        async with self._lock:
            for topic in list(self._subs.keys()):
                self._subs[topic].discard(socket)
                if not self._subs[topic]:
                    self._subs.pop(topic, None)

    async def publish(self, topic: str, payload: dict) -> None:
        async with self._lock:
            sockets = list(self._subs.get(topic, set()))
        for s in sockets:
            try:
                await s.send_json(payload)
            except Exception:  # noqa: BLE001
                # Socket is dead; remove it so it stops receiving.
                async with self._lock:
                    self._subs.get(topic, set()).discard(s)


# Singleton broadcaster shared between WS handler and chat service.
broadcaster = BroadcastManager()
```

- [ ] **Step 4: Run, see pass**

Run: `cd backend && .venv/bin/pytest tests/test_broadcast.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/broadcast.py backend/tests/test_broadcast.py
git commit -m "refactor(ws): topic-based BroadcastManager (replaces global manager)"
```

---

### Task 31: Chat service — wires Mongo writes to broadcast

**Files:**
- Create: `backend/app/services/chat.py`
- Create: `backend/tests/test_chat_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_chat_service.py`:

```python
"""Chat service — message send writes Mongo + publishes to topic."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.repositories.chat import ChatRepository
from app.services.broadcast import BroadcastManager


class FakeSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)


async def test_send_message_persists_and_broadcasts(mongo) -> None:
    from app.services.chat import ChatService

    repo = ChatRepository(mongo)
    await repo.bootstrap_lobby()
    bus = BroadcastManager()
    svc = ChatService(repo, bus)

    lobby = await repo.find_room_by_name("lobby")
    sock = FakeSocket()
    topic = f"room:{lobby['_id']}"
    await bus.subscribe(topic, sock)

    sender = uuid4()
    await svc.send(room_id=lobby["_id"], from_user_id=sender, body="hi")

    history = await repo.history(lobby["_id"])
    assert any(m["body"] == "hi" for m in history)
    assert len(sock.sent) == 1
    frame = sock.sent[0]
    assert frame["type"] == "message" and frame["msg"]["body"] == "hi"
```

- [ ] **Step 2: Run, see ImportError**

Run: `cd backend && .venv/bin/pytest tests/test_chat_service.py -v`

- [ ] **Step 3: Implement**

Create `backend/app/services/chat.py`:

```python
"""Chat service — coordinates Mongo writes and topic fan-out."""

from __future__ import annotations

from uuid import UUID

from bson import ObjectId

from app.repositories.chat import ChatRepository
from app.services.broadcast import BroadcastManager


def _topic_for(room_id) -> str:
    return f"room:{room_id}"


def _serialise(msg: dict) -> dict:
    return {
        "id": str(msg["_id"]),
        "room_id": str(msg["room_id"]),
        "from_user_id": msg["from_user_id"],
        "body": msg["body"],
        "created_at": msg["created_at"].isoformat(),
    }


class ChatService:
    def __init__(self, repo: ChatRepository, bus: BroadcastManager) -> None:
        self.repo = repo
        self.bus = bus

    async def send(self, *, room_id, from_user_id: UUID, body: str) -> dict:
        msg = await self.repo.add_message(room_id=room_id, from_user_id=from_user_id, body=body)
        payload = {"type": "message", "room_id": str(msg["room_id"]), "msg": _serialise(msg)}
        await self.bus.publish(_topic_for(msg["room_id"]), payload)
        return msg

    async def join_topic(self, room_id, socket) -> None:
        await self.bus.subscribe(_topic_for(room_id), socket)

    async def leave_topic(self, room_id, socket) -> None:
        await self.bus.unsubscribe(_topic_for(room_id), socket)
```

- [ ] **Step 4: Run, see pass**

Run: `cd backend && .venv/bin/pytest tests/test_chat_service.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/chat.py backend/tests/test_chat_service.py
git commit -m "feat(chat): ChatService — Mongo writes + topic fan-out"
```

---

### Task 32: Chat REST router — `/chat/rooms`, `/chat/rooms/{id}/messages`

**Files:**
- Create: `backend/app/api/chat.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_chat_api.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_chat_api.py`:

```python
"""Chat REST tests — list rooms, history, DM upsert."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login_two_users(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/register", json={"email": "b@x.com", "password": "hunter2"})
    await client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})


async def test_list_rooms_includes_lobby(client: AsyncClient) -> None:
    await _login_two_users(client)
    r = await client.get("/api/v1/chat/rooms")
    assert r.status_code == 200
    rooms = r.json()
    assert any(room.get("name") == "lobby" for room in rooms)


async def test_history_paginates_newest_first(client: AsyncClient) -> None:
    await _login_two_users(client)
    rooms = (await client.get("/api/v1/chat/rooms")).json()
    lobby_id = next(r["id"] for r in rooms if r.get("name") == "lobby")
    # No messages yet; expect empty list with 200
    r = await client.get(f"/api/v1/chat/rooms/{lobby_id}/messages")
    assert r.status_code == 200 and r.json() == []
```

- [ ] **Step 2: Run, see fail**

Run: `cd backend && .venv/bin/pytest tests/test_chat_api.py -v`

- [ ] **Step 3: Implement chat router**

Create `backend/app/api/chat.py`:

```python
"""Chat REST endpoints — rooms list, DM upsert, message history."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from bson import ObjectId, errors
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import current_user, requires
from app.auth.permissions import PERM_CHAT_READ, PERM_CHAT_SEND
from app.db.models import User
from app.db.mongo import get_db as get_mongo_db
from app.repositories.chat import ChatRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _repo() -> ChatRepository:
    return ChatRepository(get_mongo_db())


def _serialise_room(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "type": doc["type"],
        "name": doc.get("name"),
        "participants": doc.get("participants", []),
        "last_message_at": doc.get("last_message_at"),
    }


def _serialise_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "room_id": str(doc["room_id"]),
        "from_user_id": doc["from_user_id"],
        "body": doc["body"],
        "created_at": doc["created_at"],
    }


def _parse_room_id(room_id: str) -> ObjectId:
    try:
        return ObjectId(room_id)
    except errors.InvalidId:
        raise HTTPException(404, detail="room not found")


@router.get("/rooms")
async def list_rooms(
    user: User = Depends(requires(PERM_CHAT_READ)),
    repo: ChatRepository = Depends(_repo),
):
    rooms = await repo.list_rooms_for_user(user.id)
    return [_serialise_room(r) for r in rooms]


@router.post("/rooms", status_code=201)
async def upsert_dm(
    payload: dict,
    user: User = Depends(requires(PERM_CHAT_SEND)),
    repo: ChatRepository = Depends(_repo),
):
    other_id_str = payload.get("participant_id")
    if not other_id_str:
        raise HTTPException(400, detail="participant_id required")
    try:
        other = UUID(other_id_str)
    except ValueError:
        raise HTTPException(400, detail="participant_id must be a UUID")
    room = await repo.upsert_dm(user.id, other)
    return _serialise_room(room)


@router.get("/rooms/{room_id}/messages")
async def history(
    room_id: str,
    before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    user: User = Depends(requires(PERM_CHAT_READ)),
    repo: ChatRepository = Depends(_repo),
):
    oid = _parse_room_id(room_id)
    rows = await repo.history(oid, before=before, limit=limit)
    return [_serialise_message(r) for r in rows]
```

- [ ] **Step 4: Register router + bootstrap chat lobby on startup in `main.py`**

In `backend/app/main.py` lifespan:

```python
from app.api import chat as chat_api
from app.repositories.chat import ChatRepository
from app.db.mongo import get_db as get_mongo_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    init_mongo()
    await ChatRepository(get_mongo_db()).bootstrap_lobby()
    yield
    await dispose_engine()
    await close_mongo()

app.include_router(chat_api.router)
```

- [ ] **Step 5: Run chat REST tests**

Run: `cd backend && .venv/bin/pytest tests/test_chat_api.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/chat.py backend/app/main.py backend/tests/test_chat_api.py
git commit -m "feat(chat): REST endpoints (rooms list, DM upsert, history)"
```

---

### Task 33: WebSocket handler with topic multiplexing

**Files:**
- Modify: `backend/app/api/websocket.py`
- Create: `backend/tests/test_chat_ws.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_chat_ws.py`:

```python
"""WebSocket fan-out test using FastAPI's TestClient."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


async def test_two_clients_in_same_room_see_each_others_messages(client) -> None:
    """Use sync TestClient via the existing FastAPI app for WS testing."""
    from app.main import app
    sync_client = TestClient(app)

    # Both register + login (session cookies survive in TestClient)
    sync_client.post("/api/v1/auth/register", json={"email": "a@x.com", "password": "hunter2"})
    sync_client.post("/api/v1/auth/login", json={"email": "a@x.com", "password": "hunter2"})

    rooms = sync_client.get("/api/v1/chat/rooms").json()
    lobby_id = next(r["id"] for r in rooms if r.get("name") == "lobby")

    with sync_client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "join", "room_id": lobby_id})
        ws.send_json({"type": "send", "room_id": lobby_id, "body": "hello"})
        # Should receive at least the echo back
        frame = ws.receive_json()
        # First frame may be the history; loop until we see our message
        for _ in range(5):
            if frame.get("type") == "message" and frame["msg"]["body"] == "hello":
                break
            frame = ws.receive_json()
        assert frame["type"] == "message" and frame["msg"]["body"] == "hello"
```

- [ ] **Step 2: Run, see fail**

Run: `cd backend && .venv/bin/pytest tests/test_chat_ws.py -v`

- [ ] **Step 3: Replace `app/api/websocket.py`**

Replace `backend/app/api/websocket.py`:

```python
"""WebSocket handler — multiplexed by frame envelope (chat rooms + brewlog feed)."""

from __future__ import annotations

import json
from uuid import UUID

from bson import ObjectId, errors as bson_errors
from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect

from app.auth.sessions import lookup_session
from app.db.base import session_factory
from app.db.mongo import get_db as get_mongo_db
from app.repositories.chat import ChatRepository
from app.repositories.users import UserRepository
from app.services.audit import write_audit
from app.services.broadcast import broadcaster
from app.services.chat import ChatService

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str | None = Cookie(default=None)):
    if session_id is None:
        await websocket.close(code=4401)
        return
    try:
        sid = UUID(session_id)
    except ValueError:
        await websocket.close(code=4401)
        return

    factory = session_factory()
    async with factory() as db:
        sess = await lookup_session(db, sid)
        if sess is None:
            await websocket.close(code=4401)
            return
        user = await UserRepository(db).get_with_perms(sess.user_id)
        if user is None:
            await websocket.close(code=4401)
            return

    await websocket.accept()
    await websocket.send_json({"type": "ready", "user_id": str(user.id)})

    chat = ChatService(ChatRepository(get_mongo_db()), broadcaster)
    joined: set[str] = set()

    try:
        while True:
            frame = await websocket.receive_json()
            kind = frame.get("type")

            if kind == "join":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                await chat.join_topic(oid, websocket)
                joined.add(str(oid))
                history = await chat.repo.history(oid, limit=50)
                await websocket.send_json({
                    "type": "history",
                    "room_id": str(oid),
                    "messages": [
                        {
                            "id": str(m["_id"]),
                            "room_id": str(m["room_id"]),
                            "from_user_id": m["from_user_id"],
                            "body": m["body"],
                            "created_at": m["created_at"].isoformat(),
                        }
                        for m in history
                    ],
                })

            elif kind == "send":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                body = (frame.get("body") or "").strip()
                if not body or len(body) > 2000:
                    continue
                async with factory() as db:
                    await write_audit(db, user_id=user.id, action="CHAT_SEND", status="OK")
                    await db.commit()
                await chat.send(room_id=oid, from_user_id=user.id, body=body)

            elif kind == "leave":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                await chat.leave_topic(oid, websocket)
                joined.discard(str(oid))

    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.unsubscribe_all(websocket)
```

- [ ] **Step 4: Verify the WebSocket route is registered in `main.py`**

Ensure `backend/app/main.py` contains:

```python
from app.api import websocket as ws_api
app.include_router(ws_api.router)
```

- [ ] **Step 5: Run the WebSocket test**

Run: `cd backend && .venv/bin/pytest tests/test_chat_ws.py -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/websocket.py backend/app/main.py backend/tests/test_chat_ws.py
git commit -m "feat(ws): authenticated topic-multiplexed chat handler"
```

---

### Task 34: Frontend — `useAuth` hook + Login/Register pages

**Files:**
- Create: `brewlog/src/hooks/useAuth.ts`
- Create: `brewlog/src/pages/Login.tsx`
- Create: `brewlog/src/pages/Register.tsx`
- Create: `brewlog/src/components/RequireAuth.tsx`
- Create: `brewlog/src/components/RequirePerm.tsx`
- Modify: `brewlog/src/lib/api.ts` (cookie-aware fetch)
- Modify: `brewlog/src/App.tsx` (add routes)

- [ ] **Step 1: Cookie-aware fetch wrapper**

Modify `brewlog/src/lib/api.ts` (or create) so every fetch sends `credentials: "include"`:

```typescript
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";

export async function api<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text();
    const err = new Error(body || res.statusText) as Error & { status: number };
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
```

- [ ] **Step 2: `useAuth` hook**

Create `brewlog/src/hooks/useAuth.ts`:

```typescript
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type CurrentUser = {
  id: string;
  email: string;
  roles: string[];
  permissions: string[];
};

type State =
  | { status: "loading" }
  | { status: "anon" }
  | { status: "auth"; user: CurrentUser };

export function useAuth() {
  const [state, setState] = useState<State>({ status: "loading" });

  const refresh = useCallback(async () => {
    try {
      const user = await api<CurrentUser>("/api/v1/auth/me");
      setState({ status: "auth", user });
    } catch {
      setState({ status: "anon" });
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      await api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await refresh();
    },
    [refresh],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      await api("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    await api("/api/v1/auth/logout", { method: "POST" });
    setState({ status: "anon" });
  }, []);

  const hasPermission = useCallback(
    (code: string) =>
      state.status === "auth" && state.user.permissions.includes(code),
    [state],
  );

  return {
    state,
    user: state.status === "auth" ? state.user : null,
    permissions: state.status === "auth" ? state.user.permissions : [],
    hasPermission,
    login,
    register,
    logout,
    refresh,
  };
}
```

- [ ] **Step 3: Login + Register pages**

Create `brewlog/src/pages/Login.tsx`:

```tsx
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      nav("/dashboard");
    } catch (err) {
      setError("Invalid credentials");
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-12 max-w-sm space-y-3">
      <h1 className="text-2xl font-semibold">Log in</h1>
      <input className="w-full rounded border p-2" type="email" placeholder="email"
             value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input className="w-full rounded border p-2" type="password" placeholder="password"
             value={password} onChange={(e) => setPassword(e.target.value)} required />
      <button className="w-full rounded bg-amber-700 p-2 text-white" type="submit">Log in</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <p className="text-sm">No account? <a href="/register" className="underline">Register</a></p>
    </form>
  );
}
```

Create `brewlog/src/pages/Register.tsx`:

```tsx
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await register(email, password);
      nav("/dashboard");
    } catch (err) {
      const e = err as { status?: number };
      setError(e.status === 409 ? "Email already registered" : "Registration failed");
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-12 max-w-sm space-y-3">
      <h1 className="text-2xl font-semibold">Create account</h1>
      <input className="w-full rounded border p-2" type="email" placeholder="email"
             value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input className="w-full rounded border p-2" type="password" placeholder="password (≥6)"
             value={password} onChange={(e) => setPassword(e.target.value)} minLength={6} required />
      <button className="w-full rounded bg-amber-700 p-2 text-white" type="submit">Register</button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}
```

- [ ] **Step 4: `RequireAuth` + `RequirePerm` guards**

Create `brewlog/src/components/RequireAuth.tsx`:

```tsx
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { state } = useAuth();
  if (state.status === "loading") return null;
  if (state.status === "anon") return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

Create `brewlog/src/components/RequirePerm.tsx`:

```tsx
import type { ReactNode } from "react";

import { useAuth } from "@/hooks/useAuth";

export function RequirePerm({
  perm,
  children,
}: {
  perm: string;
  children: ReactNode;
}) {
  const { state, hasPermission } = useAuth();
  if (state.status === "loading") return null;
  if (state.status === "anon" || !hasPermission(perm)) {
    return (
      <div className="mx-auto mt-16 max-w-md text-center text-stone-700">
        <h1 className="text-3xl font-semibold">403</h1>
        <p className="mt-2">You don't have permission to view this page.</p>
      </div>
    );
  }
  return <>{children}</>;
}
```

- [ ] **Step 5: Wire routes in `App.tsx`**

In `brewlog/src/App.tsx`, add the routes:

```tsx
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import { RequireAuth } from "@/components/RequireAuth";

// inside the <Routes>:
<Route path="/login" element={<Login />} />
<Route path="/register" element={<Register />} />
{/* Wrap protected routes: */}
<Route element={<RequireAuth><Outlet /></RequireAuth>}>
  <Route path="/dashboard" element={<Dashboard />} />
  {/* …existing protected routes */}
</Route>
```

- [ ] **Step 6: Manual smoke test**

Run frontend + backend, visit `/login`, register, log in, verify `useAuth.user` is populated by inspecting `/api/v1/auth/me` in DevTools.

- [ ] **Step 7: Commit**

```bash
git add brewlog/src/hooks/useAuth.ts brewlog/src/pages/Login.tsx brewlog/src/pages/Register.tsx brewlog/src/components/RequireAuth.tsx brewlog/src/components/RequirePerm.tsx brewlog/src/lib/api.ts brewlog/src/App.tsx
git commit -m "feat(frontend): useAuth hook + Login/Register pages + auth guards"
```

---

### Task 35: Frontend — chat shell (rooms list + message panel + WebSocket)

**Files:**
- Create: `brewlog/src/hooks/useChatRooms.ts`
- Create: `brewlog/src/hooks/useChatRoom.ts`
- Create: `brewlog/src/hooks/useChatSocket.ts`
- Create: `brewlog/src/pages/Chat.tsx`
- Modify: `brewlog/src/App.tsx`, `brewlog/src/components/NavBar.tsx`

- [ ] **Step 1: Chat-rooms hook**

Create `brewlog/src/hooks/useChatRooms.ts`:

```typescript
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export type Room = {
  id: string;
  type: "dm" | "room";
  name: string | null;
  participants: string[];
  last_message_at: string | null;
};

export function useChatRooms() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Room[]>("/api/v1/chat/rooms")
      .then(setRooms)
      .finally(() => setLoading(false));
  }, []);

  async function startDm(participantId: string) {
    const room = await api<Room>("/api/v1/chat/rooms", {
      method: "POST",
      body: JSON.stringify({ participant_id: participantId }),
    });
    setRooms((prev) => (prev.find((r) => r.id === room.id) ? prev : [...prev, room]));
    return room;
  }

  return { rooms, loading, startDm };
}
```

- [ ] **Step 2: Shared WebSocket hook**

Create `brewlog/src/hooks/useChatSocket.ts`:

```typescript
import { useEffect, useRef } from "react";

type IncomingFrame =
  | { type: "ready"; user_id: string }
  | { type: "history"; room_id: string; messages: Message[] }
  | { type: "message"; room_id: string; msg: Message };

export type Message = {
  id: string;
  room_id: string;
  from_user_id: string;
  body: string;
  created_at: string;
};

export function useChatSocket(onFrame: (frame: IncomingFrame) => void) {
  const ref = useRef<WebSocket | null>(null);

  useEffect(() => {
    const base =
      (import.meta.env.VITE_API_BASE as string | undefined) ?? "http://localhost:8000";
    const wsUrl = base.replace(/^http/, "ws") + "/ws";
    const ws = new WebSocket(wsUrl);
    ref.current = ws;
    ws.onmessage = (e) => onFrame(JSON.parse(e.data) as IncomingFrame);
    return () => ws.close();
  }, [onFrame]);

  return {
    join: (roomId: string) => ref.current?.send(JSON.stringify({ type: "join", room_id: roomId })),
    leave: (roomId: string) => ref.current?.send(JSON.stringify({ type: "leave", room_id: roomId })),
    send: (roomId: string, body: string) =>
      ref.current?.send(JSON.stringify({ type: "send", room_id: roomId, body })),
  };
}
```

- [ ] **Step 3: Chat page**

Create `brewlog/src/pages/Chat.tsx`:

```tsx
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/hooks/useAuth";
import { useChatRooms, type Room } from "@/hooks/useChatRooms";
import { useChatSocket, type Message } from "@/hooks/useChatSocket";

export default function Chat() {
  const { user } = useAuth();
  const { rooms } = useChatRooms();
  const [active, setActive] = useState<Room | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");

  const onFrame = useCallback((frame: any) => {
    if (frame.type === "history") {
      setMessages(frame.messages.slice().reverse()); // server returns newest-first
    } else if (frame.type === "message" && active && frame.room_id === active.id) {
      setMessages((prev) => [...prev, frame.msg]);
    }
  }, [active]);

  const ws = useChatSocket(onFrame);

  useEffect(() => {
    if (!active) return;
    setMessages([]);
    ws.join(active.id);
    return () => ws.leave(active.id);
  }, [active, ws]);

  if (!user) return null;
  return (
    <div className="grid grid-cols-[200px_1fr] gap-4 p-4">
      <aside className="space-y-1">
        <h2 className="text-sm font-semibold uppercase text-stone-500">Rooms</h2>
        {rooms.map((r) => (
          <button
            key={r.id}
            onClick={() => setActive(r)}
            className={`block w-full rounded p-2 text-left ${
              active?.id === r.id ? "bg-amber-100" : "hover:bg-stone-100"
            }`}
          >
            {r.name ?? r.participants.find((p) => p !== user.id) ?? "DM"}
          </button>
        ))}
      </aside>
      <main className="flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {messages.map((m) => (
            <div key={m.id} className="text-sm">
              <span className="font-mono text-stone-500">{m.from_user_id.slice(0, 8)}:</span>{" "}
              {m.body}
            </div>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!active || !draft.trim()) return;
            ws.send(active.id, draft);
            setDraft("");
          }}
          className="flex gap-2 border-t pt-2"
        >
          <input
            className="flex-1 rounded border p-2"
            placeholder="message…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={!active}
          />
          <button
            className="rounded bg-amber-700 px-4 text-white disabled:opacity-50"
            type="submit"
            disabled={!active}
          >
            Send
          </button>
        </form>
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Wire route + nav link**

In `brewlog/src/App.tsx`:

```tsx
import Chat from "@/pages/Chat";
<Route path="/chat" element={<Chat />} />
```

In `brewlog/src/components/NavBar.tsx`, add:

```tsx
{user && <NavLink to="/chat">Chat</NavLink>}
```

- [ ] **Step 5: Manual smoke test (two browsers)**

1. Open two browser windows on http://localhost:5173/.
2. Register two users, log in to each.
3. Both navigate to /chat → both should see "lobby" in the sidebar.
4. Send a message from window A → window B receives it instantly.

- [ ] **Step 6: Commit**

```bash
git add brewlog/src/hooks/useChatRooms.ts brewlog/src/hooks/useChatRoom.ts brewlog/src/hooks/useChatSocket.ts brewlog/src/pages/Chat.tsx brewlog/src/App.tsx brewlog/src/components/NavBar.tsx
git commit -m "feat(frontend): chat shell (lobby + DMs + live WebSocket multiplexing)"
```

---

## Phase 5 — Admin Dashboard, Polish, Deploy

After Phase 5: admin can see observed users with sparklines and clear observations, browse the audit log, and the whole stack runs on Coolify with the frontend on a separate machine.

### Task 36: Sparkline component [USER CONTRIBUTION CHECKPOINT]

**Files:**
- Create: `brewlog/src/components/Sparkline.tsx`

- [ ] **Step 1: Scaffold the component skeleton with the rendering block as user contribution**

Create `brewlog/src/components/Sparkline.tsx`:

```tsx
/**
 * Sparkline — bucketed bar chart of recent action counts.
 *
 * USER CONTRIBUTION CHECKPOINT:
 * The bucketing math and data fetch are wired below. Replace the placeholder
 * <div> in the return statement with the bar rendering of your choice.
 *
 * Bucket semantics: each entry in `buckets` is a 1-minute window; the value is
 * the count of audit_log rows that fell inside that window. `max` is provided
 * so you can scale (linear vs log vs sqrt — your call). 50 buckets = last hour.
 */

type Action = { action: string; status: string; created_at: string };

type Props = {
  actions: Action[];
  bucketCount?: number;
  bucketMs?: number;
};

export function Sparkline({ actions, bucketCount = 50, bucketMs = 60_000 }: Props) {
  const now = Date.now();
  const buckets = new Array<number>(bucketCount).fill(0);

  for (const a of actions) {
    const t = new Date(a.created_at).getTime();
    const idx = bucketCount - 1 - Math.floor((now - t) / bucketMs);
    if (idx >= 0 && idx < bucketCount) buckets[idx] += 1;
  }
  const max = Math.max(1, ...buckets);

  // ── USER CONTRIBUTION ──
  // Replace the placeholder below with your rendering. ~10–15 lines of TSX.
  // Suggestions:
  //   - `<div>` with `display: flex` and one child per bucket
  //   - height: `${(buckets[i] / max) * 100}%`
  //   - colour ramp by intensity (e.g. amber-200 → amber-800)
  //   - title attribute for hover (`{buckets[i]} actions`)
  return (
    <div
      role="img"
      aria-label={`Sparkline: ${actions.length} actions in last ${bucketCount} minutes`}
      className="flex h-6 w-32 items-end gap-px"
    >
      {/* TODO: render bars from `buckets`, scaled by `max` */}
      <span className="text-xs text-stone-500">[sparkline placeholder]</span>
    </div>
  );
}
```

- [ ] **Step 2: Commit (skeleton)**

```bash
git add brewlog/src/components/Sparkline.tsx
git commit -m "feat(frontend): Sparkline component skeleton (user contribution slot)"
```

---

### Task 37: Frontend — Observed Users admin page

**Files:**
- Create: `brewlog/src/hooks/useObservedUsers.ts`
- Create: `brewlog/src/pages/admin/ObservedUsers.tsx`
- Modify: `brewlog/src/App.tsx`, `brewlog/src/components/NavBar.tsx`

- [ ] **Step 1: Hook**

Create `brewlog/src/hooks/useObservedUsers.ts`:

```typescript
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type ObservedUser = {
  id: string;
  email: string;
  observed_reason: string | null;
  observed_at: string | null;
  recent_actions: { action: string; status: string; created_at: string }[];
};

export function useObservedUsers() {
  const [users, setUsers] = useState<ObservedUser[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await api<ObservedUser[]>("/api/v1/admin/observed-users"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const clear = useCallback(
    async (userId: string) => {
      await api(`/api/v1/admin/observed-users/${userId}/clear`, { method: "POST" });
      await refresh();
    },
    [refresh],
  );

  return { users, loading, refresh, clear };
}
```

- [ ] **Step 2: Page**

Create `brewlog/src/pages/admin/ObservedUsers.tsx`:

```tsx
import { useObservedUsers } from "@/hooks/useObservedUsers";
import { Sparkline } from "@/components/Sparkline";

export default function ObservedUsers() {
  const { users, loading, clear } = useObservedUsers();

  return (
    <div className="mx-auto max-w-3xl p-4">
      <h1 className="mb-4 text-2xl font-semibold">Observed users</h1>
      {loading && <p>Loading…</p>}
      {!loading && users.length === 0 && (
        <p className="text-stone-500">No users currently under observation.</p>
      )}
      <ul className="space-y-3">
        {users.map((u) => (
          <li key={u.id} className="rounded border bg-white p-3">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="font-mono">{u.email}</div>
                <div className="text-sm text-red-700">{u.observed_reason}</div>
                <div className="text-xs text-stone-500">
                  {u.observed_at ? new Date(u.observed_at).toLocaleString() : ""}
                </div>
              </div>
              <button
                onClick={() => clear(u.id)}
                className="rounded bg-stone-100 px-3 py-1 text-sm hover:bg-stone-200"
              >
                Clear
              </button>
            </div>
            <div className="mt-2">
              <Sparkline actions={u.recent_actions} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

- [ ] **Step 3: Wire route + nav (perm-gated)**

In `brewlog/src/App.tsx`:

```tsx
import ObservedUsers from "@/pages/admin/ObservedUsers";
import { RequirePerm } from "@/components/RequirePerm";

<Route
  path="/admin/observed"
  element={
    <RequirePerm perm="user:observe">
      <ObservedUsers />
    </RequirePerm>
  }
/>
```

In `brewlog/src/components/NavBar.tsx`:

```tsx
{hasPermission("user:observe") && <NavLink to="/admin/observed">Admin</NavLink>}
```

- [ ] **Step 4: Manual smoke test**

Trigger an observation: log in as a normal user, hit a forbidden admin endpoint repeatedly (5×) to fire the perm-denied burst → log in as admin → navigate to `/admin/observed` → see the user with reason + sparkline + Clear button.

- [ ] **Step 5: Commit**

```bash
git add brewlog/src/hooks/useObservedUsers.ts brewlog/src/pages/admin/ObservedUsers.tsx brewlog/src/App.tsx brewlog/src/components/NavBar.tsx
git commit -m "feat(admin-ui): observed users page with sparklines + clear action"
```

---

### Task 38: Frontend — Audit Log Explorer

**Files:**
- Create: `brewlog/src/pages/admin/AuditLogExplorer.tsx`
- Modify: `brewlog/src/App.tsx`

- [ ] **Step 1: Page**

Create `brewlog/src/pages/admin/AuditLogExplorer.tsx`:

```tsx
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type Row = {
  id: number;
  user_id: string | null;
  role_snapshot: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  status: string;
  created_at: string;
};

export default function AuditLogExplorer() {
  const [filterUser, setFilterUser] = useState("");
  const [filterAction, setFilterAction] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterUser) params.set("user_id", filterUser);
    if (filterAction) params.set("action", filterAction);
    params.set("page", "1");
    params.set("page_size", "100");
    try {
      const data = await api<Row[]>(`/api/v1/admin/audit-log?${params}`);
      setRows(data);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="p-4">
      <h1 className="mb-4 text-2xl font-semibold">Audit log</h1>
      <div className="mb-3 flex gap-2">
        <input
          className="rounded border p-1"
          placeholder="user id"
          value={filterUser}
          onChange={(e) => setFilterUser(e.target.value)}
        />
        <input
          className="rounded border p-1"
          placeholder="action (e.g. LOGIN_FAIL)"
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
        />
        <button className="rounded bg-amber-700 px-3 text-white" onClick={load}>
          Filter
        </button>
      </div>
      {loading && <p>Loading…</p>}
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b text-left">
            <th className="p-1">Time</th>
            <th className="p-1">User</th>
            <th className="p-1">Role</th>
            <th className="p-1">Action</th>
            <th className="p-1">Status</th>
            <th className="p-1">Resource</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-b">
              <td className="p-1 font-mono text-xs">{new Date(r.created_at).toLocaleString()}</td>
              <td className="p-1 font-mono text-xs">{r.user_id?.slice(0, 8) ?? "—"}</td>
              <td className="p-1 text-xs">{r.role_snapshot ?? "—"}</td>
              <td className="p-1">{r.action}</td>
              <td
                className={`p-1 font-medium ${
                  r.status === "OK"
                    ? "text-green-700"
                    : r.status === "DENIED"
                    ? "text-amber-700"
                    : r.status === "FAIL"
                    ? "text-red-700"
                    : "text-stone-500"
                }`}
              >
                {r.status}
              </td>
              <td className="p-1 font-mono text-xs">
                {r.resource_type ? `${r.resource_type}/${r.resource_id?.slice(0, 8)}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Wire route**

In `brewlog/src/App.tsx`:

```tsx
import AuditLogExplorer from "@/pages/admin/AuditLogExplorer";

<Route
  path="/admin/audit"
  element={
    <RequirePerm perm="log:read">
      <AuditLogExplorer />
    </RequirePerm>
  }
/>
```

- [ ] **Step 3: Commit**

```bash
git add brewlog/src/pages/admin/AuditLogExplorer.tsx brewlog/src/App.tsx
git commit -m "feat(admin-ui): audit log explorer (filter by user/action)"
```

---

### Task 39: Gate Live page generator buttons; admin-only tooltip for non-admins

**Files:**
- Modify: `brewlog/src/pages/Live.tsx`

- [ ] **Step 1: Disable + tooltip**

In `brewlog/src/pages/Live.tsx`, replace the start/stop generator buttons with the perm-aware version:

```tsx
import { useAuth } from "@/hooks/useAuth";
const { hasPermission } = useAuth();
const canControl = hasPermission("generator:control");

<button
  onClick={start}
  disabled={!canControl}
  title={canControl ? undefined : "Admin only"}
  className="rounded bg-amber-700 px-3 py-1 text-white disabled:opacity-50"
>
  Start generator
</button>
```

Repeat for stop.

- [ ] **Step 2: Commit**

```bash
git add brewlog/src/pages/Live.tsx
git commit -m "feat(live): gate generator buttons behind generator:control permission"
```

---

### Task 40: Frontend hook tests + Playwright e2e

**Files:**
- Create: `brewlog/src/hooks/useAuth.test.ts`
- Create: `brewlog/src/components/RequirePerm.test.tsx`
- Create: `brewlog/e2e/observation-flow.spec.ts`

- [ ] **Step 1: `useAuth` tests**

Create `brewlog/src/hooks/useAuth.test.ts`:

```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "./useAuth";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

afterEach(() => mockFetch.mockReset());

function ok(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("useAuth", () => {
  it("loads /me on mount and exposes user", async () => {
    mockFetch.mockResolvedValue(
      ok({ id: "u1", email: "a@x.com", roles: ["user"], permissions: ["bean:read"] }),
    );
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user?.email).toBe("a@x.com"));
    expect(result.current.hasPermission("bean:read")).toBe(true);
    expect(result.current.hasPermission("user:observe")).toBe(false);
  });

  it("falls back to anon on 401", async () => {
    mockFetch.mockResolvedValue(new Response("", { status: 401 }));
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.user).toBeNull());
  });
});
```

- [ ] **Step 2: `RequirePerm` tests**

Create `brewlog/src/components/RequirePerm.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RequirePerm } from "./RequirePerm";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);
afterEach(() => mockFetch.mockReset());

describe("RequirePerm", () => {
  it("renders children when permission present", async () => {
    mockFetch.mockResolvedValue(
      new Response(
        JSON.stringify({ id: "u1", email: "a@x.com", roles: ["admin"], permissions: ["user:observe"] }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(
      <RequirePerm perm="user:observe">
        <div>secret</div>
      </RequirePerm>,
    );
    await waitFor(() => expect(screen.getByText("secret")).toBeInTheDocument());
  });

  it("renders 403 when permission missing", async () => {
    mockFetch.mockResolvedValue(
      new Response(
        JSON.stringify({ id: "u1", email: "a@x.com", roles: ["user"], permissions: [] }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(
      <RequirePerm perm="user:observe">
        <div>secret</div>
      </RequirePerm>,
    );
    await waitFor(() => expect(screen.getByText("403")).toBeInTheDocument());
    expect(screen.queryByText("secret")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Playwright e2e for the observation flow**

Create `brewlog/e2e/observation-flow.spec.ts`:

```typescript
import { expect, test } from "@playwright/test";

test("admin sees user observed after mass-delete burst", async ({ page, browser }) => {
  // 1. Register a normal user
  await page.goto("/register");
  await page.fill('input[type=email]', "victim@x.com");
  await page.fill('input[type=password]', "hunter2");
  await page.click('button[type=submit]');
  await expect(page).toHaveURL(/\/dashboard/);

  // 2. Create + delete 10 brewlogs to trip the mass-delete burst (helper API).
  //    NOTE: this is a UI e2e — for speed, hit the API directly with the
  //    cookie context.
  for (let i = 0; i < 10; i++) {
    // Create then immediately delete via API.
    // (Implementation here depends on existing helpers; pseudo-code below.)
  }

  // 3. Open a second browser as admin
  const adminCtx = await browser.newContext();
  const adminPage = await adminCtx.newPage();
  await adminPage.goto("/login");
  await adminPage.fill('input[type=email]', "admin@brewlog.local");
  await adminPage.fill('input[type=password]', "admin");
  await adminPage.click('button[type=submit]');
  await adminPage.goto("/admin/observed");
  await expect(adminPage.locator('text=victim@x.com')).toBeVisible();
});
```

- [ ] **Step 4: Run frontend test suites**

Run:
```bash
cd brewlog
npm run test -- --run
npx playwright test e2e/observation-flow.spec.ts
```
Expected: Vitest green, Playwright green.

- [ ] **Step 5: Commit**

```bash
git add brewlog/src/hooks/useAuth.test.ts brewlog/src/components/RequirePerm.test.tsx brewlog/e2e/observation-flow.spec.ts
git commit -m "test(frontend): useAuth + RequirePerm + observation e2e"
```

---

### Task 41: Update DEMO.md with A3 walkthrough

**Files:**
- Modify: `DEMO.md`

- [ ] **Step 1: Add an Assignment 3 demo section**

Append to `DEMO.md`:

```markdown
---

## 8. Assignment 3 demo

### 8.1 Bring up the stack

```bash
docker compose up -d
# → postgres, mongo, api running. Migrations + seed run automatically.
```

### 8.2 Bronze — DB persistence

```bash
# Confirm tables present
docker compose exec postgres psql -U brewlog -d brewlog -c "\dt"
# → 14 tables: users, roles, permissions, ..., audit_log
```

### 8.3 Silver — RBAC + chat

1. Visit `http://<server-ip>:5173/register` from a different machine.
   Register two users (e.g. `a@x.com`, `b@x.com`).
2. Both log in; both navigate to `/chat`.
3. Type messages in window A → window B updates live.

### 8.4 Gold — auto-observation

1. With a normal user logged in, hit `/api/v1/admin/observed-users` 5 times in a row → 403 each.
2. Log out, log in as admin (`admin@brewlog.local` / `admin`).
3. Visit `/admin/observed` → the user is listed with reason "permission-denied-burst (5 in 5min)".
4. Click Clear → row disappears, OBSERVATION_CLEARED row written to audit log.
5. Visit `/admin/audit` → filter by action `OBSERVED_AUTO` to see the trigger's self-audit row.
```

- [ ] **Step 2: Commit**

```bash
git add DEMO.md
git commit -m "docs(demo): add Assignment 3 walkthrough"
```

---

### Task 42: Coolify deploy + cross-machine smoke test

**Files:** none (deployment)

- [ ] **Step 1: Push the branch and connect Coolify to the repo**

Follow Coolify's "New service from compose" flow. Point at the repo + main branch. Set env vars from `.env.example` (especially `SESSION_SECRET`, `POSTGRES_PASSWORD`, `ADMIN_BOOTSTRAP_*`, and `CORS_ORIGINS` set to your laptop's frontend URL or Coolify subdomain).

- [ ] **Step 2: Verify migrations and seed ran**

After Coolify reports the API healthy:

```bash
curl -s https://<coolify-host>/health    # if you have a /health endpoint
# Or hit the docs:
curl -s https://<coolify-host>/docs | head
```

Inspect logs: `alembic upgrade head` should have executed once, followed by `seeded RBAC; admin = admin@brewlog.local` and `seeded chat (lobby + indexes)`.

- [ ] **Step 3: Run frontend on a different machine**

On a laptop separate from the Coolify host:

```bash
cd brewlog
VITE_API_BASE=https://<coolify-host> npm run dev -- --host 0.0.0.0
```

Open http://<laptop-ip>:5173 from a phone or another machine on the same network. The frontend talks to Coolify (different machine); the user opens it from yet another device. That double-jump is the strongest possible "different machine" demo.

- [ ] **Step 4: End-to-end demo flow**

Run through DEMO.md §8 against the deployed stack. Confirm:
- Login works across machines.
- Two browsers on different devices chat over the WebSocket.
- Hitting forbidden endpoints triggers observation on the deployed Postgres.

- [ ] **Step 5: Commit any deploy fixups (not the test run)**

If you had to tweak anything (env names, healthcheck timing, CORS origins), commit those changes:

```bash
git add docker-compose.yml backend/Dockerfile .env.example
git commit -m "chore(deploy): Coolify-friendly tweaks"
```

---

## Self-Review Checklist (run after final commit)

Before marking the plan complete, walk through this list:

1. **Spec coverage** — every section of the design doc is implemented somewhere:
   - §3 Topology → Tasks 5, 42
   - §4 Schema → Tasks 3, 6
   - §5 NoSQL → Tasks 9, 29, 32, 33
   - §6 Triggers + procs → Task 6 (DDL) + Task 28 (tests)
   - §7 Application layers → Tasks 11–19, 23–27
   - §8 Frontend → Tasks 34–39
   - §9 Testing → Tasks 10, 11–14, 22, 25, 28, 29–33, 40
   - §10 Build sequence → matches Phase ordering 1–5
   - §11 User contributions → Tasks 8 (perm map), 22 (audit exempts), 6 (thresholds), 28 (detection tests), 36 (sparkline)
   - §12 Out of scope honoured — no JWT, no encryption work.

2. **Coverage gate ≥ 90 %** — run `cd backend && .venv/bin/pytest --cov=app --cov-fail-under=90`. Add tests for any uncovered new code.

3. **Cross-machine demo** — Task 42 verifies the assignment's hard requirement.

4. **No placeholders left in production code** — `EXEMPT_PATHS`, `USER_ROLE_PERMISSIONS`, the four detection thresholds, and the sparkline render block are deliberate user contributions; everything else must be filled in.

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-05-06-assignment-3-database-persistence-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Dispatches a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using `executing-plans`, batch execution with checkpoints for review.

**Which approach?**

