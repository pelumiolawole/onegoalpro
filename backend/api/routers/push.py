"""
api/routers/push.py
Stores and manages web push subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_active_user
from core.database import get_db
from db.models.user import User

router = APIRouter(prefix="/api/push", tags=["push"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: str = ""


@router.post("/subscribe")
async def subscribe(
    sub: PushSubscriptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Store or update a push subscription for the current user."""
    await db.execute(
        text("""
            INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, user_agent)
            VALUES (CAST(:user_id AS uuid), :endpoint, :p256dh, :auth, :user_agent)
            ON CONFLICT (user_id) DO UPDATE
            SET endpoint = EXCLUDED.endpoint,
                p256dh = EXCLUDED.p256dh,
                auth = EXCLUDED.auth,
                user_agent = EXCLUDED.user_agent,
                updated_at = NOW()
        """),
        {
            "user_id": str(current_user.id),
            "endpoint": sub.endpoint,
            "p256dh": sub.p256dh,
            "auth": sub.auth,
            "user_agent": sub.user_agent,
        },
    )
    await db.commit()
    return {"status": "subscribed"}


@router.delete("/unsubscribe")
async def unsubscribe(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove push subscription for the current user."""
    await db.execute(
        text("DELETE FROM push_subscriptions WHERE user_id = CAST(:user_id AS uuid)"),
        {"user_id": str(current_user.id)},
    )
    await db.commit()
    return {"status": "unsubscribed"}
