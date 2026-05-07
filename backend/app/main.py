"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router, ws_router
from app.api import auth as auth_api
from app.db.base import dispose_engine, init_engine
from app.db.mongo import close_mongo, init_mongo
from app.gql.schema import build_router as build_graphql_router
from app.services.audit import AuditFailuresMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine()
    init_mongo()
    yield
    await dispose_engine()
    await close_mongo()


def create_app() -> FastAPI:
    app = FastAPI(
        title="BrewLog API",
        description=(
            "In-memory REST + GraphQL backend for the BrewLog coffee journal. "
            "Bronze: REST CRUD / Silver: Faker loop + WebSocket / Gold: GraphQL."
        ),
        version="0.3.0",
        lifespan=lifespan,
    )

    # Vite dev server runs on 5173; allow the React frontend to hit the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditFailuresMiddleware)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    app.include_router(ws_router)
    app.include_router(build_graphql_router(), prefix="/graphql")
    app.include_router(auth_api.router)
    return app


app = create_app()
