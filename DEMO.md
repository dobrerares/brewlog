# BrewLog — How to Run & Demo Everything

This is a walkthrough for demoing the project end-to-end. One terminal runs
the **backend** (FastAPI), another runs the **frontend** (Vite). From there,
every Bronze / Silver / Gold deliverable is reachable from the UI or a `curl`.

Repo layout that matters:

```
brewlog/
├── backend/                     # FastAPI + GraphQL + WebSocket (Python 3.11)
├── brewlog/                     # React + TypeScript + Vite frontend
├── BACKEND_EVALUATION.md        # framework benchmark + justification
└── A0.md                        # domain spec
```

---

## 1. First-time setup

Two independent projects — set up once, then just run them.

### 1.1 Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 1.2 Frontend

```bash
cd brewlog
npm install
```

> The frontend expects the backend at `http://localhost:8000`. Override via
> `VITE_API_BASE` env var if you run on a different port.

---

## 2. Running the app (two terminals)

### Terminal A — backend

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --port 8000
```

You should see Uvicorn listening on `:8000`. Three entry points to know:

| URL | What it is |
|-----|------------|
| http://localhost:8000/docs      | Swagger UI (REST) |
| http://localhost:8000/graphql   | GraphiQL playground (Gold) |
| ws://localhost:8000/ws          | WebSocket (Silver) |

### Terminal B — frontend

```bash
cd brewlog
npm run dev
```

Open http://localhost:5173. The app has two UIs:

| Route | What it shows |
|-------|---------------|
| `/brews`, `/dashboard`, etc. | Original in-memory Assignment 1 UI (standalone, no backend needed) |
| **`/live`** | New Assignment 2 page — consumes the backend. Silver + Gold live here |

Log in with any dummy credentials (auth is cookie-based) and click **Live** in the navbar.

---

## 3. Bronze demo

### 3.1 REST CRUD + validation + server-side pagination

Open http://localhost:8000/docs — Swagger lists every endpoint.

Try the mandatory flow from the CLI:

```bash
# 1. create a roaster
ROASTER=$(curl -s -X POST http://localhost:8000/api/v1/roasters \
  -H 'Content-Type: application/json' \
  -d '{"name":"Onyx","location":"Boston"}')
echo "$ROASTER" | python3 -m json.tool

