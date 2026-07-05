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
            completion_pattern_str = await self._get_completion_pattern(uid, db)
            day_of_week, day_context = self._get_day_context(task_date)

            # Pre-compute domain dominance so the rejection message can name it
            dominant_domain = await self._get_dominant_recent_domain(uid, db)

            system_prompt = get_prompt("task_generator").format(
                user_context=context_str,
                time_available=time_available,
                task_history=task_history_str,
                reflection_history=reflection_history_str,
                progress_context=progress_context_str,
                completion_pattern=completion_pattern_str,
                day_of_week=day_of_week,
                day_context=day_context,
            )

            if dominant_domain:
                system_prompt += (
                    f"\n\nDOMAIN OVERRIDE (computed from this user's actual history): "
                    f"The last several tasks were all in the '{dominant_domain}' domain. "
                    f"Today's task MUST NOT be in '{dominant_domain}'. Choose a different domain entirely."
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

                # Validation gauntlet: forbidden patterns, duplicates, domain rotation.
                # One retry with the specific violation named. Deterministic checks in
                # code — the prompt asks, the code verifies.
                rejection_reason = await self._validate_task(
                    uid, task_data, dominant_domain, db
                )
                if rejection_reason:
                    logger.warning(
                        "task_rejected_retrying",
                        user_id=uid,
                        title=task_data.get("title"),
                        reason=rejection_reason,
                        date=str(task_date),
                    )
                    retry_raw = await self._complete(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {
                                "role": "user",
                                "content": (
                                    f"Generate {task_type_desc} becoming task for {task_date.strftime('%A, %B %d')}.{date_note}\n\n"
                                    f"REJECTED: Your previous task '{task_data.get('title')}' failed validation.\n"
                                    f"Reason: {rejection_reason}\n"
                                    f"Generate a completely different task that passes this check."
                                ),
                            },
                        ],
                        user_id=uid,
                        temperature=0.95,
                        max_tokens=800,
                    )
                    retry_data = self._parse_json(retry_raw, fallback={})
                    if not retry_data or not retry_data.get("title"):
                        raise ValueError(f"Retry returned empty after rejection: {rejection_reason}")
                    retry_rejection = await self._validate_task(
                        uid, retry_data, dominant_domain, db
                    )
                    if retry_rejection:
                        raise ValueError(
                            f"Retry also failed validation: {retry_rejection} — title: {retry_data.get('title')}"
                        )
                    task_data = retry_data

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

    # Title patterns that violate solo-executability. Checked in code because
    # the prompt-level ban provably failed: "Host a Virtual Coffee Chat" x10,
    # "Reach Out to a Potential Mentor" x9, "Attend a Local Networking Event" x5
    # all shipped despite being in the prompt's forbidden list.
    FORBIDDEN_TITLE_PATTERNS = [
        r"\breach out\b",
        r"\battend\b",
        r"\bjoin a\b",
        r"\bjoin an\b",
        r"\bhost\b",
        r"\bfacilitate\b",
        r"\bschedule a\b",
        r"\bset up a (call|meeting)\b",
        r"\binvite\b",
        r"\binterview (a|an|your|someone)\b",
        r"\bconduct .{0,20}interview\b",
        r"\bconnect with a\b",
        r"\bfind a (community|group|mentor)\b",
        r"\bwebinar\b",
        r"\bnetworking event\b",
    ]

    def _violates_forbidden_patterns(self, title: str) -> str | None:
        """
        Returns the matched pattern if the title requires another person's
        agreement or an external event to exist. None if clean.
        Code-level enforcement of the prompt's solo-executability ban.
        """
        import re
        t = (title or "").lower()
        for pattern in self.FORBIDDEN_TITLE_PATTERNS:
            if re.search(pattern, t):
                return pattern
        return None

    async def _get_dominant_recent_domain(
        self, user_id: str, db: AsyncSession
    ) -> str | None:
        """
        Look at the domains of the last 5 generated tasks (stored in
        generation_context). If 3+ share a domain, return it — the next
        task must NOT be in that domain. Returns None if no dominance.
        """
        result = await db.execute(
            text("""
                SELECT generation_context->>'domain' AS domain
                FROM daily_tasks
                WHERE user_id = :user_id
                  AND generation_context->>'domain' IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 5
            """),
            {"user_id": user_id},
        )
        domains = [row[0].lower().strip() for row in result.fetchall() if row[0]]
        if len(domains) < 3:
            return None
        from collections import Counter
        domain, count = Counter(domains).most_common(1)[0]
        return domain if count >= 3 else None

    async def _get_completion_pattern(
        self, user_id: str, db: AsyncSession
    ) -> str:
        """
        One-line behavioural signal: which task shapes this user actually
        completes vs ignores. The strongest steering signal we have —
        completion rates vary 20x by verb across the user base.
        """
        result = await db.execute(
            text("""
                SELECT
                    lower(split_part(title, ' ', 1)) AS verb,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS done
                FROM daily_tasks
                WHERE user_id = :user_id
                  AND generated_by_ai = TRUE
                GROUP BY verb
                HAVING COUNT(*) >= 3
            """),
            {"user_id": user_id},
        )
        rows = result.fetchall()
        if not rows:
            return "No completion data yet for this user. Favour short, concrete, real-world tasks with a visible finish line."

        completed_verbs = sorted(
            [(r[0], r[2] / r[1]) for r in rows if r[2] > 0],
            key=lambda x: x[1], reverse=True,
        )[:3]
        ignored_verbs = [r[0] for r in rows if r[2] == 0 and r[1] >= 4][:4]

        parts = []
        if completed_verbs:
            verbs = ", ".join(f"'{v}'" for v, _ in completed_verbs)
            parts.append(f"This user completes tasks starting with: {verbs}.")
        if ignored_verbs:
            verbs = ", ".join(f"'{v}'" for v in ignored_verbs)
            parts.append(f"This user has NEVER completed a task starting with: {verbs} — do not generate these shapes.")
        if not parts:
            parts.append("This user has completed almost nothing — generate the smallest, most concrete real-world action possible.")
        return " ".join(parts)

    # Fallback keyword map used ONLY when the AI omits the "domain" field from its
    # JSON response. This is a real, confirmed production bug: for one user, domain
    # was null for 9 consecutive days because the model simply didn't include the
    # field, and _get_dominant_recent_domain had nothing to compare against —
    # rotation silently never fired. The prompt asking for a field is not enough;
    # this is the code-level enforcement (see Engineering Rule 15: ask, then verify).
    DOMAIN_KEYWORD_MAP = [
        (r"\b(community|connect|connection|network|peer|builder)\b", "community-connection"),
        (r"\b(customer|user|client)\b", "customer-understanding"),
        (r"\b(execut|ship|build|launch|deploy|code|develop)\b", "execution"),
        (r"\b(discipline|habit|routine|consisten|morning|evening)\b", "discipline"),
        (r"\b(market|brand|content|social|post|audience)\b", "marketing"),
        (r"\b(lead|team|delegat|manage|hire)\b", "leadership"),
        (r"\b(learn|skill|study|course|read|research)\b", "skill-development"),
        (r"\b(financ|budget|revenue|pric|invest|fund)\b", "finance"),
        (r"\b(faith|pray|spiritual|gratitude|reflect|journal)\b", "reflection"),
    ]

    def _infer_domain_from_title(self, title: str) -> str:
        """
        Best-effort domain inference when the AI omits the domain field.
        Used only as a fallback so rotation checks always have real data —
        never a substitute for the AI naming its own domain when it does.
        """
        import re
        t = (title or "").lower()
        for pattern, domain in self.DOMAIN_KEYWORD_MAP:
            if re.search(pattern, t):
                return domain
        return "uncategorised"

    async def _validate_task(
        self,
        user_id: str,
        task_data: dict,
        dominant_domain: str | None,
        db: AsyncSession,
    ) -> str | None:
        """
        Run all deterministic checks on a generated task.
        Returns a human-readable rejection reason, or None if the task passes.
        Order: missing domain (cheapest, and the confirmed-in-production bug) ->
        forbidden patterns -> duplicate -> domain rotation.
        """
        title = task_data.get("title", "")

        # CONFIRMED BUG FIX: the AI's "domain" field is advisory in the prompt but was
        # being written to the DB as-is, including null when the model omitted it.
        # That silently broke domain rotation for any user whose model output skipped
        # the field. Missing domain is now itself a validation failure, forcing a
        # retry, rather than a silent null that disables rotation with no error.
        raw_domain = (task_data.get("domain") or "").strip()
        if not raw_domain:
            logger.warning(
                "task_missing_domain_field",
                user_id=user_id,
                title=title,
                event="ai_omitted_domain_field",
            )
            return (
                "The 'domain' field was missing from your output. This field is mandatory — "
                "it is used to prevent repeating the same domain of work. Regenerate the same "
                "task idea but include an honest one-to-two-word 'domain' value this time."
            )

        violated = self._violates_forbidden_patterns(title)
        if violated:
            return (
                f"The title contains a coordination-dependent action (matched '{violated}'). "
                f"Tasks must be executable alone, immediately, without another person's "
                f"agreement or an event existing. Generate a solo, real-world action instead."
            )

        if await self._is_title_duplicate(user_id, title, db):
            return (
                f"This exact title was generated for this user within the last 14 days. "
                f"Generate a structurally different task."
            )

        task_domain = raw_domain.lower().strip()
        if dominant_domain and task_domain == dominant_domain:
            return (
                f"The task domain '{task_domain}' matches the user's over-saturated recent "
                f"domain. The last several tasks were all '{dominant_domain}'. "
                f"Choose a completely different domain of their goal."
            )

        return None

    async def _is_title_duplicate(
        self, user_id: str, title: str, db: AsyncSession
    ) -> bool:
        """
        Exact-match duplicate title check against last 14 days.

        Fuzzy matching was removed — it was too aggressive, causing valid AI-generated
        tasks to be rejected and replaced with fallback templates. The semantic
        non-repetition work is now done by the prompt (domain rotation rule).
        This method is the last-resort safety net for exact title repeats only.
        """
        if not title:
            return False

        result = await db.execute(
            text("""
                SELECT title FROM daily_tasks
                WHERE user_id = :user_id
                  AND created_at >= NOW() - INTERVAL '14 days'
                ORDER BY created_at DESC
                LIMIT 20
            """),
            {"user_id": user_id},
        )
        recent_titles = [row[0].lower().strip() for row in result.fetchall() if row[0]]
        return title.lower().strip() in recent_titles

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
            "domain": (
                (task_data.get("domain") or "").lower().strip()
                or self._infer_domain_from_title(task_data.get("title", ""))
            ),
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