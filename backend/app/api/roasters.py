"""Roaster endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.pagination import Page, PageParams, page_params, paginate
from app.schemas import Roaster, RoasterCreate, RoasterUpdate
from app.services import InMemoryStore, NotFoundError

from .deps import roaster_store

router = APIRouter(prefix="/roasters", tags=["roasters"])


@router.get("", response_model=Page[Roaster])
def list_roasters(
    params: PageParams = Depends(page_params),
    store: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Page[Roaster]:
    return paginate(store.list(), params)


@router.post("", response_model=Roaster, status_code=status.HTTP_201_CREATED)
def create_roaster(
    payload: RoasterCreate,
    store: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Roaster:
    roaster = Roaster(id=uuid4(), **payload.model_dump())
    return store.insert(roaster)


@router.get("/{roaster_id}", response_model=Roaster)
def get_roaster(
    roaster_id: UUID,
    store: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Roaster:
    try:
        return store.get(roaster_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "roaster not found") from exc


@router.patch("/{roaster_id}", response_model=Roaster)
def update_roaster(
    roaster_id: UUID,
    payload: RoasterUpdate,
    store: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Roaster:
    try:
        current = store.get(roaster_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "roaster not found") from exc
    merged = current.model_copy(update=payload.model_dump(exclude_unset=True))
    return store.replace(merged)


@router.delete(
    "/{roaster_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_roaster(
    roaster_id: UUID,
    store: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Response:
    try:
        store.delete(roaster_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "roaster not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
