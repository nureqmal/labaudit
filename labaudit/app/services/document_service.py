"""
Document service — handles create, update, upload, versioning, and expiry logic.
"""
from __future__ import annotations

import logging
import os
import uuid
import shutil
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentType, DocumentStatus, ComplianceCategory
from app.models.user import User, UserRole
from app.repositories.document_repository import DocumentRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DocumentRepository(db)
        self.log_repo = AuditLogRepository(db)

    # ─── Create ───────────────────────────────────────────────────────────────

    def create_document(
        self,
        *,
        org_id: uuid.UUID,
        title: str,
        doc_type: DocumentType,
        acting_user: User,
        doc_number: str | None = None,
        description: str | None = None,
        compliance_category: ComplianceCategory = ComplianceCategory.INTERNAL,
        department: str | None = None,
        expiry_date: date | None = None,
        effective_date: date | None = None,
        review_date: date | None = None,
        file_bytes: bytes | None = None,
        file_name: str | None = None,
    ) -> Document:
        AuthService.require_role(acting_user, UserRole.MANAGER)

        # Determine initial status
        if expiry_date and expiry_date < date.today():
            status = DocumentStatus.EXPIRED
        elif expiry_date and expiry_date <= date.today() + timedelta(days=30):
            status = DocumentStatus.EXPIRING_SOON
        elif effective_date:
            status = DocumentStatus.ACTIVE
        else:
            status = DocumentStatus.DRAFT

        doc = Document(
            id=uuid.uuid4(),
            org_id=org_id,
            owner_id=acting_user.id,
            title=title,
            doc_number=doc_number,
            description=description,
            doc_type=doc_type,
            compliance_category=compliance_category,
            department=department,
            version=1,
            is_latest=True,
            status=status,
            expiry_date=expiry_date,
            effective_date=effective_date,
            review_date=review_date,
        )

        if file_bytes and file_name:
            doc.file_path, doc.file_name, doc.file_type, doc.file_size_bytes = (
                self._save_file(org_id, doc.id, file_bytes, file_name)
            )

        self.repo.create(doc)
        self.log_repo.log(
            action="document.create",
            org_id=org_id,
            user_id=acting_user.id,
            entity_type="document",
            entity_id=str(doc.id),
            summary=f"Created document '{title}' ({doc_number or 'no ref'})",
        )
        logger.info("Document created: %s by %s", doc.id, acting_user.email)
        return doc

    # ─── Update ───────────────────────────────────────────────────────────────

    def update_document(
        self,
        doc: Document,
        acting_user: User,
        **kwargs,
    ) -> Document:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        old_vals = {k: getattr(doc, k) for k in kwargs if hasattr(doc, k)}

        for key, val in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, val)

        # Re-evaluate status from expiry date if it changed
        if "expiry_date" in kwargs:
            doc.status = self._compute_status(doc.expiry_date, doc.effective_date)

        self.db.flush()
        self.log_repo.log(
            action="document.update",
            org_id=doc.org_id,
            user_id=acting_user.id,
            entity_type="document",
            entity_id=str(doc.id),
            summary=f"Updated document '{doc.title}'",
            changes={k: {"before": str(old_vals.get(k)), "after": str(v)} for k, v in kwargs.items()},
        )
        return doc

    # ─── New version ──────────────────────────────────────────────────────────

    def create_new_version(
        self,
        previous_doc: Document,
        acting_user: User,
        *,
        file_bytes: bytes | None = None,
        file_name: str | None = None,
        expiry_date: date | None = None,
        description: str | None = None,
    ) -> Document:
        AuthService.require_role(acting_user, UserRole.MANAGER)

        new_doc = Document(
            id=uuid.uuid4(),
            org_id=previous_doc.org_id,
            owner_id=acting_user.id,
            title=previous_doc.title,
            doc_number=previous_doc.doc_number,
            description=description or previous_doc.description,
            doc_type=previous_doc.doc_type,
            compliance_category=previous_doc.compliance_category,
            department=previous_doc.department,
            version=previous_doc.version + 1,
            is_latest=True,
            previous_version_id=previous_doc.id,
            effective_date=date.today(),
            expiry_date=expiry_date or previous_doc.expiry_date,
        )
        new_doc.status = self._compute_status(new_doc.expiry_date, new_doc.effective_date)

        if file_bytes and file_name:
            new_doc.file_path, new_doc.file_name, new_doc.file_type, new_doc.file_size_bytes = (
                self._save_file(new_doc.org_id, new_doc.id, file_bytes, file_name)
            )

        # Retire the previous version
        if previous_doc.doc_number:
            self.repo.retire_previous_versions(
                previous_doc.org_id, previous_doc.doc_number, new_doc.id
            )

        self.repo.create(new_doc)
        self.log_repo.log(
            action="document.new_version",
            org_id=new_doc.org_id,
            user_id=acting_user.id,
            entity_type="document",
            entity_id=str(new_doc.id),
            summary=f"New version v{new_doc.version} of '{new_doc.title}'",
        )
        return new_doc

    # ─── Delete (archive) ─────────────────────────────────────────────────────

    def archive_document(self, doc: Document, acting_user: User) -> Document:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        doc.status = DocumentStatus.ARCHIVED
        self.db.flush()
        self.log_repo.log(
            action="document.archive",
            org_id=doc.org_id,
            user_id=acting_user.id,
            entity_type="document",
            entity_id=str(doc.id),
            summary=f"Archived '{doc.title}'",
        )
        return doc

    # ─── File handling ────────────────────────────────────────────────────────

    def _save_file(
        self,
        org_id: uuid.UUID,
        doc_id: uuid.UUID,
        file_bytes: bytes,
        original_name: str,
    ) -> tuple[str, str, str, int]:
        """Save uploaded bytes to disk. Returns (file_path, file_name, file_type, size)."""
        ext = Path(original_name).suffix.lower().lstrip(".")
        if ext not in settings.allowed_extensions_list:
            raise ValueError(f"File type .{ext} is not allowed.")

        dest_dir = Path(settings.UPLOAD_DIR) / str(org_id) / "documents"
        dest_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{doc_id}.{ext}"
        dest_path = dest_dir / safe_name
        dest_path.write_bytes(file_bytes)

        return str(dest_path), original_name, ext, len(file_bytes)

    def get_file_bytes(self, doc: Document) -> bytes | None:
        if not doc.file_path or not os.path.exists(doc.file_path):
            return None
        return Path(doc.file_path).read_bytes()

    # ─── Expiry reminder buckets ──────────────────────────────────────────────

    def get_expiry_buckets(self, org_id: uuid.UUID) -> dict[str, list[Document]]:
        """Returns documents grouped by expiry urgency for reminder display."""
        return {
            "7_days":  self.repo.get_expiring_within(org_id, 7),
            "14_days": [
                d for d in self.repo.get_expiring_within(org_id, 14)
                if (d.days_until_expiry or 999) > 7
            ],
            "30_days": [
                d for d in self.repo.get_expiring_within(org_id, 30)
                if (d.days_until_expiry or 999) > 14
            ],
            "overdue": self.repo.get_overdue(org_id),
        }

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_status(
        expiry_date: date | None, effective_date: date | None
    ) -> DocumentStatus:
        today = date.today()
        if not effective_date:
            return DocumentStatus.DRAFT
        if expiry_date:
            if expiry_date < today:
                return DocumentStatus.EXPIRED
            if expiry_date <= today + timedelta(days=30):
                return DocumentStatus.EXPIRING_SOON
        return DocumentStatus.ACTIVE
