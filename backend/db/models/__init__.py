"""
db/models/__init__.py

Import all models here so Alembic can discover them for autogenerate,
and so they're importable from a single location.

Usage:
    from db.models import User, Goal, DailyTask, Reflection, IdentityProfile
"""

from db.models.goal import Goal, IdentityTrait, Objective
from db.models.identity_profile import IdentityProfile
from db.models.task import DailyTask, Reflection
from db.models.user import User

__all__ = [
    "User",
    "IdentityProfile",
    "Goal",
    "Objective",
    "IdentityTrait",
    "DailyTask",
    "Reflection",
]
