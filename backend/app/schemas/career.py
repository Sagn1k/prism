from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CareerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    slug: str
    category: str | None = None
    stream_fit: str | None = None
    description: str | None = None
    salary_range: dict | None = None
    entry_paths: dict | None = None
    required_exams: dict | None = None
    college_options: dict | None = None
    day_in_life: dict | None = None


class CareerListResponse(BaseModel):
    careers: list[CareerResponse]
    total: int
    page: int


class CareerBookmarkRequest(BaseModel):
    notes: str | None = None


class CareerRecommendation(BaseModel):
    career: CareerResponse
    match_score: float
