from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    """AuditLog is append-only — no update/delete, no BaseRepository inheritance."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        action: str,
        org_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        summary: str | None = None,
        changes: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            org_id=org_id,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            summary=summary,
            changes=changes,
            ip_address=ip_address,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_recent(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        entity_type: str | None = None,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        return list(self.db.scalars(stmt).all())

    def get_by_entity(
        self, entity_type: str, entity_id: str
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())
