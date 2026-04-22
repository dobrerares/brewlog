# BrewLog Backend Stack Evaluation

The BrewLog assignment requires a REST API that implements CRUD + statistics
endpoints, strict server-side validation, server-side pagination, high test
coverage, and an in-memory store (no persistence). For the Silver challenge
the same stack must also support asynchronous background tasks (Faker loops)
and WebSocket push; for Gold, a GraphQL layer over the same logic.

The criteria below were chosen to reflect those requirements directly, rather
than generic popularity metrics.

## 1. Candidates

Six free, open-source frameworks spanning the main ecosystems used for
academic and industry REST backends:

| # | Framework | Language | Paradigm |
|---|-----------|----------|----------|
| 1 | **FastAPI** | Python 3.11+ | Async ASGI, type-hint driven |
| 2 | **Flask + Flask-RESTful** | Python 3 | Sync WSGI, decorator routes |
| 3 | **Express.js** | Node.js / JS | Sync middleware pipeline |
| 4 | **Fastify** | Node.js / TS | Async, JSON-schema validation |
| 5 | **NestJS** | TypeScript | Opinionated DI, decorators |
| 6 | **Spring Boot** | Java 17+ | Annotation-driven, JVM |

## 2. Criteria

Scored 1 (poor) to 5 (excellent). Weightings are uniform — each criterion
reflects a hard requirement or a direct Silver/Gold deliverable.

| # | Criterion | Why it matters for BrewLog |
|---|-----------|----------------------------|
| C1 | **Validation ergonomics** | Bronze requires thorough server-side validation. A framework with first-class schema validation lets us declare constraints (ranges, enums, cross-field) once and reuse them for OpenAPI docs. |
| C2 | **Endpoint separation** | Bronze mandates separating endpoints from the rest of the implementation. Frameworks with routers/controllers enforce this naturally. |
| C3 | **Testing infrastructure** | Bronze requires maximum achievable coverage. Built-in test clients and parametrised test support shorten the feedback loop. |
| C4 | **OpenAPI / docs** | Not strictly required, but auto-generated Swagger UI makes manual grading and frontend integration trivial. |
| C5 | **Async + WebSocket support** | Silver requires async Faker loops + WebSocket push. Sync frameworks need extra machinery. |
| C6 | **GraphQL story** | Gold requires re-exposing the same logic through GraphQL. Strawberry/Ariadne/Apollo/type-graphql maturity matters. |
| C7 | **Learning curve / boilerplate** | One-week deadline. Less boilerplate = faster delivery. |
| C8 | **Community & docs** | Stack Overflow, blog posts, Faker/WebSocket examples for the chosen stack. |

## 3. Benchmark Table

| Criterion (1–5)           | FastAPI | Flask | Express | Fastify | NestJS | Spring Boot |
|---------------------------|:-------:|:-----:|:-------:|:-------:|:------:|:-----------:|
| C1 Validation ergonomics  | **5**   | 2     | 2       | 4       | 4      | 4           |
| C2 Endpoint separation    | 5       | 3     | 3       | 4       | **5**  | 5           |
| C3 Testing infrastructure | **5**   | 4     | 3       | 4       | 4      | 5           |
| C4 OpenAPI / docs         | **5**   | 2     | 2       | 4       | 4      | 4           |
| C5 Async + WebSocket      | **5**   | 2     | 4       | 4       | 4      | 4           |
| C6 GraphQL story          | 4       | 3     | **5**   | 3       | **5**  | 3           |
| C7 Learning curve         | **5**   | 5     | 4       | 4       | 2      | 1           |
| C8 Community & docs       | 5       | **5** | **5**   | 4       | 4      | **5**       |
| **TOTAL (out of 40)**     | **39**  | 26    | 28      | 31      | 32     | 31          |

## 4. Per-Framework Notes

- **FastAPI** — Pydantic v2 gives declarative field validation (`Field(ge=1, le=5)`,
  enums, `model_validator` for cross-field). Returns RFC-7807-ish 422 errors
  automatically. `TestClient` wraps Starlette with a requests-compatible API.
  Built-in OpenAPI + Swagger at `/docs`. Native `async def` and `WebSocket`
  support. Strawberry integrates cleanly for the Gold GraphQL task.
- **Flask** — Minimal and familiar, but validation is a bolt-on (Marshmallow,
  Pydantic, webargs). No built-in OpenAPI. Async support is partial via
  `async def` view funcs but WSGI means true concurrency needs extra setup.
