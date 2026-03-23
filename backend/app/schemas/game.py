from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    world_id: UUID
    title: str
    type: str
    difficulty: str
    duration_seconds: int | None = None
    content_payload: dict | None = None
    completed: bool = False
    xp_earned: int | None = None


class WorldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    color_hex: str | None = None
    description: str | None = None
    icon_url: str | None = None
    sort_order: int
    mission_count: int
    user_progress: float | None = None


class MissionStartResponse(BaseModel):
    attempt_id: UUID
    id: UUID
    world_id: UUID
    title: str
    type: str
    difficulty: str
    duration_seconds: int | None = None
    content_payload: dict


class MissionSubmitRequest(BaseModel):
    responses: dict
    time_spent: int


class MissionResultResponse(BaseModel):
    scores: dict
    xp_earned: int
    creativity_score: float
    speed_score: float
    accuracy_score: float
    spectrum_update: dict | None = None


class TotResponseItem(BaseModel):
    qid: UUID
    choice: str


class TotSubmitRequest(BaseModel):
    responses: list[TotResponseItem]


class DailyQuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mission: MissionResponse
    quest_date: date
    is_completed: bool
