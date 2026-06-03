"""Statistics endpoints — SQL-aggregated over the brewlogs table."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, requires
from app.auth.permissions import PERM_BREWLOG_READ
from app.db.models import Bean, BeanTastingNote, Brewlog, BrewlogTastingNote, TastingNote, User
from app.schemas import BrewStats, MethodCount, TasteCount
from app.schemas.common import BrewMethod, TasteResult

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/brewlogs", response_model=BrewStats)
async def brewlog_stats(
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    db: AsyncSession = Depends(get_db),
) -> BrewStats:
    total = await db.scalar(
        select(func.count(Brewlog.id)).where(Brewlog.user_id == user.id)
    )
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
    raw_avg = await db.scalar(
        select(func.avg(Brewlog.rating)).where(Brewlog.user_id == user.id)
    )
    avg_rating = round(float(raw_avg), 2) if raw_avg is not None else None

    # By-method breakdown — descending count order
    method_rows = (
        await db.execute(
            select(Brewlog.method, func.count().label("cnt"))
            .where(Brewlog.user_id == user.id)
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
            .where(Brewlog.user_id == user.id)
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


@router.get("/tasting-note-matrix-naive")
async def tasting_note_matrix_naive(
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    beans = (await db.execute(select(Bean).where(Bean.user_id == user.id))).scalars().all()
    matrix: dict[str, dict[str, int]] = {}
    for bean in beans:
        labels = (
            await db.execute(
                select(TastingNote.label)
                .join(BeanTastingNote, BeanTastingNote.tasting_note_id == TastingNote.id)
                .where(BeanTastingNote.bean_id == bean.id)
            )
        ).scalars().all()
        for a in labels:
            matrix.setdefault(a, {})
            for b in labels:
                if a != b:
                    matrix[a][b] = matrix[a].get(b, 0) + 1
    return {"source": "naive", "notes": matrix}


@router.get("/tasting-note-matrix")
async def tasting_note_matrix(
    user: User = Depends(requires(PERM_BREWLOG_READ)),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    rows = (
        await db.execute(
            select(Bean.id, TastingNote.label)
            .join(BeanTastingNote, BeanTastingNote.bean_id == Bean.id)
            .join(TastingNote, TastingNote.id == BeanTastingNote.tasting_note_id)
            .where(Bean.user_id == user.id)
            .union_all(
                select(Brewlog.id, TastingNote.label)
                .join(BrewlogTastingNote, BrewlogTastingNote.brewlog_id == Brewlog.id)
                .join(TastingNote, TastingNote.id == BrewlogTastingNote.tasting_note_id)
                .where(Brewlog.user_id == user.id)
            )
        )
    ).all()
    grouped: dict[str, list[str]] = {}
    for entity_id, label in rows:
        grouped.setdefault(str(entity_id), []).append(label)
    matrix: dict[str, dict[str, int]] = {}
    for labels in grouped.values():
        uniq = sorted(set(labels))
        for a in uniq:
            matrix.setdefault(a, {})
            for b in uniq:
                if a != b:
                    matrix[a][b] = matrix[a].get(b, 0) + 1
    return {"source": "optimized", "entity_count": len(grouped), "notes": matrix}
