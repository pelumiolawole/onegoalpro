"""
api/routers/tasks.py

Daily task endpoints — the core daily loop.

GET  /tasks/today               — get today's task (with backlog info)
GET  /tasks/backlog             — get missed/archived tasks
GET  /tasks/{date}              — get task for a specific date
POST /tasks/{id}/start          — mark task as started
POST /tasks/{id}/complete       — mark task as complete
POST /tasks/{id}/skip           — skip with a reason
GET  /tasks/history             — task history with completion stats
POST /tasks/generate            — manually trigger task generation
"""

from datetime import date, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai.engines.task_generator import TaskGeneratorEngine
from api.dependencies.auth import get_onboarded_user
from core.cache import invalidate_user_context
from core.database import get_db
from db.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/tasks", tags=["Daily Tasks"])
task_generator = TaskGeneratorEngine()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CompleteTaskRequest(BaseModel):
    execution_notes: str | None = Field(default=None, max_length=2000)
    actual_duration_minutes: int | None = Field(default=None, ge=1, le=480)


class SkipTaskRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


# ─── Continuous Guardrail Helper ──────────────────────────────────────────────

async def ensure_today_task_exists(user_id: str, db: AsyncSession) -> None:
    """
    CONTINUOUS GUARDRAIL
    ├── Check if user has a task for today
    ├── If not, trigger immediate generation (fire-and-forget)
    └── Log for monitoring
    """
    from datetime import date
    
    # Check if task exists for today
    result = await db.execute(
        text("""
            SELECT id FROM daily_tasks
            WHERE user_id = :user_id
              AND scheduled_date = CURRENT_DATE
              AND task_type = 'becoming'
            LIMIT 1
        """),
        {"user_id": user_id}
    )
    
    if result.scalar():
        return  # Task exists, nothing to do
    
    # No task found - trigger immediate generation
    logger.info(
        "guardrail_triggered_task_generation",
        user_id=user_id,
        reason="missing_today_task"
    )
    
    try:
        engine = TaskGeneratorEngine()
        
        # Generate task for today
        task = await engine.generate_task_for_user(
            user_id=user_id,
            target_date=date.today(),
            is_backlog=False,
        )
        
        if task:
            # Mark as guardrail-generated
            await db.execute(
                text("""
                    UPDATE daily_tasks
                    SET generation_context = generation_context || '{"guardrail_generated": true}'::jsonb
                    WHERE user_id = :user_id
                      AND scheduled_date = CURRENT_DATE
                      AND task_type = 'becoming'
                """),
                {"user_id": user_id}
            )
            await db.commit()
            
            logger.info(
                "guardrail_task_generated_success",
                user_id=user_id,
                task_title=task.get("title")
            )
        else:
            logger.warning(
                "guardrail_task_generation_returned_none",
                user_id=user_id
            )
            
    except Exception as e:
        logger.error(
            "guardrail_task_generation_failed",
            user_id=user_id,
            error=str(e)
        )
        # Don't raise - this is a background safety net, not a blocking operation


# ─── Today's Task ─────────────────────────────────────────────────────────────

