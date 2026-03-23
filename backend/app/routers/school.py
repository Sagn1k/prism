"""School / Counsellor dashboard router — requires counsellor or admin role."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.school import Class, ClassStudent, School
from app.models.spectrum import Spectrum
from app.models.user import User, UserRole
from app.schemas.school import (
    ClassResponse,
    DashboardResponse,
    ReportGenerateRequest,
    StudentProfileResponse,
)
from app.schemas.spectrum import SpectrumResponse
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/school",
    tags=["school"],
    dependencies=[Depends(require_role("counsellor", "admin"))],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_school_id(user: User, db: AsyncSession) -> uuid.UUID:
    """Resolve the school the counsellor belongs to."""
    if user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a school",
        )
    return user.school_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("counsellor", "admin"))],
):
    """Aggregate stats for the counsellor's school."""
    school_id = await _get_school_id(current_user, db)

    # Total students
    total_q = select(func.count(User.id)).where(
        User.school_id == school_id, User.role == UserRole.student
    )
    total_students = (await db.execute(total_q)).scalar() or 0

    # Active students (active in last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_q = select(func.count(User.id)).where(
        User.school_id == school_id,
        User.role == UserRole.student,
        User.last_active_at >= week_ago,
    )
    active_students = (await db.execute(active_q)).scalar() or 0

    # Average engagement (active / total)
    avg_engagement = round(active_students / total_students, 2) if total_students > 0 else 0.0

    # Archetype distribution
    arch_q = (
        select(User.current_archetype_label, func.count(User.id))
        .where(
            User.school_id == school_id,
            User.role == UserRole.student,
            User.current_archetype_label.is_not(None),
        )
        .group_by(User.current_archetype_label)
    )
    arch_rows = (await db.execute(arch_q)).all()
    archetype_distribution = {label: count for label, count in arch_rows}

    # Stream readiness — count students per stream from classes
    stream_q = (
        select(Class.stream, func.count(ClassStudent.user_id))
        .join(ClassStudent, Class.id == ClassStudent.class_id)
        .where(Class.school_id == school_id, Class.stream.is_not(None))
        .group_by(Class.stream)
    )
    stream_rows = (await db.execute(stream_q)).all()
    stream_readiness = {stream: count for stream, count in stream_rows}

    return DashboardResponse(
        total_students=total_students,
        active_students=active_students,
        avg_engagement=avg_engagement,
        archetype_distribution=archetype_distribution,
        stream_readiness=stream_readiness,
    )


@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("counsellor", "admin"))],
):
    """List classes for the counsellor's school."""
    school_id = await _get_school_id(current_user, db)

    # Classes with student count and avg engagement
    student_count_sq = (
        select(
            ClassStudent.class_id,
            func.count(ClassStudent.user_id).label("student_count"),
        )
        .group_by(ClassStudent.class_id)
        .subquery()
    )

    # Avg engagement: fraction of students active in last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_count_sq = (
        select(
            ClassStudent.class_id,
            func.count(ClassStudent.user_id).label("active_count"),
        )
        .join(User, User.id == ClassStudent.user_id)
        .where(User.last_active_at >= week_ago)
        .group_by(ClassStudent.class_id)
        .subquery()
    )

    stmt = (
        select(
            Class,
            func.coalesce(student_count_sq.c.student_count, 0).label("student_count"),
            func.coalesce(active_count_sq.c.active_count, 0).label("active_count"),
        )
        .outerjoin(student_count_sq, Class.id == student_count_sq.c.class_id)
        .outerjoin(active_count_sq, Class.id == active_count_sq.c.class_id)
        .where(Class.school_id == school_id)
        .order_by(Class.grade, Class.section)
    )
    rows = (await db.execute(stmt)).all()

    return [
        ClassResponse(
            id=cls.id,
            grade=cls.grade,
            section=cls.section or "",
            stream=cls.stream,
            student_count=sc,
            avg_engagement=round(ac / sc, 2) if sc > 0 else 0.0,
        )
        for cls, sc, ac in rows
    ]


