"""Integration tests for /api/v1/equipment."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import make_brewer, make_grinder


def test_create_brewer(client: TestClient) -> None:
    brewer = make_brewer(client)
    assert brewer["type"] == "Brewer"
    assert brewer["grind_type"] is None


def test_create_grinder(client: TestClient) -> None:
    grinder = make_grinder(client)
    assert grinder["type"] == "Grinder"
    assert grinder["grind_type"] == "Stepped"


def test_grinder_requires_grind_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Orphan",
            "type": "Grinder",
            "brand": "X",
            "model": None,
            "grind_type": None,
            "grind_range": None,
            "grind_unit": None,
            "notes": None,
        },
    )
    assert response.status_code == 422
    assert "grind_type" in response.text


def test_brewer_cannot_have_grinder_fields(client: TestClient) -> None:
    response = client.post(
        "/api/v1/equipment",
        json={
            "name": "Weirdbrewer",
            "type": "Brewer",
            "brand": "X",
            "model": None,
            "grind_type": "Stepless",
            "grind_range": None,
            "grind_unit": None,
            "notes": None,
        },
    )
    assert response.status_code == 422


def test_list_equipment_paginated(client: TestClient) -> None:
    for i in range(4):
        make_brewer(client, name=f"Brewer {i}")
    response = client.get("/api/v1/equipment", params={"page_size": 2})
    data = response.json()
    assert data["total"] == 4
    assert data["total_pages"] == 2


def test_update_equipment(client: TestClient) -> None:
    brewer = make_brewer(client)
    response = client.patch(
        f"/api/v1/equipment/{brewer['id']}",
        json={"model": "Ceramic"},
    )
    assert response.status_code == 200
    assert response.json()["model"] == "Ceramic"


def test_update_into_invalid_grinder_combo_is_rejected(client: TestClient) -> None:
    brewer = make_brewer(client)
    response = client.patch(
        f"/api/v1/equipment/{brewer['id']}",
        json={"grind_type": "Stepped"},
    )
    # Brewer can't get a grind_type — re-validation must catch it.
    assert response.status_code == 422


def test_update_unknown_equipment_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/equipment/00000000-0000-0000-0000-000000000000",
        json={"model": "X"},
    )
    assert response.status_code == 404


def test_delete_equipment(client: TestClient) -> None:
    brewer = make_brewer(client)
    response = client.delete(f"/api/v1/equipment/{brewer['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/equipment/{brewer['id']}").status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/equipment/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/equipment/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
