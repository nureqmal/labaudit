import uuid
from datetime import datetime, date, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, Date, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class DocumentType(str, PyEnum):
    SOP               = "sop"
    CALIBRATION_CERT  = "calibration_cert"
    TRAINING_RECORD   = "training_record"
    CAPA_RECORD       = "capa_record"
    POLICY            = "policy"
    WORK_INSTRUCTION  = "work_instruction"
    FORM_TEMPLATE     = "form_template"
    AUDIT_REPORT      = "audit_report"
    OTHER             = "other"


class DocumentStatus(str, PyEnum):
    DRAFT          = "draft"
    ACTIVE         = "active"
    EXPIRING_SOON  = "expiring_soon"   # within 30 days
    EXPIRED        = "expired"
    SUPERSEDED     = "superseded"      # replaced by newer version
    ARCHIVED       = "archived"


class ComplianceCategory(str, PyEnum):
    ISO_17025   = "iso_17025"
    ISO_9001    = "iso_9001"
    GMP         = "gmp"
    GLP         = "glp"
    HACCP       = "haccp"
    ISO_14001   = "iso_14001"
    OSHA        = "osha"
    INTERNAL    = "internal"
    OTHER       = "other"


class Document(Base):
    __tablename__ = "documents"

    # ─── Primary Key ──────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ─── Foreign Keys ─────────────────────────────────────
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    # self-referential: points to previous version
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Core Fields ──────────────────────────────────────
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    doc_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ─── Classification ───────────────────────────────────
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum"), nullable=False, index=True
    )
    compliance_category: Mapped[ComplianceCategory] = mapped_column(
        Enum(ComplianceCategory, name="compliance_category_enum"),
        default=ComplianceCategory.INTERNAL, nullable=False,
    )
    department: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)

    # ─── File ─────────────────────────────────────────────
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(10), nullable=True)   # pdf/docx/xlsx
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ─── Versioning ───────────────────────────────────────
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Dates & Status ───────────────────────────────────
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status_enum"),
        default=DocumentStatus.DRAFT, nullable=False, index=True,
    )

    # ─── Timestamps ───────────────────────────────────────
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
        "Organization", back_populates="documents"
    )
    owner: Mapped["User"] = relationship(                 # noqa: F821
        "User", back_populates="owned_documents", foreign_keys=[owner_id]
    )
    previous_version: Mapped["Document | None"] = relationship(
        "Document", remote_side="Document.id", foreign_keys=[previous_version_id]
    )

    # ─── Computed helpers ─────────────────────────────────
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
        return f"<Document {self.doc_number!r} v{self.version} status={self.status.value}>"
