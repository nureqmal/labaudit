"""
Score card component — renders the big Audit Readiness Score gauge
and the four pillar breakdown cards.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go

from app.services.audit_score_service import AuditReadinessReport, PillarScore


def render_score_gauge(report: AuditReadinessReport) -> None:
    """Big gauge chart for overall score."""
    score = report.overall_score
    colour = _score_colour(score)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "%", "font": {"size": 48, "color": colour}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#94a3b8",
                "tickfont": {"size": 12},
            },
            "bar": {"color": colour, "thickness": 0.28},
            "bgcolor": "#f1f5f9",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  50],  "color": "#fee2e2"},
                {"range": [50, 70],  "color": "#ffedd5"},
                {"range": [70, 90],  "color": "#fef9c3"},
                {"range": [90, 100], "color": "#dcfce7"},
            ],
            "threshold": {
                "line": {"color": colour, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
        title={
            "text": (
                f"<b>Audit Readiness Score</b><br>"
                f"<span style='font-size:0.9em;color:{colour}'>{report.status_label}</span>"
            ),
            "font": {"size": 15},
        },
    ))

    fig.update_layout(
        height=280,
        margin=dict(t=60, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Status caption
    caption_map = {
        "green":  "✅ Your lab is audit-ready.",
        "yellow": "⚠️ Minor gaps detected — review action items.",
        "red":    "🚨 Critical gaps — immediate action required.",
    }
    caption_colour = {"green": "#16a34a", "yellow": "#ca8a04", "red": "#dc2626"}
    c = report.status_colour
    st.markdown(
        f"<div style='text-align:center;color:{caption_colour[c]};"
        f"font-weight:600;font-size:0.95rem;margin-top:-0.5rem;'>"
        f"{caption_map[c]}</div>",
        unsafe_allow_html=True,
    )


def render_pillar_cards(report: AuditReadinessReport) -> None:
    """Four metric cards — one per compliance pillar."""
    cols = st.columns(4)
    for col, pillar in zip(cols, report.pillars):
        with col:
            _pillar_card(pillar)


def _pillar_card(pillar: PillarScore) -> None:
    colour = _score_colour(pillar.score)
    bg_map  = {"#16a34a": "#f0fdf4", "#ca8a04": "#fefce8", "#dc2626": "#fef2f2"}
    brd_map = {"#16a34a": "#bbf7d0", "#ca8a04": "#fde68a", "#dc2626": "#fecaca"}
    bg  = bg_map.get(colour, "#f8fafc")
    brd = brd_map.get(colour, "#e2e8f0")

    icon_map = {
        "Documents":    "📁",
        "Calibrations": "⚙️",
        "Training":     "🎓",
        "CAPA":         "🔧",
    }
    icon = icon_map.get(pillar.name, "📋")

    issues_html = ""
    if pillar.issues:
        issues_html = "".join(
            f"<div style='font-size:0.72rem;color:#64748b;margin-top:4px;'>"
            f"• {issue}</div>"
            for issue in pillar.issues[:2]  # max 2 shown
        )

    st.markdown(
        f"""
        <div style="background:{bg};border:1px solid {brd};border-radius:12px;
                    padding:1rem;height:100%;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <div style="font-size:0.78rem;color:#64748b;font-weight:500;">
                        {icon} {pillar.name}
                    </div>
                    <div style="font-size:1.8rem;font-weight:700;color:{colour};
                                line-height:1.1;margin-top:2px;">
                        {pillar.score:.0f}%
                    </div>
                </div>
                <div style="text-align:right;font-size:0.75rem;color:#94a3b8;">
                    <div>{pillar.compliant}/{pillar.total}</div>
                    <div>compliant</div>
                </div>
            </div>
            <div style="margin-top:6px;height:4px;background:#e2e8f0;border-radius:2px;">
                <div style="width:{pillar.score}%;height:100%;background:{colour};
                            border-radius:2px;transition:width 0.5s;"></div>
            </div>
            {issues_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_colour(score: float) -> str:
    if score >= 90:
        return "#16a34a"
    if score >= 70:
        return "#ca8a04"
    return "#dc2626"
