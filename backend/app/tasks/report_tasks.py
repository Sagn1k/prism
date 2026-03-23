import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import insert, select

from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _assemble_report_data(session, student_id: str | None, class_id: str | None) -> dict:
    """Gather spectrum, mission attempts, streaks, and archetype data for the report."""
    from app.models.spectrum import Spectrum
    from app.models.game import MissionAttempt, Streak
    from app.models.user import User
    from app.models.school import ClassStudent

    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "students": []}

    if student_id:
        user_ids = [uuid.UUID(student_id)]
    elif class_id:
        rows = session.execute(
            select(ClassStudent.user_id).where(
                ClassStudent.class_id == uuid.UUID(class_id)
            )
        ).scalars().all()
        user_ids = list(rows)
    else:
        return report

    for uid in user_ids:
        user = session.execute(
            select(User).where(User.id == uid)
        ).scalar_one_or_none()
        if not user:
            continue

        spectrum = session.execute(
            select(Spectrum).where(Spectrum.user_id == uid)
        ).scalar_one_or_none()

        attempts = session.execute(
            select(MissionAttempt).where(MissionAttempt.user_id == uid)
        ).scalars().all()

        streak = session.execute(
            select(Streak).where(Streak.user_id == uid)
        ).scalar_one_or_none()

        student_data = {
            "user_id": str(uid),
            "name": user.name,
            "xp_points": user.xp_points,
            "level": user.level,
            "archetype": user.current_archetype_label,
            "spectrum": {
                "analytical_creative": spectrum.analytical_creative if spectrum else None,
                "builder_explorer": spectrum.builder_explorer if spectrum else None,
                "leader_specialist": spectrum.leader_specialist if spectrum else None,
                "entrepreneur_steward": spectrum.entrepreneur_steward if spectrum else None,
                "people_systems": spectrum.people_systems if spectrum else None,
                "confidence_score": spectrum.confidence_score if spectrum else None,
            },
            "missions_completed": len([a for a in attempts if a.status.value == "completed"]),
            "total_xp_from_missions": sum(a.xp_earned for a in attempts),
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
        }
        report["students"].append(student_data)

    return report


def _generate_pdf(report_data: dict) -> bytes:
    """Placeholder: Generate a PDF from report data.

    In production this will use a library like WeasyPrint or ReportLab
    to render the report as a styled PDF document.
    """
    logger.info("Generating PDF for report (placeholder)")
    return b"%PDF-1.4 placeholder"


def _upload_to_s3(file_bytes: bytes, key: str, content_type: str = "application/pdf") -> str:
    """Placeholder: Upload bytes to S3 and return the public URL."""
    logger.info("Uploading PDF to S3 key=%s (placeholder)", key)
    return f"https://s3.ap-south-1.amazonaws.com/prism-assets/{key}"


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_parent_report(
    self, student_id: str | None = None, class_id: str | None = None
) -> dict:
    """Generate a parent report PDF, upload to S3, and create a parent_report record.

    Must provide either student_id or class_id (not both).

    Returns:
        Dict with report_id and pdf_url.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.models.card import ParentReport

    if not student_id and not class_id:
        raise ValueError("Either student_id or class_id must be provided")

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_url)

    try:
        with Session(sync_engine) as session:
            # 1. Assemble report data
            report_data = _assemble_report_data(session, student_id, class_id)

            # 2. Generate PDF
            pdf_bytes = _generate_pdf(report_data)

            # 3. Upload to S3
            report_id = uuid.uuid4()
            s3_key = f"reports/{report_id.hex}.pdf"
            pdf_url = _upload_to_s3(pdf_bytes, s3_key)

            # 4. Create parent_report records (one per student)
            created_ids = []
            for student in report_data["students"]:
                record = ParentReport(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(student["user_id"]),
                    report_data=report_data,
                    pdf_url=pdf_url,
                )
                session.add(record)
                created_ids.append(str(record.id))

            session.commit()

        logger.info(
            "Parent report generated: student_id=%s class_id=%s pdf_url=%s",
            student_id,
            class_id,
            pdf_url,
        )
        return {
            "report_ids": created_ids,
            "pdf_url": pdf_url,
            "student_count": len(report_data["students"]),
        }

    except Exception as exc:
        logger.exception("Failed to generate parent report")
        raise self.retry(exc=exc)
    finally:
        sync_engine.dispose()
