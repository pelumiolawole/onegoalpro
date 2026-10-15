"""
api/routers/settings.py

User settings endpoints including data export and account deletion.
"""

import json
from datetime import datetime, timezone
from typing import Optional

import stripe
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import bearer_scheme, get_current_user
from core.cache import blocklist_access_token
from core.security import decode_token
from core.database import get_db
from db.models.user import User
from services.account_deletion import request_account_deletion
from services.data_export import data_export_service

logger = structlog.get_logger()

router = APIRouter(prefix="/settings", tags=["Settings"])


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class DeletionConfirmRequest(BaseModel):
    confirm: bool = Field(description="Must be True to confirm deletion")
    reason: Optional[str] = Field(None, max_length=500)


@router.post(
    "/export-data",
    summary="Export all user data (GDPR)",
)
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all personal data as JSON.
    GDPR Article 20: Right to data portability.
    """
    export_data = await data_export_service.export_user_data(current_user.id, db)
    
    # Create filename with timestamp
    timestamp = __import__('datetime').datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"onegoal_export_{current_user.id}_{timestamp}.json"
    
    logger.info(
        "data_export_downloaded",
        user_id=str(current_user.id),
        filename=filename,
    )
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/json",
        },
    )


@router.post(
    "/delete-account",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Delete account (GDPR Article 17)",
)
async def delete_account(
    request: DeletionConfirmRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete the account. Cannot be undone.

    Now: cancels any Stripe subscription, deactivates the account (which stops
    emails, push and task generation), deletes push subscriptions and signs the
    user out everywhere. Within 24 hours: the nightly purge deletes all data.
    See docs/ACCOUNT_DELETION.md.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion by setting confirm=True",
        )

    try:
        result = await request_account_deletion(current_user, db)
    except stripe.error.StripeError as e:
        logger.error("account_deletion_stripe_failed", user_id=str(current_user.id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We couldn't cancel your subscription just now, so your account was not deleted. Please try again in a few minutes.",
        )

    # Blocklist the access token used for this request until it expires.
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        jti = payload.get("jti")
        if jti:
            ttl = max(int(payload.get("exp", 0) - datetime.now(timezone.utc).timestamp()), 1)
            await blocklist_access_token(jti, ttl)
    except Exception:
        pass  # Every other route now rejects this account anyway (get_current_user)

    if request.reason:
        logger.info("account_deletion_reason", user_id=str(current_user.id), reason=request.reason)

    return result
