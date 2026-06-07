from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.calibration import CalibrationRecord, CalibrationStatus
from app.models.user import User, UserRole
from app.repositories.calibration_repository import CalibrationRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class CalibrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CalibrationRepository(db)
        self.log_repo = AuditLogRepository(db)

    def create(
        self,
        *,
        org_id: uuid.UUID,
        equipment_name: str,
        equipment_id: str,
        department: str | None,
        last_calibrated: date | None,
        next_due: date | None,
        interval_days: int = 365,
        calibrated_by: str | None = None,
        certificate_number: str | None = None,
        assigned_to: uuid.UUID | None = None,
        acting_user: User,
    ) -> CalibrationRecord:
        AuthService.require_role(acting_user, UserRole.MANAGER)

        status = self._compute_status(next_due)
        rec = CalibrationRecord(
            id=uuid.uuid4(),
            org_id=org_id,
            equipment_name=equipment_name,
            equipment_id=equipment_id,
            department=department,
            last_calibrated=last_calibrated,
            next_due=next_due,
            calibration_interval_days=interval_days,
            calibrated_by=calibrated_by,
            certificate_number=certificate_number,
            assigned_to=assigned_to,
            status=status,
        )
        self.repo.create(rec)
        self.log_repo.log(
            action="calibration.create",
            org_id=org_id,
            user_id=acting_user.id,
            entity_type="calibration_record",
            entity_id=str(rec.id),
            summary=f"Added calibration record for {equipment_name} ({equipment_id})",
        )
        return rec

    def record_calibration(
        self,
        rec: CalibrationRecord,
        calibrated_on: date,
        next_due: date,
        acting_user: User,
        calibrated_by: str | None = None,
        certificate_number: str | None = None,
        notes: str | None = None,
    ) -> CalibrationRecord:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        rec.last_calibrated = calibrated_on
        rec.next_due = next_due
        rec.status = self._compute_status(next_due)
        if calibrated_by:
            rec.calibrated_by = calibrated_by
        if certificate_number:
            rec.certificate_number = certificate_number
        if notes:
            rec.notes = notes
        self.db.flush()
        self.log_repo.log(
            action="calibration.update",
            org_id=rec.org_id,
            user_id=acting_user.id,
            entity_type="calibration_record",
            entity_id=str(rec.id),
            summary=f"Calibration recorded for {rec.equipment_name}, next due {next_due}",
        )
        return rec

    @staticmethod
    def _compute_status(next_due: date | None) -> CalibrationStatus:
        if not next_due:
            return CalibrationStatus.CURRENT
        today = date.today()
        from datetime import timedelta
        if next_due < today:
            return CalibrationStatus.OVERDUE
        if next_due <= today + timedelta(days=30):
            return CalibrationStatus.DUE_SOON
        return CalibrationStatus.CURRENT
