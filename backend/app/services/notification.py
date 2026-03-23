"""Notification service — WhatsApp, push notifications, and scheduled quests."""

import logging
import random
import uuid
from datetime import date, datetime, timezone

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.game import DailyQuest, Mission
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def send_whatsapp(
    phone: str,
    template: str,
    params: dict | None = None,
) -> bool:
    """
    Send a WhatsApp message via WhatsApp Business API.

    Placeholder implementation — requires WHATSAPP_API_URL and
    WHATSAPP_API_TOKEN to be configured in settings.
    """
    if not settings.WHATSAPP_API_URL or not settings.WHATSAPP_API_TOKEN:
        logger.warning("WhatsApp API not configured, skipping send to %s", phone[-4:])
        return False

    components = []
    if params:
        body_params = [
            {"type": "text", "text": str(v)} for v in params.values()
        ]
        components.append({"type": "body", "parameters": body_params})

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
                        "name": template,
                        "language": {"code": "en"},
                        "components": components,
                    },
                },
            )
            response.raise_for_status()
            logger.info("WhatsApp sent to %s (template=%s)", phone[-4:], template)
            return True
    except httpx.HTTPError as e:
        logger.error("WhatsApp send failed: %s", e)
        return False


async def send_push(
    user_id: uuid.UUID,
    title: str,
    body: str,
) -> bool:
    """
    Send a push notification via FCM.

    Placeholder implementation — requires FCM server key and user
    device token storage to be set up.
    """
    # TODO: Implement FCM integration
    # 1. Look up user's FCM device token from DB
    # 2. Send via Firebase Admin SDK or HTTP v1 API
    logger.info(
        "Push notification (placeholder): user=%s title=%s",
        user_id,
        title,
    )
    return True


async def schedule_daily_quests(db: AsyncSession) -> int:
    """
    Assign a random mission as a daily quest for each active student.

    Returns the number of quests created.
    """
    today = date.today()

    # Get active students
    student_result = await db.execute(
        select(User.id).where(
            and_(
                User.role == UserRole.student,
                User.onboarded.is_(True),
            )
        )
    )
    student_ids = [row[0] for row in student_result.all()]

    if not student_ids:
        logger.info("No active students found for daily quests")
        return 0

    # Get active missions
    mission_result = await db.execute(
        select(Mission.id).where(Mission.is_active.is_(True))
    )
    mission_ids = [row[0] for row in mission_result.all()]

    if not mission_ids:
        logger.warning("No active missions available for daily quests")
        return 0

    # Check which students already have a quest today
    existing_result = await db.execute(
        select(DailyQuest.user_id).where(DailyQuest.quest_date == today)
    )
    already_assigned = {row[0] for row in existing_result.all()}

    created = 0
    for student_id in student_ids:
        if student_id in already_assigned:
            continue

        quest = DailyQuest(
            user_id=student_id,
            mission_id=random.choice(mission_ids),
            quest_date=today,
            is_completed=False,
        )
        db.add(quest)
        created += 1

    if created:
        await db.flush()

    logger.info("Scheduled %d daily quests for %s", created, today.isoformat())
    return created