@router.get(
    "/today",
    summary="Get today's becoming task with backlog info",
)
async def get_today_task(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Returns today's identity-focused task.
    
    CONTINUOUS GUARDRAIL: Runs background check to ensure task exists.
    If missing, triggers async generation.
    
    Also includes:
    - backlog_count: number of missed tasks
    - intervention_message: if backlog >= 3, shows AI intervention
    - can_generate_manual: whether user can manually generate today's task
    """
    uid = str(current_user.id)
    today = date.today()

    # CONTINUOUS GUARDRAIL: Trigger background check (non-blocking)
    # This ensures task exists without slowing down the response
    background_tasks.add_task(ensure_today_task_exists, uid, db)

    # Get today's task
    result = await db.execute(
        text("""
            SELECT
                dt.id, dt.identity_focus, dt.title, dt.description,
                dt.execution_guidance, dt.time_estimate_minutes,
                dt.difficulty_level, dt.task_type, dt.status,
                dt.started_at, dt.completed_at, dt.execution_notes,
                dt.scheduled_date, dt.generation_context,
                r.id AS reflection_id,
                r.submitted_at AS reflected_at
            FROM daily_tasks dt
            LEFT JOIN reflections r ON r.task_id = dt.id
            WHERE dt.user_id = :user_id
              AND dt.scheduled_date = :today
              AND dt.status != 'skipped'
            LIMIT 1
        """),
        {"user_id": uid, "today": today},
    )
    task = result.fetchone()

    # If no task, try synchronous generation (fallback for immediate need)
    # This maintains backward compatibility while guardrail runs in background
    if not task:
        logger.info("generating_on_demand_task", user_id=uid)
        generated = await task_generator.generate_task_for_user(
            user_id=current_user.id,
            target_date=today,
            db=db,
        )
        if not generated:
            # Return empty state - guardrail is running in background
            # Next refresh will likely have the task
            return {
                "has_task": False,
                "task": None,
                "message": "Your task is being prepared. Refresh in a moment.",
                "guardrail_triggered": True,
                "backlog": {
                    "count": 0,
                    "missed_dates": [],
                    "max_allowed": 3,
                    "intervention_message": None,
                }
            }
        
        # Reload from DB
        result = await db.execute(
            text("""
                SELECT dt.id, dt.identity_focus, dt.title, dt.description,
                       dt.execution_guidance, dt.time_estimate_minutes,
                       dt.difficulty_level, dt.task_type, dt.status,
                       dt.started_at, dt.completed_at, dt.execution_notes,
                       dt.scheduled_date, dt.generation_context,
                       NULL AS reflection_id, NULL AS reflected_at
                FROM daily_tasks dt
                WHERE dt.user_id = :user_id
                  AND dt.scheduled_date = :today
                  AND dt.status != 'skipped'
                LIMIT 1
            """),
            {"user_id": uid, "today": today},
        )
        task = result.fetchone()

    # Get backlog info
    backlog_result = await db.execute(
        text("""
            SELECT 
                COUNT(*) as missed_count,
                ARRAY_AGG(scheduled_date ORDER BY scheduled_date) as missed_dates
            FROM daily_tasks
            WHERE user_id = :user_id
              AND scheduled_date < :today
              AND status = 'pending'
              AND task_type = 'becoming'
        """),
        {"user_id": uid, "today": today},
    )
    backlog_row = backlog_result.fetchone()
    backlog_count = backlog_row.missed_count or 0
    missed_dates = backlog_row.missed_dates or []

    # Get intervention message if applicable
    intervention_message = None
    if backlog_count >= 3:
        intervention_result = await db.execute(
            text("""
                SELECT message FROM coach_interventions
                WHERE user_id = :user_id
                  AND intervention_type = 'backlog_crisis'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": uid},
        )
        intervention_row = intervention_result.fetchone()
        if intervention_row:
            intervention_message = intervention_row.message

    response = _format_task(task, today)
    response["has_task"] = True
    response["backlog"] = {
        "count": backlog_count,
        "missed_dates": [str(d) for d in missed_dates],
        "max_allowed": 3,
        "intervention_message": intervention_message,
    }
    
    # Add task source for monitoring/debugging
    gen_context = task.generation_context or {}
    if gen_context.get("sweep_generated"):
        response["task_source"] = "morning_sweep"
    elif gen_context.get("guardrail_generated"):
        response["task_source"] = "guardrail"
    elif gen_context.get("fallback"):
        response["task_source"] = "fallback"
    else:
        response["task_source"] = "midnight"
    
    return response


# ─── Backlog Tasks ────────────────────────────────────────────────────────────

