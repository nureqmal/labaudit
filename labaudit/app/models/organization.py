import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    # ─── Primary Key ──────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ─── Fields ───────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    industry: Mapped[str] = mapped_column(
        String(100), nullable=False,
        # food_testing | environmental | pharmaceutical | industrial_rd | other
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Timestamps ───────────────────────────────────────
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
    users: Mapped[list["User"]] = relationship(         # noqa: F821
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship( # noqa: F821
        "Document", back_populates="organization", cascade="all, delete-orphan"
    )
    calibration_records: Mapped[list["CalibrationRecord"]] = relationship( # noqa: F821
        "CalibrationRecord", back_populates="organization", cascade="all, delete-orphan"
    )
    training_records: Mapped[list["TrainingRecord"]] = relationship( # noqa: F821
        "TrainingRecord", back_populates="organization", cascade="all, delete-orphan"
    )
    capa_items: Mapped[list["CapaItem"]] = relationship( # noqa: F821
        "CapaItem", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug!r}>"
