"""GraphQL types mirroring the Pydantic schemas.

Each `@strawberry.type` is a thin view over an existing Pydantic model; the
`from_model` classmethods convert once at resolver boundaries so we never
duplicate the business rules. Relationship fields (e.g. `Roaster.beans`) use
resolvers that filter the in-memory stores by parent id — this is the 1-to-many
story the Gold challenge asks for.
"""

from __future__ import annotations

from datetime import date as DateType
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import strawberry

from app.schemas import (
    Bean as BeanModel,
)
from app.schemas import (
    BrewLog as BrewLogModel,
)
from app.schemas import (
    BrewStats as BrewStatsModel,
)
from app.schemas import (
    Equipment as EquipmentModel,
)
from app.schemas import (
    MethodCount as MethodCountModel,
)
from app.schemas import (
    Roaster as RoasterModel,
)
from app.schemas import (
    TasteCount as TasteCountModel,
)
from app.schemas.common import (
    BrewMethod,
    EquipmentType,
    GrindType,
    Process,
    RoastLevel,
    TasteResult,
)

if TYPE_CHECKING:
    from app.services import AppState


# --- enums ---------------------------------------------------------------
BrewMethodGQL = strawberry.enum(BrewMethod, name="BrewMethod")
TasteResultGQL = strawberry.enum(TasteResult, name="TasteResult")
ProcessGQL = strawberry.enum(Process, name="Process")
RoastLevelGQL = strawberry.enum(RoastLevel, name="RoastLevel")
EquipmentTypeGQL = strawberry.enum(EquipmentType, name="EquipmentType")
GrindTypeGQL = strawberry.enum(GrindType, name="GrindType")


# --- entity types --------------------------------------------------------


@strawberry.type
class Roaster:
    id: UUID
    name: str
    location: Optional[str]
    website: Optional[str]
    notes: Optional[str]

    @strawberry.field
    def beans(self, info: strawberry.Info) -> list["Bean"]:
        state: "AppState" = info.context["state"]
        return [
            Bean.from_model(b) for b in state.beans.list() if b.roaster_id == self.id
        ]

    @classmethod
    def from_model(cls, m: RoasterModel) -> "Roaster":
        return cls(
            id=m.id,
            name=m.name,
            location=m.location,
            website=str(m.website) if m.website else None,
            notes=m.notes,
        )


@strawberry.type
class Bean:
    id: UUID
    name: str
    roaster_id: Optional[UUID]
    origin_country: str
    origin_region: Optional[str]
    process: ProcessGQL
    roast_level: RoastLevelGQL
    variety: Optional[str]
    elevation_m: Optional[int]
    tasting_notes: list[str]
    purchase_date: Optional[DateType]
    price: Optional[float]

    @strawberry.field
    def roaster(self, info: strawberry.Info) -> Optional[Roaster]:
        if self.roaster_id is None:
            return None
        state: "AppState" = info.context["state"]
        try:
            return Roaster.from_model(state.roasters.get(self.roaster_id))
        except LookupError:
            return None

    @strawberry.field
    def brewlogs(self, info: strawberry.Info) -> list["BrewLog"]:
        state: "AppState" = info.context["state"]
        return [
            BrewLog.from_model(b)
            for b in state.brewlogs.list()
            if b.bean_id == self.id
        ]

    @classmethod
    def from_model(cls, m: BeanModel) -> "Bean":
        return cls(
            id=m.id,
            name=m.name,
            roaster_id=m.roaster_id,
            origin_country=m.origin_country,
            origin_region=m.origin_region,
            process=m.process,
            roast_level=m.roast_level,
            variety=m.variety,
            elevation_m=m.elevation_m,
            tasting_notes=list(m.tasting_notes),
            purchase_date=m.purchase_date,
            price=float(m.price) if m.price is not None else None,
        )


@strawberry.type
class Equipment:
    id: UUID
    name: str
    type: EquipmentTypeGQL
    brand: str
    model: Optional[str]
    grind_type: Optional[GrindTypeGQL]
    grind_range: Optional[str]
    grind_unit: Optional[str]
    notes: Optional[str]

    @strawberry.field
    def brewlogs(self, info: strawberry.Info) -> list["BrewLog"]:
        state: "AppState" = info.context["state"]
        return [
            BrewLog.from_model(b)
            for b in state.brewlogs.list()
            if self.id in (b.equipment_id, b.grinder_id)
        ]

    @classmethod
    def from_model(cls, m: EquipmentModel) -> "Equipment":
        return cls(
            id=m.id,
            name=m.name,
            type=m.type,
            brand=m.brand,
            model=m.model,
            grind_type=m.grind_type,
            grind_range=m.grind_range,
            grind_unit=m.grind_unit,
            notes=m.notes,
        )


