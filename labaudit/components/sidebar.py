"""
Sidebar component — rendered on every authenticated page.
Shows org info, navigation links, user card, and logout button.
"""
from __future__ import annotations

import streamlit as st

from components.auth_guard import current_user, logout
from app.models.user import UserRole


# Role badge colours
_ROLE_STYLE = {
    UserRole.ADMIN:   ("🔴", "#fee2e2", "#991b1b"),
    UserRole.MANAGER: ("🟡", "#fef9c3", "#854d0e"),
    UserRole.VIEWER:  ("🔵", "#dbeafe", "#1e40af"),
}

# Page map: (label, icon, path)
_NAV = [
    ("Dashboard",     "📊", "pages/1_Dashboard.py"),
    ("Documents",     "📁", "pages/2_Documents.py"),
    ("Calibrations",  "⚙️", "pages/3_Calibration.py"),
    ("Training",      "🎓", "pages/4_Training.py"),
    ("CAPA",          "🔧", "pages/5_CAPA.py"),
    ("Audit View",    "✅", "pages/6_Audit_View.py"),
]
_ADMIN_NAV = [
    ("Admin",         "👤", "pages/7_Admin.py"),
]


def render_sidebar() -> None:
    user = current_user()
    emoji, bg, fg = _ROLE_STYLE.get(user.role, ("⚪", "#f1f5f9", "#475569"))

    with st.sidebar:
        # ── Brand ─────────────────────────────────────────
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;padding:0.5rem 0 1.2rem;">
                <span style="font-size:1.8rem;">🔬</span>
                <div>
                    <div style="font-weight:700;font-size:1.15rem;color:#1e293b;">LabAudit</div>
                    <div style="font-size:0.72rem;color:#64748b;margin-top:-2px;">Audit Readiness Platform</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Navigation ────────────────────────────────────
        st.markdown(
            "<div style='font-size:0.72rem;font-weight:600;color:#94a3b8;"
            "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;'>"
            "Navigation</div>",
            unsafe_allow_html=True,
        )

        nav_items = _NAV + (_ADMIN_NAV if user.is_admin else [])
        for label, icon, path in nav_items:
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{label}",
                use_container_width=True,
            ):
                st.switch_page(path)

        st.divider()

        # ── User card ─────────────────────────────────────
        initials = "".join(w[0].upper() for w in user.full_name.split()[:2])
        st.markdown(
            f"""
            <div style="background:#f8fafc;border-radius:12px;padding:0.85rem;margin-bottom:0.6rem;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:36px;height:36px;border-radius:50%;background:#2563eb;
                                color:white;display:flex;align-items:center;justify-content:center;
                                font-size:0.85rem;font-weight:700;flex-shrink:0;">
                        {initials}
                    </div>
                    <div style="min-width:0;">
                        <div style="font-weight:600;font-size:0.88rem;color:#1e293b;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                            {user.full_name}
                        </div>
                        <div style="font-size:0.75rem;color:#64748b;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                            {user.email}
                        </div>
                    </div>
                </div>
                <div style="margin-top:0.6rem;">
                    <span style="background:{bg};color:{fg};font-size:0.72rem;font-weight:600;
                                 padding:2px 8px;border-radius:999px;">
                        {emoji} {user.role.value.title()}
                    </span>
                    {"<span style='font-size:0.72rem;color:#64748b;margin-left:6px;'>" + (user.department or "") + "</span>" if user.department else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign out", use_container_width=True, key="logout_btn"):
            logout()
