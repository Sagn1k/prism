import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StreamFit(str, enum.Enum):
    science = "science"
    commerce = "commerce"
    humanities = "humanities"
    any = "any"


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stream_fit: Mapped[StreamFit] = mapped_column(
        Enum(StreamFit, name="stream_fit"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_range: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    entry_paths: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    required_exams: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    college_options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    day_in_life: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    archetype_fit_ids: Mapped[list | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    bookmarks = relationship("CareerBookmark", back_populates="career")


class CareerBookmark(Base):
    __tablename__ = "career_bookmarks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    career_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("careers.id"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="career_bookmarks")
    career = relationship("Career", back_populates="bookmarks")
