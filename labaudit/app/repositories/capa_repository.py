from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.capa import CapaItem, CapaStatus, CapaPriority
from app.repositories.base import BaseRepository


class CapaRepository(BaseRepository[CapaItem]):
    model = CapaItem

    def get_by_reference(
        self, org_id: uuid.UUID, reference_no: str
    ) -> CapaItem | None:
        stmt = select(CapaItem).where(
            CapaItem.org_id == org_id,
            CapaItem.reference_no == reference_no,
        )
        return self.db.scalar(stmt)

    def get_open(self, org_id: uuid.UUID) -> list[CapaItem]:
        stmt = (
            select(CapaItem)
            .where(
                CapaItem.org_id == org_id,
                CapaItem.status != CapaStatus.CLOSED,
            )
            .order_by(CapaItem.due_date.asc().nulls_last())
        )
        return list(self.db.scalars(stmt).all())

    def get_overdue(self, org_id: uuid.UUID) -> list[CapaItem]:
        today = date.today()
        stmt = (
            select(CapaItem)
            .where(
                CapaItem.org_id == org_id,
                CapaItem.due_date.isnot(None),
                CapaItem.due_date < today,
                CapaItem.status != CapaStatus.CLOSED,
            )
            .order_by(CapaItem.due_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_priority(
        self, org_id: uuid.UUID, priority: CapaPriority
    ) -> list[CapaItem]:
        stmt = (
            select(CapaItem)
            .where(
                CapaItem.org_id == org_id,
                CapaItem.priority == priority,
                CapaItem.status != CapaStatus.CLOSED,
            )
            .order_by(CapaItem.due_date.asc().nulls_last())
        )
        return list(self.db.scalars(stmt).all())

    def next_reference_number(self, org_id: uuid.UUID) -> str:
        """Auto-generate next CAPA reference: CAPA-YYYY-NNN"""
        year = date.today().year
        stmt = (
            select(func.count())
            .select_from(CapaItem)
            .where(
                CapaItem.org_id == org_id,
                CapaItem.reference_no.like(f"CAPA-{year}-%"),
            )
        )
        count = self.db.scalar(stmt) or 0
        return f"CAPA-{year}-{count + 1:03d}"

    def count_by_status(self, org_id: uuid.UUID) -> dict[str, int]:
        return {
            status.value: self.count(
                org_id, filters=[CapaItem.status == status]
            )
            for status in CapaStatus
        }

    def sync_overdue_statuses(self, org_id: uuid.UUID) -> int:
        today = date.today()
        open_items = self.get_open(org_id)
        updated = 0
        for item in open_items:
            if item.due_date and item.due_date < today and item.status != CapaStatus.OVERDUE:
                item.status = CapaStatus.OVERDUE
                updated += 1
        self.db.flush()
        return updated
