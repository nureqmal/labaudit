"""Dashboard — 2026 redesign."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from components.auth_guard import require_auth
from components.sidebar import render_sidebar
from components.theme import inject_theme_css, is_dark
from components.score_card import render_score_gauge, render_pillar_cards
from components.ui_helpers import page_header, metric_card, metric_card_danger, section_header, empty_state
from components.status_badge import alert_dot
from app.database import db_session
from app.services.audit_score_service import AuditScoreService
from app.services.notification_service import NotificationService, AlertLevel

st.set_page_config(page_title="Dashboard — LabAudit", page_icon="📊", layout="wide")
user = require_auth()
inject_theme_css()
render_sidebar()

dark  = is_dark()
t1    = "#e8edf5" if dark else "#0f172a"
t2    = "#8ba3c0" if dark else "#64748b"
t3    = "#4d6a8a" if dark else "#94a3b8"
bg    = "#0d1829" if dark else "#ffffff"
bd    = "#1e3a5f" if dark else "#e2e8f0"
acc   = "#3b82f6" if dark else "#2563eb"
bg2   = "#111f35" if dark else "#f8fafc"

page_header("Dashboard", f"Welcome back, {user.full_name.split()[0]} 👋", "")
org_id = st.session_state["org_id"]

@st.cache_data(ttl=120, show_spinner="Calculating readiness score...")
def load_report(_org_id):
    with db_session() as db:
        return AuditScoreService(db).calculate(_org_id)

@st.cache_data(ttl=120, show_spinner=False)
def load_alerts(_org_id):
    with db_session() as db:
        return NotificationService(db).get_alerts(_org_id)

report = load_report(org_id)
alerts = load_alerts(org_id)
red_alerts = [a for a in alerts if a.level == AlertLevel.RED]

# ── Score + Alerts row ────────────────────────────────────────────────────────
col_gauge, col_alerts = st.columns([1.2, 1], gap="medium")

with col_gauge:
    with st.container(border=True):
        render_score_gauge(report)

with col_alerts:
    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
            <span style="font-size:0.95rem;font-weight:600;color:{t1};">🚨 Action Required</span>
            <span style="background:{'rgba(239,68,68,0.12)' if red_alerts else 'rgba(16,185,129,0.1)'};
                         color:{'#ef4444' if red_alerts else '#10b981'};font-size:0.72rem;font-weight:600;
                         padding:3px 10px;border-radius:100px;">{len(red_alerts)} critical</span>
        </div>
        """, unsafe_allow_html=True)

        if not red_alerts:
            st.markdown(f"""
            <div style="text-align:center;padding:2rem;color:#10b981;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">✅</div>
                <div style="font-size:0.875rem;font-weight:500;">No critical issues</div>
                <div style="font-size:0.78rem;color:{t3};margin-top:4px;">Your lab is in good shape</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for a in red_alerts[:6]:
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;gap:10px;padding:0.55rem 0;
                            border-bottom:1px solid {bd};">
                    <span style="width:6px;height:6px;background:#ef4444;border-radius:50%;
                                 flex-shrink:0;margin-top:5px;"></span>
                    <div>
                        <div style="font-size:0.78rem;font-weight:600;color:{t2};">{a.category}</div>
                        <div style="font-size:0.82rem;color:{t1};line-height:1.4;">{a.title}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if len(red_alerts) > 6:
                st.caption(f"+ {len(red_alerts)-6} more critical items")

# ── Pillars ───────────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
render_pillar_cards(report)

# ── KPI Metrics ───────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size:0.72rem;font-weight:600;color:{t3};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;'>Key Metrics</p>", unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: metric_card("Total Documents", report.total_documents, icon="📁", accent=acc)
with c2: metric_card_danger("Overdue Docs", report.overdue_documents, icon="📄")
with c3: metric_card("Expiring 30d", report.expiring_30d_documents, icon="⏰",
                      accent="#f59e0b" if report.expiring_30d_documents else "#10b981")
with c4: metric_card_danger("Overdue Cals", report.overdue_calibrations, icon="⚙️")
with c5: metric_card_danger("Overdue Training", report.overdue_training, icon="🎓")
with c6: metric_card_danger("Open CAPAs", report.open_capas, icon="🔧")

# ── Expiry warnings ───────────────────────────────────────────────────────────
st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
w1,w2,w3 = st.columns(3)
warn_data = [("Expiring within 7 days",  report.expiring_7d_documents,  "#ef4444","rgba(239,68,68,0.08)","rgba(239,68,68,0.15)"),
             ("Expiring within 14 days", report.expiring_14d_documents, "#f59e0b","rgba(245,158,11,0.08)","rgba(245,158,11,0.15)"),
             ("Expiring within 30 days", report.expiring_30d_documents, "#3b82f6","rgba(59,130,246,0.08)","rgba(59,130,246,0.15)")]
for col,(label,count,color,bgg,brd) in zip([w1,w2,w3], warn_data):
    if count == 0:
        bgg = "rgba(16,185,129,0.08)"; color = "#10b981"; brd = "rgba(16,185,129,0.15)"
    with col:
        st.markdown(f"""
        <div style="background:{bgg};border:1px solid {brd};border-radius:14px;padding:1.1rem;text-align:center;">
            <div style="font-size:2.2rem;font-weight:700;color:{color};line-height:1;letter-spacing:-0.02em;">{count}</div>
            <div style="font-size:0.75rem;font-weight:500;color:{color};opacity:0.8;margin-top:4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
ch1, ch2 = st.columns(2, gap="medium")

with ch1:
    with st.container(border=True):
        st.markdown(f"<p style='font-size:0.875rem;font-weight:600;color:{t1};margin-bottom:0.5rem;'>Compliance by Pillar</p>", unsafe_allow_html=True)
        colours = ["#10b981" if p.score>=90 else "#f59e0b" if p.score>=70 else "#ef4444" for p in report.pillars]
        fig = go.Figure(go.Bar(
            x=[p.name for p in report.pillars],
            y=[p.score for p in report.pillars],
            marker_color=colours,
            marker_line_width=0,
            text=[f"{p.score:.0f}%" for p in report.pillars],
            textposition="outside",
            textfont={"size": 11, "color": t1, "family": "Inter"},
        ))
        fig.add_hline(y=90, line_dash="dot", line_color="#10b981", line_width=1,
                      annotation_text="Target 90%", annotation_font_color="#10b981", annotation_font_size=10)
        fig.update_layout(
            height=220, margin=dict(t=25,b=0,l=0,r=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0,115], showgrid=True, gridcolor="rgba(255,255,255,0.05)" if dark else "rgba(0,0,0,0.04)", showticklabels=False),
            xaxis=dict(showgrid=False, tickfont=dict(color=t2, size=11, family="Inter")),
            showlegend=False, font={"family":"Inter"},
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

with ch2:
    with st.container(border=True):
        st.markdown(f"<p style='font-size:0.875rem;font-weight:600;color:{t1};margin-bottom:0.5rem;'>CAPA Status</p>", unsafe_allow_html=True)

        @st.cache_data(ttl=120, show_spinner=False)
        def load_capa_counts(_org_id):
            with db_session() as db:
                from app.repositories.capa_repository import CapaRepository
                return CapaRepository(db).count_by_status(_org_id)

        capa_counts = load_capa_counts(org_id)
        capa_map = {"open":"Open","in_progress":"In Progress","pending_verification":"Pending","closed":"Closed","overdue":"Overdue"}
        capa_colors = {"open":"#3b82f6","in_progress":"#f59e0b","pending_verification":"#8b5cf6","closed":"#10b981","overdue":"#ef4444"}
        labels = [capa_map.get(k,k) for k,v in capa_counts.items() if v>0]
        values = [v for v in capa_counts.values() if v>0]
        colors = [capa_colors.get(k,"#94a3b8") for k,v in capa_counts.items() if v>0]
        if values:
            fig2 = go.Figure(go.Pie(
                labels=labels, values=values, marker_colors=colors,
                hole=0.65, textinfo="label+value", textfont={"size":11,"family":"Inter"},
                hoverinfo="label+percent",
            ))
            fig2.update_layout(
                height=220, margin=dict(t=10,b=0,l=0,r=0),
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                font={"family":"Inter"},
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        else:
            empty_state("No CAPA records yet.", "🔧")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
col_ref, col_btn = st.columns([4,1])
with col_ref:
    st.caption(f"Score calculated at {report.generated_at.strftime('%d %b %Y')} · Auto-refreshes every 2 minutes")
with col_btn:
    if st.button("🔄 Refresh", key="refresh_score"):
        st.cache_data.clear(); st.rerun()
