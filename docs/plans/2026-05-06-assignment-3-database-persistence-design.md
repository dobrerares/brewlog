# BrewLog Assignment 3 — Database Persistence Design

**Goal:** Replace the in-memory store with a real relational database driven by ORM-generated migrations, add user/role/permission infrastructure with login, real-time NoSQL chat over WebSockets, and a Postgres-trigger-based audit + observation system. Targets all three challenge tiers (Bronze + Silver + Gold).

**Stack additions on top of A2:** PostgreSQL 16 + SQLAlchemy 2.x async + Alembic + asyncpg, MongoDB 7 + motor, passlib[bcrypt], testcontainers-python.

**Deployment:** Docker Compose (Postgres + Mongo + FastAPI). Same compose file deploys to Coolify; the frontend stays a separate Vite project run on a different machine — that satisfies the "client and server not on localhost" constraint.

---

## 1. Scope

| Tier | Deliverables |
|------|--------------|
| **Bronze** | Relational DB with all 4 entities. ORM-generated migrations (no hand-written DDL). Schema is in 3NF. CRUD + statistics + filters preserved. ~180 tests with ≥ 90 % coverage. Client and server demonstrably on different machines. |
| **Silver** | `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `sessions` tables (full RBAC). Login UI for admin and normal user with permission-gated routes. MongoDB-backed real-time chat between two logged-in users with WebSocket transport. |
| **Gold** | `audit_log` table capturing every authenticated action. Postgres trigger + stored procedure detects four malicious-behaviour patterns (failed-login burst, permission-denied burst, mass-mutation burst, mass-delete burst) and atomically flips a per-user `is_observed` flag. Admin observation dashboard with sparklines and a "Clear" action. |

---

## 2. Stack Decisions and Rationale

| Decision | Choice | Why |
|----------|--------|-----|
| RDBMS | PostgreSQL 16 | Real triggers + procedural language (PL/pgSQL). JSONB for `audit_log.metadata`. Partial indexes for the observed-users hot list. Easy to dockerize for the "different machine" demo. |
| ORM + migrations | SQLAlchemy 2.x async + Alembic | Pydantic stays as the validation tier; SQLAlchemy is a separate persistence tier. `alembic revision --autogenerate` diffs models against the live DB and writes migrations. Stored procs and triggers go in raw `op.execute(...)` blocks inside Alembic versions. |
| DB driver | asyncpg | Matches existing `async def` FastAPI handlers and the Faker generator loop. No thread bridge required. |
| NoSQL | MongoDB 7 + motor | Document model fits chat messages naturally. Aggregation pipelines for paginated history. Most canonical "NoSQL DB" answer for grading optics. |
| Test isolation | testcontainers-python (Postgres + Mongo per session) | Real Postgres in test means triggers + stored procs are exercised end-to-end. Per-test SAVEPOINT rollback for relational, per-test collection drop for chat. |
| Auth model | Full RBAC (5 tables + sessions) | Assignment names "USER, ROLES and PERMISSIONS" specifically. Granular permissions of shape `<resource>:<verb>:<scope>`. |
| Detection logic | Postgres `AFTER INSERT` trigger calling stored procedure | Atomic with the audit log insert. Demonstrates the assignment's explicit invitation to use stored procedures and triggers. Application code only reads the `is_observed` flag. |

---

## 3. Architecture Topology

```
┌─────────── Coolify host (or dev box) ─────────────┐
│                                                   │
│  ┌─────────────┐    ┌──────────┐  ┌──────────┐    │
│  │  FastAPI    │───▶│ Postgres │  │ MongoDB  │    │
│  │  (uvicorn)  │    │   16     │  │   7      │    │
│  │             │───▶│ entities │  │   chat   │    │
│  │  REST + WS  │    │ + RBAC   │  │          │    │
│  │  + GraphQL  │    │ + audit  │  │          │    │
│  └─────────────┘    └──────────┘  └──────────┘    │
│         ▲                                         │
└─────────┼─────────────────────────────────────────┘
          │  HTTPS + WSS, CORS allow-list
          ▼
   ┌──────────────┐
   │   Frontend   │   Vite dev or static build, on a different machine.
   │   (laptop)   │   Reads VITE_API_BASE from env.
   └──────────────┘
