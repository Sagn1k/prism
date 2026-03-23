"""Authentication router — OTP login, token refresh, profile."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.card import OtpToken
from app.models.user import User, UserRole
from passlib.hash import bcrypt

from app.schemas.auth import LoginRequest, OtpSendRequest, OtpVerifyRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_token(user_id: str, *, expires_delta: timedelta, token_type: str = "access") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _issue_tokens(user: User) -> tuple[str, str]:
    access = _create_token(
        str(user.id),
        expires_delta=timedelta(days=settings.JWT_EXPIRY_DAYS),
        token_type="access",
    )
    refresh = _create_token(
        str(user.id),
        expires_delta=timedelta(days=30),
        token_type="refresh",
    )
    return access, refresh


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/otp/send", status_code=status.HTTP_200_OK)
async def send_otp(
    body: OtpSendRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate a 6-digit OTP and persist it with a 5-minute expiry."""
    phone = body.phone.strip()
    if not phone or len(phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid phone number",
        )

    # Purge any existing OTPs for this phone
    await db.execute(delete(OtpToken).where(OtpToken.phone == phone))

    code = f"{random.randint(0, 999999):06d}"
    otp = OtpToken(
        phone=phone,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
    )
    db.add(otp)
    await db.flush()

    return {"ok": True, "message": "OTP sent"}


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(
    body: OtpVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify OTP, create user if new, and issue JWT tokens."""
    phone = body.phone.strip()

    result = await db.execute(
        select(OtpToken)
        .where(OtpToken.phone == phone, OtpToken.code == body.otp)
        .order_by(OtpToken.expires_at.desc())
        .limit(1)
    )
    otp_row = result.scalar_one_or_none()

    if otp_row is None or otp_row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    # OTP consumed — delete it
    await db.execute(delete(OtpToken).where(OtpToken.phone == phone))

    # Fetch or create user
    user_result = await db.execute(select(User).where(User.phone == phone))
    user = user_result.scalar_one_or_none()

    is_new = user is None
    if is_new:
        if not body.name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name is required for new users",
            )
        user = User(
            phone=phone,
            name=body.name,
            role=UserRole.student,
        )
        db.add(user)
        await db.flush()
    elif body.name:
        user.name = body.name
        await db.flush()

    access, refresh = _issue_tokens(user)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh")
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Validate refresh token and issue a new access token."""
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access = _create_token(str(user.id), expires_delta=timedelta(days=settings.JWT_EXPIRY_DAYS))
    return {"access_token": access}


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user with email and password."""
    email = body.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address",
        )
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters",
        )

    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        name=body.name.strip(),
        password_hash=bcrypt.hash(body.password),
        role=UserRole.student,
    )
    db.add(user)
    await db.flush()

    access, refresh = _issue_tokens(user)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate a user with email and password."""
    email = body.email.strip().lower()

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not bcrypt.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access, refresh = _issue_tokens(user)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