@router.get("/students", response_model=dict)
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("counsellor", "admin"))],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    class_id: uuid.UUID | None = Query(None),
    q: str | None = Query(None),
):
    """Paginated student list with spectrum summaries."""
    school_id = await _get_school_id(current_user, db)

    stmt = (
        select(User)
        .outerjoin(Spectrum, Spectrum.user_id == User.id)
        .where(User.school_id == school_id, User.role == UserRole.student)
    )

    if class_id:
        stmt = stmt.join(ClassStudent, ClassStudent.user_id == User.id).where(
            ClassStudent.class_id == class_id
        )
    if q:
        stmt = stmt.where(User.name.ilike(f"%{q}%"))

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    stmt = stmt.options(selectinload(User.spectrum)).order_by(User.name).offset(offset).limit(limit)
    students = (await db.execute(stmt)).scalars().unique().all()

    items = []
    for s in students:
        item = {
            "user": UserResponse.model_validate(s).model_dump(),
            "spectrum_summary": None,
        }
        if s.spectrum:
            item["spectrum_summary"] = {
                "archetype": s.current_archetype_label,
                "confidence": s.spectrum.confidence_score,
                "total_signals": s.spectrum.total_signals,
            }
        items.append(item)

    return {"students": items, "total": total, "page": page}


@router.get("/students/{student_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("counsellor", "admin"))],
):
    """Full student profile visible to counsellor."""
    school_id = await _get_school_id(current_user, db)

    student = (
        await db.execute(
            select(User)
            .options(selectinload(User.spectrum), selectinload(User.badges), selectinload(User.mission_attempts))
            .where(User.id == student_id, User.school_id == school_id, User.role == UserRole.student)
        )
    ).scalar_one_or_none()

    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in your school")

    spectrum_resp = None
    if student.spectrum:
        # Eagerly load archetypes for spectrum
        spec_with_arch = (
            await db.execute(
                select(Spectrum)
                .options(
                    selectinload(Spectrum.primary_archetype),
                    selectinload(Spectrum.secondary_archetype),
                )
                .where(Spectrum.id == student.spectrum.id)
            )
        ).scalar_one()
        spectrum_resp = SpectrumResponse.model_validate(spec_with_arch)

    badges = [
        {"id": str(b.id) if hasattr(b, "id") else None, "badge": getattr(b, "badge_name", None)}
        for b in (student.badges or [])
    ]

    recent_attempts = [
        {
            "mission_id": str(a.mission_id),
            "xp_earned": a.xp_earned,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        }
        for a in sorted(
            (student.mission_attempts or []),
            key=lambda x: x.started_at,
            reverse=True,
        )[:10]
    ]

    return StudentProfileResponse(
        user=UserResponse.model_validate(student),
        spectrum=spectrum_resp,
        badges=badges,
        recent_attempts=recent_attempts,
    )


@router.post("/reports/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    body: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("counsellor", "admin"))],
):
    """Trigger async PDF report generation."""
    school_id = await _get_school_id(current_user, db)

    if body.student_id:
        # Verify student belongs to school
        student = (
            await db.execute(
                select(User).where(
                    User.id == body.student_id,
                    User.school_id == school_id,
                    User.role == UserRole.student,
                )
            )
        ).scalar_one_or_none()
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if body.class_id:
        cls = (
            await db.execute(
                select(Class).where(Class.id == body.class_id, Class.school_id == school_id)
            )
        ).scalar_one_or_none()
        if cls is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Enqueue report generation as a background task
    # In production: from app.services.report_generator import generate_pdf_report
    async def _generate_report():
        # Placeholder: actual implementation calls report_generator service
        pass

    background_tasks.add_task(_generate_report)

    return {
        "ok": True,
        "message": "Report generation started. You will be notified when it is ready.",
        "student_id": str(body.student_id) if body.student_id else None,
        "class_id": str(body.class_id) if body.class_id else None,
    }
