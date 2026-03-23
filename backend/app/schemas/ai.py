from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str


class ConversationPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    last_message: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    sessions: list[ConversationPreview]
