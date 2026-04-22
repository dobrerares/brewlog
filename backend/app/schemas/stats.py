"""Statistics response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import BrewMethod, TasteResult


class MethodCount(BaseModel):
    method: BrewMethod
    count: int = Field(ge=0)


class TasteCount(BaseModel):
    taste_result: TasteResult
    count: int = Field(ge=0)


class BrewStats(BaseModel):
    total_brews: int = Field(ge=0)
    average_rating: float | None = Field(default=None, ge=0, le=5)
    most_used_method: BrewMethod | None = None
    by_method: list[MethodCount]
    by_taste: list[TasteCount]
    balanced_ratio: float | None = Field(default=None, ge=0, le=1)
