import logging
import os
import uuid

from sqlalchemy import update

from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _render_card_image(card_id: str) -> bytes:
    """Placeholder: Use Playwright to render the Prism card as a PNG screenshot."""
    logger.info("Rendering card image for card_id=%s (placeholder)", card_id)
    return b"<placeholder-png-bytes>"


def _upload_to_s3(file_bytes: bytes, key: str, content_type: str = "image/png") -> str:
    """Upload bytes to S3 and return the public URL."""
    from app.config import get_settings

    settings = get_settings()
    import boto3

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        region_name=settings.S3_REGION,
    )
    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"


def _save_local(file_bytes: bytes, key: str) -> str:
    """Save file to local storage directory (dev mode)."""
    from app.config import get_settings

    settings = get_settings()
    storage_path = settings.LOCAL_STORAGE_PATH
    full_path = os.path.join(storage_path, key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(file_bytes)
    logger.info("Saved locally: %s", full_path)
    return f"/static/{key}"


def _upload_file(file_bytes: bytes, key: str, content_type: str = "image/png") -> str:
    """Route to local storage in dev, S3 in prod."""
    from app.config import get_settings

    settings = get_settings()
    if settings.APP_ENV == "development" or not settings.AWS_ACCESS_KEY:
        return _save_local(file_bytes, key)
    return _upload_to_s3(file_bytes, key, content_type)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def generate_card_image(self, card_id: str) -> dict:
    """Generate a Prism card image, upload/save, and update the database record."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.database import Base

    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    sync_engine = create_engine(sync_url)

    try:
        image_bytes = _render_card_image(card_id)
        s3_key = f"cards/{card_id}/{uuid.uuid4().hex}.png"
        image_url = _upload_file(image_bytes, s3_key)

        prism_cards = Base.metadata.tables.get("prism_cards")
        if prism_cards is not None:
            with Session(sync_engine) as session:
                session.execute(
                    update(prism_cards)
                    .where(prism_cards.c.id == uuid.UUID(card_id))
                    .values(image_url=image_url)
                )
                session.commit()

        logger.info("Card image generated: card_id=%s url=%s", card_id, image_url)
        return {"card_id": card_id, "image_url": image_url}

    except Exception as exc:
        logger.exception("Failed to generate card image for card_id=%s", card_id)
        raise self.retry(exc=exc)
    finally:
        sync_engine.dispose()
