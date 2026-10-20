"""
core/time_budget.py

The user's daily time budget: how many minutes a day they can give their
goal, and when they usually have that time. Asked as a structured question
(onboarding and Settings), not inferred by the AI interview, because the
interview captured it for 4 of 50 users. Stored on identity_profiles.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DAILY_MINUTES_OPTIONS = (10, 20, 30, 45, 60)   # 60 means "1 hour+"
PREFERRED_TIME_OPTIONS = ("morning", "midday", "evening", "varies")
DEFAULT_DAILY_MINUTES = 20                     # used for generation when not yet answered

PREFERRED_TIME_LABELS = {
    "morning": "in the morning",
    "midday": "around midday",
    "evening": "in the evening",
    "varies": "at varying times of day",
}


async def get_time_budget(user_id: str, db: AsyncSession) -> dict:
    """{'daily_minutes': int|None, 'preferred_time': str|None} as stored (None if unanswered)."""
    row = (await db.execute(
        text("""
            SELECT daily_minutes, preferred_time FROM identity_profiles
            WHERE user_id = CAST(:user_id AS uuid)
        """),
        {"user_id": str(user_id)},
    )).first()
    if not row:
        return {"daily_minutes": None, "preferred_time": None}
    return {"daily_minutes": row[0], "preferred_time": row[1]}


async def save_time_budget(user_id: str, daily_minutes: int, preferred_time: str, db: AsyncSession) -> None:
    if daily_minutes not in DAILY_MINUTES_OPTIONS:
        raise ValueError("daily_minutes must be one of 10, 20, 30, 45, 60")
    if preferred_time not in PREFERRED_TIME_OPTIONS:
        raise ValueError("preferred_time must be morning, midday, evening or varies")
    await db.execute(
        text("""
            INSERT INTO identity_profiles (user_id, daily_minutes, preferred_time)
            VALUES (CAST(:user_id AS uuid), :minutes, :pref)
            ON CONFLICT (user_id) DO UPDATE
               SET daily_minutes = EXCLUDED.daily_minutes,
                   preferred_time = EXCLUDED.preferred_time
        """),
        {"user_id": str(user_id), "minutes": daily_minutes, "pref": preferred_time},
    )
