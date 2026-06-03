# Railway Deployment

Deploy this repo as separate Railway services from the same GitHub repository:

1. Add a PostgreSQL database service.
2. Add a MongoDB database service.
3. Add a backend service with root directory `backend`.
4. Add a frontend service with root directory `brewlog`.

## Backend variables

Set these on the backend service:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
MONGO_URL=${{MongoDB.MONGO_URL}}
MONGO_DB=brewlog_chat
SESSION_SECRET=<random-long-secret>
JWT_SECRET=<random-long-secret>
CORS_ORIGINS=https://<frontend-domain>
AUTH_COOKIE_SECURE=true
AUTH_COOKIE_SAMESITE=none
APP_BASE_URL=https://<frontend-domain>
ALLOW_DEV_MAGIC_LINK=false
ALLOW_DEV_TOTP_CODE=false
RESEND_API_KEY=<optional-resend-key>
RESEND_FROM_EMAIL=BrewLog <your-sender@example.com>
ADMIN_BOOTSTRAP_EMAIL=<admin-email>
ADMIN_BOOTSTRAP_PASSWORD=<strong-admin-password>
```

Use `AUTH_COOKIE_SAMESITE=lax` instead if the frontend and API are served from the same site behind a reverse proxy.

## Frontend variables

Set this on the frontend service before it builds:

```text
VITE_API_BASE=https://<backend-domain>
```

Leave `VITE_API_BASE` unset only when the frontend and API are served behind the same origin reverse proxy.

## Notes

- Railway injects `PORT`; both Dockerfiles now bind to that at runtime.
- The backend runs Alembic migrations and RBAC/chat seed scripts on startup.
- The backend health check is `/health`; the frontend health check is `/`.

## CLI-assisted setup

You can create the Railway services and set most variables with:

```powershell
.\scripts\railway-setup.ps1
```

After creating Railway public domains, run it again with domains and skip service creation:

```powershell
.\scripts\railway-setup.ps1 `
  -SkipCreateServices `
  -BackendDomain "https://<backend-domain>" `
  -FrontendDomain "https://<frontend-domain>"
```

Railway still needs these service source settings once per app:

- Backend root directory: `/backend`
- Backend config path: `/backend/railway.json`
- Frontend root directory: `/brewlog`
- Frontend config path: `/brewlog/railway.json`

The checked-in `railway.json` files define Dockerfile builds, health checks, restart policy, and monorepo watch paths.
