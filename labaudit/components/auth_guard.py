"""
Auth guard — login UI, session state management, and auth check helpers.

Session state keys used across the app:
  st.session_state["authenticated"]  : bool
  st.session_state["current_user"]   : User ORM object
  st.session_state["token"]          : JWT string
  st.session_state["org_id"]         : uuid.UUID
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
    """Call at the top of every page. Redirects to login if not authenticated."""
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
    _inject_login_css()

    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # Logo / branding
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:2rem;">
                <div style="font-size:3rem; margin-bottom:0.5rem;">🔬</div>
                <h1 style="font-size:2rem; font-weight:700; margin:0; color:#1e293b;">
                    LabAudit
                </h1>
                <p style="color:#64748b; margin-top:0.25rem; font-size:0.95rem;">
                    Laboratory Audit Readiness Platform
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email address",
                placeholder="you@lab.com",
                label_visibility="visible",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••",
            )
            submitted = st.form_submit_button(
                "Sign in", use_container_width=True, type="primary"
            )

        if submitted:
            _handle_login(email.strip(), password)

        # Demo credentials hint
        with st.expander("Demo credentials", expanded=False):
            st.markdown(
                """
                | Role | Email | Password |
                |------|-------|----------|
                | Admin | admin@nexusfood.com.my | Admin@1234 |
                | Manager | quality.manager@nexusfood.com.my | Manager@1234 |
                | Viewer | lab.microbio@nexusfood.com.my | Viewer@1234 |
                """
            )

        st.markdown("</div>", unsafe_allow_html=True)


def _handle_login(email: str, password: str) -> None:
    if not email or not password:
        st.warning("Please enter your email and password.")
        return

    with st.spinner("Signing in..."):
        try:
            with db_session() as db:
                service = AuthService(db)
                user, token = service.login(email, password)
                # Detach user from session before storing in session_state
                db.expunge(user)

            st.session_state["authenticated"] = True
            st.session_state["current_user"] = user
            st.session_state["token"] = token
            st.session_state["org_id"] = user.org_id

            st.success(f"Welcome back, {user.full_name.split()[0]}!")
            st.rerun()

        except AuthError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error("Something went wrong. Please try again.")
            import logging
            logging.getLogger(__name__).error("Login error: %s", e)


def _inject_login_css() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 50%, #f0faf4 100%);
        }
        [data-testid="stSidebar"] { display: none; }
        .login-card {
            background: white;
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            margin-top: 4rem;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            background: #2563eb !important;
            border: none !important;
            font-weight: 600 !important;
            height: 2.75rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
