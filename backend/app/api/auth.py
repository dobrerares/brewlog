"""Register / login / logout / me — JWT cookie based."""

from __future__ import annotations

import html
import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, get_db
from app.auth.mfa import (
    dev_totp_code,
    hash_backup_code,
    new_backup_codes,
    new_totp_secret,
    totp_uri,
    verify_backup_code,
    verify_totp,
)
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import (
    create_refresh_session,
    lookup_refresh_session,
    revoke_refresh_session,
    touch_refresh_session,
)
from app.auth.tokens import (
    TokenError,
    access_minutes,
    cookie_samesite,
    cookie_secure,
    jwt_decode,
    jwt_encode,
    make_access_token,
    refresh_hours,
    token_hash,
)
from app.db.models import LoginEmailCode, MfaBackupCode, PasswordResetToken, RefreshSession, Role, User
from app.repositories.users import UserRepository
from app.services.audit import write_audit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MfaCodeIn(BaseModel):
    code: str = Field(min_length=6, max_length=20)


class LoginMfaIn(BaseModel):
    totp_code: str = Field(min_length=6, max_length=20)
    email_token: str = Field(min_length=20, max_length=200)


class LoginMfaRequiredOut(BaseModel):
    mfa_required: bool = True
    email_sent: bool = True
    dev_magic_link: str | None = None


class MfaSetupOut(BaseModel):
    secret: str
    provisioning_uri: str
    dev_code: str | None = None


class MfaVerifySetupOut(BaseModel):
    backup_codes: list[str]


class PasswordResetConfirmIn(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=200)


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    roles: list[str]
    permissions: list[str]
    mfa_enabled: bool = False


def _serialise(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        roles=[r.name for r in user.roles],
        permissions=[p.code for r in user.roles for p in r.permissions],
        mfa_enabled=user.mfa_enabled,
    )


def _roles(user: User) -> list[str]:
    return [r.name for r in user.roles]


def _permissions(user: User) -> list[str]:
    return sorted({p.code for r in user.roles for p in r.permissions})


def _set_auth_cookies(response: Response, user: User, session_id: UUID, refresh_token: str) -> None:
    access = make_access_token(
        user_id=user.id,
        session_id=session_id,
        email=user.email,
        roles=_roles(user),
        permissions=_permissions(user),
    )
    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=cookie_secure(),
        samesite=cookie_samesite(),
        max_age=access_minutes() * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=cookie_secure(),
        samesite=cookie_samesite(),
        max_age=refresh_hours() * 60 * 60,
        path="/api/v1/auth/refresh",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    response.delete_cookie("mfa_challenge", path="/api/v1/auth/login")


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _issue_auth(response: Response, request: Request, db: AsyncSession, user: User) -> None:
    refresh_session, refresh_token = await create_refresh_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=_client_ip(request),
    )
    _set_auth_cookies(response, user, refresh_session.id, refresh_token)


