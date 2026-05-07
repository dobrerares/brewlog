"""GraphQL write-side — reuses Pydantic Create/Update models for validation.

Every resolver converts the Strawberry input → Pydantic model; validation
errors bubble up as standard GraphQL errors with the Pydantic message list.
"""

from __future__ import annotations

import os
from uuid import UUID

import strawberry
from pydantic import ValidationError
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BeanTastingNote, BrewlogTastingNote
from app.repositories.base import NotFoundError
from app.repositories.beans import BeanRepository
from app.repositories.brewlogs import BrewlogRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.roasters import RoasterRepository
from app.repositories.tasting_notes import TastingNoteRepository
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
from app.schemas import Bean as BeanModel
from app.schemas import BrewLog as BrewLogModel
from app.schemas import Equipment as EquipmentModel
from app.schemas import Roaster as RoasterModel

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

_DEV_USER = UUID(os.environ.get("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"))


def _db(info: strawberry.Info) -> AsyncSession:
    return info.context["db"]


def _wrap_validation(exc: ValidationError) -> ValueError:
    msgs = [
        f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}"
        for err in exc.errors(include_url=False, include_input=False, include_context=False)
    ]
    return ValueError("; ".join(msgs))


async def _roaster_model_from_row(row) -> RoasterModel:
    return RoasterModel.model_validate(row, from_attributes=True)


async def _equipment_model_from_row(row) -> EquipmentModel:
    return EquipmentModel.model_validate(row, from_attributes=True)


async def _bean_model_from_row(row, tn_repo: TastingNoteRepository) -> BeanModel:
    notes = await tn_repo.labels_for_bean(row.id)
    return BeanModel.model_validate(
        {
            "id": row.id,
            "name": row.name,
            "roaster_id": row.roaster_id,
            "origin_country": row.origin_country,
            "origin_region": row.origin_region,
            "process": row.process,
            "roast_level": row.roast_level,
            "variety": row.variety,
            "elevation_m": row.elevation_m,
            "tasting_notes": notes,
            "purchase_date": row.purchase_date,
            "price": row.price,
        }
    )


async def _brewlog_model_from_row(row, tn_repo: TastingNoteRepository) -> BrewLogModel:
    notes = await tn_repo.labels_for_brewlog(row.id)
    return BrewLogModel.model_validate(
        {
            "id": row.id,
            "date": row.date,
            "bean_id": row.bean_id,
            "equipment_id": row.equipment_id,
            "grinder_id": row.grinder_id,
            "grind_setting": row.grind_setting,
            "method": row.method,
            "dose_g": row.dose_g,
            "water_g": row.water_g,
            "water_temp_c": row.water_temp_c,
            "brew_time_s": row.brew_time_s,
            "yield_g": row.yield_g,
            "rating": row.rating,
            "taste_result": row.taste_result,
            "grind_adjustment": row.grind_adjustment,
            "tasting_notes": notes,
            "notes": row.notes,
            "photo_url": row.photo_url,
        }
    )


