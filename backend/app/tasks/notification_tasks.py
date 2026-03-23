import logging
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.tasks import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Celery Beat schedule — 7 AM IST for daily quest reminders,
#                        6 PM IST for streak reminders
# IST = UTC+5:30, so 7:00 AM IST = 1:30 AM UTC, 6:00 PM IST = 12:30 PM UTC
# ---------------------------------------------------------------------------

celery_app.conf.beat_schedule = {
    "send-daily-quest-reminders": {
        "task": "app.tasks.notification_tasks.send_daily_quest_reminders",
        "schedule": {
            "__type__": "crontab",
            "minute": "30",
            "hour": "1",  # 1:30 UTC = 7:00 AM IST
        },
    },
    "send-streak-reminders": {
        "task": "app.tasks.notification_tasks.send_streak_reminders",
        "schedule": {
            "__type__": "crontab",
            "minute": "30",
            "hour": "12",  # 12:30 UTC = 6:00 PM IST
        },
    },
}

# Override with proper crontab objects
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "send-daily-quest-reminders": {
        "task": "app.tasks.notification_tasks.send_daily_quest_reminders",
        "schedule": crontab(minute=30, hour=1),  # 1:30 UTC = 7:00 AM IST
    },
    "send-streak-reminders": {
        "task": "app.tasks.notification_tasks.send_streak_reminders",
        "schedule": crontab(minute=30, hour=12),  # 12:30 UTC = 6:00 PM IST
    },
}


def _send_whatsapp_message(phone: str, message: str) -> bool:
    """Placeholder: Send a WhatsApp message via the configured API.

    In production this will use the WhatsApp Business API to send
    template messages to the user's phone number.
    """
    logger.info("WhatsApp message to %s: %s (placeholder)", phone, message[:80])
    return True


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def send_daily_quest_reminders(self) -> dict:
    """Send reminder notifications to students who have incomplete daily quests.

    Scheduled to run at 7:00 AM IST daily.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models.user import User, UserRole
    from app.models.game import DailyQuest

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_url)

    sent_count = 0
    error_count = 0

    try:
        with Session(sync_engine) as session:
            # Find students with incomplete quests for today
            today = date.today()
            incomplete = session.execute(
                select(DailyQuest)
                .where(DailyQuest.quest_date == today)
                .where(DailyQuest.is_completed.is_(False))
            ).scalars().all()

            user_ids = {q.user_id for q in incomplete}

            for uid in user_ids:
                user = session.execute(
                    select(User).where(User.id == uid)
                ).scalar_one_or_none()

                if not user or user.role != UserRole.student:
                    continue

                message = (
                    f"Good morning, {user.name}! "
                    f"You have a daily quest waiting for you on Prism. "
                    f"Complete it to keep your streak alive!"
                )
                try:
                    _send_whatsapp_message(user.phone, message)
                    sent_count += 1
                except Exception:
                    error_count += 1
                    logger.exception("Failed to send quest reminder to user=%s", uid)

        logger.info(
            "Daily quest reminders sent: %d success, %d errors", sent_count, error_count
        )
        return {"sent": sent_count, "errors": error_count}

    except Exception as exc:
        logger.exception("Failed to send daily quest reminders")
        raise self.retry(exc=exc)
    finally:
        sync_engine.dispose()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def send_streak_reminders(self) -> dict:
    """Send evening reminders to students who haven't completed any activity today.

    Scheduled to run at 6:00 PM IST daily. Targets students with active streaks
    who risk losing them if they don't play today.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models.user import User, UserRole
    from app.models.game import Streak

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_url)

    sent_count = 0
    error_count = 0

    try:
        with Session(sync_engine) as session:
            today = date.today()

            # Find students with active streaks who haven't played today
            streaks = session.execute(
                select(Streak)
                .where(Streak.current_streak > 0)
                .where(Streak.last_activity_date < today)
            ).scalars().all()

            for streak in streaks:
                user = session.execute(
                    select(User).where(User.id == streak.user_id)
                ).scalar_one_or_none()

                if not user or user.role != UserRole.student:
                    continue

                message = (
                    f"Hey {user.name}! "
                    f"You have a {streak.current_streak}-day streak on Prism. "
                    f"Don't let it break — play a quick mission before the day ends!"
                )
                try:
                    _send_whatsapp_message(user.phone, message)
                    sent_count += 1
                except Exception:
                    error_count += 1
                    logger.exception(
                        "Failed to send streak reminder to user=%s", streak.user_id
                    )

        logger.info(
            "Streak reminders sent: %d success, %d errors", sent_count, error_count
        )
        return {"sent": sent_count, "errors": error_count}

    except Exception as exc:
        logger.exception("Failed to send streak reminders")
        raise self.retry(exc=exc)
    finally:
        sync_engine.dispose()
