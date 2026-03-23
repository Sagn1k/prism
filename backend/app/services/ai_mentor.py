"""Ray AI Mentor — personalized career guidance powered by Claude."""

import logging
import uuid

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.card import AIConversation, AIMessage
from app.models.spectrum import Archetype, Spectrum

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    return _client


def _build_system_prompt(
    spectrum: Spectrum | None,
    primary_archetype: Archetype | None,
    secondary_archetype: Archetype | None,
) -> str:
    """Build Ray's system prompt with user personality context."""
    base = (
        "You are Ray, a friendly and encouraging AI career mentor for Indian high school "
        "students on the Prism platform. You help students discover their strengths, explore "
        "careers, and make informed decisions about their future.\n\n"
        "Your personality:\n"
        "- Warm, supportive, and genuinely curious about each student\n"
        "- You use simple, relatable language (avoid jargon)\n"
        "- You ask follow-up questions to understand students better\n"
        "- You give practical, actionable advice grounded in the Indian education system\n"
        "- You celebrate strengths rather than highlighting weaknesses\n"
        "- Keep responses concise (2-3 short paragraphs max unless asked for detail)\n"
    )

    if spectrum:
        dims = {
            "analytical_creative": spectrum.analytical_creative,
            "builder_explorer": spectrum.builder_explorer,
            "leader_specialist": spectrum.leader_specialist,
            "entrepreneur_steward": spectrum.entrepreneur_steward,
            "people_systems": spectrum.people_systems,
        }
        non_null = {k: v for k, v in dims.items() if v is not None}
        if non_null:
            base += "\nThis student's Prism Spectrum (trait dimensions, range -1 to 1):\n"
            for dim, val in non_null.items():
                label = dim.replace("_", " ").title()
                base += f"  - {label}: {val:.2f}\n"

        if spectrum.color_ratios:
            base += "\nPrism Colors (personality blend):\n"
            for color, ratio in spectrum.color_ratios.items():
                base += f"  - {color}: {ratio:.0%}\n"

    if primary_archetype:
        base += (
            f"\nPrimary Archetype: {primary_archetype.label}"
            f" {primary_archetype.emoji_icon or ''}\n"
        )
        if primary_archetype.description:
            base += f"  {primary_archetype.description}\n"

    if secondary_archetype:
        base += f"Secondary Archetype: {secondary_archetype.label}\n"

    base += (
        "\nUse this personality context to personalize your advice. Reference their "
        "strengths naturally in conversation. Do not dump all the data back at them — "
        "weave it in organically."
    )
    return base


async def chat(
    db: AsyncSession,
    user_id: uuid.UUID,
    message: str,
    session_id: str,
) -> str:
    """
    Send a message to Ray and get a response.

    Loads user spectrum/archetype context, retrieves conversation history,
    calls Claude API, and persists both messages.
    """
    # Load user's spectrum and archetypes
    result = await db.execute(
        select(Spectrum).where(Spectrum.user_id == user_id)
    )
    spectrum = result.scalar_one_or_none()

    primary_arch = None
    secondary_arch = None
    if spectrum:
        if spectrum.primary_archetype_id:
            r = await db.execute(
                select(Archetype).where(Archetype.id == spectrum.primary_archetype_id)
            )
            primary_arch = r.scalar_one_or_none()
        if spectrum.secondary_archetype_id:
            r = await db.execute(
                select(Archetype).where(Archetype.id == spectrum.secondary_archetype_id)
            )
            secondary_arch = r.scalar_one_or_none()

    system_prompt = _build_system_prompt(spectrum, primary_arch, secondary_arch)

    # Load or create conversation
    conv_result = await db.execute(
        select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.session_id == session_id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if conv is None:
        conv = AIConversation(user_id=user_id, session_id=session_id)
        db.add(conv)
        await db.flush()

    # Load message history
    history_result = await db.execute(
        select(AIMessage)
        .where(AIMessage.conversation_id == conv.id)
        .order_by(AIMessage.created_at.asc())
        .limit(50)
    )
    history = history_result.scalars().all()

    # Build messages list
    messages: list[dict] = []
    for msg in history:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    # Add current user message
    messages.append({"role": "user", "content": message})

    # Call Claude API
    try:
        client = _get_client()
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        assistant_text = response.content[0].text
    except anthropic.APIError as e:
        logger.error("Claude API error: %s", e)
        assistant_text = (
            "I'm having a bit of trouble thinking right now. "
            "Could you try again in a moment?"
        )
    except Exception as e:
        logger.exception("Unexpected error calling Claude API")
        assistant_text = (
            "Something went wrong on my end. Please try again shortly!"
        )

    # Persist both messages
    user_msg = AIMessage(
        conversation_id=conv.id,
        role="user",
        content=message,
    )
    assistant_msg = AIMessage(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_text,
    )
    db.add(user_msg)
    db.add(assistant_msg)

    conv.message_count = (conv.message_count or 0) + 2
    conv.last_message = assistant_text
    await db.flush()

    logger.info(
        "Ray chat: user=%s session=%s messages=%d",
        user_id,
        session_id,
        len(messages),
    )
    return assistant_text