@strawberry.type
class Mutation:
    # --- roaster --------------------------------------------------------

    @strawberry.mutation
    async def create_roaster(self, info: strawberry.Info, input: RoasterInput) -> Roaster:
        db = _db(info)
        try:
            payload = RoasterCreate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        repo = RoasterRepository(db)
        row = await repo.create(user_id=_DEV_USER, **payload.model_dump(mode="json"))
        await db.commit()
        return Roaster.from_model(await _roaster_model_from_row(row))

    @strawberry.mutation
    async def update_roaster(
        self, info: strawberry.Info, id: UUID, input: RoasterPatch
    ) -> Roaster:
        db = _db(info)
        repo = RoasterRepository(db)
        try:
            await repo.get(id)
        except NotFoundError as exc:
            raise ValueError("roaster not found") from exc
        try:
            patch = RoasterUpdate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        row = await repo.update(id, **patch.model_dump(exclude_unset=True, mode="json"))
        await db.commit()
        return Roaster.from_model(await _roaster_model_from_row(row))

    @strawberry.mutation
    async def delete_roaster(self, info: strawberry.Info, id: UUID) -> bool:
        db = _db(info)
        try:
            await RoasterRepository(db).delete(id)
            await db.commit()
        except NotFoundError:
            return False
        return True

    # --- bean -----------------------------------------------------------

    @strawberry.mutation
    async def create_bean(self, info: strawberry.Info, input: BeanInput) -> Bean:
        db = _db(info)
        raw = strip_unset(input)
        if "price" in raw:
            raw["price"] = decimal_or_none(raw["price"])  # type: ignore[arg-type]
        # Validate roaster FK
        roaster_id = raw.get("roaster_id")
        if roaster_id is not None:
            try:
                await RoasterRepository(db).get(roaster_id)  # type: ignore[arg-type]
            except NotFoundError as exc:
                raise ValueError(f"roaster_id {roaster_id} does not exist") from exc
        try:
            payload = BeanCreate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        repo = BeanRepository(db)
        tn_repo = TastingNoteRepository(db)
        data = payload.model_dump(exclude={"tasting_notes"})
        row = await repo.create(user_id=_DEV_USER, **data)
        if payload.tasting_notes:
            await tn_repo.attach_to_bean(row.id, payload.tasting_notes)
        await db.commit()
        return Bean.from_model(await _bean_model_from_row(row, tn_repo))

    @strawberry.mutation
    async def update_bean(
        self, info: strawberry.Info, id: UUID, input: BeanPatch
    ) -> Bean:
        db = _db(info)
        repo = BeanRepository(db)
        tn_repo = TastingNoteRepository(db)
        try:
            current_row = await repo.get(id)
        except NotFoundError as exc:
            raise ValueError("bean not found") from exc
        raw = strip_unset(input)
        if "price" in raw:
            raw["price"] = decimal_or_none(raw["price"])  # type: ignore[arg-type]
        if "roaster_id" in raw and raw["roaster_id"] is not None:
            try:
                await RoasterRepository(db).get(raw["roaster_id"])  # type: ignore[arg-type]
            except NotFoundError as exc:
                raise ValueError(f"roaster_id {raw['roaster_id']} does not exist") from exc
        try:
            patch = BeanUpdate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        # Fetch current tasting notes for cross-field validation
        current_notes = await tn_repo.labels_for_bean(id)
        current_dict = {
            "id": current_row.id,
            "name": current_row.name,
            "roaster_id": current_row.roaster_id,
            "origin_country": current_row.origin_country,
            "origin_region": current_row.origin_region,
            "process": current_row.process,
            "roast_level": current_row.roast_level,
            "variety": current_row.variety,
            "elevation_m": current_row.elevation_m,
            "tasting_notes": current_notes,
            "purchase_date": current_row.purchase_date,
            "price": current_row.price,
        }
        updates = patch.model_dump(exclude_unset=True)
        new_notes = updates.pop("tasting_notes", None)
        merged_dict = {**current_dict, **updates}
        if new_notes is not None:
            merged_dict["tasting_notes"] = new_notes
        try:
            BeanModel.model_validate(merged_dict)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        if updates:
            await repo.update(id, **updates)
        if new_notes is not None:
            await db.execute(sa_delete(BeanTastingNote).where(BeanTastingNote.bean_id == id))
            if new_notes:
                await tn_repo.attach_to_bean(id, new_notes)
        await db.commit()
        updated_row = await repo.get(id)
        return Bean.from_model(await _bean_model_from_row(updated_row, tn_repo))

    @strawberry.mutation
    async def delete_bean(self, info: strawberry.Info, id: UUID) -> bool:
        db = _db(info)
        try:
            await BeanRepository(db).delete(id)
            await db.commit()
        except NotFoundError:
            return False
        return True

    # --- equipment ------------------------------------------------------

    @strawberry.mutation
    async def create_equipment(
        self, info: strawberry.Info, input: EquipmentInput
    ) -> Equipment:
        db = _db(info)
        try:
            payload = EquipmentCreate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        repo = EquipmentRepository(db)
        row = await repo.create(user_id=_DEV_USER, **payload.model_dump())
        await db.commit()
        return Equipment.from_model(await _equipment_model_from_row(row))

    @strawberry.mutation
    async def update_equipment(
        self, info: strawberry.Info, id: UUID, input: EquipmentPatch
    ) -> Equipment:
        db = _db(info)
        repo = EquipmentRepository(db)
        try:
            await repo.get(id)
        except NotFoundError as exc:
            raise ValueError("equipment not found") from exc
        try:
            patch = EquipmentUpdate(**strip_unset(input))
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        row = await repo.update(id, **patch.model_dump(exclude_unset=True))
        await db.commit()
        return Equipment.from_model(await _equipment_model_from_row(row))

    @strawberry.mutation
    async def delete_equipment(self, info: strawberry.Info, id: UUID) -> bool:
        db = _db(info)
        try:
            await EquipmentRepository(db).delete(id)
            await db.commit()
        except NotFoundError:
            return False
        return True

    # --- brewlog --------------------------------------------------------

    @strawberry.mutation
    async def create_brewlog(
        self, info: strawberry.Info, input: BrewLogInput
    ) -> BrewLog:
        db = _db(info)
        raw = strip_unset(input)
        for key in ("dose_g", "water_g", "yield_g"):
            if key in raw:
                raw[key] = decimal_or_none(raw[key])  # type: ignore[arg-type]
        # Validate FK references
        bean_id = raw["bean_id"]
        equipment_id = raw["equipment_id"]
        grinder_id = raw["grinder_id"]
        bean_repo = BeanRepository(db)
        equip_repo = EquipmentRepository(db)
        try:
            await bean_repo.get(bean_id)  # type: ignore[arg-type]
        except NotFoundError as exc:
            raise ValueError(f"bean_id {bean_id} does not exist") from exc
        try:
            await equip_repo.get(equipment_id)  # type: ignore[arg-type]
        except NotFoundError as exc:
            raise ValueError(f"equipment_id {equipment_id} does not exist") from exc
        try:
            await equip_repo.get(grinder_id)  # type: ignore[arg-type]
        except NotFoundError as exc:
            raise ValueError(f"grinder_id {grinder_id} does not exist") from exc
        try:
            payload = BrewLogCreate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        repo = BrewlogRepository(db)
        tn_repo = TastingNoteRepository(db)
        data = payload.model_dump(exclude={"tasting_notes"})
        row = await repo.create(user_id=_DEV_USER, **data)
        if payload.tasting_notes:
            await tn_repo.attach_to_brewlog(row.id, payload.tasting_notes)
        await db.commit()
        return BrewLog.from_model(await _brewlog_model_from_row(row, tn_repo))

    @strawberry.mutation
    async def update_brewlog(
        self, info: strawberry.Info, id: UUID, input: BrewLogPatch
    ) -> BrewLog:
        db = _db(info)
        repo = BrewlogRepository(db)
        tn_repo = TastingNoteRepository(db)
        try:
            current_row = await repo.get(id)
        except NotFoundError as exc:
            raise ValueError("brewlog not found") from exc
        raw = strip_unset(input)
        for key in ("dose_g", "water_g", "yield_g"):
            if key in raw:
                raw[key] = decimal_or_none(raw[key])  # type: ignore[arg-type]
        try:
            patch = BrewLogUpdate(**raw)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        current_notes = await tn_repo.labels_for_brewlog(id)
        current_dict = {
            "id": current_row.id,
            "date": current_row.date,
            "bean_id": current_row.bean_id,
            "equipment_id": current_row.equipment_id,
            "grinder_id": current_row.grinder_id,
            "grind_setting": current_row.grind_setting,
            "method": current_row.method,
            "dose_g": current_row.dose_g,
            "water_g": current_row.water_g,
            "water_temp_c": current_row.water_temp_c,
            "brew_time_s": current_row.brew_time_s,
            "yield_g": current_row.yield_g,
            "rating": current_row.rating,
            "taste_result": current_row.taste_result,
            "grind_adjustment": current_row.grind_adjustment,
            "tasting_notes": current_notes,
            "notes": current_row.notes,
            "photo_url": current_row.photo_url,
        }
        updates = patch.model_dump(exclude_unset=True)
        new_notes = updates.pop("tasting_notes", None)
        merged_dict = {**current_dict, **updates}
        if new_notes is not None:
            merged_dict["tasting_notes"] = new_notes
        # Validate FK references if any FK field is changing
        if any(k in raw for k in ("bean_id", "equipment_id", "grinder_id")):
            bean_repo = BeanRepository(db)
            equip_repo = EquipmentRepository(db)
            try:
                await bean_repo.get(merged_dict["bean_id"])
            except NotFoundError as exc:
                raise ValueError(f"bean_id {merged_dict['bean_id']} does not exist") from exc
            try:
                await equip_repo.get(merged_dict["equipment_id"])
            except NotFoundError as exc:
                raise ValueError(f"equipment_id {merged_dict['equipment_id']} does not exist") from exc
            try:
                await equip_repo.get(merged_dict["grinder_id"])
            except NotFoundError as exc:
                raise ValueError(f"grinder_id {merged_dict['grinder_id']} does not exist") from exc
        try:
            BrewLogModel.model_validate(merged_dict)
        except ValidationError as exc:
            raise _wrap_validation(exc) from exc
        scalar_updates = {k: v for k, v in updates.items()}
        if scalar_updates:
            await repo.update(id, **scalar_updates)
        if new_notes is not None:
            await db.execute(
                sa_delete(BrewlogTastingNote).where(BrewlogTastingNote.brewlog_id == id)
            )
            if new_notes:
                await tn_repo.attach_to_brewlog(id, new_notes)
        await db.commit()
        updated_row = await repo.get(id)
        return BrewLog.from_model(await _brewlog_model_from_row(updated_row, tn_repo))

    @strawberry.mutation
    async def delete_brewlog(self, info: strawberry.Info, id: UUID) -> bool:
        db = _db(info)
        try:
            await BrewlogRepository(db).delete(id)
            await db.commit()
        except NotFoundError:
            return False
        return True
