"""Tasting-note catalog + junction writes — 3NF normalisation in code."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BeanTastingNote, BrewlogTastingNote, TastingNote


class TastingNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_labels(self, labels: list[str]) -> dict[str, UUID]:
        if not labels:
            return {}
        for label in labels:
            stmt = pg_insert(TastingNote).values(label=label).on_conflict_do_nothing(
                index_elements=["label"]
            )
            await self.session.execute(stmt)
        rows = (
            await self.session.execute(
                select(TastingNote).where(TastingNote.label.in_(labels))
            )
        ).scalars().all()
        return {r.label: r.id for r in rows}

    async def attach_to_bean(self, bean_id: UUID, labels: list[str]) -> None:
        ids = await self.upsert_labels(labels)
        for tn_id in ids.values():
            stmt = pg_insert(BeanTastingNote).values(
                bean_id=bean_id, tasting_note_id=tn_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.flush()

    async def attach_to_brewlog(self, brewlog_id: UUID, labels: list[str]) -> None:
        ids = await self.upsert_labels(labels)
        for tn_id in ids.values():
            stmt = pg_insert(BrewlogTastingNote).values(
                brewlog_id=brewlog_id, tasting_note_id=tn_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.flush()

    async def labels_for_bean(self, bean_id: UUID) -> list[str]:
        rows = await self.session.execute(
            select(TastingNote.label)
            .join(BeanTastingNote, BeanTastingNote.tasting_note_id == TastingNote.id)
            .where(BeanTastingNote.bean_id == bean_id)
        )
        return [r[0] for r in rows.all()]

    async def labels_for_brewlog(self, brewlog_id: UUID) -> list[str]:
        rows = await self.session.execute(
            select(TastingNote.label)
            .join(BrewlogTastingNote, BrewlogTastingNote.tasting_note_id == TastingNote.id)
            .where(BrewlogTastingNote.brewlog_id == brewlog_id)
        )
        return [r[0] for r in rows.all()]
