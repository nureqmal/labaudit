"""Sidebar — redesigned 2026."""
from __future__ import annotations
import streamlit as st
from components.auth_guard import current_user, logout
from components.theme import render_theme_toggle, is_dark
from app.models.user import UserRole

_NAV = [
    ("Dashboard",    "📊", "pages/1_Dashboard.py"),
    ("Documents",    "📁", "pages/2_Documents.py"),
    ("Calibrations", "⚙️", "pages/3_Calibration.py"),
    ("Training",     "🎓", "pages/4_Training.py"),
    ("CAPA",         "🔧", "pages/5_CAPA.py"),
    ("Audit View",   "✅", "pages/6_Audit_View.py"),
]
_ADMIN_NAV = [("Admin", "👤", "pages/7_Admin.py")]

def render_sidebar() -> None:
    user = current_user()
    dark = is_dark()

    t1  = "#e8edf5" if dark else "#0f172a"
    t2  = "#8ba3c0" if dark else "#475569"
    t3  = "#4d6a8a" if dark else "#94a3b8"
    bd  = "#1e3a5f" if dark else "#e2e8f0"
    cb  = "#111f35" if dark else "#f8fafc"
    acc = "#3b82f6" if dark else "#2563eb"
    ag  = "rgba(59,130,246,0.12)" if dark else "rgba(37,99,235,0.08)"

    role_cfg = {
        UserRole.ADMIN:   ("#ef4444", "rgba(239,68,68,0.12)",   "Admin"),
        UserRole.MANAGER: ("#f59e0b", "rgba(245,158,11,0.12)",  "Manager"),
        UserRole.VIEWER:  ("#3b82f6", "rgba(59,130,246,0.12)",  "Viewer"),
    }
    role_color, role_bg, role_label = role_cfg.get(user.role, ("#94a3b8", "#f1f5f9", "Viewer"))
    initials = "".join(w[0].upper() for w in user.full_name.split()[:2])

    with st.sidebar:
        # ── Brand ─────────────────────────────────────
        st.markdown(f"""
        <div style="padding:1.5rem 1.25rem 1rem;border-bottom:1px solid {bd};">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:36px;height:36px;background:linear-gradient(135deg,{acc},#6366f1);
                            border-radius:10px;display:flex;align-items:center;justify-content:center;
                            font-size:1.1rem;flex-shrink:0;">🔬</div>
                <div>
                    <div style="font-weight:700;font-size:1rem;color:{t1};letter-spacing:-0.01em;">LabAudit</div>
                    <div style="font-size:0.68rem;color:{t3};margin-top:1px;font-weight:500;
                                text-transform:uppercase;letter-spacing:0.06em;">Audit Platform</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Nav label ─────────────────────────────────
        st.markdown(f"""
        <div style="padding:1rem 1.25rem 0.4rem;">
            <span style="font-size:0.68rem;font-weight:600;color:{t3};
                         text-transform:uppercase;letter-spacing:0.1em;">Menu</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Nav items ─────────────────────────────────
        nav_items = _NAV + (_ADMIN_NAV if user.is_admin else [])
        for label, icon, path in nav_items:
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.switch_page(path)

        # ── Divider ───────────────────────────────────
        st.markdown(f"<div style='height:1px;background:{bd};margin:0.75rem 0;'></div>", unsafe_allow_html=True)

        # ── Theme toggle ──────────────────────────────
        render_theme_toggle(location="sidebar")

        # ── Spacer ────────────────────────────────────
        st.markdown("<div style='flex:1;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='height:1px;background:{bd};margin:0.75rem 0;'></div>", unsafe_allow_html=True)

        # ── User card ─────────────────────────────────
        st.markdown(f"""
        <div style="padding:0 0.75rem 0.75rem;">
            <div style="background:{cb};border:1px solid {bd};border-radius:12px;padding:0.875rem;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.6rem;">
                    <div style="width:34px;height:34px;border-radius:50%;
                                background:linear-gradient(135deg,{acc},#6366f1);
                                color:white;display:flex;align-items:center;justify-content:center;
                                font-size:0.8rem;font-weight:700;flex-shrink:0;">{initials}</div>
                    <div style="min-width:0;">
                        <div style="font-weight:600;font-size:0.85rem;color:{t1};
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{user.full_name}</div>
                        <div style="font-size:0.72rem;color:{t2};
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{user.email}</div>
                    </div>
                </div>
                <div>
                    <span style="background:{role_bg};color:{role_color};font-size:0.68rem;
                                 font-weight:600;padding:3px 8px;border-radius:100px;
                                 text-transform:uppercase;letter-spacing:0.04em;">{role_label}</span>
                    {f'<span style="font-size:0.72rem;color:{t3};margin-left:6px;">{user.department}</span>' if user.department else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⎋  Sign out", use_container_width=True, key="logout_btn"):
            logout()
