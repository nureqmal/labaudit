from __future__ import annotations

import logging
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.capa import CapaItem, CapaType, CapaPriority, CapaStatus
from app.models.user import User, UserRole
from app.repositories.capa_repository import CapaRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class CapaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CapaRepository(db)
        self.log_repo = AuditLogRepository(db)

    def create(
        self,
        *,
        org_id: uuid.UUID,
        title: str,
        capa_type: CapaType,
        priority: CapaPriority,
        acting_user: User,
        department: str | None = None,
        description: str | None = None,
        source: str | None = None,
        due_date: date | None = None,
        assigned_to: uuid.UUID | None = None,
    ) -> CapaItem:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        ref = self.repo.next_reference_number(org_id)

        item = CapaItem(
            id=uuid.uuid4(),
            org_id=org_id,
            reference_no=ref,
            title=title,
            capa_type=capa_type,
            priority=priority,
            department=department,
            description=description,
            source=source,
            raised_date=date.today(),
            due_date=due_date,
            assigned_to=assigned_to,
            raised_by=acting_user.id,
            status=CapaStatus.OPEN,
        )
        self.repo.create(item)
        self.log_repo.log(
            action="capa.create",
            org_id=org_id,
            user_id=acting_user.id,
            entity_type="capa_item",
            entity_id=str(item.id),
            summary=f"Raised {ref}: {title}",
        )
        return item

    def transition_status(
        self,
        item: CapaItem,
        new_status: CapaStatus,
        acting_user: User,
        notes: str | None = None,
    ) -> CapaItem:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        old_status = item.status
        item.status = new_status
        if new_status == CapaStatus.CLOSED:
            item.closed_date = date.today()
        if notes:
            item.verification_notes = (item.verification_notes or "") + f"\n[{date.today()}] {notes}"
        self.db.flush()
        self.log_repo.log(
            action="capa.status_change",
            org_id=item.org_id,
            user_id=acting_user.id,
            entity_type="capa_item",
            entity_id=str(item.id),
            summary=f"{item.reference_no} status: {old_status.value} → {new_status.value}",
            changes={"status": {"before": old_status.value, "after": new_status.value}},
        )
        return item

    def update(self, item: CapaItem, acting_user: User, **kwargs) -> CapaItem:
        AuthService.require_role(acting_user, UserRole.MANAGER)
        for k, v in kwargs.items():
            if hasattr(item, k):
                setattr(item, k, v)
        self.db.flush()
        return item
