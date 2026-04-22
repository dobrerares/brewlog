# BrewLog Backend

In-memory REST + GraphQL backend for the BrewLog coffee journal, built with
**FastAPI 0.115 + Pydantic 2.9 + Strawberry GraphQL 0.246**. Framework choice
and trade-offs are documented in [`../BACKEND_EVALUATION.md`](../BACKEND_EVALUATION.md).

Covers all three server-side challenges:

| Challenge | Scope | Where it lives |
|-----------|-------|----------------|
| **Bronze** | REST CRUD + stats, strict validation, server-side pagination, in-memory only | `app/api/`, `app/schemas/`, `app/services/store.py` |
| **Silver** | Async Faker producer loop (`/generator/{start,stop,status,tick}`) + WebSocket batch push (`/ws`) | `app/services/generator.py`, `app/services/broadcast.py`, `app/api/generator.py`, `app/api/websocket.py` |
| **Gold**   | Same logic re-exposed through a GraphQL endpoint at `/graphql`, including 1-to-many (`Roaster → Beans → BrewLogs`, `Equipment → BrewLogs`) | `app/gql/` |

> **Persistence constraint (all challenges):** no storage of any kind. Every
> entity lives in a `dict` inside `app/services/state.py`. Restarting the
> process wipes the data.

> **Client-side challenges** — Silver offline cache + sync, and Gold infinite
> scroll / 1-to-many frontend wiring — live in the React app (`brewlog/`) and
> are not implemented on this branch.

## Quick start

```bash
# from backend/
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# run the API
.venv/bin/uvicorn app.main:app --reload --port 8000

# REST        → http://localhost:8000/docs        (Swagger UI)
# GraphQL     → http://localhost:8000/graphql     (GraphiQL playground)
# WebSocket   → ws://localhost:8000/ws
```

Frontend (Vite on `:5173`) is allowed through CORS by default.

## Tests & coverage

```bash
.venv/bin/pytest
```

Current status: **129 tests passing, 95.7 % line + branch coverage**. Coverage
gate is enforced at 90 % via `pyproject.toml`.

```
tests/test_beans.py                 14  Bronze — beans CRUD
tests/test_brewlogs.py              25  Bronze — brewlog CRUD + filtering
tests/test_equipment.py             11  Bronze — equipment CRUD + grinder rules
tests/test_roasters.py               9  Bronze — roaster CRUD
tests/test_stats.py                  2  Bronze — stats aggregation
tests/test_pagination.py             6  Bronze — pagination helper
tests/test_store.py                  9  Bronze — in-memory store
tests/test_validation_schemas.py    11  Bronze — direct Pydantic validators
tests/test_health.py                 2  meta (health + OpenAPI)
tests/test_generator.py              9  Silver — Faker loop + WebSocket
tests/test_graphql.py               31  Gold  — queries, mutations, 1-to-many
```

## Project layout

```
backend/
  app/
    main.py                # FastAPI app factory, CORS, /health, router mounts
    pagination.py          # PageParams dependency + Page[T] envelope
    api/                   # Bronze + Silver REST / WebSocket
      deps.py              # FastAPI dependencies for each store
      brewlogs.py          # CRUD + filtering (method, taste, bean, rating, date)
      beans.py             # CRUD + roaster FK check
      equipment.py         # CRUD + grinder-only field rules
      roasters.py          # CRUD
      stats.py             # aggregated dashboard metrics
      generator.py         # /generator/{status,start,stop,tick}
      websocket.py         # /ws broadcast endpoint
    schemas/               # Pydantic validation models
      common.py            # enums (BrewMethod, TasteResult, Process, …)
      brewlog.py           # strict validators: ratio, temp bands, rating>notes
      bean.py              # FK to roaster, tasting notes
      equipment.py         # grinder-only field rules
      roaster.py           # HttpUrl website
      stats.py             # MethodCount / TasteCount / BrewStats
    services/
      store.py             # generic thread-safe InMemoryStore[T]
      state.py             # AppState aggregate + reset_state() for tests
      broadcast.py         # Silver — async WebSocket ConnectionManager
      generator.py         # Silver — BrewLogGenerator with Faker
    gql/                   # Gold — GraphQL layer
      types.py             # @strawberry.type / @strawberry.input (with UNSET)
      queries.py           # list/get + pagination + stats
      mutations.py         # create/update/delete reusing Pydantic Create/Update
      schema.py            # Strawberry schema + FastAPI router factory
  tests/
    conftest.py            # TestClient fixture + factories + state reset
    test_*.py              # see table above
```

## REST surface — `/api/v1`

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
| `CRUD` | `/beans`, `/beans/{id}`       | CRUD + roaster FK check                       |
| `CRUD` | `/equipment`, `/equipment/{id}` | CRUD + grinder-only field rules             |
| `CRUD` | `/roasters`, `/roasters/{id}` | CRUD                                          |
| GET    | `/stats/brewlogs`             | Aggregates: total, avg rating, by method, by taste, balanced ratio |
| GET    | `/generator/status`           | Current loop status (`running`, `batches_emitted`, …) |
| POST   | `/generator/start`            | Start loop — body: `{ batch_size, interval_s }` |
| POST   | `/generator/stop`              | Stop loop (202 if running, 409 otherwise)     |
| POST   | `/generator/tick`              | Emit one batch immediately (test / demo)      |

All list endpoints return the common envelope:

