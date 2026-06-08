from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.calibration import CalibrationRecord, CalibrationStatus
from app.repositories.base import BaseRepository


class CalibrationRepository(BaseRepository[CalibrationRecord]):
    model = CalibrationRecord

    def get_by_equipment_id(
        self, org_id: uuid.UUID, equipment_id: str
    ) -> CalibrationRecord | None:
        stmt = select(CalibrationRecord).where(
            CalibrationRecord.org_id == org_id,
            CalibrationRecord.equipment_id == equipment_id,
        )
        return self.db.scalar(stmt)

    def get_by_status(
        self, org_id: uuid.UUID, status: CalibrationStatus
    ) -> list[CalibrationRecord]:
        stmt = (
            select(CalibrationRecord)
            .where(
                CalibrationRecord.org_id == org_id,
                CalibrationRecord.status == status,
            )
            .order_by(CalibrationRecord.next_due.asc().nulls_last())
        )
        return list(self.db.scalars(stmt).all())

    def get_overdue(self, org_id: uuid.UUID) -> list[CalibrationRecord]:
        today = date.today()
        stmt = (
            select(CalibrationRecord)
            .where(
                CalibrationRecord.org_id == org_id,
                CalibrationRecord.next_due.isnot(None),
                CalibrationRecord.next_due < today,
                CalibrationRecord.status != CalibrationStatus.OUT_OF_SERVICE,
            )
            .order_by(CalibrationRecord.next_due.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_due_within(
        self, org_id: uuid.UUID, days: int
    ) -> list[CalibrationRecord]:
        today = date.today()
        cutoff = today + timedelta(days=days)
        stmt = (
            select(CalibrationRecord)
            .where(
                CalibrationRecord.org_id == org_id,
                CalibrationRecord.next_due.isnot(None),
                CalibrationRecord.next_due >= today,
                CalibrationRecord.next_due <= cutoff,
                CalibrationRecord.status != CalibrationStatus.OUT_OF_SERVICE,
            )
            .order_by(CalibrationRecord.next_due.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_department(
        self, org_id: uuid.UUID, department: str
    ) -> list[CalibrationRecord]:
        stmt = (
            select(CalibrationRecord)
            .where(
                CalibrationRecord.org_id == org_id,
                CalibrationRecord.department == department,
            )
            .order_by(CalibrationRecord.equipment_name)
        )
        return list(self.db.scalars(stmt).all())

    def count_by_status(self, org_id: uuid.UUID) -> dict[str, int]:
        return {
            status.value: self.count(
                org_id, filters=[CalibrationRecord.status == status]
            )
            for status in CalibrationStatus
        }

    def sync_statuses(self, org_id: uuid.UUID) -> int:
        """
        Recalculate and update status for all calibration records in the org.
        Returns the number of records updated.
        """
        today = date.today()
        warn_cutoff = today + timedelta(days=30)
        records = self.get_all(org_id, limit=9999)
        updated = 0
        for rec in records:
            if rec.status == CalibrationStatus.OUT_OF_SERVICE:
                continue
            if not rec.next_due:
                continue
            if rec.next_due < today:
                new_status = CalibrationStatus.OVERDUE
            elif rec.next_due <= warn_cutoff:
                new_status = CalibrationStatus.DUE_SOON
            else:
                new_status = CalibrationStatus.CURRENT
            if rec.status != new_status:
                rec.status = new_status
                updated += 1
        self.db.flush()
        return updated
