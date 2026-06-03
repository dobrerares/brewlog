"""MongoDB client (motor) — chat-only.

The async client is created at startup and disposed at shutdown.
Collection names are constants so callers can't typo their way to a missing index.
"""

from __future__ import annotations

import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

CHAT_ROOMS = "chat_rooms"
CHAT_MESSAGES = "chat_messages"
DEFAULT_DB_NAME = "brewlog_chat"

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def mongo_database_name() -> str:
    return os.environ.get("MONGO_DB", DEFAULT_DB_NAME)


def init_mongo(mongo_url: str | None = None, database_name: str | None = None) -> AsyncIOMotorDatabase:
    global _client, _db
    url = mongo_url or os.environ["MONGO_URL"]
    _client = AsyncIOMotorClient(url)
    _db = _client.get_default_database(default=database_name or mongo_database_name())
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
