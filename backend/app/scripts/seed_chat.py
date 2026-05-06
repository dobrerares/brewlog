"""Create Mongo indexes and seed the lobby room. Idempotent."""

from __future__ import annotations

import asyncio

from pymongo import ASCENDING, DESCENDING

from app.db.mongo import CHAT_ROOMS, init_mongo, close_mongo, messages, rooms


async def seed() -> None:
    init_mongo()

    # Indexes
    await rooms().create_index(
        [("participant_pair", ASCENDING)],
        unique=True,
        partialFilterExpression={"type": "dm"},
        name="ix_room_pair_unique_dm",
    )
    await rooms().create_index([("participants", ASCENDING)], name="ix_room_participants")
    await messages().create_index(
        [("room_id", ASCENDING), ("created_at", DESCENDING)], name="ix_msg_room_time"
    )

    # Lobby room
    existing = await rooms().find_one({"type": "room", "name": "lobby"})
    if existing is None:
        await rooms().insert_one(
            {
                "type": "room",
                "name": "lobby",
                "participants": [],
                "participant_pair": None,
                "created_at": __import__("datetime").datetime.utcnow(),
                "last_message_at": None,
            }
        )
    print("seeded chat (lobby + indexes)")
    await close_mongo()


if __name__ == "__main__":
    asyncio.run(seed())
