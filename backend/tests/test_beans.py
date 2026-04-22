"""Integration tests for /api/v1/beans."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import make_bean, make_roaster


def test_create_bean_with_roaster(client: TestClient) -> None:
    roaster = make_roaster(client)
    bean = make_bean(client, roaster_id=roaster["id"])
    assert bean["roaster_id"] == roaster["id"]


def test_create_bean_without_roaster(client: TestClient) -> None:
    bean = make_bean(client)
    assert bean["roaster_id"] is None


def test_create_bean_rejects_invalid_roaster(client: TestClient) -> None:
    response = client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": "00000000-0000-0000-0000-000000000000",
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "tasting_notes": [],
        },
    )
    assert response.status_code == 422


def test_create_bean_rejects_invalid_process(client: TestClient) -> None:
    response = client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Mystery",
            "roast_level": "Light",
        },
    )
    assert response.status_code == 422


def test_create_bean_rejects_negative_elevation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "elevation_m": -1,
        },
    )
    assert response.status_code == 422


def test_create_bean_rejects_too_many_tasting_notes(client: TestClient) -> None:
    response = client.post(
        "/api/v1/beans",
        json={
            "name": "Bean",
            "roaster_id": None,
            "origin_country": "CO",
            "process": "Washed",
            "roast_level": "Light",
            "tasting_notes": [f"n{i}" for i in range(40)],
        },
    )
    assert response.status_code == 422


def test_list_beans_paginated(client: TestClient) -> None:
    for i in range(5):
        make_bean(client, name=f"Bean {i}")
    response = client.get("/api/v1/beans", params={"page": 2, "page_size": 2})
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["total_pages"] == 3


def test_update_bean(client: TestClient) -> None:
    bean = make_bean(client)
    response = client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"roast_level": "Medium"},
    )
    assert response.status_code == 200
    assert response.json()["roast_level"] == "Medium"


def test_update_bean_into_unknown_roaster_is_rejected(client: TestClient) -> None:
    bean = make_bean(client)
    response = client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"roaster_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 422


def test_update_bean_with_invalid_field_returns_422(client: TestClient) -> None:
    bean = make_bean(client)
    response = client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"elevation_m": -5},
    )
    assert response.status_code == 422


def test_update_bean_that_nulls_required_field_returns_422(client: TestClient) -> None:
    bean = make_bean(client)
    # BeanUpdate allows null for optional fields. Sending null for a
    # Bean-required field passes the partial validator but must fail when
    # the merged entity is re-validated.
    response = client.patch(
        f"/api/v1/beans/{bean['id']}",
        json={"origin_country": None},
    )
    assert response.status_code == 422


def test_update_unknown_bean_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/beans/00000000-0000-0000-0000-000000000000",
        json={"roast_level": "Dark"},
    )
    assert response.status_code == 404


def test_delete_bean(client: TestClient) -> None:
    bean = make_bean(client)
    response = client.delete(f"/api/v1/beans/{bean['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/beans/{bean['id']}").status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/beans/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/beans/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