def _make_mfa_challenge(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt_encode(
        {
            "sub": str(user.id),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "type": "mfa_challenge",
        }
    )


def _new_email_token() -> str:
    return secrets.token_urlsafe(32)


def _allow_dev_magic_link() -> bool:
    return os.environ.get("ALLOW_DEV_MAGIC_LINK", "true").lower() in {"1", "true", "yes"}


def _app_base_url(request: Request) -> str:
    configured = os.environ.get("APP_BASE_URL")
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


async def _send_magic_link_email(user: User, magic_link: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    sender = os.environ.get("RESEND_FROM_EMAIL")
    if not api_key or not sender:
        print(f"[auth-magic-link] {user.email}: {magic_link}")
        return
    payload = {
        "from": sender,
        "to": [user.email],
        "subject": "Your BrewLog sign-in link",
        "html": (
            "<p>Use this link to continue signing in to BrewLog:</p>"
            f'<p><a href="{html.escape(magic_link)}">Continue sign-in</a></p>'
            "<p>This link expires in 10 minutes.</p>"
        ),
        "text": f"Use this link to continue signing in to BrewLog: {magic_link}\n\nThis link expires in 10 minutes.",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
    if response.status_code >= 400:
        raise HTTPException(502, detail="could not send login email")


async def _issue_login_email_code(db: AsyncSession, request: Request, user: User) -> str:
    token = _new_email_token()
    now = datetime.now(timezone.utc)
    await db.execute(
        LoginEmailCode.__table__.update()
        .where(LoginEmailCode.user_id == user.id, LoginEmailCode.used_at.is_(None))
        .values(used_at=now)
    )
    db.add(
        LoginEmailCode(
            user_id=user.id,
            code_hash=token_hash(token),
            expires_at=now + timedelta(minutes=10),
        )
    )
    magic_link = f"{_app_base_url(request)}/login/mfa?token={token}"
    await _send_magic_link_email(user, magic_link)
    return magic_link


async def _consume_login_email_code(db: AsyncSession, user: User, token: str) -> bool:
    row = (
        await db.execute(
            select(LoginEmailCode)
            .where(
                LoginEmailCode.user_id == user.id,
                LoginEmailCode.code_hash == token_hash(token),
                LoginEmailCode.used_at.is_(None),
                LoginEmailCode.expires_at > datetime.now(timezone.utc),
            )
            .order_by(LoginEmailCode.created_at.desc())
        )
    ).scalars().first()
    if row is None:
        return False
    row.used_at = datetime.now(timezone.utc)
    return True


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


@router.post("/login", response_model=None)
async def login(
    payload: LoginIn,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut | dict[str, bool]:
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

    fresh = await UserRepository(db).get_with_perms(user.id)
    if fresh is None:
        raise HTTPException(401, detail="user no longer exists")
    if fresh.mfa_enabled:
        magic_link = await _issue_login_email_code(db, request, fresh)
        response.set_cookie(
            key="mfa_challenge",
            value=_make_mfa_challenge(fresh),
            httponly=True,
            secure=cookie_secure(),
            samesite=cookie_samesite(),
            max_age=5 * 60,
            path="/api/v1/auth/login",
        )
        await db.commit()
        return LoginMfaRequiredOut(dev_magic_link=magic_link if _allow_dev_magic_link() else None)  # type: ignore[return-value]
    await _issue_auth(response, request, db, fresh)
    await write_audit(
        db, user_id=fresh.id, action="LOGIN", status="OK",
        role_snapshot=",".join(r.name for r in fresh.roles),
        ip_address=_client_ip(request),
    )
    await db.commit()
    return _serialise(fresh)


@router.post("/login/resend-magic-link", response_model=LoginMfaRequiredOut)
async def resend_login_email_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginMfaRequiredOut:
    challenge = request.cookies.get("mfa_challenge")
    if not challenge:
        raise HTTPException(401, detail="mfa challenge missing")
    try:
        claims = jwt_decode(challenge, "mfa_challenge")
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError, TokenError):
        raise HTTPException(401, detail="mfa challenge expired")
    user = await UserRepository(db).get_with_perms(user_id)
    if user is None or not user.mfa_enabled:
        raise HTTPException(401, detail="mfa unavailable")
    magic_link = await _issue_login_email_code(db, request, user)
    await write_audit(db, user_id=user.id, action="LOGIN_EMAIL_CODE_RESEND", status="OK", ip_address=_client_ip(request))
    await db.commit()
    return LoginMfaRequiredOut(dev_magic_link=magic_link if _allow_dev_magic_link() else None)


@router.post("/login/verify-mfa", response_model=UserOut)
async def verify_login_mfa(
    payload: LoginMfaIn,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    challenge = request.cookies.get("mfa_challenge")
    if not challenge:
        raise HTTPException(401, detail="mfa challenge missing")
    try:
        claims = jwt_decode(challenge, "mfa_challenge")
        user_id = UUID(claims["sub"])
    except (KeyError, ValueError, TokenError):
        raise HTTPException(401, detail="mfa challenge expired")
    user = await UserRepository(db).get_with_perms(user_id)
    if user is None or not user.mfa_enabled or user.mfa_secret is None:
        raise HTTPException(401, detail="mfa unavailable")
    valid_totp_or_backup = verify_totp(user.mfa_secret, payload.totp_code)
    used_backup_code: MfaBackupCode | None = None
    if not valid_totp_or_backup:
        codes = (
            await db.execute(
                select(MfaBackupCode).where(
                    MfaBackupCode.user_id == user.id,
                    MfaBackupCode.used_at.is_(None),
                )
            )
        ).scalars().all()
        for code in codes:
            if verify_backup_code(payload.totp_code, code.code_hash):
                used_backup_code = code
                valid_totp_or_backup = True
                break
    valid_email = await _consume_login_email_code(db, user, payload.email_token)
    if not valid_totp_or_backup or not valid_email:
        await write_audit(db, user_id=user.id, action="MFA_FAIL", status="FAIL", ip_address=_client_ip(request))
        await db.commit()
        raise HTTPException(401, detail="invalid mfa factors")
    if used_backup_code is not None:
        used_backup_code.used_at = datetime.now(timezone.utc)
    await _issue_auth(response, request, db, user)
    response.delete_cookie("mfa_challenge", path="/api/v1/auth/login")
    await write_audit(db, user_id=user.id, action="LOGIN_3FA", status="OK", ip_address=_client_ip(request))
    await db.commit()
    return _serialise(user)


@router.post("/refresh", response_model=UserOut)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, detail="refresh token missing")
    session = await lookup_refresh_session(db, refresh_token)
    if session is None:
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(401, detail="refresh session expired or revoked")
    user = await UserRepository(db).get_with_perms(session.user_id)
    if user is None:
        await revoke_refresh_session(db, session)
        await db.commit()
        _clear_auth_cookies(response)
        raise HTTPException(401, detail="user no longer exists")
    await touch_refresh_session(db, session)
    access = make_access_token(
        user_id=user.id,
        session_id=session.id,
        email=user.email,
        roles=_roles(user),
        permissions=_permissions(user),
    )
    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=cookie_secure(),
        samesite=cookie_samesite(),
        max_age=access_minutes() * 60,
        path="/",
    )
    await db.commit()
    return _serialise(user)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Response:
    refresh_token = request.cookies.get("refresh_token")
    user_id = None
    if refresh_token:
        session = await lookup_refresh_session(db, refresh_token)
        if session is not None:
            user_id = session.user_id
            await revoke_refresh_session(db, session)
    else:
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                claims = jwt_decode(access_token, "access")
                session_id = UUID(claims["sid"])
                session = await db.get(RefreshSession, session_id)
                if session is not None:
                    user_id = session.user_id
                    await revoke_refresh_session(db, session)
            except (KeyError, ValueError, TokenError):
                pass
    await write_audit(db, user_id=user_id, action="LOGOUT", status="OK")
    await db.commit()
    _clear_auth_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> UserOut:
    return _serialise(user)


@router.post("/mfa/setup", response_model=MfaSetupOut)
async def mfa_setup(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MfaSetupOut:
    user.mfa_secret = new_totp_secret()
    user.mfa_enabled = False
    await db.commit()
    return MfaSetupOut(
        secret=user.mfa_secret,
        provisioning_uri=totp_uri(email=user.email, secret=user.mfa_secret),
        dev_code=dev_totp_code(user.mfa_secret) or None,
    )


@router.post("/mfa/verify-setup", response_model=MfaVerifySetupOut)
async def mfa_verify_setup(
    payload: MfaCodeIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> MfaVerifySetupOut:
    if not user.mfa_secret or not verify_totp(user.mfa_secret, payload.code):
        raise HTTPException(400, detail="invalid mfa setup code")
    user.mfa_enabled = True
    await db.execute(
        MfaBackupCode.__table__.delete().where(MfaBackupCode.user_id == user.id)
    )
    codes = new_backup_codes()
    for code in codes:
        db.add(MfaBackupCode(user_id=user.id, code_hash=hash_backup_code(code)))
    await db.commit()
    return MfaVerifySetupOut(backup_codes=codes)


@router.post("/password-reset/confirm", status_code=204)
async def confirm_password_reset(
    payload: PasswordResetConfirmIn,
    db: AsyncSession = Depends(get_db),
) -> Response:
    reset = (
        await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash(payload.token),
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
            )
        )
    ).scalar_one_or_none()
    if reset is None:
        raise HTTPException(400, detail="invalid or expired reset token")
    user = await UserRepository(db).get(reset.user_id)
    user.password_hash = hash_password(payload.new_password)
    reset.used_at = datetime.now(timezone.utc)
    await write_audit(db, user_id=user.id, action="PASSWORD_RESET_CONFIRM", status="OK")
    await db.commit()
    return Response(status_code=204)
