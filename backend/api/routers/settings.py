"""
api/routers/settings.py

User settings endpoints including data export and account deletion.
"""

import json
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from core.database import get_db
from db.models.user import User
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
    summary="Request account deletion (GDPR)",
)
async def delete_account(
    request: DeletionConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate account deletion.
    GDPR Article 17: Right to erasure.
    
    - Account immediately deactivated
    - 30-day grace period to cancel
    - Permanent deletion after 30 days
    """
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion by setting confirm=True",
        )
    
    result = await data_export_service.initiate_deletion(current_user.id, db)
    
    logger.info(
        "account_deletion_requested",
        user_id=str(current_user.id),
        reason=request.reason,
    )
    
    return result


@router.post(
    "/cancel-deletion",
    summary="Cancel scheduled account deletion",
)
async def cancel_deletion(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel deletion if within grace period."""
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            UPDATE users
            SET 
                is_active = TRUE,
                deletion_requested_at = NULL,
                deletion_scheduled_at = NULL,
                email = REPLACE(email, CONCAT('.inactive.', EXTRACT(EPOCH FROM deletion_requested_at)::bigint), '')
            WHERE id = :user_id
              AND deletion_scheduled_at IS NOT NULL
              AND deletion_scheduled_at > NOW()
            RETURNING id
        """),
        {"user_id": str(current_user.id)},
    )
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active deletion request found or grace period expired",
        )
    
    logger.info("account_deletion_cancelled", user_id=str(current_user.id))
    
    return {"status": "deletion_cancelled", "message": "Account restored successfully"}


@router.get(
    "/deletion-status",
    summary="Check account deletion status",
)
async def deletion_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if account is scheduled for deletion."""
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            SELECT 
                deletion_requested_at,
                deletion_scheduled_at,
                CASE 
                    WHEN deletion_scheduled_at IS NOT NULL 
                         AND deletion_scheduled_at > NOW() 
                    THEN TRUE 
                    ELSE FALSE 
                END as can_cancel
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": str(current_user.id)},
    )
    
    row = result.fetchone()
    if not row or not row.deletion_scheduled_at:
        return {
            "deletion_scheduled": False,
            "message": "No deletion scheduled",
        }
    
    return {
        "deletion_scheduled": True,
        "requested_at": str(row.deletion_requested_at),
        "scheduled_for": str(row.deletion_scheduled_at),
        "can_cancel": row.can_cancel,
        "days_remaining": max(0, (row.deletion_scheduled_at - __import__('datetime').datetime.utcnow()).days),
    }