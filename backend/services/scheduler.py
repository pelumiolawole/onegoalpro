"""
services/scheduler.py

Background job scheduler using APScheduler.
Runs nightly AI jobs that power the adaptive system.

Key change: Task generation now runs hourly, checking which users
are at 11pm in their local timezone (instead of 9pm UTC for everyone).
"""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.config import settings

logger = structlog.get_logger()


async def start_scheduler() -> AsyncIOScheduler:
    """
    Initialize and start the APScheduler.
    Returns the scheduler instance so it can be shut down on app close.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    # ── Job 1: Nightly task generation ────────────────────────────────
    # CHANGED: Runs every hour, checks who's at 11pm local time
    scheduler.add_job(
        func=run_nightly_task_generation,
        trigger=CronTrigger(hour="*", minute=0),  # Every hour at :00
        id="nightly_task_generation",
        name="Generate tomorrow's tasks for users at 11pm local time",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    # ── Job 2: Score update ───────────────────────────────────────────
    # CHANGED: Now runs at 2am UTC (after all timezones have passed 11pm)
    scheduler.add_job(
        func=run_score_updates,
        trigger=CronTrigger(hour=2, minute=0),
        id="score_update",
        name="Update transformation scores for all active users",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    # ── Job 3: Weekly review (Sunday only) ───────────────────────────
    # CHANGED: Runs at 2am UTC Monday (after all Sunday 11pms passed)
    scheduler.add_job(
        func=run_weekly_review_generation,
        trigger=CronTrigger(
            day_of_week="mon",
            hour=2,
            minute=0,
        ),
        id="weekly_review",
        name="Generate weekly evolution reviews",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=7200,
    )

    # ── Job 4: Intervention check ─────────────────────────────────────
    scheduler.add_job(
        func=run_intervention_check,
        trigger=CronTrigger(hour=10, minute=0),
        id="intervention_check",
        name="Detect and notify users needing coach check-ins",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    # ── Job 5: Behavioral snapshot (Sunday) ──────────────────────────
    # CHANGED: Runs at 2:30am UTC Monday
    scheduler.add_job(
        func=run_behavioral_snapshots,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=30),
        id="behavioral_snapshot",
        name="Build weekly behavioral fingerprints",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    scheduler.start()
    logger.info("scheduler_started", job_count=len(scheduler.get_jobs()))
    return scheduler


# ─── Job Implementations ──────────────────────────────────────────────────────

async def run_nightly_task_generation() -> None:
    """
    NEW LOGIC: Runs every hour. Only generates tasks for users
    where it's currently 11pm in their local timezone.
    """
    from datetime import datetime
    import pytz
    
    from core.cache import acquire_lock, release_lock
    from core.database import get_db_context

    lock_acquired = await acquire_lock("nightly_task_generation", ttl_seconds=3600)
    if not lock_acquired:
        logger.warning("task_generation_lock_not_acquired")
        return

    try:
        # Figure out which timezone is currently at 11pm
        current_utc_hour = datetime.now(pytz.UTC).hour
        
        async with get_db_context() as db:
            from sqlalchemy import text

            # Find users where it's 11pm right now
            # This query checks: user's local hour = 23 (11pm)
            result = await db.execute(text("""
                SELECT u.id, u.timezone
                FROM users u
                JOIN goals g ON g.user_id = u.id AND g.status = 'active'
                WHERE u.is_active = TRUE
                  AND u.onboarding_status = 'active'
                  AND EXTRACT(HOUR FROM NOW() AT TIME ZONE u.timezone) = 23
                  AND NOT EXISTS (
                    SELECT 1 FROM daily_tasks dt
                    WHERE dt.user_id = u.id
                      AND dt.scheduled_date = CURRENT_DATE + 1
                      AND dt.task_type = 'becoming'
                  )
            """))
            user_rows = result.fetchall()

        if not user_rows:
            logger.info("no_users_at_11pm", utc_hour=current_utc_hour)
            return

        user_ids = [str(row[0]) for row in user_rows]
        timezones = [row[1] for row in user_rows]
        
        logger.info(
            "task_generation_started", 
            user_count=len(user_ids),
            timezones=list(set(timezones))  # Just show unique timezones
        )

        from ai.engines.task_generator import TaskGeneratorEngine

        engine = TaskGeneratorEngine()
        success_count = 0
        error_count = 0

        for user_id in user_ids:
            try:
                await engine.generate_task_for_user(user_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    "task_generation_user_failed",
                    user_id=user_id,
                    error=str(e),
                )

        logger.info(
            "task_generation_complete",
            success=success_count,
            errors=error_count,
        )

    finally:
        await release_lock("nightly_task_generation")


async def run_score_updates() -> None:
    """Update transformation scores for all active users."""
    from core.cache import acquire_lock, release_lock
    from core.database import get_db_context

    lock_acquired = await acquire_lock("score_updates", ttl_seconds=3600)
    if not lock_acquired:
        return

    try:
        async with get_db_context() as db:
            from sqlalchemy import text

            result = await db.execute(text("""
                SELECT id FROM users
                WHERE is_active = TRUE
                  AND onboarding_status = 'active'
            """))
            user_ids = [str(row[0]) for row in result.fetchall()]

            for user_id in user_ids:
                try:
                    await db.execute(
                        text("SELECT update_user_scores(:user_id)"),
                        {"user_id": user_id},
                    )
                    # Also check if intervention is needed
                    await db.execute(
                        text("SELECT check_momentum_and_queue_intervention(:user_id)"),
                        {"user_id": user_id},
                    )
                except Exception as e:
                    logger.error("score_update_failed", user_id=user_id, error=str(e))

        logger.info("score_updates_complete", user_count=len(user_ids))

    finally:
        await release_lock("score_updates")


async def run_weekly_review_generation() -> None:
    """
    Generate weekly evolution letters for all active users.
    Runs Monday 2am UTC.
    """
    from core.cache import acquire_lock, release_lock
    from core.database import get_db_context

    lock_acquired = await acquire_lock("weekly_review_generation", ttl_seconds=7200)
    if not lock_acquired:
        logger.warning("weekly_review_lock_not_acquired")
        return

    try:
        async with get_db_context() as db:
            from sqlalchemy import text
            from ai.engines.reflection_analyzer import WeeklyReviewEngine

            # Find users who need a weekly review for the current week
            # (Monday morning, looking back at previous week)
            result = await db.execute(text("""
                SELECT u.id 
                FROM users u
                WHERE u.is_active = TRUE
                  AND u.onboarding_status = 'active'
                  AND NOT EXISTS (
                    SELECT 1 FROM weekly_reviews wr
                    WHERE wr.user_id = u.id
                      AND wr.week_start_date = date_trunc('week', CURRENT_DATE - INTERVAL '7 days')::DATE
                  )
            """))
            user_ids = [str(row[0]) for row in result.fetchall()]

        if not user_ids:
            logger.info("no_users_need_weekly_review")
            return

        logger.info("weekly_review_started", user_count=len(user_ids))

        engine = WeeklyReviewEngine()
        success_count = 0
        error_count =