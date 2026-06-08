"""
Training Records page.
"""
import streamlit as st
from datetime import date

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.ui_helpers import inject_global_css, page_header, empty_state, alert_banner, search_filter_bar
from components.status_badge import training_status_badge, expiry_countdown
from app.database import db_session
from app.models.training import TrainingType, TrainingStatus
from app.services.training_service import TrainingService
from app.repositories.training_repository import TrainingRepository
from app.repositories.user_repository import UserRepository

st.set_page_config(page_title="Training — LabAudit", page_icon="🎓", layout="wide")

user = require_auth()
inject_theme_css()
inject_global_css()
render_sidebar()
page_header("Training Records", "Staff competency and training compliance", "🎓")

org_id    = st.session_state["org_id"]
can_write = user.is_manager_or_above

tab_list, tab_add = st.tabs(["📋 Training Records", "➕ Add Record"])

with tab_list:
    query, filters = search_filter_bar(
        search_key="trn_search",
        placeholder="Search training title...",
        extra_filters=[
            ("Status", [s.value.replace("_"," ").title() for s in TrainingStatus], "trn_status_filter"),
            ("Type",   [t.value.replace("_"," ").title() for t in TrainingType],   "trn_type_filter"),
        ],
    )

    @st.cache_data(ttl=60, show_spinner=False)
    def load_trn(_org_id):
        with db_session() as db:
            repo = TrainingRepository(db)
            return repo.get_all(_org_id, limit=500)

    all_trn = load_trn(org_id)
    q_lower = (query or "").lower()
    status_f = filters.get("trn_status_filter", "All")
    type_f   = filters.get("trn_type_filter", "All")

    displayed = [
        t for t in all_trn
        if (not q_lower or q_lower in t.training_title.lower())
        and (status_f == "All" or t.status.value.replace("_"," ").title() == status_f)
        and (type_f == "All" or t.training_type.value.replace("_"," ").title() == type_f)
    ]

    st.caption(f"{len(displayed)} training record(s)")

    if not displayed:
        empty_state("No training records found.", "🎓")
    else:
        for rec in sorted(displayed, key=lambda x: (
            0 if x.status == TrainingStatus.OVERDUE else
            1 if x.status == TrainingStatus.DUE_SOON else 2,
            x.expiry_date or date.max,
        )):
            cols = st.columns([0.7, 3, 1.5, 1.5, 1.5])
            with cols[0]:
                st.markdown(training_status_badge(rec.status), unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<span style='font-size:0.88rem;font-weight:500;color:#1e293b;'>{rec.training_title}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{rec.training_type.value.replace('_',' ').title()}</span>", unsafe_allow_html=True)
            with cols[3]:
                completed = rec.completed_date.strftime("%d %b %Y") if rec.completed_date else "—"
                st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>Done: {completed}</span>", unsafe_allow_html=True)
            with cols[4]:
                st.markdown(expiry_countdown(rec.expiry_date), unsafe_allow_html=True)
            st.markdown("<hr style='margin:3px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

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

        with st.form("add_trn_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                staff_sel   = st.selectbox("Staff Member *", [s[1] for s in staff])
                trn_title   = st.text_input("Training Title *", placeholder="e.g. ISO 17025 Awareness")
                trn_type    = st.selectbox("Training Type", [t.value.replace("_"," ").title() for t in TrainingType])
                trainer     = st.text_input("Trainer / Provider")
            with c2:
                completed   = st.date_input("Completion Date", value=date.today())
                has_expiry  = st.checkbox("This training has an expiry date")
                expiry_date = st.date_input("Expiry Date", value=None) if has_expiry else None
                notes       = st.text_area("Notes", height=80)

            submitted = st.form_submit_button("Save Record", type="primary")

        if submitted:
            if not trn_title or not staff_sel:
                st.error("Training title and staff member are required.")
            else:
                staff_id = next(s[0] for s in staff if s[1] == staff_sel)
                type_val = next(t for t in TrainingType if t.value.replace("_"," ").title() == trn_type)
                try:
                    with db_session() as db:
                        svc = TrainingService(db)
                        svc.create(
                            org_id=org_id, user_id=staff_id,
                            training_title=trn_title, training_type=type_val,
                            completed_date=completed, expiry_date=expiry_date,
                            trainer=trainer or None, notes=notes or None,
                            acting_user=user,
                        )
                    st.success(f"✅ Training record saved for {staff_sel}.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error: {e}")
