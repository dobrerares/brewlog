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


def async_database_url(database_url: str) -> str:
    """Accept Railway-style Postgres URLs while using SQLAlchemy's asyncpg driver."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url


def init_engine(database_url: str | None = None) -> AsyncEngine:
    """Create the global engine. Call once at app startup."""
    global _engine, _factory
    url = async_database_url(database_url or os.environ["DATABASE_URL"])
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
