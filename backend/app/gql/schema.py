"""Assemble the Strawberry schema and a FastAPI router for `/graphql`."""

from __future__ import annotations

from typing import Any

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.services import get_state

from .mutations import Mutation
from .queries import Query

schema = strawberry.Schema(query=Query, mutation=Mutation)


def build_router() -> GraphQLRouter[Any, Any]:
    """Return a FastAPI-mountable GraphQL router that injects AppState into context."""

    async def context_getter() -> dict[str, Any]:
        return {"state": get_state()}

    return GraphQLRouter(schema, context_getter=context_getter)
