import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Archetype(Base):
    __tablename__ = "archetypes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    emoji_icon: Mapped[str | None] = mapped_column(String(10), nullable=True)
    trait_ranges: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    color_weights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Spectrum(Base):
    __tablename__ = "spectrums"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    analytical_creative: Mapped[float | None] = mapped_column(Float, nullable=True)
    builder_explorer: Mapped[float | None] = mapped_column(Float, nullable=True)
    leader_specialist: Mapped[float | None] = mapped_column(Float, nullable=True)
    entrepreneur_steward: Mapped[float | None] = mapped_column(Float, nullable=True)
    people_systems: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_archetype_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("archetypes.id"), nullable=True
    )
    secondary_archetype_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("archetypes.id"), nullable=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    color_ratios: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_signals: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="spectrum")
    primary_archetype = relationship("Archetype", foreign_keys=[primary_archetype_id])
    secondary_archetype = relationship(
        "Archetype", foreign_keys=[secondary_archetype_id]
    )
    history = relationship("SpectrumHistory", back_populates="spectrum")


class SpectrumHistory(Base):
    __tablename__ = "spectrum_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    spectrum_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spectrums.id"), nullable=False
    )
    dimension_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    archetype_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    trigger_event: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    spectrum = relationship("Spectrum", back_populates="history")
