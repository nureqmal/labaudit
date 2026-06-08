"""Auth guard — redesigned login page."""
from __future__ import annotations
import streamlit as st
from app.database import db_session
from app.services.auth_service import AuthService, AuthError
from app.models.user import User

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
        st.error("⛔ Manager or Admin role required.")
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

def render_login_page() -> None:
    from components.theme import inject_theme_css, is_dark, toggle_theme
    inject_theme_css()

    dark = is_dark()
    bg_page  = "radial-gradient(ellipse at 60% 0%, #1a3a6e 0%, #070d1a 60%)" if dark else \
               "radial-gradient(ellipse at 60% 0%, #dbeafe 0%, #f0f4f8 60%)"
    bg_card  = "#0d1829" if dark else "#ffffff"
    bd_card  = "#1e3a5f" if dark else "#e2e8f0"
    t1       = "#e8edf5" if dark else "#0f172a"
    t2       = "#8ba3c0" if dark else "#64748b"
    t3       = "#4d6a8a" if dark else "#94a3b8"
    acc      = "#3b82f6" if dark else "#2563eb"
    acc_glow = "rgba(59,130,246,0.2)" if dark else "rgba(37,99,235,0.1)"
    inp_bg   = "#111f35" if dark else "#f8fafc"
    inp_bd   = "#1e3a5f" if dark else "#e2e8f0"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif !important; }}
    [data-testid="stAppViewContainer"] {{ background: {bg_page} !important; }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stDecoration"] {{ display:none !important; }}
    .main .block-container {{ max-width: 460px !important; margin: 0 auto !important; padding-top: 4rem !important; }}
    [data-testid="stTextInput"] input {{
        background: {inp_bg} !important; border: 1.5px solid {inp_bd} !important;
        color: {t1} !important; border-radius: 10px !important;
        font-size: 0.9rem !important; padding: 0.65rem 0.9rem !important;
    }}
    [data-testid="stTextInput"] input:focus {{
        border-color: {acc} !important; box-shadow: 0 0 0 3px {acc_glow} !important;
    }}
    [data-testid="stTextInput"] label {{
        font-size: 0.78rem !important; font-weight: 600 !important; color: {t2} !important;
        text-transform: uppercase !important; letter-spacing: 0.06em !important;
    }}
    button[kind="primaryFormSubmit"] {{
        background: linear-gradient(135deg, {acc}, #6366f1) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        font-weight: 600 !important; font-size: 0.9rem !important; padding: 0.75rem !important;
        width: 100% !important; box-shadow: 0 4px 16px {acc_glow} !important;
        transition: all 0.2s !important; cursor: pointer !important;
    }}
    button[kind="primaryFormSubmit"]:hover {{ transform: translateY(-1px) !important; }}
    [data-testid="stExpander"] {{
        background: {inp_bg} !important; border: 1px solid {inp_bd} !important;
        border-radius: 10px !important; margin-top: 0.5rem !important;
    }}
    [data-testid="stExpander"] summary {{ color: {t2} !important; font-size: 0.85rem !important; }}
    </style>
    """, unsafe_allow_html=True)

    # Theme toggle
    col_r = st.columns([5, 1])
    with col_r[1]:
        icon = "☀️" if dark else "🌙"
        if st.button(icon, key="login_theme_toggle", help="Toggle theme"):
            toggle_theme(); st.rerun()

    # Logo
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:2rem;">
        <div style="width:56px;height:56px;background:linear-gradient(135deg,{acc},#6366f1);
                    border-radius:16px;display:flex;align-items:center;justify-content:center;
                    font-size:1.8rem;margin:0 auto 1rem;
                    box-shadow:0 8px 24px {acc_glow};">🔬</div>
        <h1 style="font-size:1.75rem;font-weight:700;color:{t1};margin:0;letter-spacing:-0.03em;">LabAudit</h1>
        <p style="color:{t2};margin:0.25rem 0 0;font-size:0.875rem;">Laboratory Audit Readiness Platform</p>
    </div>
    """, unsafe_allow_html=True)

    # Card
    st.markdown(f"""
    <div style="background:{bg_card};border:1px solid {bd_card};border-radius:20px;
                padding:2rem;box-shadow:0 8px 32px rgba(0,0,0,{'0.3' if dark else '0.1'});">
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown(f"<p style='font-size:1.05rem;font-weight:600;color:{t1};margin-bottom:1.25rem;'>Sign in to your account</p>", unsafe_allow_html=True)
        email    = st.text_input("Email address", placeholder="you@lab.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Sign in →", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        _handle_login(email.strip(), password)

    with st.expander("Demo credentials"):
        st.markdown(f"""
        <div style="font-size:0.82rem;color:{t2};">
        <div style="margin-bottom:6px;"><strong style="color:{t1};">Admin</strong> — admin@nexusfood.com.my / Admin1234</div>
        <div style="margin-bottom:6px;"><strong style="color:{t1};">Manager</strong> — quality.manager@nexusfood.com.my / Manager1234</div>
        <div><strong style="color:{t1};">Viewer</strong> — lab.microbio@nexusfood.com.my / Viewer1234</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<p style='text-align:center;color:{t3};font-size:0.75rem;margin-top:1.5rem;'>© 2025 LabAudit · Secure login</p>", unsafe_allow_html=True)

def _handle_login(email: str, password: str) -> None:
    if not email or not password:
        st.warning("Please enter your email and password.")
        return
    with st.spinner("Authenticating..."):
        try:
            with db_session() as db:
                service = AuthService(db)
                user, token = service.login(email, password)
                db.expunge(user)
            st.session_state["authenticated"] = True
            st.session_state["current_user"]  = user
            st.session_state["token"]         = token
            st.session_state["org_id"]        = user.org_id
            st.rerun()
        except AuthError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error("Something went wrong. Please try again.")
            import logging
            logging.getLogger(__name__).error("Login error: %s", e)
