"""Silver challenge tests: Faker generator endpoints + WebSocket broadcast."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services import get_state


def test_status_reports_idle_on_boot(client: TestClient) -> None:
    response = client.get("/api/v1/generator/status")
    assert response.status_code == 200
    body = response.json()
    assert body["running"] is False
    assert body["batches_emitted"] == 0
    assert body["items_emitted"] == 0


def test_stop_before_start_returns_409(client: TestClient) -> None:
    response = client.post("/api/v1/generator/stop")
    assert response.status_code == 409


def test_start_validates_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/generator/start", json={"batch_size": 0, "interval_s": 1}
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/generator/start", json={"batch_size": 2, "interval_s": 0}
    )
    assert response.status_code == 422


def test_tick_emits_a_single_batch(client: TestClient) -> None:
    response = client.post("/api/v1/generator/tick")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    # The batch populates brewlogs and their prerequisites.
    assert client.get("/api/v1/brewlogs").json()["total"] == body["count"]
    # Prereqs: one roaster + one bean + one brewer + one grinder.
    assert client.get("/api/v1/roasters").json()["total"] == 1
    assert client.get("/api/v1/beans").json()["total"] == 1
    assert client.get("/api/v1/equipment").json()["total"] == 2


@pytest.mark.asyncio
async def test_start_and_stop_cycle() -> None:
    # Must share one event loop across requests — TestClient spins a new
    # loop per call which would immediately orphan the background task.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        start = await ac.post(
            "/api/v1/generator/start", json={"batch_size": 2, "interval_s": 30}
        )
        assert start.status_code == 202
        assert start.json()["running"] is True

        duplicate = await ac.post(
            "/api/v1/generator/start", json={"batch_size": 2, "interval_s": 30}
        )
        assert duplicate.status_code == 409

        stop = await ac.post("/api/v1/generator/stop")
        assert stop.status_code == 202
        assert stop.json()["running"] is False


@pytest.mark.asyncio
async def test_emit_once_broadcasts_to_websocket_clients(client: TestClient) -> None:
    # Connect, call /tick which emits a batch, then receive the broadcast.
    with client.websocket_connect("/ws") as ws:
        response = client.post("/api/v1/generator/tick")
        assert response.status_code == 200
        emitted = response.json()["count"]

        message = ws.receive_json()
        assert message["type"] == "brewlog.batch"
        assert message["count"] == emitted
        assert len(message["items"]) == emitted
        # items are valid BrewLog dumps
        first = message["items"][0]
        assert "id" in first and "method" in first and "rating" in first


def test_generator_reuses_existing_seed_entities(client: TestClient) -> None:
    # Seed a roaster manually first — the generator should not duplicate it.
    manual = client.post("/api/v1/roasters", json={"name": "Already here"}).json()
    client.post("/api/v1/generator/tick")
    roasters = client.get("/api/v1/roasters").json()
    assert roasters["total"] == 1
    assert roasters["items"][0]["id"] == manual["id"]


def test_broadcast_drops_dead_connections(client: TestClient) -> None:
    # After disconnecting, the manager should clean up its connection set.
    state = get_state()
    with client.websocket_connect("/ws"):
        assert state.broadcaster.connection_count == 1
    # Allow the disconnect handler to run by triggering another op.
    client.post("/api/v1/generator/tick")
    assert state.broadcaster.connection_count == 0


def test_ws_survives_client_text_messages(client: TestClient) -> None:
    # Clients may send keep-alive pings; the handler just reads and ignores.
    with client.websocket_connect("/ws") as ws:
        ws.send_text(json.dumps({"ping": True}))
        client.post("/api/v1/generator/tick")
        message = ws.receive_json()
        assert message["type"] == "brewlog.batch"
