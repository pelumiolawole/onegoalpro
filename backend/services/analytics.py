"""
services/analytics.py

Product analytics using PostHog.
"""

from posthog import Posthog
from core.config import settings

# Initialize PostHog
posthog = Posthog(
    settings.posthog_api_key,
    host=settings.posthog_host,
    disabled=not settings.posthog_api_key,
)


def identify_user(user_id: str, email: str, properties: dict = None):
    """Identify a user in PostHog"""
    if not settings.posthog_api_key:
        return
    
    props = properties or {}
    props["email"] = email
    
    posthog.identify(user_id, props)


def track_event(user_id: str, event: str, properties: dict = None):
    """Track an event in PostHog"""
    if not settings.posthog_api_key:
        return
    
    posthog.capture(user_id, event, properties or {})


def track_signup(user_id: str, email: str, provider: str = "email"):
    """Track user signup"""
    identify_user(user_id, email, {"signup_provider": provider})
    track_event(user_id, "user_signed_up", {"provider": provider})


def track_login(user_id: str, email: str):
    """Track user login"""
    track_event(user_id, "user_logged_in")


def track_goal_created(user_id: str, goal_title: str):
    """Track goal creation"""
    track_event(user_id, "goal_created", {"goal_title": goal_title})


def track_task_completed(user_id: str, task_title: str):
    """Track task completion"""
    track_event(user_id, "task_completed", {"task_title": task_title})