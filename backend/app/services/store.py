"""Generic in-memory repository.

No persistence — the dict below lives only for the lifetime of the process.
Matches the Bronze requirement: "the information will be stored solely in the
RAM of the server machine."
"""

from __future__ import annotations

import threading
from typing import Callable, Generic, Iterable, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel

EntityT = TypeVar("EntityT", bound=BaseModel)


class NotFoundError(LookupError):
    """Raised by the store when an id cannot be resolved."""


class InMemoryStore(Generic[EntityT]):
    """Thread-safe dict-backed store keyed by UUID.

    Ordering is preserved by insertion. Bulk readers return a snapshot so the
    caller can iterate without holding the lock.
    """

    def __init__(self, entity_factory: Callable[..., EntityT]) -> None:
        self._factory = entity_factory
        self._items: dict[UUID, EntityT] = {}
        self._lock = threading.RLock()

    # --- queries -----------------------------------------------------------

    def list(self) -> list[EntityT]:
        with self._lock:
            return list(self._items.values())

    def get(self, entity_id: UUID) -> EntityT:
        with self._lock:
            try:
                return self._items[entity_id]
            except KeyError as exc:
                raise NotFoundError(str(entity_id)) from exc

    def exists(self, entity_id: UUID) -> bool:
        with self._lock:
            return entity_id in self._items

    def count(self) -> int:
        with self._lock:
            return len(self._items)

    # --- mutations ---------------------------------------------------------

    def create(self, **fields: object) -> EntityT:
        entity_id = uuid4()
        entity = self._factory(id=entity_id, **fields)
        with self._lock:
            self._items[entity_id] = entity
        return entity

    def insert(self, entity: EntityT) -> EntityT:
        """Insert a fully-built entity (must already carry an id)."""
        entity_id: UUID = entity.id  # type: ignore[attr-defined]
        with self._lock:
            if entity_id in self._items:
                raise ValueError(f"duplicate id {entity_id}")
            self._items[entity_id] = entity
        return entity

    def replace(self, entity: EntityT) -> EntityT:
        entity_id: UUID = entity.id  # type: ignore[attr-defined]
        with self._lock:
            if entity_id not in self._items:
                raise NotFoundError(str(entity_id))
            self._items[entity_id] = entity
        return entity

    def delete(self, entity_id: UUID) -> None:
        with self._lock:
            if entity_id not in self._items:
                raise NotFoundError(str(entity_id))
            del self._items[entity_id]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def bulk_insert(self, entities: Iterable[EntityT]) -> None:
        with self._lock:
            for entity in entities:
                self._items[entity.id] = entity  # type: ignore[attr-defined]
