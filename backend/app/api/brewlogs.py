"""Brew-log endpoints — filtering + pagination + FK validation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import ValidationError

from app.pagination import Page, PageParams, page_params, paginate
from app.schemas import Bean, BrewLog, BrewLogCreate, BrewLogUpdate, Equipment
from app.schemas.common import BrewMethod, TasteResult
from app.services import InMemoryStore, NotFoundError

from .deps import bean_store, brewlog_store, equipment_store

router = APIRouter(prefix="/brewlogs", tags=["brewlogs"])


def _check_refs(
    bean_id: UUID,
    equipment_id: UUID,
    grinder_id: UUID,
    beans: InMemoryStore[Bean],
    equipment: InMemoryStore[Equipment],
) -> None:
    if not beans.exists(bean_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"bean_id {bean_id} does not exist"
        )
    if not equipment.exists(equipment_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"equipment_id {equipment_id} does not exist",
        )
    if not equipment.exists(grinder_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"grinder_id {grinder_id} does not exist",
        )


@router.get("", response_model=Page[BrewLog])
def list_brewlogs(
    params: PageParams = Depends(page_params),
    method: BrewMethod | None = Query(None, description="Filter by brew method"),
    taste_result: TasteResult | None = Query(None, description="Filter by taste"),
    bean_id: UUID | None = Query(None, description="Filter by bean"),
    min_rating: int | None = Query(None, ge=1, le=5),
    max_rating: int | None = Query(None, ge=1, le=5),
    date_from: datetime | None = Query(None, description="Inclusive lower bound"),
    date_to: datetime | None = Query(None, description="Inclusive upper bound"),
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
) -> Page[BrewLog]:
    items = store.list()
    if method is not None:
        items = [b for b in items if b.method == method]
    if taste_result is not None:
        items = [b for b in items if b.taste_result == taste_result]
    if bean_id is not None:
        items = [b for b in items if b.bean_id == bean_id]
    if min_rating is not None:
        items = [b for b in items if b.rating >= min_rating]
    if max_rating is not None:
        items = [b for b in items if b.rating <= max_rating]
    if date_from is not None:
        items = [b for b in items if b.date >= date_from]
    if date_to is not None:
        items = [b for b in items if b.date <= date_to]
    # newest first, stable
    items.sort(key=lambda b: b.date, reverse=True)
    return paginate(items, params)


@router.post("", response_model=BrewLog, status_code=status.HTTP_201_CREATED)
def create_brewlog(
    payload: BrewLogCreate,
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
    beans: InMemoryStore[Bean] = Depends(bean_store),
    equipment: InMemoryStore[Equipment] = Depends(equipment_store),
) -> BrewLog:
    _check_refs(payload.bean_id, payload.equipment_id, payload.grinder_id, beans, equipment)
    brewlog = BrewLog(id=uuid4(), **payload.model_dump())
    return store.insert(brewlog)


@router.get("/{brewlog_id}", response_model=BrewLog)
def get_brewlog(
    brewlog_id: UUID,
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
) -> BrewLog:
    try:
        return store.get(brewlog_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found") from exc


@router.patch("/{brewlog_id}", response_model=BrewLog)
def update_brewlog(
    brewlog_id: UUID,
    payload: BrewLogUpdate,
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
    beans: InMemoryStore[Bean] = Depends(bean_store),
    equipment: InMemoryStore[Equipment] = Depends(equipment_store),
) -> BrewLog:
    try:
        current = store.get(brewlog_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found") from exc

    updates = payload.model_dump(exclude_unset=True)
    merged_dict = {**current.model_dump(), **updates}

    if any(k in updates for k in ("bean_id", "equipment_id", "grinder_id")):
        _check_refs(
            merged_dict["bean_id"],
            merged_dict["equipment_id"],
            merged_dict["grinder_id"],
            beans,
            equipment,
        )

    try:
        merged = BrewLog.model_validate(merged_dict)
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc
    return store.replace(merged)


@router.delete(
    "/{brewlog_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_brewlog(
    brewlog_id: UUID,
    store: InMemoryStore[BrewLog] = Depends(brewlog_store),
) -> Response:
    try:
        store.delete(brewlog_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "brewlog not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
