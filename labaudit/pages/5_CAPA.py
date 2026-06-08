"""
CAPA page — Corrective and Preventive Actions.
"""
import streamlit as st
from datetime import date, timedelta

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.ui_helpers import inject_global_css, page_header, empty_state, alert_banner, search_filter_bar
from components.status_badge import capa_status_badge, capa_priority_badge, expiry_countdown
from app.database import db_session
from app.models.capa import CapaType, CapaPriority, CapaStatus
from app.services.capa_service import CapaService
from app.repositories.capa_repository import CapaRepository
from app.repositories.user_repository import UserRepository

st.set_page_config(page_title="CAPA — LabAudit", page_icon="🔧", layout="wide")

user = require_auth()
inject_theme_css()
inject_global_css()
render_sidebar()
page_header("CAPA", "Corrective and Preventive Actions register", "🔧")

org_id    = st.session_state["org_id"]
can_write = user.is_manager_or_above

tab_list, tab_add = st.tabs(["📋 CAPA Register", "➕ Raise New CAPA"])

with tab_list:
    query, filters = search_filter_bar(
        search_key="capa_search",
        placeholder="Search CAPA title or reference...",
        extra_filters=[
            ("Status",   [s.value.replace("_"," ").title() for s in CapaStatus],   "capa_status_filter"),
            ("Priority", [p.value.title() for p in CapaPriority],                  "capa_priority_filter"),
        ],
    )

    @st.cache_data(ttl=60, show_spinner=False)
    def load_capas(_org_id):
        with db_session() as db:
            repo = CapaRepository(db)
            return repo.get_all(_org_id, limit=500)

    all_capas = load_capas(org_id)
    q_lower  = (query or "").lower()
    stat_f   = filters.get("capa_status_filter", "All")
    prior_f  = filters.get("capa_priority_filter", "All")

    displayed = [
        c for c in all_capas
        if (not q_lower or q_lower in c.title.lower() or q_lower in c.reference_no.lower())
        and (stat_f == "All" or c.status.value.replace("_"," ").title() == stat_f)
        and (prior_f == "All" or c.priority.value.title() == prior_f)
    ]

    st.caption(f"{len(displayed)} CAPA item(s)")

    if not displayed:
        empty_state("No CAPA records found.", "🔧")
    else:
        for item in sorted(displayed, key=lambda x: (
            x.status != CapaStatus.OVERDUE,
            x.priority != CapaPriority.CRITICAL,
            x.due_date or date.max,
        )):
            with st.expander(
                f"{item.reference_no} — {item.title[:70]}{'...' if len(item.title)>70 else ''}",
                expanded=(item.status in (CapaStatus.OVERDUE,) or item.priority == CapaPriority.CRITICAL),
            ):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown("**Status**")
                    st.markdown(capa_status_badge(item.status), unsafe_allow_html=True)
                with c2:
                    st.markdown("**Priority**")
                    st.markdown(capa_priority_badge(item.priority), unsafe_allow_html=True)
                with c3:
                    st.markdown("**Type**")
                    st.markdown(f"<span style='font-size:0.85rem;color:#64748b;'>{item.capa_type.value.title()}</span>", unsafe_allow_html=True)
                with c4:
                    st.markdown("**Due Date**")
                    st.markdown(expiry_countdown(item.due_date), unsafe_allow_html=True)

                if item.description:
                    st.markdown(f"**Description:** {item.description}")
                if item.root_cause:
                    st.markdown(f"**Root Cause:** {item.root_cause}")
                if item.action_taken:
                    st.markdown(f"**Action Taken:** {item.action_taken}")
                if item.source:
                    st.caption(f"Source: {item.source}")

                # Status transition buttons (manager+)
                if can_write and item.status != CapaStatus.CLOSED:
                    st.divider()
                    btn_cols = st.columns(4)
                    transitions = {
                        CapaStatus.OPEN:         [(CapaStatus.IN_PROGRESS, "▶ Start", "secondary")],
                        CapaStatus.IN_PROGRESS:  [(CapaStatus.PENDING_VERIFICATION, "🔍 Submit for Review", "secondary")],
                        CapaStatus.PENDING_VERIFICATION: [(CapaStatus.CLOSED, "✅ Close", "primary")],
                        CapaStatus.OVERDUE:      [(CapaStatus.IN_PROGRESS, "▶ Start Now", "primary")],
                    }
                    for trans in transitions.get(item.status, []):
                        new_status, label, btn_type = trans
                        with btn_cols[0]:
                            if st.button(label, key=f"trans_{item.id}_{new_status.value}", type=btn_type):
                                try:
                                    with db_session() as db:
                                        repo = CapaRepository(db)
                                        db_item = repo.get_by_id(item.id)
                                        svc = CapaService(db)
                                        svc.transition_status(db_item, new_status, user)
                                    st.success(f"CAPA {item.reference_no} updated to {new_status.value}.")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

with tab_add:
    if not can_write:
        alert_banner("Manager or Admin role required.", "warning")
    else:
        @st.cache_data(ttl=300, show_spinner=False)
        def load_users(_org_id):
            with db_session() as db:
                repo = UserRepository(db)
                return [(u.id, u.full_name) for u in repo.get_by_org(_org_id)]

        staff = load_users(org_id)

        with st.form("raise_capa_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                title_     = st.text_input("CAPA Title *", placeholder="Describe the issue or action...")
                capa_type  = st.selectbox("Type", [t.value.title() for t in CapaType])
                priority   = st.selectbox("Priority", [p.value.title() for p in CapaPriority])
                source     = st.text_input("Source", placeholder="e.g. Internal Audit, Customer Complaint")
            with c2:
                department = st.selectbox("Department", ["", "Chemistry", "Microbiology", "Quality Assurance", "Management"])
                assigned   = st.selectbox("Assign To", ["Unassigned"] + [s[1] for s in staff])
                due_date   = st.date_input("Due Date", value=date.today() + timedelta(days=30))
                description = st.text_area("Description", height=80)

            submitted = st.form_submit_button("Raise CAPA", type="primary")

        if submitted:
            if not title_:
                st.error("CAPA title is required.")
            else:
                type_val = next(t for t in CapaType if t.value.title() == capa_type)
                prio_val = next(p for p in CapaPriority if p.value.title() == priority)
                assigned_id = next((s[0] for s in staff if s[1] == assigned), None) if assigned != "Unassigned" else None
                try:
                    with db_session() as db:
                        svc = CapaService(db)
                        item = svc.create(
                            org_id=org_id, title=title_, capa_type=type_val,
                            priority=prio_val, department=department or None,
                            description=description or None, source=source or None,
                            due_date=due_date, assigned_to=assigned_id,
                            acting_user=user,
                        )
                    st.success(f"✅ CAPA {item.reference_no} raised successfully.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
