"""Seed roles, permissions, role-permission junction, and bootstrap admin user.

Idempotent — safe to run multiple times. Skips inserts when rows already exist.

USER CONTRIBUTION CHECKPOINT:
The mapping `USER_ROLE_PERMISSIONS` below decides which scope (`:own` vs `:any`)
the normal `user` role gets. The default below gives `user` only `:own` scopes;
adjust as your security policy requires.
"""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.auth.passwords import hash_password
from app.auth.permissions import (
    ALL_PERMISSIONS,
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_DELETE_OWN,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_DELETE_OWN,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_DELETE_OWN,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_DELETE_OWN,
    PERM_CHAT_SEND, PERM_CHAT_READ,
)
from app.db.base import init_engine, session_factory, dispose_engine
from app.db.models import Permission, Role, RolePermission, User, UserRole

# Admin: gets ALL_PERMISSIONS automatically.
# User: gets the `:own` scopes + reads + chat (no admin verbs).
USER_ROLE_PERMISSIONS: list[str] = [
    PERM_BEAN_READ, PERM_BEAN_CREATE, PERM_BEAN_UPDATE_OWN, PERM_BEAN_DELETE_OWN,
    PERM_BREWLOG_READ, PERM_BREWLOG_CREATE, PERM_BREWLOG_UPDATE_OWN, PERM_BREWLOG_DELETE_OWN,
    PERM_EQUIPMENT_READ, PERM_EQUIPMENT_CREATE, PERM_EQUIPMENT_UPDATE_OWN, PERM_EQUIPMENT_DELETE_OWN,
    PERM_ROASTER_READ, PERM_ROASTER_CREATE, PERM_ROASTER_UPDATE_OWN, PERM_ROASTER_DELETE_OWN,
    PERM_CHAT_SEND, PERM_CHAT_READ,
]


async def seed() -> None:
    init_engine()
    factory = session_factory()
    async with factory() as session:
        # 1. Permissions
        for code in ALL_PERMISSIONS:
            stmt = pg_insert(Permission).values(code=code, description=code).on_conflict_do_nothing(index_elements=["code"])
            await session.execute(stmt)

        # 2. Roles
        for name in ("admin", "user"):
            stmt = pg_insert(Role).values(name=name).on_conflict_do_nothing(index_elements=["name"])
            await session.execute(stmt)
        await session.commit()

        # 3. Role-permission mapping
        admin = (await session.execute(select(Role).where(Role.name == "admin"))).scalar_one()
        user_role = (await session.execute(select(Role).where(Role.name == "user"))).scalar_one()
        all_perms = (await session.execute(select(Permission))).scalars().all()
        perm_by_code = {p.code: p for p in all_perms}

        for p in all_perms:
            stmt = pg_insert(RolePermission).values(role_id=admin.id, permission_id=p.id).on_conflict_do_nothing()
            await session.execute(stmt)

        for code in USER_ROLE_PERMISSIONS:
            stmt = pg_insert(RolePermission).values(
                role_id=user_role.id, permission_id=perm_by_code[code].id
            ).on_conflict_do_nothing()
            await session.execute(stmt)

        # 4. Bootstrap admin user
        admin_email = os.environ.get("ADMIN_BOOTSTRAP_EMAIL", "admin@brewlog.local")
        admin_pw = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD", "admin")
        existing = (await session.execute(select(User).where(User.email == admin_email))).scalar_one_or_none()
        if existing is None:
            user = User(email=admin_email, password_hash=hash_password(admin_pw))
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=admin.id))

        await session.commit()
        print(f"seeded RBAC; admin = {admin_email}")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(seed())
