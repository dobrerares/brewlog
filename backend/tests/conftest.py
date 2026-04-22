"""Shared pytest fixtures — resets the in-memory state for every test."""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import reset_state


@pytest.fixture(autouse=True)
def _fresh_state() -> Iterator[None]:
    reset_state()
    yield
    reset_state()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ------------------------------------------------------------------ factories


def make_roaster(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "Nomad Coffee",
        "location": "Barcelona",
        "website": "https://nomadcoffee.es/",
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/roasters", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_bean(client: TestClient, roaster_id: str | None = None, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Finca La Esperanza",
        "roaster_id": roaster_id,
        "origin_country": "Colombia",
        "origin_region": "Huila",
        "process": "Washed",
        "roast_level": "Light",
        "variety": "Caturra",
        "elevation_m": 1800,
        "tasting_notes": ["chocolate", "citrus"],
        "purchase_date": "2026-03-01",
        "price": "18.50",
    }
    payload.update(overrides)
    response = client.post("/api/v1/beans", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_brewer(client: TestClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Hario V60",
        "type": "Brewer",
        "brand": "Hario",
        "model": "02",
        "grind_type": None,
        "grind_range": None,
        "grind_unit": None,
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_grinder(client: TestClient, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "name": "Comandante C40",
        "type": "Grinder",
        "brand": "Comandante",
        "model": "MK4",
        "grind_type": "Stepped",
        "grind_range": "clicks 0-40",
        "grind_unit": "1 click",
        "notes": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def make_brewlog(
    client: TestClient,
    bean_id: str,
    equipment_id: str,
    grinder_id: str,
    **overrides: object,
) -> dict:
    payload: dict[str, object] = {
        "date": "2026-04-01T08:30:00",
        "bean_id": bean_id,
        "equipment_id": equipment_id,
        "grinder_id": grinder_id,
        "grind_setting": "22 clicks",
        "method": "V60",
        "dose_g": "15",
        "water_g": "250",
        "water_temp_c": 94,
        "brew_time_s": 150,
        "yield_g": None,
        "rating": 4,
        "taste_result": "Balanced",
        "grind_adjustment": None,
        "tasting_notes": ["chocolate"],
        "notes": "Solid pourover.",
        "photo_url": None,
    }
    payload.update(overrides)
    response = client.post("/api/v1/brewlogs", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
