"""Score card — 2026 redesign. Plotly 6.x compatible."""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from components.theme import is_dark
from app.services.audit_score_service import AuditReadinessReport, PillarScore


def _score_colour(score: float) -> str:
    if score >= 90: return "#10b981"
    if score >= 70: return "#f59e0b"
    return "#ef4444"


def render_score_gauge(report: AuditReadinessReport) -> None:
    dark   = is_dark()
    score  = report.overall_score
    colour = _score_colour(score)
    # Match tick colour to background so ticks are invisible
    invis  = "#0d1829" if dark else "#f0f4f8"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            "suffix": "%",
            "font": {"size": 52, "color": colour, "family": "Inter, sans-serif"},
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 0,
                "tickcolor": invis,
            },
            "bar":  {"color": colour, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  50],  "color": "rgba(239,68,68,0.08)"},
                {"range": [50, 70],  "color": "rgba(245,158,11,0.08)"},
                {"range": [70, 90],  "color": "rgba(245,158,11,0.06)"},
                {"range": [90, 100], "color": "rgba(16,185,129,0.08)"},
            ],
            "threshold": {
                "line": {"color": colour, "width": 2},
                "thickness": 0.85,
                "value": score,
            },
        },
        title={
            "text": (
                f"<b>Audit Readiness</b><br>"
                f"<span style='font-size:0.85em;color:{colour};'>{report.status_label}</span>"
            ),
            "font": {"size": 14, "family": "Inter, sans-serif"},
        },
    ))

    fig.update_layout(
        height=260,
        margin=dict(t=60, b=0, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_pillar_cards(report: AuditReadinessReport) -> None:
    cols = st.columns(4)
    icons = {"Documents": "📁", "Calibrations": "⚙️", "Training": "🎓", "CAPA": "🔧"}
    for col, pillar in zip(cols, report.pillars):
        with col:
            _pillar_card(pillar, icons.get(pillar.name, "📋"))


def _pillar_card(pillar: PillarScore, icon: str) -> None:
    dark   = is_dark()
    colour = _score_colour(pillar.score)
    bg     = "#0d1829" if dark else "#ffffff"
    bd     = "#1e3a5f" if dark else "#e2e8f0"
    t2     = "#8ba3c0" if dark else "#64748b"
    bar_pct = f"{pillar.score:.0f}%"

    issues_html = ""
    if pillar.issues:
        iss = pillar.issues[0][:55] + ("..." if len(pillar.issues[0]) > 55 else "")
        issues_html = (
            f"<div style='font-size:0.7rem;color:{t2};margin-top:6px;"
            f"line-height:1.4;'>• {iss}</div>"
        )

    st.markdown(f"""
    <div style="background:{bg};border:1px solid {bd};border-top:3px solid {colour};
                border-radius:14px;padding:1.1rem;height:100%;
                box-shadow:0 1px 4px rgba(0,0,0,{'0.2' if dark else '0.04'});">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
            <div>
                <div style="font-size:0.7rem;font-weight:600;color:{t2};
                            text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">
                    {icon} {pillar.name}
                </div>
                <div style="font-size:1.9rem;font-weight:700;color:{colour};line-height:1;">
                    {pillar.score:.0f}%
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:0.72rem;color:{t2};">{pillar.compliant}/{pillar.total}</div>
                <div style="font-size:0.65rem;color:{t2};opacity:0.7;">compliant</div>
            </div>
        </div>
        <div style="height:4px;background:{'rgba(255,255,255,0.08)' if dark else '#f1f5f9'};
                    border-radius:100px;overflow:hidden;">
            <div style="width:{bar_pct};height:100%;background:{colour};border-radius:100px;"></div>
        </div>
        {issues_html}
    </div>
    """, unsafe_allow_html=True)
