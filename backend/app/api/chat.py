"""Chat REST endpoints — rooms list, DM upsert, message history."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from bson import ObjectId, errors
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import current_user, requires
from app.auth.permissions import PERM_CHAT_READ, PERM_CHAT_SEND
from app.db.models import User
from app.db.mongo import get_db as get_mongo_db
from app.repositories.chat import ChatRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _repo() -> ChatRepository:
    return ChatRepository(get_mongo_db())


def _serialise_room(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "type": doc["type"],
        "name": doc.get("name"),
        "participants": doc.get("participants", []),
        "last_message_at": doc.get("last_message_at"),
    }


def _serialise_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "room_id": str(doc["room_id"]),
        "from_user_id": doc["from_user_id"],
        "body": doc["body"],
        "created_at": doc["created_at"],
    }


def _parse_room_id(room_id: str) -> ObjectId:
    try:
        return ObjectId(room_id)
    except errors.InvalidId:
        raise HTTPException(404, detail="room not found")


@router.get("/rooms")
async def list_rooms(
    user: User = Depends(requires(PERM_CHAT_READ)),
    repo: ChatRepository = Depends(_repo),
):
    rooms = await repo.list_rooms_for_user(user.id)
    return [_serialise_room(r) for r in rooms]


@router.post("/rooms", status_code=201)
async def upsert_dm(
    payload: dict,
    user: User = Depends(requires(PERM_CHAT_SEND)),
    repo: ChatRepository = Depends(_repo),
):
    other_id_str = payload.get("participant_id")
    if not other_id_str:
        raise HTTPException(400, detail="participant_id required")
    try:
        other = UUID(other_id_str)
    except ValueError:
        raise HTTPException(400, detail="participant_id must be a UUID")
    room = await repo.upsert_dm(user.id, other)
    return _serialise_room(room)


@router.get("/rooms/{room_id}/messages")
async def history(
    room_id: str,
    before: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    user: User = Depends(requires(PERM_CHAT_READ)),
    repo: ChatRepository = Depends(_repo),
):
    oid = _parse_room_id(room_id)
    rows = await repo.history(oid, before=before, limit=limit)
    return [_serialise_message(r) for r in rows]
