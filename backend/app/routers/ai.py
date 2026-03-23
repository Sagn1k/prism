"""AI / Ray mentor router — chat, conversation history."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.card import AIConversation, AIMessage
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse, ConversationListResponse, ConversationPreview

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
):
    """Send a message to Ray AI mentor and return the response.

    Works for both authenticated and unauthenticated users. Unauthenticated
    users get a generic system prompt without spectrum data and conversations
    are not persisted.
    """
    from app.services.ai_mentor import chat as ai_chat, _build_system_prompt, _get_client

    if current_user is not None:
        # Authenticated path — persist conversation and use personalized prompt
        if body.session_id:
            conv = (
                await db.execute(
                    select(AIConversation).where(
                        AIConversation.session_id == body.session_id,
                        AIConversation.user_id == current_user.id,
                    )
                )
            ).scalar_one_or_none()
            if conv is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        else:
            session_id = uuid.uuid4().hex
            conv = AIConversation(user_id=current_user.id, session_id=session_id)
            db.add(conv)
            await db.flush()

        ai_text = await ai_chat(db, current_user.id, body.message, conv.session_id)

        return ChatResponse(message=ai_text, session_id=conv.session_id)
    else:
        # Unauthenticated path — no persistence, generic prompt
        import anthropic
        import logging
        from app.config import settings

        logger = logging.getLogger(__name__)
        system_prompt = _build_system_prompt(None, None, None)
        session_id = body.session_id or uuid.uuid4().hex

        try:
            client = _get_client()
            response = await client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": body.message}],
            )
            ai_text = response.content[0].text
        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            ai_text = (
                "I'm having a bit of trouble thinking right now. "
                "Could you try again in a moment?"
            )
        except Exception:
            logger.exception("Unexpected error calling Claude API")
            ai_text = (
                "Something went wrong on my end. Please try again shortly!"
            )

        return ChatResponse(message=ai_text, session_id=session_id)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all conversation sessions for the current user."""
    stmt = (
        select(AIConversation)
        .where(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.updated_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    return ConversationListResponse(
        sessions=[ConversationPreview.model_validate(r) for r in rows]
    )


@router.get("/conversations/{session_id}")
async def get_conversation(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get full conversation history for a session."""
    conv = (
        await db.execute(
            select(AIConversation)
            .where(
                AIConversation.session_id == session_id,
                AIConversation.user_id == current_user.id,
            )
        )
    ).scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = (
        await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.created_at)
        )
    ).scalars().all()

    return {
        "session_id": conv.session_id,
        "created_at": conv.created_at.isoformat(),
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ],
    }
