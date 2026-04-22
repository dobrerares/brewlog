"""Integration tests for /api/v1/stats/brewlogs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import make_bean, make_brewer, make_brewlog, make_grinder


def test_stats_empty_collection(client: TestClient) -> None:
    response = client.get("/api/v1/stats/brewlogs")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "total_brews": 0,
        "average_rating": None,
        "most_used_method": None,
        "by_method": [],
        "by_taste": [],
        "balanced_ratio": None,
    }


def test_stats_aggregates_correctly(client: TestClient) -> None:
    bean = make_bean(client)
    brewer = make_brewer(client)
    grinder = make_grinder(client)
    refs = dict(bean_id=bean["id"], equipment_id=brewer["id"], grinder_id=grinder["id"])

    make_brewlog(client, **refs, method="V60", rating=4, taste_result="Balanced")
    make_brewlog(client, **refs, method="V60", rating=5, taste_result="Balanced")
    make_brewlog(
        client,
        **refs,
        method="V60",
        rating=2,
        taste_result="Sour",
        notes="under-extracted",
    )
    make_brewlog(
        client,
        **refs,
        method="Espresso",
        dose_g="18",
        water_g="36",
        water_temp_c=93,
        brew_time_s=30,
        yield_g="34",
        rating=3,
        taste_result="Astringent",
        notes=None,
    )

    response = client.get("/api/v1/stats/brewlogs")
    body = response.json()
    assert body["total_brews"] == 4
    assert body["most_used_method"] == "V60"
    # (4+5+2+3)/4 == 3.5
    assert body["average_rating"] == 3.5

    methods = {entry["method"]: entry["count"] for entry in body["by_method"]}
    assert methods == {"V60": 3, "Espresso": 1}

    tastes = {entry["taste_result"]: entry["count"] for entry in body["by_taste"]}
    assert tastes == {"Balanced": 2, "Sour": 1, "Astringent": 1}

    # 2 balanced out of 4 rated brews
    assert body["balanced_ratio"] == 0.5
