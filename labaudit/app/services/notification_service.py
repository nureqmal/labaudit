"""
Notification service — generates in-app reminder lists (no email yet).
Called by the dashboard to surface actionable alerts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum

from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.repositories.calibration_repository import CalibrationRepository
from app.repositories.training_repository import TrainingRepository
from app.repositories.capa_repository import CapaRepository


class AlertLevel(str, Enum):
    RED    = "red"      # overdue / critical
    ORANGE = "orange"   # 7 days
    YELLOW = "yellow"   # 14 days
    BLUE   = "blue"     # 30 days / informational


@dataclass
class Alert:
    level: AlertLevel
    category: str      # Documents | Calibrations | Training | CAPA
    title: str
    detail: str
    days_remaining: int | None = None
    entity_id: str | None = None


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.doc_repo  = DocumentRepository(db)
        self.cal_repo  = CalibrationRepository(db)
        self.trn_repo  = TrainingRepository(db)
        self.capa_repo = CapaRepository(db)

    def get_alerts(self, org_id: uuid.UUID) -> list[Alert]:
        alerts: list[Alert] = []
        today = date.today()

        # ── Documents ─────────────────────────────────────
        for doc in self.doc_repo.get_overdue(org_id):
            days = (today - doc.expiry_date).days if doc.expiry_date else 0
            alerts.append(Alert(
                level=AlertLevel.RED,
                category="Documents",
                title=f"Expired: {doc.title}",
                detail=f"{doc.doc_number or ''} expired {days} day(s) ago.",
                days_remaining=-days,
                entity_id=str(doc.id),
            ))

        for doc in self.doc_repo.get_expiring_within(org_id, 7):
            days = doc.days_until_expiry or 0
            alerts.append(Alert(
                level=AlertLevel.ORANGE,
                category="Documents",
                title=f"Expiring in {days}d: {doc.title}",
                detail=f"{doc.doc_number or ''} expires on {doc.expiry_date}.",
                days_remaining=days,
                entity_id=str(doc.id),
            ))

        for doc in self.doc_repo.get_expiring_within(org_id, 14):
            days = doc.days_until_expiry or 0
            if days > 7:
                alerts.append(Alert(
                    level=AlertLevel.YELLOW,
                    category="Documents",
                    title=f"Expiring in {days}d: {doc.title}",
                    detail=f"{doc.doc_number or ''} expires on {doc.expiry_date}.",
                    days_remaining=days,
                    entity_id=str(doc.id),
                ))

        # ── Calibrations ──────────────────────────────────
        for rec in self.cal_repo.get_overdue(org_id):
            days = (today - rec.next_due).days if rec.next_due else 0
            alerts.append(Alert(
                level=AlertLevel.RED,
                category="Calibrations",
                title=f"Overdue: {rec.equipment_name}",
                detail=f"{rec.equipment_id} calibration overdue by {days} day(s).",
                days_remaining=-days,
                entity_id=str(rec.id),
            ))

        for rec in self.cal_repo.get_due_within(org_id, 14):
            days = rec.days_until_due or 0
            alerts.append(Alert(
                level=AlertLevel.YELLOW,
                category="Calibrations",
                title=f"Due in {days}d: {rec.equipment_name}",
                detail=f"{rec.equipment_id} calibration due {rec.next_due}.",
                days_remaining=days,
                entity_id=str(rec.id),
            ))

        # ── Training ──────────────────────────────────────
        for rec in self.trn_repo.get_overdue(org_id):
            days = (today - rec.expiry_date).days if rec.expiry_date else 0
            alerts.append(Alert(
                level=AlertLevel.RED,
                category="Training",
                title=f"Overdue: {rec.training_title}",
                detail=f"Training expired {days} day(s) ago.",
                days_remaining=-days,
                entity_id=str(rec.id),
            ))

        for rec in self.trn_repo.get_due_within(org_id, 14):
            days = rec.days_until_expiry or 0
            if days >= 0:
                alerts.append(Alert(
                    level=AlertLevel.YELLOW,
                    category="Training",
                    title=f"Renewal in {days}d: {rec.training_title}",
                    detail=f"Training expires {rec.expiry_date}.",
                    days_remaining=days,
                    entity_id=str(rec.id),
                ))

        # ── CAPA ──────────────────────────────────────────
        for item in self.capa_repo.get_overdue(org_id):
            days = (today - item.due_date).days if item.due_date else 0
            alerts.append(Alert(
                level=AlertLevel.RED,
                category="CAPA",
                title=f"Overdue: {item.reference_no}",
                detail=f"{item.title[:80]} — overdue by {days} day(s).",
                days_remaining=-days,
                entity_id=str(item.id),
            ))

        # Sort: RED first, then by urgency (most negative days_remaining first)
        level_order = {
            AlertLevel.RED: 0, AlertLevel.ORANGE: 1,
            AlertLevel.YELLOW: 2, AlertLevel.BLUE: 3,
        }
        alerts.sort(key=lambda a: (level_order[a.level], a.days_remaining or 0))
        return alerts
