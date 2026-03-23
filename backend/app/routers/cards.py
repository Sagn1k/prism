"""Prism Cards router — generate, list, public share."""

from __future__ import annotations

import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.card import PrismCard
from app.models.spectrum import Spectrum
from app.models.user import User
from app.schemas.card import CardGenerateResponse, CardPublicResponse, CardResponse

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("/generate", response_model=CardGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate_card(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Generate a new Prism Card from the user's current spectrum."""
    spectrum = (
        await db.execute(select(Spectrum).where(Spectrum.user_id == current_user.id))
    ).scalar_one_or_none()

    if spectrum is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No spectrum data found — complete some missions first",
        )

    # Determine version number
    last_card = (
        await db.execute(
            select(PrismCard.card_version)
            .where(PrismCard.user_id == current_user.id)
            .order_by(PrismCard.card_version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    version = (last_card or 0) + 1

    # Resolve primary archetype details
    from app.models.spectrum import Archetype
    primary_arch_data = None
    if spectrum.primary_archetype_id:
        arch = (await db.execute(
            select(Archetype).where(Archetype.id == spectrum.primary_archetype_id)
        )).scalar_one_or_none()
        if arch:
            primary_arch_data = {
                "label": arch.label,
                "emoji_icon": arch.emoji_icon,
                "description": arch.description,
            }

    card_data = {
        "name": current_user.name,
        "level": current_user.level,
        "xp_points": current_user.xp_points,
        "archetype": current_user.current_archetype_label,
        "primary_archetype": primary_arch_data,
        "dimensions": {
            "analytical_creative": spectrum.analytical_creative,
            "builder_explorer": spectrum.builder_explorer,
            "leader_specialist": spectrum.leader_specialist,
            "entrepreneur_steward": spectrum.entrepreneur_steward,
            "people_systems": spectrum.people_systems,
        },
        "color_ratios": spectrum.color_ratios,
        "confidence": spectrum.confidence_score,
        "total_signals": spectrum.total_signals,
        "version": version,
    }

    share_token = secrets.token_urlsafe(32)
    image_url = None  # Populated asynchronously by card generator

    og_title = f"{current_user.name}'s Prism Card"
    og_desc = f"Archetype: {current_user.current_archetype_label or 'Discovering...'}"

    card = PrismCard(
        user_id=current_user.id,
        card_version=version,
        card_data=card_data,
        image_url=image_url,
        share_token=share_token,
        is_public=True,
        og_title=og_title,
        og_description=og_desc,
    )
    db.add(card)
    await db.flush()

    return CardGenerateResponse(id=card.id, image_url=image_url or "", share_token=share_token)


@router.get("/me", response_model=list[CardResponse])
async def list_my_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all Prism Cards for the current user."""
    stmt = (
        select(PrismCard)
        .where(PrismCard.user_id == current_user.id)
        .order_by(PrismCard.generated_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [CardResponse.model_validate(c) for c in rows]


@router.get("/{share_token}", response_model=CardPublicResponse)
async def get_public_card(
    share_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """PUBLIC endpoint — return card data for the sharing page (no auth required)."""
    card = (
        await db.execute(
            select(PrismCard).where(PrismCard.share_token == share_token, PrismCard.is_public.is_(True))
        )
    ).scalar_one_or_none()

    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

    return CardPublicResponse(
        card_data=card.card_data,
        image_url=card.image_url,
        og_title=card.og_title,
        og_description=card.og_description,
    )
