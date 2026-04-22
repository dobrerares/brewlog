"""Unit tests for the pagination helper."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.pagination import PageParams, paginate


def test_paginate_returns_correct_slice() -> None:
    items = list(range(55))
    page = paginate(items, PageParams(page=3, page_size=10))
    assert page.items == list(range(20, 30))
    assert page.page == 3
    assert page.page_size == 10
    assert page.total == 55
    assert page.total_pages == 6


def test_paginate_handles_empty_collection() -> None:
    page = paginate([], PageParams(page=1, page_size=10))
    assert page.items == []
    assert page.total == 0
    assert page.total_pages == 0


def test_paginate_last_page_is_short() -> None:
    items = list(range(23))
    page = paginate(items, PageParams(page=3, page_size=10))
    assert page.items == [20, 21, 22]
    assert page.total_pages == 3


def test_paginate_out_of_range_returns_empty_slice() -> None:
    items = list(range(5))
    page = paginate(items, PageParams(page=10, page_size=10))
    assert page.items == []
    assert page.total == 5


def test_page_params_rejects_negative_page() -> None:
    with pytest.raises(ValidationError):
        PageParams(page=0, page_size=10)


def test_page_params_rejects_oversized_page() -> None:
    with pytest.raises(ValidationError):
        PageParams(page=1, page_size=500)
