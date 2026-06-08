from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus, DocumentType
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    # ─── Lookups ──────────────────────────────────────────────────────────────

    def get_by_doc_number(self, org_id: uuid.UUID, doc_number: str) -> Document | None:
        stmt = select(Document).where(
            Document.org_id == org_id,
            Document.doc_number == doc_number,
            Document.is_latest == True,  # noqa: E712
        )
        return self.db.scalar(stmt)

    def get_latest_versions(self, org_id: uuid.UUID) -> list[Document]:
        """Return only the latest version of each document."""
        stmt = (
            select(Document)
            .where(Document.org_id == org_id, Document.is_latest == True)  # noqa: E712
            .order_by(Document.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_status(
        self, org_id: uuid.UUID, status: DocumentStatus
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.org_id == org_id,
                Document.status == status,
                Document.is_latest == True,  # noqa: E712
            )
            .order_by(Document.expiry_date.asc().nulls_last())
        )
        return list(self.db.scalars(stmt).all())

    def get_expiring_within(self, org_id: uuid.UUID, days: int) -> list[Document]:
        """Documents expiring within the next N days (not yet expired)."""
        today = date.today()
        cutoff = today + __import__("datetime").timedelta(days=days)
        stmt = (
            select(Document)
            .where(
                Document.org_id == org_id,
                Document.is_latest == True,  # noqa: E712
                Document.expiry_date.isnot(None),
                Document.expiry_date >= today,
                Document.expiry_date <= cutoff,
                Document.status != DocumentStatus.ARCHIVED,
            )
            .order_by(Document.expiry_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_overdue(self, org_id: uuid.UUID) -> list[Document]:
        today = date.today()
        stmt = (
            select(Document)
            .where(
                Document.org_id == org_id,
                Document.is_latest == True,  # noqa: E712
                Document.expiry_date.isnot(None),
                Document.expiry_date < today,
                Document.status != DocumentStatus.ARCHIVED,
            )
            .order_by(Document.expiry_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_department(
        self, org_id: uuid.UUID, department: str
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(
                Document.org_id == org_id,
                Document.department == department,
                Document.is_latest == True,  # noqa: E712
            )
            .order_by(Document.title)
        )
        return list(self.db.scalars(stmt).all())

    # ─── Search ───────────────────────────────────────────────────────────────

    def search(
        self,
        org_id: uuid.UUID,
        query: str,
        doc_type: DocumentType | None = None,
        department: str | None = None,
        status: DocumentStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Document], int]:
        conditions = [
            Document.org_id == org_id,
            Document.is_latest == True,  # noqa: E712
        ]
        if query:
            q = f"%{query.lower()}%"
            conditions.append(
                or_(
                    Document.title.ilike(q),
                    Document.doc_number.ilike(q),
                    Document.description.ilike(q),
                )
            )
        if doc_type:
            conditions.append(Document.doc_type == doc_type)
        if department:
            conditions.append(Document.department == department)
        if status:
            conditions.append(Document.status == status)

        return self.paginate(
            org_id,
            page=page,
            page_size=page_size,
            filters=conditions[1:],  # base already adds org_id in paginate
            order_by=Document.updated_at.desc(),
        )

    # ─── Stats ────────────────────────────────────────────────────────────────

    def count_by_status(self, org_id: uuid.UUID) -> dict[str, int]:
        results: dict[str, int] = {}
        for status in DocumentStatus:
            results[status.value] = self.count(
                org_id,
                filters=[
                    Document.status == status,
                    Document.is_latest == True,  # noqa: E712
                ],
            )
        return results

    def count_active(self, org_id: uuid.UUID) -> int:
        return self.count(
            org_id,
            filters=[
                Document.status.in_([DocumentStatus.ACTIVE, DocumentStatus.EXPIRING_SOON]),
                Document.is_latest == True,  # noqa: E712
            ],
        )

    def count_total_latest(self, org_id: uuid.UUID) -> int:
        return self.count(org_id, filters=[Document.is_latest == True])  # noqa: E712

    # ─── Versioning ───────────────────────────────────────────────────────────

    def retire_previous_versions(
        self, org_id: uuid.UUID, doc_number: str, new_doc_id: uuid.UUID
    ) -> None:
        """Mark all other versions of doc_number as not latest."""
        stmt = (
            select(Document)
            .where(
                Document.org_id == org_id,
                Document.doc_number == doc_number,
                Document.id != new_doc_id,
            )
        )
        for doc in self.db.scalars(stmt).all():
            doc.is_latest = False
            doc.status = DocumentStatus.SUPERSEDED
        self.db.flush()

    def get_version_history(
        self, org_id: uuid.UUID, doc_number: str
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.org_id == org_id, Document.doc_number == doc_number)
            .order_by(Document.version.desc())
        )
        return list(self.db.scalars(stmt).all())
