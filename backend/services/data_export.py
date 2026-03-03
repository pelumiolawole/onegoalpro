"""
services/data_export.py

Data export and deletion service for GDPR compliance.
Aggregates all user data into downloadable format.
"""

import json
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DataExportService:
    """Service for exporting and deleting user data."""

    async def export_user_data(
        self,
        user_id: UUID | str,
        db: AsyncSession,
    ) -> dict:
        """
        Export all user data as a structured dictionary.
        Includes: profile, goals, tasks, reflections, coach sessions, safety flags.
        """
        uid = str(user_id)
        export_timestamp = datetime.utcnow().isoformat()

        # Build comprehensive export
        export_data = {
            "export_metadata": {
                "user_id": uid,
                "exported_at": export_timestamp,
                "version": "1.0",
                "platform": "OneGoal Pro",
            },
            "user_profile": await self._get_user_profile(uid, db),
            "identity_profile": await self._get_identity_profile(uid, db),
            "goals": await self._get_goals(uid, db),
            "daily_tasks": await self._get_daily_tasks(uid, db),
            "reflections": await self._get_reflections(uid, db),
            "coach_sessions": await self._get_coach_sessions(uid, db),
            "weekly_reviews": await self._get_weekly_reviews(uid, db),
            "safety_flags": await self._get_safety_flags(uid, db),
            "progress_metrics": await self._get_progress_metrics(uid, db),
        }

        logger.info("user_data_exported", user_id=uid, timestamp=export_timestamp)
        return export_data

    async def _get_user_profile(self, user_id: str, db: AsyncSession) -> dict:
        """Get basic user account info."""
        result = await db.execute(
            text("""
                SELECT 
                    email, display_name, timezone, locale,
                    onboarding_status, is_active, created_at, last_seen_at
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return {}
        
        return {
            "email": row.email,
            "display_name": row.display_name,
            "timezone": row.timezone,
            "locale": row.locale,
            "onboarding_status": row.onboarding_status,
            "is_active": row.is_active,
            "created_at": str(row.created_at) if row.created_at else None,
            "last_seen_at": str(row.last_seen_at) if row.last_seen_at else None,
        }

    async def _get_identity_profile(self, user_id: str, db: AsyncSession) -> dict:
        """Get identity profile data."""
        result = await db.execute(
            text("""
                SELECT 
                    life_direction, personal_vision, core_values,
                    self_reported_strengths, self_reported_weaknesses,
                    time_availability, lifestyle_context, resistance_triggers,
                    motivation_style, peak_performance_time, consistency_pattern,
                    last_ai_update
                FROM identity_profiles
                WHERE user_id = :user_id
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return {}
        
        return {
            "life_direction": row.life_direction,
            "personal_vision": row.personal_vision,
            "core_values": row.core_values,
            "self_reported_strengths": row.self_reported_strengths,
            "self_reported_weaknesses": row.self_reported_weaknesses,
            "time_availability": row.time_availability,
            "lifestyle_context": row.lifestyle_context,
            "resistance_triggers": row.resistance_triggers,
            "motivation_style": row.motivation_style,
            "peak_performance_time": row.peak_performance_time,
            "consistency_pattern": row.consistency_pattern,
            "last_ai_update": str(row.last_ai_update) if row.last_ai_update else None,
        }

    async def _get_goals(self, user_id: str, db: AsyncSession) -> list:
        """Get all goals."""
        result = await db.execute(
            text("""
                SELECT 
                    id, title, description, status,
                    why_statement, success_definition, required_identity,
                    estimated_timeline_weeks, difficulty_level,
                    created_at, completed_at
                FROM goals
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id},
        )
        
        goals = []
        for row in result.fetchall():
            goals.append({
                "id": str(row.id),
                "title": row.title,
                "description": row.description,
                "status": row.status,
                "why_statement": row.why_statement,
                "success_definition": row.success_definition,
                "required_identity": row.required_identity,
                "estimated_timeline_weeks": row.estimated_timeline_weeks,
                "difficulty_level": row.difficulty_level,
                "created_at": str(row.created_at),
                "completed_at": str(row.completed_at) if row.completed_at else None,
            })
        return goals

    async def _get_daily_tasks(self, user_id: str, db: AsyncSession) -> list:
        """Get all daily tasks."""
        result = await db.execute(
            text("""
                SELECT 
                    id, title, description, identity_focus,
                    time_estimate_minutes, difficulty_level, task_type,
                    status, scheduled_date, completed_at, skipped_reason
                FROM daily_tasks
                WHERE user_id = :user_id
                ORDER BY scheduled_date DESC
                LIMIT 1000
            """),
            {"user_id": user_id},
        )
        
        tasks = []
        for row in result.fetchall():
            tasks.append({
                "id": str(row.id),
                "title": row.title,
                "description": row.description,
                "identity_focus": row.identity_focus,
                "time_estimate_minutes": row.time_estimate_minutes,
                "difficulty_level": row.difficulty_level,
                "task_type": row.task_type,
                "status": row.status,
                "scheduled_date": str(row.scheduled_date),
                "completed_at": str(row.completed_at) if row.completed_at else None,
                "skipped_reason": row.skipped_reason,
            })
        return tasks

    async def _get_reflections(self, user_id: str, db: AsyncSession) -> list:
        """Get all reflections."""
        result = await db.execute(
            text("""
                SELECT 
                    id, task_id, sentiment, depth_score,
                    emotional_tone, key_themes, resistance_detected,
                    breakthrough_detected, ai_feedback_shown, ai_insight,
                    reflection_date, created_at
                FROM reflections
                WHERE user_id = :user_id
                ORDER BY reflection_date DESC
                LIMIT 1000
            """),
            {"user_id": user_id},
        )
        
        reflections = []
        for row in result.fetchall():
            reflections.append({
                "id": str(row.id),
                "task_id": str(row.task_id),
                "sentiment": row.sentiment,
                "depth_score": float(row.depth_score) if row.depth_score else None,
                "emotional_tone": row.emotional_tone,
                "key_themes": row.key_themes,
                "resistance_detected": row.resistance_detected,
                "breakthrough_detected": row.breakthrough_detected,
                "ai_feedback_shown": row.ai_feedback_shown,
                "ai_insight": row.ai_insight,
                "reflection_date": str(row.reflection_date),
                "created_at": str(row.created_at),
            })
        return reflections

    async def _get_coach_sessions(self, user_id: str, db: AsyncSession) -> list:
        """Get coach sessions with messages."""
        result = await db.execute(
            text("""
                SELECT 
                    id, coaching_mode, message_count, started_at, ended_at
                FROM ai_coach_sessions
                WHERE user_id = :user_id
                ORDER BY started_at DESC
                LIMIT 100
            """),
            {"user_id": user_id},
        )
        
        sessions = []
        for row in result.fetchall():
            session_id = str(row.id)
            
            # Get messages for this session
            messages_result = await db.execute(
                text("""
                    SELECT role, content, created_at
                    FROM ai_coach_messages
                    WHERE session_id = :session_id
                    ORDER BY created_at ASC
                """),
                {"session_id": session_id},
            )
            
            messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": str(msg.created_at),
                }
                for msg in messages_result.fetchall()
            ]
            
            sessions.append({
                "id": session_id,
                "coaching_mode": row.coaching_mode,
                "message_count": row.message_count,
                "started_at": str(row.started_at),
                "ended_at": str(row.ended_at) if row.ended_at else None,
                "messages": messages,
            })
        return sessions

    async def _get_weekly_reviews(self, user_id: str, db: AsyncSession) -> list:
        """Get weekly reviews."""
        result = await db.execute(
            text("""
                SELECT 
                    week_start_date, week_end_date,
                    tasks_completed, tasks_total, reflections_submitted,
                    avg_depth_score, consistency_pct, score_delta,
                    evolution_letter, generated_at, read_at
                FROM weekly_reviews
                WHERE user_id = :user_id
                ORDER BY week_start_date DESC
            """),
            {"user_id": user_id},
        )
        
        reviews = []
        for row in result.fetchall():
            reviews.append({
                "week_start_date": str(row.week_start_date),
                "week_end_date": str(row.week_end_date),
                "tasks_completed": row.tasks_completed,
                "tasks_total": row.tasks_total,
                "reflections_submitted": row.reflections_submitted,
                "avg_depth_score": float(row.avg_depth_score) if row.avg_depth_score else None,
                "consistency_pct": float(row.consistency_pct) if row.consistency_pct else None,
                "score_delta": float(row.score_delta) if row.score_delta else None,
                "evolution_letter": row.evolution_letter,
                "generated_at": str(row.generated_at),
                "read_at": str(row.read_at) if row.read_at else None,
            })
        return reviews

    async def _get_safety_flags(self, user_id: str, db: AsyncSession) -> list:
        """Get safety flags."""
        result = await db.execute(
            text("""
                SELECT 
                    flag_type, severity, excerpt, ai_response,
                    resources_shown, reviewed, created_at
                FROM ai_safety_flags
                WHERE user_id = :user_id
                ORDER BY created_at DESC
            """),
            {"user_id": user_id},
        )
        
        flags = []
        for row in result.fetchall():
            flags.append({
                "flag_type": row.flag_type,
                "severity": row.severity,
                "excerpt": row.excerpt,
                "ai_response": row.ai_response,
                "resources_shown": row.resources_shown,
                "reviewed": row.reviewed,
                "created_at": str(row.created_at),
            })
        return flags

    async def _get_progress_metrics(self, user_id: str, db: AsyncSession) -> list:
        """Get progress metrics."""
        result = await db.execute(
            text("""
                SELECT 
                    metric_date, transformation_score, consistency_score,
                    depth_score, momentum_state, task_completed,
                    reflection_submitted, streak_at_date
                FROM progress_metrics
                WHERE user_id = :user_id
                ORDER BY metric_date DESC
                LIMIT 365
            """),
            {"user_id": user_id},
        )
        
        metrics = []
        for row in result.fetchall():
            metrics.append({
                "metric_date": str(row.metric_date),
                "transformation_score": float(row.transformation_score) if row.transformation_score else None,
                "consistency_score": float(row.consistency_score) if row.consistency_score else None,
                "depth_score": float(row.depth_score) if row.depth_score else None,
                "momentum_state": row.momentum_state,
                "task_completed": row.task_completed,
                "reflection_submitted": row.reflection_submitted,
                "streak_at_date": row.streak_at_date,
            })
        return metrics

    async def initiate_deletion(
        self,
        user_id: UUID | str,
        db: AsyncSession,
    ) -> dict:
        """
        Initiate account deletion (soft delete).
        Data is marked for purge after 30 days.
        """
        uid = str(user_id)
        
        # Mark user for deletion
        await db.execute(
            text("""
                UPDATE users
                SET 
                    is_active = FALSE,
                    deletion_requested_at = NOW(),
                    deletion_scheduled_at = NOW() + INTERVAL '30 days',
                    email = CONCAT(email, '.inactive.', EXTRACT(EPOCH FROM NOW())::bigint)
                WHERE id = :user_id
            """),
            {"user_id": uid},
        )
        
        logger.info("user_deletion_initiated", user_id=uid, grace_period_days=30)
        
        return {
            "status": "deletion_scheduled",
            "user_id": uid,
            "deletion_scheduled_at": (datetime.utcnow() + __import__('datetime').timedelta(days=30)).isoformat(),
            "grace_period_days": 30,
            "message": "Account deactivated. Data will be permanently deleted after 30 days. Contact support to cancel.",
        }


# Singleton instance
data_export_service = DataExportService()