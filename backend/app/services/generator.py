"""Async Faker loop that produces valid BrewLog batches.

The loop:
  1. On start, seeds one roaster / bean / brewer / grinder if the stores are
     empty so that FK constraints can be satisfied.
  2. Repeatedly waits `interval_s` seconds and emits a batch of `batch_size`
     freshly-generated BrewLogs.
  3. After every batch, broadcasts a `{"type": "brewlog.batch", ...}` envelope
     through the shared `ConnectionManager`.

All generated entities go through Pydantic, so they obey the same server-side
validation rules as payloads arriving via REST.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from faker import Faker

from app.schemas import (
    Bean,
    BeanCreate,
    BrewLog,
    BrewLogCreate,
    Equipment,
    EquipmentCreate,
    Roaster,
    RoasterCreate,
)
from app.schemas.common import (
    BrewMethod,
    EquipmentType,
    GrindType,
    Process,
    RoastLevel,
    TasteResult,
)

from .broadcast import ConnectionManager
from .store import InMemoryStore

if TYPE_CHECKING:
    from .state import AppState


_SAFE_RATIOS: dict[BrewMethod, tuple[Decimal, Decimal]] = {
    # method → (dose_g, water_g) that always sits inside the validator bands
    BrewMethod.V60: (Decimal("15"), Decimal("250")),
    BrewMethod.CHEMEX: (Decimal("30"), Decimal("500")),
    BrewMethod.FRENCH_PRESS: (Decimal("32"), Decimal("520")),
    BrewMethod.AEROPRESS: (Decimal("16"), Decimal("240")),
    BrewMethod.MOKA_POT: (Decimal("18"), Decimal("180")),
    BrewMethod.ESPRESSO: (Decimal("18"), Decimal("36")),
    BrewMethod.COLD_BREW: (Decimal("60"), Decimal("1000")),
    BrewMethod.OTHER: (Decimal("15"), Decimal("250")),
}

_TEMP_PICK: dict[BrewMethod, int] = {
    BrewMethod.V60: 94,
    BrewMethod.CHEMEX: 94,
    BrewMethod.FRENCH_PRESS: 94,
    BrewMethod.AEROPRESS: 88,
    BrewMethod.MOKA_POT: 95,
    BrewMethod.ESPRESSO: 93,
    BrewMethod.COLD_BREW: 20,
    BrewMethod.OTHER: 94,
}


class BrewLogGenerator:
    """Thin controller over the async task driving the Faker loop."""

    def __init__(
        self,
        state: "AppState",
        broadcaster: ConnectionManager,
        *,
        seed: int | None = 42,
    ) -> None:
        self._state = state
        self._broadcaster = broadcaster
        self._faker = Faker()
        self._random = random.Random(seed)
        self._task: asyncio.Task[None] | None = None
        self._batches_emitted = 0
        self._items_emitted = 0
        self._interval_s: float = 1.0
        self._batch_size: int = 3

    # --- introspection ----------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def status(self) -> dict[str, object]:
        return {
            "running": self.is_running,
            "batches_emitted": self._batches_emitted,
            "items_emitted": self._items_emitted,
            "batch_size": self._batch_size,
            "interval_s": self._interval_s,
        }

    # --- lifecycle --------------------------------------------------------

    async def start(self, batch_size: int, interval_s: float) -> None:
        if self.is_running:
            return
        self._batch_size = batch_size
        self._interval_s = interval_s
        self._seed_prereqs_if_needed()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def emit_once(self) -> list[BrewLog]:
        """Produce and broadcast a single batch synchronously.

        Exposed so tests can drive the generator deterministically without
        racing against `asyncio.sleep`.
        """
        self._seed_prereqs_if_needed()
        return await self._emit_batch()

    # --- internals --------------------------------------------------------

    async def _run(self) -> None:
        try:
            while True:
                await self._emit_batch()
                await asyncio.sleep(self._interval_s)
        except asyncio.CancelledError:
            raise

    async def _emit_batch(self) -> list[BrewLog]:
        produced = [self._make_brewlog() for _ in range(self._batch_size)]
        for brew in produced:
            self._state.brewlogs.insert(brew)
        self._batches_emitted += 1
        self._items_emitted += len(produced)
        await self._broadcaster.broadcast(
            {
                "type": "brewlog.batch",
                "count": len(produced),
                "items": [b.model_dump(mode="json") for b in produced],
            }
        )
        return produced

    # --- prerequisites ----------------------------------------------------

    def _seed_prereqs_if_needed(self) -> None:
        if self._state.roasters.count() == 0:
            roaster_payload = RoasterCreate(
                name=self._faker.company() + " Coffee",
                location=self._faker.city(),
                website=None,
                notes=None,
            )
            self._state.roasters.create(**roaster_payload.model_dump())

        if self._state.beans.count() == 0:
            roaster_id = self._state.roasters.list()[0].id
            bean_payload = BeanCreate(
                name=f"{self._faker.city()} Lot {self._random.randint(1, 99)}",
                roaster_id=roaster_id,
                origin_country=self._faker.country(),
                origin_region=None,
                process=self._random.choice(list(Process)),
                roast_level=self._random.choice(list(RoastLevel)),
                variety=None,
                elevation_m=self._random.randint(800, 2200),
                tasting_notes=self._random.sample(
                    ["chocolate", "citrus", "berry", "floral", "honey", "nutty"],
                    k=3,
                ),
                purchase_date=None,
                price=None,
            )
            self._state.beans.create(**bean_payload.model_dump())

        has_brewer = any(
            e.type == EquipmentType.BREWER for e in self._state.equipment.list()
        )
        has_grinder = any(
            e.type == EquipmentType.GRINDER for e in self._state.equipment.list()
        )
        if not has_brewer:
            brewer = EquipmentCreate(
                name="Hario V60",
                type=EquipmentType.BREWER,
                brand="Hario",
                model="02",
                grind_type=None,
                grind_range=None,
                grind_unit=None,
                notes=None,
            )
            self._state.equipment.create(**brewer.model_dump())
        if not has_grinder:
            grinder = EquipmentCreate(
                name="Comandante C40",
                type=EquipmentType.GRINDER,
                brand="Comandante",
                model="MK4",
                grind_type=GrindType.STEPPED,
                grind_range="clicks 0-40",
                grind_unit="1 click",
                notes=None,
            )
            self._state.equipment.create(**grinder.model_dump())

    def _make_brewlog(self) -> BrewLog:
        bean = self._random.choice(self._state.beans.list())
        brewers = [
            e for e in self._state.equipment.list() if e.type == EquipmentType.BREWER
        ]
        grinders = [
            e for e in self._state.equipment.list() if e.type == EquipmentType.GRINDER
        ]
        brewer = self._random.choice(brewers)
        grinder = self._random.choice(grinders)

        method = self._random.choice(
            [
                BrewMethod.V60,
                BrewMethod.CHEMEX,
                BrewMethod.FRENCH_PRESS,
                BrewMethod.AEROPRESS,
                BrewMethod.ESPRESSO,
            ]
        )
        dose, water = _SAFE_RATIOS[method]
        rating = self._random.randint(3, 5)  # avoid needing the low-rating notes path
        taste = self._random.choice(list(TasteResult))

        payload = BrewLogCreate(
            date=datetime.now(timezone.utc) - timedelta(minutes=self._random.randint(0, 600)),
            bean_id=bean.id,
            equipment_id=brewer.id,
            grinder_id=grinder.id,
            grind_setting=f"{self._random.randint(10, 32)} clicks",
            method=method,
            dose_g=dose,
            water_g=water,
            water_temp_c=_TEMP_PICK[method],
            brew_time_s=self._random.randint(90, 270),
            yield_g=Decimal("36") if method == BrewMethod.ESPRESSO else None,
            rating=rating,
            taste_result=taste,
            grind_adjustment=None,
            tasting_notes=[],
            notes=self._faker.sentence(nb_words=6),
            photo_url=None,
        )
        # build a concrete BrewLog with a generated id (same as the POST handler)
        from uuid import uuid4

        return BrewLog(id=uuid4(), **payload.model_dump())
