"""Register / login / logout / me — session-cookie based."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, get_db
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import create_session, revoke_session
from app.db.models import Role, User
from app.repositories.users import UserRepository
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    roles: list[str]
    permissions: list[str]


def _serialise(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        roles=[r.name for r in user.roles],
        permissions=[p.code for r in user.roles for p in r.permissions],
    )


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, detail="email already registered")

    user_role = (await db.execute(select(Role).where(Role.name == "user"))).scalar_one_or_none()
    if user_role is None:
        user_role = Role(name="user")
        db.add(user_role)
        await db.flush()
    await UserRepository(db).attach_role(user_id=user.id, role_id=user_role.id)
    await db.commit()
    fresh = await UserRepository(db).get_with_perms(user.id)
    return _serialise(fresh)


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginIn,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await UserRepository(db).find_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        await write_audit(
            db,
            user_id=user.id if user else None,
            action="LOGIN_FAIL",
            status="FAIL",
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
        raise HTTPException(401, detail="invalid credentials")

    sess = await create_session(db, user.id)
    await write_audit(
        db, user_id=user.id, action="LOGIN", status="OK",
        role_snapshot=",".join(r.name for r in user.roles),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    response.set_cookie(
        key="session_id",
        value=str(sess.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return _serialise(user)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    cookie = request.cookies.get("session_id")
    if cookie:
        try:
            await revoke_session(db, UUID(cookie))
        except ValueError:
            pass
    await write_audit(db, user_id=user.id, action="LOGOUT", status="OK")
    await db.commit()
    response.delete_cookie("session_id")
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return _serialise(user)
