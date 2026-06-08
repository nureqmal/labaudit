import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UserRole(str, PyEnum):
    ADMIN   = "admin"
    MANAGER = "manager"
    VIEWER  = "viewer"


class User(Base):
    __tablename__ = "users"

    # ─── Primary Key ──────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ─── Foreign Keys ─────────────────────────────────────
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # ─── Auth Fields ──────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ─── Profile Fields ───────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # ─── RBAC ─────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"), default=UserRole.VIEWER, nullable=False
    )

    # ─── Status ───────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Timestamps ───────────────────────────────────────
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ─── Relationships ────────────────────────────────────
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="users"
    )
    owned_documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="owner", foreign_keys="Document.owner_id"
    )
    assigned_calibrations: Mapped[list["CalibrationRecord"]] = relationship(  # noqa: F821
        "CalibrationRecord", back_populates="assigned_to_user",
        foreign_keys="CalibrationRecord.assigned_to",
    )
    training_records: Mapped[list["TrainingRecord"]] = relationship(  # noqa: F821
        "TrainingRecord", back_populates="user"
    )
    raised_capas: Mapped[list["CapaItem"]] = relationship(  # noqa: F821
        "CapaItem", back_populates="raised_by_user",
        foreign_keys="CapaItem.raised_by",
    )
    assigned_capas: Mapped[list["CapaItem"]] = relationship(  # noqa: F821
        "CapaItem", back_populates="assigned_to_user",
        foreign_keys="CapaItem.assigned_to",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="user"
    )

    # ─── Helpers ──────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_manager_or_above(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.MANAGER)

    def __repr__(self) -> str:
        return f"<User {self.email!r} role={self.role.value}>"
