from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArchetypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    label: str
    description: str | None = None
    emoji_icon: str | None = None


class SpectrumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    analytical_creative: float = 0.0
    builder_explorer: float = 0.0
    leader_specialist: float = 0.0
    entrepreneur_steward: float = 0.0
    people_systems: float = 0.0
    primary_archetype: ArchetypeResponse | None = None
    secondary_archetype: ArchetypeResponse | None = None
    confidence_score: float = 0.0
    color_ratios: dict | None = None
    total_signals: int = 0


class SpectrumHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dimension_snapshot: dict | None = None
    archetype_label: str | None = None
    confidence: float = 0.0
    trigger_event: str | None = None
    recorded_at: datetime
