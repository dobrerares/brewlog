"""Silver challenge: start / stop / inspect the async Faker loop."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services import AppState, BrewLogGenerator, get_state

router = APIRouter(prefix="/generator", tags=["generator"])


class StartRequest(BaseModel):
    """Payload for `POST /generator/start`."""

    batch_size: int = Field(3, ge=1, le=50, description="Items produced per batch")
    interval_s: float = Field(1.0, gt=0, le=60, description="Seconds between batches")


def _generator(state: AppState = Depends(get_state)) -> BrewLogGenerator:
    gen = state.generator
    if not isinstance(gen, BrewLogGenerator):  # pragma: no cover — bootstrap guarantees this
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "generator unavailable")
    return gen


@router.get("/status")
def generator_status(
    gen: BrewLogGenerator = Depends(_generator),
) -> dict[str, object]:
    return gen.status()


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_generator(
    payload: StartRequest,
    gen: BrewLogGenerator = Depends(_generator),
) -> dict[str, object]:
    if gen.is_running:
        raise HTTPException(status.HTTP_409_CONFLICT, "generator already running")
    await gen.start(batch_size=payload.batch_size, interval_s=payload.interval_s)
    return gen.status()


@router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_generator(
    gen: BrewLogGenerator = Depends(_generator),
) -> dict[str, object]:
    if not gen.is_running:
        raise HTTPException(status.HTTP_409_CONFLICT, "generator is not running")
    await gen.stop()
    return gen.status()


@router.post("/tick", status_code=status.HTTP_200_OK)
async def generator_tick(
    gen: BrewLogGenerator = Depends(_generator),
) -> dict[str, object]:
    """Emit one batch immediately — convenience for testing / manual demo."""
    produced = await gen.emit_once()
    return {"count": len(produced), "status": gen.status()}