- **Express.js** — Most tutorials on the internet, but validation is entirely
  manual (`express-validator`, `joi`, or `zod`). No typing story unless you
  add TypeScript yourself. Boilerplate for OpenAPI generation.
- **Fastify** — JSON Schema validation is first-class and very fast. TypeScript
  support via `@fastify/type-provider-typebox` is good. WebSocket plugin is
  official. Smaller ecosystem than Express and Pydantic is still a sharper
  validation tool than JSON Schema for cross-field rules.
- **NestJS** — Excellent DI-based separation (controllers/services/modules) and
  decorator validation via `class-validator`. Cost: heavy boilerplate and a
  steep ramp on decorators, DI scopes, modules. Overkill for a week-long
  in-memory assignment.
- **Spring Boot** — Industrial-grade, superb tooling, but JVM startup cost and
  annotation boilerplate are excessive for this scope; the Bronze-level "no
  persistence" constraint makes half of Spring's value (JPA, repositories,
  transactions) irrelevant.

## 5. Justification — FastAPI Wins (39/40)

Applying logical assertions to the table:

1. **C1 + C4 dominate Bronze.** BrewLog validation rules are cross-field
   (dose/water ratio 10–20×, method-specific temperature bands, rating < 3
   requires notes). Pydantic v2's `@model_validator(mode="after")` expresses
   those in a few lines and reuses them in the OpenAPI schema. No competitor
   scores 5 on both — Flask/Express drop to 2, Spring/Nest to 4 (extra
   annotation plumbing).
2. **C5 covers Silver without a rewrite.** Starlette's `asyncio.create_task`
   drives the Faker generator loop; `WebSocket` broadcasts batches. Flask and
   Express need `gevent`/`ws` shims that add friction.
3. **C3 lets us hit the coverage target.** `TestClient` gives synchronous,
   in-process HTTP access, so unit-testing endpoints needs no running server.
   `pytest-cov` reports per-file coverage out of the box.
4. **C7 is decisive under a one-week deadline.** NestJS and Spring Boot match
   FastAPI on separation (C2) but cost 2–3× the lines for the same endpoints.
   A simpler codebase is a more testable codebase.
5. **C6 is adequate for Gold.** Strawberry/GraphQL wraps the same Pydantic
   models and in-memory services. Apollo/Nest score higher, but only by one
   point — not enough to outweigh FastAPI's C1/C4/C5 lead.

Runner-up is **NestJS (32)**; it would be the pick if the team were already a
TypeScript shop and validation rules were simpler. **Fastify (31)** is the
best Node-only option if sharing types with the React/TypeScript frontend
were a stronger constraint than validation expressiveness.

## 6. Decision

**FastAPI 0.115 + Pydantic 2.9 + pytest 8 + httpx TestClient**, running on
Uvicorn. In-memory stores live in `backend/app/services/`, Pydantic schemas
in `backend/app/schemas/`, routers in `backend/app/api/`. Tests live in
`backend/tests/` and target ≥ 90 % line coverage for the CRUD code paths.

## 7. Validation — Silver & Gold Confirmed the Choice

The hypothesis in §5 was that FastAPI's C1/C3/C4/C5/C6 lead would carry
through into the Silver and Gold deliverables. Implementation confirmed it:

- **Silver (Faker loop + WebSocket)** — the async producer is ~90 lines in
  `app/services/generator.py` and hooks straight into Starlette's `WebSocket`
  primitive via `ConnectionManager` (~40 lines). Pydantic's `BrewLogCreate`
  validates every generated entity, so the loop can't emit invalid data. On
  Express we would have needed `ws` + a separate JSON-schema validator; on
  Flask we would have rewritten the loop on `gevent`.
- **Gold (GraphQL)** — Strawberry consumed the existing Pydantic models with
  zero changes. Mutations convert the Strawberry `@input` into the existing
  `BrewLogCreate` / `BrewLogUpdate` and surface `ValidationError.errors()`
  as GraphQL errors; 1-to-many relationships are plain resolvers over the
  same `InMemoryStore` instances the REST endpoints already use.
- **Testing** — `TestClient.websocket_connect` and httpx `AsyncClient` over
  ASGI cover async and WebSocket paths without spinning up a real server.
  Final status: **129 tests, 95.7 % line + branch coverage.**

A like-for-like NestJS implementation would have required type-graphql plus
`class-validator` DTO duplication for both mutations and controllers; on
Express we would have maintained three validation definitions (HTTP,
WebSocket payloads, GraphQL inputs). FastAPI's single-source validation
story is what actually kept the code small.
