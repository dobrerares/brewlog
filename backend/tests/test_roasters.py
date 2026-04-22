"""Integration tests for /api/v1/roasters."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import make_roaster


def test_create_and_get_roaster(client: TestClient) -> None:
    roaster = make_roaster(client, name="Onyx")
    got = client.get(f"/api/v1/roasters/{roaster['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "Onyx"


def test_list_roasters_is_paginated(client: TestClient) -> None:
    for i in range(7):
        make_roaster(client, name=f"Roaster {i}")
    response = client.get("/api/v1/roasters", params={"page": 2, "page_size": 3})
    data = response.json()
    assert data["total"] == 7
    assert data["page"] == 2
    assert data["page_size"] == 3
    assert data["total_pages"] == 3
    assert len(data["items"]) == 3


def test_update_roaster_partial(client: TestClient) -> None:
    roaster = make_roaster(client)
    response = client.patch(
        f"/api/v1/roasters/{roaster['id']}",
        json={"location": "Madrid"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Madrid"
    assert body["name"] == roaster["name"]  # unchanged


def test_update_unknown_roaster_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/roasters/00000000-0000-0000-0000-000000000000",
        json={"location": "Madrid"},
    )
    assert response.status_code == 404


def test_delete_roaster(client: TestClient) -> None:
    roaster = make_roaster(client)
    response = client.delete(f"/api/v1/roasters/{roaster['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/roasters/{roaster['id']}").status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/roasters/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_create_rejects_blank_name(client: TestClient) -> None:
    response = client.post(
        "/api/v1/roasters",
        json={"name": "", "website": None},
    )
    assert response.status_code == 422


def test_create_rejects_malformed_url(client: TestClient) -> None:
    response = client.post(
        "/api/v1/roasters",
        json={"name": "X", "website": "not a url"},
    )
    assert response.status_code == 422


def test_create_rejects_unknown_field(client: TestClient) -> None:
    response = client.post(
        "/api/v1/roasters",
        json={"name": "X", "mystery": 1},
    )
    assert response.status_code == 422
