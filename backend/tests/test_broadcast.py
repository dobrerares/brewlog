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
