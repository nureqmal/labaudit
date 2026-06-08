"""
Audit View — the compliance status map auditors actually look at.
Green / Yellow / Red indicators per category and department.
"""
import streamlit as st
import pandas as pd
from datetime import date

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.ui_helpers import inject_global_css, page_header, section_header, empty_state
from components.status_badge import (
    doc_status_badge, cal_status_badge, training_status_badge,
    capa_status_badge, capa_priority_badge, expiry_countdown,
)
from app.database import db_session
from app.services.audit_score_service import AuditScoreService
from app.repositories.document_repository import DocumentRepository
from app.repositories.calibration_repository import CalibrationRepository
from app.repositories.training_repository import TrainingRepository
from app.repositories.capa_repository import CapaRepository

st.set_page_config(page_title="Audit View — LabAudit", page_icon="✅", layout="wide")

user = require_auth()
inject_theme_css()
inject_global_css()
render_sidebar()
page_header("Audit View", "Full compliance status map — ready for auditor review", "✅")

org_id = st.session_state["org_id"]


@st.cache_data(ttl=120, show_spinner="Loading compliance data...")
def load_all(_org_id):
    with db_session() as db:
        score_svc = AuditScoreService(db)
        report    = score_svc.calculate(_org_id)

        doc_repo = DocumentRepository(db)
        cal_repo = CalibrationRepository(db)
        trn_repo = TrainingRepository(db)
        cap_repo = CapaRepository(db)

        docs   = doc_repo.get_latest_versions(_org_id)
        cals   = cal_repo.get_all(_org_id, limit=999)
        trns   = trn_repo.get_all(_org_id, limit=999)
        capas  = cap_repo.get_all(_org_id, limit=999)

        return report, docs, cals, trns, capas


report, docs, cals, trns, capas = load_all(org_id)


# ── Overall score banner ──────────────────────────────────────────────────────
score = report.overall_score
score_bg  = {"green": "#f0fdf4", "yellow": "#fefce8", "red": "#fef2f2"}[report.status_colour]
score_brd = {"green": "#bbf7d0", "yellow": "#fde68a", "red": "#fecaca"}[report.status_colour]
score_fg  = {"green": "#166534", "yellow": "#854d0e", "red": "#991b1b"}[report.status_colour]
score_ico = {"green": "✅", "yellow": "⚠️", "red": "🚨"}[report.status_colour]

