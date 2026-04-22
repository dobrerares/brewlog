"""BrewLog schemas — core entity with strict validation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import BrewMethod, TasteResult

# Temperature bands enforced by the post-brew review. Mirrors the client-side
# rules in `useBrewValidation` so the server is the source of truth.
_TEMP_BANDS: dict[BrewMethod, tuple[int, int]] = {
    BrewMethod.V60: (90, 96),
    BrewMethod.CHEMEX: (90, 96),
    BrewMethod.FRENCH_PRESS: (92, 96),
    BrewMethod.AEROPRESS: (80, 95),
    BrewMethod.ESPRESSO: (85, 100),
    BrewMethod.MOKA_POT: (90, 100),
    BrewMethod.COLD_BREW: (1, 25),
    BrewMethod.OTHER: (1, 100),
}


class BrewLogBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: datetime
    bean_id: UUID
    equipment_id: UUID
    grinder_id: UUID
    grind_setting: str = Field(min_length=1, max_length=40)
    method: BrewMethod
    dose_g: Decimal = Field(gt=Decimal("0"), le=Decimal("100"))
    water_g: Decimal = Field(gt=Decimal("0"), le=Decimal("2000"))
    water_temp_c: int = Field(ge=1, le=100)
    brew_time_s: int = Field(ge=1, le=3600)
    yield_g: Decimal | None = Field(default=None, gt=Decimal("0"), le=Decimal("200"))
    rating: int = Field(ge=1, le=5)
    taste_result: TasteResult | None = None
    grind_adjustment: str | None = Field(default=None, max_length=120)
    tasting_notes: list[str] = Field(default_factory=list, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    photo_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _validate_business_rules(self) -> Self:
        # Dose / water ratio: the coffee brewing standard is 10–20 × dose.
        # Espresso recipes use ~2× ratios, so they're exempt.
        if self.method != BrewMethod.ESPRESSO:
            ratio = self.water_g / self.dose_g
            if ratio < Decimal("10") or ratio > Decimal("20"):
                raise ValueError(
                    f"water_g/dose_g ratio must be between 10 and 20 for {self.method.value}; "
                    f"got {ratio:.1f}"
                )

        lo, hi = _TEMP_BANDS[self.method]
        if not lo <= self.water_temp_c <= hi:
            raise ValueError(
                f"water_temp_c must be in [{lo}, {hi}] °C for method {self.method.value}; "
                f"got {self.water_temp_c}"
            )

        # Espresso records yield; every other method does not.
        if self.method == BrewMethod.ESPRESSO and self.yield_g is None:
            raise ValueError("yield_g is required for espresso brews")

        # A low rating must carry explanatory notes — otherwise the dial-in
        # history is not actionable.
        if self.rating < 3 and not (self.notes and self.notes.strip()):
            raise ValueError("notes are required when rating is below 3")

        return self


class BrewLogCreate(BrewLogBase):
    pass


class BrewLogUpdate(BaseModel):
    """Partial update; full validation re-runs after merging with the stored brew."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: datetime | None = None
    bean_id: UUID | None = None
    equipment_id: UUID | None = None
    grinder_id: UUID | None = None
    grind_setting: str | None = Field(default=None, min_length=1, max_length=40)
    method: BrewMethod | None = None
    dose_g: Decimal | None = Field(default=None, gt=Decimal("0"), le=Decimal("100"))
    water_g: Decimal | None = Field(default=None, gt=Decimal("0"), le=Decimal("2000"))
    water_temp_c: int | None = Field(default=None, ge=1, le=100)
    brew_time_s: int | None = Field(default=None, ge=1, le=3600)
    yield_g: Decimal | None = Field(default=None, gt=Decimal("0"), le=Decimal("200"))
    rating: int | None = Field(default=None, ge=1, le=5)
    taste_result: TasteResult | None = None
    grind_adjustment: str | None = Field(default=None, max_length=120)
    tasting_notes: list[str] | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    photo_url: str | None = Field(default=None, max_length=500)


class BrewLog(BrewLogBase):
    id: UUID
