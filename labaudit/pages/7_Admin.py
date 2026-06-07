"""
Admin page — user management, org settings, audit trail.
Admin role only.
"""
import streamlit as st
from datetime import datetime

from components.auth_guard import require_admin
from components.sidebar import render_sidebar
from components.ui_helpers import inject_global_css, page_header, empty_state, alert_banner
from app.database import db_session
from app.models.user import UserRole
from app.services.auth_service import AuthService, AuthError
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository

st.set_page_config(page_title="Admin — LabAudit", page_icon="👤", layout="wide")

user = require_admin()
inject_theme_css()
inject_global_css()
render_sidebar()
page_header("Admin Panel", "User management, org settings and audit trail", "👤")

org_id = st.session_state["org_id"]

tab_users, tab_audit = st.tabs(["👥 Users", "📜 Audit Trail"])

# ── Users tab ─────────────────────────────────────────────────────────────────
with tab_users:
    @st.cache_data(ttl=60, show_spinner=False)
    def load_users(_org_id):
        with db_session() as db:
            repo = UserRepository(db)
            return repo.get_by_org(_org_id, active_only=False)

    users = load_users(org_id)
    st.markdown(f"**{len(users)} users** in this organisation")
    st.divider()

    # User list
    for u in users:
        role_colours = {
            UserRole.ADMIN:   ("#991b1b", "#fee2e2"),
            UserRole.MANAGER: ("#854d0e", "#fef9c3"),
            UserRole.VIEWER:  ("#1e40af", "#dbeafe"),
        }
        fg, bg = role_colours.get(u.role, ("#475569", "#f1f5f9"))
        active_dot = "🟢" if u.is_active else "🔴"
        last_login = u.last_login.strftime("%d %b %Y %H:%M") if u.last_login else "Never"

        cols = st.columns([2.5, 2, 1.2, 1.5, 1])
        with cols[0]:
            st.markdown(
                f"<span style='font-weight:600;color:#1e293b;'>{u.full_name}</span> "
                f"<span style='font-size:0.8rem;color:#64748b;'>{u.email}</span>",
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(f"<span style='font-size:0.8rem;color:#64748b;'>{u.job_title or '—'} · {u.department or '—'}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(
                f"<span style='background:{bg};color:{fg};padding:2px 10px;border-radius:999px;"
                f"font-size:0.75rem;font-weight:600;'>{u.role.value.title()}</span>",
                unsafe_allow_html=True,
            )
        with cols[3]:
            st.markdown(f"<span style='font-size:0.78rem;color:#94a3b8;'>Last: {last_login}</span>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"{active_dot} {'Active' if u.is_active else 'Inactive'}", unsafe_allow_html=True)

        st.markdown("<hr style='margin:4px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

    st.divider()

    # Create new user
    with st.expander("➕ Create New User", expanded=False):
        with st.form("create_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                new_name  = st.text_input("Full Name *")
                new_email = st.text_input("Email *")
                new_title = st.text_input("Job Title")
                new_dept  = st.text_input("Department")
            with c2:
                new_role  = st.selectbox("Role", [r.value.title() for r in UserRole])
                new_pass  = st.text_input("Password *", type="password")
                new_pass2 = st.text_input("Confirm Password *", type="password")

            if st.form_submit_button("Create User", type="primary"):
                if not new_name or not new_email or not new_pass:
                    st.error("Name, email and password are required.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                else:
                    role_val = next(r for r in UserRole if r.value.title() == new_role)
                    try:
                        with db_session() as db:
                            svc = AuthService(db)
                            svc.create_user(
                                org_id=org_id, email=new_email,
                                password=new_pass, full_name=new_name,
                                role=role_val, job_title=new_title or None,
                                department=new_dept or None, created_by=user,
                            )
                        st.success(f"✅ User {new_email} created.")
                        st.cache_data.clear()
                        st.rerun()
                    except AuthError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Error: {e}")


# ── Audit trail tab ───────────────────────────────────────────────────────────
with tab_audit:
    @st.cache_data(ttl=30, show_spinner=False)
    def load_logs(_org_id):
        with db_session() as db:
            repo = AuditLogRepository(db)
            return repo.get_recent(_org_id, limit=100)

    logs = load_logs(org_id)
    st.markdown(f"**Last {len(logs)} events**")
    st.divider()

    if not logs:
        empty_state("No audit log entries.", "📜")
    else:
        action_icons = {
            "user.login": "🔑", "user.login_failed": "⚠️",
            "document.create": "📄", "document.update": "✏️",
            "document.archive": "📦", "document.new_version": "🔄",
            "capa.create": "🔧", "capa.status_change": "🔄",
            "calibration.create": "⚙️", "calibration.update": "⚙️",
            "training.create": "🎓",
        }
        for log in logs:
            icon = action_icons.get(log.action, "📋")
            ts   = log.created_at.strftime("%d %b %Y %H:%M") if log.created_at else "—"
            cols = st.columns([0.3, 1.2, 3, 1.5])
            with cols[0]:
                st.markdown(icon)
            with cols[1]:
                st.markdown(f"<span style='font-size:0.78rem;color:#94a3b8;'>{ts}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<span style='font-size:0.85rem;color:#1e293b;'>{log.summary or log.action}</span>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<span style='font-size:0.78rem;color:#64748b;'>{log.action}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:2px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)
