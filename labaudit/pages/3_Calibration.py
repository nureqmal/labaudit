"""
Calibration Records page.
"""
import streamlit as st
from datetime import date, timedelta

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.ui_helpers import (
    inject_global_css, page_header, empty_state,
    search_filter_bar, alert_banner,
)
from components.status_badge import cal_status_badge, expiry_countdown
from app.database import db_session
from app.models.calibration import CalibrationStatus
from app.services.calibration_service import CalibrationService
from app.repositories.calibration_repository import CalibrationRepository

st.set_page_config(page_title="Calibrations — LabAudit", page_icon="⚙️", layout="wide")

user = require_auth()
inject_global_css()
render_sidebar()
page_header("Calibrations", "Equipment calibration status and schedule", "⚙️")

org_id = st.session_state["org_id"]
can_write = user.is_manager_or_above

tab_list, tab_add = st.tabs(["📋 Equipment List", "➕ Add Record"])

with tab_list:
    query, filters = search_filter_bar(
        search_key="cal_search",
        placeholder="Search equipment name or ID...",
        extra_filters=[
            ("Status",     [s.value.replace("_"," ").title() for s in CalibrationStatus], "cal_status_filter"),
            ("Department", ["Chemistry", "Microbiology", "Quality Assurance", "Management"], "cal_dept_filter"),
        ],
    )

    @st.cache_data(ttl=60, show_spinner=False)
    def load_cals(_org_id):
        with db_session() as db:
            repo = CalibrationRepository(db)
            return repo.get_all(_org_id, limit=500)

    all_cals = load_cals(org_id)
    q_lower = (query or "").lower()
    status_filter = filters.get("cal_status_filter", "All")
    dept_filter   = filters.get("cal_dept_filter", "All")

    displayed = [
        c for c in all_cals
        if (not q_lower or q_lower in c.equipment_name.lower() or q_lower in c.equipment_id.lower())
        and (status_filter == "All" or c.status.value.replace("_"," ").title() == status_filter)
        and (dept_filter == "All" or c.department == dept_filter)
    ]

    st.caption(f"{len(displayed)} equipment record(s)")

    if not displayed:
        empty_state("No calibration records found.", "⚙️")
    else:
        # Quick summary row
        n_overdue  = sum(1 for c in displayed if c.status == CalibrationStatus.OVERDUE)
        n_due_soon = sum(1 for c in displayed if c.status == CalibrationStatus.DUE_SOON)
        n_current  = sum(1 for c in displayed if c.status == CalibrationStatus.CURRENT)
        scols = st.columns(3)
        for col, (label, val, colour) in zip(scols, [
            ("Current", n_current, "#16a34a"),
            ("Due Soon", n_due_soon, "#ca8a04"),
            ("Overdue", n_overdue, "#dc2626"),
        ]):
            with col:
                st.markdown(
                    f"<div style='background:white;border:1px solid #e2e8f0;border-radius:10px;"
                    f"padding:0.75rem;text-align:center;'>"
                    f"<div style='font-size:1.6rem;font-weight:700;color:{colour};'>{val}</div>"
                    f"<div style='font-size:0.78rem;color:#64748b;'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        for rec in sorted(displayed, key=lambda x: (
            0 if x.status == CalibrationStatus.OVERDUE else
            1 if x.status == CalibrationStatus.DUE_SOON else 2,
            x.next_due or date.max,
        )):
            cols = st.columns([0.8, 0.8, 3, 1.5, 1.5, 1.5])
            with cols[0]:
                st.markdown(cal_status_badge(rec.status), unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{rec.equipment_id}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{rec.equipment_name}</span>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{rec.department or '—'}</span>", unsafe_allow_html=True)
            with cols[4]:
                last = rec.last_calibrated.strftime("%d %b %Y") if rec.last_calibrated else "—"
                st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>Last: {last}</span>", unsafe_allow_html=True)
            with cols[5]:
                st.markdown(expiry_countdown(rec.next_due), unsafe_allow_html=True)
            st.markdown("<hr style='margin:3px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

with tab_add:
    if not can_write:
        alert_banner("Manager or Admin role required.", "warning")
    else:
        with st.form("add_cal_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                eq_name   = st.text_input("Equipment Name *", placeholder="e.g. Analytical Balance A&D")
                eq_id     = st.text_input("Equipment ID *",   placeholder="e.g. EQ-BAL-003")
                dept      = st.selectbox("Department", ["", "Chemistry", "Microbiology", "Quality Assurance", "Management"])
                cal_by    = st.text_input("Calibrated By", placeholder="e.g. SIRIM QAS")
            with c2:
                last_cal  = st.date_input("Last Calibrated", value=date.today())
                interval  = st.selectbox("Calibration Interval", ["90 days", "180 days", "365 days", "730 days"])
                cert_no   = st.text_input("Certificate Number")
            submitted = st.form_submit_button("Save Record", type="primary")

        if submitted:
            if not eq_name or not eq_id:
                st.error("Equipment name and ID are required.")
            else:
                interval_days = int(interval.split()[0])
                next_due = last_cal + timedelta(days=interval_days)
                try:
                    with db_session() as db:
                        svc = CalibrationService(db)
                        svc.create(
                            org_id=org_id, equipment_name=eq_name, equipment_id=eq_id,
                            department=dept or None, last_calibrated=last_cal,
                            next_due=next_due, interval_days=interval_days,
                            calibrated_by=cal_by or None, certificate_number=cert_no or None,
                            acting_user=user,
                        )
                    st.success(f"✅ Calibration record added for {eq_name}.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
