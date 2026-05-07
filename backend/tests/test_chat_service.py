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
