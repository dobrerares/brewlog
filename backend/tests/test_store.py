"""Unit tests for the generic in-memory store."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.schemas import Roaster
from app.services import InMemoryStore, NotFoundError


def _make() -> InMemoryStore[Roaster]:
    return InMemoryStore(Roaster)


def test_create_assigns_id_and_stores_entity() -> None:
    store = _make()
    roaster = store.create(name="A", location=None, website=None, notes=None)
    assert roaster.id is not None
    assert store.count() == 1
    assert store.get(roaster.id) == roaster


def test_get_raises_for_unknown_id() -> None:
    store = _make()
    with pytest.raises(NotFoundError):
        store.get(uuid4())


def test_replace_requires_existing_id() -> None:
    store = _make()
    phantom = Roaster(id=uuid4(), name="ghost", location=None, website=None, notes=None)
    with pytest.raises(NotFoundError):
        store.replace(phantom)


def test_replace_updates_existing_entity() -> None:
    store = _make()
    original = store.create(name="A", location=None, website=None, notes=None)
    updated = original.model_copy(update={"name": "B"})
    result = store.replace(updated)
    assert result.name == "B"
    assert store.get(original.id).name == "B"


def test_delete_raises_for_unknown_id() -> None:
    store = _make()
    with pytest.raises(NotFoundError):
        store.delete(uuid4())


def test_delete_removes_entity() -> None:
    store = _make()
    r = store.create(name="A", location=None, website=None, notes=None)
    store.delete(r.id)
    assert store.count() == 0
    assert not store.exists(r.id)


def test_insert_rejects_duplicate_id() -> None:
    store = _make()
    r = store.create(name="A", location=None, website=None, notes=None)
    with pytest.raises(ValueError):
        store.insert(r)


def test_bulk_insert_preserves_order() -> None:
    store = _make()
    entities = [
        Roaster(id=uuid4(), name=f"r{i}", location=None, website=None, notes=None)
        for i in range(5)
    ]
    store.bulk_insert(entities)
    assert [e.name for e in store.list()] == ["r0", "r1", "r2", "r3", "r4"]


def test_clear_empties_the_store() -> None:
    store = _make()
    store.create(name="A", location=None, website=None, notes=None)
    store.clear()
    assert store.count() == 0
