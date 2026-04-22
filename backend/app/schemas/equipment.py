"""Equipment schemas — includes grinder calibration data."""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import EquipmentType, GrindType


class EquipmentBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    type: EquipmentType
    brand: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=80)

    # Grinder-only fields
    grind_type: GrindType | None = None
    grind_range: str | None = Field(default=None, max_length=80)
    grind_unit: str | None = Field(default=None, max_length=40)

    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _grinder_fields_are_grinder_only(self) -> Self:
        grinder_fields = (self.grind_type, self.grind_range, self.grind_unit)
        has_any = any(f is not None for f in grinder_fields)
        if self.type != EquipmentType.GRINDER and has_any:
            raise ValueError(
                "grind_type, grind_range and grind_unit are only valid for "
                "equipment of type 'Grinder'"
            )
        if self.type == EquipmentType.GRINDER and self.grind_type is None:
            raise ValueError("grind_type is required when type is 'Grinder'")
        return self


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    """Partial update — validated at the route layer by merging with the stored entity."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: EquipmentType | None = None
    brand: str | None = Field(default=None, min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    grind_type: GrindType | None = None
    grind_range: str | None = Field(default=None, max_length=80)
    grind_unit: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class Equipment(EquipmentBase):
    id: UUID
