from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.training import TrainingRecord, TrainingStatus
from app.repositories.base import BaseRepository


class TrainingRepository(BaseRepository[TrainingRecord]):
    model = TrainingRecord

    def get_by_user(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[TrainingRecord]:
        stmt = (
            select(TrainingRecord)
            .where(
                TrainingRecord.org_id == org_id,
                TrainingRecord.user_id == user_id,
            )
            .order_by(TrainingRecord.expiry_date.asc().nulls_last())
        )
        return list(self.db.scalars(stmt).all())

    def get_overdue(self, org_id: uuid.UUID) -> list[TrainingRecord]:
        today = date.today()
        stmt = (
            select(TrainingRecord)
            .where(
                TrainingRecord.org_id == org_id,
                TrainingRecord.expiry_date.isnot(None),
                TrainingRecord.expiry_date < today,
                TrainingRecord.status != TrainingStatus.COMPLETED,
            )
            .order_by(TrainingRecord.expiry_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_due_within(
        self, org_id: uuid.UUID, days: int
    ) -> list[TrainingRecord]:
        today = date.today()
        cutoff = today + timedelta(days=days)
        stmt = (
            select(TrainingRecord)
            .where(
                TrainingRecord.org_id == org_id,
                TrainingRecord.expiry_date.isnot(None),
                TrainingRecord.expiry_date >= today,
                TrainingRecord.expiry_date <= cutoff,
            )
            .order_by(TrainingRecord.expiry_date.asc())
        )
        return list(self.db.scalars(stmt).all())

    def count_by_status(self, org_id: uuid.UUID) -> dict[str, int]:
        return {
            status.value: self.count(
                org_id, filters=[TrainingRecord.status == status]
            )
            for status in TrainingStatus
        }

    def sync_statuses(self, org_id: uuid.UUID) -> int:
        today = date.today()
        warn_cutoff = today + timedelta(days=30)
        records = self.get_all(org_id, limit=9999)
        updated = 0
        for rec in records:
            if not rec.expiry_date:
                continue
            if rec.expiry_date < today:
                new_status = TrainingStatus.OVERDUE
            elif rec.expiry_date <= warn_cutoff:
                new_status = TrainingStatus.DUE_SOON
            else:
                new_status = TrainingStatus.CURRENT
            if rec.status != new_status:
                rec.status = new_status
                updated += 1
        self.db.flush()
        return updated
