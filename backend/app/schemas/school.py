from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.spectrum import SpectrumResponse
from app.schemas.user import UserResponse


class DashboardResponse(BaseModel):
    total_students: int
    active_students: int
    avg_engagement: float
    archetype_distribution: dict
    stream_readiness: dict


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grade: str
    section: str
    stream: str | None = None
    student_count: int
    avg_engagement: float


class StudentProfileResponse(BaseModel):
    user: UserResponse
    spectrum: SpectrumResponse | None = None
    badges: list[dict] = []
    recent_attempts: list[dict] = []


class ReportGenerateRequest(BaseModel):
    student_id: UUID | None = None
    class_id: UUID | None = None
