"""
dashboards/q8_sustainable_strategy/charts.py -- visuals for Question 8
("What optimal strategy may be opted to make energy development sustainable?").

Simple chart types, one per analytical job:
V1  Pillar scorecard (grouped bars)   -- now vs 10 yrs ago, per pillar
V2  Index trajectory (multi-line)     -- pillar scores + composite over time
V3  Value density ranking (h-bars)    -- impact-per-$ order of the strategy library
V4  Cost-impact bubble map (scatter)  -- strategy space, in/out of package
V5  Pathway projection (bar+line)     -- history continued by BAU/announced/optimal
V6  Pillar gain vs BAU (diverging)    -- score points added per pillar at horizon
V7  Component diagnostics (h-bars)    -- the nine underlying 0-100 scores

Presentation-only ("dumb"): core/sustainability_engine.py pre-computes every
value; these functions only draw.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import PILLAR_COLOURS

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8D0DA"
_PAPER = "#1A1D24"
_PLOT = "#14171E"


def _dark_theme(fig, height: int = 380, y_title: Optional[str] = None,
                x_title: Optional[str] = None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        margin=dict(l=62, r=46, t=45, b=72),
        height=height,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
        legend=dict(orientation="h", y=-0.28, x=0.5, xanchor="center",
                    font=dict(size=10.5, color=_TEXT)),
    )
    fig.update_xaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=x_title, font=dict(size=11.5, color=_TEXT)) if x_title else None,
                     tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=y_title, font=dict(size=11.5, color=_TEXT)) if y_title else None,
                     tickfont=dict(size=11, color=_TICK))
    return fig


def _empty(fig, msg="No data available", **kw):
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, **kw)


# ═══════════════ V1 -- pillar scorecard (grouped bars) ══════════════════════

def visual1_pillar_scorecard(scorecard: pd.DataFrame) -> go.Figure:
    """Four pillars, two bars each: latest score vs the score 10 years earlier."""
    fig = go.Figure()
    if scorecard is None or scorecard.empty:
        return _empty(fig, "Indicator history unavailable", height=400,
                      y_title="Pillar Score (0-100)", x_title="Sustainability Pillar")
    fig.add_trace(go.Bar(
        x=scorecard["pillar"], y=scorecard["then"], name=scorecard["then_label"].iat[0],
        marker=dict(color="rgba(148,163,184,0.55)", line=dict(width=0)),
        hovertemplate="%{x}: %{y:.1f}<extra>%{text}</extra>",
        text=[scorecard["then_label"].iat[0]] * len(scorecard),
    ))
    fig.add_trace(go.Bar(
        x=scorecard["pillar"], y=scorecard["now"], name=scorecard["now_label"].iat[0],
        marker=dict(color=[PILLAR_COLOURS.get(p, "#00A6FB") for p in scorecard["pillar_key"]],
                    line=dict(width=0)),
        text=[f"{v:.0f}" for v in scorecard["now"]], textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=scorecard["delta"],
        hovertemplate="%{x}: %{y:.1f}<br>Δ vs then: %{customdata:+.1f}<extra></extra>",
    ))
    fig.update_layout(barmode="group")
    _dark_theme(fig, height=400, y_title="Pillar Score (0-100)",
                x_title="Sustainability Pillar")
    fig.update_yaxes(range=[0, 105])
    return fig


# ═══════════════ V2 -- index trajectory (multi-line) ════════════════════════

def visual2_index_trajectory(traj: pd.DataFrame) -> go.Figure:
    """Pillar scores across the record with the weighted composite drawn bold."""
    fig = go.Figure()
    if traj is None or traj.empty:
        return _empty(fig, "Indicator history unavailable", height=400,
                      y_title="Score (0-100)", x_title="Year")
    for col, lab, colr in (("security", "Energy Security", PILLAR_COLOURS["security"]),
                           ("economy", "Economic Viability", PILLAR_COLOURS["economy"]),
                           ("environment", "Environmental", PILLAR_COLOURS["environment"]),
                           ("access", "Energy Access", PILLAR_COLOURS["access"])):
        if col in traj.columns:
            fig.add_trace(go.Scatter(
                x=traj["calendar_year"], y=traj[col], mode="lines", name=lab,
                line=dict(color=colr, width=1.8), opacity=0.8,
                hovertemplate=f"{lab}: %{{y:.1f}}<extra></extra>",
            ))
    if "composite" in traj.columns:
        fig.add_trace(go.Scatter(
            x=traj["calendar_year"], y=traj["composite"], mode="lines",
            name="Weighted Composite",
            line=dict(color="#E2E8F0", width=3.2),
            hovertemplate="Composite: %{y:.1f}<extra></extra>",
        ))
    _dark_theme(fig, height=400, y_title="Score (0-100)", x_title="Year")
    fig.update_yaxes(range=[0, 105])
    return fig


# ═══════════ V3 -- strategy value density (horizontal ranking bars) ═════════

def visual3_value_density(ranked: pd.DataFrame) -> go.Figure:
    """Feasibility-discounted weighted impact per $bn/yr, best strategy on top."""
    fig = go.Figure()
    if ranked is None or ranked.empty:
        return _empty(fig, "Strategy library empty", height=430,
                      x_title="Weighted Impact per $bn/yr (feasibility-discounted)",
                      y_title="Strategy")
    d = ranked.iloc[::-1]
    fig.add_trace(go.Bar(
        y=d["short"], x=d["density"], orientation="h",
        marker=dict(color=d["feasibility"], colorscale=[[0, "#EF4444"], [1, "#10B981"]],
                    line=dict(width=0)),
        text=[f"{v:.1f}" for v in d["density"]], textposition="outside",
        textfont=dict(size=10, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=np.stack([d["cost_bn_per_year"], d["feasibility"],
                             d["weighted_impact"]], axis=-1),
        hovertemplate="<b>%{y}</b><br>Density: %{x:.1f} pts/$bn<br>"
                      "Cost: $%{customdata[0]:.1f} bn/yr · Feasibility: %{customdata[1]}%"
                      "<br>Weighted impact: %{customdata[2]:.1f} pts<extra></extra>",
        showlegend=False,
    ))
    _dark_theme(fig, height=430,
                x_title="Weighted Impact per $bn/yr (feasibility-discounted)",
                y_title="Strategy (bar colour = feasibility)")
    fig.update_yaxes(tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═══════════════ V4 -- cost vs impact bubble map (scatter) ══════════════════

def visual4_cost_impact_bubbles(ranked: pd.DataFrame,
                                 chosen_ids: set) -> go.Figure:
    """The strategy space: x = annual cost, y = weighted impact, bubble size =
    feasibility; selected package members are filled, the rest hollow."""
    fig = go.Figure()
    if ranked is None or ranked.empty:
        return _empty(fig, "Strategy library empty", height=430,
                      y_title="Weighted Impact (score pts)",
                      x_title="Cost (USD bn / year)")
    in_pk = ranked[ranked["id"].isin(chosen_ids)]
    out_pk = ranked[~ranked["id"].isin(chosen_ids)]
    for d, name, fill, sym in ((in_pk, "In optimal package", "#10B981", "circle"),
                               (out_pk, "Not selected", "rgba(0,0,0,0)", "circle-open")):
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["cost_bn_per_year"], y=d["weighted_impact"], mode="markers",
            name=name,
            marker=dict(symbol=sym, size=d["feasibility"] / 3.2 + 8,
                        color=fill if fill != "rgba(0,0,0,0)" else "#94A3B8",
                        opacity=0.85 if fill != "rgba(0,0,0,0)" else 0.5,
                        line=dict(color="#E2E8F0", width=1.2)),
            customdata=np.stack([d["short"], d["feasibility"], d["density"]], axis=-1),
            hovertemplate="<b>%{customdata[0]}</b><br>Cost: $%{x:.1f} bn/yr<br>"
                          "Impact: %{y:.1f} pts · Feasibility: %{customdata[1]}%<br>"
                          "Density: %{customdata[2]:.1f} pts/$bn<extra></extra>",
        ))
    _dark_theme(fig, height=430, y_title="Weighted Impact (score pts)",
                x_title="Cost (USD bn / year)  ·  bubble = feasibility")
    return fig


# ═══════════ V5 -- pathway projection (history bars + scenario lines) ════════

def visual5_pathway_chart(paths: pd.DataFrame, base_year: int) -> go.Figure:
    """Composite index: reported history as bars, continued by BAU / announced
    / optimal scenario lines to the horizon."""
    fig = go.Figure()
    if paths is None or paths.empty:
        return _empty(fig, "Pathway projection unavailable", height=420,
                      y_title="Composite Sustainability Index (0-100)",
                      x_title="Year")
    hist = paths[paths["is_actual"]]
    proj = paths[~paths["is_actual"]]
    fig.add_trace(go.Bar(
        x=hist["calendar_year"], y=hist["composite_bau"], name="Reported",
        marker=dict(color="rgba(20,184,166,0.5)", line=dict(color="#14B8A6", width=1)),
        hovertemplate="%{x}: %{y:.1f}<extra>Reported</extra>",
    ))
    styles = (("composite_bau", "BAU (trend continues)", "#EF4444", "solid"),
              ("composite_announced", "Announced Pledges", "#F59E0B", "dash"),
              ("composite_optimal", "Optimal Package", "#10B981", "solid"))
    for col, lab, colr, dash in styles:
        x = pd.concat([hist["calendar_year"], proj["calendar_year"]]) if not hist.empty \
            else proj["calendar_year"]
        y = pd.concat([hist[col], proj[col]]) if not hist.empty else proj[col]
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=lab,
            line=dict(color=colr, width=2.6, dash=dash), marker=dict(size=4),
            hovertemplate="%{x}: %{y:.1f}<extra>" + lab + "</extra>",
        ))
    if base_year:
        fig.add_vline(x=base_year + 0.5,
                      line=dict(color="rgba(255,255,255,0.30)", width=1.2, dash="dot"),
                      annotation_text="History ◀ | ▶ Pathways",
                      annotation_position="top",
                      annotation_font_size=9, annotation_font_color=_TICK)
    _dark_theme(fig, height=420,
                y_title="Composite Sustainability Index (0-100)", x_title="Year")
    fig.update_yaxes(range=[0, 105])
    return fig


# ═══════════════ V6 -- pillar gain vs BAU (diverging bars) ══════════════════

def visual6_pillar_gain(gain: pd.DataFrame, horizon: int) -> go.Figure:
    """Score points the optimal package adds (or costs) per pillar at horizon."""
    fig = go.Figure()
    if gain is None or gain.empty:
        return _empty(fig, "No pathway gain computed", height=420,
                      y_title="Gain vs BAU (score pts)", x_title="Pillar")
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in gain["gain"]]
    fig.add_trace(go.Bar(
        x=gain["pillar"], y=gain["gain"],
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+.1f}" for v in gain["gain"]], textposition="outside",
        textfont=dict(size=11, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=np.stack([gain["bau"], gain["optimal"]], axis=-1),
        hovertemplate="<b>%{x}</b><br>Gain: %{y:+.1f} pts<br>"
                      "BAU: %{customdata[0]:.1f} -> Optimal: %{customdata[1]:.1f}"
                      "<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))
    _dark_theme(fig, height=420, y_title=f"Gain vs BAU at {horizon} (score pts)",
                x_title="Sustainability Pillar")
    return fig


# ═══════════════ V7 -- component diagnostics (horizontal bars) ══════════════

def visual7_component_diagnostics(comp: pd.DataFrame) -> go.Figure:
    """All nine underlying 0-100 component scores, latest observation each;
    bars coloured by band (weak <40, middle 40-70, strong >70)."""
    fig = go.Figure()
    if comp is None or comp.empty:
        return _empty(fig, "No component scores available", height=460,
                      x_title="Component Score (0-100)", y_title="Component")
    d = comp.sort_values("score")
    def band(v):
        return "#EF4444" if v < 40 else ("#F59E0B" if v <= 70 else "#10B981")
    fig.add_trace(go.Bar(
        y=d["label"], x=d["score"], orientation="h",
        marker=dict(color=[band(v) for v in d["score"]], line=dict(width=0)),
        text=[f"{v:.0f}" for v in d["score"]], textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=np.stack([d["pillar"], d["year"]], axis=-1),
        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>Score: %{x:.1f}"
                      " · observed %{customdata[1]}"
                      "<extra></extra>",
        showlegend=False,
    ))
    for lvl, col in ((40, "rgba(239,68,68,0.6)"), (70, "rgba(16,185,129,0.6)")):
        fig.add_vline(x=lvl, line=dict(color=col, width=1.2, dash="dot"),
                      annotation_text="weak" if lvl == 40 else "strong",
                      annotation_position="top",
                      annotation_font_size=9, annotation_font_color=_TICK)
    _dark_theme(fig, height=460, x_title="Component Score (0-100, latest observation)",
                y_title="Component")
    fig.update_xaxes(range=[0, 112])
    fig.update_yaxes(tickfont=dict(size=10, color="#CBD5E1"))
    return fig
