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
