"""
Status badge helpers — consistent colour-coded labels used across all pages.
All functions return HTML strings for use with st.markdown(..., unsafe_allow_html=True).
"""
from __future__ import annotations

from datetime import date

from app.models.document import DocumentStatus
from app.models.calibration import CalibrationStatus
from app.models.training import TrainingStatus
from app.models.capa import CapaStatus, CapaPriority


# ─── Generic badge builder ────────────────────────────────────────────────────

def badge(text: str, bg: str, colour: str, border: str | None = None) -> str:
    brd = f"border:1px solid {border};" if border else ""
    return (
        f"<span style='background:{bg};color:{colour};{brd}"
        f"padding:2px 10px;border-radius:999px;font-size:0.75rem;"
        f"font-weight:600;white-space:nowrap;'>{text}</span>"
    )


# ─── Document status ──────────────────────────────────────────────────────────

_DOC_STATUS_MAP: dict[DocumentStatus, tuple[str, str, str, str]] = {
    DocumentStatus.ACTIVE:        ("Active",         "#dcfce7", "#166534", "#bbf7d0"),
    DocumentStatus.EXPIRING_SOON: ("Expiring Soon",  "#fef9c3", "#854d0e", "#fde68a"),
    DocumentStatus.EXPIRED:       ("Expired",        "#fee2e2", "#991b1b", "#fecaca"),
    DocumentStatus.DRAFT:         ("Draft",          "#f1f5f9", "#475569", "#e2e8f0"),
    DocumentStatus.SUPERSEDED:    ("Superseded",     "#f5f3ff", "#5b21b6", "#ddd6fe"),
    DocumentStatus.ARCHIVED:      ("Archived",       "#f1f5f9", "#94a3b8", "#e2e8f0"),
}

def doc_status_badge(status: DocumentStatus) -> str:
    label, bg, fg, brd = _DOC_STATUS_MAP.get(
        status, ("Unknown", "#f1f5f9", "#94a3b8", "#e2e8f0")
    )
    return badge(label, bg, fg, brd)


# ─── Calibration status ───────────────────────────────────────────────────────

_CAL_STATUS_MAP: dict[CalibrationStatus, tuple[str, str, str, str]] = {
    CalibrationStatus.CURRENT:        ("Current",         "#dcfce7", "#166534", "#bbf7d0"),
    CalibrationStatus.DUE_SOON:       ("Due Soon",        "#fef9c3", "#854d0e", "#fde68a"),
    CalibrationStatus.OVERDUE:        ("Overdue",         "#fee2e2", "#991b1b", "#fecaca"),
    CalibrationStatus.OUT_OF_SERVICE: ("Out of Service",  "#f1f5f9", "#94a3b8", "#e2e8f0"),
}

def cal_status_badge(status: CalibrationStatus) -> str:
    label, bg, fg, brd = _CAL_STATUS_MAP.get(
        status, ("Unknown", "#f1f5f9", "#94a3b8", "#e2e8f0")
    )
    return badge(label, bg, fg, brd)


# ─── Training status ──────────────────────────────────────────────────────────

_TRN_STATUS_MAP: dict[TrainingStatus, tuple[str, str, str, str]] = {
    TrainingStatus.CURRENT:   ("Current",   "#dcfce7", "#166534", "#bbf7d0"),
    TrainingStatus.DUE_SOON:  ("Due Soon",  "#fef9c3", "#854d0e", "#fde68a"),
    TrainingStatus.OVERDUE:   ("Overdue",   "#fee2e2", "#991b1b", "#fecaca"),
    TrainingStatus.COMPLETED: ("Completed", "#dbeafe", "#1e40af", "#bfdbfe"),
}

def training_status_badge(status: TrainingStatus) -> str:
    label, bg, fg, brd = _TRN_STATUS_MAP.get(
        status, ("Unknown", "#f1f5f9", "#94a3b8", "#e2e8f0")
    )
    return badge(label, bg, fg, brd)


# ─── CAPA status ──────────────────────────────────────────────────────────────

_CAPA_STATUS_MAP: dict[CapaStatus, tuple[str, str, str, str]] = {
    CapaStatus.OPEN:                  ("Open",                 "#dbeafe", "#1e40af", "#bfdbfe"),
    CapaStatus.IN_PROGRESS:           ("In Progress",          "#fef9c3", "#854d0e", "#fde68a"),
    CapaStatus.PENDING_VERIFICATION:  ("Pending Verification", "#f5f3ff", "#5b21b6", "#ddd6fe"),
    CapaStatus.CLOSED:                ("Closed",               "#dcfce7", "#166534", "#bbf7d0"),
    CapaStatus.OVERDUE:               ("Overdue",              "#fee2e2", "#991b1b", "#fecaca"),
}

def capa_status_badge(status: CapaStatus) -> str:
    label, bg, fg, brd = _CAPA_STATUS_MAP.get(
        status, ("Unknown", "#f1f5f9", "#94a3b8", "#e2e8f0")
    )
    return badge(label, bg, fg, brd)


_CAPA_PRIORITY_MAP: dict[CapaPriority, tuple[str, str, str, str]] = {
    CapaPriority.CRITICAL: ("Critical", "#fee2e2", "#991b1b", "#fecaca"),
    CapaPriority.HIGH:     ("High",     "#ffedd5", "#9a3412", "#fed7aa"),
    CapaPriority.MEDIUM:   ("Medium",   "#fef9c3", "#854d0e", "#fde68a"),
    CapaPriority.LOW:      ("Low",      "#f1f5f9", "#475569", "#e2e8f0"),
}

def capa_priority_badge(priority: CapaPriority) -> str:
    label, bg, fg, brd = _CAPA_PRIORITY_MAP.get(
        priority, ("Unknown", "#f1f5f9", "#94a3b8", "#e2e8f0")
    )
    return badge(label, bg, fg, brd)


# ─── Expiry countdown ─────────────────────────────────────────────────────────

def expiry_countdown(expiry_date: date | None) -> str:
    """Returns a coloured days-remaining string."""
    if not expiry_date:
        return "<span style='color:#94a3b8;font-size:0.82rem;'>No expiry</span>"
    today = date.today()
    delta = (expiry_date - today).days
    if delta < 0:
        return badge(f"{abs(delta)}d overdue", "#fee2e2", "#991b1b", "#fecaca")
    if delta <= 7:
        return badge(f"{delta}d left", "#fee2e2", "#991b1b", "#fecaca")
    if delta <= 14:
        return badge(f"{delta}d left", "#ffedd5", "#9a3412", "#fed7aa")
    if delta <= 30:
        return badge(f"{delta}d left", "#fef9c3", "#854d0e", "#fde68a")
    return f"<span style='color:#64748b;font-size:0.82rem;'>{expiry_date.strftime('%d %b %Y')}</span>"


# ─── Alert level dot ──────────────────────────────────────────────────────────

def alert_dot(level: str) -> str:
    colours = {"red": "#ef4444", "orange": "#f97316", "yellow": "#eab308", "blue": "#3b82f6"}
    c = colours.get(level, "#94a3b8")
    return f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin-right:6px;'></span>"
