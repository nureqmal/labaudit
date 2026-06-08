import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class AuditLog(Base):
    """
    Immutable audit trail. Never update or delete rows from this table.
    Every write action in the app should create a log entry.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # ─── What happened ────────────────────────────────────
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "document.create", "capa.status_change", "user.login"

    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g. "document", "capa_item", "calibration_record"

    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    # UUID of the affected record as string

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Human-readable description

    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {"field": {"before": "...", "after": "..."}}

    # ─── Context ──────────────────────────────────────────
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ─── Relationships ────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action!r} by user={self.user_id}>"