@router.get(
    "/backlog",
    summary="Get missed/archived tasks (up to 3)",
)
async def get_backlog_tasks(
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Returns missed tasks from the past (max 3).
    These are tasks that weren't completed or skipped.
    User can choose to complete them or archive them.
    """
    uid = str(current_user.id)
    today = date.today()

    result = await db.execute(
        text("""
            SELECT
                dt.id, dt.identity_focus, dt.title, dt.description,
                dt.execution_guidance, dt.time_estimate_minutes,
                dt.difficulty_level, dt.task_type, dt.status,
                dt.scheduled_date, dt.created_at,
                r.id AS reflection_id
            FROM daily_tasks dt
            LEFT JOIN reflections r ON r.task_id = dt.id
            WHERE dt.user_id = :user_id
              AND dt.scheduled_date < :today
              AND dt.status = 'pending'
              AND dt.task_type = 'becoming'
            ORDER BY dt.scheduled_date DESC
            LIMIT 3
        """),
        {"user_id": uid, "today": today},
    )
    tasks = result.fetchall()

    return {
        "backlog_count": len(tasks),
        "max_allowed": 3,
        "tasks": [
            {
                "id": str(t.id),
                "date": str(t.scheduled_date),
                "identity_focus": t.identity_focus,
                "title": t.title,
                "description": t.description,
                "execution_guidance": t.execution_guidance,
                "time_estimate_minutes": t.time_estimate_minutes,
                "difficulty": t.difficulty_level,
                "days_ago": (today - t.scheduled_date).days,
                "can_complete": True,
                "can_archive": True,
            }
            for t in tasks
        ]
    }


# ─── Archive Task ─────────────────────────────────────────────────────────────

@router.post(
    "/{task_id}/archive",
    summary="Archive a missed task without completing it",
)
async def archive_task(
    task_id: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Archive a missed task from the past.
    This marks it as 'missed' rather than completed or skipped.
    Used for clearing backlog without doing old tasks.
    """
    uid = str(current_user.id)

    result = await db.execute(
        text("""
            UPDATE daily_tasks
            SET status = 'missed',
                updated_at = NOW()
            WHERE id = :id 
              AND user_id = :user_id
              AND scheduled_date < CURRENT_DATE
              AND status = 'pending'
            RETURNING id, scheduled_date
        """),
        {"id": task_id, "user_id": uid},
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or cannot be archived.",
        )

    logger.info("task_archived", user_id=uid, task_id=task_id, date=str(row.scheduled_date))

    return {
        "status": "archived",
        "message": "Task archived. Focus on today's work.",
    }


# ─── Task by Date ─────────────────────────────────────────────────────────────

@router.get(
    "/{task_date}",
    summary="Get task for a specific date (YYYY-MM-DD)",
)
async def get_task_by_date(
    task_date: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a task for a specific date."""
    try:
        parsed_date = date.fromisoformat(task_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    result = await db.execute(
        text("""
            SELECT
                dt.id, dt.identity_focus, dt.title, dt.description,
                dt.execution_guidance, dt.time_estimate_minutes,
                dt.difficulty_level, dt.task_type, dt.status,
                dt.started_at, dt.completed_at, dt.execution_notes,
                r.id AS reflection_id,
                r.submitted_at AS reflected_at
            FROM daily_tasks dt
            LEFT JOIN reflections r ON r.task_id = dt.id
            WHERE dt.user_id = :user_id
              AND dt.scheduled_date = :date
              AND dt.status != 'skipped'
            LIMIT 1
        """),
        {"user_id": str(current_user.id), "date": parsed_date},
    )
    task = result.fetchone()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No task found for {task_date}.",
        )

    return _format_task(task, parsed_date)


# ─── Task Actions ─────────────────────────────────────────────────────────────

@router.post(
    "/{task_id}/start",
    summary="Enter execution mode — mark task as started",
)
async def start_task(
    task_id: str,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark the task as started."""
    result = await db.execute(
        text("""
            UPDATE daily_tasks
            SET status = 'pending',
                started_at = COALESCE(started_at, NOW()),
                updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
            RETURNING id, started_at
        """),
        {"id": task_id, "user_id": str(current_user.id)},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found.")

    await _log_engagement(str(current_user.id), "task_start", db)

    return {"status": "started", "started_at": str(row.started_at)}


@router.post(
    "/{task_id}/complete",
    summary="Complete today's task",
)
async def complete_task(
    task_id: str,
    payload: CompleteTaskRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark the task as complete."""
    uid = str(current_user.id)

    result = await db.execute(
        text("""
            UPDATE daily_tasks
            SET status = 'completed',
                completed_at = NOW(),
                execution_notes = COALESCE(:notes, execution_notes),
                actual_duration_mins = COALESCE(:duration, actual_duration_mins),
                updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
              AND status != 'completed'
            RETURNING id, scheduled_date
        """),
        {
            "id": task_id,
            "user_id": uid,
            "notes": payload.execution_notes,
            "duration": payload.actual_duration_minutes,
        },
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or already completed.",
        )

    # Update progress metrics
    await db.execute(
        text("""
            INSERT INTO progress_metrics (user_id, metric_date, task_completed)
            VALUES (:user_id, :date, TRUE)
            ON CONFLICT (user_id, metric_date)
            DO UPDATE SET task_completed = TRUE
        """),
        {"user_id": uid, "date": row.scheduled_date},
    )

    await _log_engagement(uid, "task_complete", db)
    await invalidate_user_context(uid)

    logger.info("task_completed", user_id=uid, task_id=task_id)

    return {
        "status": "completed",
        "message": "Task complete. Take a moment to reflect.",
        "reflection_available": True,
    }


@router.post(
    "/{task_id}/skip",
    summary="Skip today's task with a reason",
)
async def skip_task(
    task_id: str,
    payload: SkipTaskRequest,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Skip a task."""
    uid = str(current_user.id)

    await db.execute(
        text("""
            UPDATE daily_tasks
            SET status = 'skipped',
                skipped_reason = :reason,
                updated_at = NOW()
            WHERE id = :id AND user_id = :user_id
              AND status NOT IN ('completed', 'skipped')
        """),
        {"id": task_id, "user_id": uid, "reason": payload.reason},
    )

    await db.execute(
        text("""
            INSERT INTO progress_metrics (user_id, metric_date, task_completed)
            VALUES (:user_id, CURRENT_DATE, FALSE)
            ON CONFLICT (user_id, metric_date) DO NOTHING
        """),
        {"user_id": uid},
    )

    logger.info("task_skipped", user_id=uid, task_id=task_id, reason=payload.reason)

    return {
        "status": "skipped",
        "message": "Noted. Tomorrow is a new opportunity to show up.",
    }


# ─── Task History ─────────────────────────────────────────────────────────────

@router.get(
    "/history",
    summary="Get task history with completion stats",
)
async def get_task_history(
    days: int = 30,
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns task history for the past N days."""
    uid = str(current_user.id)
    limit_days = min(days, 90)
    since = date.today() - timedelta(days=limit_days)

    result = await db.execute(
        text("""
            SELECT
                dt.id, dt.scheduled_date, dt.identity_focus,
                dt.title, dt.status, dt.difficulty_level,
                dt.completed_at, dt.skipped_reason,
                r.depth_score, r.sentiment
            FROM daily_tasks dt
            LEFT JOIN reflections r ON r.task_id = dt.id
            WHERE dt.user_id = :user_id
              AND dt.scheduled_date >= :since
              AND dt.status != 'skipped'
            ORDER BY dt.scheduled_date DESC
        """),
        {"user_id": uid, "since": since},
    )
    tasks = result.fetchall()

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    skipped = sum(1 for t in tasks if t.status == "skipped")
    missed = sum(1 for t in tasks if t.status == "missed")
    reflected = sum(1 for t in tasks if t.depth_score is not None)

    return {
        "stats": {
            "total": total,
            "completed": completed,
            "skipped": skipped,
            "missed": missed,
            "reflected": reflected,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
        },
        "tasks": [
            {
                "id": str(t.id),
                "date": str(t.scheduled_date),
                "identity_focus": t.identity_focus,
                "title": t.title,
                "status": t.status,
                "difficulty": t.difficulty_level,
                "completed_at": str(t.completed_at) if t.completed_at else None,
                "skip_reason": t.skipped_reason,
                "reflection_depth": float(t.depth_score) if t.depth_score else None,
                "reflection_sentiment": t.sentiment,
            }
            for t in tasks
        ],
    }


@router.post(
    "/generate",
    summary="Manually generate today's task if none exists",
)
async def generate_task(
    current_user: User = Depends(get_onboarded_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger task generation for today."""
    today = date.today()
    generated = await task_generator.generate_task_for_user(
        user_id=current_user.id,
        target_date=today,
        db=db,
    )
    if not generated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A task already exists for today.",
        )
    return {"status": "generated", "task": generated}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_task(task, task_date: date) -> dict:
    """Format a task row into the standard API response."""
    return {
        "id": str(task.id),
        "date": str(task_date),
        "identity_focus": task.identity_focus,
        "title": task.title,
        "description": task.description,
        "execution_guidance": task.execution_guidance,
        "time_estimate_minutes": task.time_estimate_minutes,
        "difficulty": task.difficulty_level,
        "task_type": task.task_type,
        "status": task.status,
        "started_at": str(task.started_at) if task.started_at else None,
        "completed_at": str(task.completed_at) if task.completed_at else None,
        "execution_notes": task.execution_notes,
        "reflection_submitted": task.reflection_id is not None,
        "reflected_at": str(task.reflected_at) if task.reflected_at else None,
    }


async def _log_engagement(user_id: str, event_type: str, db: AsyncSession) -> None:
    """Log an engagement event."""
    try:
        await db.execute(
            text("""
                INSERT INTO engagement_events (user_id, event_type)
                VALUES (:user_id, :event_type)
            """),
            {"user_id": user_id, "event_type": event_type},
        )
    except Exception:
        pass