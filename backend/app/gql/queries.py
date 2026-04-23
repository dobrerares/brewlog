"""GraphQL read-side: queries, pagination and statistics."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry

from app.api.stats import brewlog_stats
from app.pagination import PageParams, paginate as _paginate_py
from app.services import AppState

from .types import (
    Bean,
    BeanPage,
    BrewLog,
    BrewLogPage,
    BrewMethodGQL,
    BrewStats,
    Equipment,
    EquipmentPage,
    Roaster,
    RoasterPage,
    TasteResultGQL,
)


def _page_bounds(page: int, page_size: int) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def _state(info: strawberry.Info) -> AppState:
    return info.context["state"]


@strawberry.type
class Query:
    # --- roasters -------------------------------------------------------

    @strawberry.field
    def roasters(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> RoasterPage:
        state = _state(info)
        sliced = _paginate_py(state.roasters.list(), _page_bounds(page, page_size))
        return RoasterPage(
            items=[Roaster.from_model(m) for m in sliced.items],
            total=sliced.total,
            page=sliced.page,
            page_size=sliced.page_size,
            total_pages=sliced.total_pages,
        )

    @strawberry.field
    def roaster(self, info: strawberry.Info, id: UUID) -> Optional[Roaster]:
        try:
            return Roaster.from_model(_state(info).roasters.get(id))
        except LookupError:
            return None

    # --- beans ----------------------------------------------------------

    @strawberry.field
    def beans(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> BeanPage:
        state = _state(info)
        sliced = _paginate_py(state.beans.list(), _page_bounds(page, page_size))
        return BeanPage(
            items=[Bean.from_model(m) for m in sliced.items],
            total=sliced.total,
            page=sliced.page,
            page_size=sliced.page_size,
            total_pages=sliced.total_pages,
        )

    @strawberry.field
    def bean(self, info: strawberry.Info, id: UUID) -> Optional[Bean]:
        try:
            return Bean.from_model(_state(info).beans.get(id))
        except LookupError:
            return None

    # --- equipment ------------------------------------------------------

    @strawberry.field(name="equipmentList")
    def equipment_list(
        self,
        info: strawberry.Info,
        page: int = 1,
        page_size: int = 20,
    ) -> EquipmentPage:
        state = _state(info)
        sliced = _paginate_py(state.equipment.list(), _page_bounds(page, page_size))
        return EquipmentPage(
            items=[Equipment.from_model(m) for m in sliced.items],
            total=sliced.total,
            page=sliced.page,
            page_size=sliced.page_size,
            total_pages=sliced.total_pages,
        )

    @strawberry.field
    def equipment(self, info: strawberry.Info, id: UUID) -> Optional[Equipment]:
        try:
            return Equipment.from_model(_state(info).equipment.get(id))
        except LookupError:
            return None

    # --- brewlogs -------------------------------------------------------

    @strawberry.field
    def brewlogs(
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
        state = _state(info)
        items = state.brewlogs.list()
        if method is not None:
            items = [b for b in items if b.method == method]
        if taste_result is not None:
            items = [b for b in items if b.taste_result == taste_result]
        if bean_id is not None:
            items = [b for b in items if b.bean_id == bean_id]
        if min_rating is not None:
            items = [b for b in items if b.rating >= min_rating]
        if max_rating is not None:
            items = [b for b in items if b.rating <= max_rating]
        if date_from is not None:
            items = [b for b in items if b.date >= date_from]
        if date_to is not None:
            items = [b for b in items if b.date <= date_to]
        items.sort(key=lambda b: b.date, reverse=True)

        sliced = _paginate_py(items, _page_bounds(page, page_size))
        return BrewLogPage(
            items=[BrewLog.from_model(m) for m in sliced.items],
            total=sliced.total,
            page=sliced.page,
            page_size=sliced.page_size,
            total_pages=sliced.total_pages,
        )

    @strawberry.field
    def brewlog(self, info: strawberry.Info, id: UUID) -> Optional[BrewLog]:
        try:
            return BrewLog.from_model(_state(info).brewlogs.get(id))
        except LookupError:
            return None

    # --- stats ----------------------------------------------------------

    @strawberry.field
    def brew_stats(self, info: strawberry.Info) -> BrewStats:
        return BrewStats.from_model(brewlog_stats(_state(info).brewlogs))
