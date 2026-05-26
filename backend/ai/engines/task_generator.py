"""
ai/engines/task_generator.py

Daily Task Generator Engine

Generates identity-focused becoming tasks with backlog support.
Handles missed days (max 3 backlog) and triggers interventions.
"""

import json
from datetime import date, timedelta
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai.base import BaseAIEngine
from ai.memory.context_builder import context_builder
from ai.prompts.system_prompts import get_prompt

logger = structlog.get_logger()


class TaskGeneratorEngine(BaseAIEngine):
    """
    Generates adaptive daily becoming tasks with backlog handling.
    """

    engine_name = "task_generator"
    default_temperature = 0.85

    # Fallback template tasks when AI generation fails
    FALLBACK_TASKS = [
        {
            "title": "15-Minute Identity Anchor",
            "description": "Spend 15 minutes on one action that reinforces who you're becoming. No perfection required—just presence.",
            "identity_focus": "Today you are someone who shows up, even when it's hard.",
            "execution_guidance": "Set a timer for 15 minutes. Work on one small thing related to your goal. When the timer ends, you're done.",
            "guidance": "Pick one specific action connected to your goal — not planning it, doing it. Set a timer for 15 minutes. Start before you feel ready. Stop when it ends.",
            "time_estimate_minutes": 15,
            "difficulty_level": 3,
            "task_type": "identity_anchor",
        },
        {
            "title": "The Minimum Effective Dose",
            "description": "Do the smallest possible version of your goal-related action. Consistency beats intensity.",
            "identity_focus": "Today you are someone who chooses consistency over perfection.",
            "execution_guidance": "Identify the absolute minimum action that still moves you forward. Do only that. Celebrate completion.",
            "guidance": "Write down the single smallest action that still counts as forward movement. Not the plan — the action. Do it now. That's the whole task.",
            "time_estimate_minutes": 10,
            "difficulty_level": 2,
            "task_type": "micro_action",
        },
        {
            "title": "Reflection in Action",
            "description": "Take one small step toward your goal, then pause to notice how it felt.",
            "identity_focus": "Today you are someone who learns by doing, not just planning.",
            "execution_guidance": "Spend 10 minutes on your goal. Then write one sentence about what you noticed.",
            "guidance": "Do 10 minutes of actual work on your goal — not thinking about it, doing it. Immediately after, write one honest sentence: what did you notice about yourself while you were doing it?",
            "time_estimate_minutes": 15,
            "difficulty_level": 3,
            "task_type": "becoming",
        },
    ]

    async def generate_daily_tasks_with_backlog(
        self,
        user_id: UUID | str,
        db: AsyncSession | None = None,
    ) -> int:
        """
        Generate today's task plus any missed tasks (max 3 backlog).
        Returns number of tasks generated.
        """
        from core.database import get_db_context

        uid = str(user_id)
        today = date.today()
        tasks_generated = 0

        async def _run(db: AsyncSession):
            nonlocal tasks_generated

            dates_needed = await self._get_missed_task_dates(uid, today, db)

            if len(dates_needed) > 3:
                dates_needed = sorted(dates_needed)[-3:]
                logger.warning(
                    "backlog_exceeds_limit",
                    user_id=uid,
                    total_missed=len(dates_needed),
                    limiting_to=3
                )

            for task_date in dates_needed:
                try:
                    task = await self.generate_task_for_user(
                        user_id=uid,
                        target_date=task_date,
                        db=db,
                        is_backlog=(task_date < today)
                    )
                    if task:
                        tasks_generated += 1
                except Exception as e:
                    logger.error(
                        "backlog_task_generation_failed",
                        user_id=uid,
                        date=str(task_date),
                        error=str(e)
                    )
                    try:
                        await db.rollback()
                    except Exception:
                        pass
                    try:
                        await self._create_fallback_task(uid, task_date, db)
                        tasks_generated += 1
                    except Exception as fallback_error:
                        logger.error(
                            "fallback_task_failed",
                            user_id=uid,
                            date=str(task_date),
                            error=str(fallback_error)
                        )

            await self._trigger_intervention_if_needed(uid, db)
            return tasks_generated

        if db:
            return await _run(db)
        else:
            async with get_db_context() as db:
                return await _run(db)

    async def _get_missed_task_dates(
        self,
        user_id: str,
        today: date,
        db: AsyncSession,
    ) -> list[date]:
        check_dates = [today - timedelta(days=i) for i in range(3, -1, -1)]

        result = await db.execute(
            text("""
                SELECT scheduled_date
                FROM daily_tasks
                WHERE user_id = :user_id
                  AND scheduled_date >= :start_date
                  AND scheduled_date <= :end_date
                  AND status != 'skipped'
            """),
            {
                "user_id": user_id,
                "start_date": check_dates[0],
                "end_date": check_dates[-1],
            },
        )
        existing_dates = {row[0] for row in result.fetchall()}
        return [d for d in check_dates if d not in existing_dates]

    async def _trigger_intervention_if_needed(
        self,
        user_id: str,
        db: AsyncSession,
    ) -> None:
        result = await db.execute(
            text("""
                SELECT COUNT(*)
                FROM daily_tasks
                WHERE user_id = :user_id
                  AND scheduled_date < CURRENT_DATE
                  AND status = 'pending'
                  AND task_type = 'becoming'
            """),
            {"user_id": user_id},
        )
        missed_count = result.scalar() or 0

        if missed_count >= 3:
            existing = await db.execute(
                text("""
                    SELECT id FROM coach_interventions
                    WHERE user_id = :user_id
                      AND intervention_type = 'backlog_crisis'
                      AND created_at > NOW() - INTERVAL '3 days'
                    LIMIT 1
                """),
                {"user_id": user_id},
            )
            if not existing.fetchone():
                await db.execute(
                    text("""
                        INSERT INTO coach_interventions
                        (user_id, intervention_type, message, urgency)
                        VALUES (:user_id, 'backlog_crisis', :message, 'high')
                    """),
                    {
                        "user_id": user_id,
                        "message": "You've missed 3 days of transformation work. This isn't about perfection—it's about choosing who you want to become. Start with just today's task. The past is data, not destiny."
                    }
                )
                await db.commit()
                logger.info("backlog_intervention_triggered", user_id=user_id, missed_count=missed_count)

    async def _create_fallback_task(
        self,
        user_id: str,
        task_date: date,
        db: AsyncSession,
    ) -> None:
        fallback_index = task_date.day % len(self.FALLBACK_TASKS)
        fallback = self.FALLBACK_TASKS[fallback_index]

        await db.execute(
            text("""
                INSERT INTO daily_tasks (
                    user_id, scheduled_date, task_type,
                    identity_focus, title, description,
                    execution_guidance, guidance, time_estimate_minutes,
                    difficulty_level, generated_by_ai, generation_context
                ) VALUES (
                    :user_id, :date, :task_type,
                    :identity_focus, :title, :description,
                    :execution_guidance, :guidance, :time_estimate,
                    :difficulty, FALSE, CAST(:gen_context AS jsonb)
                )
            """),
            {
                "user_id": user_id,
                "date": task_date,
                "task_type": fallback["task_type"],
                "identity_focus": fallback["identity_focus"],
                "title": fallback["title"],
                "description": fallback["description"],
                "execution_guidance": fallback["execution_guidance"],
                "guidance": fallback["guidance"],
                "time_estimate": fallback["time_estimate_minutes"],
                "difficulty": fallback["difficulty_level"],
                "gen_context": json.dumps({"fallback": True, "reason": "ai_generation_failed"}),
            }
        )
        await db.commit()

    async def generate_task_for_user(
        self,
        user_id: UUID | str,
        target_date: date | None = None,
        db: AsyncSession | None = None,
        is_backlog: bool = False,
    ) -> dict:
        from core.database import get_db_context

        uid = str(user_id)
        task_date = target_date or date.today() + timedelta(days=1)

        async def _run(db: AsyncSession):
            existing = await db.execute(
                text("""
                    SELECT id FROM daily_tasks
                    WHERE user_id = :user_id
                      AND scheduled_date = :date
                      AND task_type = 'becoming'
                """),
                {"user_id": uid, "date": task_date},
            )
            if existing.scalar():
                logger.info("task_already_exists", user_id=uid, date=str(task_date))
                return None

            context = await context_builder.get_context(uid, db, force_refresh=True)
            context_str = context_builder.format_for_prompt(context)

            identity = context.get("identity", {})
            time_avail = identity.get("time_availability") or {}
            day_name = task_date.strftime("%A").lower()
            if day_name in ("saturday", "sunday"):
                time_available = time_avail.get("weekend", 45)
            else:
                time_available = time_avail.get("weekday", 30)
            time_available = max(15, min(120, time_available or 30))

            task_history_str = await self._get_task_history(uid, db)
            reflection_history_str = await self._get_reflection_history(uid, db)
            progress_context_str = await self._get_progress_context(context)
            day_of_week, day_context = self._get_day_context(task_date)

            system_prompt = get_prompt("task_generator").format(
                user_context=context_str,
                time_available=time_available,
                task_history=task_history_str,
                reflection_history=reflection_history_str,
                progress_context=progress_context_str,
                day_of_week=day_of_week,
                day_context=day_context,
            )

            date_note = ""
            if is_backlog:
                date_note = f"\n\nNOTE: This task is for {task_date.strftime('%A, %B %d')} (a missed day). Keep the tone supportive and non-judgmental. Focus on 'starting fresh' rather than 'catching up'."

            task_type_desc = "a catch-up" if is_backlog else "tomorrow's"

            try:
                response_raw = await self._complete(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Generate {task_type_desc} becoming task for {task_date.strftime('%A, %B %d')}.{date_note}",
                        },
                    ],
                    user_id=uid,
                    temperature=0.85,
                    max_tokens=800,
                )

                task_data = self._parse_json(response_raw, fallback={})

                if not task_data or not task_data.get("title"):
                    raise ValueError("Empty task data from AI")

                # Database-level duplicate check — safety net that catches what the prompt misses
                is_duplicate = await self._is_title_duplicate(uid, task_data.get("title", ""), db)
                if is_duplicate:
                    logger.warning(
                        "duplicate_task_title_detected",
                        user_id=uid,
                        title=task_data.get("title"),
                        date=str(task_date),
                    )
                    raise ValueError(f"Duplicate task title: {task_data.get('title')}")

            except Exception as e:
                logger.error("ai_task_generation_failed", user_id=uid, date=str(task_date), error=str(e))
                fallback_index = task_date.day % len(self.FALLBACK_TASKS)
                task_data = self.FALLBACK_TASKS[fallback_index].copy()
                task_data["fallback"] = True

            task_id = await self._persist_task(uid, task_date, task_data, context, db)

            logger.info(
                "task_generated",
                user_id=uid,
                date=str(task_date),
                task_title=task_data.get("title"),
                is_backlog=is_backlog,
                is_fallback=task_data.get("fallback", False),
                day_of_week=day_of_week,
            )

            return {**task_data, "id": str(task_id), "scheduled_date": str(task_date)}

        if db:
            return await _run(db)
        else:
            async with get_db_context() as db:
                return await _run(db)

    async def _is_title_duplicate(
        self, user_id: str, title: str, db: AsyncSession
    ) -> bool:
        """
        Database-level duplicate title check.
        Normalises away filler words and compares against last 21 days of generated titles.
        Catches what the prompt-level non-repetition instruction misses.
        """
        if not title:
            return False

        result = await db.execute(
            text("""
                SELECT title FROM daily_tasks
                WHERE user_id = :user_id
                  AND created_at >= NOW() - INTERVAL '21 days'
                ORDER BY created_at DESC
                LIMIT 30
            """),
            {"user_id": user_id},
        )
        recent_titles = [row[0] for row in result.fetchall() if row[0]]

        filler = {
            "a", "an", "the", "your", "my", "on", "in", "of", "for",
            "to", "and", "with", "about", "write", "create", "draft",
            "reflect", "engage", "design", "build", "craft", "explore",
            "conduct", "identify", "develop", "make", "do", "plan", "how",
        }

        def normalise(t: str) -> str:
            return " ".join(
                w.lower() for w in t.split()
                if w.lower() not in filler and len(w) > 2
            )

        norm_new = normalise(title)
        for recent in recent_titles:
            norm_recent = normalise(recent)
            if norm_new == norm_recent:
                return True
            new_words = set(norm_new.split())
            recent_words = set(norm_recent.split())
            if new_words and recent_words:
                overlap = len(new_words & recent_words) / max(len(new_words), len(recent_words))
                if overlap >= 0.70:
                    return True
        return False

    async def generate_initial_tasks(
        self,
        user_id: UUID | str,
        db: AsyncSession,
    ) -> list[dict]:
        uid = str(user_id)
        tasks = []
        today = date.today()

        for i in range(3):
            task_date = today + timedelta(days=i)
            try:
                task = await self.generate_task_for_user(uid, target_date=task_date, db=db)
                if task:
                    tasks.append(task)
            except Exception as e:
                logger.error("initial_task_generation_failed", user_id=uid, day=i, error=str(e))
                await db.rollback()

        return tasks

    async def _get_task_history(
        self, user_id: str, db: AsyncSession, days: int = 30
    ) -> str:
        """
        Fetch task history for non-repetition checking.

        Uses two windows merged together:
        1. Last 30 days by scheduled date (standard window)
        2. Last 14 tasks by creation date (catches users with large pending backlogs
           where the date-based window shows stale data)

        This is the key fix for the repetition problem: users with 90 pending tasks
        were generating into a blind spot because the date window only showed pending
        tasks that looked "different" by title even when they were effectively the same.
        """
        result = await db.execute(
            text("""
                WITH by_date AS (
                    SELECT scheduled_date, title, status, created_at
                    FROM daily_tasks
                    WHERE user_id = :user_id
                      AND scheduled_date >= CURRENT_DATE - (:days * INTERVAL '1 day')
                    ORDER BY scheduled_date DESC
                    LIMIT 30
                ),
                by_creation AS (
                    SELECT scheduled_date, title, status, created_at
                    FROM daily_tasks
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 14
                )
                SELECT DISTINCT ON (title) scheduled_date, title, status
                FROM (
                    SELECT * FROM by_date
                    UNION ALL
                    SELECT * FROM by_creation
                ) combined
                ORDER BY title, scheduled_date DESC
                LIMIT 45
            """),
            {"user_id": user_id, "days": days},
        )
        rows = result.fetchall()

        if not rows:
            return "No task history yet."

        lines = [f"  {row[0]} | {row[2]} | {row[1]}" for row in rows]
        return "\n".join(sorted(lines, reverse=True))

    async def _get_reflection_history(
        self, user_id: str, db: AsyncSession, limit: int = 10
    ) -> str:
        result = await db.execute(
            text("""
                SELECT
                    r.created_at::date AS reflection_date,
                    dt.title AS task_title,
                    r.questions_answers,
                    r.depth_score
                FROM reflections r
                LEFT JOIN daily_tasks dt ON dt.user_id = r.user_id
                    AND dt.scheduled_date = r.created_at::date
                WHERE r.user_id = :user_id
                ORDER BY r.created_at DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "limit": limit},
        )
        rows = result.fetchall()

        if not rows:
            return "No reflections yet."

        lines = []
        for row in rows:
            reflection_date, task_title, questions_answers, depth_score = row
            task_label = task_title or "unknown task"

            user_responses = []
            if questions_answers:
                pairs = questions_answers if isinstance(questions_answers, list) else []
                for pair in pairs:
                    answer = pair.get("answer") or pair.get("response") or ""
                    if answer and len(answer) > 10:
                        user_responses.append(answer[:120])

            response_text = " / ".join(user_responses[:2]) if user_responses else "no response recorded"
            lines.append(
                f"  {reflection_date} | task: {task_label} | depth: {depth_score or 'n/a'} | said: \"{response_text}\""
            )

        return "\n".join(lines)

    async def _get_progress_context(self, context: dict) -> str:
        scores = context.get("scores", {})
        retention = context.get("retention", {})

        lines = [
            f"Streak: {scores.get('streak', 0)} days",
            f"Momentum: {scores.get('momentum_state', 'holding')}",
            f"Transformation score: {scores.get('transformation', 0):.1f}/100",
            f"Consistency: {scores.get('consistency', 0):.1f}",
            f"Days active: {context.get('days_active', 0)}",
            f"Days since last task: {retention.get('days_since_last_task', 0)}",
        ]
        return "\n".join(lines)

    def _get_day_context(self, task_date: date) -> tuple[str, str]:
        day = task_date.strftime("%A")
        contexts = {
            "Monday": (
                "Monday — re-entry day. The user may be coming back after a weekend gap. "
                "Favour tasks that feel like a clean recommitment to their identity — something "
                "that resets the anchor rather than continuing mid-thread. Keep friction low "
                "enough to guarantee completion. A won Monday builds the week."
            ),
            "Tuesday": (
                "Tuesday — the week is finding its rhythm. Energy is typically higher than Monday. "
                "A good day for tasks that require focus or a degree of stretch. "
                "If momentum is rising, use it. If it stalled on Monday, Tuesday is the recovery point."
            ),
            "Wednesday": (
                "Wednesday — mid-week. The highest-leverage day of the week for identity work. "
                "Momentum is either building or has visibly stalled. Calibrate difficulty accordingly. "
                "A strong Wednesday task often determines whether the week is a win."
            ),
            "Thursday": (
                "Thursday — late-week push. The user knows how the week has gone. "
                "If it has been strong, a slightly harder task capitalises on momentum. "
                "If it has been difficult, favour something achievable that closes the week on a completion."
            ),
            "Friday": (
                "Friday — energy and attention are shifting toward the weekend. "
                "Favour tasks that can be completed and felt within a shorter window. "
                "Avoid tasks requiring sustained multi-hour focus. "
                "A task that ends the work week with a clear identity moment works well here."
            ),
            "Saturday": (
                "Saturday — weekend. More time available but context has shifted away from desk work. "
                "Favour tasks that happen in real life rather than at a screen: physical action, "
                "a conversation, a real-world experience connected to their goal. "
                "Identity is built in the world, not just at the desk."
            ),
            "Sunday": (
                "Sunday — reflective and transitional. The week is closing, the next is approaching. "
                "A good day for consolidation: reviewing the week, clarifying one intention for Monday, "
                "or completing something that closes a loop. Avoid tasks that feel like starting something large. "
                "Tasks that help the user arrive at Monday with clarity and purpose are ideal."
            ),
        }
        return day, contexts.get(day, contexts["Monday"])

    async def _persist_task(
        self,
        user_id: str,
        task_date: date,
        task_data: dict,
        context: dict,
        db: AsyncSession,
    ) -> UUID:
        goal = context.get("goal") or {}
        goal_id = goal.get("id")
        obj_id = await self._get_current_objective_id(user_id, db)

        generation_context = {
            "momentum_state": context.get("scores", {}).get("momentum_state"),
            "streak": context.get("scores", {}).get("streak"),
            "top_trait_gap": (context.get("traits") or [{}])[0].get("name") if context.get("traits") else None,
            "is_fallback": task_data.get("fallback", False),
        }

        result = await db.execute(
            text("""
                INSERT INTO daily_tasks (
                    user_id, goal_id, objective_id,
                    scheduled_date, task_type,
                    identity_focus, title, description,
                    execution_guidance, guidance, time_estimate_minutes,
                    difficulty_level, generated_by_ai, generation_context
                ) VALUES (
                    :user_id, :goal_id, :objective_id,
                    :date, :task_type,
                    :identity_focus, :title, :description,
                    :execution_guidance, :guidance, :time_estimate,
                    :difficulty, :generated_by_ai, CAST(:gen_context AS jsonb)
                )
                RETURNING id
            """),
            {
                "user_id": user_id,
                "goal_id": goal_id,
                "objective_id": str(obj_id) if obj_id else None,
                "date": task_date,
                "task_type": task_data.get("task_type", "becoming"),
                "identity_focus": task_data.get("identity_focus", ""),
                "title": task_data.get("title", ""),
                "description": task_data.get("description", ""),
                "execution_guidance": task_data.get("execution_guidance", ""),
                "guidance": task_data.get("guidance", ""),
                "time_estimate": task_data.get("time_estimate_minutes", 30),
                "difficulty": task_data.get("difficulty_level", 5),
                "generated_by_ai": not task_data.get("fallback", False),
                "gen_context": json.dumps(generation_context),
            },
        )
        await db.commit()
        return result.scalar()

    async def _get_current_objective_id(self, user_id: str, db: AsyncSession):
        result = await db.execute(
            text("""
                SELECT o.id FROM objectives o
                JOIN goals g ON g.id = o.goal_id
                WHERE g.user_id = :user_id AND g.status = 'active'
                  AND o.status IN ('in_progress', 'upcoming')
                ORDER BY o.sequence_order ASC
                LIMIT 1
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        return row[0] if row else None