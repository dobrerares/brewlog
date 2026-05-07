"""Statistics endpoints — SQL-aggregated over the brewlogs table."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Brewlog
from app.schemas import BrewStats, MethodCount, TasteCount
from app.schemas.common import BrewMethod, TasteResult

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/brewlogs", response_model=BrewStats)
async def brewlog_stats(
    db: AsyncSession = Depends(get_db),
) -> BrewStats:
    total = await db.scalar(select(func.count(Brewlog.id)))
    total = total or 0

    if total == 0:
        return BrewStats(
            total_brews=0,
            average_rating=None,
            most_used_method=None,
            by_method=[],
            by_taste=[],
            balanced_ratio=None,
        )

    # Average rating
    raw_avg = await db.scalar(select(func.avg(Brewlog.rating)))
    avg_rating = round(float(raw_avg), 2) if raw_avg is not None else None

    # By-method breakdown — descending count order
    method_rows = (
        await db.execute(
            select(Brewlog.method, func.count().label("cnt"))
            .group_by(Brewlog.method)
            .order_by(func.count().desc())
        )
    ).all()
    by_method = [MethodCount(method=BrewMethod(m), count=c) for m, c in method_rows]
    most_used_method = by_method[0].method if by_method else None

    # By-taste breakdown — exclude rows with no taste_result
    taste_rows = (
        await db.execute(
            select(Brewlog.taste_result, func.count().label("cnt"))
            .where(Brewlog.taste_result.is_not(None))
            .group_by(Brewlog.taste_result)
            .order_by(func.count().desc())
        )
    ).all()
    by_taste = [TasteCount(taste_result=TasteResult(t), count=c) for t, c in taste_rows]

    # Balanced ratio
    rated_count = sum(entry.count for entry in by_taste)
    balanced_count = next(
        (entry.count for entry in by_taste if entry.taste_result == TasteResult.BALANCED),
        0,
    )
    balanced_ratio = (
        round(balanced_count / rated_count, 3) if rated_count else None
    )

    return BrewStats(
        total_brews=total,
        average_rating=avg_rating,
        most_used_method=most_used_method,
        by_method=by_method,
        by_taste=by_taste,
        balanced_ratio=balanced_ratio,
    )
