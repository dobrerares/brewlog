"""GraphQL read-side: queries, pagination and statistics."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Brewlog as BrewlogORM
from app.pagination import PageParams
from app.repositories.beans import BeanRepository
from app.repositories.brewlogs import BrewlogRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.roasters import RoasterRepository
from app.repositories.tasting_notes import TastingNoteRepository
from app.schemas import Bean as BeanModel
from app.schemas import BrewLog as BrewLogModel
from app.schemas import Equipment as EquipmentModel
from app.schemas import Roaster as RoasterModel
from app.schemas import BrewStats, MethodCount, TasteCount
from app.schemas.common import BrewMethod, TasteResult

from .types import (
    Bean,
    BeanPage,
    BrewLog,
    BrewLogPage,
    BrewMethodGQL,
    BrewStats as BrewStatsGQL,
    Equipment,
    EquipmentPage,
    Roaster,
    RoasterPage,
    TasteResultGQL,
)

_DEV_USER = UUID(os.environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))


def _page_bounds(page: int, page_size: int) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def _db(info: strawberry.Info) -> AsyncSession:
    return info.context["db"]


async def _bean_to_model(row, tn_repo: TastingNoteRepository) -> BeanModel:
    notes = await tn_repo.labels_for_bean(row.id)
    return BeanModel.model_validate(
        {
            "id": row.id,
            "name": row.name,
            "roaster_id": row.roaster_id,
            "origin_country": row.origin_country,
            "origin_region": row.origin_region,
            "process": row.process,
            "roast_level": row.roast_level,
            "variety": row.variety,
            "elevation_m": row.elevation_m,
            "tasting_notes": notes,
            "purchase_date": row.purchase_date,
            "price": row.price,
        }
    )


async def _brewlog_to_model(row, tn_repo: TastingNoteRepository) -> BrewLogModel:
    notes = await tn_repo.labels_for_brewlog(row.id)
    return BrewLogModel.model_validate(
        {
            "id": row.id,
            "date": row.date,
            "bean_id": row.bean_id,
            "equipment_id": row.equipment_id,
            "grinder_id": row.grinder_id,
            "grind_setting": row.grind_setting,
            "method": row.method,
            "dose_g": row.dose_g,
            "water_g": row.water_g,
            "water_temp_c": row.water_temp_c,
            "brew_time_s": row.brew_time_s,
            "yield_g": row.yield_g,
            "rating": row.rating,
            "taste_result": row.taste_result,
            "grind_adjustment": row.grind_adjustment,
            "tasting_notes": notes,
            "notes": row.notes,
            "photo_url": row.photo_url,
        }
    )


def _paginate_list(items: list, page: int, page_size: int):
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total, page, page_size, total_pages


@strawberry.type
class Query:
    # --- roasters -------------------------------------------------------

    @strawberry.field
    async def roasters(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> RoasterPage:
        db = _db(info)
        rows = await RoasterRepository(db).list()
        items = [
            Roaster.from_model(
                RoasterModel.model_validate(r, from_attributes=True)
            )
            for r in rows
        ]
        sliced, total, pg, ps, total_pages = _paginate_list(items, page, page_size)
        return RoasterPage(
            items=sliced,
            total=total,
            page=pg,
            page_size=ps,
            total_pages=total_pages,
        )

    @strawberry.field
    async def roaster(self, info: strawberry.Info, id: UUID) -> Optional[Roaster]:
        db = _db(info)
        try:
            row = await RoasterRepository(db).get(id)
        except Exception:
            return None
        return Roaster.from_model(RoasterModel.model_validate(row, from_attributes=True))

    # --- beans ----------------------------------------------------------

    @strawberry.field
    async def beans(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> BeanPage:
        db = _db(info)
        rows = await BeanRepository(db).list()
        tn_repo = TastingNoteRepository(db)
        items = [Bean.from_model(await _bean_to_model(r, tn_repo)) for r in rows]
        sliced, total, pg, ps, total_pages = _paginate_list(items, page, page_size)
        return BeanPage(
            items=sliced,
            total=total,
            page=pg,
            page_size=ps,
            total_pages=total_pages,
        )

    @strawberry.field
    async def bean(self, info: strawberry.Info, id: UUID) -> Optional[Bean]:
        db = _db(info)
        try:
            row = await BeanRepository(db).get(id)
        except Exception:
            return None
        tn_repo = TastingNoteRepository(db)
        return Bean.from_model(await _bean_to_model(row, tn_repo))

    # --- equipment ------------------------------------------------------

    @strawberry.field(name="equipmentList")
    async def equipment_list(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> EquipmentPage:
        db = _db(info)
        rows = await EquipmentRepository(db).list()
        items = [
            Equipment.from_model(
                EquipmentModel.model_validate(r, from_attributes=True)
            )
            for r in rows
        ]
        sliced, total, pg, ps, total_pages = _paginate_list(items, page, page_size)
        return EquipmentPage(
            items=sliced,
            total=total,
            page=pg,
            page_size=ps,
            total_pages=total_pages,
        )

    @strawberry.field
    async def equipment(self, info: strawberry.Info, id: UUID) -> Optional[Equipment]:
        db = _db(info)
        try:
            row = await EquipmentRepository(db).get(id)
        except Exception:
            return None
        return Equipment.from_model(EquipmentModel.model_validate(row, from_attributes=True))

    # --- brewlogs -------------------------------------------------------

    @strawberry.field
    async def brewlogs(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
        method: Optional[BrewMethodGQL] = None,
        taste_result: Optional[TasteResultGQL] = None,
        bean_id: Optional[UUID] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> BrewLogPage:
        db = _db(info)
        stmt = select(BrewlogORM).order_by(BrewlogORM.date.desc())
        if method is not None:
            stmt = stmt.where(BrewlogORM.method == method.value)
        if taste_result is not None:
            stmt = stmt.where(BrewlogORM.taste_result == taste_result.value)
        if bean_id is not None:
            stmt = stmt.where(BrewlogORM.bean_id == bean_id)
        if min_rating is not None:
            stmt = stmt.where(BrewlogORM.rating >= min_rating)
        if max_rating is not None:
            stmt = stmt.where(BrewlogORM.rating <= max_rating)
        if date_from is not None:
            stmt = stmt.where(BrewlogORM.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(BrewlogORM.date <= date_to)
        rows = list((await db.execute(stmt)).scalars().all())
        tn_repo = TastingNoteRepository(db)
        items = [BrewLog.from_model(await _brewlog_to_model(r, tn_repo)) for r in rows]
        sliced, total, pg, ps, total_pages = _paginate_list(items, page, page_size)
        return BrewLogPage(
            items=sliced,
            total=total,
            page=pg,
            page_size=ps,
            total_pages=total_pages,
        )

    @strawberry.field
    async def brewlog(self, info: strawberry.Info, id: UUID) -> Optional[BrewLog]:
        db = _db(info)
        try:
            row = await BrewlogRepository(db).get(id)
        except Exception:
            return None
        tn_repo = TastingNoteRepository(db)
        return BrewLog.from_model(await _brewlog_to_model(row, tn_repo))

    # --- stats ----------------------------------------------------------

    @strawberry.field
    async def brew_stats(self, info: strawberry.Info) -> BrewStatsGQL:
        db = _db(info)

        total = (await db.scalar(select(func.count(BrewlogORM.id)))) or 0

        if total == 0:
            return BrewStatsGQL.from_model(
                BrewStats(
                    total_brews=0,
                    average_rating=None,
                    most_used_method=None,
                    by_method=[],
                    by_taste=[],
                    balanced_ratio=None,
                )
            )

        raw_avg = await db.scalar(select(func.avg(BrewlogORM.rating)))
        avg_rating = round(float(raw_avg), 2) if raw_avg is not None else None

        method_rows = (
            await db.execute(
                select(BrewlogORM.method, func.count().label("cnt"))
                .group_by(BrewlogORM.method)
                .order_by(func.count().desc())
            )
        ).all()
        by_method = [MethodCount(method=BrewMethod(m), count=c) for m, c in method_rows]
        most_used_method = by_method[0].method if by_method else None

        taste_rows = (
            await db.execute(
                select(BrewlogORM.taste_result, func.count().label("cnt"))
                .where(BrewlogORM.taste_result.is_not(None))
                .group_by(BrewlogORM.taste_result)
                .order_by(func.count().desc())
            )
        ).all()
        by_taste = [TasteCount(taste_result=TasteResult(t), count=c) for t, c in taste_rows]

        rated_count = sum(e.count for e in by_taste)
        balanced_count = next(
            (e.count for e in by_taste if e.taste_result == TasteResult.BALANCED), 0
        )
        balanced_ratio = (
            round(balanced_count / rated_count, 3) if rated_count else None
        )

        return BrewStatsGQL.from_model(
            BrewStats(
                total_brews=total,
                average_rating=avg_rating,
                most_used_method=most_used_method,
                by_method=by_method,
                by_taste=by_taste,
                balanced_ratio=balanced_ratio,
            )
        )
