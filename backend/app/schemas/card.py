from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CardGenerateResponse(BaseModel):
    id: UUID
    image_url: str
    share_token: str


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_version: int
    card_data: dict
    image_url: str | None = None
    share_token: str
    is_public: bool
    generated_at: datetime


class CardPublicResponse(BaseModel):
    card_data: dict
    image_url: str | None = None
    og_title: str | None = None
    og_description: str | None = None