```json
{ "items": [...], "total": 42, "page": 2, "page_size": 10, "total_pages": 5 }
```

Pagination query params: `page` (≥ 1, default 1), `page_size` (1–100,
default 20). FastAPI rejects out-of-range values with **422** before any
handler runs.

## Silver — Faker loop + WebSocket

1. Client opens `ws://.../ws` — FastAPI accepts it via `ConnectionManager`.
2. Client POSTs `/api/v1/generator/start` with a batch size and interval.
3. The generator emits fake, fully-validated `BrewLog` entities and inserts
   them into the in-memory store.
4. After each batch, the server broadcasts:

   ```json
   {
     "type": "brewlog.batch",
     "count": 3,
     "items": [ { /* serialized BrewLog */ }, ... ]
   }
   ```

5. Clients refresh their master/detail view and charts from the received
   payload (the frontend side of this flow lives in `brewlog/`).

The generator seeds one roaster / bean / brewer / grinder the first time it
runs so FK constraints can always be satisfied. Subsequent batches reuse
them; user-created entities are preserved.

## Gold — GraphQL at `/graphql`

Same data and business rules, re-exposed through a GraphQL schema. Pydantic
is still the source of truth for validation — resolvers convert Strawberry
inputs into `*Create` / `*Update` models, and any `ValidationError` surfaces
as a GraphQL error with the concatenated Pydantic messages.

### Root types

- **Query** — `roasters`, `roaster(id)`, `beans`, `bean(id)`,
  `equipmentList`, `equipment(id)`, `brewlogs(...filters)`, `brewlog(id)`,
  `brewStats`.
- **Mutation** — `create{Roaster,Bean,Equipment,Brewlog}`,
  `update{Roaster,Bean,Equipment,Brewlog}`, `delete{Roaster,Bean,Equipment,Brewlog}`.

### 1-to-many relationships

Modeled as nested resolvers on the parent type:

- `Roaster.beans` → every `Bean` whose `roaster_id` matches.
- `Bean.roaster` → inverse of the above.
- `Bean.brewlogs` → every `BrewLog` that references this bean.
- `Equipment.brewlogs` → every `BrewLog` where this equipment is either the
  brewer or the grinder.
- `BrewLog.bean` / `BrewLog.equipment` / `BrewLog.grinder` — single-parent
  resolvers for detail views.

The combination covers the Gold "1-to-many" deliverable server-side: a single
GraphQL query can walk `roaster → beans → brewlogs` without extra round trips.

Example end-to-end query:

```graphql
query {
  roaster(id: "...") {
    name
    beans {
      name
      brewlogs {
        id
        method
        rating
        tasteResult
      }
    }
  }
}
```

## Validation — server side

All rules come from the assignment spec (`../A0.md`) and match the
client-side validator in `brewlog/src/app/hooks/useBrewValidation.ts`.
Violations produce **422** on REST and a GraphQL error on `/graphql`.

**Field level**
- UUIDs validated by FastAPI's path converter / Strawberry's scalar.
- `extra="forbid"` on every schema → unknown fields reject the request.
- `Field(gt=…)`, `Field(ge=…, le=…)`, `min_length`, `max_length`, `HttpUrl`,
  enum membership, etc.

**Business rules (`BrewLog.model_validator`)**
- `water_g / dose_g` must be in `[10, 20]` for every non-espresso method.
- `water_temp_c` must sit inside the method-specific band
  (V60/Chemex 90–96, French Press 92–96, AeroPress 80–95, Espresso 85–100,
  Moka Pot 90–100, Cold Brew 1–25).
- Espresso brews must carry a `yield_g`.
- Any `rating < 3` requires non-empty `notes`.

**Equipment rules (`Equipment.model_validator`)**
- `grind_type` is required iff `type == "Grinder"`.
- Grinder-only fields (`grind_type`, `grind_range`, `grind_unit`) are
  rejected on non-grinder types.

**FK rules (endpoint + resolver layer)**
- `BrewLog.bean_id`, `equipment_id`, `grinder_id` must resolve to existing
  rows. Same for `Bean.roaster_id`. Partial updates that touch an FK
  re-check it; partial updates that touch any field re-validate the merged
  entity.

## Architectural notes

- **Endpoint / resolver separation**: REST handlers and GraphQL resolvers
  only orchestrate — they call `InMemoryStore` for I/O and reuse the same
  Pydantic Create/Update models for validation. No business logic inlined
  into FastAPI or Strawberry.
- **Dependency injection**: stores are injected through `Depends(...)` so
  tests can swap in a fresh state via `reset_state()` between cases
  (`conftest.py` does this in an `autouse` fixture).
- **Thread safety**: `InMemoryStore` guards its dict with an `RLock`, which
  matters once the Silver async Faker producer is running alongside REST
  traffic.
- **Pydantic 2**: server-side validation is declared once and reused for
  OpenAPI doc generation *and* GraphQL mutation validation. Error responses
  strip `input`, `context`, and `url` so the payloads stay JSON-serialisable
  even when inputs contain UUID/enum objects.
- **Strawberry `UNSET` defaults**: input types default optional fields to
  `strawberry.UNSET`; the resolver's `strip_unset` helper filters those out
  before handing the dict to Pydantic. This keeps the Pydantic defaults
  (`tasting_notes: list[str] = []`, etc.) working instead of being replaced
  by `None`.
