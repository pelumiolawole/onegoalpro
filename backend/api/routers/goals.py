"""
api/routers/goals.py

Goal management endpoints.

GET  /goals/active              — get current active goal with full detail
GET  /goals/history             — list all past goals
GET  /goals/{id}                — get specific goal
PUT  /goals/{id}                — update goal (minor edits only)
POST /goals/{id}/pause          — pause current goal
POST /goals/{id}/abandon        — abandon goal with reason
POST /goals/{id}/complete       — mark goal as complete

Objectives:
GET  /goals/{id}/objectives     — list objectives for a goal
PUT  /goals/{id}/objectives/{obj_id} — update objective status/progress

Identity Traits:
GET  /goals/traits              — list active identity traits
PUT  /goals/traits/{id}         — update trait (user can correct AI scores)
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_onboarded_user
from core.cache import invalidate_user_context
from core.database import get_db
from db.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/goals", tags=["Goals"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GoalUpdateRequest(BaseModel):
    refined_statement: str | None = Field(default=None, max_length=500)
    why_statement: str | None = Field(default=None, max_length=1000)
    success_definition: str | None = Field(default=None, max_length=1000)
    target_date: str | None = None


class AbandonGoalRequest(BaseModel):
    reason: str = Field(min_length=10, max_length=500)


class ObjectiveUpdateRequest(BaseModel):
    status: str | None = None     # upcoming | in_progress | completed | missed
    progress_percentage: float | None = Field(default=None, ge=0, le=100)


class TraitUpdateRequest(BaseModel):
    current_score: float | None = Field(default=None, ge=1.0, le=10.0)
    description: str | None = Field(default=None, max_length=500)


# ─── Active Goal ──────────────────────────────────────────────────────────────

@router.get(
    "/active",
    summary="Get current active goal with full strategy detail",
)
async def get_active_goal(
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Returns the complete active goal including:
    - Goal statement and strategy
    - All objectives with status
    - Identity traits with scores
    - Progress metrics
    """
    uid = str(current_user.id)

    # Get goal — progress calculated live from task completions
    goal_result = await db.execute(
        text("""
            SELECT
                g.id, g.refined_statement, g.raw_input, g.why_statement,
                g.success_definition, g.required_identity, g.key_shifts,
                g.estimated_timeline, g.difficulty_level,
                g.started_at, g.target_date,
                g.objectives_count, g.objectives_completed,
                ROUND(
                    COUNT(CASE WHEN dt.status = 'completed' THEN 1 END)::numeric /
                    NULLIF(COUNT(dt.id), 0) * 100, 1
                ) AS progress_percentage
            FROM goals g
            LEFT JOIN daily_tasks dt ON dt.user_id = g.user_id
                AND dt.scheduled_date >= g.started_at
            WHERE g.user_id = :user_id AND g.status = 'active'
            GROUP BY g.id, g.refined_statement, g.raw_input, g.why_statement,
                g.success_definition, g.required_identity, g.key_shifts,
                g.estimated_timeline, g.difficulty_level,
                g.started_at, g.target_date,
                g.objectives_count, g.objectives_completed
            LIMIT 1
        """),
        {"user_id": uid},
    )
    goal = goal_result.fetchone()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active goal found.",
        )

    # Get objectives
    obj_result = await db.execute(
        text("""
            SELECT
                id, title, description, success_criteria,
                sequence_order, estimated_weeks, status,
                progress_percentage, started_at, completed_at
            FROM objectives
            WHERE goal_id = :goal_id
            ORDER BY sequence_order
        """),
        {"goal_id": str(goal.id)},
    )
    objectives = [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "success_criteria": r.success_criteria,
            "order": r.sequence_order,
            "estimated_weeks": r.estimated_weeks,
            "status": r.status,
            "progress": float(r.progress_percentage) if r.progress_percentage else 0.0,
            "started_at": str(r.started_at) if r.started_at else None,
            "completed_at": str(r.completed_at) if r.completed_at else None,
        }
        for r in obj_result.fetchall()
    ]

    # Get identity traits
    trait_result = await db.execute(
        text("""
            SELECT
                id, name, description, category,
                current_score, target_score, velocity
            FROM identity_traits
            WHERE user_id = :user_id AND is_active = TRUE
            ORDER BY (target_score - current_score) DESC
        """),
        {"user_id": uid},
    )
    traits = [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "current_score": float(r.current_score),
            "target_score": float(r.target_score),
            "velocity": float(r.velocity),
            "progress_pct": round(float(r.current_score) / float(r.target_score) * 100, 1),
            "gap": round(float(r.target_score) - float(r.current_score), 1),
            "trend": "growing" if float(r.velocity) > 0 else ("declining" if float(r.velocity) < 0 else "stable"),
        }
        for r in trait_result.fetchall()
    ]

    # Get identity profile scores
    scores_result = await db.execute(
        text("""
            SELECT
                transformation_score, consistency_score,
                depth_score, momentum_score, alignment_score,
                momentum_state, current_streak, longest_streak
            FROM identity_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": uid},
    )
    scores_row = scores_result.fetchone()
    scores = {}
    if scores_row:
        scores = {
            "transformation": float(scores_row.transformation_score or 0),
            "consistency": float(scores_row.consistency_score or 0),
            "depth": float(scores_row.depth_score or 0),
            "momentum": float(scores_row.momentum_score or 0),
            "alignment": float(scores_row.alignment_score or 0),
            "momentum_state": scores_row.momentum_state,
            "streak": scores_row.current_streak,
            "longest_streak": scores_row.longest_streak,
        }

    return {
        "goal": {
            "id": str(goal.id),
            "statement": goal.refined_statement,
            "original": goal.raw_input,
            "why": goal.why_statement,
            "success_definition": goal.success_definition,
            "required_identity": goal.required_identity,
            "key_shifts": goal.key_shifts or [],
            "estimated_weeks": goal.estimated_timeline,
            "difficulty": goal.difficulty_level,
            "progress": float(goal.progress_percentage or 0),
            "started_at": str(goal.started_at) if goal.started_at else None,
            "target_date": str(goal.target_date) if goal.target_date else None,
            "objectives_total": goal.objectives_count,
            "objectives_done": goal.objectives_completed,
        },
        "objectives": objectives,
        "identity_traits": traits,
        "scores": scores,
    }


# ─── Goal History ─────────────────────────────────────────────────────────────

@router.get(
    "/history",
    summary="List all past goals",
)
async def get_goal_history(
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        text("""
            SELECT
                id, refined_statement, status,
                progress_percentage, started_at,
                completed_at, abandoned_at, abandon_reason
            FROM goals
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """),
        {"user_id": str(current_user.id)},
    )
    goals = [
        {
            "id": str(r.id),
            "statement": r.refined_statement,
            "status": r.status,
            "progress": float(r.progress_percentage or 0),
            "started_at": str(r.started_at) if r.started_at else None,
            "completed_at": str(r.completed_at) if r.completed_at else None,
            "abandoned_at": str(r.abandoned_at) if r.abandoned_at else None,
            "abandon_reason": r.abandon_reason,
        }
        for r in result.fetchall()
    ]
    return {"goals": goals, "total": len(goals)}


# ─── Goal Updates ─────────────────────────────────────────────────────────────

@router.put(
    "/{goal_id}",
    summary="Update goal statement or details",
)
async def update_goal(
    goal_id: str,
    payload: GoalUpdateRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Minor edits to the goal — statement, why, success definition, target date.
    Does not re-run AI decomposition. For major goal changes, abandon and resubmit.
    """
    # Verify ownership
    result = await db.execute(
        text("SELECT id FROM goals WHERE id = :id AND user_id = :user_id AND status = 'active'"),
        {"id": goal_id, "user_id": str(current_user.id)},
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Goal not found.")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = goal_id

    await db.execute(
        text(f"UPDATE goals SET {set_clauses}, updated_at = NOW() WHERE id = :id"),
        updates,
    )
    await invalidate_user_context(str(current_user.id))

    return {"status": "updated"}


@router.post(
    "/{goal_id}/pause",
    summary="Pause the current goal",
)
async def pause_goal(
    goal_id: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await db.execute(
        text("""
            UPDATE goals SET status = 'paused', updated_at = NOW()
            WHERE id = :id AND user_id = :user_id AND status = 'active'
        """),
        {"id": goal_id, "user_id": str(current_user.id)},
    )
    await invalidate_user_context(str(current_user.id))
    return {"status": "paused"}


@router.post(
    "/{goal_id}/abandon",
    summary="Abandon goal with a reason",
)
async def abandon_goal(
    goal_id: str,
    payload: AbandonGoalRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Abandon the current goal. Requires a reason — this is stored
    and used by the AI to improve future goal setting.
    After abandoning, the user can define a new goal.
    """
    await db.execute(
        text("""
            UPDATE goals
            SET status = 'abandoned',
                abandoned_at = NOW(),
                abandon_reason = :reason,
                updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
        """),
        {"id": goal_id, "user_id": str(current_user.id), "reason": payload.reason},
    )
    # Reset onboarding to allow new goal definition
    await db.execute(
        text("UPDATE users SET onboarding_status = 'interview_complete' WHERE id = :user_id"),
        {"user_id": str(current_user.id)},
    )
    await invalidate_user_context(str(current_user.id))
    logger.info("goal_abandoned", user_id=str(current_user.id), goal_id=goal_id)
    return {"status": "abandoned", "next_step": "define_new_goal"}


@router.post(
    "/{goal_id}/complete",
    summary="Mark goal as complete",
)
async def complete_goal(
    goal_id: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Mark the goal as complete. This is a celebration moment.
    The AI will generate a completion summary.
    """
    await db.execute(
        text("""
            UPDATE goals
            SET status = 'completed',
                completed_at = NOW(),
                progress_percentage = 100,
                updated_at = NOW()
            WHERE id = :id AND user_id = :user_id AND status = 'active'
        """),
        {"id": goal_id, "user_id": str(current_user.id)},
    )
    await invalidate_user_context(str(current_user.id))
    logger.info("goal_completed", user_id=str(current_user.id), goal_id=goal_id)
    return {"status": "completed", "message": "Remarkable. You did it."}


# ─── Objectives ───────────────────────────────────────────────────────────────

@router.get(
    "/{goal_id}/objectives",
    summary="List objectives for a goal",
)
async def get_objectives(
    goal_id: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        text("""
            SELECT o.id, o.title, o.description, o.success_criteria,
                   o.sequence_order, o.estimated_weeks, o.status,
                   o.progress_percentage, o.started_at, o.completed_at
            FROM objectives o
            JOIN goals g ON g.id = o.goal_id
            WHERE o.goal_id = :goal_id AND g.user_id = :user_id
            ORDER BY o.sequence_order
        """),
        {"goal_id": goal_id, "user_id": str(current_user.id)},
    )
    objectives = [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "success_criteria": r.success_criteria,
            "order": r.sequence_order,
            "estimated_weeks": r.estimated_weeks,
            "status": r.status,
            "progress": float(r.progress_percentage or 0),
            "started_at": str(r.started_at) if r.started_at else None,
            "completed_at": str(r.completed_at) if r.completed_at else None,
        }
        for r in result.fetchall()
    ]
    return {"objectives": objectives}


@router.put(
    "/{goal_id}/objectives/{obj_id}",
    summary="Update objective status or progress",
)
async def update_objective(
    goal_id: str,
    obj_id: str,
    payload: ObjectiveUpdateRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    updates: dict = {}
    if payload.status:
        updates["status"] = payload.status
        if payload.status == "in_progress":
            updates["started_at"] = "NOW()"
        elif payload.status == "completed":
            updates["completed_at"] = "NOW()"
            updates["progress_percentage"] = 100
    if payload.progress_percentage is not None:
        updates["progress_percentage"] = payload.progress_percentage

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    # Build SET clause carefully (NOW() can't be parameterized)
    set_parts = []
    params = {"id": obj_id, "user_id": str(current_user.id)}
    for k, v in updates.items():
        if v == "NOW()":
            set_parts.append(f"{k} = NOW()")
        else:
            set_parts.append(f"{k} = :{k}")
            params[k] = v

    await db.execute(
        text(f"""
            UPDATE objectives SET {', '.join(set_parts)}, updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
        """),
        params,
    )
    await invalidate_user_context(str(current_user.id))
    return {"status": "updated"}


# ─── Identity Traits ──────────────────────────────────────────────────────────

@router.get(
    "/traits",
    summary="Get active identity traits",
)
async def get_traits(
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        text("""
            SELECT id, name, description, category,
                   current_score, target_score, velocity
            FROM identity_traits
            WHERE user_id = :user_id AND is_active = TRUE
            ORDER BY (target_score - current_score) DESC
        """),
        {"user_id": str(current_user.id)},
    )
    traits = [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "current_score": float(r.current_score),
            "target_score": float(r.target_score),
            "velocity": float(r.velocity),
            "progress_pct": round(float(r.current_score) / float(r.target_score) * 100, 1),
            "trend": "growing" if r.velocity > 0 else ("declining" if r.velocity < 0 else "stable"),
        }
        for r in result.fetchall()
    ]
    return {"traits": traits}


@router.put(
    "/traits/{trait_id}",
    summary="Update a trait score or description",
)
async def update_trait(
    trait_id: str,
    payload: TraitUpdateRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Users can correct AI-assessed trait scores if they disagree.
    This is important for trust and accuracy.
    """
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
    updates["id"] = trait_id
    updates["user_id"] = str(current_user.id)

    await db.execute(
        text(f"""
            UPDATE identity_traits
            SET {set_clauses}, updated_at = NOW()
            WHERE id = :id AND user_id = :user_id AND is_active = TRUE
        """),
        updates,
    )
    await invalidate_user_context(str(current_user.id))
    return {"status": "updated"}
