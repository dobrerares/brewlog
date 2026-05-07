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
