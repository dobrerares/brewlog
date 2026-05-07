"""GraphQL queries + mutations + 1-to-many relationships — DB-backed."""

from __future__ import annotations

from httpx import AsyncClient


async def _gql(client: AsyncClient, query: str, variables: dict | None = None) -> dict:
    response = await client.post(
        "/graphql",
        json={"query": query, "variables": variables or {}},
    )
    assert response.status_code == 200, response.text
    return response.json()


# --- async factory helpers ------------------------------------------------


async def make_roaster(client: AsyncClient, **overrides: object) -> dict:
    payload = {
        "name": "Nomad Coffee",
        "location": "Barcelona",
        "website": None,
        "notes": None,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/roasters", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def make_bean(
    client: AsyncClient,
    roaster_id: str | None = None,
    **overrides: object,
) -> dict:
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
    response = await client.post("/api/v1/beans", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def make_brewer(client: AsyncClient, **overrides: object) -> dict:
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
    response = await client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def make_grinder(client: AsyncClient, **overrides: object) -> dict:
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
    response = await client.post("/api/v1/equipment", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def make_brewlog(
    client: AsyncClient,
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
    response = await client.post("/api/v1/brewlogs", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# --- schema / query smoke ------------------------------------------------


async def test_schema_exposes_root_queries(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        {
          __schema { queryType { fields { name } } }
        }
        """,
    )
    names = {f["name"] for f in body["data"]["__schema"]["queryType"]["fields"]}
    assert {"roasters", "beans", "equipmentList", "brewlogs", "brewStats"} <= names


async def test_paginated_queries_cover_every_resource(client: AsyncClient) -> None:
    await make_roaster(client)
    await make_bean(client)
    await make_brewer(client)
    body = await _gql(
        client,
        """
        {
          roasters(page: 1, pageSize: 5) { total items { id } }
          beans(page: 1, pageSize: 5) { total items { id } }
          equipmentList(page: 1, pageSize: 5) { total items { id } }
        }
        """,
    )
    assert body["data"]["roasters"]["total"] == 1
    assert body["data"]["beans"]["total"] == 1
    assert body["data"]["equipmentList"]["total"] == 1


async def test_empty_brewlogs_page(client: AsyncClient) -> None:
    body = await _gql(
        client,
        "{ brewlogs { total items { id } page totalPages } }",
    )
    data = body["data"]["brewlogs"]
    assert data == {"total": 0, "items": [], "page": 1, "totalPages": 0}


# --- create via mutation, read via query ---------------------------------


async def test_create_roaster_and_read_back(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($input: RoasterInput!) {
          createRoaster(input: $input) { id name location }
        }
        """,
        {"input": {"name": "Onyx", "location": "Boston"}},
    )
    created = body["data"]["createRoaster"]
    assert created["name"] == "Onyx"

    body = await _gql(
        client,
        "{ roasters { total items { id name location } } }",
    )
    assert body["data"]["roasters"]["total"] == 1
    assert body["data"]["roasters"]["items"][0]["id"] == created["id"]


async def test_create_bean_links_to_roaster(client: AsyncClient) -> None:
    roaster = await make_roaster(client)
    body = await _gql(
        client,
        """
        mutation ($input: BeanInput!) {
          createBean(input: $input) { id name roaster { name } }
        }
        """,
        {
            "input": {
                "name": "Finca X",
                "roasterId": roaster["id"],
                "originCountry": "Colombia",
                "process": "WASHED",
                "roastLevel": "LIGHT",
            }
        },
    )
    bean = body["data"]["createBean"]
    assert bean["roaster"]["name"] == roaster["name"]


async def test_mutation_surfaces_validation_errors(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($input: RoasterInput!) {
          createRoaster(input: $input) { id }
        }
        """,
        {"input": {"name": ""}},  # blank name — Pydantic rejects
    )
    assert "errors" in body
    assert "name" in body["errors"][0]["message"]


async def test_create_bean_with_unknown_roaster_errors(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($input: BeanInput!) {
          createBean(input: $input) { id }
        }
        """,
        {
            "input": {
                "name": "Bean",
                "roasterId": "00000000-0000-0000-0000-000000000000",
                "originCountry": "CO",
                "process": "WASHED",
                "roastLevel": "LIGHT",
            }
        },
    )
    assert "errors" in body
    assert "roaster_id" in body["errors"][0]["message"]


# --- Gold "1-to-many": full relationship story in one query --------------


async def test_one_to_many_relationships(client: AsyncClient) -> None:
    """Roaster → Beans → BrewLogs and Equipment → BrewLogs."""
    roaster = await make_roaster(client, name="R1")
    bean1 = await make_bean(client, roaster_id=roaster["id"], name="Bean 1")
    bean2 = await make_bean(client, roaster_id=roaster["id"], name="Bean 2")
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)

    # Two brews on bean1, one on bean2
    await make_brewlog(client, bean1["id"], brewer["id"], grinder["id"])
    await make_brewlog(client, bean1["id"], brewer["id"], grinder["id"])
    await make_brewlog(client, bean2["id"], brewer["id"], grinder["id"])

    body = await _gql(
        client,
        """
        query ($id: UUID!) {
          roaster(id: $id) {
            name
            beans {
              name
              brewlogs { id method rating }
            }
          }
        }
        """,
        {"id": roaster["id"]},
    )
    data = body["data"]["roaster"]
    assert data["name"] == "R1"
    beans = {b["name"]: b for b in data["beans"]}
    assert len(beans["Bean 1"]["brewlogs"]) == 2
    assert len(beans["Bean 2"]["brewlogs"]) == 1

    # Equipment → brewlogs resolver
    body = await _gql(
        client,
        """
        query ($id: UUID!) {
          equipment(id: $id) { name brewlogs { id } }
        }
        """,
        {"id": brewer["id"]},
    )
    assert len(body["data"]["equipment"]["brewlogs"]) == 3


async def test_brewlog_nested_entities_resolve(client: AsyncClient) -> None:
    roaster = await make_roaster(client, name="R")
    bean = await make_bean(client, roaster_id=roaster["id"], name="B")
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    brew = await make_brewlog(client, bean["id"], brewer["id"], grinder["id"])

    body = await _gql(
        client,
        """
        query ($id: UUID!) {
          brewlog(id: $id) {
            method
            bean { name roaster { name } }
            equipment { name }
            grinder { name type }
          }
        }
        """,
        {"id": brew["id"]},
    )
    data = body["data"]["brewlog"]
    assert data["bean"]["name"] == "B"
    assert data["bean"]["roaster"]["name"] == "R"
    assert data["equipment"]["name"] == "Hario V60"
    assert data["grinder"]["type"] == "GRINDER"


async def test_brewlogs_query_supports_pagination_and_filter(client: AsyncClient) -> None:
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    for _ in range(5):
        await make_brewlog(client, bean["id"], brewer["id"], grinder["id"])

    body = await _gql(
        client,
        """
        query { brewlogs(page: 2, pageSize: 2, method: V60) {
            total page pageSize totalPages items { id method }
        } }
        """,
    )
    data = body["data"]["brewlogs"]
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["pageSize"] == 2
    assert data["totalPages"] == 3
    assert len(data["items"]) == 2
    assert all(item["method"] == "V60" for item in data["items"])


# --- Update & delete mutations ------------------------------------------


async def test_update_and_delete_via_graphql(client: AsyncClient) -> None:
    roaster = await make_roaster(client)
    bean = await make_bean(client, roaster_id=roaster["id"])

    updated = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: BeanPatch!) {
          updateBean(id: $id, input: $input) { id roastLevel }
        }
        """,
        {"id": bean["id"], "input": {"roastLevel": "DARK"}},
    )
    assert updated["data"]["updateBean"]["roastLevel"] == "DARK"

    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteBean(id: $id) }",
        {"id": bean["id"]},
    )
    assert body["data"]["deleteBean"] is True

    # Second delete is a no-op returning False, not an exception.
    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteBean(id: $id) }",
        {"id": bean["id"]},
    )
    assert body["data"]["deleteBean"] is False


async def test_brewlog_update_revalidates_business_rules(client: AsyncClient) -> None:
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    brew = await make_brewlog(
        client, bean["id"], brewer["id"], grinder["id"], rating=4, taste_result="Balanced"
    )

    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: BrewLogPatch!) {
          updateBrewlog(id: $id, input: $input) { id rating }
        }
        """,
        {"id": brew["id"], "input": {"rating": 2, "notes": None}},
    )
    assert "errors" in body
    assert "notes" in body["errors"][0]["message"]


async def test_update_unknown_entity_returns_graphql_error(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: RoasterPatch!) {
          updateRoaster(id: $id, input: $input) { id }
        }
        """,
        {"id": "00000000-0000-0000-0000-000000000000", "input": {"name": "X"}},
    )
    assert "errors" in body


async def test_unknown_single_entity_returns_null(client: AsyncClient) -> None:
    body = await _gql(
        client,
        "query ($id: UUID!) { roaster(id: $id) { id } }",
        {"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert body["data"]["roaster"] is None


async def test_brew_stats_aggregates_via_graphql(client: AsyncClient) -> None:
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    await make_brewlog(client, bean["id"], brewer["id"], grinder["id"], rating=5)
    await make_brewlog(client, bean["id"], brewer["id"], grinder["id"], rating=3)

    body = await _gql(
        client,
        """
        {
          brewStats {
            totalBrews
            averageRating
            mostUsedMethod
            byMethod { method count }
            balancedRatio
          }
        }
        """,
    )
    data = body["data"]["brewStats"]
    assert data["totalBrews"] == 2
    assert data["averageRating"] == 4.0


# --- Equipment + full CRUD ----------------------------------------------


async def test_create_update_delete_equipment_via_graphql(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($input: EquipmentInput!) {
          createEquipment(input: $input) { id name type grindType }
        }
        """,
        {
            "input": {
                "name": "Ode",
                "type": "GRINDER",
                "brand": "Fellow",
                "grindType": "STEPPED",
                "grindRange": "1-11",
                "grindUnit": "1 step",
            }
        },
    )
    grinder = body["data"]["createEquipment"]
    assert grinder["grindType"] == "STEPPED"

    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: EquipmentPatch!) {
          updateEquipment(id: $id, input: $input) { id model }
        }
        """,
        {"id": grinder["id"], "input": {"model": "Gen2"}},
    )
    assert body["data"]["updateEquipment"]["model"] == "Gen2"

    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteEquipment(id: $id) }",
        {"id": grinder["id"]},
    )
    assert body["data"]["deleteEquipment"] is True


async def test_create_brewlog_with_unknown_bean_errors(client: AsyncClient) -> None:
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    body = await _gql(
        client,
        """
        mutation ($input: BrewLogInput!) {
          createBrewlog(input: $input) { id }
        }
        """,
        {
            "input": {
                "date": "2026-04-01T08:00:00",
                "beanId": "00000000-0000-0000-0000-000000000000",
                "equipmentId": brewer["id"],
                "grinderId": grinder["id"],
                "grindSetting": "22 clicks",
                "method": "V60",
                "doseG": 15.0,
                "waterG": 250.0,
                "waterTempC": 94,
                "brewTimeS": 150,
                "rating": 4,
                "tasteResult": "BALANCED",
            }
        },
    )
    assert "errors" in body
    assert "bean_id" in body["errors"][0]["message"]


async def test_update_equipment_unknown_errors(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: EquipmentPatch!) {
          updateEquipment(id: $id, input: $input) { id }
        }
        """,
        {"id": "00000000-0000-0000-0000-000000000000", "input": {"model": "X"}},
    )
    assert "errors" in body


