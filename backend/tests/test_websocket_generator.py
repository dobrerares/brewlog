"""WebSocket bridge coverage for live brew generator batches."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import WebSocketDisconnect

from app.api import websocket as ws_api
from app.services import reset_state


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.closed_code: int | None = None
        self.sent: list[dict] = []
        self.receive_started = asyncio.Event()
        self.stop_receiving = asyncio.Event()

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int) -> None:
        self.closed_code = code

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)

    async def receive_json(self) -> dict:
        self.receive_started.set()
        await self.stop_receiving.wait()
        raise WebSocketDisconnect()


@pytest.mark.asyncio
async def test_ws_subscribes_to_generator_broadcasts(monkeypatch: pytest.MonkeyPatch) -> None:
    state = reset_state()
    user_id = uuid4()

    @asynccontextmanager
    async def fake_session_factory():
        yield object()

    async def fake_lookup_session(_db: object, _session_id: object) -> SimpleNamespace:
        return SimpleNamespace(user_id=user_id)

    def fake_jwt_decode(_token: str, expected_type: str) -> dict[str, str]:
        assert expected_type == "access"
        return {"sub": str(user_id)}

    class FakeUserRepository:
        def __init__(self, _db: object) -> None:
            pass

        async def get_with_perms(self, _user_id: object) -> SimpleNamespace:
            return SimpleNamespace(id=user_id)

    monkeypatch.setattr(ws_api, "session_factory", lambda: lambda: fake_session_factory())
    monkeypatch.setattr(ws_api, "lookup_session", fake_lookup_session)
    monkeypatch.setattr(ws_api, "jwt_decode", fake_jwt_decode)
    monkeypatch.setattr(ws_api, "UserRepository", FakeUserRepository)
    monkeypatch.setattr(ws_api, "get_mongo_db", lambda: object())

    websocket = FakeWebSocket()
    task = asyncio.create_task(ws_api.websocket_endpoint(websocket, access_token="access"))
    await asyncio.wait_for(websocket.receive_started.wait(), timeout=1)

    assert websocket.accepted is True
    assert state.broadcaster.connection_count == 1
    assert websocket.sent[0]["type"] == "ready"

    await state.broadcaster.broadcast({"type": "brewlog.batch", "count": 1, "items": []})
    assert websocket.sent[-1] == {"type": "brewlog.batch", "count": 1, "items": []}

    websocket.stop_receiving.set()
    await asyncio.wait_for(task, timeout=1)
    assert state.broadcaster.connection_count == 0
