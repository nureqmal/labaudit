import uuid
from datetime import datetime, date, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TrainingType(str, PyEnum):
    INDUCTION        = "induction"
    SOP_TRAINING     = "sop_training"
    SAFETY           = "safety"
    EQUIPMENT        = "equipment"
    QUALITY_SYSTEMS  = "quality_systems"
    REGULATORY       = "regulatory"
    EXTERNAL_COURSE  = "external_course"
    ON_THE_JOB       = "on_the_job"
    OTHER            = "other"


class TrainingStatus(str, PyEnum):
    CURRENT   = "current"
    DUE_SOON  = "due_soon"    # renewal within 30 days
    OVERDUE   = "overdue"
    COMPLETED = "completed"   # one-time training (no expiry)


class TrainingRecord(Base):
    __tablename__ = "training_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # ─── Training Info ────────────────────────────────────
    training_title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    training_type: Mapped[TrainingType] = mapped_column(
        Enum(TrainingType, name="training_type_enum"), nullable=False
    )
    trainer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    training_provider: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sop_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ─── Dates ────────────────────────────────────────────
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # ─── Status ───────────────────────────────────────────
    status: Mapped[TrainingStatus] = mapped_column(
        Enum(TrainingStatus, name="training_status_enum"),
        default=TrainingStatus.COMPLETED, nullable=False, index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ─── Relationships ────────────────────────────────────
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="training_records"
    )
    user: Mapped["User"] = relationship(                   # noqa: F821
        "User", back_populates="training_records"
    )

    @property
    def days_until_expiry(self) -> int | None:
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_overdue(self) -> bool:
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    def __repr__(self) -> str:
        return f"<TrainingRecord {self.training_title!r} status={self.status.value}>"
