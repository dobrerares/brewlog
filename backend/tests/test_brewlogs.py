"""Integration tests for /api/v1/brewlogs — CRUD, filtering, validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_bean, make_brewer, make_brewlog, make_grinder


@pytest.fixture
def refs(client: TestClient) -> dict[str, str]:
    bean = make_bean(client)
    brewer = make_brewer(client)
    grinder = make_grinder(client)
    return {
        "bean_id": bean["id"],
        "equipment_id": brewer["id"],
        "grinder_id": grinder["id"],
    }


def test_create_and_get_brewlog(client: TestClient, refs: dict[str, str]) -> None:
    brew = make_brewlog(client, **refs)
    got = client.get(f"/api/v1/brewlogs/{brew['id']}")
    assert got.status_code == 200
    assert got.json()["method"] == "V60"


def test_create_espresso_requires_yield(client: TestClient, refs: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "fine",
            "method": "Espresso",
            "dose_g": "18",
            "water_g": "36",
            "water_temp_c": 93,
            "brew_time_s": 30,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "yield_g" in response.text


def test_create_espresso_with_yield(client: TestClient, refs: dict[str, str]) -> None:
    brew = make_brewlog(
        client,
        **refs,
        method="Espresso",
        dose_g="18",
        water_g="36",
        water_temp_c=93,
        brew_time_s=30,
        yield_g="34",
    )
    assert brew["method"] == "Espresso"
    assert brew["yield_g"] == "34"


def test_create_rejects_bad_ratio(client: TestClient, refs: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "100",  # ratio ~6.6x — too low
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "ratio" in response.text


def test_create_rejects_bad_temp_for_method(
    client: TestClient, refs: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 75,  # way below V60's 90–96 band
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "water_temp_c" in response.text


def test_create_rejects_low_rating_without_notes(
    client: TestClient, refs: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 2,
            "taste_result": "Sour",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "notes" in response.text


def test_low_rating_with_notes_is_accepted(
    client: TestClient, refs: dict[str, str]
) -> None:
    brew = make_brewlog(
        client, **refs, rating=2, taste_result="Sour", notes="Too sharp, go finer."
    )
    assert brew["rating"] == 2


def test_create_rejects_unknown_bean(client: TestClient, refs: dict[str, str]) -> None:
    bad = {**refs, "bean_id": "00000000-0000-0000-0000-000000000000"}
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "bean_id" in response.text


def test_create_rejects_unknown_equipment(
    client: TestClient, refs: dict[str, str]
) -> None:
    bad = {**refs, "equipment_id": "00000000-0000-0000-0000-000000000000"}
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "equipment_id" in response.text


def test_create_rejects_unknown_grinder(
    client: TestClient, refs: dict[str, str]
) -> None:
    bad = {**refs, "grinder_id": "00000000-0000-0000-0000-000000000000"}
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **bad,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
        },
    )
    assert response.status_code == 422
    assert "grinder_id" in response.text


def test_list_brewlogs_paginated_and_sorted(
    client: TestClient, refs: dict[str, str]
) -> None:
    dates = [
        "2026-04-01T08:00:00",
        "2026-04-02T08:00:00",
        "2026-04-03T08:00:00",
        "2026-04-04T08:00:00",
        "2026-04-05T08:00:00",
    ]
    for d in dates:
        make_brewlog(client, **refs, date=d)

    response = client.get("/api/v1/brewlogs", params={"page": 1, "page_size": 3})
    data = response.json()
    assert data["total"] == 5
    assert data["total_pages"] == 2
    # newest first
    returned_dates = [item["date"] for item in data["items"]]
    assert returned_dates == sorted(returned_dates, reverse=True)


def test_list_filters_by_method(client: TestClient, refs: dict[str, str]) -> None:
    make_brewlog(client, **refs, method="V60")
    make_brewlog(
        client,
        **refs,
        method="Espresso",
        dose_g="18",
        water_g="36",
        water_temp_c=93,
        brew_time_s=30,
        yield_g="34",
    )
    response = client.get("/api/v1/brewlogs", params={"method": "Espresso"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["method"] == "Espresso"


def test_list_filters_by_taste_and_rating_range(
    client: TestClient, refs: dict[str, str]
) -> None:
    make_brewlog(client, **refs, rating=5, taste_result="Balanced")
    make_brewlog(
        client,
        **refs,
        rating=2,
        taste_result="Sour",
        notes="under-extracted",
    )
    response = client.get(
        "/api/v1/brewlogs", params={"min_rating": 4, "taste_result": "Balanced"}
    )
    data = response.json()
    assert data["total"] == 1

    response = client.get("/api/v1/brewlogs", params={"max_rating": 3})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["rating"] == 2


def test_list_filters_by_bean_id(client: TestClient, refs: dict[str, str]) -> None:
    other_bean = make_bean(client, name="Other")
    make_brewlog(client, **refs)
    make_brewlog(client, **{**refs, "bean_id": other_bean["id"]})
    response = client.get("/api/v1/brewlogs", params={"bean_id": other_bean["id"]})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["bean_id"] == other_bean["id"]


def test_list_filters_by_date_range(client: TestClient, refs: dict[str, str]) -> None:
    make_brewlog(client, **refs, date="2026-03-01T08:00:00")
    make_brewlog(client, **refs, date="2026-04-01T08:00:00")
    response = client.get(
        "/api/v1/brewlogs",
        params={"date_from": "2026-03-15T00:00:00", "date_to": "2026-05-01T00:00:00"},
    )
    data = response.json()
    assert data["total"] == 1


def test_update_brewlog(client: TestClient, refs: dict[str, str]) -> None:
    brew = make_brewlog(client, **refs)
    response = client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"rating": 5, "notes": "Revisited and loved it."},
    )
    assert response.status_code == 200
    assert response.json()["rating"] == 5


def test_update_brewlog_revalidates_business_rules(
    client: TestClient, refs: dict[str, str]
) -> None:
    brew = make_brewlog(client, **refs, rating=4, taste_result="Balanced")
    # Rating < 3 without notes must fail the cross-field rule.
    response = client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"rating": 2, "notes": None},
    )
    assert response.status_code == 422


def test_update_brewlog_can_change_bean(client: TestClient, refs: dict[str, str]) -> None:
    brew = make_brewlog(client, **refs)
    other_bean = make_bean(client, name="Another")
    response = client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"bean_id": other_bean["id"]},
    )
    assert response.status_code == 200
    assert response.json()["bean_id"] == other_bean["id"]


def test_update_brewlog_rejects_unknown_ref(
    client: TestClient, refs: dict[str, str]
) -> None:
    brew = make_brewlog(client, **refs)
    response = client.patch(
        f"/api/v1/brewlogs/{brew['id']}",
        json={"bean_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 422


def test_update_unknown_brewlog_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/brewlogs/00000000-0000-0000-0000-000000000000",
        json={"rating": 5, "notes": "x"},
    )
    assert response.status_code == 404


def test_delete_brewlog(client: TestClient, refs: dict[str, str]) -> None:
    brew = make_brewlog(client, **refs)
    response = client.delete(f"/api/v1/brewlogs/{brew['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/brewlogs/{brew['id']}").status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/brewlogs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/brewlogs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_create_rejects_extra_field(client: TestClient, refs: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/brewlogs",
        json={
            "date": "2026-04-01T08:00:00",
            **refs,
            "grind_setting": "22 clicks",
            "method": "V60",
            "dose_g": "15",
            "water_g": "250",
            "water_temp_c": 94,
            "brew_time_s": 150,
            "yield_g": None,
            "rating": 4,
            "taste_result": "Balanced",
            "tasting_notes": [],
            "notes": None,
            "photo_url": None,
            "mystery": "x",
        },
    )
    assert response.status_code == 422


def test_pagination_query_bounds_are_enforced(
    client: TestClient, refs: dict[str, str]
) -> None:
    make_brewlog(client, **refs)
    # page must be >= 1
    assert client.get("/api/v1/brewlogs", params={"page": 0}).status_code == 422
    # page_size must be <= 100
    assert client.get("/api/v1/brewlogs", params={"page_size": 500}).status_code == 422
