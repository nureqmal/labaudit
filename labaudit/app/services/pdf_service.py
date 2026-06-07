"""
PDF Report Service — generates a professional Audit Readiness Report
for laboratory auditors using ReportLab.

Output: multi-page PDF with:
  - Cover page (org name, score, date)
  - Executive summary (4 pillar scores)
  - Document compliance table
  - Calibration status table
  - Training records table
  - CAPA register table
  - Action items (overdue / expiring soon)
"""
from __future__ import annotations

import io
from datetime import date, datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from app.services.audit_score_service import AuditReadinessReport
from app.repositories.document_repository import DocumentRepository
from app.repositories.calibration_repository import CalibrationRepository
from app.repositories.training_repository import TrainingRepository
from app.repositories.capa_repository import CapaRepository
from app.database import db_session

# ─── Colour palette ───────────────────────────────────────────────────────────
NAVY        = colors.HexColor("#0a1628")
NAVY_LIGHT  = colors.HexColor("#162952")
TEAL        = colors.HexColor("#00c6a2")
TEAL_LIGHT  = colors.HexColor("#e6fdf7")
GOLD        = colors.HexColor("#e8b84b")
GOLD_LIGHT  = colors.HexColor("#fffbeb")
RED         = colors.HexColor("#dc2626")
RED_LIGHT   = colors.HexColor("#fee2e2")
YELLOW      = colors.HexColor("#ca8a04")
YELLOW_LIGHT= colors.HexColor("#fef9c3")
GREEN       = colors.HexColor("#16a34a")
GREEN_LIGHT = colors.HexColor("#dcfce7")
GRAY        = colors.HexColor("#64748b")
GRAY_LIGHT  = colors.HexColor("#f8fafc")
GRAY_BORDER = colors.HexColor("#e2e8f0")
WHITE       = colors.white
BLACK       = colors.HexColor("#1a2035")


def _status_colour(score: float) -> tuple:
    if score >= 90:
        return GREEN, GREEN_LIGHT
    if score >= 70:
        return YELLOW, YELLOW_LIGHT
    return RED, RED_LIGHT


def _doc_status_colour(status: str):
    m = {
        "active":        (GREEN,  GREEN_LIGHT),
        "expiring_soon": (YELLOW, YELLOW_LIGHT),
        "expired":       (RED,    RED_LIGHT),
        "draft":         (GRAY,   GRAY_LIGHT),
    }
    return m.get(status, (GRAY, GRAY_LIGHT))


def _cal_status_colour(status: str):
    m = {
        "current":  (GREEN,  GREEN_LIGHT),
        "due_soon": (YELLOW, YELLOW_LIGHT),
        "overdue":  (RED,    RED_LIGHT),
    }
    return m.get(status, (GRAY, GRAY_LIGHT))


# ─── Styles ───────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold",
            fontSize=28, textColor=WHITE, leading=34, alignment=TA_CENTER,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica",
            fontSize=13, textColor=colors.HexColor("#9aa3b8"),
            leading=18, alignment=TA_CENTER,
        ),
        "cover_score": ParagraphStyle(
            "cover_score", fontName="Helvetica-Bold",
            fontSize=64, textColor=TEAL, leading=72, alignment=TA_CENTER,
        ),
        "cover_label": ParagraphStyle(
            "cover_label", fontName="Helvetica",
            fontSize=11, textColor=colors.HexColor("#9aa3b8"),
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "section_title": ParagraphStyle(
            "section_title", fontName="Helvetica-Bold",
            fontSize=14, textColor=NAVY, leading=18, spaceBefore=16, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica",
            fontSize=9, textColor=BLACK, leading=14,
        ),
        "body_small": ParagraphStyle(
            "body_small", fontName="Helvetica",
            fontSize=8, textColor=GRAY, leading=12,
        ),
        "tag": ParagraphStyle(
            "tag", fontName="Helvetica",
            fontSize=8, textColor=GRAY, leading=10,
            spaceBefore=2,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica",
            fontSize=7, textColor=GRAY, alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "table_header", fontName="Helvetica-Bold",
            fontSize=8, textColor=WHITE, leading=10,
        ),
        "table_cell": ParagraphStyle(
            "table_cell", fontName="Helvetica",
            fontSize=8, textColor=BLACK, leading=11,
        ),
        "table_cell_small": ParagraphStyle(
            "table_cell_small", fontName="Helvetica",
            fontSize=7, textColor=GRAY, leading=10,
        ),
    }