```

**Three Compose services:**
- `postgres` — `postgres:16-alpine`, named volume `pg_data`, healthcheck `pg_isready`.
- `mongo` — `mongo:7`, named volume `mongo_data`, healthcheck `mongosh ping`.
- `api` — built from `backend/Dockerfile`, depends on both with `condition: service_healthy`. Entrypoint runs `alembic upgrade head` then `uvicorn app.main:app`.

**Configuration via env:**

```
DATABASE_URL=postgresql+asyncpg://brewlog:<pw>@postgres:5432/brewlog
MONGO_URL=mongodb://mongo:27017/brewlog_chat
SESSION_SECRET=<random>
CORS_ORIGINS=http://localhost:5173,https://brewlog.example.com
SESSION_TTL_HOURS=24
```

The frontend is **not** in compose. It stays a separate Vite project; `VITE_API_BASE` points at the Coolify URL (or the dev box's LAN IP for a local demo). That's the "different machine" boundary.

---

## 4. Relational Schema (3NF)

### 4.1 Tables

```sql
-- ─── Auth (Silver) ────────────────────────────────────────────
users               (id PK, email UQ, password_hash, created_at,
                     is_observed BOOL DEFAULT false,
                     observed_reason TEXT NULL, observed_at TIMESTAMPTZ NULL)
roles               (id PK, name UQ)                       -- 'admin', 'user'
permissions         (id PK, code UQ, description)          -- 'brewlog:write:own', etc.
user_roles          (user_id FK, role_id FK)               -- composite PK
role_permissions    (role_id FK, permission_id FK)         -- composite PK
sessions            (id PK, user_id FK, created_at, expires_at, last_seen_at)

-- ─── Entities (Bronze) ────────────────────────────────────────
roasters            (id PK, user_id FK, name, location, website, notes, created_at)
beans               (id PK, user_id FK, roaster_id FK NULL, name, origin_country,
                     origin_region, process, roast_level, variety, elevation_m,
                     purchase_date, price, created_at)
equipment           (id PK, user_id FK, name, type, brand, model, grind_type,
                     grind_range, grind_unit, notes, created_at)
brewlogs            (id PK, user_id FK, bean_id FK, equipment_id FK, grinder_id FK,
                     date, grind_setting, method, dose_g, water_g, water_temp_c,
                     brew_time_s, yield_g, rating, taste_result,
                     grind_adjustment, notes, photo_url, created_at)

-- ─── Tasting notes (normalised out of the array columns) ──────
tasting_notes        (id PK, label UQ)                     -- catalog
bean_tasting_notes   (bean_id FK, tasting_note_id FK)      -- composite PK
brewlog_tasting_notes(brewlog_id FK, tasting_note_id FK)   -- composite PK

-- ─── Audit & detection (Gold) ─────────────────────────────────
audit_log            (id BIGSERIAL PK, user_id FK NULL, role_snapshot TEXT,
                      action TEXT, resource_type TEXT NULL, resource_id UUID NULL,
                      status TEXT, metadata JSONB, ip_address INET, created_at)
