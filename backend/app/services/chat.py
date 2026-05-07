"""Chat service — coordinates Mongo writes and topic fan-out."""

from __future__ import annotations

from uuid import UUID

from bson import ObjectId

from app.repositories.chat import ChatRepository
from app.services.broadcast import BroadcastManager


def _topic_for(room_id) -> str:
    return f"room:{room_id}"


def _serialise(msg: dict) -> dict:
    return {
        "id": str(msg["_id"]),
        "room_id": str(msg["room_id"]),
        "from_user_id": msg["from_user_id"],
        "body": msg["body"],
        "created_at": msg["created_at"].isoformat(),
    }


class ChatService:
    def __init__(self, repo: ChatRepository, bus: BroadcastManager) -> None:
        self.repo = repo
        self.bus = bus

    async def send(self, *, room_id, from_user_id: UUID, body: str) -> dict:
        msg = await self.repo.add_message(room_id=room_id, from_user_id=from_user_id, body=body)
        payload = {"type": "message", "room_id": str(msg["room_id"]), "msg": _serialise(msg)}
        await self.bus.publish(_topic_for(msg["room_id"]), payload)
        return msg

    async def join_topic(self, room_id, socket) -> None:
        await self.bus.subscribe(_topic_for(room_id), socket)

    async def leave_topic(self, room_id, socket) -> None:
        await self.bus.unsubscribe(_topic_for(room_id), socket)
