import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SchoolTier(str, enum.Enum):
    starter = "starter"
    professional = "professional"
    premium = "premium"


class School(Base):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cbse_affiliation_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[SchoolTier] = mapped_column(
        Enum(SchoolTier, name="school_tier"), nullable=False
    )
    plan_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    student_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subscription_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    subscription_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="school")
    classes = relationship("Class", back_populates="school")


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    grade: Mapped[str] = mapped_column(String(10), nullable=False)
    section: Mapped[str | None] = mapped_column(String(10), nullable=True)
    stream: Mapped[str | None] = mapped_column(String(50), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    school = relationship("School", back_populates="classes")
    students = relationship("ClassStudent", back_populates="class_")


class ClassStudent(Base):
    __tablename__ = "class_students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User")
    class_ = relationship("Class", back_populates="students")
