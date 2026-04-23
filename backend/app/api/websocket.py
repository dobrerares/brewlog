"""Silver challenge: WebSocket endpoint clients subscribe to for batch pushes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.services import AppState, get_state

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def brewlog_ws(
    websocket: WebSocket,
    state: AppState = Depends(get_state),
) -> None:
    await state.broadcaster.connect(websocket)
    try:
        while True:
            # The client doesn't need to send anything, but reading keeps
            # the connection open and lets us observe disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await state.broadcaster.disconnect(websocket)