async def test_update_brewlog_unknown_errors(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: BrewLogPatch!) {
          updateBrewlog(id: $id, input: $input) { id }
        }
        """,
        {"id": "00000000-0000-0000-0000-000000000000", "input": {"rating": 5}},
    )
    assert "errors" in body


async def test_update_bean_unknown_errors(client: AsyncClient) -> None:
    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: BeanPatch!) {
          updateBean(id: $id, input: $input) { id }
        }
        """,
        {"id": "00000000-0000-0000-0000-000000000000", "input": {"roastLevel": "DARK"}},
    )
    assert "errors" in body


async def test_delete_roaster_returns_false_when_unknown(client: AsyncClient) -> None:
    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteRoaster(id: $id) }",
        {"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert body["data"]["deleteRoaster"] is False


async def test_delete_brewlog_via_graphql(client: AsyncClient) -> None:
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    brew = await make_brewlog(client, bean["id"], brewer["id"], grinder["id"])
    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteBrewlog(id: $id) }",
        {"id": brew["id"]},
    )
    assert body["data"]["deleteBrewlog"] is True
    # second delete no-ops
    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteBrewlog(id: $id) }",
        {"id": brew["id"]},
    )
    assert body["data"]["deleteBrewlog"] is False


async def test_delete_equipment_returns_false_when_unknown(client: AsyncClient) -> None:
    body = await _gql(
        client,
        "mutation ($id: UUID!) { deleteEquipment(id: $id) }",
        {"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert body["data"]["deleteEquipment"] is False


async def test_update_roaster_partial(client: AsyncClient) -> None:
    roaster = await make_roaster(client)
    body = await _gql(
        client,
        """
        mutation ($id: UUID!, $input: RoasterPatch!) {
          updateRoaster(id: $id, input: $input) { id location }
        }
        """,
        {"id": roaster["id"], "input": {"location": "Madrid"}},
    )
    assert body["data"]["updateRoaster"]["location"] == "Madrid"


async def test_bean_with_null_roaster_query_path(client: AsyncClient) -> None:
    bean = await make_bean(client)  # no roaster attached
    body = await _gql(
        client,
        """
        query ($id: UUID!) { bean(id: $id) { name roaster { id } } }
        """,
        {"id": bean["id"]},
    )
    assert body["data"]["bean"]["roaster"] is None


async def test_brewlogs_query_date_range(client: AsyncClient) -> None:
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    await make_brewlog(client, bean["id"], brewer["id"], grinder["id"], date="2026-02-01T08:00:00")
    await make_brewlog(client, bean["id"], brewer["id"], grinder["id"], date="2026-04-01T08:00:00")

    body = await _gql(
        client,
        """
        query {
          brewlogs(dateFrom: "2026-03-01T00:00:00") { total }
        }
        """,
    )
    assert body["data"]["brewlogs"]["total"] == 1

    body = await _gql(
        client,
        """
        query {
          brewlogs(dateTo: "2026-03-01T00:00:00") { total }
        }
        """,
    )
    assert body["data"]["brewlogs"]["total"] == 1


async def test_brewlogs_query_all_filters(client: AsyncClient) -> None:
    bean1 = await make_bean(client, name="B1")
    bean2 = await make_bean(client, name="B2")
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)

    await make_brewlog(
        client, bean1["id"], brewer["id"], grinder["id"],
        rating=5, taste_result="Balanced",
    )
    await make_brewlog(
        client, bean2["id"], brewer["id"], grinder["id"],
        rating=2, taste_result="Sour", notes="under-extracted",
    )

    # taste filter
    body = await _gql(
        client,
        'query { brewlogs(tasteResult: SOUR) { total items { rating } } }',
    )
    assert body["data"]["brewlogs"]["total"] == 1
    assert body["data"]["brewlogs"]["items"][0]["rating"] == 2

    # rating range
    body = await _gql(client, "query { brewlogs(minRating: 4, maxRating: 5) { total } }")
    assert body["data"]["brewlogs"]["total"] == 1

    # bean id
    body = await _gql(
        client,
        "query ($b: UUID!) { brewlogs(beanId: $b) { total } }",
        {"b": bean2["id"]},
    )
    assert body["data"]["brewlogs"]["total"] == 1


async def test_unknown_queries_return_null(client: AsyncClient) -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    for field in ("bean", "equipment", "brewlog"):
        body = await _gql(
            client,
            f"query ($id: UUID!) {{ {field}(id: $id) {{ id }} }}",
            {"id": missing},
        )
        assert body["data"][field] is None


async def test_brewlog_nested_fields_resolve_when_parents_exist(client: AsyncClient) -> None:
    # DB enforces RESTRICT FK, so parents can't be deleted while brewlog exists.
    # This test verifies that the nested field resolvers correctly return
    # non-null values when all referenced parents are present.
    bean = await make_bean(client)
    brewer = await make_brewer(client)
    grinder = await make_grinder(client)
    brew = await make_brewlog(client, bean["id"], brewer["id"], grinder["id"])

    body = await _gql(
        client,
        """
        query ($id: UUID!) {
          brewlog(id: $id) {
            id
            bean { id name }
            equipment { id name }
            grinder { id name }
          }
        }
        """,
        {"id": brew["id"]},
    )
    data = body["data"]["brewlog"]
    assert data["bean"] is not None
    assert data["bean"]["id"] == bean["id"]
    assert data["equipment"] is not None
    assert data["equipment"]["id"] == brewer["id"]
    assert data["grinder"] is not None
    assert data["grinder"]["id"] == grinder["id"]
    # Verify non-existent brewlog returns None (null resolver path)
    body2 = await _gql(
        client,
        "query ($id: UUID!) { brewlog(id: $id) { id } }",
        {"id": "00000000-0000-0000-0000-000000000099"},
    )
    assert body2["data"]["brewlog"] is None


async def test_bean_with_missing_roaster_resolver_returns_null(client: AsyncClient) -> None:
    roaster = await make_roaster(client)
    bean = await make_bean(client, roaster_id=roaster["id"])
    # Roaster deletion leaves the bean pointing at a phantom id.
    await client.delete(f"/api/v1/roasters/{roaster['id']}")

    body = await _gql(
        client,
        "query ($id: UUID!) { bean(id: $id) { roaster { id } } }",
        {"id": bean["id"]},
    )
    assert body["data"]["bean"]["roaster"] is None
