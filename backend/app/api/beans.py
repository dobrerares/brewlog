"""Coffee-bean endpoints."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import ValidationError

from app.pagination import Page, PageParams, page_params, paginate
from app.schemas import Bean, BeanCreate, BeanUpdate, Roaster
from app.services import InMemoryStore, NotFoundError

from .deps import bean_store, roaster_store

router = APIRouter(prefix="/beans", tags=["beans"])


def _ensure_roaster(roaster_id: UUID | None, store: InMemoryStore[Roaster]) -> None:
    if roaster_id is None:
        return
    if not store.exists(roaster_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"roaster_id {roaster_id} does not exist",
        )


@router.get("", response_model=Page[Bean])
def list_beans(
    params: PageParams = Depends(page_params),
    store: InMemoryStore[Bean] = Depends(bean_store),
) -> Page[Bean]:
    return paginate(store.list(), params)


@router.post("", response_model=Bean, status_code=status.HTTP_201_CREATED)
def create_bean(
    payload: BeanCreate,
    store: InMemoryStore[Bean] = Depends(bean_store),
    roasters: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Bean:
    _ensure_roaster(payload.roaster_id, roasters)
    bean = Bean(id=uuid4(), **payload.model_dump())
    return store.insert(bean)


@router.get("/{bean_id}", response_model=Bean)
def get_bean(
    bean_id: UUID,
    store: InMemoryStore[Bean] = Depends(bean_store),
) -> Bean:
    try:
        return store.get(bean_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bean not found") from exc


@router.patch("/{bean_id}", response_model=Bean)
def update_bean(
    bean_id: UUID,
    payload: BeanUpdate,
    store: InMemoryStore[Bean] = Depends(bean_store),
    roasters: InMemoryStore[Roaster] = Depends(roaster_store),
) -> Bean:
    try:
        current = store.get(bean_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bean not found") from exc

    updates = payload.model_dump(exclude_unset=True)
    if "roaster_id" in updates:
        _ensure_roaster(updates["roaster_id"], roasters)

    # Re-run full-model validation after merging partial fields.
    try:
        merged = Bean.model_validate({**current.model_dump(), **updates})
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            exc.errors(include_url=False, include_input=False, include_context=False),
        ) from exc
    return store.replace(merged)


@router.delete(
    "/{bean_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_bean(
    bean_id: UUID,
    store: InMemoryStore[Bean] = Depends(bean_store),
) -> Response:
    try:
        store.delete(bean_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "bean not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
