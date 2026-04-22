# BrewLog Backend

In-memory REST API for the BrewLog coffee journal, built with **FastAPI 0.115 +
Pydantic 2.9**. Framework choice and trade-offs are documented in
[`../BACKEND_EVALUATION.md`](../BACKEND_EVALUATION.md).

> **Bronze constraint:** no persistence of any kind. Every entity lives in a
> `dict` inside `app/services/state.py`. Restarting the process wipes the data.

## Quick start

```bash
# from backend/
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# run the API
.venv/bin/uvicorn app.main:app --reload --port 8000

# open Swagger UI
# http://localhost:8000/docs
```

Frontend (Vite on `:5173`) is allowed through CORS by default.

## Tests & coverage

```bash
.venv/bin/pytest
```

Current status: **90 tests passing, 100 % line + branch coverage**. Coverage
gate is enforced at 90 % via `pyproject.toml`.

## Project layout

```
backend/
  app/
    main.py                # FastAPI app factory, CORS, /health
    pagination.py          # PageParams dependency + Page[T] envelope
    api/                   # REST routers — one per resource
      __init__.py          # composes api_router (prefix=/api/v1)
      deps.py              # FastAPI dependencies for each store
      brewlogs.py          # CRUD + filtering
      beans.py             # CRUD + roaster FK check
      equipment.py         # CRUD + grinder-only field rules
      roasters.py          # CRUD
      stats.py             # aggregated dashboard metrics
    schemas/               # Pydantic validation models
      common.py            # enums (BrewMethod, TasteResult, ...)
      brewlog.py           # strict validators: ratio, temp bands, rating>notes
      bean.py
      equipment.py
      roaster.py
      stats.py
    services/
      store.py             # generic thread-safe InMemoryStore[T]
      state.py             # AppState aggregate + reset_state() for tests
  tests/
    conftest.py            # TestClient fixture + factories + state reset
    test_brewlogs.py       # CRUD, filters, validation, pagination
    test_beans.py
    test_equipment.py
    test_roasters.py
    test_stats.py
    test_pagination.py     # unit tests for pagination helper
    test_store.py          # unit tests for InMemoryStore
    test_validation_schemas.py
    test_health.py
```

## API surface

Base URL: `/api/v1`

| Method | Path                          | Description                                   |
|--------|-------------------------------|-----------------------------------------------|
| GET    | `/health`                     | Liveness probe                                |
| GET    | `/docs`                       | Swagger UI                                    |
| GET    | `/openapi.json`               | OpenAPI schema                                |
| GET    | `/brewlogs`                   | Paginated list, filters: `method`, `taste_result`, `bean_id`, `min_rating`, `max_rating`, `date_from`, `date_to` |
| POST   | `/brewlogs`                   | Create                                        |
| GET    | `/brewlogs/{id}`              | Fetch one                                     |
| PATCH  | `/brewlogs/{id}`              | Partial update (re-validates business rules)  |
| DELETE | `/brewlogs/{id}`              | 204 on success                                |
| GET/POST/GET/PATCH/DELETE | `/beans`, `/beans/{id}`            | CRUD + roaster FK check                       |
| GET/POST/GET/PATCH/DELETE | `/equipment`, `/equipment/{id}`    | CRUD + grinder-only field rules               |
| GET/POST/GET/PATCH/DELETE | `/roasters`, `/roasters/{id}`      | CRUD                                          |
| GET    | `/stats/brewlogs`             | Aggregates: total, avg rating, by method, by taste, balanced ratio |

All list endpoints return the common envelope:

```json
{
  "items": [...],
  "total": 42,
  "page": 2,
  "page_size": 10,
  "total_pages": 5
}
```

Pagination query params: `page` (≥ 1, default 1), `page_size` (1–100,
default 20). FastAPI rejects out-of-range values with **422** before any
handler runs.

## Validation rules — server side

All rules come from the assignment spec (`../A0.md`) and match the client-side
validator in `brewlog/src/app/hooks/useBrewValidation.ts`. Violations produce
**422** with a Pydantic error list.

**Field level**
- UUIDs are validated by FastAPI's path converter.
- `extra="forbid"` on every schema → unknown fields reject the request.
- `Field(gt=…)`, `Field(ge=…, le=…)`, `min_length`, `max_length`, `HttpUrl`,
  enum membership, etc.

**Business rules (`BrewLog.model_validator`)**
- `water_g / dose_g` must be in `[10, 20]` for every non-espresso method.
- `water_temp_c` must be inside the method-specific band
  (V60/Chemex 90–96, French Press 92–96, AeroPress 80–95, Espresso 85–100,
  Moka Pot 90–100, Cold Brew 1–25).
- Espresso brews must carry a `yield_g`.
- Any `rating < 3` requires non-empty `notes` (actionable dial-in history).

**Equipment rules (`Equipment.model_validator`)**
- `grind_type` is required iff `type == "Grinder"`.
- `grind_type`, `grind_range`, `grind_unit` are rejected on non-grinder types.

**FK rules (endpoint layer)**
- `BrewLog.bean_id`, `equipment_id`, `grinder_id` must resolve to existing
  rows. Same for `Bean.roaster_id`.
- Partial updates that touch an FK re-check it; partial updates that touch
  any field re-validate the merged entity.

## Architectural notes

- **Separation of endpoints from implementation** (Bronze requirement):
  routes in `app/api/` only orchestrate — they call `InMemoryStore` for I/O
  and Pydantic for validation. No business logic inlined in route handlers.
- **Dependency injection**: stores are injected through `Depends(...)` so tests
  can swap in an empty state via `reset_state()` between cases (`conftest.py`
  does this in an `autouse` fixture).
- **Thread safety**: `InMemoryStore` guards its dict with an `RLock`, which
  matters once the Silver challenge introduces an async Faker producer loop.
- **Pydantic 2**: server-side validation is declared once and reused for
  OpenAPI doc generation. Error responses drop `input`, `context`, and `url`
  fields so the payloads stay JSON-serializable even when inputs contain
  UUID/enum objects.

## What's next

- **Silver** — WebSocket endpoint + async Faker producer (`app/ws/` +
  `app/services/generator.py`). Hooks into the same `InMemoryStore` so clients
  receive batched inserts in real time.
- **Gold** — add Strawberry GraphQL exposing the same schemas/services at
  `/graphql`. No code duplication: types derive from Pydantic models.
