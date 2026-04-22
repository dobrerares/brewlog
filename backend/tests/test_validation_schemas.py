"""Direct unit tests for Pydantic schema validators.

These cover code paths the endpoint tests also exercise, but fail faster and
make the intent of each rule explicit.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import BrewLogCreate, EquipmentCreate
from app.schemas.common import BrewMethod, EquipmentType, TasteResult


def _valid_brew(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "date": "2026-04-01T08:00:00",
        "bean_id": uuid4(),
        "equipment_id": uuid4(),
        "grinder_id": uuid4(),
        "grind_setting": "22 clicks",
        "method": BrewMethod.V60,
        "dose_g": Decimal("15"),
        "water_g": Decimal("250"),
        "water_temp_c": 94,
        "brew_time_s": 150,
        "rating": 4,
        "taste_result": TasteResult.BALANCED,
        "tasting_notes": [],
        "notes": None,
        "photo_url": None,
        "yield_g": None,
        "grind_adjustment": None,
    }
    payload.update(overrides)
    return payload


def test_valid_brewlog_parses() -> None:
    BrewLogCreate(**_valid_brew())  # should not raise


@pytest.mark.parametrize(
    "ratio_water",
    [Decimal("100"), Decimal("400")],  # 6.6x and 26.6x — both out of band
)
def test_brewlog_rejects_out_of_band_ratio(ratio_water: Decimal) -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(**_valid_brew(water_g=ratio_water))


def test_brewlog_rejects_temp_out_of_method_band() -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(**_valid_brew(method=BrewMethod.FRENCH_PRESS, water_temp_c=85))


def test_brewlog_espresso_requires_yield() -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(
            **_valid_brew(
                method=BrewMethod.ESPRESSO,
                dose_g=Decimal("18"),
                water_g=Decimal("36"),
                water_temp_c=93,
                brew_time_s=30,
                yield_g=None,
            )
        )


def test_brewlog_low_rating_without_notes_fails() -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(**_valid_brew(rating=2, notes=None))


def test_brewlog_low_rating_with_notes_passes() -> None:
    BrewLogCreate(**_valid_brew(rating=2, notes="under-extracted"))


def test_brewlog_rejects_rating_out_of_range() -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(**_valid_brew(rating=0))


def test_brewlog_rejects_negative_dose() -> None:
    with pytest.raises(ValidationError):
        BrewLogCreate(**_valid_brew(dose_g=Decimal("0")))


def test_equipment_grinder_needs_grind_type() -> None:
    with pytest.raises(ValidationError):
        EquipmentCreate(
            name="X",
            type=EquipmentType.GRINDER,
            brand="Y",
            model=None,
            grind_type=None,
            grind_range=None,
            grind_unit=None,
            notes=None,
        )


def test_equipment_non_grinder_cannot_have_grind_fields() -> None:
    with pytest.raises(ValidationError):
        EquipmentCreate(
            name="X",
            type=EquipmentType.BREWER,
            brand="Y",
            model=None,
            grind_type=None,
            grind_range="clicks 0-40",
            grind_unit=None,
            notes=None,
        )
