"""
LabAudit Theme Engine — 2026 Design System
Completely disguises Streamlit's default UI.
Dark / Light mode support.
"""
from __future__ import annotations
import streamlit as st

LIGHT = "light"
DARK  = "dark"

def get_theme() -> str:
    return st.session_state.get("theme", LIGHT)

def toggle_theme() -> None:
    st.session_state["theme"] = DARK if get_theme() == LIGHT else LIGHT

def is_dark() -> bool:
    return get_theme() == DARK

def render_theme_toggle(location: str = "sidebar") -> None:
    dark = is_dark()
    label = "☀️  Light mode" if dark else "🌙  Dark mode"
    key = f"theme_toggle_{location}"
    if location == "sidebar":
        if st.sidebar.button(label, key=key, use_container_width=True):
            toggle_theme(); st.rerun()
    else:
        if st.button(label, key=key):
            toggle_theme(); st.rerun()

def inject_theme_css() -> None:
    dark = is_dark()
    if dark:
        bg_app      = "#070d1a"
        bg_card     = "#0d1829"
        bg_card2    = "#111f35"
        bg_input    = "#0d1829"
        border      = "#1e3a5f"
        border2     = "#1a3252"
        text1       = "#e8edf5"
        text2       = "#8ba3c0"
        text3       = "#4d6a8a"
        accent      = "#3b82f6"
        accent2     = "#2563eb"
        accent_glow = "rgba(59,130,246,0.15)"
        sidebar_bg  = "#0a1525"
        header_bg   = "#0a1525"
        success_bg  = "rgba(16,185,129,0.1)"
        warning_bg  = "rgba(245,158,11,0.1)"
        danger_bg   = "rgba(239,68,68,0.1)"
        scrollbar   = "#1e3a5f"
        tag_bg      = "rgba(59,130,246,0.1)"
    else:
        bg_app      = "#f0f4f8"
        bg_card     = "#ffffff"
        bg_card2    = "#f8fafc"
        bg_input    = "#ffffff"
        border      = "#e2e8f0"
        border2     = "#dde3ec"
        text1       = "#0f172a"
        text2       = "#475569"
        text3       = "#94a3b8"
        accent      = "#2563eb"
        accent2     = "#1d4ed8"
        accent_glow = "rgba(37,99,235,0.1)"
        sidebar_bg  = "#ffffff"
        header_bg   = "#ffffff"
        success_bg  = "rgba(16,185,129,0.08)"
        warning_bg  = "rgba(245,158,11,0.08)"
        danger_bg   = "rgba(239,68,68,0.08)"
        scrollbar   = "#e2e8f0"
        tag_bg      = "rgba(37,99,235,0.08)"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ═══════════════════════════════════════════
       RESET & FOUNDATION
    ═══════════════════════════════════════════ */
    *, *::before, *::after {{ box-sizing: border-box; }}

    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: {bg_app} !important;
        color: {text1} !important;
    }}

    /* Hide Streamlit branding */
    #MainMenu, footer, header {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    /* ═══════════════════════════════════════════
       SIDEBAR — Complete Redesign
    ═══════════════════════════════════════════ */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {border} !important;
        box-shadow: 2px 0 20px rgba(0,0,0,{'0.3' if dark else '0.06'}) !important;
        padding-top: 0 !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }}
    [data-testid="stSidebar"] .block-container {{
        padding: 0 !important;
    }}

    /* Sidebar buttons — nav items */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: transparent !important;
        border: none !important;
        border-radius: 10px !important;
        color: {text2} !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.6rem 1rem !important;
        margin: 1px 0 !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: {accent_glow} !important;
        color: {accent} !important;
    }}

    /* ═══════════════════════════════════════════
       MAIN CONTENT AREA
    ═══════════════════════════════════════════ */
    .main .block-container {{
        padding: 1.5rem 2rem 3rem !important;
        max-width: 1400px !important;
        background: transparent !important;
    }}

    /* ═══════════════════════════════════════════
       TYPOGRAPHY
    ═══════════════════════════════════════════ */
    h1 {{ font-size: 1.65rem !important; font-weight: 700 !important; color: {text1} !important; letter-spacing: -0.02em !important; margin-bottom: 0.25rem !important; }}
    h2 {{ font-size: 1.3rem !important; font-weight: 600 !important; color: {text1} !important; letter-spacing: -0.01em !important; }}
    h3 {{ font-size: 1.05rem !important; font-weight: 600 !important; color: {text1} !important; }}
    h4 {{ font-size: 0.95rem !important; font-weight: 600 !important; color: {text1} !important; }}
    p {{ color: {text2} !important; line-height: 1.6 !important; }}

    /* ═══════════════════════════════════════════
       CARDS & CONTAINERS
    ═══════════════════════════════════════════ */
    [data-testid="stExpander"] {{
        background: {bg_card} !important;
        border: 1px solid {border} !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 4px rgba(0,0,0,{'0.2' if dark else '0.04'}) !important;
        margin-bottom: 0.5rem !important;
    }}
    [data-testid="stExpander"] summary {{
        padding: 0.9rem 1.1rem !important;
        font-weight: 500 !important;
        color: {text1} !important;
    }}
    [data-testid="stExpander"] summary:hover {{
        background: {bg_card2} !important;
    }}

    [data-testid="stForm"] {{
        background: {bg_card} !important;
        border: 1px solid {border} !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,{'0.2' if dark else '0.04'}) !important;
    }}

    /* stVerticalBlock inside expander */
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
        padding: 0.5rem 1rem 1rem !important;
    }}

    /* ═══════════════════════════════════════════
       INPUTS & FORM CONTROLS
    ═══════════════════════════════════════════ */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input {{
        background: {bg_input} !important;
        border: 1.5px solid {border} !important;
        border-radius: 10px !important;
        color: {text1} !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 0.9rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }}
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px {accent_glow} !important;
        outline: none !important;
    }}
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stDateInput"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stCheckbox"] label {{
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        color: {text2} !important;
        margin-bottom: 4px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }}

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {{
        background: {bg_input} !important;
        border: 1.5px solid {border} !important;
        border-radius: 10px !important;
        color: {text1} !important;
        font-size: 0.9rem !important;
    }}
    [data-testid="stSelectbox"] > div > div:focus-within {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px {accent_glow} !important;
    }}

    /* ═══════════════════════════════════════════
       BUTTONS — Complete Override
    ═══════════════════════════════════════════ */
    button[kind="primary"] {{
        background: linear-gradient(135deg, {accent}, {accent2}) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.25rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 2px 8px {accent_glow} !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    button[kind="primary"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px {accent_glow} !important;
    }}
    button[kind="primary"]:active {{
        transform: translateY(0) !important;
    }}
    button[kind="secondary"] {{
        background: {bg_card} !important;
        color: {text1} !important;
        border: 1.5px solid {border} !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.6rem 1.25rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: {accent} !important;
        color: {accent} !important;
        background: {accent_glow} !important;
    }}
    button[kind="primaryFormSubmit"] {{
        background: linear-gradient(135deg, {accent}, {accent2}) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.7rem 1.5rem !important;
        width: 100% !important;
        box-shadow: 0 2px 12px {accent_glow} !important;
        transition: all 0.2s !important;
    }}
    button[kind="primaryFormSubmit"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px {accent_glow} !important;
    }}

    /* ═══════════════════════════════════════════
       TABS
    ═══════════════════════════════════════════ */
    [data-baseweb="tab-list"] {{
        background: {bg_card2} !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 2px !important;
        border: 1px solid {border} !important;
        width: fit-content !important;
        margin-bottom: 1.25rem !important;
    }}
    button[data-baseweb="tab"] {{
        background: transparent !important;
        border: none !important;
        border-radius: 9px !important;
        color: {text2} !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s !important;
    }}
    button[data-baseweb="tab"]:hover {{
        color: {text1} !important;
        background: {accent_glow} !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: {accent} !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px {accent_glow} !important;
    }}
    [data-baseweb="tab-highlight"] {{ display: none !important; }}
    [data-baseweb="tab-border"] {{ display: none !important; }}

    /* ═══════════════════════════════════════════
       METRICS
    ═══════════════════════════════════════════ */
    [data-testid="stMetric"] {{
        background: {bg_card} !important;
        border: 1px solid {border} !important;
        border-radius: 14px !important;
        padding: 1.1rem 1.25rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,{'0.2' if dark else '0.04'}) !important;
        transition: box-shadow 0.2s !important;
    }}
    [data-testid="stMetric"]:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,{'0.3' if dark else '0.08'}) !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: {text2} !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: {text1} !important;
        letter-spacing: -0.02em !important;
    }}

    /* ═══════════════════════════════════════════
       ALERTS & NOTIFICATIONS
    ═══════════════════════════════════════════ */
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        border: none !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.875rem 1rem !important;
    }}
    [data-testid="stAlert"][data-baseweb="notification"] {{
        background: {success_bg} !important;
    }}

    /* ═══════════════════════════════════════════
       DATAFRAME / TABLE
    ═══════════════════════════════════════════ */
    [data-testid="stDataFrame"] {{
        border: 1px solid {border} !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        box-shadow: 0 1px 4px rgba(0,0,0,{'0.2' if dark else '0.04'}) !important;
    }}
    [data-testid="stDataFrame"] th {{
        background: {bg_card2} !important;
        color: {text2} !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid {border} !important;
    }}
    [data-testid="stDataFrame"] td {{
        background: {bg_card} !important;
        color: {text1} !important;
        font-size: 0.875rem !important;
        padding: 0.65rem 1rem !important;
        border-bottom: 1px solid {border2} !important;
    }}
    [data-testid="stDataFrame"] tr:hover td {{
        background: {bg_card2} !important;
    }}

    /* ═══════════════════════════════════════════
       DIVIDERS & SEPARATORS
    ═══════════════════════════════════════════ */
    hr {{
        border: none !important;
        border-top: 1px solid {border} !important;
        margin: 1.25rem 0 !important;
    }}

    /* ═══════════════════════════════════════════
       CONTAINERS WITH BORDER
    ═══════════════════════════════════════════ */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: {bg_card} !important;
        border: 1px solid {border} !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 6px rgba(0,0,0,{'0.2' if dark else '0.05'}) !important;
        overflow: hidden !important;
    }}

    /* ═══════════════════════════════════════════
       PLOTLY CHARTS
    ═══════════════════════════════════════════ */
    .js-plotly-plot .plotly .main-svg {{
        background: transparent !important;
    }}
    .js-plotly-plot .plotly .bg {{
        fill: transparent !important;
    }}

    /* ═══════════════════════════════════════════
       SCROLLBAR
    ═══════════════════════════════════════════ */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {scrollbar}; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {text3}; }}

    /* ═══════════════════════════════════════════
       CAPTION & SMALL TEXT
    ═══════════════════════════════════════════ */
    [data-testid="stCaptionContainer"] {{
        color: {text3} !important;
        font-size: 0.78rem !important;
    }}

    /* ═══════════════════════════════════════════
       CHECKBOX & RADIO
    ═══════════════════════════════════════════ */
    [data-testid="stCheckbox"] {{
        gap: 8px !important;
    }}

    /* ═══════════════════════════════════════════
       FILE UPLOADER
    ═══════════════════════════════════════════ */
    [data-testid="stFileUploader"] {{
        background: {bg_card} !important;
        border: 2px dashed {border} !important;
        border-radius: 14px !important;
        padding: 1.5rem !important;
        transition: border-color 0.2s !important;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: {accent} !important;
    }}

    /* ═══════════════════════════════════════════
       SPINNER
    ═══════════════════════════════════════════ */
    [data-testid="stSpinner"] {{
        color: {accent} !important;
    }}

    /* ═══════════════════════════════════════════
       DOWNLOAD BUTTON
    ═══════════════════════════════════════════ */
    [data-testid="stDownloadButton"] button {{
        background: {bg_card} !important;
        border: 1.5px solid {accent} !important;
        color: {accent} !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s !important;
    }}
    [data-testid="stDownloadButton"] button:hover {{
        background: {accent} !important;
        color: white !important;
        box-shadow: 0 4px 12px {accent_glow} !important;
    }}

    /* ═══════════════════════════════════════════
       CUSTOM UTILITY CLASSES
    ═══════════════════════════════════════════ */
    .la-card {{
        background: {bg_card};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,{'0.2' if dark else '0.04'});
        transition: box-shadow 0.2s, transform 0.2s;
    }}
    .la-card:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,{'0.25' if dark else '0.08'});
        transform: translateY(-1px);
    }}
    .la-metric {{
        background: {bg_card};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        height: 100%;
        box-shadow: 0 1px 4px rgba(0,0,0,{'0.15' if dark else '0.04'});
        transition: all 0.2s;
    }}
    .la-metric:hover {{
        border-color: {accent};
        box-shadow: 0 4px 16px {accent_glow};
    }}
    .la-page-header {{
        margin-bottom: 1.75rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid {border};
    }}
    .la-tag {{
        display: inline-block;
        background: {tag_bg};
        color: {accent};
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 100px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    .la-row {{
        display: flex;
        align-items: center;
        padding: 0.65rem 0;
        border-bottom: 1px solid {border2};
        gap: 0.75rem;
    }}
    .la-row:last-child {{ border-bottom: none; }}
    .la-empty {{
        text-align: center;
        padding: 4rem 2rem;
        color: {text3};
    }}
    .la-empty-icon {{ font-size: 3rem; margin-bottom: 1rem; }}
    .la-empty-text {{ font-size: 0.95rem; }}
    </style>
    """, unsafe_allow_html=True)
