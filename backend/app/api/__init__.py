from fastapi import APIRouter

from . import beans, brewlogs, equipment, generator, roasters, stats, websocket

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(brewlogs.router)
api_router.include_router(beans.router)
api_router.include_router(equipment.router)
api_router.include_router(roasters.router)
api_router.include_router(stats.router)
api_router.include_router(generator.router)

# WebSocket is mounted at the app root (no /api/v1 prefix) so URLs stay short.
ws_router = websocket.router

__all__ = ["api_router", "ws_router"]