@strawberry.type
class BrewLog:
    id: UUID
    date: datetime
    bean_id: UUID
    equipment_id: UUID
    grinder_id: UUID
    grind_setting: str
    method: BrewMethodGQL
    dose_g: float
    water_g: float
    water_temp_c: int
    brew_time_s: int
    yield_g: Optional[float]
    rating: int
    taste_result: Optional[TasteResultGQL]
    grind_adjustment: Optional[str]
    tasting_notes: list[str]
    notes: Optional[str]
    photo_url: Optional[str]

    @strawberry.field
    def bean(self, info: strawberry.Info) -> Optional[Bean]:
        state: "AppState" = info.context["state"]
        try:
            return Bean.from_model(state.beans.get(self.bean_id))
        except LookupError:
            return None

    @strawberry.field
    def equipment(self, info: strawberry.Info) -> Optional[Equipment]:
        state: "AppState" = info.context["state"]
        try:
            return Equipment.from_model(state.equipment.get(self.equipment_id))
        except LookupError:
            return None

    @strawberry.field
    def grinder(self, info: strawberry.Info) -> Optional[Equipment]:
        state: "AppState" = info.context["state"]
        try:
            return Equipment.from_model(state.equipment.get(self.grinder_id))
        except LookupError:
            return None

    @classmethod
    def from_model(cls, m: BrewLogModel) -> "BrewLog":
        return cls(
            id=m.id,
            date=m.date,
            bean_id=m.bean_id,
            equipment_id=m.equipment_id,
            grinder_id=m.grinder_id,
            grind_setting=m.grind_setting,
            method=m.method,
            dose_g=float(m.dose_g),
            water_g=float(m.water_g),
            water_temp_c=m.water_temp_c,
            brew_time_s=m.brew_time_s,
            yield_g=float(m.yield_g) if m.yield_g is not None else None,
            rating=m.rating,
            taste_result=m.taste_result,
            grind_adjustment=m.grind_adjustment,
            tasting_notes=list(m.tasting_notes),
            notes=m.notes,
            photo_url=m.photo_url,
        )


# --- stats ---------------------------------------------------------------


@strawberry.type
class MethodCount:
    method: BrewMethodGQL
    count: int

    @classmethod
    def from_model(cls, m: MethodCountModel) -> "MethodCount":
        return cls(method=m.method, count=m.count)


@strawberry.type
class TasteCount:
    taste_result: TasteResultGQL
    count: int

    @classmethod
    def from_model(cls, m: TasteCountModel) -> "TasteCount":
        return cls(taste_result=m.taste_result, count=m.count)


@strawberry.type
class BrewStats:
    total_brews: int
    average_rating: Optional[float]
    most_used_method: Optional[BrewMethodGQL]
    by_method: list[MethodCount]
    by_taste: list[TasteCount]
    balanced_ratio: Optional[float]

    @classmethod
    def from_model(cls, m: BrewStatsModel) -> "BrewStats":
        return cls(
            total_brews=m.total_brews,
            average_rating=m.average_rating,
            most_used_method=m.most_used_method,
            by_method=[MethodCount.from_model(x) for x in m.by_method],
            by_taste=[TasteCount.from_model(x) for x in m.by_taste],
            balanced_ratio=m.balanced_ratio,
        )


# --- pagination envelopes -----------------------------------------------


@strawberry.type
class RoasterPage:
    items: list[Roaster]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class BeanPage:
    items: list[Bean]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class EquipmentPage:
    items: list[Equipment]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class BrewLogPage:
    items: list[BrewLog]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- input types --------------------------------------------------------


# Strawberry inputs use `strawberry.UNSET` as default (instead of `None`) so
# that `strip_unset` can distinguish "client omitted the field" from "client
# passed null". This matters because Pydantic's Create models have non-null
# defaults for some fields (e.g. `tasting_notes: list[str] = []`) which would
# be rejected if we forwarded `None`.

_UNSET = strawberry.UNSET