```

### 4.2 Foreign-key semantics

| Reference                                       | ON DELETE | Why                                                              |
|-------------------------------------------------|-----------|------------------------------------------------------------------|
| entities.user_id → users                        | RESTRICT  | Force admin to reassign/clear before deleting a user             |
| audit_log.user_id → users                       | SET NULL  | Preserve historical record even after user deletion              |
| user_roles, role_permissions                    | CASCADE   | Junction tables; meaningless without their parents               |
| sessions.user_id → users                        | CASCADE   | A user-less session is dead anyway                               |
| beans.roaster_id → roasters                     | SET NULL  | Beans survive a roaster deletion                                 |
| brewlogs.bean_id → beans                        | RESTRICT  | Don't lose history; explicit cleanup required                    |
| `bean_tasting_notes`, `brewlog_tasting_notes`   | CASCADE   | Junctions follow their owners                                    |

### 4.3 3NF analysis

**1NF.** Every column is atomic. The original `tasting_notes: list[str]` arrays from A0/A2 are normalised out into a catalog table (`tasting_notes`) with two M:N junctions. The only non-scalar column is `audit_log.metadata JSONB`, which is intentional — it holds variable-shape action context (request body excerpts, denied permission codes) where forcing a schema would create dozens of nullable columns.

**2NF.** Every non-key attribute fully depends on the entire PK. The composite-PK tables (`user_roles`, `role_permissions`, `bean_tasting_notes`, `brewlog_tasting_notes`) carry no non-key attributes, so 2NF is trivial. Single-column-PK tables get 2NF automatically.

**3NF.** No non-key column transitively depends on another non-key column. Two cases worth flagging:

- **`brewlogs` does not store `roaster_id`.** A naïve schema might denormalise `bean_name` and `bean_roaster_id` onto `brewlogs` "for performance"; that creates the chain `brewlogs.id → bean_id → bean_name` which is a textbook 3NF violation. We avoid it by storing only the FK to `beans` and walking through to the roaster at query time.
- **`audit_log.role_snapshot` is intentionally denormalised.** It records the user's role *at the time of the action*, not their current role. Joining `users → user_roles → roles` later would yield the present-time role, not the historical one. The snapshot describes the log row itself, not the user — this is a temporal-correctness denormalisation, not a 3NF violation.

### 4.4 Indexes

| Table        | Index                                                                          | Purpose                                          |
|--------------|--------------------------------------------------------------------------------|--------------------------------------------------|
| users        | `(email)` UQ                                                                   | Login lookup                                     |
| users        | `(id) WHERE is_observed = true` (partial)                                      | Admin observation list (small, hot)              |
| sessions     | `(id)`, `(user_id)`, `(expires_at)`                                            | Cookie validation, reaping                       |
| audit_log    | `(user_id, created_at DESC)`                                                   | Recent actions for a user                        |
| audit_log    | `(action, created_at DESC) WHERE status IN ('FAIL','DENIED')` (partial)        | Detection windows (failed-login, perm-denied)    |
| brewlogs     | `(user_id, date DESC)`                                                         | Paginated list — most common query               |
| brewlogs     | `(bean_id)`, `(equipment_id)`                                                  | FK lookups + 1-to-many walks                     |
| beans        | `(user_id, name)`, `(roaster_id)`                                              | Listing + roaster's beans                        |

---

## 5. NoSQL Schema (MongoDB)

### 5.1 Collections

```javascript
// chat_rooms
{
  _id: ObjectId,
  type: "dm" | "room",                       // 1:1 vs named
  participants: [<user_uuid>, ...],          // user UUIDs (string) from Postgres
  participant_pair: "<min_uuid>:<max_uuid>", // DM dedup key, set only when type="dm"
  name: string | null,                       // for type="room" (e.g. "lobby")
  created_at: ISODate,
  last_message_at: ISODate
}

// chat_messages
{
  _id: ObjectId,
  room_id: ObjectId,
  from_user_id: <user_uuid>,
  body: string,                              // ≤ 2000 chars (validated app-side)
  created_at: ISODate
}
```

Cross-engine references are by UUID string only — there are no FKs across engines. User identity is verified at the WebSocket boundary (cookie auth), and Mongo writes only what the app inserts.

### 5.2 Indexes

| Collection      | Index                                                                          | Purpose                              |
|-----------------|--------------------------------------------------------------------------------|--------------------------------------|
| chat_rooms      | `{ participant_pair: 1 }` UNIQUE, partial filter `{ type: "dm" }`              | Idempotent DM creation               |
| chat_rooms      | `{ participants: 1 }` (multikey)                                                | "List rooms I'm in"                  |
| chat_messages   | `{ room_id: 1, created_at: -1 }`                                                | Paginated history (newest first)     |

### 5.3 Bootstrap

Seed a single `chat_rooms` document of type `"room"`, name `"lobby"`, `participants: []`. Anyone authenticated can join the lobby; no DM dedup needed for it. DMs are created on demand: the first message from A to B does an upsert keyed on `participant_pair = sorted([A,B]).join(":")`.

### 5.4 WebSocket protocol

Topic-based fan-out. The existing `ConnectionManager` (used for the A2 brewlog broadcast) is generalised from a flat list of sockets to a `topic → set[WebSocket]` map.

```
Client ──▶ ws://api/ws  (cookie-authenticated)
       ◀── { type: "ready", user_id }
Client ──▶ { type: "join", room_id }
       ◀── { type: "history", room_id, messages: [...50] }   // initial history
