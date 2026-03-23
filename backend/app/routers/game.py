"""Game router — worlds, missions, This-or-That, daily quests."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.game import (
    AttemptStatus,
    DailyQuest,
    Mission,
    MissionAttempt,
    TotQuestion,
    TotResponse,
    World,
)
from app.models.user import User
from app.schemas.game import (
    DailyQuestResponse,
    MissionResponse,
    MissionResultResponse,
    MissionStartResponse,
    MissionSubmitRequest,
    TotSubmitRequest,
    WorldResponse,
    WorldSwipeRequest,
    WorldSwipeResponse,
)
from app.services.identity_engine import process_mission_signals, DIMENSIONS

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/game", tags=["game"])


@router.get("/worlds", response_model=list[WorldResponse])
async def list_worlds(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
):
    """List all active worlds with mission counts."""
    mission_count_sq = (
        select(Mission.world_id, func.count(Mission.id).label("cnt"))
        .where(Mission.is_active.is_(True))
        .group_by(Mission.world_id)
        .subquery()
    )

    stmt = (
        select(World, func.coalesce(mission_count_sq.c.cnt, 0).label("mission_count"))
        .outerjoin(mission_count_sq, World.id == mission_count_sq.c.world_id)
        .where(World.is_active.is_(True))
        .order_by(World.sort_order)
    )
    rows = (await db.execute(stmt)).all()

    # Calculate user progress per world
    user_progress_map: dict[uuid.UUID, float] = {}
    if current_user:
        for world, mc in rows:
            if mc == 0:
                continue
            completed_count = (
                await db.execute(
                    select(func.count(func.distinct(MissionAttempt.mission_id)))
                    .join(Mission, MissionAttempt.mission_id == Mission.id)
                    .where(
                        MissionAttempt.user_id == current_user.id,
                        MissionAttempt.completed_at.is_not(None),
                        Mission.world_id == world.id,
                    )
                )
            ).scalar() or 0
            user_progress_map[world.id] = completed_count / mc

    return [
        WorldResponse(
            id=world.id,
            name=world.name,
            slug=world.slug,
            color_hex=world.color_hex or "",
            description=world.description,
            icon_url=world.icon_url,
            sort_order=world.sort_order,
            mission_count=mission_count,
            user_progress=user_progress_map.get(world.id),
        )
        for world, mission_count in rows
    ]


# World slug -> trait dimension signals for right-swipe (interest).
# Left-swipe sends the negation of these signals.
WORLD_TRAIT_MAP: dict[str, dict[str, float]] = {
    "space-lab": {"builder_explorer": 0.4, "analytical_creative": -0.2},
    "creator-studio": {"analytical_creative": 0.5, "people_systems": 0.15},
    "code-dungeon": {"analytical_creative": -0.5, "builder_explorer": -0.2},
    "market-arena": {"entrepreneur_steward": 0.5, "leader_specialist": 0.3},
}


@router.post("/worlds/{world_id}/swipe", response_model=WorldSwipeResponse)
async def swipe_world(
    world_id: uuid.UUID,
    body: WorldSwipeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Record a world swipe as a soft identity signal."""
    if body.direction not in ("left", "right"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="direction must be 'left' or 'right'",
        )

    world = (
        await db.execute(select(World).where(World.id == world_id))
    ).scalar_one_or_none()
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")

    trait_signals = WORLD_TRAIT_MAP.get(world.slug, {})
    if trait_signals:
        # Right swipe = interested -> positive signal; left = negate
        multiplier = 1.0 if body.direction == "right" else -1.0
        # Low weight since this is an implicit/soft signal
        soft_signals = {dim: val * multiplier * 0.3 for dim, val in trait_signals.items()}

        from app.services.identity_engine import process_signal, recalculate_spectrum

        await process_signal(db, current_user.id, soft_signals, source=f"world_swipe:{world.slug}")
        await recalculate_spectrum(db, current_user.id)

    return WorldSwipeResponse(ok=True, world_id=world_id, direction=body.direction)


