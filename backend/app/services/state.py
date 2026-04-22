"""Application state — owns every in-memory store plus the Silver runtime.

Using a single dataclass-style object makes it easy to inject a fresh instance
in tests and to reason about the app's lifecycle (no hidden globals).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import Bean, BrewLog, Equipment, Roaster

from .broadcast import ConnectionManager
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
    broadcaster: ConnectionManager = field(default_factory=ConnectionManager)

    # Generator is attached lazily (see services/__init__.py) to avoid a
    # circular import between state ↔ generator.
    generator: object | None = None


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
    # re-attach a fresh generator bound to the new state
    from .generator import BrewLogGenerator

    _state.generator = BrewLogGenerator(_state, _state.broadcaster)
    return _state


# Bootstrap the generator for the initial state instance.
def _init_generator() -> None:
    from .generator import BrewLogGenerator

    if _state.generator is None:
        _state.generator = BrewLogGenerator(_state, _state.broadcaster)


_init_generator()
