from fastapi import APIRouter

from . import beans, brewlogs, equipment, roasters, stats

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(brewlogs.router)
api_router.include_router(beans.router)
api_router.include_router(equipment.router)
api_router.include_router(roasters.router)
api_router.include_router(stats.router)

__all__ = ["api_router"]