@router.get("/worlds/{world_id}/missions", response_model=list[MissionResponse])
async def list_missions(
    world_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
    type: str | None = Query(None, description="Filter by mission type"),
):
    """List missions for a given world, optionally filtered by type."""
    world = (await db.execute(select(World).where(World.id == world_id))).scalar_one_or_none()
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="World not found")

    stmt = select(Mission).where(Mission.world_id == world_id, Mission.is_active.is_(True))
    if type:
        stmt = stmt.where(Mission.type == type)
    stmt = stmt.order_by(Mission.sort_order)

    missions = (await db.execute(stmt)).scalars().all()

    # Build completion map for current user
    completed_map: dict[uuid.UUID, int] = {}
    if current_user:
        completed_attempts = (
            await db.execute(
                select(MissionAttempt.mission_id, MissionAttempt.xp_earned)
                .where(
                    MissionAttempt.user_id == current_user.id,
                    MissionAttempt.completed_at.is_not(None),
                    MissionAttempt.mission_id.in_([m.id for m in missions]),
                )
            )
        ).all()
        for mission_id, xp in completed_attempts:
            completed_map[mission_id] = xp or 0

    return [
        MissionResponse(
            id=m.id,
            world_id=m.world_id,
            title=m.title,
            type=m.type.value if hasattr(m.type, "value") else str(m.type),
            difficulty=m.difficulty.value if hasattr(m.difficulty, "value") else str(m.difficulty),
            duration_seconds=m.duration_seconds or 300,
            content_payload=m.content_payload or {},
            completed=m.id in completed_map,
            xp_earned=completed_map.get(m.id),
        )
        for m in missions
    ]


