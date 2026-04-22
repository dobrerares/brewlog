"""GraphQL write-side — reuses Pydantic Create/Update models for validation.

Every resolver converts the Strawberry input → Pydantic model; validation
errors bubble up as standard GraphQL errors with the Pydantic message list.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import strawberry
from pydantic import ValidationError

from app.schemas import (
    Bean as BeanModel,
)
from app.schemas import (
    BeanCreate,
    BeanUpdate,
    BrewLogCreate,
    BrewLogUpdate,
    EquipmentCreate,
    EquipmentUpdate,
    RoasterCreate,
    RoasterUpdate,
)
from app.schemas import (
    BrewLog as BrewLogModel,
)
from app.schemas import (
    Equipment as EquipmentModel,
)
from app.schemas import (
    Roaster as RoasterModel,
)
from app.services import AppState

from .types import (
    Bean,
    BeanInput,
    BeanPatch,
    BrewLog,
    BrewLogInput,
    BrewLogPatch,
    Equipment,
    EquipmentInput,
    EquipmentPatch,
    Roaster,
    RoasterInput,
    RoasterPatch,
    decimal_or_none,
    strip_unset,
)


def _state(info: strawberry.Info) -> AppState:
    return info.context["state"]


def _wrap_validation(exc: ValidationError) -> ValueError:
    # Keep the error short and JSON-safe; GraphQL will format it.
    msgs = [
        f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
        for err in exc.errors(include_url=False, include_input=False, include_context=False)
    ]
    return ValueError("; ".join(msgs))


def _check_roaster(state: AppState, roaster_id: UUID | None) -> None:
    if roaster_id is not None and not state.roasters.exists(roaster_id):
        raise ValueError(f"roaster_id {roaster_id} does not exist")


def _check_brewlog_refs(
    state: AppState, bean_id: UUID, equipment_id: UUID, grinder_id: UUID
) -> None:
    if not state.beans.exists(bean_id):
        raise ValueError(f"bean_id {bean_id} does not exist")
    if not state.equipment.exists(equipment_id):
        raise ValueError(f"equipment_id {equipment_id} does not exist")
    if not state.equipment.exists(grinder_id):
        raise ValueError(f"grinder_id {grinder_id} does not exist")


@strawberry.type
class Mutation:
    # --- roaster --------------------------------------------------------

    @strawberry.mutation
    def create_roaster(self, info: strawberry.Info, input: RoasterInput) -> Roaster:
        state = _state(info)
        try:
            payload = RoasterCreate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        model = RoasterModel(id=uuid4(), **payload.model_dump())
        return Roaster.from_model(state.roasters.insert(model))

    @strawberry.mutation
    def update_roaster(
        self, info: strawberry.Info, id: UUID, input: RoasterPatch
    ) -> Roaster:
        state = _state(info)
        try:
            current = state.roasters.get(id)
        except LookupError as exc:
            raise ValueError("roaster not found") from exc
        try:
            patch = RoasterUpdate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        merged = current.model_copy(update=patch.model_dump(exclude_unset=True))
        return Roaster.from_model(state.roasters.replace(merged))

    @strawberry.mutation
    def delete_roaster(self, info: strawberry.Info, id: UUID) -> bool:
        try:
            _state(info).roasters.delete(id)
        except LookupError:
            return False
        return True

    # --- bean -----------------------------------------------------------

    @strawberry.mutation
    def create_bean(self, info: strawberry.Info, input: BeanInput) -> Bean:
        state = _state(info)
        raw = strip_unset(input)
        if "price" in raw:
            raw["price"] = decimal_or_none(raw["price"])  # type: ignore[arg-type]
        _check_roaster(state, raw.get("roaster_id"))  # type: ignore[arg-type]
        try:
            payload = BeanCreate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        model = BeanModel(id=uuid4(), **payload.model_dump())
        return Bean.from_model(state.beans.insert(model))

    @strawberry.mutation
    def update_bean(
        self, info: strawberry.Info, id: UUID, input: BeanPatch
    ) -> Bean:
        state = _state(info)
        try:
            current = state.beans.get(id)
        except LookupError as exc:
            raise ValueError("bean not found") from exc
        raw = strip_unset(input)
        if "price" in raw:
            raw["price"] = decimal_or_none(raw["price"])  # type: ignore[arg-type]
        if "roaster_id" in raw:
            _check_roaster(state, raw["roaster_id"])  # type: ignore[arg-type]
        try:
            patch = BeanUpdate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        try:
            merged = BeanModel.model_validate(
                {**current.model_dump(), **patch.model_dump(exclude_unset=True)}
            )
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        return Bean.from_model(state.beans.replace(merged))

    @strawberry.mutation
    def delete_bean(self, info: strawberry.Info, id: UUID) -> bool:
        try:
            _state(info).beans.delete(id)
        except LookupError:
            return False
        return True

    # --- equipment ------------------------------------------------------

    @strawberry.mutation
    def create_equipment(
        self, info: strawberry.Info, input: EquipmentInput
    ) -> Equipment:
        state = _state(info)
        try:
            payload = EquipmentCreate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        model = EquipmentModel(id=uuid4(), **payload.model_dump())
        return Equipment.from_model(state.equipment.insert(model))

    @strawberry.mutation
    def update_equipment(
        self, info: strawberry.Info, id: UUID, input: EquipmentPatch
    ) -> Equipment:
        state = _state(info)
        try:
            current = state.equipment.get(id)
        except LookupError as exc:
            raise ValueError("equipment not found") from exc
        try:
            patch = EquipmentUpdate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        try:
            merged = EquipmentModel.model_validate(
                {**current.model_dump(), **patch.model_dump(exclude_unset=True)}
            )
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        return Equipment.from_model(state.equipment.replace(merged))

    @strawberry.mutation
    def delete_equipment(self, info: strawberry.Info, id: UUID) -> bool:
        try:
            _state(info).equipment.delete(id)
        except LookupError:
            return False
        return True

    # --- brewlog --------------------------------------------------------

    @strawberry.mutation
    def create_brewlog(
        self, info: strawberry.Info, input: BrewLogInput
    ) -> BrewLog:
        state = _state(info)
        raw = strip_unset(input)
        for key in ("dose_g", "water_g", "yield_g"):
            if key in raw:
                raw[key] = decimal_or_none(raw[key])  # type: ignore[arg-type]
        _check_brewlog_refs(
            state,
            raw["bean_id"],  # type: ignore[arg-type]
            raw["equipment_id"],  # type: ignore[arg-type]
            raw["grinder_id"],  # type: ignore[arg-type]
        )
        try:
            payload = BrewLogCreate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        model = BrewLogModel(id=uuid4(), **payload.model_dump())
        return BrewLog.from_model(state.brewlogs.insert(model))

    @strawberry.mutation
    def update_brewlog(
        self, info: strawberry.Info, id: UUID, input: BrewLogPatch
    ) -> BrewLog:
        state = _state(info)
        try:
            current = state.brewlogs.get(id)
        except LookupError as exc:
            raise ValueError("brewlog not found") from exc
        raw = strip_unset(input)
        for key in ("dose_g", "water_g", "yield_g"):
            if key in raw:
                raw[key] = decimal_or_none(raw[key])  # type: ignore[arg-type]
        try:
            patch = BrewLogUpdate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        merged_dict = {**current.model_dump(), **patch.model_dump(exclude_unset=True)}
        if any(k in raw for k in ("bean_id", "equipment_id", "grinder_id")):
            _check_brewlog_refs(
                state,
                merged_dict["bean_id"],
                merged_dict["equipment_id"],
                merged_dict["grinder_id"],
            )
        try:
            merged = BrewLogModel.model_validate(merged_dict)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        return BrewLog.from_model(state.brewlogs.replace(merged))

    @strawberry.mutation
    def delete_brewlog(self, info: strawberry.Info, id: UUID) -> bool:
        try:
            _state(info).brewlogs.delete(id)
        except LookupError:
            return False
        return True
