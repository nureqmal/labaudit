"""Shared UI helpers — 2026 redesign."""
from __future__ import annotations
import streamlit as st
from components.theme import is_dark

def inject_global_css() -> None:
    pass  # All CSS now handled by inject_theme_css() in theme.py

def page_header(title: str, subtitle: str | None = None, icon: str = "") -> None:
    dark = is_dark()
    t1 = "#e8edf5" if dark else "#0f172a"
    t2 = "#8ba3c0" if dark else "#64748b"
    bd = "#1e3a5f" if dark else "#e2e8f0"
    st.markdown(f"""
    <div class="la-page-header">
        <h1 style="margin:0;font-size:1.6rem;font-weight:700;color:{t1};letter-spacing:-0.02em;">
            {(icon + '&nbsp;&nbsp;') if icon else ''}{title}
        </h1>
        {f'<p style="margin:0.25rem 0 0;color:{t2};font-size:0.9rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)

def metric_card(label: str, value: str | int, delta: str | None = None,
                delta_good: bool = True, icon: str = "", accent: str | None = None) -> None:
    dark = is_dark()
    t1   = "#e8edf5" if dark else "#0f172a"
    t2   = "#8ba3c0" if dark else "#64748b"
    bg   = "#0d1829" if dark else "#ffffff"
    bd   = "#1e3a5f" if dark else "#e2e8f0"
    acc  = accent or ("#3b82f6" if dark else "#2563eb")
    delta_html = ""
    if delta:
        dc = "#10b981" if delta_good else "#ef4444"
        delta_html = f"<div style='font-size:0.75rem;color:{dc};margin-top:4px;font-weight:500;'>{delta}</div>"
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {bd};border-radius:14px;padding:1.1rem 1.25rem;
                height:100%;box-shadow:0 1px 4px rgba(0,0,0,0.05);transition:all 0.2s;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
            <div style="font-size:0.72rem;font-weight:600;color:{t2};text-transform:uppercase;letter-spacing:0.07em;">{label}</div>
            <div style="font-size:1.1rem;opacity:0.7;">{icon}</div>
        </div>
        <div style="font-size:2rem;font-weight:700;color:{acc};letter-spacing:-0.02em;line-height:1.1;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def metric_card_danger(label: str, value: int, icon: str = "🔴") -> None:
    dark  = is_dark()
    acc   = "#ef4444" if value > 0 else ("#10b981")
    metric_card(label, str(value), icon=icon, accent=acc)

def section_header(title: str, action_label: str | None = None) -> bool:
    dark = is_dark()
    t1   = "#e8edf5" if dark else "#0f172a"
    cols = st.columns([5, 1]) if action_label else [st.container()]
    with cols[0]:
        st.markdown(f"<h3 style='font-size:1rem;font-weight:600;color:{t1};"
                    f"margin:1rem 0 0.6rem;letter-spacing:-0.01em;'>{title}</h3>",
                    unsafe_allow_html=True)
    if action_label:
        with cols[1]:
            return st.button(action_label, type="primary", use_container_width=True)
    return False

def empty_state(message: str = "No records found.", icon: str = "📭") -> None:
    dark = is_dark()
    t3   = "#4d6a8a" if dark else "#94a3b8"
    st.markdown(f"""
    <div class="la-empty">
        <div class="la-empty-icon">{icon}</div>
        <div class="la-empty-text" style="color:{t3};">{message}</div>
    </div>
    """, unsafe_allow_html=True)

def alert_banner(message: str, level: str = "warning") -> None:
    dark = is_dark()
    cfg = {
        "error":   ("🚨", "#ef4444", "rgba(239,68,68,0.1)",   "rgba(239,68,68,0.2)"),
        "warning": ("⚠️", "#f59e0b", "rgba(245,158,11,0.1)",  "rgba(245,158,11,0.2)"),
        "info":    ("ℹ️", "#3b82f6", "rgba(59,130,246,0.1)",  "rgba(59,130,246,0.2)"),
        "success": ("✅", "#10b981", "rgba(16,185,129,0.1)",  "rgba(16,185,129,0.2)"),
    }
    icon, color, bg, brd = cfg.get(level, cfg["info"])
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {brd};border-radius:12px;
                padding:0.875rem 1rem;margin-bottom:0.75rem;
                display:flex;align-items:center;gap:10px;">
        <span>{icon}</span>
        <span style="color:{color};font-size:0.875rem;font-weight:500;">{message}</span>
    </div>
    """, unsafe_allow_html=True)

def search_filter_bar(search_key: str = "search", placeholder: str = "Search...",
                      extra_filters: list | None = None) -> tuple[str, dict]:
    dark = is_dark()
    cols_count = 2 + (len(extra_filters) if extra_filters else 0)
    weights = [3] + [1.5] * (cols_count - 1)
    cols = st.columns(weights)
    with cols[0]:
        query = st.text_input("Search", placeholder=placeholder,
                              key=search_key, label_visibility="collapsed")
    selected: dict[str, str] = {}
    if extra_filters:
        for idx, (label, options, fkey) in enumerate(extra_filters):
            with cols[idx + 1]:
                selected[fkey] = st.selectbox(label, ["All"] + list(options),
                                              key=fkey, label_visibility="collapsed")
    return query, selected

def pagination_controls(total: int, page_size: int, key: str = "page") -> int:
    total_pages = max(1, -(-total // page_size))
    if total_pages <= 1:
        return 1
    current = st.session_state.get(f"_page_{key}", 1)
    dark = is_dark()
    t2 = "#8ba3c0" if dark else "#64748b"
    cols = st.columns([2, 1, 1, 1, 2])
    with cols[1]:
        if st.button("← Prev", key=f"prev_{key}", disabled=current <= 1):
            st.session_state[f"_page_{key}"] = max(1, current - 1); st.rerun()
    with cols[2]:
        st.markdown(f"<div style='text-align:center;padding-top:0.45rem;font-size:0.82rem;"
                    f"color:{t2};'>{current} / {total_pages}</div>", unsafe_allow_html=True)
    with cols[3]:
        if st.button("Next →", key=f"next_{key}", disabled=current >= total_pages):
            st.session_state[f"_page_{key}"] = min(total_pages, current + 1); st.rerun()
    return st.session_state.get(f"_page_{key}", 1)
