"""
api/routers/admin.py

Admin endpoints for reviewing safety flags and system health.
Protected by admin authentication.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user, require_admin
from core.database import get_db
from db.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["Admin"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SafetyFlagResponse(BaseModel):
    id: str
    user_id: str
    source_type: str
    flag_type: str
    severity: int = Field(ge=1, le=10)
    excerpt: str
    ai_response: str
    resources_shown: bool
    reviewed: bool
    created_at: str
    
    class Config:
        from_attributes = True


class SafetyFlagReviewRequest(BaseModel):
    reviewed: bool = True
    notes: Optional[str] = None


class SafetyStatsResponse(BaseModel):
    total_flags: int
    unreviewed_flags: int
    crisis_flags: int
    distress_flags: int
    last_24h: int


# ─── Safety Flag Endpoints ────────────────────────────────────────────────────

@router.get(
    "/safety-flags",
    response_model=List[SafetyFlagResponse],
    summary="List safety flags with filtering",
)
async def list_safety_flags(
    reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    flag_type: Optional[str] = Query(None, description="Filter by type (crisis, distress)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[SafetyFlagResponse]:
    """
    List safety flags for admin review.
    
    Query parameters:
    - reviewed: true/false (default: all)
    - flag_type: crisis, distress (default: all)
    - limit: number of results (1-100, default 50)
    - offset: pagination offset
    """
    
    # Build query dynamically
    conditions = ["1=1"]
    params = {"limit": limit, "offset": offset}
    
    if reviewed is not None:
        conditions.append("reviewed = :reviewed")
        params["reviewed"] = reviewed
    
    if flag_type:
        conditions.append("flag_type = :flag_type")
        params["flag_type"] = flag_type
    
    where_clause = " AND ".join(conditions)
    
    result = await db.execute(
        text(f"""
            SELECT 
                id, user_id, source_type, flag_type, severity,
                excerpt, ai_response, resources_shown, reviewed, created_at
            FROM ai_safety_flags
            WHERE {where_clause}
            ORDER BY 
                CASE WHEN reviewed = FALSE THEN 0 ELSE 1 END,
                severity DESC,
                created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    
    flags = []
    for row in result.fetchall():
        flags.append(SafetyFlagResponse(
            id=str(row.id),
            user_id=str(row.user_id),
            source_type=row.source_type,
            flag_type=row.flag_type,
            severity=row.severity,
            excerpt=row.excerpt or "",
            ai_response=row.ai_response or "",
            resources_shown=row.resources_shown,
            reviewed=row.reviewed,
            created_at=str(row.created_at),
        ))
    
    logger.info(
        "safety_flags_listed",
        admin_id=str(current_user.id),
        count=len(flags),
        filters={"reviewed": reviewed, "flag_type": flag_type},
    )
    
    return flags


@router.get(
    "/safety-flags/stats",
    response_model=SafetyStatsResponse,
    summary="Get safety flag statistics",
)
async def get_safety_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SafetyStatsResponse:
    """Get summary statistics of safety flags."""
    
    result = await db.execute(
        text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE reviewed = FALSE) as unreviewed,
                COUNT(*) FILTER (WHERE flag_type = 'crisis') as crisis,
                COUNT(*) FILTER (WHERE flag_type = 'distress') as distress,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h
            FROM ai_safety_flags
        """)
    )
    
    row = result.fetchone()
    
    return SafetyStatsResponse(
        total_flags=row.total or 0,
        unreviewed_flags=row.unreviewed or 0,
        crisis_flags=row.crisis or 0,
        distress_flags=row.distress or 0,
        last_24h=row.last_24h or 0,
    )


@router.post(
    "/safety-flags/{flag_id}/review",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark a safety flag as reviewed",
)
async def review_safety_flag(
    flag_id: str,
    request: SafetyFlagReviewRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Mark a safety flag as reviewed with optional notes."""
    
    # Check if flag exists
    result = await db.execute(
        text("SELECT id FROM ai_safety_flags WHERE id = :flag_id"),
        {"flag_id": flag_id},
    )
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safety flag not found",
        )
    
    # Update the flag
    await db.execute(
        text("""
            UPDATE ai_safety_flags
            SET reviewed = :reviewed,
                reviewed_at = CASE WHEN :reviewed THEN NOW() ELSE NULL END,
                reviewed_by = CASE WHEN :reviewed THEN :admin_id ELSE NULL END,
                notes = COALESCE(:notes, notes)
            WHERE id = :flag_id
        """),
        {
            "flag_id": flag_id,
            "reviewed": request.reviewed,
            "admin_id": str(current_user.id),
            "notes": request.notes,
        },
    )
    
    logger.info(
        "safety_flag_reviewed",
        flag_id=flag_id,
        admin_id=str(current_user.id),
        reviewed=request.reviewed,
    )


@router.get(
    "/safety-flags/unreviewed-count",
    summary="Get count of unreviewed flags",
)
async def get_unreviewed_count(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Quick endpoint for dashboard badge."""
    
    result = await db.execute(
        text("""
            SELECT COUNT(*) as count
            FROM ai_safety_flags
            WHERE reviewed = FALSE
        """)
    )
    
    return {"unreviewed_count": result.scalar() or 0}


@router.post(
    "/dry-run/initial-tasks/{user_id}",
    summary="Generate a user's first three tasks without saving them",
)
async def dry_run_initial_tasks(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Runs the activation batch (generate_initial_tasks) in dry-run mode for an
    existing user and returns the three tasks. No daily_tasks rows are
    written. OpenAI usage is still recorded in ai_interactions as normal.
    """
    from ai.engines.task_generator import TaskGeneratorEngine

    engine = TaskGeneratorEngine()
    tasks = await engine.generate_initial_tasks(user_id, db, dry_run=True)
    await db.rollback()  # belt and braces: nothing in a dry run should be committed
    logger.info("dry_run_initial_tasks", admin_id=str(current_user.id), user_id=user_id, count=len(tasks))
    return {
        "user_id": user_id,
        "tasks": [
            {
                "scheduled_date": t.get("scheduled_date"),
                "title": t.get("title"),
                "task_type": t.get("task_type"),
                "domain": t.get("domain"),
                "time_estimate_minutes": t.get("time_estimate_minutes"),
                "fallback": bool(t.get("fallback")),
                "rejected_reasons": t.get("rejected_reasons", []),
            }
            for t in tasks
        ],
    }


@router.post(
    "/dry-run/interview-extraction/{user_id}",
    summary="Re-run interview profile extraction on a stored transcript without saving",
)
async def dry_run_interview_extraction(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Before/after for the interview extractor: returns what is stored for this
    user's interview and what the current extractor reads from the same
    transcript, plus the essential fields each leaves empty. Writes nothing
    (OpenAI usage is still recorded in ai_interactions as normal).
    """
    from ai.engines.interview import InterviewEngine

    row = (await db.execute(
        text("SELECT messages, extracted_data FROM onboarding_interview_state WHERE user_id = CAST(:uid AS uuid)"),
        {"uid": user_id},
    )).first()
    if not row or not row[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No interview transcript for this user")

    engine = InterviewEngine()
    stored = {k: v for k, v in (row[1] or {}).items() if not k.startswith("_")}
    new = engine._merge_extractions({}, await engine._extract_data(messages=row[0], current_extracted={}, user_id=user_id))
    await db.rollback()
    logger.info("dry_run_interview_extraction", admin_id=str(current_user.id), user_id=user_id)
    return {
        "user_id": user_id,
        "before": stored,
        "before_missing_essentials": engine._missing_essentials(stored),
        "after": new,
        "after_missing_essentials": engine._missing_essentials(new),
    }
