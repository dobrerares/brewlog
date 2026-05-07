"""Topic-based fan-out manager. Replaces the global ConnectionManager from A2.

Subscribers register against a topic string; publishes are scoped to that topic.
A failing send is dropped silently (treats the socket as disconnected) so one
bad client cannot stop a broadcast.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol


class _SocketLike(Protocol):
    async def send_json(self, data: Any) -> None: ...


class BroadcastManager:
    def __init__(self) -> None:
        self._subs: dict[str, set[_SocketLike]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, socket: _SocketLike) -> None:
        async with self._lock:
            self._subs.setdefault(topic, set()).add(socket)

    async def unsubscribe(self, topic: str, socket: _SocketLike) -> None:
        async with self._lock:
            self._subs.get(topic, set()).discard(socket)
            if not self._subs.get(topic):
                self._subs.pop(topic, None)

    async def unsubscribe_all(self, socket: _SocketLike) -> None:
        async with self._lock:
            for topic in list(self._subs.keys()):
                self._subs[topic].discard(socket)
                if not self._subs[topic]:
                    self._subs.pop(topic, None)

    async def publish(self, topic: str, payload: dict) -> None:
        async with self._lock:
            sockets = list(self._subs.get(topic, set()))
        for s in sockets:
            try:
                await s.send_json(payload)
            except Exception:  # noqa: BLE001
                # Socket is dead; remove it so it stops receiving.
                async with self._lock:
                    self._subs.get(topic, set()).discard(s)


# Singleton broadcaster shared between WS handler and chat service.
broadcaster = BroadcastManager()


# ---------------------------------------------------------------------------
# Backwards-compat shim — keeps A2 callers (state.py, generator.py,
# websocket.py) working until Task 33 rewrites them.
# ---------------------------------------------------------------------------

_GLOBAL_TOPIC = "__global__"


class ConnectionManager(BroadcastManager):
    """Drop-in replacement for the old global ConnectionManager.

    Wraps the topic-based API under the single ``_GLOBAL_TOPIC`` topic so
    that pre-Task-33 callers continue to work without modification.

    Will be removed when websocket.py and generator.py are ported (Task 33).
    """

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        await self.subscribe(_GLOBAL_TOPIC, websocket)

    async def disconnect(self, websocket: Any) -> None:
        await self.unsubscribe(_GLOBAL_TOPIC, websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        await self.publish(_GLOBAL_TOPIC, message)

    @property
    def connection_count(self) -> int:
        return len(self._subs.get(_GLOBAL_TOPIC, set()))
