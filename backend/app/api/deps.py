"""FastAPI dependencies that resolve the app state and its sub-stores."""

from __future__ import annotations

from fastapi import Depends

from app.schemas import Bean, BrewLog, Equipment, Roaster
from app.services import AppState, InMemoryStore, get_state


def brewlog_store(state: AppState = Depends(get_state)) -> InMemoryStore[BrewLog]:
    return state.brewlogs


def bean_store(state: AppState = Depends(get_state)) -> InMemoryStore[Bean]:
    return state.beans


def equipment_store(state: AppState = Depends(get_state)) -> InMemoryStore[Equipment]:
    return state.equipment


def roaster_store(state: AppState = Depends(get_state)) -> InMemoryStore[Roaster]:
    return state.roasters
