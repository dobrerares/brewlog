"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router, ws_router
from app.gql.schema import build_router as build_graphql_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="BrewLog API",
        description=(
            "In-memory REST + GraphQL backend for the BrewLog coffee journal. "
            "Bronze: REST CRUD / Silver: Faker loop + WebSocket / Gold: GraphQL."
        ),
        version="0.3.0",
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

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)
    app.include_router(ws_router)
    app.include_router(build_graphql_router(), prefix="/graphql")
    return app


app = create_app()
