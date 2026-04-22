"""WebSocket connection manager — fan-out JSON messages to every client.

Kept deliberately simple: no rooms, no auth. Listeners subscribe by opening a
WebSocket to `/ws`; the generator service pushes `{"type": "...", "data": ...}`
envelopes through `broadcast()`.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send a JSON message to every connected client.

        Connections that fail to accept the message are removed silently —
        they will reconnect or not on their own.
        """
        async with self._lock:
            targets = list(self._connections)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:  # pragma: no cover — connection already closed
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
