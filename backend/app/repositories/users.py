"""User repository — adds email lookup and role/permission loaders."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Role, User, UserRole
from app.repositories.base import AsyncRepository


class UserRepository(AsyncRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def find_by_email(self, email: str) -> User | None:
        rows = await self.session.execute(
            select(User).where(User.email == email).options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return rows.scalar_one_or_none()

    async def get_with_perms(self, user_id: UUID) -> User | None:
        rows = await self.session.execute(
            select(User).where(User.id == user_id).options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        return rows.scalar_one_or_none()

    async def attach_role(self, user_id: UUID, role_id: UUID) -> None:
        self.session.add(UserRole(user_id=user_id, role_id=role_id))
        await self.session.flush()

    async def list_observed(self) -> list[User]:
        rows = await self.session.execute(
            select(User).where(User.is_observed.is_(True)).order_by(User.observed_at.desc())
        )
        return list(rows.scalars().all())

    async def clear_observation(self, user_id: UUID) -> None:
        u = await self.get(user_id)
        u.is_observed = False
        u.observed_reason = None
        u.observed_at = None
        await self.session.flush()