@strawberry.input
class RoasterInput:
    name: str
    location: Optional[str] = _UNSET
    website: Optional[str] = _UNSET
    notes: Optional[str] = _UNSET


@strawberry.input
class RoasterPatch:
    name: Optional[str] = _UNSET
    location: Optional[str] = _UNSET
    website: Optional[str] = _UNSET
    notes: Optional[str] = _UNSET


@strawberry.input
class BeanInput:
    name: str
    origin_country: str
    process: ProcessGQL
    roast_level: RoastLevelGQL
    roaster_id: Optional[UUID] = _UNSET
    origin_region: Optional[str] = _UNSET
    variety: Optional[str] = _UNSET
    elevation_m: Optional[int] = _UNSET
    tasting_notes: Optional[list[str]] = _UNSET
    purchase_date: Optional[DateType] = _UNSET
    price: Optional[float] = _UNSET


@strawberry.input
class BeanPatch:
    name: Optional[str] = _UNSET
    roaster_id: Optional[UUID] = _UNSET
    origin_country: Optional[str] = _UNSET
    origin_region: Optional[str] = _UNSET
    process: Optional[ProcessGQL] = _UNSET
    roast_level: Optional[RoastLevelGQL] = _UNSET
    variety: Optional[str] = _UNSET
    elevation_m: Optional[int] = _UNSET
    tasting_notes: Optional[list[str]] = _UNSET
    purchase_date: Optional[DateType] = _UNSET
    price: Optional[float] = _UNSET


@strawberry.input
class EquipmentInput:
    name: str
    type: EquipmentTypeGQL
    brand: str
    model: Optional[str] = _UNSET
    grind_type: Optional[GrindTypeGQL] = _UNSET
    grind_range: Optional[str] = _UNSET
    grind_unit: Optional[str] = _UNSET
    notes: Optional[str] = _UNSET


@strawberry.input
class EquipmentPatch:
    name: Optional[str] = _UNSET
    type: Optional[EquipmentTypeGQL] = _UNSET
    brand: Optional[str] = _UNSET
    model: Optional[str] = _UNSET
    grind_type: Optional[GrindTypeGQL] = _UNSET
    grind_range: Optional[str] = _UNSET
    grind_unit: Optional[str] = _UNSET
    notes: Optional[str] = _UNSET


@strawberry.input
class BrewLogInput:
    date: datetime
    bean_id: UUID
    equipment_id: UUID
    grinder_id: UUID
    grind_setting: str
    method: BrewMethodGQL
    dose_g: float
    water_g: float
    water_temp_c: int
    brew_time_s: int
    rating: int
    yield_g: Optional[float] = _UNSET
    taste_result: Optional[TasteResultGQL] = _UNSET
    grind_adjustment: Optional[str] = _UNSET
    tasting_notes: Optional[list[str]] = _UNSET
    notes: Optional[str] = _UNSET
    photo_url: Optional[str] = _UNSET


@strawberry.input
class BrewLogPatch:
    date: Optional[datetime] = _UNSET
    bean_id: Optional[UUID] = _UNSET
    equipment_id: Optional[UUID] = _UNSET
    grinder_id: Optional[UUID] = _UNSET
    grind_setting: Optional[str] = _UNSET
    method: Optional[BrewMethodGQL] = _UNSET
    dose_g: Optional[float] = _UNSET
    water_g: Optional[float] = _UNSET
    water_temp_c: Optional[int] = _UNSET
    brew_time_s: Optional[int] = _UNSET
    yield_g: Optional[float] = _UNSET
    rating: Optional[int] = _UNSET
    taste_result: Optional[TasteResultGQL] = _UNSET
    grind_adjustment: Optional[str] = _UNSET
    tasting_notes: Optional[list[str]] = _UNSET
    notes: Optional[str] = _UNSET
    photo_url: Optional[str] = _UNSET


# --- helpers ------------------------------------------------------------


def decimal_or_none(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def strip_unset(input_obj: object) -> dict[str, object]:
    """Return a dict of only the fields that were explicitly set on a Strawberry input.

    Strawberry represents unset fields as `strawberry.UNSET`.
    """
    result: dict[str, object] = {}
    for field_def in input_obj.__strawberry_definition__.fields:  # type: ignore[attr-defined]
        name = field_def.python_name
        value = getattr(input_obj, name)
        if value is strawberry.UNSET:
            continue
        result[name] = value
    return result