Client ──▶ { type: "send", room_id, body }
       ◀── { type: "message", room_id, msg: {...} }          // to all subscribers
       ◀── { type: "brewlog_batch", items: [...] }           // unchanged from A2
```

History on join is delivered as one frame (last 50 messages); older history is fetched via REST `GET /chat/rooms/{id}/messages?before=<iso>&limit=50`.

---

## 6. Triggers, Stored Procedures, and Detection Mechanism

### 6.1 The procedure — `detect_malicious(p_user_id UUID)`

Runs four count-over-window queries against `audit_log`. If any threshold trips, flips the user's `is_observed` flag and writes a self-audit row.

```sql
CREATE OR REPLACE FUNCTION detect_malicious(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
  c_failed_login   INT;
  c_perm_denied    INT;
  c_mass_mutate    INT;
  c_mass_delete    INT;
  v_reason         TEXT := NULL;
BEGIN
  -- Don't re-observe an already-observed user; admin must explicitly clear.
  IF p_user_id IS NULL OR
     EXISTS (SELECT 1 FROM users WHERE id = p_user_id AND is_observed)
  THEN
    RETURN;
  END IF;

  -- Heuristic 1: failed-login burst (≥ 5 in 5 min)
  SELECT count(*) INTO c_failed_login FROM audit_log
   WHERE user_id = p_user_id AND action = 'LOGIN_FAIL'
     AND created_at > now() - interval '5 minutes';
  IF c_failed_login >= 5 THEN
    v_reason := format('failed-login-burst (%s in 5min)', c_failed_login);
  END IF;

  -- Heuristic 2: permission-denied burst (≥ 5 in 5 min)
  IF v_reason IS NULL THEN
    SELECT count(*) INTO c_perm_denied FROM audit_log
     WHERE user_id = p_user_id AND status = 'DENIED'
       AND created_at > now() - interval '5 minutes';
    IF c_perm_denied >= 5 THEN
      v_reason := format('permission-denied-burst (%s in 5min)', c_perm_denied);
    END IF;
  END IF;

  -- Heuristic 3: mass mutation burst (≥ 20 successful CREATE/UPDATE/DELETE in 60s)
  IF v_reason IS NULL THEN
    SELECT count(*) INTO c_mass_mutate FROM audit_log
     WHERE user_id = p_user_id AND status = 'OK'
       AND action ~ '_(CREATE|UPDATE|DELETE)$'
       AND created_at > now() - interval '60 seconds';
    IF c_mass_mutate >= 20 THEN
      v_reason := format('mass-mutation-burst (%s in 60s)', c_mass_mutate);
    END IF;
  END IF;

  -- Heuristic 4: mass-delete burst (≥ 10 successful DELETEs in 60s)
  IF v_reason IS NULL THEN
    SELECT count(*) INTO c_mass_delete FROM audit_log
     WHERE user_id = p_user_id AND status = 'OK'
       AND action LIKE '%_DELETE'
       AND created_at > now() - interval '60 seconds';
    IF c_mass_delete >= 10 THEN
      v_reason := format('mass-delete-burst (%s in 60s)', c_mass_delete);
    END IF;
  END IF;

  IF v_reason IS NOT NULL THEN
    UPDATE users SET is_observed = true,
                     observed_reason = v_reason,
                     observed_at = now()
    WHERE id = p_user_id;

    -- Self-audit; trigger ignores status='SYSTEM' to prevent recursion
    INSERT INTO audit_log(user_id, role_snapshot, action, status, metadata)
    VALUES (p_user_id, NULL, 'OBSERVED_AUTO', 'SYSTEM',
            jsonb_build_object('reason', v_reason));
  END IF;
END;
$$ LANGUAGE plpgsql;
```

### 6.2 The trigger

```sql
CREATE OR REPLACE FUNCTION audit_log_after_insert_fn()
RETURNS TRIGGER AS $$
BEGIN
  -- Skip system rows (the OBSERVED_AUTO insert from detect_malicious itself)
  IF NEW.status <> 'SYSTEM' AND NEW.user_id IS NOT NULL THEN
    PERFORM detect_malicious(NEW.user_id);
  END IF;
  RETURN NULL;  -- AFTER trigger; return value ignored
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_after_insert
AFTER INSERT ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_after_insert_fn();
```

The `status <> 'SYSTEM'` guard is what lets the procedure write its own audit row without firing itself again.

### 6.3 Why this lives in Postgres, not Python

- **Atomicity** — the audit insert and the observation flip are in the same transaction. Application-side detection means a crash between log-insert and threshold-check leaves an unobserved attacker.
- **Performance** — four count queries against indexed time windows on the same row's user, evaluated in microseconds; Python would need four round trips.
- **Grading optics** — the assignment explicitly mentions stored procedures and triggers. Putting the most distinctive Gold logic in the DB demonstrates that the database is *intelligent storage*, not a passive layer.

### 6.4 Admin observation API

```
GET  /api/v1/admin/observed-users           → 200 [{ id, email, observed_reason, observed_at, recent_actions }]
POST /api/v1/admin/observed-users/{id}/clear → 204
```

Both gated by `permission user:observe` (admin-only). Clearing writes an `OBSERVATION_CLEARED` audit row.

---

## 7. Application Layers and API Surface

### 7.1 Backend layout (delta from A2)

```
backend/app/
├── api/
│   ├── auth.py        ← NEW   POST /login, /logout, GET /me
│   ├── admin.py       ← NEW   observed users + audit log explorer
│   ├── chat.py        ← NEW   GET /chat/rooms, /messages (REST history)
│   ├── beans.py       ← MOD   user_id scope + permission gates
│   ├── brewlogs.py    ← MOD
│   ├── equipment.py   ← MOD
│   ├── roasters.py    ← MOD
│   ├── stats.py       ← MOD   scope to current_user
│   ├── generator.py   ← MOD   admin-only
│   ├── websocket.py   ← MOD   topic-based (chat rooms + brewlog feed)
│   └── deps.py        ← MOD   current_user, requires(*perms), audit
├── auth/
│   ├── passwords.py   ← NEW   passlib[bcrypt] hashing
│   ├── sessions.py    ← NEW   create/lookup/revoke session rows
│   └── permissions.py ← NEW   constants: PERM_BREWLOG_WRITE_OWN, etc.
├── db/
│   ├── base.py        ← NEW   AsyncEngine, AsyncSession factory, DeclarativeBase
│   ├── models.py      ← NEW   SQLAlchemy ORM classes (mirrors §4.1)
│   └── mongo.py       ← NEW   motor client + collection getters
├── repositories/
│   ├── base.py        ← NEW   generic repo: list/get/create/update/delete/scope_to_user
│   ├── {entity}.py    ← NEW   one per entity, plus users / sessions / audit_log
│   └── chat.py        ← NEW   Mongo-backed: rooms + messages
├── services/
│   ├── broadcast.py   ← MOD   topic-based (was global)
│   ├── chat.py        ← NEW   Mongo writes + broadcast
│   ├── audit.py       ← NEW   audit() helper
│   ├── generator.py   ← MOD   writes via repo, logs as admin action
│   └── store.py       ← DELETE
├── gql/               ← MOD   resolvers swap to repos; schema mostly unchanged
└── main.py            ← MOD   startup creates engines, shutdown disposes
alembic/
├── env.py             ← NEW   target_metadata = db.base.Base.metadata
└── versions/          ← NEW   migration files
```

### 7.2 Dependency injection (`deps.py` core)

```python
async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session

async def current_user(
    session_id: str | None = Cookie(default=None, alias="session_id"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """401 if cookie missing/expired/revoked. Returns user with roles eager-loaded."""

def requires(*perm_codes: str):
    """Dependency factory. 403 + audit('PERM_DENIED', 'DENIED') if any perm missing."""
    async def _check(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)) -> User:
        ...
    return _check

async def audit(action: str, status: str = "OK", **metadata) -> None:
    """Inserts an audit_log row. Called explicitly from mutating endpoints."""
```

A typical endpoint becomes:

```python
@router.post("/", response_model=BrewLog, status_code=201)
async def create_brewlog(
    payload: BrewLogCreate,
    user: User = Depends(requires(PERM_BREWLOG_CREATE)),
    repo: BrewLogRepository = Depends(get_brewlog_repo),
):
    brewlog = await repo.create(user_id=user.id, **payload.model_dump())
    await audit("BREWLOG_CREATE", resource_type="brewlog", resource_id=brewlog.id)
    return brewlog
```

### 7.3 Auditing strategy — split the load

| Source                          | Writes which audit rows                                                   |
|---------------------------------|---------------------------------------------------------------------------|
| Middleware (`AuditFailures`)    | `status='DENIED'` (403) and `status='FAIL'` (401, login fail). Catches the *bad* path automatically, including users who lack permission to even reach the endpoint body. |
| Endpoint code (`await audit(…)`)| `status='OK'` for mutations only. Reads are not audited (noise; the audit log is for actions, not browsing). |

Why split: middleware can't reliably name an action (`POST_/api/v1/brewlogs` is ugly and lossy), so semantic actions live in endpoint code. But endpoints never run if perms fail — so the middleware catches what the endpoint can't.

### 7.4 New REST endpoints

```
POST   /api/v1/auth/register        body: { email, password }     # creates user, assigns 'user' role
POST   /api/v1/auth/login           body: { email, password }     # sets session_id cookie
POST   /api/v1/auth/logout                                        # revokes session, clears cookie
GET    /api/v1/auth/me                                            # current user + roles + perms

GET    /api/v1/admin/observed-users                               # PERM user:observe
POST   /api/v1/admin/observed-users/{id}/clear                    # PERM user:observe
GET    /api/v1/admin/audit-log?user_id=&action=&since=&page=      # PERM log:read

GET    /api/v1/chat/rooms                                         # rooms current user is in
POST   /api/v1/chat/rooms                  body: { participant_id }   # upsert DM
GET    /api/v1/chat/rooms/{id}/messages?before=&limit=            # paginated history
```

Existing endpoints keep their paths; the change is a `Depends(requires(...))` and a `user_id=user.id` scope on every query.

### 7.5 GraphQL changes

Resolvers swap data source (in-memory → repository); entity schema unchanged. Two additions:

```graphql
type Query {
  me: User!
  observedUsers: [ObservedUser!]!   # admin-only; raises if not admin
}
type Mutation {
  login(email: String!, password: String!): User!
  logout: Boolean!
}
```

Permission errors become GraphQL errors with `extensions: { code: "FORBIDDEN" }`.

---

## 8. Frontend Changes

### 8.1 Auth wiring (replaces existing dummy)

A `useAuth()` hook fetches `/api/v1/auth/me` on mount; on 401 it redirects to `/login`. Returns `{ user, permissions, hasPermission, login, logout, register }`.

Two new pages plus two guards:

```
src/pages/Login.tsx              ← email + password → POST /auth/login → set cookie → redirect
src/pages/Register.tsx           ← creates a 'user' role account
src/components/RequireAuth.tsx   ← wraps protected routes; redirects to /login on 401
src/components/RequirePerm.tsx   ← wraps admin routes; renders 403 page if perm missing
```

The existing dummy `useCookie` hook stays as a thin wrapper but its `setUser` flow is retired in favour of `useAuth.login()`.

### 8.2 Chat UI

A single `/chat` route, two-column layout: rooms sidebar on the left (lobby + DMs + "New DM" button), message panel on the right with infinite-scroll history and an input box. State comes from three hooks:

- `useChatRooms()` — REST `GET /chat/rooms` once, then maintains in-memory list.
- `useChatRoom(roomId)` — REST `GET /chat/rooms/:id/messages` for history (initial + scroll-up paging), WebSocket subscribes to that room's topic via `{ type: "join", room_id }`.
- `useChatSocket()` — one shared WebSocket, multiplexed by `room_id` in the frame envelope. Survives navigation between rooms.

Out of scope: typing indicators, read receipts, presence list.

### 8.3 Admin pages

```
src/pages/admin/ObservedUsers.tsx     ← Gold demo
src/pages/admin/AuditLogExplorer.tsx  ← filterable log table
```

Each observed-users row shows email + reason + `observed_at`, plus a 50-bucket sparkline of the user's last hour of `audit_log` entries (one bar per minute, height = count). The Clear button posts to `/admin/observed-users/:id/clear`.

### 8.4 Navigation gating

The navbar reads `permissions` from `useAuth`:

```tsx
{hasPermission('user:observe') && <NavLink to="/admin/observed">Admin</NavLink>}
{user && <NavLink to="/chat">Chat</NavLink>}
```

Direct-URL access to admin routes by a non-admin renders the 403 page (clean, no crash). The server has already rejected the API call.

### 8.5 What stays unchanged

- The Live page, charts, infinite scroll, offline queue, Faker generator controls (Silver of A2). Generator start/stop becomes admin-only — non-admin sees the buttons disabled with a tooltip.
- The Original Assignment 1 UI (`/brews`, `/dashboard`, etc.) — still works in-memory, gated by `RequireAuth` so it isn't browsable when logged out.

---

## 9. Testing Strategy

Existing: 129 tests, 95.7 % coverage. Target after A3: ~180 tests, ≥ 90 % gate on new persistence + auth + audit + chat code.

### 9.1 Test infrastructure (`conftest.py` core)

```python
@pytest.fixture(scope="session")
def pg_container() -> PostgresContainer:
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url(driver="asyncpg")
        engine = create_async_engine(url)
        anyio.run(_alembic_upgrade, engine, "head")   # migrations once per session
        yield engine
        anyio.run(engine.dispose)

@pytest.fixture
async def db(pg_container) -> AsyncIterator[AsyncSession]:
    """Per-test SAVEPOINT that rolls back on teardown."""
    async with pg_container.connect() as conn:
        trans = await conn.begin()
        async with AsyncSession(bind=conn) as session:
            yield session
        await trans.rollback()

@pytest.fixture(scope="session")
def mongo_container() -> AsyncIOMotorDatabase:
    with MongoDbContainer("mongo:7") as mongo:
        client = AsyncIOMotorClient(mongo.get_connection_url())
        yield client["brewlog_test"]
        anyio.run(client.drop_database, "brewlog_test")
```

### 9.2 Test surface

| Layer                | Tests | Notes                                                                                |
|----------------------|-------|--------------------------------------------------------------------------------------|
| Migrations           | ~5    | `alembic upgrade head` round-trip, all 14 tables present, FKs declared, indexes present |
| Repositories         | ~30   | One per repo × CRUD + edge cases (NotFound, scoping, cascade behaviour)              |
| Detection trigger    | ~10   | Each heuristic isolated, already-observed-no-rerun, non-recursion guard, threshold-just-below |
| Auth                 | ~15   | Register: success / duplicate / weak-pw. Login: success / bad-pw / unknown-email. Session: expiry / revoke / cookie missing |
| Permissions          | ~12   | Each route × admin allowed / user denied → 403 → audit row check                     |
| Audit middleware     | ~5    | 401 → FAIL row, 403 → DENIED row, OK paths only emit explicit `audit()` rows         |
| Chat                 | ~12   | Room upsert idempotent, message persistence + ordering, WS fan-out, history paging   |
| GraphQL              | ~8    | Existing tests adapted to repos, plus new login/logout mutations                     |
| End-to-end smoke     | ~5    | Register → login → create-brew → mass-delete → observed → admin clears               |
| **Ported existing**  | ~80   | The 129 in-memory tests, mechanically rewritten to use `db` fixture                  |
| **Total**            | **~180** |                                                                                   |

### 9.3 Coverage gate

```toml
[tool.coverage.run]
omit = ["alembic/*", "*/conftest.py"]    # migrations are not unit-testable

[tool.coverage.report]
fail_under = 90
exclude_lines = ["pragma: no cover", "raise NotImplementedError"]
```

### 9.4 Tests notable enough to call out

- **Trigger non-recursion guard.** Insert an `OBSERVED_AUTO` row directly with `status='SYSTEM'`; assert no second row appears, no second `is_observed` flip.
- **Permission denied → audit row present.** A test that fails to assert this would let real abuse go un-logged.
- **3NF round-trip.** Insert a brewlog with two tasting notes that already exist on another brewlog → assert the catalog row is reused (no duplicate `tasting_notes` row, two new junction rows).
- **Cascade vs RESTRICT semantics.** Deleting a roaster nulls bean.roaster_id; deleting a user with brewlogs raises `IntegrityError`. Both are tested explicitly.

### 9.5 Frontend tests

Existing Vitest suite stays. New tests:
- `useAuth` (~6) — login success/fail, logout clears state, /me parsing
- `RequirePerm` (~3) — renders children with perm, renders 403 without
- Login + Register form validation (~4)
- Observed users page (~3) — renders list, sparkline, clear button POSTs

Existing Playwright e2e infra extends with one new flow: register → log brews → trigger mass-delete → admin sees observation.

---

## 10. Build Sequence (Schema-first)

The schema is the architectural anchor. Lock it first, then fill application code. Five phases:

**Phase 1 — Infra & schema (anchor).**
- `backend/Dockerfile`, `docker-compose.yml`, env scaffolding.
- `app/db/base.py`, `app/db/models.py`, `app/db/mongo.py`.
- Alembic init, single big migration generating all 14 PG tables + indexes + the detection function/trigger via `op.execute(...)`.
- Mongo bootstrap script that creates indexes and seeds the lobby room.
- Seed script for roles + permissions + an initial admin user.

**Phase 2 — Repository ports.**
- `repositories/base.py` + one repo per entity.
- Mechanical port of the 80 existing entity tests onto the `db` fixture.
- New repository tests (NotFound, user scoping, cascade behaviour).

**Phase 3 — Auth + permissions + audit.**
- `auth/passwords.py`, `auth/sessions.py`, `auth/permissions.py`.
- `api/auth.py` (register / login / logout / me).
- `api/deps.py` `current_user` + `requires(...)`.
- `services/audit.py` + middleware for DENIED / FAIL rows.
- All existing endpoints get the perm gate + `await audit(...)`.

**Phase 4 — Chat.**
- `app/db/mongo.py` collection getters.
- `repositories/chat.py` + `services/chat.py`.
- `api/chat.py` REST history.
- `api/websocket.py` topic-based fan-out (generalises the A2 broadcast).
- Frontend `/chat` route + `useChatSocket` / `useChatRoom`.

**Phase 5 — Gold dashboard + Polish.**
- `api/admin.py` (observed users + audit log explorer).
- Frontend `/admin/observed`, `/admin/audit`.
- Sparkline component.
- Final smoke tests and deploy to Coolify.
- Frontend dev server runs on a different machine for the demo.

The tiers map to phases: Bronze = phases 1–2, Silver = phases 3–4, Gold = phase 5.

---

## 11. Learning-Mode Contribution Checkpoints

Five spots in the implementation where the user owns ~5–15 lines of meaningful code:

1. **Permission catalog seeding** (Phase 1, ~10 lines) — the exact mapping of which permissions belong to `admin` vs `user`. The full catalog is seeded; the user decides which `:own` vs `:any` scope each role gets.
2. **Audit middleware filter list** (Phase 3, ~5 lines) — which routes are audit-exempt (`/health`, `/docs`, the websocket handshake). Scaffolded with `EXEMPT_PATHS` constant; user populates it.
3. **Detection thresholds** (Phase 1, ~10 lines pl/pgSQL) — the four threshold integers and the order of evaluation in `detect_malicious`. Tighter thresholds catch more abuse but generate false positives during legitimate Faker-generator demos; looser thresholds make the demo cleaner but miss real attacks. That trade-off is the user's.
4. **Detection trigger tests** (Phase 1, ~5 lines × 4) — parametrised tests for the four heuristic scenarios at the threshold boundary and threshold + 1 boundary. Forces reasoning about exactly what the trigger should do at the edges.
5. **Sparkline component** (Phase 5, ~15 lines TSX) — bucket size, scale (linear vs log), colour ramp by intensity, hover behaviour. Distinctive UX choice for the Gold demo.

---

## 12. Out of Scope (Explicit)

- **JWT, OAuth, refresh tokens.** Sessions are server-side rows; cookies hold only an opaque session id. The assignment defers full auth to the next.
- **Encrypted in-transit traffic** beyond what Coolify provides at the proxy. The assignment text explicitly says encryption is not required for A3.
- **Typing indicators, read receipts, presence in chat.** Out of scope for the Silver chat deliverable.
- **A backfill story for the existing in-memory data.** The store is retired; there is no production data to migrate. Demo data is generated via the existing Faker seed.
- **Multi-tenant data isolation beyond user_id.** Admin can read everything (Gold log explorer requires it). Stronger isolation (per-org workspaces) is a future concern.

---

## 13. Open Questions

None at the time of writing. All major decisions are recorded above. Threshold integers and audit-exempt route list are deliberate user contributions, not open questions.
