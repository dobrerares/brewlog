"""MongoDB chat repository — rooms + messages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING


def _pair_key(a: UUID, b: UUID) -> str:
    lo, hi = sorted([str(a), str(b)])
    return f"{lo}:{hi}"


class ChatRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def bootstrap_lobby(self) -> None:
        await self.db["chat_rooms"].create_index(
            [("participant_pair", ASCENDING)],
            unique=True,
            partialFilterExpression={"type": "dm"},
            name="ix_room_pair_unique_dm",
        )
        await self.db["chat_rooms"].create_index([("participants", ASCENDING)], name="ix_room_participants")
        await self.db["chat_messages"].create_index(
            [("room_id", ASCENDING), ("created_at", DESCENDING)], name="ix_msg_room_time"
        )
        existing = await self.db["chat_rooms"].find_one({"type": "room", "name": "lobby"})
        if existing is None:
            await self.db["chat_rooms"].insert_one(
                {
                    "type": "room",
                    "name": "lobby",
                    "participants": [],
                    "participant_pair": None,
                    "created_at": datetime.now(timezone.utc),
                    "last_message_at": None,
                }
            )

    async def find_room_by_name(self, name: str) -> dict | None:
        return await self.db["chat_rooms"].find_one({"type": "room", "name": name})

    async def find_room(self, room_id: ObjectId | str) -> dict | None:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        return await self.db["chat_rooms"].find_one({"_id": room_id})

    async def list_rooms_for_user(self, user_id: UUID) -> list[dict]:
        cursor = self.db["chat_rooms"].find(
            {"$or": [{"name": "lobby"}, {"participants": str(user_id)}]}
        )
        return [doc async for doc in cursor]

    async def upsert_dm(self, user_a: UUID, user_b: UUID) -> dict:
        pair = _pair_key(user_a, user_b)
        result = await self.db["chat_rooms"].find_one_and_update(
            {"type": "dm", "participant_pair": pair},
            {
                "$setOnInsert": {
                    "type": "dm",
                    "participants": sorted([str(user_a), str(user_b)]),
                    "participant_pair": pair,
                    "created_at": datetime.now(timezone.utc),
                    "last_message_at": None,
                    "name": None,
                }
            },
            upsert=True,
            return_document=True,
        )
        return result

    async def add_message(
        self, room_id: ObjectId | str, from_user_id: UUID, body: str
    ) -> dict:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        now = datetime.now(timezone.utc)
        doc = {
            "room_id": room_id,
            "from_user_id": str(from_user_id),
            "body": body,
            "created_at": now,
        }
        result = await self.db["chat_messages"].insert_one(doc)
        doc["_id"] = result.inserted_id
        await self.db["chat_rooms"].update_one(
            {"_id": room_id}, {"$set": {"last_message_at": now}}
        )
        return doc

    async def history(
        self, room_id: ObjectId | str, *, before: datetime | None = None, limit: int = 50
    ) -> list[dict]:
        if not isinstance(room_id, ObjectId):
            room_id = ObjectId(room_id)
        query: dict[str, Any] = {"room_id": room_id}
        if before is not None:
            query["created_at"] = {"$lt": before}
        cursor = (
            self.db["chat_messages"]
            .find(query)
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return [doc async for doc in cursor]