# 2. create a bean linked to the roaster
BEAN_ID=$(echo "$ROASTER" | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
curl -s -X POST http://localhost:8000/api/v1/beans \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Finca La Esperanza\",\"roaster_id\":\"$BEAN_ID\",\"origin_country\":\"Colombia\",\"process\":\"Washed\",\"roast_level\":\"Light\"}"

# 3. paginated list
curl -s 'http://localhost:8000/api/v1/beans?page=1&page_size=5' | python3 -m json.tool

# 4. validation in action — ratio out of band (water/dose must be 10–20×)
curl -s -X POST http://localhost:8000/api/v1/brewlogs \
  -H 'Content-Type: application/json' \
  -d '{"date":"2026-04-01T08:00:00","bean_id":"00000000-0000-0000-0000-000000000000","equipment_id":"00000000-0000-0000-0000-000000000000","grinder_id":"00000000-0000-0000-0000-000000000000","grind_setting":"22","method":"V60","dose_g":"15","water_g":"100","water_temp_c":94,"brew_time_s":150,"rating":4}'
# → 422 with "water_g/dose_g ratio must be between 10 and 20"
```

Show the Swagger UI responses as proof of:
- 422 on bad input (validation)
- `{ items, total, page, page_size, total_pages }` envelope (pagination)
- Separate URL per resource (endpoint separation)

### 3.2 Tests & coverage

```bash
cd backend
.venv/bin/pytest
# 129 tests passing, 95.7% line + branch coverage, 90% gate enforced
```

Open `backend/htmlcov/index.html` in a browser to show the per-file coverage
report.

### 3.3 In-memory storage proof

Restart uvicorn (Ctrl-C in terminal A, rerun the command). Hit
`GET /api/v1/beans` again — the list is empty. No persistence.

---

## 4. Silver demo

### 4.1 Side-by-side live charts + WebSocket

With both servers running:

1. Navigate to http://localhost:5173/live in the browser.
2. Click **Start generator** (top-right of the Live page). This POSTs to
   `/api/v1/generator/start`; the backend starts emitting synthetic brewlogs
   every 2 s.
3. Watch the **method PieChart** and **rating BarChart** (side-by-side at the
   top) re-render as batches arrive. The master list below updates in the
   same render — every update is pushed via WebSocket, not polled.
4. Click the bean pills in the sidebar to filter — the charts re-derive from
   the filtered items in real time.
5. Click **Stop generator** to halt the loop.

Cross-check on the CLI:

```bash
curl -s http://localhost:8000/api/v1/generator/status | python3 -m json.tool
# { "running": true, "batches_emitted": 5, "items_emitted": 15, ... }
```

### 4.2 Offline detection + sync

With both servers running and the Live page open:

1. Chrome DevTools → Network tab → throttle to **Offline** (or run
   `pkill -f uvicorn` to kill the backend).
2. Within ~10 s, the connection pill flips from **Online** → **Offline**.
3. Click the trash icon next to any brew → it stays in the list locally and
   the banner shows **Offline — 1 pending**.
4. Click **Add brew for this bean** a couple of times → pending count goes up.
5. Re-enable the network (or restart uvicorn). The banner flips to
   **Syncing — N pending**, drains the queue, and lands back on **Online**.

Cross-check the queue in DevTools → Application → Local Storage:

```
brewlog_offline_queue → [{ kind: "delete-brewlog", ... }, ...]
```

### 4.3 WebSocket raw

If you want to show the raw frames:

```bash
# in another terminal
python3 -c "
import asyncio, json, websockets
async def main():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        while True:
            msg = json.loads(await ws.recv())
            print(msg['type'], msg['count'], msg['items'][0]['method'])
asyncio.run(main())
"
# then click Start generator in the UI — watch frames arrive
```

---

## 5. Gold demo

### 5.1 GraphQL at /graphql

Open http://localhost:8000/graphql (GraphiQL). Paste and run:

```graphql
{
  brewStats {
    totalBrews
    averageRating
    mostUsedMethod
    byMethod { method count }
  }
  roasters {
    total
    items {
      id
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
}
```

This single query walks **roaster → beans → brewlogs** — that is the Gold
1-to-many walked end-to-end on the server side.

Show a mutation too:

```graphql
mutation {
  createRoaster(input: { name: "Prodigal", location: "Waco" }) {
    id
    name
  }
}
```

Validation errors surface as standard GraphQL errors:

```graphql
mutation {
  createRoaster(input: { name: "" }) { id }
}
# → errors: [{ message: "name: String should have at least 1 character" }]
```

### 5.2 Infinite scroll with prefetching

On the Live page:

1. Start the generator (Silver) and let it produce ~60 brewlogs so there are
   at least 3 pages of 20.
2. Stop the generator, then refresh.
3. Open DevTools → Network → filter on `brewlogs`.
4. On first paint you will see **two** requests: `?page=1` and `?page=2`.
   That second one is the prefetch — page 2 is already cached before the
   user scrolls.
5. Scroll down to the sentinel — page 2 is served from cache (no network),
   and the hook immediately fires page 3 as the new prefetch.

This is the "minimum network usage" behaviour the spec asks for.

### 5.3 1-to-many with full CRUD + statistics (frontend)

Still on the Live page, pick a bean from the sidebar:

- **Read** — the master list re-queries with `bean_id=...` (REST) and the
  sidebar shows **1-to-many stats**: count, average rating, method breakdown.
  The two top charts also filter to this bean.
- **Create** — click **Add brew for this bean**. A brewlog is POSTed with a
  valid default recipe, associated with the selected bean. Works offline
  too (queued + synced).
- **Update** — click any brew → opens `BrewDetail` / `BrewForm` in the
  existing Assignment 1 UI for full editing.
- **Delete** — trash icon next to each brew. Also queued offline.

And the server-side statistics:

```bash
curl -s http://localhost:8000/api/v1/stats/brewlogs | python3 -m json.tool
```

---

## 6. Running the test suites (for grading)

```bash
# backend — 129 tests, 95.7% coverage, 90% gate enforced
cd backend
.venv/bin/pytest

# frontend — 94 tests (unit), typecheck, build
cd ../brewlog
npm run test -- --run
npx tsc -b
npm run build
```

---

## 7. One-page proof matrix

| Challenge | Requirement | Where to show it |
|-----------|-------------|------------------|
| Bronze | REST CRUD + validation + pagination + no persistence + tests | `http://localhost:8000/docs` + `pytest` |
| Silver | Offline detection + local queue + sync on reconnect | Live page + DevTools → throttle offline, re-enable |
| Silver | Start/stop Faker loop endpoints | `POST /api/v1/generator/{start,stop}` (Swagger or Live page button) |
| Silver | WebSocket pushes batches | Live page charts + list update on each batch |
| Silver | Side-by-side charts update live | PieChart + BarChart at top of Live page |
| Gold   | Reimplement as GraphQL | `http://localhost:8000/graphql` |
| Gold   | Infinite scroll + prefetching | Live page + Network tab shows `?page=1`+`?page=2` on first load |
| Gold   | 1-to-many full-stack CRUD + stats | Bean sidebar on Live page (filter / add / delete / stats) |