st.markdown(
    f"""
    <div style="background:{score_bg};border:2px solid {score_brd};border-radius:16px;
                padding:1.5rem 2rem;margin-bottom:1.5rem;display:flex;
                justify-content:space-between;align-items:center;">
        <div>
            <div style="font-size:0.85rem;color:{score_fg};font-weight:600;
                        text-transform:uppercase;letter-spacing:0.06em;">
                Overall Audit Readiness
            </div>
            <div style="font-size:3rem;font-weight:800;color:{score_fg};line-height:1;">
                {score:.0f}%
            </div>
            <div style="font-size:1rem;color:{score_fg};font-weight:600;margin-top:4px;">
                {score_ico} {report.status_label}
            </div>
        </div>
        <div style="text-align:right;">
            {"".join(
                f"<div style='font-size:0.82rem;color:{score_fg};margin-bottom:4px;'>"
                f"{'✅' if p.score >= 90 else '⚠️' if p.score >= 70 else '❌'} "
                f"{p.name}: <b>{p.score:.0f}%</b></div>"
                for p in report.pillars
            )}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Tab per compliance area ───────────────────────────────────────────────────
tab_docs, tab_cal, tab_trn, tab_capa = st.tabs([
    f"📁 Documents ({len(docs)})",
    f"⚙️ Calibrations ({len(cals)})",
    f"🎓 Training ({len(trns)})",
    f"🔧 CAPA ({len(capas)})",
])


# ──────────────────────────────────────────────────────────────────────────────
# Documents tab
# ──────────────────────────────────────────────────────────────────────────────
with tab_docs:
    if not docs:
        empty_state("No documents found.", "📁")
    else:
        # Group by department
        depts: dict[str, list] = {}
        for d in docs:
            dept = d.department or "General"
            depts.setdefault(dept, []).append(d)

        for dept, dept_docs in sorted(depts.items()):
            n_red    = sum(1 for d in dept_docs if d.status.value in ("expired",))
            n_yellow = sum(1 for d in dept_docs if d.status.value == "expiring_soon")
            n_green  = sum(1 for d in dept_docs if d.status.value == "active")
            dept_colour = "🔴" if n_red > 0 else "🟡" if n_yellow > 0 else "🟢"

            with st.expander(
                f"{dept_colour}  {dept}  —  {n_green} active · {n_yellow} expiring · {n_red} expired",
                expanded=(n_red > 0 or n_yellow > 0),
            ):
                rows = []
                for d in sorted(dept_docs, key=lambda x: (x.status.value, x.title)):
                    rows.append({
                        "Status":      d.status,
                        "Ref":         d.doc_number or "—",
                        "Title":       d.title,
                        "Type":        d.doc_type.value.replace("_", " ").title(),
                        "Version":     f"v{d.version}",
                        "Expiry":      d.expiry_date,
                        "Owner":       "—",
                    })

                for row in rows:
                    cols = st.columns([0.6, 0.8, 3.5, 1.2, 0.5, 1.2])
                    with cols[0]:
                        st.markdown(doc_status_badge(row["Status"]), unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f"<span style='font-size:0.82rem;color:#64748b;'>{row['Ref']}</span>", unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{row['Title']}</span>", unsafe_allow_html=True)
                    with cols[3]:
                        st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{row['Type']}</span>", unsafe_allow_html=True)
                    with cols[4]:
                        st.markdown(f"<span style='font-size:0.8rem;color:#94a3b8;'>{row['Version']}</span>", unsafe_allow_html=True)
                    with cols[5]:
                        st.markdown(expiry_countdown(row["Expiry"]), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Calibrations tab
# ──────────────────────────────────────────────────────────────────────────────
with tab_cal:
    if not cals:
        empty_state("No calibration records found.", "⚙️")
    else:
        depts_cal: dict[str, list] = {}
        for c in cals:
            dept = c.department or "General"
            depts_cal.setdefault(dept, []).append(c)

        for dept, recs in sorted(depts_cal.items()):
            n_over  = sum(1 for r in recs if r.status.value == "overdue")
            n_soon  = sum(1 for r in recs if r.status.value == "due_soon")
            dept_colour = "🔴" if n_over > 0 else "🟡" if n_soon > 0 else "🟢"

            with st.expander(
                f"{dept_colour}  {dept}  —  {len(recs)-n_over-n_soon} current · {n_soon} due soon · {n_over} overdue",
                expanded=(n_over > 0),
            ):
                for rec in sorted(recs, key=lambda x: (x.status.value, x.equipment_name)):
                    cols = st.columns([0.7, 0.8, 3, 1.5, 1.5])
                    with cols[0]:
                        st.markdown(cal_status_badge(rec.status), unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{rec.equipment_id}</span>", unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{rec.equipment_name}</span>", unsafe_allow_html=True)
                    with cols[3]:
                        last = rec.last_calibrated.strftime("%d %b %Y") if rec.last_calibrated else "—"
                        st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>Last: {last}</span>", unsafe_allow_html=True)
                    with cols[4]:
                        st.markdown(expiry_countdown(rec.next_due), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Training tab
# ──────────────────────────────────────────────────────────────────────────────
with tab_trn:
    if not trns:
        empty_state("No training records found.", "🎓")
    else:
        # Group by status for quick overview
        overdue_trn = [t for t in trns if t.status.value == "overdue"]
        due_soon_trn = [t for t in trns if t.status.value == "due_soon"]
        current_trn  = [t for t in trns if t.status.value not in ("overdue", "due_soon")]

        if overdue_trn:
            st.markdown("#### 🔴 Overdue")
            for t in overdue_trn:
                cols = st.columns([0.7, 2.5, 1.5, 1.5, 1.3])
                with cols[0]:
                    st.markdown(training_status_badge(t.status), unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{t.training_title}</span>", unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{t.training_type.value.replace('_',' ').title()}</span>", unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(expiry_countdown(t.expiry_date), unsafe_allow_html=True)

        if due_soon_trn:
            st.markdown("#### 🟡 Due Soon")
            for t in due_soon_trn:
                cols = st.columns([0.7, 2.5, 1.5, 1.5])
                with cols[0]:
                    st.markdown(training_status_badge(t.status), unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"<span style='font-size:0.88rem;color:#1e293b;'>{t.training_title}</span>", unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{t.training_type.value.replace('_',' ').title()}</span>", unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(expiry_countdown(t.expiry_date), unsafe_allow_html=True)

        if current_trn:
            with st.expander(f"✅ Current / Completed ({len(current_trn)})", expanded=False):
                for t in current_trn:
                    cols = st.columns([0.7, 3, 1.5, 1.5])
                    with cols[0]:
                        st.markdown(training_status_badge(t.status), unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f"<span style='font-size:0.85rem;color:#1e293b;'>{t.training_title}</span>", unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{t.training_type.value.replace('_',' ').title()}</span>", unsafe_allow_html=True)
                    with cols[3]:
                        st.markdown(expiry_countdown(t.expiry_date), unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CAPA tab
# ──────────────────────────────────────────────────────────────────────────────
with tab_capa:
    if not capas:
        empty_state("No CAPA records found.", "🔧")
    else:
        open_capas   = [c for c in capas if c.status.value != "closed"]
        closed_capas = [c for c in capas if c.status.value == "closed"]

        if open_capas:
            st.markdown(f"#### Open / In Progress ({len(open_capas)})")
            for item in sorted(open_capas, key=lambda x: (x.status.value != "overdue", x.due_date or date.max)):
                cols = st.columns([0.7, 0.7, 3, 1, 1.3])
                with cols[0]:
                    st.markdown(capa_status_badge(item.status), unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(capa_priority_badge(item.priority), unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(
                        f"<span style='font-size:0.82rem;color:#94a3b8;'>{item.reference_no}</span> "
                        f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{item.title[:80]}</span>",
                        unsafe_allow_html=True,
                    )
                with cols[3]:
                    st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{item.department or '—'}</span>", unsafe_allow_html=True)
                with cols[4]:
                    st.markdown(expiry_countdown(item.due_date), unsafe_allow_html=True)

        if closed_capas:
            with st.expander(f"✅ Closed CAPAs ({len(closed_capas)})", expanded=False):
                for item in closed_capas:
                    cols = st.columns([0.7, 0.7, 3.5, 1.5])
                    with cols[0]:
                        st.markdown(capa_status_badge(item.status), unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(capa_priority_badge(item.priority), unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(
                            f"<span style='font-size:0.82rem;color:#94a3b8;'>{item.reference_no}</span> "
                            f"<span style='font-size:0.85rem;color:#1e293b;'>{item.title[:80]}</span>",
                            unsafe_allow_html=True,
                        )
                    with cols[3]:
                        closed = item.closed_date.strftime("%d %b %Y") if item.closed_date else "—"
                        st.markdown(f"<span style='font-size:0.8rem;color:#16a34a;'>Closed: {closed}</span>", unsafe_allow_html=True)

# ── Refresh ───────────────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Refresh View", key="audit_refresh"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Compliance data as of {date.today().strftime('%d %B %Y')}.")

# ── Export PDF ────────────────────────────────────────────────────────────────
st.divider()
st.markdown("#### 📄 Export Audit Report")
col_exp1, col_exp2 = st.columns([2, 3])
with col_exp1:
    if st.button("📥 Generate PDF Report", type="primary", key="gen_pdf"):
        with st.spinner("Generating PDF report..."):
            try:
                from components.auth_guard import current_user
                u = current_user()
                pdf_bytes = generate_audit_report(
                    report=report,
                    org_name="Nexus Food Analytics Sdn Bhd",
                    generated_by=u.full_name,
                )
                st.session_state["pdf_bytes"] = pdf_bytes
                st.success("✅ PDF ready! Click download below.")
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")

if "pdf_bytes" in st.session_state:
    with col_exp2:
        filename = f"LabAudit_Report_{date.today().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="⬇️ Download PDF Report",
            data=st.session_state["pdf_bytes"],
            file_name=filename,
            mime="application/pdf",
            key="download_pdf",
        )
        st.caption(f"Report generated for audit review — {date.today().strftime('%d %B %Y')}")