# ─── Table helpers ────────────────────────────────────────────────────────────

def _base_table_style(header_bg=None) -> list:
    bg = header_bg or NAVY
    return [
        ("BACKGROUND",  (0, 0), (-1, 0),  bg),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_LIGHT]),
        ("GRID",        (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
    ]


def _status_badge_cell(text: str, fg, bg) -> Paragraph:
    style = ParagraphStyle(
        "badge", fontName="Helvetica-Bold", fontSize=7,
        textColor=fg, backColor=bg,
        borderPadding=(2, 4, 2, 4), leading=10,
    )
    return Paragraph(text, style)


# ─── Page template ────────────────────────────────────────────────────────────

def _on_page(canvas, doc, org_name: str, report_date: str):
    """Header and footer on every page except cover."""
    if doc.page == 1:
        return
    W, H = A4
    canvas.saveState()
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 22*mm, W, 22*mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(15*mm, H - 13*mm, "LabAudit")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#9aa3b8"))
    canvas.drawString(15*mm, H - 18*mm, f"Audit Readiness Report — {org_name}")
    canvas.setFillColor(colors.HexColor("#9aa3b8"))
    canvas.drawRightString(W - 15*mm, H - 15*mm, report_date)
    # Footer
    canvas.setFillColor(GRAY_BORDER)
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15*mm, 3.5*mm, "CONFIDENTIAL — For internal and audit use only")
    canvas.drawRightString(W - 15*mm, 3.5*mm, f"Page {doc.page}")
    canvas.restoreState()


# ─── Main generator ───────────────────────────────────────────────────────────

