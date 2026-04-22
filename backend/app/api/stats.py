"""Statistics endpoints computed over the brewlog collection."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends

from app.schemas import BrewLog, BrewStats, MethodCount, TasteCount
from app.schemas.common import BrewMethod, TasteResult
from app.services import InMemoryStore

from .deps import brewlog_store

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/brewlogs", response_model=BrewStats)
def brewlog_stats(
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
) -> BrewStats:
    brews = store.list()
    total = len(brews)

    if total == 0:
        return BrewStats(
            total_brews=0,
            average_rating=None,
            most_used_method=None,
            by_method=[],
            by_taste=[],
            balanced_ratio=None,
        )

    by_method: Counter[BrewMethod] = Counter(b.method for b in brews)
    by_taste: Counter[TasteResult] = Counter(
        b.taste_result for b in brews if b.taste_result is not None
    )

    avg_rating = sum(b.rating for b in brews) / total
    most_used, _ = by_method.most_common(1)[0]
    balanced = by_taste.get(TasteResult.BALANCED, 0)
    rated_count = sum(by_taste.values())
    balanced_ratio = balanced / rated_count if rated_count else None

    return BrewStats(
        total_brews=total,
        average_rating=round(avg_rating, 2),
        most_used_method=most_used,
        by_method=[MethodCount(method=m, count=c) for m, c in by_method.most_common()],
        by_taste=[TasteCount(taste_result=t, count=c) for t, c in by_taste.most_common()],
        balanced_ratio=round(balanced_ratio, 3) if balanced_ratio is not None else None,
    )