@router.post("/missions/{mission_id}/start", response_model=MissionStartResponse)
async def start_mission(
    mission_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new mission attempt and return content payload."""
    mission = (await db.execute(select(Mission).where(Mission.id == mission_id, Mission.is_active.is_(True)))).scalar_one_or_none()
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")

    # Check if already completed
    already_completed = (
        await db.execute(
            select(MissionAttempt).where(
                MissionAttempt.user_id == current_user.id,
                MissionAttempt.mission_id == mission_id,
                MissionAttempt.completed_at.is_not(None),
            ).limit(1)
        )
    ).scalar_one_or_none()

    if already_completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mission already completed",
        )

    # Check for an existing in-progress attempt (limit 1 to handle race conditions from double-mounts)
    existing = (
        await db.execute(
            select(MissionAttempt).where(
                MissionAttempt.user_id == current_user.id,
                MissionAttempt.mission_id == mission_id,
                MissionAttempt.completed_at.is_(None),
            ).order_by(MissionAttempt.started_at.desc()).limit(1)
        )
    ).scalar_one_or_none()

    def _build_start_response(attempt_id: uuid.UUID) -> MissionStartResponse:
        return MissionStartResponse(
            attempt_id=attempt_id,
            id=mission.id,
            world_id=mission.world_id,
            title=mission.title,
            type=mission.type.value if hasattr(mission.type, "value") else str(mission.type),
            difficulty=mission.difficulty.value if hasattr(mission.difficulty, "value") else str(mission.difficulty),
            duration_seconds=mission.duration_seconds or 300,
            content_payload=mission.content_payload or {},
        )

    if existing:
        return _build_start_response(existing.id)

    attempt = MissionAttempt(user_id=current_user.id, mission_id=mission_id)
    db.add(attempt)
    await db.flush()

    return _build_start_response(attempt.id)


@router.post("/missions/{mission_id}/submit", response_model=MissionResultResponse)
async def submit_mission(
    mission_id: uuid.UUID,
    body: MissionSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Score a mission attempt, award XP, and trigger identity engine."""
    # Find open attempt (use limit 1 to handle duplicate rows from race conditions)
    attempt = (
        await db.execute(
            select(MissionAttempt).where(
                MissionAttempt.user_id == current_user.id,
                MissionAttempt.mission_id == mission_id,
                MissionAttempt.completed_at.is_(None),
            ).order_by(MissionAttempt.started_at.desc()).limit(1)
        )
    ).scalar_one_or_none()

    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open attempt found for this mission")

    mission = (await db.execute(select(Mission).where(Mission.id == mission_id))).scalar_one()

    # --- Scoring ---
    max_time = mission.duration_seconds or 300
    speed_score = max(0.0, min(1.0, 1.0 - (body.time_spent / (max_time * 1.5))))
    accuracy_score = 0.7  # Placeholder
    creativity_score = 0.5  # Placeholder
    xp_earned = int(10 * (0.4 * accuracy_score + 0.3 * speed_score + 0.3 * creativity_score))

    scores = {
        "accuracy": accuracy_score,
        "speed": speed_score,
        "creativity": creativity_score,
    }

    attempt.responses = body.responses
    attempt.scores = scores
    attempt.xp_earned = xp_earned
    attempt.creativity_score = creativity_score
    attempt.speed_score = speed_score
    attempt.accuracy_score = accuracy_score
    attempt.time_spent_sec = body.time_spent
    attempt.status = AttemptStatus.completed
    attempt.completed_at = datetime.now(timezone.utc)

    # Award XP to user
    current_user.xp_points += xp_earned
    current_user.level = (current_user.xp_points // 100) + 1

    await db.flush()

    # --- Trigger identity engine ---
    spectrum_update: dict | None = None
    try:
        spectrum = await process_mission_signals(db, current_user.id, attempt)
        # Build spectrum delta for response
        spectrum_update = {
            dim: round(getattr(spectrum, dim) or 0.0, 3)
            for dim in DIMENSIONS
        }
        # Update user's archetype label
        if spectrum.primary_archetype_id:
            from app.models.spectrum import Archetype
            arch = (await db.execute(
                select(Archetype).where(Archetype.id == spectrum.primary_archetype_id)
            )).scalar_one_or_none()
            if arch:
                current_user.current_archetype_label = arch.label

        await db.flush()
    except Exception as exc:
        # Don't fail the submission if identity engine errors
        import logging
        import traceback
        logging.getLogger(__name__).error("Identity engine error: %s\n%s", exc, traceback.format_exc())

    return MissionResultResponse(
        scores=scores,
        xp_earned=xp_earned,
        creativity_score=creativity_score,
        speed_score=speed_score,
        accuracy_score=accuracy_score,
        spectrum_update=spectrum_update,
    )


@router.post("/tot/submit-batch")
async def submit_tot_batch(
    body: TotSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Bulk submit This-or-That responses and trigger identity engine."""
    if not body.responses:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No responses provided")

    question_ids = [r.qid for r in body.responses]
    existing_qs = (
        await db.execute(
            select(TotQuestion.id).where(TotQuestion.id.in_(question_ids), TotQuestion.is_active.is_(True))
        )
    ).scalars().all()
    existing_set = set(existing_qs)

    created = 0
    for item in body.responses:
        if item.qid not in existing_set:
            continue
        if item.choice not in ("a", "b"):
            continue
        resp = TotResponse(
            user_id=current_user.id,
            question_id=item.qid,
            chosen_option=item.choice,
        )
        db.add(resp)
        created += 1

    await db.flush()

    return {"ok": True, "recorded": created}


@router.get("/daily-quest", response_model=DailyQuestResponse)
async def get_daily_quest(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get today's daily quest for the current user, creating one if needed."""
    today = date.today()

    stmt = (
        select(DailyQuest)
        .options(selectinload(DailyQuest.mission))
        .where(DailyQuest.user_id == current_user.id, DailyQuest.quest_date == today)
    )
    quest = (await db.execute(stmt)).scalar_one_or_none()

    if quest is not None:
        return DailyQuestResponse(
            id=quest.id,
            mission=MissionResponse(
                id=quest.mission.id,
                world_id=quest.mission.world_id,
                title=quest.mission.title,
                type=quest.mission.type.value if hasattr(quest.mission.type, "value") else str(quest.mission.type),
                difficulty=quest.mission.difficulty.value if hasattr(quest.mission.difficulty, "value") else str(quest.mission.difficulty),
                duration_seconds=quest.mission.duration_seconds or 300,
                content_payload=quest.mission.content_payload or {},
            ),
            quest_date=quest.quest_date,
            is_completed=quest.is_completed,
        )

    # Pick a random mission the user hasn't completed recently
    completed_ids_sq = (
        select(MissionAttempt.mission_id)
        .where(MissionAttempt.user_id == current_user.id, MissionAttempt.completed_at.is_not(None))
        .subquery()
    )
    mission = (
        await db.execute(
            select(Mission)
            .where(Mission.is_active.is_(True), Mission.id.notin_(select(completed_ids_sq)))
            .order_by(func.random())
            .limit(1)
        )
    ).scalar_one_or_none()

    if mission is None:
        mission = (
            await db.execute(select(Mission).where(Mission.is_active.is_(True)).order_by(func.random()).limit(1))
        ).scalar_one_or_none()

    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No missions available for daily quest")

    quest = DailyQuest(user_id=current_user.id, mission_id=mission.id, quest_date=today)
    db.add(quest)
    await db.flush()
    await db.refresh(quest, attribute_names=["mission"])

    return DailyQuestResponse(
        id=quest.id,
        mission=MissionResponse(
            id=quest.mission.id,
            world_id=quest.mission.world_id,
            title=quest.mission.title,
            type=quest.mission.type.value if hasattr(quest.mission.type, "value") else str(quest.mission.type),
            difficulty=quest.mission.difficulty.value if hasattr(quest.mission.difficulty, "value") else str(quest.mission.difficulty),
            duration_seconds=quest.mission.duration_seconds or 300,
            content_payload=quest.mission.content_payload or {},
        ),
        quest_date=quest.quest_date,
        is_completed=quest.is_completed,
    )
