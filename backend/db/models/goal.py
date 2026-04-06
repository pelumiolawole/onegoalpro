"""
db/models/goal.py

SQLAlchemy ORM models for goals, objectives, milestones, and identity traits.
"""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    APPROACHING_COMPLETION = "approaching_completion"  # NEW: system-flagged, invisible to user
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ObjectiveStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TraitCategory(str, enum.Enum):
    MINDSET = "mindset"
    BEHAVIOR = "behavior"
    DISCIPLINE = "discipline"
    SOCIAL = "social"
    EMOTIONAL = "emotional"
    COGNITIVE = "cognitive"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[GoalStatus] = mapped_column(String, nullable=False, default=GoalStatus.ACTIVE)

    # Raw and refined goal content
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    refined_statement: Mapped[str | None] = mapped_column(Text)
    why_statement: Mapped[str | None] = mapped_column(Text)
    success_definition: Mapped[str | None] = mapped_column(Text)
    required_identity: Mapped[str | None] = mapped_column(Text)
    key_shifts: Mapped[list | None] = mapped_column(ARRAY(Text))

    # Planning
    estimated_timeline: Mapped[int | None] = mapped_column(Integer)  # weeks
    difficulty_level: Mapped[int | None] = mapped_column(Integer)    # 1-10
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Lifecycle
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    abandoned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    abandon_reason: Mapped[str | None] = mapped_column(Text)

    # Completion tracking — populated by scheduler when approaching_completion is flagged
    approaching_completion_flagged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_check_score: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")  # noqa: F821
    objectives: Mapped[list["Objective"]] = relationship("Objective", back_populates="goal", lazy="selectin", order_by="Objective.sequence_order")
    identity_traits: Mapped[list["IdentityTrait"]] = relationship("IdentityTrait", back_populates="goal", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Goal id={self.id} status={self.status}>"

    @property
    def weeks_active(self) -> int:
        if not self.started_at:
            return 0
        delta = datetime.now(self.started_at.tzinfo) - self.started_at
        return delta.days // 7

    @property
    def is_approaching_completion(self) -> bool:
        return self.status == GoalStatus.APPROACHING_COMPLETION


class Objective(Base):
    __tablename__ = "objectives"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    success_criteria: Mapped[str | None] = mapped_column(Text)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_weeks: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[ObjectiveStatus] = mapped_column(String, nullable=False, default=ObjectiveStatus.UPCOMING)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    goal: Mapped["Goal"] = relationship("Goal", back_populates="objectives")


class IdentityTrait(Base):
    __tablename__ = "identity_traits"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"))

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[TraitCategory] = mapped_column(String, nullable=False, default=TraitCategory.BEHAVIOR)

    current_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=5.0)
    target_score: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=8.0)
    velocity: Mapped[float] = mapped_column(Numeric(4, 3), default=0.0)  # change per week

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    goal: Mapped["Goal"] = relationship("Goal", back_populates="identity_traits")

    @property
    def gap(self) -> float:
        return float(self.target_score) - float(self.current_score)

    @property
    def progress_pct(self) -> float:
        if float(self.target_score) == 0:
            return 0
        return round(float(self.current_score) / float(self.target_score) * 100, 1)