def generate_audit_report(
    report: AuditReadinessReport,
    org_name: str,
    generated_by: str = "LabAudit System",
) -> bytes:
    """
    Generate a full audit readiness PDF report.
    Returns raw PDF bytes for Streamlit download_button.
    """
    buf = io.BytesIO()
    W, H = A4
    report_date = date.today().strftime("%d %B %Y")
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=25*mm,
        bottomMargin=15*mm,
        title=f"Audit Readiness Report — {org_name}",
        author="LabAudit",
        subject="Laboratory Compliance Report",
    )

    def on_page(c, d):
        _on_page(c, d, org_name, report_date)

    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    # Navy background block (drawn via canvas — workaround: use a big coloured table)
    cover_bg_data = [[""]]
    cover_bg = Table(cover_bg_data, colWidths=[W - 30*mm], rowHeights=[60*mm])
    cover_bg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0,0), (-1, -1), 0),
    ]))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("🔬  LabAudit", ParagraphStyle(
        "logo", fontName="Helvetica-Bold", fontSize=16,
        textColor=TEAL, alignment=TA_CENTER, spaceAfter=4,
    )))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("AUDIT READINESS REPORT", ParagraphStyle(
        "report_type", fontName="Helvetica-Bold", fontSize=10,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=2,
        letterSpacing=2,
    )))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(org_name, ParagraphStyle(
        "org", fontName="Helvetica-Bold", fontSize=20,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=2,
    )))
    story.append(Paragraph(report_date, ParagraphStyle(
        "date", fontName="Helvetica", fontSize=10,
        textColor=GRAY, alignment=TA_CENTER,
    )))
    story.append(Spacer(1, 10*mm))

    # Score box
    fg, bg = _status_colour(report.overall_score)
    score_data = [[
        Paragraph(f"{report.overall_score:.0f}%", ParagraphStyle(
            "sc", fontName="Helvetica-Bold", fontSize=52,
            textColor=fg, alignment=TA_CENTER, leading=60,
        )),
    ], [
        Paragraph("Overall Audit Readiness Score", ParagraphStyle(
            "scl", fontName="Helvetica", fontSize=10,
            textColor=GRAY, alignment=TA_CENTER,
        )),
    ], [
        Paragraph(f"Status: {report.status_label}", ParagraphStyle(
            "scs", fontName="Helvetica-Bold", fontSize=11,
            textColor=fg, alignment=TA_CENTER,
        )),
    ]]
    score_table = Table(score_data, colWidths=[W - 30*mm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8*mm))

    # Pillar summary on cover
    pillar_header = [
        Paragraph(p.name, ParagraphStyle("ph", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, alignment=TA_CENTER))
        for p in report.pillars
    ]
    pfg_list = [_status_colour(p.score)[0] for p in report.pillars]
    pillar_scores = [
        Paragraph(f"{p.score:.0f}%", ParagraphStyle("ps", fontName="Helvetica-Bold", fontSize=18, textColor=pfg_list[i], alignment=TA_CENTER))
        for i, p in enumerate(report.pillars)
    ]
    pillar_weights = [
        Paragraph(f"Weight: {int(p.weight*100)}%", ParagraphStyle("pw", fontName="Helvetica", fontSize=7, textColor=GRAY, alignment=TA_CENTER))
        for p in report.pillars
    ]
    col_w = (W - 30*mm) / 4
    pillar_table = Table(
        [pillar_header, pillar_scores, pillar_weights],
        colWidths=[col_w] * 4,
    )
    pillar_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("BACKGROUND",    (0, 1), (-1, -1), GRAY_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(pillar_table)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph(
        f"Generated by: {generated_by}  |  Report Date: {report_date}  |  Confidential",
        styles["body_small"],
    ))
    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ───────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 4*mm))

    summary_rows = [
        ["Pillar", "Score", "Weight", "Compliant / Total", "Status", "Key Issues"],
    ]
    for p in report.pillars:
        fg2, _ = _status_colour(p.score)
        issues_text = "\n".join(f"• {i}" for i in p.issues[:3]) if p.issues else "No issues"
        summary_rows.append([
            Paragraph(p.name, styles["table_cell"]),
            Paragraph(f"{p.score:.0f}%", ParagraphStyle("sc2", fontName="Helvetica-Bold", fontSize=9, textColor=fg2)),
            Paragraph(f"{int(p.weight*100)}%", styles["table_cell"]),
            Paragraph(f"{p.compliant} / {p.total}", styles["table_cell"]),
            Paragraph(p.status_label.upper(), ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=7, textColor=fg2)),
            Paragraph(issues_text, styles["table_cell_small"]),
        ])

    summary_table = Table(
        summary_rows,
        colWidths=[28*mm, 16*mm, 14*mm, 28*mm, 18*mm, None],
    )
    ts = _base_table_style()
    summary_table.setStyle(TableStyle(ts))
    story.append(summary_table)
    story.append(Spacer(1, 4*mm))

    # Quick stats
    stats_data = [[
        Paragraph(f"Total Documents\n{report.total_documents}", ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, alignment=TA_CENTER, leading=14)),
        Paragraph(f"Overdue Docs\n{report.overdue_documents}", ParagraphStyle("st2", fontName="Helvetica-Bold", fontSize=10, textColor=RED if report.overdue_documents else GREEN, alignment=TA_CENTER, leading=14)),
        Paragraph(f"Expiring (30d)\n{report.expiring_30d_documents}", ParagraphStyle("st3", fontName="Helvetica-Bold", fontSize=10, textColor=YELLOW if report.expiring_30d_documents else GREEN, alignment=TA_CENTER, leading=14)),
        Paragraph(f"Overdue Cals\n{report.overdue_calibrations}", ParagraphStyle("st4", fontName="Helvetica-Bold", fontSize=10, textColor=RED if report.overdue_calibrations else GREEN, alignment=TA_CENTER, leading=14)),
        Paragraph(f"Overdue Training\n{report.overdue_training}", ParagraphStyle("st5", fontName="Helvetica-Bold", fontSize=10, textColor=RED if report.overdue_training else GREEN, alignment=TA_CENTER, leading=14)),
        Paragraph(f"Open CAPAs\n{report.open_capas}", ParagraphStyle("st6", fontName="Helvetica-Bold", fontSize=10, textColor=RED if report.open_capas > 2 else YELLOW if report.open_capas else GREEN, alignment=TA_CENTER, leading=14)),
    ]]
    col_w2 = (W - 30*mm) / 6
    stats_table = Table(stats_data, colWidths=[col_w2]*6, rowHeights=[18*mm])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GRAY_LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(stats_table)
    story.append(PageBreak())

    # ── FETCH DATA ───────────────────────────────────────────────────────────
    org_id = report.org_id
    with db_session() as db:
        docs  = DocumentRepository(db).get_latest_versions(org_id)
        cals  = CalibrationRepository(db).get_all(org_id, limit=999)
        trns  = TrainingRepository(db).get_all(org_id, limit=999)
        capas = CapaRepository(db).get_all(org_id, limit=999)

    # ── DOCUMENTS TABLE ──────────────────────────────────────────────────────
    story.append(Paragraph("Document Register", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 3*mm))

    doc_rows = [["Ref", "Title", "Type", "Department", "Version", "Expiry", "Status"]]
    for d in sorted(docs, key=lambda x: x.status.value):
        fg3, _ = _doc_status_colour(d.status.value)
        expiry_str = d.expiry_date.strftime("%d %b %Y") if d.expiry_date else "—"
        if d.expiry_date:
            days = (d.expiry_date - date.today()).days
            if days < 0:
                expiry_str += f" ({abs(days)}d ago)"
            elif days <= 30:
                expiry_str += f" ({days}d)"
        doc_rows.append([
            Paragraph(d.doc_number or "—", styles["table_cell"]),
            Paragraph(d.title[:55] + ("..." if len(d.title) > 55 else ""), styles["table_cell"]),
            Paragraph(d.doc_type.value.replace("_", " ").title(), styles["table_cell_small"]),
            Paragraph(d.department or "—", styles["table_cell_small"]),
            Paragraph(f"v{d.version}", styles["table_cell"]),
            Paragraph(expiry_str, ParagraphStyle("exp", fontName="Helvetica", fontSize=7, textColor=fg3)),
            Paragraph(d.status.value.replace("_", " ").upper(), ParagraphStyle("ds", fontName="Helvetica-Bold", fontSize=7, textColor=fg3)),
        ])

    doc_table = Table(doc_rows, colWidths=[18*mm, 55*mm, 22*mm, 24*mm, 12*mm, 24*mm, 22*mm])
    doc_table.setStyle(TableStyle(_base_table_style()))
    story.append(doc_table)
    story.append(PageBreak())

    # ── CALIBRATIONS TABLE ───────────────────────────────────────────────────
    story.append(Paragraph("Calibration Register", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 3*mm))

    cal_rows = [["Equipment ID", "Equipment Name", "Department", "Last Calibrated", "Next Due", "Status"]]
    for c in sorted(cals, key=lambda x: x.status.value):
        fg4, _ = _cal_status_colour(c.status.value)
        last_str = c.last_calibrated.strftime("%d %b %Y") if c.last_calibrated else "—"
        next_str = c.next_due.strftime("%d %b %Y") if c.next_due else "—"
        if c.next_due:
            days = (c.next_due - date.today()).days
            if days < 0:
                next_str += f" ({abs(days)}d overdue)"
            elif days <= 30:
                next_str += f" ({days}d)"
        cal_rows.append([
            Paragraph(c.equipment_id, styles["table_cell"]),
            Paragraph(c.equipment_name[:40] + ("..." if len(c.equipment_name) > 40 else ""), styles["table_cell"]),
            Paragraph(c.department or "—", styles["table_cell_small"]),
            Paragraph(last_str, styles["table_cell_small"]),
            Paragraph(next_str, ParagraphStyle("nd", fontName="Helvetica", fontSize=7, textColor=fg4)),
            Paragraph(c.status.value.replace("_", " ").upper(), ParagraphStyle("cs", fontName="Helvetica-Bold", fontSize=7, textColor=fg4)),
        ])

    cal_table = Table(cal_rows, colWidths=[22*mm, 50*mm, 25*mm, 25*mm, 30*mm, 25*mm])
    cal_table.setStyle(TableStyle(_base_table_style()))
    story.append(cal_table)
    story.append(PageBreak())

    # ── TRAINING TABLE ───────────────────────────────────────────────────────
    story.append(Paragraph("Training Records", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 3*mm))

    trn_rows = [["Training Title", "Type", "Completed", "Expiry", "Status"]]
    for t in sorted(trns, key=lambda x: x.status.value):
        from app.models.training import TrainingStatus
        fg5 = RED if t.status == TrainingStatus.OVERDUE else YELLOW if t.status == TrainingStatus.DUE_SOON else GREEN
        completed_str = t.completed_date.strftime("%d %b %Y") if t.completed_date else "—"
        expiry_str2 = t.expiry_date.strftime("%d %b %Y") if t.expiry_date else "No expiry"
        trn_rows.append([
            Paragraph(t.training_title[:55] + ("..." if len(t.training_title) > 55 else ""), styles["table_cell"]),
            Paragraph(t.training_type.value.replace("_", " ").title(), styles["table_cell_small"]),
            Paragraph(completed_str, styles["table_cell_small"]),
            Paragraph(expiry_str2, ParagraphStyle("te", fontName="Helvetica", fontSize=7, textColor=fg5)),
            Paragraph(t.status.value.replace("_", " ").upper(), ParagraphStyle("ts2", fontName="Helvetica-Bold", fontSize=7, textColor=fg5)),
        ])

    trn_table = Table(trn_rows, colWidths=[65*mm, 35*mm, 25*mm, 25*mm, 27*mm])
    trn_table.setStyle(TableStyle(_base_table_style()))
    story.append(trn_table)
    story.append(PageBreak())

    # ── CAPA TABLE ───────────────────────────────────────────────────────────
    story.append(Paragraph("CAPA Register", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 3*mm))

    capa_rows = [["Reference", "Title", "Type", "Priority", "Due Date", "Status"]]
    for item in sorted(capas, key=lambda x: (x.status.value != "overdue", x.priority.value)):
        from app.models.capa import CapaStatus, CapaPriority
        sfg = RED if item.status == CapaStatus.OVERDUE else GREEN if item.status == CapaStatus.CLOSED else YELLOW
        pfg = RED if item.priority == CapaPriority.CRITICAL else YELLOW if item.priority == CapaPriority.HIGH else GRAY
        due_str = item.due_date.strftime("%d %b %Y") if item.due_date else "—"
        if item.due_date and item.status != CapaStatus.CLOSED:
            days = (item.due_date - date.today()).days
            if days < 0:
                due_str += f" ({abs(days)}d ago)"
        capa_rows.append([
            Paragraph(item.reference_no, styles["table_cell"]),
            Paragraph(item.title[:50] + ("..." if len(item.title) > 50 else ""), styles["table_cell"]),
            Paragraph(item.capa_type.value.title(), styles["table_cell_small"]),
            Paragraph(item.priority.value.upper(), ParagraphStyle("pp", fontName="Helvetica-Bold", fontSize=7, textColor=pfg)),
            Paragraph(due_str, styles["table_cell_small"]),
            Paragraph(item.status.value.replace("_", " ").upper(), ParagraphStyle("ss", fontName="Helvetica-Bold", fontSize=7, textColor=sfg)),
        ])

    capa_table = Table(capa_rows, colWidths=[24*mm, 57*mm, 20*mm, 18*mm, 24*mm, 34*mm])
    capa_table.setStyle(TableStyle(_base_table_style()))
    story.append(capa_table)
    story.append(Spacer(1, 6*mm))

    # ── SIGN-OFF BOX ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_BORDER))
    story.append(Spacer(1, 4*mm))
    signoff_data = [
        ["Prepared by:", "", "Reviewed by:", "", "Date:"],
        ["", "", "", "", report_date],
        ["________________________", "", "________________________", "", "________________________"],
        ["Quality Manager", "", "Laboratory Director", "", ""],
    ]
    signoff_table = Table(signoff_data, colWidths=[40*mm, 10*mm, 40*mm, 10*mm, 40*mm])
    signoff_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",   (0, 0), (-1, -1), GRAY),
        ("TOPPADDING",  (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1),   3),
    ]))
    story.append(signoff_table)

    # Build
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
