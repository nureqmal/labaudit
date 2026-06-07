import uuid
from datetime import datetime, date, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class CalibrationStatus(str, PyEnum):
    CURRENT      = "current"
    DUE_SOON     = "due_soon"      # within 30 days
    OVERDUE      = "overdue"
    OUT_OF_SERVICE = "out_of_service"


class CalibrationRecord(Base):
    __tablename__ = "calibration_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Equipment Info ───────────────────────────────────
    equipment_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # ─── Calibration Details ──────────────────────────────
    calibrated_by: Mapped[str | None] = mapped_column(String(200), nullable=True)  # external lab
    calibration_standard: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ─── Dates ────────────────────────────────────────────
    last_calibrated: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_due: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    calibration_interval_days: Mapped[int | None] = mapped_column(nullable=True)  # e.g. 365

    # ─── Status ───────────────────────────────────────────
    status: Mapped[CalibrationStatus] = mapped_column(
        Enum(CalibrationStatus, name="calibration_status_enum"),
        default=CalibrationStatus.CURRENT, nullable=False, index=True,
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
        "Organization", back_populates="calibration_records"
    )
    assigned_to_user: Mapped["User"] = relationship(       # noqa: F821
        "User", back_populates="assigned_calibrations", foreign_keys=[assigned_to]
    )

    @property
    def days_until_due(self) -> int | None:
        if not self.next_due:
            return None
        return (self.next_due - date.today()).days

    @property
    def is_overdue(self) -> bool:
        if not self.next_due:
            return False
        return date.today() > self.next_due

    def __repr__(self) -> str:
        return f"<CalibrationRecord {self.equipment_id!r} status={self.status.value}>"
