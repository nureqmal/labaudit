"""
Audit Score Service — the core value proposition of LabAudit.

Calculates a weighted 0–100 readiness score from four compliance pillars:
  1. Documents    (35%)
  2. Calibrations (30%)
  3. Training     (20%)
  4. CAPA         (15%)

Score interpretation:
  90–100  ✅ Audit ready
  70–89   🟡 Minor gaps — attention needed
  50–69   🟠 Moderate risk — action required
  0–49    🔴 Critical risk — not audit ready
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.repositories.calibration_repository import CalibrationRepository
from app.repositories.training_repository import TrainingRepository
from app.repositories.capa_repository import CapaRepository
from app.models.document import DocumentStatus
from app.models.calibration import CalibrationStatus
from app.models.training import TrainingStatus
from app.models.capa import CapaStatus, CapaPriority

logger = logging.getLogger(__name__)

import uuid


@dataclass
class PillarScore:
    name: str
    score: float          # 0.0 – 100.0
    weight: float         # 0.0 – 1.0 (should sum to 1.0 across pillars)
    total: int
    compliant: int
    issues: list[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    @property
    def status_label(self) -> str:
        if self.score >= 90:
            return "green"
        if self.score >= 70:
            return "yellow"
        return "red"


@dataclass
class AuditReadinessReport:
    org_id: uuid.UUID
    overall_score: float
    pillars: list[PillarScore]
    generated_at: date

    # ─── Quick-access counts for dashboard ────────────────────────────────────
    total_documents: int = 0
    overdue_documents: int = 0
    expiring_soon_documents: int = 0   # within 30 days
    expiring_7d_documents: int = 0
    expiring_14d_documents: int = 0
    expiring_30d_documents: int = 0

    total_calibrations: int = 0
    overdue_calibrations: int = 0
    due_soon_calibrations: int = 0

    total_training: int = 0
    overdue_training: int = 0
    due_soon_training: int = 0

    open_capas: int = 0
    overdue_capas: int = 0
    critical_capas: int = 0

    @property
    def status_label(self) -> str:
        if self.overall_score >= 90:
            return "Audit Ready"
        if self.overall_score >= 70:
            return "Minor Gaps"
        if self.overall_score >= 50:
            return "Moderate Risk"
        return "Critical Risk"

    @property
    def status_colour(self) -> str:
        if self.overall_score >= 90:
            return "green"
        if self.overall_score >= 70:
            return "yellow"
        return "red"

    def get_pillar(self, name: str) -> PillarScore | None:
        return next((p for p in self.pillars if p.name == name), None)


class AuditScoreService:
    # Pillar weights — must sum to 1.0
    W_DOCUMENTS    = 0.35
    W_CALIBRATIONS = 0.30
    W_TRAINING     = 0.20
    W_CAPA         = 0.15

    def __init__(self, db: Session) -> None:
        self.db = db
        self.doc_repo   = DocumentRepository(db)
        self.cal_repo   = CalibrationRepository(db)
        self.trn_repo   = TrainingRepository(db)
        self.capa_repo  = CapaRepository(db)

    def calculate(self, org_id: uuid.UUID) -> AuditReadinessReport:
        """
        Main entry point — calculate full audit readiness report for an org.
        Sync statuses first so the score reflects reality.
        """
        self._sync_all_statuses(org_id)

        doc_pillar = self._score_documents(org_id)
        cal_pillar = self._score_calibrations(org_id)
        trn_pillar = self._score_training(org_id)
        cap_pillar = self._score_capa(org_id)

        pillars = [doc_pillar, cal_pillar, trn_pillar, cap_pillar]
        overall = sum(p.weighted_score for p in pillars)

        report = AuditReadinessReport(
            org_id=org_id,
            overall_score=round(overall, 1),
            pillars=pillars,
            generated_at=date.today(),
        )

        # Populate dashboard counts
        self._populate_counts(org_id, report)

        logger.info(
            "Audit score for org %s: %.1f%% (%s)",
            org_id, overall, report.status_label,
        )
        return report

    # ─── Pillar scorers ───────────────────────────────────────────────────────

    def _score_documents(self, org_id: uuid.UUID) -> PillarScore:
        total = self.doc_repo.count_total_latest(org_id)
        issues: list[str] = []

        if total == 0:
            return PillarScore(
                name="Documents", score=0.0, weight=self.W_DOCUMENTS,
                total=0, compliant=0, issues=["No documents found."],
            )

        expired   = self.doc_repo.count(org_id, filters=[
            __import__("app.models.document", fromlist=["Document"]).Document.status
            == DocumentStatus.EXPIRED,
            __import__("app.models.document", fromlist=["Document"]).Document.is_latest == True,  # noqa: E712
        ])
        expiring  = len(self.doc_repo.get_expiring_within(org_id, 30))
        drafts    = self.doc_repo.count(org_id, filters=[
            __import__("app.models.document", fromlist=["Document"]).Document.status
            == DocumentStatus.DRAFT,
            __import__("app.models.document", fromlist=["Document"]).Document.is_latest == True,  # noqa: E712
        ])

        # Scoring: expired docs are full deductions; expiring = half; drafts = 0
        compliant = total - expired
        base_score = (compliant / total) * 100

        # Apply penalty for expiring-soon (encourage proactive renewal)
        expiry_penalty = min(10.0, (expiring / total) * 20)
        score = max(0.0, base_score - expiry_penalty)

        if expired > 0:
            issues.append(f"{expired} expired document(s) require immediate renewal.")
        if expiring > 0:
            issues.append(f"{expiring} document(s) expiring within 30 days.")
        if drafts > 0:
            issues.append(f"{drafts} document(s) still in draft — not yet effective.")

        return PillarScore(
            name="Documents",
            score=round(score, 1),
            weight=self.W_DOCUMENTS,
            total=total,
            compliant=compliant - drafts,
            issues=issues,
        )

    def _score_calibrations(self, org_id: uuid.UUID) -> PillarScore:
        from app.models.calibration import CalibrationRecord

        total = self.cal_repo.count(org_id, filters=[
            CalibrationRecord.status != CalibrationStatus.OUT_OF_SERVICE
        ])
        issues: list[str] = []

        if total == 0:
            return PillarScore(
                name="Calibrations", score=100.0, weight=self.W_CALIBRATIONS,
                total=0, compliant=0, issues=[],
            )

        overdue  = len(self.cal_repo.get_overdue(org_id))
        due_soon = len(self.cal_repo.get_due_within(org_id, 30))

        compliant = total - overdue
        base_score = (compliant / total) * 100
        expiry_penalty = min(10.0, (due_soon / total) * 20)
        score = max(0.0, base_score - expiry_penalty)

        if overdue > 0:
            issues.append(f"{overdue} equipment calibration(s) overdue.")
        if due_soon > 0:
            issues.append(f"{due_soon} calibration(s) due within 30 days.")

        return PillarScore(
            name="Calibrations",
            score=round(score, 1),
            weight=self.W_CALIBRATIONS,
            total=total,
            compliant=compliant,
            issues=issues,
        )

    def _score_training(self, org_id: uuid.UUID) -> PillarScore:
        from app.models.training import TrainingRecord

        total = self.trn_repo.count(org_id, filters=[
            TrainingRecord.expiry_date.isnot(None)
        ])
        issues: list[str] = []

        if total == 0:
            return PillarScore(
                name="Training", score=100.0, weight=self.W_TRAINING,
                total=0, compliant=0, issues=[],
            )

        overdue  = len(self.trn_repo.get_overdue(org_id))
        due_soon = len(self.trn_repo.get_due_within(org_id, 30))

        compliant = total - overdue
        base_score = (compliant / total) * 100
        expiry_penalty = min(10.0, (due_soon / total) * 20)
        score = max(0.0, base_score - expiry_penalty)

        if overdue > 0:
            issues.append(f"{overdue} training record(s) overdue for renewal.")
        if due_soon > 0:
            issues.append(f"{due_soon} training record(s) expiring within 30 days.")

        return PillarScore(
            name="Training",
            score=round(score, 1),
            weight=self.W_TRAINING,
            total=total,
            compliant=compliant,
            issues=issues,
        )

    def _score_capa(self, org_id: uuid.UUID) -> PillarScore:
        from app.models.capa import CapaItem

        total_open    = len(self.capa_repo.get_open(org_id))
        total_ever    = self.capa_repo.count(org_id)
        overdue       = len(self.capa_repo.get_overdue(org_id))
        critical_open = len(self.capa_repo.get_by_priority(org_id, CapaPriority.CRITICAL))
        issues: list[str] = []

        if total_ever == 0:
            return PillarScore(
                name="CAPA", score=100.0, weight=self.W_CAPA,
                total=0, compliant=0, issues=[],
            )

        # Score based on closed ratio with heavy penalty for overdue/critical
        closed = total_ever - total_open
        base_score = (closed / total_ever) * 100 if total_ever > 0 else 100.0

        # Overdue CAPAs = -5 per item (capped at -25)
        overdue_penalty = min(25.0, overdue * 5.0)
        # Critical open = -8 per item (capped at -24)
        critical_penalty = min(24.0, critical_open * 8.0)

        score = max(0.0, base_score - overdue_penalty - critical_penalty)

        if overdue > 0:
            issues.append(f"{overdue} CAPA item(s) past their due date.")
        if critical_open > 0:
            issues.append(f"{critical_open} critical CAPA(s) still open.")
        if total_open > 0:
            issues.append(f"{total_open} CAPA item(s) open / in progress.")

        return PillarScore(
            name="CAPA",
            score=round(score, 1),
            weight=self.W_CAPA,
            total=total_ever,
            compliant=closed,
            issues=issues,
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _sync_all_statuses(self, org_id: uuid.UUID) -> None:
        """Keep status fields in DB consistent with today's date."""
        self.cal_repo.sync_statuses(org_id)
        self.trn_repo.sync_statuses(org_id)
        self.capa_repo.sync_overdue_statuses(org_id)
        self._sync_document_statuses(org_id)
        self.db.flush()

    def _sync_document_statuses(self, org_id: uuid.UUID) -> None:
        from app.models.document import Document
        from sqlalchemy import select

        today = date.today()
        warn_cutoff = today + timedelta(days=30)

        stmt = (
            __import__("sqlalchemy", fromlist=["select"]).select(Document)
            .where(
                Document.org_id == org_id,
                Document.is_latest == True,  # noqa: E712
                Document.status.notin_([DocumentStatus.ARCHIVED, DocumentStatus.SUPERSEDED, DocumentStatus.DRAFT]),
            )
        )
        docs = list(self.db.scalars(stmt).all())
        for doc in docs:
            if not doc.expiry_date:
                continue
            if doc.expiry_date < today:
                doc.status = DocumentStatus.EXPIRED
            elif doc.expiry_date <= warn_cutoff:
                doc.status = DocumentStatus.EXPIRING_SOON
            else:
                doc.status = DocumentStatus.ACTIVE

    def _populate_counts(self, org_id: uuid.UUID, report: AuditReadinessReport) -> None:
        report.total_documents         = self.doc_repo.count_total_latest(org_id)
        report.overdue_documents       = len(self.doc_repo.get_overdue(org_id))
        report.expiring_30d_documents  = len(self.doc_repo.get_expiring_within(org_id, 30))
        report.expiring_14d_documents  = len(self.doc_repo.get_expiring_within(org_id, 14))
        report.expiring_7d_documents   = len(self.doc_repo.get_expiring_within(org_id, 7))

        report.total_calibrations      = self.cal_repo.count(org_id)
        report.overdue_calibrations    = len(self.cal_repo.get_overdue(org_id))
        report.due_soon_calibrations   = len(self.cal_repo.get_due_within(org_id, 30))

        report.total_training          = self.trn_repo.count(org_id)
        report.overdue_training        = len(self.trn_repo.get_overdue(org_id))
        report.due_soon_training       = len(self.trn_repo.get_due_within(org_id, 30))

        report.open_capas              = len(self.capa_repo.get_open(org_id))
        report.overdue_capas           = len(self.capa_repo.get_overdue(org_id))
        report.critical_capas          = len(self.capa_repo.get_by_priority(org_id, CapaPriority.CRITICAL))
