"""Server-side pagination primitives."""

from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(1, ge=1, description="1-based page index")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")


def page_params(
    page: int = Query(1, ge=1, description="1-based page index"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> PageParams:
    """FastAPI dependency that binds pagination query params."""
    return PageParams(page=page, page_size=page_size)


class Page(BaseModel, Generic[T]):
    """Envelope returned by every list endpoint."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)

    @classmethod
    def build(cls, items: Sequence[T], total: int, params: PageParams) -> "Page[T]":
        total_pages = (total + params.page_size - 1) // params.page_size if total else 0
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )


def paginate(items: Sequence[T], params: PageParams) -> Page[T]:
    """Slice a sequence according to pagination parameters."""
    total = len(items)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    return Page.build(items[start:end], total, params)
