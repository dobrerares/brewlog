"""Assemble the Strawberry schema and a FastAPI router for `/graphql`."""

from __future__ import annotations

from typing import Any

import strawberry
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.api.deps import get_db

from .mutations import Mutation
from .queries import Query

schema = strawberry.Schema(query=Query, mutation=Mutation)


def build_router() -> GraphQLRouter[Any, Any]:
    """Return a FastAPI-mountable GraphQL router that injects AsyncSession into context."""

    async def context_getter(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
        return {"db": db}

    return GraphQLRouter(schema, context_getter=context_getter)
