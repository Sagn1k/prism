"""Identity / Spectrum router — view spectrum and evolution history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.spectrum import Spectrum, SpectrumHistory
from app.models.user import User
from app.schemas.spectrum import SpectrumHistoryResponse, SpectrumResponse

router = APIRouter(prefix="/spectrum", tags=["spectrum"])


@router.get("/me", response_model=SpectrumResponse)
async def get_my_spectrum(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return the current user's full spectrum with archetypes."""
    stmt = (
        select(Spectrum)
        .options(
            selectinload(Spectrum.primary_archetype),
            selectinload(Spectrum.secondary_archetype),
        )
        .where(Spectrum.user_id == current_user.id)
    )
    spectrum = (await db.execute(stmt)).scalar_one_or_none()

    if spectrum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spectrum not yet generated. Complete some missions first!",
        )

    return SpectrumResponse.model_validate(spectrum)


@router.get("/history", response_model=list[SpectrumHistoryResponse])
async def get_spectrum_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Return the spectrum evolution timeline (paginated)."""
    # Get spectrum id
    spectrum = (
        await db.execute(select(Spectrum.id).where(Spectrum.user_id == current_user.id))
    ).scalar_one_or_none()

    if spectrum is None:
        return []

    offset = (page - 1) * limit
    stmt = (
        select(SpectrumHistory)
        .where(SpectrumHistory.spectrum_id == spectrum)
        .order_by(SpectrumHistory.recorded_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()

    return [SpectrumHistoryResponse.model_validate(r) for r in rows]
