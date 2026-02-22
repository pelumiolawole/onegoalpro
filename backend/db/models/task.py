"""
db/models/task.py

ORM models for daily tasks and reflections.
"""

import enum
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    MISSED = "missed"


class TaskType(str, enum.Enum):
    BECOMING = "becoming"
    IDENTITY_ANCHOR = "identity_anchor"
    MICRO_ACTION = "micro_action"
    CHALLENGE = "challenge"


class ReflectionSentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    RESISTANT = "resistant"
    STRUGGLING = "struggling"
    BREAKTHROUGH = "breakthrough"


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"))
    objective_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("objectives.id", ondelete="SET NULL"))

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    task_type: Mapped[TaskType] = mapped_column(String, nullable=False, default=TaskType.BECOMING)
    status: Mapped[TaskStatus] = mapped_column(String, nullable=False, default=TaskStatus.PENDING)

    # AI-generated content
    identity_focus: Mapped[str | None] = mapped_column(Text)  # "Today you are someone who..."
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    execution_guidance: Mapped[str | None] = mapped_column(Text)

    # Metadata
    time_estimate_minutes: Mapped[int | None] = mapped_column(Integer)
    difficulty_level: Mapped[int | None] = mapped_column(Integer)
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=True)
    generation_context: Mapped[dict | None] = mapped_column(JSONB)  # snapshot of context used

    # Execution tracking
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    skip_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reflection: Mapped["Reflection"] = relationship(  # noqa: F821
        "Reflection", back_populates="task", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DailyTask id={self.id} date={self.scheduled_date} status={self.status}>"

    @property
    def is_today(self) -> bool:
        return self.scheduled_date == date.today()

    @property
    def is_overdue(self) -> bool:
        return self.scheduled_date < date.today() and self.status == TaskStatus.PENDING


class Reflection(Base):
    __tablename__ = "reflections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("daily_tasks.id", ondelete="SET NULL"))

    reflection_date: Mapped[date] = mapped_column(Date, nullable=False)
    questions_answers: Mapped[list | None] = mapped_column(JSONB)  # [{"question": "...", "answer": "..."}]

    # AI Analysis results
    sentiment: Mapped[ReflectionSentiment | None] = mapped_column(String)
    depth_score: Mapped[float | None] = mapped_column(Numeric(4, 2))  # 1-10
    word_count: Mapped[int | None] = mapped_column(Integer)
    emotional_tone: Mapped[str | None] = mapped_column(String(50))
    key_themes: Mapped[list | None] = mapped_column(ARRAY(Text))

    # Signals
    resistance_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    breakthrough_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    resistance_signals: Mapped[list | None] = mapped_column(ARRAY(Text))

    # AI output
    ai_insight: Mapped[str | None] = mapped_column(Text)
    ai_feedback_shown: Mapped[str | None] = mapped_column(Text)
    trait_evidence: Mapped[dict | None] = mapped_column(JSONB)

    # Timing
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    task: Mapped["DailyTask"] = relationship("DailyTask", back_populates="reflection")

    def __repr__(self) -> str:
        return f"<Reflection id={self.id} date={self.reflection_date} sentiment={self.sentiment}>"
