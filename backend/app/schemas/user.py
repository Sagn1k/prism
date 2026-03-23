from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str | None = None
    email: str | None = None
    role: str
    avatar_url: str | None = None
    xp_points: int
    level: int
    current_archetype_label: str | None = None
    onboarded: bool
    school_id: UUID | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
