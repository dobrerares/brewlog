"""FastAPI dependencies."""

from __future__ import annotations

from typing import AsyncIterator
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import lookup_session
from app.auth.tokens import TokenError, jwt_decode
from app.db.base import get_db as _get_db
from app.db.models import User
from app.repositories.users import UserRepository
from app.services.audit import write_audit


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in _get_db():
        yield session


async def current_user(
    request: Request,
    access_token: str | None = Cookie(default=None, alias="access_token"),
    session_id: str | None = Cookie(default=None, alias="session_id"),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id: UUID | None = None
    if access_token:
        try:
            claims = jwt_decode(access_token, "access")
            user_id = UUID(claims["sub"])
            request.state.auth_claims = claims
        except (KeyError, ValueError, TokenError):
            raise HTTPException(401, detail="invalid or expired access token")
    elif session_id is not None:
        try:
            sid = UUID(session_id)
        except ValueError:
            raise HTTPException(401, detail="malformed session")
        sess = await lookup_session(db, sid)
        if sess is None:
            raise HTTPException(401, detail="session expired or revoked")
        user_id = sess.user_id
    else:
        raise HTTPException(401, detail="not authenticated")
    user = await UserRepository(db).get_with_perms(user_id)
    if user is None:
        raise HTTPException(401, detail="user no longer exists")
    request.state.user = user
    return user


def _user_permission_codes(user: User) -> set[str]:
    codes: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return codes


def requires(*perm_codes: str):
    """Dependency factory. 403 + DENIED audit row if any perm missing."""

    async def _check(
        user: User = Depends(current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        granted = _user_permission_codes(user)
        missing = [code for code in perm_codes if code not in granted]
        if missing:
            await write_audit(
                db,
                user_id=user.id,
                action="PERM_DENIED",
                status="DENIED",
                role_snapshot=",".join(r.name for r in user.roles),
                metadata={"required": list(perm_codes), "missing": missing},
            )
            await db.commit()
            raise HTTPException(403, detail={"required": list(perm_codes), "missing": missing})
        return user

    return _check
