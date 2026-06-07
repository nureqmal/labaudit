"""
Theme manager — handles dark/light mode toggle.
Stores preference in st.session_state["theme"] = "light" | "dark"
Call inject_theme_css() at the top of every page.
Call render_theme_toggle() in sidebar or login page.
"""
from __future__ import annotations
import streamlit as st


LIGHT = "light"
DARK  = "dark"


def get_theme() -> str:
    return st.session_state.get("theme", LIGHT)


def toggle_theme() -> None:
    current = get_theme()
    st.session_state["theme"] = DARK if current == LIGHT else LIGHT


def is_dark() -> bool:
    return get_theme() == DARK


def render_theme_toggle(location: str = "sidebar") -> None:
    """Render a toggle button. location = 'sidebar' or 'inline'"""
    dark = is_dark()
    label = "☀️  Light mode" if dark else "🌙  Dark mode"
    if location == "sidebar":
        if st.sidebar.button(label, key="theme_toggle_btn", use_container_width=True):
            toggle_theme()
            st.rerun()
    else:
        if st.button(label, key="theme_toggle_btn_inline"):
            toggle_theme()
            st.rerun()


def inject_theme_css() -> None:
    """Inject full CSS theme — call once at top of every page."""
    dark = is_dark()

    if dark:
        css = _dark_css()
    else:
        css = _light_css()

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ─── Light theme ──────────────────────────────────────────────────────────────

def _light_css() -> str:
    return """
    /* ── Root variables ── */
    :root {
        --bg-primary:    #f8fafc;
        --bg-secondary:  #ffffff;
        --bg-tertiary:   #f1f5f9;
        --border:        #e2e8f0;
        --border-focus:  #2563eb;
        --text-primary:  #1e293b;
        --text-secondary:#64748b;
        --text-muted:    #94a3b8;
        --accent:        #2563eb;
        --accent-hover:  #1d4ed8;
        --success:       #16a34a;
        --warning:       #ca8a04;
        --danger:        #dc2626;
        --sidebar-bg:    #ffffff;
        --card-shadow:   0 1px 4px rgba(0,0,0,0.06);
    }

    /* ── App background ── */
    [data-testid="stAppViewContainer"] {
        background: var(--bg-primary) !important;
    }
    [data-testid="stHeader"] {
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* ── Main content ── */
    .block-container {
        padding-top: 1.5rem !important;
        background: transparent !important;
    }

    /* ── Text ── */
    p, span, label, div {
        color: var(--text-primary);
    }
    h1, h2, h3, h4 {
        color: var(--text-primary) !important;
    }

    /* ── Inputs ── */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    }

    /* ── Buttons ── */
    button[kind="primary"] {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
    }
    button[kind="secondary"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    /* ── Cards / containers ── */
    [data-testid="stExpander"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    [data-testid="stForm"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
    }

    /* ── Divider ── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    """


# ─── Dark theme ───────────────────────────────────────────────────────────────

def _dark_css() -> str:
    return """
    /* ── Root variables ── */
    :root {
        --bg-primary:    #0f172a;
        --bg-secondary:  #1e293b;
        --bg-tertiary:   #162032;
        --border:        #334155;
        --border-focus:  #3b82f6;
        --text-primary:  #f1f5f9;
        --text-secondary:#94a3b8;
        --text-muted:    #64748b;
        --accent:        #3b82f6;
        --accent-hover:  #2563eb;
        --success:       #22c55e;
        --warning:       #eab308;
        --danger:        #ef4444;
        --sidebar-bg:    #1e293b;
        --card-shadow:   0 1px 4px rgba(0,0,0,0.3);
    }

    /* ── App background ── */
    [data-testid="stAppViewContainer"] {
        background: var(--bg-primary) !important;
    }
    [data-testid="stHeader"] {
        background: var(--bg-secondary) !important;
        border-bottom: 1px solid var(--border);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* ── Main content ── */
    .block-container {
        padding-top: 1.5rem !important;
        background: transparent !important;
    }

    /* ── Text ── */
    p, span, label, div {
        color: var(--text-primary);
    }
    h1, h2, h3, h4 {
        color: var(--text-primary) !important;
    }

    /* ── Inputs ── */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--border-focus) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }

    /* ── Buttons ── */
    button[kind="primary"] {
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
    }
    button[kind="secondary"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
    }

    /* ── Cards / containers ── */
    [data-testid="stExpander"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
    }
    [data-testid="stForm"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        background: transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom-color: var(--accent) !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] th {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stDataFrame"] td {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Divider ── */
    hr {
        border-color: var(--border) !important;
    }

    /* ── Plotly charts background ── */
    .js-plotly-plot .plotly {
        background: var(--bg-secondary) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ── Select dropdown options ── */
    [data-baseweb="popover"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
    }
    [role="option"] {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }
    [role="option"]:hover {
        background: var(--bg-tertiary) !important;
    }
    """
