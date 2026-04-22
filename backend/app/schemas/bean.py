"""Coffee-bean schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .common import Process, RoastLevel


class BeanBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    roaster_id: UUID | None = None
    origin_country: str = Field(min_length=1, max_length=80)
    origin_region: str | None = Field(default=None, max_length=80)
    process: Process
    roast_level: RoastLevel
    variety: str | None = Field(default=None, max_length=80)
    elevation_m: int | None = Field(default=None, ge=0, le=4000)
    tasting_notes: list[str] = Field(default_factory=list, max_length=32)
    purchase_date: date | None = None
    price: Decimal | None = Field(default=None, ge=0, le=Decimal("10000"))


class BeanCreate(BeanBase):
    pass


class BeanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    roaster_id: UUID | None = None
    origin_country: str | None = Field(default=None, min_length=1, max_length=80)
    origin_region: str | None = Field(default=None, max_length=80)
    process: Process | None = None
    roast_level: RoastLevel | None = None
    variety: str | None = Field(default=None, max_length=80)
    elevation_m: int | None = Field(default=None, ge=0, le=4000)
    tasting_notes: list[str] | None = Field(default=None, max_length=32)
    purchase_date: date | None = None
    price: Decimal | None = Field(default=None, ge=0, le=Decimal("10000"))


class Bean(BeanBase):
    id: UUID
