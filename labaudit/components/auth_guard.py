"""
Auth guard — login UI, session state management, and auth check helpers.
"""
from __future__ import annotations

import streamlit as st

from app.database import db_session
from app.services.auth_service import AuthService, AuthError
from app.models.user import User


# ─── Session helpers ──────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated") and st.session_state.get("current_user"))


def current_user() -> User:
    user = st.session_state.get("current_user")
    if not user:
        st.error("Session expired. Please log in again.")
        st.session_state.clear()
        st.rerun()
    return user


def require_auth() -> User:
    if not is_authenticated():
        st.switch_page("Home.py")
    return current_user()


def require_write_access() -> User:
    user = require_auth()
    if not AuthService.can_write(user):
        st.error("⛔ You need Manager or Admin role to perform this action.")
        st.stop()
    return user


def require_admin() -> User:
    user = require_auth()
    if not AuthService.can_admin(user):
        st.error("⛔ Admin access required.")
        st.stop()
    return user


def logout() -> None:
    st.session_state.clear()
    st.rerun()


# ─── Login page ───────────────────────────────────────────────────────────────

def render_login_page() -> None:
    from components.theme import inject_theme_css, is_dark, toggle_theme, get_theme

    inject_theme_css()
    _inject_login_css()

    # ── Theme toggle ── top right corner
    dark = is_dark()
    toggle_col = st.container()
    with toggle_col:
        right = st.columns([6, 1])
        with right[1]:
            icon = "☀️" if dark else "🌙"
            if st.button(icon, key="login_theme_toggle", help="Toggle dark/light mode"):
                toggle_theme()
                st.rerun()

    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        # Card wrapper
        card_bg  = "#1e293b" if dark else "#ffffff"
        card_brd = "#334155" if dark else "#e2e8f0"
        text_col = "#f1f5f9" if dark else "#1e293b"
        sub_col  = "#94a3b8" if dark else "#64748b"

        st.markdown(
            f"""
            <div style="background:{card_bg};border:1px solid {card_brd};
                        border-radius:16px;padding:2.5rem;
                        box-shadow:0 4px 24px rgba(0,0,0,{'0.3' if dark else '0.08'});
                        margin-top:2rem;">
                <div style="text-align:center;margin-bottom:2rem;">
                    <div style="font-size:3rem;margin-bottom:0.5rem;">🔬</div>
                    <h1 style="font-size:2rem;font-weight:700;margin:0;color:{text_col};">
                        LabAudit
                    </h1>
                    <p style="color:{sub_col};margin-top:0.25rem;font-size:0.95rem;">
                        Laboratory Audit Readiness Platform
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            email    = st.text_input("Email address", placeholder="you@lab.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            _handle_login(email.strip(), password)

        with st.expander("Demo credentials", expanded=False):
            st.markdown(
                """
                | Role | Email | Password |
                |---|---|---|
                | Admin | admin@nexusfood.com.my | Admin1234 |
                | Manager | quality.manager@nexusfood.com.my | Manager1234 |
                | Viewer | lab.microbio@nexusfood.com.my | Viewer1234 |
                """
            )

        # Mode indicator
        mode_label = "🌙 Dark mode" if dark else "☀️ Light mode"
        st.markdown(
            f"<div style='text-align:center;margin-top:1rem;font-size:0.78rem;color:{sub_col};'>"
            f"Currently in {mode_label} — toggle with button above</div>",
            unsafe_allow_html=True,
        )


def _handle_login(email: str, password: str) -> None:
    if not email or not password:
        st.warning("Please enter your email and password.")
        return

    with st.spinner("Signing in..."):
        try:
            with db_session() as db:
                service = AuthService(db)
                user, token = service.login(email, password)
                db.expunge(user)

            st.session_state["authenticated"] = True
            st.session_state["current_user"]  = user
            st.session_state["token"]         = token
            st.session_state["org_id"]        = user.org_id

            st.success(f"Welcome back, {user.full_name.split()[0]}!")
            st.rerun()

        except AuthError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error("Something went wrong. Please try again.")
            import logging
            logging.getLogger(__name__).error("Login error: %s", e)


def _inject_login_css() -> None:
    from components.theme import is_dark
    dark = is_dark()
    bg = "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f2040 100%)" if dark else \
         "linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 50%, #f0faf4 100%)"

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background: {bg} !important;
        }}
        [data-testid="stSidebar"] {{ display: none; }}
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {{
            background: #2563eb !important;
            border: none !important;
            font-weight: 600 !important;
            height: 2.75rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
