"""Prism Card generation — assembles and stores shareable identity cards."""

import logging
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import PrismCard
from app.models.game import Badge, UserBadge
from app.models.spectrum import Archetype, Spectrum
from app.models.user import User

logger = logging.getLogger(__name__)


def generate_share_token() -> str:
    """Generate a random 32-character URL-safe token."""
    return secrets.token_urlsafe(24)[:32]


async def generate_card(db: AsyncSession, user_id: uuid.UUID) -> PrismCard:
    """
    Assemble a Prism Card with the user's identity data.

    Gathers spectrum, archetype, badges, level, XP, and name,
    then stores a card_data JSON for frontend rendering.
    """
    # Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    # Fetch spectrum
    spec_result = await db.execute(
        select(Spectrum).where(Spectrum.user_id == user_id)
    )
    spectrum = spec_result.scalar_one_or_none()

    # Fetch archetypes
    primary_archetype = None
    secondary_archetype = None
    if spectrum:
        if spectrum.primary_archetype_id:
            r = await db.execute(
                select(Archetype).where(Archetype.id == spectrum.primary_archetype_id)
            )
            primary_archetype = r.scalar_one_or_none()
        if spectrum.secondary_archetype_id:
            r = await db.execute(
                select(Archetype).where(
                    Archetype.id == spectrum.secondary_archetype_id
                )
            )
            secondary_archetype = r.scalar_one_or_none()

    # Fetch badges
    badge_result = await db.execute(
        select(Badge)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id)
    )
    badges = badge_result.scalars().all()

    # Build card data
    card_data: dict = {
        "name": user.name,
        "level": user.level,
        "xp_points": user.xp_points,
        "avatar_url": user.avatar_url,
        "spectrum": None,
        "primary_archetype": None,
        "secondary_archetype": None,
        "color_ratios": None,
        "badges": [
            {
                "name": b.name,
                "description": b.description,
                "icon_url": b.icon_url,
            }
            for b in badges
        ],
    }

    if spectrum:
        card_data["spectrum"] = {
            "analytical_creative": spectrum.analytical_creative,
            "builder_explorer": spectrum.builder_explorer,
            "leader_specialist": spectrum.leader_specialist,
            "entrepreneur_steward": spectrum.entrepreneur_steward,
            "people_systems": spectrum.people_systems,
        }
        card_data["color_ratios"] = spectrum.color_ratios
        card_data["confidence_score"] = spectrum.confidence_score

    if primary_archetype:
        card_data["primary_archetype"] = {
            "name": primary_archetype.name,
            "label": primary_archetype.label,
            "emoji_icon": primary_archetype.emoji_icon,
            "description": primary_archetype.description,
        }

    if secondary_archetype:
        card_data["secondary_archetype"] = {
            "name": secondary_archetype.name,
            "label": secondary_archetype.label,
            "emoji_icon": secondary_archetype.emoji_icon,
        }

    # Create card record
    share_token = generate_share_token()
    card = PrismCard(
        user_id=user_id,
        card_data=card_data,
        share_token=share_token,
        is_public=False,
    )
    db.add(card)
    await db.flush()

    logger.info("Generated Prism Card for user %s (token=%s)", user_id, share_token)
    return card
