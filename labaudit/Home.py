"""
LabAudit — main entry point.
Streamlit runs this file first; it handles auth gate then redirects to Dashboard.
"""
import streamlit as st

from app.utils.logging_config import setup_logging
from app.database import init_db, check_db_connection
from app.config import settings
from components.auth_guard import render_login_page, is_authenticated

# ── One-time setup ─────────────────────────────────────────────────────────────
setup_logging()

st.set_page_config(
    page_title="LabAudit",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "LabAudit — Laboratory Audit Readiness Platform",
    },
)

# ── DB init on first run ───────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to database...")
def startup():
    if not check_db_connection():
        st.error("❌ Cannot connect to database. Check your DATABASE_URL.")
        st.stop()
    init_db()
    if settings.SEED_DEMO_DATA:
        try:
            from app.utils.seed import run_seed
            run_seed()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Seed skipped: %s", e)
    return True

startup()

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not is_authenticated():
    render_login_page()
    st.stop()

# ── Redirect authenticated users to Dashboard ─────────────────────────────────
st.switch_page("pages/1_Dashboard.py")
