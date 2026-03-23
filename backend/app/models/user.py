import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    counsellor = "counsellor"
    admin = "admin"
    parent = "parent"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    xp_points: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    current_archetype_label: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    onboarded: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    school = relationship("School", back_populates="users")
    spectrum = relationship("Spectrum", back_populates="user", uselist=False)
    mission_attempts = relationship("MissionAttempt", back_populates="user")
    tot_responses = relationship("TotResponse", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    streak = relationship("Streak", back_populates="user", uselist=False)
    daily_quests = relationship("DailyQuest", back_populates="user")
    career_bookmarks = relationship("CareerBookmark", back_populates="user")
    prism_cards = relationship("PrismCard", back_populates="user")
    ai_conversations = relationship("AIConversation", back_populates="user")
    parent_reports = relationship("ParentReport", back_populates="user")
