"""OTP service — generation, storage, and verification of one-time passwords."""

import logging
import os
import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.card import OtpToken

logger = logging.getLogger(__name__)

RATE_LIMIT_PER_MINUTE = 3
MAX_VERIFY_ATTEMPTS = 3


def _generate_otp_code() -> str:
    """Generate a 6-digit numeric OTP code."""
    return "".join(random.choices(string.digits, k=6))


async def send_otp(db: AsyncSession, phone: str) -> bool:
    """
    Generate and send a 6-digit OTP to the given phone number.

    - Rate limited to 3 OTPs per minute per phone
    - In dev mode: logs OTP instead of sending via WhatsApp
    - In prod mode: sends via WhatsApp Business API
    """
    # Rate limit check: count OTPs sent in the last minute
    one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    rate_result = await db.execute(
        select(func.count(OtpToken.id)).where(
            and_(
                OtpToken.phone == phone,
                OtpToken.created_at >= one_minute_ago,
            )
        )
    )
    recent_count = rate_result.scalar() or 0

    if recent_count >= RATE_LIMIT_PER_MINUTE:
        logger.warning("OTP rate limit exceeded for phone %s", phone[-4:])
        raise ValueError("Too many OTP requests. Please wait a minute and try again.")

    code = _generate_otp_code()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.OTP_EXPIRY_SECONDS
    )

    otp = OtpToken(
        phone=phone,
        code=code,
        expires_at=expires_at,
        is_used=False,
        attempts=0,
    )
    db.add(otp)
    await db.flush()

    # Send OTP
    is_dev = os.getenv("APP_ENV", "development") == "development"
    if is_dev:
        logger.info("DEV OTP for %s: %s", phone[-4:], code)
    else:
        # Production: send via WhatsApp Business API
        await _send_whatsapp_otp(phone, code)

    return True


async def _send_whatsapp_otp(phone: str, code: str) -> None:
    """Send OTP via WhatsApp Business API."""
    import httpx

    if not settings.WHATSAPP_API_URL or not settings.WHATSAPP_API_TOKEN:
        logger.error("WhatsApp API not configured, cannot send OTP")
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.WHATSAPP_API_URL}/messages",
                headers={
                    "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "template",
                    "template": {
                        "name": "otp_verification",
                        "language": {"code": "en"},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": code},
                                ],
                            }
                        ],
                    },
                },
            )
            response.raise_for_status()
            logger.info("WhatsApp OTP sent to %s", phone[-4:])
    except httpx.HTTPError as e:
        logger.error("Failed to send WhatsApp OTP: %s", e)
        raise RuntimeError("Failed to send OTP via WhatsApp") from e


async def verify_otp(db: AsyncSession, phone: str, code: str) -> bool:
    """
    Verify an OTP code for the given phone number.

    - Checks the latest unused, unexpired OTP
    - Max 3 verification attempts per OTP
    - Marks OTP as used on success
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(OtpToken)
        .where(
            and_(
                OtpToken.phone == phone,
                OtpToken.is_used.is_(False),
                OtpToken.expires_at > now,
                OtpToken.attempts < MAX_VERIFY_ATTEMPTS,
            )
        )
        .order_by(OtpToken.created_at.desc())
        .limit(1)
    )
    otp = result.scalar_one_or_none()

    if otp is None:
        logger.warning("No valid OTP found for phone %s", phone[-4:])
        return False

    otp.attempts = (otp.attempts or 0) + 1

    if otp.code != code:
        logger.info(
            "OTP mismatch for phone %s (attempt %d/%d)",
            phone[-4:],
            otp.attempts,
            MAX_VERIFY_ATTEMPTS,
        )
        await db.flush()
        return False

    # Success
    otp.is_used = True
    await db.flush()
    logger.info("OTP verified for phone %s", phone[-4:])
    return True
