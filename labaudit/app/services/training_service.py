from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.training import TrainingRecord, TrainingType, TrainingStatus
from app.models.user import User, UserRole
from app.repositories.training_repository import TrainingRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class TrainingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TrainingRepository(db)
        self.log_repo = AuditLogRepository(db)

    def create(
        self,
        *,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        training_title: str,
        training_type: TrainingType,
        acting_user: User,
        completed_date: date | None = None,
        expiry_date: date | None = None,
        trainer: str | None = None,
        training_provider: str | None = None,
        sop_reference: str | None = None,
        notes: str | None = None,
    ) -> TrainingRecord:
        AuthService.require_role(acting_user, UserRole.MANAGER)

        status = self._compute_status(expiry_date)
        rec = TrainingRecord(
            id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            training_title=training_title,
            training_type=training_type,
            completed_date=completed_date,
            expiry_date=expiry_date,
            trainer=trainer,
            training_provider=training_provider,
            sop_reference=sop_reference,
            notes=notes,
            status=status,
        )
        self.repo.create(rec)
        self.log_repo.log(
            action="training.create",
            org_id=org_id,
            user_id=acting_user.id,
            entity_type="training_record",
            entity_id=str(rec.id),
            summary=f"Training record created: '{training_title}'",
        )
        return rec

    def update(self, rec: TrainingRecord, acting_user: User, **kwargs) -> TrainingRecord:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        for k, v in kwargs.items():
            if hasattr(rec, k):
                setattr(rec, k, v)
        if "expiry_date" in kwargs:
            rec.status = self._compute_status(kwargs["expiry_date"])
        self.db.flush()
        return rec

    @staticmethod
    def _compute_status(expiry_date: date | None) -> TrainingStatus:
        if not expiry_date:
            return TrainingStatus.COMPLETED
        today = date.today()
        from datetime import timedelta
        if expiry_date < today:
            return TrainingStatus.OVERDUE
        if expiry_date <= today + timedelta(days=30):
            return TrainingStatus.DUE_SOON
        return TrainingStatus.CURRENT
