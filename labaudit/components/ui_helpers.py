"""
Shared UI helpers — metric cards, page headers, tables, alerts, and CSS injection.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd


# ─── Global CSS ───────────────────────────────────────────────────────────────

def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Layout ── */
        [data-testid="stAppViewContainer"] { background: #f8fafc; }
        [data-testid="stSidebar"] {
            background: white !important;
            border-right: 1px solid #e2e8f0;
        }
        .block-container { padding-top: 1.5rem !important; }

        /* ── Buttons ── */
        button[kind="primary"] {
            background: #2563eb !important;
            border: none !important;
            font-weight: 600 !important;
        }
        button[kind="secondary"] {
            border: 1px solid #e2e8f0 !important;
            color: #1e293b !important;
        }

        /* ── Cards ── */
        .la-card {
            background: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 1.25rem;
            margin-bottom: 0.75rem;
        }
        .la-card:hover { border-color: #cbd5e1; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }

        /* ── Metric tiles ── */
        .la-metric {
            background: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 1.1rem 1.25rem;
            height: 100%;
        }

        /* ── Tabs ── */
        button[data-baseweb="tab"] {
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }

        /* ── Expanders ── */
        [data-testid="stExpander"] {
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
        }

        /* ── Dataframe ── */
        [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

        /* ── Inputs ── */
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] > div,
        [data-testid="stDateInput"] input {
            border-radius: 8px !important;
        }

        /* ── Divider ── */
        hr { border-color: #e2e8f0 !important; }

        /* ── Success/warning/error ── */
        [data-testid="stAlert"] { border-radius: 10px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─── Page header ──────────────────────────────────────────────────────────────

def page_header(title: str, subtitle: str | None = None, icon: str = "") -> None:
    st.markdown(
        f"""
        <div style="margin-bottom:1.5rem;">
            <h1 style="font-size:1.6rem;font-weight:700;color:#1e293b;margin:0;">
                {icon + '&nbsp;&nbsp;' if icon else ''}{title}
            </h1>
            {"<p style='color:#64748b;margin:0.2rem 0 0;font-size:0.93rem;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Metric cards ─────────────────────────────────────────────────────────────

def metric_card(
    label: str,
    value: str | int,
    delta: str | None = None,
    delta_good: bool = True,
    icon: str = "",
    accent: str = "#2563eb",
) -> None:
    delta_html = ""
    if delta is not None:
        delta_colour = "#16a34a" if delta_good else "#dc2626"
        delta_html = f"<div style='font-size:0.78rem;color:{delta_colour};margin-top:2px;'>{delta}</div>"

    st.markdown(
        f"""
        <div class="la-metric">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div style="font-size:0.78rem;color:#64748b;font-weight:500;">{label}</div>
                <div style="font-size:1.2rem;">{icon}</div>
            </div>
            <div style="font-size:2rem;font-weight:700;color:{accent};line-height:1.1;margin-top:4px;">
                {value}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card_danger(label: str, value: int, icon: str = "🔴") -> None:
    accent = "#dc2626" if value > 0 else "#16a34a"
    metric_card(label, str(value), icon=icon, accent=accent)


# ─── Section heading ──────────────────────────────────────────────────────────

def section_header(title: str, action_label: str | None = None) -> bool:
    """Returns True if action button was clicked."""
    cols = st.columns([5, 1])
    with cols[0]:
        st.markdown(
            f"<h3 style='font-size:1.05rem;font-weight:600;color:#1e293b;"
            f"margin:0.8rem 0 0.5rem;'>{title}</h3>",
            unsafe_allow_html=True,
        )
    if action_label:
        with cols[1]:
            return st.button(action_label, type="primary", use_container_width=True)
    return False


# ─── Empty state ──────────────────────────────────────────────────────────────

def empty_state(message: str = "No records found.", icon: str = "📭") -> None:
    st.markdown(
        f"""
        <div style="text-align:center;padding:3rem;color:#94a3b8;">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">{icon}</div>
            <div style="font-size:0.95rem;">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Alert banner ─────────────────────────────────────────────────────────────

def alert_banner(message: str, level: str = "warning") -> None:
    cfg = {
        "error":   ("#fef2f2", "#dc2626", "#fee2e2", "🚨"),
        "warning": ("#fffbeb", "#d97706", "#fde68a", "⚠️"),
        "info":    ("#eff6ff", "#2563eb", "#bfdbfe", "ℹ️"),
        "success": ("#f0fdf4", "#16a34a", "#bbf7d0", "✅"),
    }
    bg, fg, brd, icon = cfg.get(level, cfg["info"])
    st.markdown(
        f"""
        <div style="background:{bg};border:1px solid {brd};border-radius:10px;
                    padding:0.75rem 1rem;margin-bottom:0.75rem;color:{fg};
                    font-size:0.9rem;font-weight:500;">
            {icon} {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Pagination controls ──────────────────────────────────────────────────────

def pagination_controls(
    total: int,
    page_size: int,
    key: str = "page",
) -> int:
    """Returns current page number (1-indexed)."""
    total_pages = max(1, -(-total // page_size))  # ceiling division
    if total_pages <= 1:
        return 1

    current = st.session_state.get(f"_page_{key}", 1)
    cols = st.columns([2, 1, 1, 1, 2])

    with cols[1]:
        if st.button("← Prev", key=f"prev_{key}", disabled=current <= 1):
            st.session_state[f"_page_{key}"] = max(1, current - 1)
            st.rerun()
    with cols[2]:
        st.markdown(
            f"<div style='text-align:center;padding-top:0.45rem;font-size:0.85rem;"
            f"color:#64748b;'>{current} / {total_pages}</div>",
            unsafe_allow_html=True,
        )
    with cols[3]:
        if st.button("Next →", key=f"next_{key}", disabled=current >= total_pages):
            st.session_state[f"_page_{key}"] = min(total_pages, current + 1)
            st.rerun()

    return st.session_state.get(f"_page_{key}", 1)


# ─── Search + filter bar ──────────────────────────────────────────────────────

def search_filter_bar(
    search_key: str = "search",
    placeholder: str = "Search...",
    extra_filters: list[tuple] | None = None,   # [(label, options, key), ...]
) -> tuple[str, dict]:
    """
    Returns (search_query, {filter_key: selected_value}).
    extra_filters: list of (label, options_list, session_key)
    """
    cols_count = 2 + (len(extra_filters) if extra_filters else 0)
    weights = [3] + [1.5] * (cols_count - 1)
    cols = st.columns(weights)

    with cols[0]:
        query = st.text_input(
            "Search", placeholder=placeholder,
            key=search_key, label_visibility="collapsed"
        )

    selected: dict[str, str] = {}
    if extra_filters:
        for idx, (label, options, fkey) in enumerate(extra_filters):
            with cols[idx + 1]:
                selected[fkey] = st.selectbox(
                    label, ["All"] + list(options),
                    key=fkey, label_visibility="collapsed"
                )

    return query, selected
