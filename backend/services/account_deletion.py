"""
services/account_deletion.py

Account deletion: the request (immediate) and the purge (nightly).
The plan behind every step is in docs/ACCOUNT_DELETION.md.

Request: cancel Stripe, deactivate the account so every scheduled job skips it,
delete push subscriptions, revoke sessions, record a deletion_requests row.

Purge: cancel Stripe again if needed, delete avatar files and the Supabase Auth
user, then delete the users row. ON DELETE CASCADE removes the user's data from
every table that references users(id). Each step tolerates already-deleted state,
so the purge is safe to re-run.
"""

import asyncio
import os

import sentry_sdk
import stripe
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import invalidate_user_context, revoke_refresh_token
from core.config import settings

logger = structlog.get_logger()

stripe.api_key = stripe.api_key or os.getenv("STRIPE_SECRET_KEY")

AVATAR_BUCKET = "avatars"
_FINISHED_STRIPE_STATUSES = {"canceled", "incomplete_expired"}


def _supabase_admin():
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _cancel_stripe_subscription_sync(subscription_id: str) -> str:
    """Cancel immediately. Returns what happened. Raises on any other Stripe error."""
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
    except stripe.error.InvalidRequestError as e:
        if getattr(e, "code", None) == "resource_missing":
            return "not_found"
        raise

    if subscription.get("status") in _FINISHED_STRIPE_STATUSES:
        return "already_cancelled"

    stripe.Subscription.cancel(subscription_id)
    return "cancelled"


async def cancel_stripe_subscription(subscription_id: str | None) -> str:
    if not subscription_id:
        return "none"
    return await asyncio.to_thread(_cancel_stripe_subscription_sync, subscription_id)


async def request_account_deletion(user, db: AsyncSession) -> dict:
    """
    Run when the user confirms deletion. Stripe is cancelled first: if that fails,
    this raises and nothing is marked, so a user is never told their account is
    deleted while their subscription keeps charging.
    """
    user_id = str(user.id)

    stripe_result = await cancel_stripe_subscription(user.stripe_subscription_id)

    await db.execute(
        text("""
            UPDATE users
            SET is_active = FALSE,
                deletion_scheduled_at = NOW(),
                subscription_status = CASE
                    WHEN stripe_subscription_id IS NOT NULL THEN 'ended'
                    ELSE subscription_status
                END
            WHERE id = CAST(:user_id AS uuid)
        """),
        {"user_id": user_id},
    )
    await db.execute(
        text("UPDATE subscriptions SET status = 'ended', updated_at = NOW() WHERE user_id = CAST(:user_id AS uuid)"),
        {"user_id": user_id},
    )
    await db.execute(
        text("DELETE FROM push_subscriptions WHERE user_id = CAST(:user_id AS uuid)"),
        {"user_id": user_id},
    )
    await db.execute(
        text("""
            INSERT INTO deletion_requests (user_id, requested_at, scheduled_for, status)
            VALUES (CAST(:user_id AS uuid), NOW(), NOW(), 'pending')
            ON CONFLICT (user_id) WHERE status = 'pending' DO NOTHING
        """),
        {"user_id": user_id},
    )
    await db.commit()

    await revoke_refresh_token(user_id)
    await invalidate_user_context(user_id)

    logger.info("account_deletion_requested", user_id=user_id, stripe=stripe_result)
    return {"status": "deletion_scheduled", "stripe_subscription": stripe_result}


def _delete_avatar_files_sync(user_id: str) -> int:
    bucket = _supabase_admin().storage.from_(AVATAR_BUCKET)
    files = bucket.list(user_id) or []
    paths = [f"{user_id}/{f['name']}" for f in files if f.get("name")]
    if paths:
        bucket.remove(paths)
    return len(paths)


def _delete_auth_user_sync(auth_user_id: str) -> None:
    _supabase_admin().auth.admin.delete_user(auth_user_id)


async def _find_auth_user_ids(email: str, db: AsyncSession) -> list[str]:
    """Supabase Auth users are linked to our users by email, not by ID."""
    result = await db.execute(
        text("SELECT id::text FROM auth.users WHERE lower(email) = lower(:email)"),
        {"email": email},
    )
    return [row[0] for row in result.fetchall()]


async def purge_user(user_id: str, email: str, stripe_subscription_id: str | None, db: AsyncSession) -> dict:
    """
    Permanently delete one user. External systems first: if any of them fails this
    raises before the database delete, and the nightly purge retries the user.
    """
    stripe_result = await cancel_stripe_subscription(stripe_subscription_id)
    avatars_removed = await asyncio.to_thread(_delete_avatar_files_sync, user_id)

    auth_ids = await _find_auth_user_ids(email, db)
    for auth_id in auth_ids:
        await asyncio.to_thread(_delete_auth_user_sync, auth_id)

    await db.execute(
        text("""
            UPDATE ai_interactions
            SET error_message = NULL, request_hash = NULL
            WHERE user_id = CAST(:user_id AS uuid)
        """),
        {"user_id": user_id},
    )
    await db.execute(text("DELETE FROM users WHERE id = CAST(:user_id AS uuid)"), {"user_id": user_id})

    completed = await db.execute(
        text("""
            UPDATE deletion_requests
            SET status = 'completed', completed_at = NOW()
            WHERE user_id = CAST(:user_id AS uuid) AND status = 'pending'
        """),
        {"user_id": user_id},
    )
    if completed.rowcount == 0:
        # Deletion set up by hand (for example an email request): still leave a record.
        await db.execute(
            text("""
                INSERT INTO deletion_requests (user_id, requested_at, scheduled_for, status, completed_at)
                VALUES (CAST(:user_id AS uuid), NOW(), NOW(), 'completed', NOW())
            """),
            {"user_id": user_id},
        )
    await db.commit()

    # No PostHog personal API key is configured, so the person cannot be deleted from here.
    logger.warning("posthog_person_delete_manual", user_id=user_id)

    result = {
        "user_id": user_id,
        "stripe": stripe_result,
        "avatars_removed": avatars_removed,
        "auth_users_removed": len(auth_ids),
    }
    logger.info("user_data_purged", **result)
    return result


async def run_purge() -> int:
    """Purge every account whose deletion is due. Returns how many were purged."""
    from core.database import get_db_context

    async with get_db_context() as db:
        rows = (await db.execute(text("""
            SELECT id::text, email, stripe_subscription_id
            FROM users
            WHERE deletion_scheduled_at IS NOT NULL AND deletion_scheduled_at <= NOW()
            ORDER BY deletion_scheduled_at
            LIMIT 100
        """))).fetchall()

    purged = 0
    for user_id, email, stripe_subscription_id in rows:
        try:
            async with get_db_context() as db:
                await purge_user(user_id, email, stripe_subscription_id, db)
            purged += 1
        except Exception as e:
            logger.error("user_purge_failed", user_id=user_id, error=str(e), exc_info=True)
            sentry_sdk.capture_exception(e, tags={"purge_user_id": user_id})

    logger.info("data_purge_complete", purged_count=purged, total_found=len(rows))
    return purged
