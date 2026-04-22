from fastapi.testclient import TestClient


def test_health_endpoint_reports_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_is_served(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "BrewLog API"
    # Every resource is documented.
    paths = schema["paths"].keys()
    for expected in (
        "/api/v1/brewlogs",
        "/api/v1/beans",
        "/api/v1/equipment",
        "/api/v1/roasters",
        "/api/v1/stats/brewlogs",
    ):
        assert expected in paths, expected
