"""Shared pytest fixtures — resets the in-memory state for every test."""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import reset_state


@pytest.fixture(autouse=True)
def _fresh_state() -> Iterator[None]:
    reset_state()
    yield
    reset_state()


@pytest.fixture
def sync_client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------------------ factories


def make_roaster(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "Nomad Coffee",
        "location": "Barcelona",
        "website": "https://nomadcoffee.es/",
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/roasters", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_bean(client: TestClient, roaster_id: str | None = None, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Finca La Esperanza",
        "roaster_id": roaster_id,
        "origin_country": "Colombia",
        "origin_region": "Huila",
        "process": "Washed",
        "roast_level": "Light",
        "variety": "Caturra",
        "elevation_m": 1800,
        "tasting_notes": ["chocolate", "citrus"],
        "purchase_date": "2026-03-01",
        "price": "18.50",
    }
    payload.update(overrides)
    response = client.post("/api/v1/beans", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_brewer(client: TestClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Hario V60",
        "type": "Brewer",
        "brand": "Hario",
        "model": "02",
        "grind_type": None,
        "grind_range": None,
        "grind_unit": None,
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_grinder(client: TestClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Comandante C40",
        "type": "Grinder",
        "brand": "Comandante",
        "model": "MK4",
        "grind_type": "Stepped",
        "grind_range": "clicks 0-40",
        "grind_unit": "1 click",
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_brewlog(
    client: TestClient,
    bean_id: str,
    equipment_id: str,
    grinder_id: str,
    **overrides: object,
) -> dict:
    payload: dict[str, object] = {
        "date": "2026-04-01T08:30:00",
        "bean_id": bean_id,
        "equipment_id": equipment_id,
        "grinder_id": grinder_id,
        "grind_setting": "22 clicks",
        "method": "V60",
        "dose_g": "15",
        "water_g": "250",
        "water_temp_c": 94,
        "brew_time_s": 150,
        "yield_g": None,
        "rating": 4,
        "taste_result": "Balanced",
        "grind_adjustment": None,
        "tasting_notes": ["chocolate"],
        "notes": "Solid pourover.",
        "photo_url": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/brewlogs", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ─── Phase 1 testcontainers fixtures (Postgres + Mongo) ──────────────────────────

import asyncio as _asyncio_tc
import os as _os_tc
from collections.abc import AsyncIterator, Iterator as _Iterator_tc
from pathlib import Path as _Path_tc

from alembic import command as _alembic_command
from alembic.config import Config as _AlembicConfig
from motor.motor_asyncio import AsyncIOMotorClient as _AsyncIOMotorClient
from sqlalchemy.pool import NullPool as _NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker as _async_sessionmaker,
    create_async_engine as _create_async_engine,
)
from testcontainers.mongodb import MongoDbContainer
from testcontainers.postgres import PostgresContainer

ALEMBIC_INI = _Path_tc(__file__).resolve().parents[1] / "alembic.ini"


def _alembic_config(database_url: str) -> _AlembicConfig:
    cfg = _AlembicConfig(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    cfg.attributes["sqlalchemy.url"] = database_url  # not strictly needed; env.py reads env var
    _os_tc.environ["DATABASE_URL"] = database_url
    return cfg


@pytest.fixture(scope="session")
def pg_url() -> _Iterator_tc[str]:
    with PostgresContainer("postgres:16-alpine", username="brewlog", password="brewlog", dbname="brewlog") as pg:
        url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+asyncpg")
        cfg = _alembic_config(url)
        _alembic_command.upgrade(cfg, "head")
        yield url


@pytest.fixture(scope="session")
def engine(pg_url: str) -> _Iterator_tc[AsyncEngine]:
    """Session-scoped engine handle (URL only; NullPool — no live connections held)."""
    eng = _create_async_engine(pg_url, future=True, poolclass=_NullPool)
    yield eng
    # engine has NullPool so no connections to dispose; this is a no-op but clean
    try:
        _asyncio_tc.run(eng.dispose())
    except RuntimeError:
        pass  # already closed or no loop


@pytest.fixture
async def db(pg_url: str) -> AsyncIterator[AsyncSession]:
    """Per-test async session — fresh engine per test to avoid cross-loop issues."""
    eng = _create_async_engine(pg_url, future=True, poolclass=_NullPool)
    async with eng.connect() as conn:
        trans = await conn.begin()
        factory = _async_sessionmaker(bind=conn, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            yield session
        await trans.rollback()
    await eng.dispose()


@pytest.fixture(scope="session")
def mongo_url() -> _Iterator_tc[str]:
    with MongoDbContainer("mongo:7") as mc:
        yield mc.get_connection_url() + "/brewlog_test"


@pytest.fixture
async def mongo(mongo_url: str) -> AsyncIterator:
    client = _AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    yield db
    await client.drop_database(db.name)
    client.close()


# ─── Async HTTP client fixture (Task 16+) — DB-backed handler tests ──────────

from httpx import ASGITransport, AsyncClient as _AsyncClient

from app.api.deps import get_db as _api_get_db
from app.db.models import User as _User
from sqlalchemy.dialects.postgresql import insert as _pg_insert


@pytest.fixture
async def client(db: AsyncSession) -> AsyncIterator[_AsyncClient]:
    async def _override():
        yield db

    app.dependency_overrides[_api_get_db] = _override
    transport = ASGITransport(app=app)
    async with _AsyncClient(transport=transport, base_url="http://test") as c:
        # Ensure the dev user exists for unauthenticated handlers (Phase 2 only)
        from uuid import UUID as _UUID
        await db.execute(
            _pg_insert(_User)
            .values(id=_UUID("00000000-0000-0000-0000-000000000001"), email="dev@x.com", password_hash="x")
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await db.flush()
        yield c
    app.dependency_overrides.clear()
