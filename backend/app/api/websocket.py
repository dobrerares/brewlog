"""WebSocket handler — multiplexed by frame envelope (chat rooms + brewlog feed)."""

from __future__ import annotations

import json
from uuid import UUID

from bson import ObjectId, errors as bson_errors
from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect

from app.auth.sessions import lookup_session
from app.auth.tokens import TokenError, jwt_decode
from app.db.base import session_factory
from app.db.mongo import get_db as get_mongo_db
from app.repositories.chat import ChatRepository
from app.repositories.users import UserRepository
from app.services import get_state
from app.services.audit import write_audit
from app.services.broadcast import broadcaster
from app.services.chat import ChatService

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    access_token: str | None = Cookie(default=None),
    session_id: str | None = Cookie(default=None),
):
    user_id: UUID | None = None
    sid: UUID | None = None
    if access_token:
        try:
            claims = jwt_decode(access_token, "access")
            user_id = UUID(claims["sub"])
        except (KeyError, ValueError, TokenError):
            await websocket.close(code=4401)
            return
    elif session_id:
        try:
            sid = UUID(session_id)
        except ValueError:
            await websocket.close(code=4401)
            return
    else:
        await websocket.close(code=4401)
        return

    factory = session_factory()
    async with factory() as db:
        if user_id is None:
            if sid is None:
                await websocket.close(code=4401)
                return
            sess = await lookup_session(db, sid)
            if sess is None:
                await websocket.close(code=4401)
                return
            user_id = sess.user_id
        user = await UserRepository(db).get_with_perms(user_id)
        if user is None:
            await websocket.close(code=4401)
            return

    state = get_state()
    await state.broadcaster.connect(websocket)
    await websocket.send_json({"type": "ready", "user_id": str(user.id)})

    chat = ChatService(ChatRepository(get_mongo_db()), broadcaster)
    joined: set[str] = set()

    try:
        while True:
            frame = await websocket.receive_json()
            kind = frame.get("type")

            if kind == "join":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                await chat.join_topic(oid, websocket)
                joined.add(str(oid))
                history = await chat.repo.history(oid, limit=50)
                await websocket.send_json({
                    "type": "history",
                    "room_id": str(oid),
                    "messages": [
                        {
                            "id": str(m["_id"]),
                            "room_id": str(m["room_id"]),
                            "from_user_id": m["from_user_id"],
                            "body": m["body"],
                            "created_at": m["created_at"].isoformat(),
                        }
                        for m in history
                    ],
                })

            elif kind == "send":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                body = (frame.get("body") or "").strip()
                if not body or len(body) > 2000:
                    continue
                async with factory() as db:
                    await write_audit(db, user_id=user.id, action="CHAT_SEND", status="OK")
                    await db.commit()
                await chat.send(room_id=oid, from_user_id=user.id, body=body)

            elif kind == "leave":
                try:
                    oid = ObjectId(frame["room_id"])
                except (KeyError, bson_errors.InvalidId):
                    continue
                await chat.leave_topic(oid, websocket)
                joined.discard(str(oid))

    except WebSocketDisconnect:
        pass
    finally:
        await state.broadcaster.disconnect(websocket)
        await broadcaster.unsubscribe_all(websocket)
