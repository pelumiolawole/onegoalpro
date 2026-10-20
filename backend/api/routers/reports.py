"""
api/routers/reports.py

Users report AI-generated content (coach replies, interview messages, daily tasks).
Required by Google Play's AI-generated content policy.
"""

from typing import Literal, Optional

import sentry_sdk
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_active_user
from core.database import get_db
from db.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/reports", tags=["Reports"])

MAX_EXCERPT_CHARS = 1000
MAX_REPORTS_PER_HOUR = 20


class AIContentReportRequest(BaseModel):
    source: Literal["coach", "interview", "task"]
    reason: Literal["offensive", "inaccurate", "inappropriate_advice", "other"]
    content: str = Field(min_length=1, max_length=20000)
    reference_id: Optional[str] = Field(None, max_length=100)
    details: Optional[str] = Field(None, max_length=1000)


@router.post("/ai-content", status_code=status.HTTP_201_CREATED)
async def report_ai_content(
    body: AIContentReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a user's report of AI-generated content."""
    recent = (await db.execute(
        text("""
            SELECT COUNT(*) FROM ai_content_reports
            WHERE user_id = CAST(:user_id AS uuid) AND created_at > NOW() - INTERVAL '1 hour'
        """),
        {"user_id": str(current_user.id)},
    )).scalar_one()
    if recent >= MAX_REPORTS_PER_HOUR:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many reports. Try again later.")

    details = (body.details or "").strip() or None
    row = (await db.execute(
        text("""
            INSERT INTO ai_content_reports (user_id, source, reference_id, content_excerpt, reason, details)
            VALUES (CAST(:user_id AS uuid), :source, :reference_id, :excerpt, :reason, :details)
            RETURNING id
        """),
        {
            "user_id": str(current_user.id),
            "source": body.source,
            "reference_id": body.reference_id,
            "excerpt": body.content.strip()[:MAX_EXCERPT_CHARS],
            "reason": body.reason,
            "details": details,
        },
    )).first()
    await db.commit()

    report_id = str(row[0])
    # Event name and report ID only: never the reported content.
    sentry_sdk.capture_message("ai_content_reported", level="warning", tags={"report_id": report_id, "source": body.source})
    logger.info("ai_content_reported", report_id=report_id, source=body.source, reason=body.reason)
    return {"status": "received", "report_id": report_id}
