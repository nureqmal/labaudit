"""
Dashboard — Audit Readiness Score + KPI tiles + Alerts + Quick charts.
"Know your audit readiness in 30 seconds."
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.score_card import render_score_gauge, render_pillar_cards
from components.ui_helpers import (
    inject_global_css, page_header, metric_card,
    metric_card_danger, section_header, empty_state, alert_banner,
)
from components.status_badge import alert_dot, expiry_countdown
from app.database import db_session
from app.services.audit_score_service import AuditScoreService
from app.services.notification_service import NotificationService, AlertLevel

st.set_page_config(
    page_title="Dashboard — LabAudit",
    page_icon="📊",
    layout="wide",
)

# ── Auth + layout setup ───────────────────────────────────────────────────────
user = require_auth()
inject_global_css()
render_sidebar()
page_header("Dashboard", "Real-time audit readiness overview", "📊")

org_id = st.session_state["org_id"]

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner="Calculating readiness score...")
def load_report(_org_id):
    with db_session() as db:
        svc = AuditScoreService(db)
        return svc.calculate(_org_id)

@st.cache_data(ttl=120, show_spinner=False)
def load_alerts(_org_id):
    with db_session() as db:
        svc = NotificationService(db)
        return svc.get_alerts(_org_id)

report = load_report(org_id)
alerts = load_alerts(org_id)

# ── Top: Score gauge + critical alerts ───────────────────────────────────────
col_gauge, col_alerts = st.columns([1.3, 1])

with col_gauge:
    with st.container(border=True):
        render_score_gauge(report)

with col_alerts:
    with st.container(border=True):
        st.markdown(
            "<div style='font-weight:600;font-size:0.95rem;color:#1e293b;"
            "margin-bottom:0.75rem;'>🚨 Action Required</div>",
            unsafe_allow_html=True,
        )
        red_alerts = [a for a in alerts if a.level == AlertLevel.RED]
        if not red_alerts:
            st.markdown(
                "<div style='text-align:center;padding:1.5rem;color:#16a34a;'>"
                "✅ No critical issues</div>",
                unsafe_allow_html=True,
            )
        else:
            for a in red_alerts[:6]:
                st.markdown(
                    f"<div style='padding:0.5rem 0;border-bottom:1px solid #f1f5f9;"
                    f"font-size:0.85rem;'>"
                    f"{alert_dot('red')}"
                    f"<span style='font-weight:500;color:#1e293b;'>{a.category}</span>"
                    f"<span style='color:#64748b;margin-left:6px;'>{a.title}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if len(red_alerts) > 6:
                st.caption(f"+ {len(red_alerts)-6} more critical items")

# ── Pillar breakdown ──────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.8rem;color:#94a3b8;font-weight:500;"
    "text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem;'>"
    "Compliance Pillars</p>",
    unsafe_allow_html=True,
)
render_pillar_cards(report)

# ── KPI metric tiles ──────────────────────────────────────────────────────────
st.divider()
section_header("Key Metrics")

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    metric_card("Total Documents", report.total_documents, icon="📁", accent="#2563eb")
with c2:
    metric_card_danger("Overdue Docs", report.overdue_documents, icon="📄")
with c3:
    metric_card(
        "Expiring (30d)", report.expiring_30d_documents,
        icon="⏰",
        accent="#d97706" if report.expiring_30d_documents > 0 else "#16a34a",
    )
with c4:
    metric_card_danger("Overdue Calibrations", report.overdue_calibrations, icon="⚙️")
with c5:
    metric_card_danger("Overdue Training", report.overdue_training, icon="🎓")
with c6:
    metric_card_danger("Open CAPAs", report.open_capas, icon="🔧")

# ── Expiry warnings ───────────────────────────────────────────────────────────
st.divider()

warn_cols = st.columns(3)
warn_data = [
    ("7 days", report.expiring_7d_documents,  "red"),
    ("14 days", report.expiring_14d_documents, "orange"),
    ("30 days", report.expiring_30d_documents, "yellow"),
]
for col, (label, count, lvl) in zip(warn_cols, warn_data):
    with col:
        colour_map = {"red": "#fee2e2", "orange": "#ffedd5", "yellow": "#fef9c3"}
        fg_map     = {"red": "#991b1b",  "orange": "#9a3412", "yellow": "#854d0e"}
        bg  = colour_map[lvl] if count > 0 else "#f0fdf4"
        fg  = fg_map[lvl]     if count > 0 else "#166534"
        st.markdown(
            f"""
            <div style="background:{bg};border-radius:12px;padding:1rem;text-align:center;">
                <div style="font-size:0.78rem;color:{fg};font-weight:500;">
                    Documents expiring within {label}
                </div>
                <div style="font-size:2.2rem;font-weight:700;color:{fg};line-height:1.1;margin-top:4px;">
                    {count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Charts row ────────────────────────────────────────────────────────────────
st.divider()
chart_l, chart_r = st.columns(2)

with chart_l:
    section_header("Compliance by Pillar")
    pillar_data = pd.DataFrame([
        {"Pillar": p.name, "Score": p.score, "Weight": f"{int(p.weight*100)}%"}
        for p in report.pillars
    ])
    colours = [
        "#16a34a" if s >= 90 else "#ca8a04" if s >= 70 else "#dc2626"
        for s in pillar_data["Score"]
    ]
    fig = go.Figure(go.Bar(
        x=pillar_data["Pillar"],
        y=pillar_data["Score"],
        marker_color=colours,
        text=pillar_data["Score"].apply(lambda x: f"{x:.0f}%"),
        textposition="outside",
        textfont={"size": 12, "color": "#1e293b"},
    ))
    fig.add_hline(y=90, line_dash="dot", line_color="#16a34a", annotation_text="Target 90%")
    fig.update_layout(
        height=250,
        margin=dict(t=20, b=10, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#f1f5f9"),
        xaxis=dict(showgrid=False),
        showlegend=False,
        font={"family": "Inter, sans-serif", "size": 12},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with chart_r:
    section_header("CAPA Status Distribution")
    from app.database import db_session
    from app.repositories.capa_repository import CapaRepository

    @st.cache_data(ttl=120, show_spinner=False)
    def load_capa_counts(_org_id):
        with db_session() as db:
            repo = CapaRepository(db)
            return repo.count_by_status(_org_id)

    capa_counts = load_capa_counts(org_id)
    capa_labels = {
        "open": "Open", "in_progress": "In Progress",
        "pending_verification": "Pending", "closed": "Closed", "overdue": "Overdue",
    }
    capa_colours = {
        "open": "#3b82f6", "in_progress": "#f59e0b",
        "pending_verification": "#8b5cf6", "closed": "#22c55e", "overdue": "#ef4444",
    }
    capa_df = pd.DataFrame([
        {"Status": capa_labels.get(k, k), "Count": v, "colour": capa_colours.get(k, "#94a3b8")}
        for k, v in capa_counts.items() if v > 0
    ])
    if capa_df.empty:
        empty_state("No CAPA records yet.", "🔧")
    else:
        fig2 = go.Figure(go.Pie(
            labels=capa_df["Status"],
            values=capa_df["Count"],
            marker_colors=capa_df["colour"],
            hole=0.55,
            textinfo="label+value",
            textfont={"size": 12},
        ))
        fig2.update_layout(
            height=250,
            margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            font={"family": "Inter, sans-serif"},
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── Refresh button ────────────────────────────────────────────────────────────
st.divider()
if st.button("🔄 Refresh Score", key="refresh_score"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Score calculated as of {report.generated_at.strftime('%d %b %Y')}. Auto-refreshes every 2 minutes.")
