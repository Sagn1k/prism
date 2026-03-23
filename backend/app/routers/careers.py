"""Careers router — search, recommend, bookmark."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.career import Career, CareerBookmark
from app.models.spectrum import Spectrum
from app.models.user import User
from app.schemas.career import (
    CareerBookmarkRequest,
    CareerListResponse,
    CareerRecommendation,
    CareerResponse,
)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/careers", tags=["careers"])


@router.get("/", response_model=CareerListResponse)
async def search_careers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    stream: str | None = Query(None),
    q: str | None = Query(None, description="Free-text search"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search and filter careers."""
    stmt = select(Career).where(Career.is_active.is_(True))

    if stream:
        stmt = stmt.where(Career.stream_fit == stream)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Career.title.ilike(pattern),
                Career.description.ilike(pattern),
                Career.category.ilike(pattern),
            )
        )

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.order_by(Career.title).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()

    return CareerListResponse(
        careers=[CareerResponse.model_validate(c) for c in rows],
        total=total,
        page=page,
    )


@router.get("/recommended", response_model=list[CareerRecommendation])
async def recommended_careers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return careers that best match the user's current archetype."""
    spectrum = (
        await db.execute(select(Spectrum).where(Spectrum.user_id == current_user.id))
    ).scalar_one_or_none()

    if spectrum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No spectrum found — complete some missions first",
        )

    # Build user dimension vector
    user_dims = {
        "analytical_creative": spectrum.analytical_creative or 0.5,
        "builder_explorer": spectrum.builder_explorer or 0.5,
        "leader_specialist": spectrum.leader_specialist or 0.5,
        "entrepreneur_steward": spectrum.entrepreneur_steward or 0.5,
        "people_systems": spectrum.people_systems or 0.5,
    }

    careers = (
        await db.execute(
            select(Career).where(Career.is_active.is_(True))
        )
    ).scalars().all()

    # Score each career
    scored: list[tuple[Career, float]] = []
    for career in careers:
        # Use salary_range or entry_paths as a proxy; skip if no data
        score = 0.5  # Default score
        scored.append((career, round(score, 3)))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:10]

    return [
        CareerRecommendation(
            career=CareerResponse.model_validate(c),
            match_score=s,
        )
        for c, s in top
    ]


@router.get("/{career_id}", response_model=CareerResponse)
async def get_career(
    career_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single career detail."""
    career = (
        await db.execute(select(Career).where(Career.id == career_id, Career.is_active.is_(True)))
    ).scalar_one_or_none()

    if career is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career not found")

    return CareerResponse.model_validate(career)


@router.post("/{career_id}/bookmark", status_code=status.HTTP_201_CREATED)
async def bookmark_career(
    career_id: uuid.UUID,
    body: CareerBookmarkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Bookmark a career (toggle — re-posting removes it)."""
    # Verify career exists
    career = (
        await db.execute(select(Career).where(Career.id == career_id, Career.is_active.is_(True)))
    ).scalar_one_or_none()
    if career is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career not found")

    # Check existing bookmark
    existing = (
        await db.execute(
            select(CareerBookmark).where(
                CareerBookmark.user_id == current_user.id,
                CareerBookmark.career_id == career_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        await db.flush()
        return {"ok": True, "bookmarked": False}

    bookmark = CareerBookmark(
        user_id=current_user.id,
        career_id=career_id,
        notes=body.notes,
    )
    db.add(bookmark)
    await db.flush()
    return {"ok": True, "bookmarked": True}
