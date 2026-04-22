"""Application state — owns every in-memory store.

Using a single dataclass-style object makes it easy to inject a fresh instance
in tests and to reason about the app's lifecycle (no hidden globals).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import Bean, BrewLog, Equipment, Roaster

from .store import InMemoryStore


@dataclass
class AppState:
    brewlogs: InMemoryStore[BrewLog] = field(
        default_factory=lambda: InMemoryStore(BrewLog)
    )
    beans: InMemoryStore[Bean] = field(
        default_factory=lambda: InMemoryStore(Bean)
    )
    equipment: InMemoryStore[Equipment] = field(
        default_factory=lambda: InMemoryStore(Equipment)
    )
    roasters: InMemoryStore[Roaster] = field(
        default_factory=lambda: InMemoryStore(Roaster)
    )


_state = AppState()


def get_state() -> AppState:
    """FastAPI dependency returning the process-wide state."""
    return _state


def reset_state() -> AppState:
    """Replace the process-wide state with a fresh empty instance.

    Used by the test suite between cases to guarantee isolation.
    """
    global _state
    _state = AppState()
    return _state
