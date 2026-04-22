"""Roaster / café schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RoasterBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    website: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=2000)


class RoasterCreate(RoasterBase):
    pass


class RoasterUpdate(BaseModel):
    """Partial update payload — every field optional."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    website: HttpUrl | None = None
    notes: str | None = Field(default=None, max_length=2000)


class Roaster(RoasterBase):
    id: UUID
