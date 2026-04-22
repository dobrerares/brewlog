"""Equipment endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError

from app.pagination import Page, PageParams, page_params, paginate
from app.schemas import Equipment, EquipmentCreate, EquipmentUpdate
from app.services import InMemoryStore, NotFoundError

from .deps import equipment_store

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=Page[Equipment])
def list_equipment(
    params: PageParams = Depends(page_params),
    store: InMemoryStore[Equipment] = Depends(equipment_store),
) -> Page[Equipment]:
    return paginate(store.list(), params)


@router.post("", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(
    payload: EquipmentCreate,
    store: InMemoryStore[Equipment] = Depends(equipment_store),
) -> Equipment:
    equipment = Equipment(id=uuid4(), **payload.model_dump())
    return store.insert(equipment)


@router.get("/{equipment_id}", response_model=Equipment)
def get_equipment(
    equipment_id: UUID,
    store: InMemoryStore[Equipment] = Depends(equipment_store),
) -> Equipment:
    try:
        return store.get(equipment_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "equipment not found") from exc


@router.patch("/{equipment_id}", response_model=Equipment)
def update_equipment(
    equipment_id: UUID,
    payload: EquipmentUpdate,
    store: InMemoryStore[Equipment] = Depends(equipment_store),
) -> Equipment:
    try:
        current = store.get(equipment_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "equipment not found") from exc

    updates = payload.model_dump(exclude_unset=True)
    try:
        merged = Equipment.model_validate({**current.model_dump(), **updates})
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc
    return store.replace(merged)


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_equipment(
    equipment_id: UUID,
    store: InMemoryStore[Equipment] = Depends(equipment_store),
) -> Response:
    try:
        store.delete(equipment_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "equipment not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
