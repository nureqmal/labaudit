import uuid
from datetime import datetime, date, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CapaType(str, PyEnum):
    CORRECTIVE  = "corrective"
    PREVENTIVE  = "preventive"
    IMPROVEMENT = "improvement"


class CapaPriority(str, PyEnum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class CapaStatus(str, PyEnum):
    OPEN        = "open"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    CLOSED      = "closed"
    OVERDUE     = "overdue"


class CapaItem(Base):
    __tablename__ = "capa_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    raised_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # ─── Reference & Classification ───────────────────────
    reference_no: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    capa_type: Mapped[CapaType] = mapped_column(
        Enum(CapaType, name="capa_type_enum"), nullable=False
    )
    priority: Mapped[CapaPriority] = mapped_column(
        Enum(CapaPriority, name="capa_priority_enum"),
        default=CapaPriority.MEDIUM, nullable=False,
    )
    department: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)

    # ─── Description & Root Cause ─────────────────────────
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ─── Source ───────────────────────────────────────────
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # e.g. "Internal Audit", "Customer Complaint", "Proficiency Test"

    # ─── Dates ────────────────────────────────────────────
    raised_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ─── Status ───────────────────────────────────────────
    status: Mapped[CapaStatus] = mapped_column(
        Enum(CapaStatus, name="capa_status_enum"),
        default=CapaStatus.OPEN, nullable=False, index=True,
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
        "Organization", back_populates="capa_items"
    )
    raised_by_user: Mapped["User"] = relationship(         # noqa: F821
        "User", back_populates="raised_capas", foreign_keys=[raised_by]
    )
    assigned_to_user: Mapped["User"] = relationship(       # noqa: F821
        "User", back_populates="assigned_capas", foreign_keys=[assigned_to]
    )

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.status == CapaStatus.CLOSED:
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    def __repr__(self) -> str:
        return f"<CapaItem {self.reference_no!r} status={self.status.value}>"
