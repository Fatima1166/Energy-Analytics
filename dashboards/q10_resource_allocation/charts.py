"""
dashboards/q10_resource_allocation/charts.py -- visuals for Optimal Resource
Allocation for Sustainable Development (question 10).

Five plain charts, each answering one part of the question:
V1  How the power is split          -- grouped bars, the base-year mix vs the plan
V2  What the priorities buy         -- cost and CO2 across the whole sweep
V3  What moves, source by source    -- diverging bars (+/- vs the base-year mix)
V4  Is the plan more sustainable?   -- butterfly bars, 0-100 on six things
V5  The cost-CO₂ trade-off shape    -- scatter of every plan, one dot per priority

Presentation-only ("dumb"): core/resource_allocation.py pre-computes every
number; these functions only draw.  Every visual sits in a half-width row, so
side margins are sized to the longest label and legends stay small.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.cost_forecast import COST_TECHS, TECH_COLORS

from .config import PLAN_WORD, bau_word, tech_tick, tech_word

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8D0DA"
_PAPER = "#1A1D24"
_PLOT = "#14171E"

_MUTED_BAR = "rgba(148, 163, 184, 0.55)"
_GREEN = "#10B981"
_RED = "#EF4444"


def _dark_theme(fig, height: int = 390, y_title: Optional[str] = None,
                x_title: Optional[str] = None, left: int = 62, right: int = 46):
    """Half-width rows: tight sides, small horizontal legend under the plot."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        margin=dict(l=left, r=right, t=45, b=72),
        height=height,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
        legend=dict(orientation="h", y=-0.26, x=0.5, xanchor="center",
                    font=dict(size=10, color=_TEXT)),
    )
    fig.update_xaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=x_title, font=dict(size=11, color=_TEXT)) if x_title else None,
                     tickfont=dict(size=10.5, color=_TICK))
    fig.update_yaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=y_title, font=dict(size=11, color=_TEXT)) if y_title else None,
                     tickfont=dict(size=11, color=_TICK))
    return fig


def _empty(fig, msg="Nothing to show", **kw):
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, **kw)


# ═══════════════ V1 -- the split: base-year mix vs plan (grouped bars) ════════════

def visual1_allocation_bars(
    allocation: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
    base_year: int = 2024,
) -> go.Figure:
    """Two bars per resource: what the base-year mix would make, what the plan
    makes.  The base-year label travels with the year the mix came from."""
    fig = go.Figure()
    if allocation is None or allocation.empty:
        return _empty(fig, "No allocation to show", height=390,
                      y_title=f"Power a year ({unit_elec})", x_title="Resource")

    order = [t for t in COST_TECHS if t in set(allocation["technology"])]
    alloc = allocation.set_index("technology").loc[order]
    labels = [tech_word(t) for t in order]
    bau = alloc["bau_gwh"] * factor_elec
    opt = alloc["optimal_gwh"] * factor_elec
    ceil = alloc["ceiling_gwh"] * factor_elec

    fig.add_trace(go.Bar(
        x=labels, y=bau.tolist(), name=bau_word(base_year),
        marker=dict(color=_MUTED_BAR, line=dict(color="#94A3B8", width=1)),
        customdata=ceil.tolist(),
        hovertemplate="%{x} on the " + str(int(base_year)) + " mix: %{y:,.0f} " + unit_elec +
                      "<br>Most it could ever make: %{customdata:,.0f} " + unit_elec +
                      "<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels, y=opt.tolist(), name=PLAN_WORD,
        marker=dict(color=[TECH_COLORS[t] for t in order],
                    line=dict(color="rgba(255,255,255,0.25)", width=1)),
        customdata=alloc["clamped"].map(
            lambda c: "This is at its limit" if c else "").tolist(),
        hovertemplate="%{x} in the plan: %{y:,.0f} " + unit_elec +
                      "<br>%{customdata}<extra></extra>",
    ))

    _dark_theme(fig, height=390, y_title=f"Power a year ({unit_elec})",
                x_title="Resource", right=26)
    fig.update_xaxes(tickmode="array", tickvals=labels,
                     ticktext=[tech_tick(t) for t in order])
    fig.update_layout(barmode="group")
    return fig


# ═══════════════ V2 -- what the priorities buy (cost vs CO2) ═════════════════

def visual2_tradeoff_lines(
    pareto: pd.DataFrame,
    selected_theta: Optional[float] = None,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
    unit_em: str = "t",
    factor_em: float = 1.0,
) -> go.Figure:
    """The same plan run from cheapest-first to cleanest-first, with the money
    on the left axis and the CO2 on the right."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if pareto is None or pareto.empty:
        base = go.Figure()
        return _empty(base, "No sweep to show", height=390,
                      y_title=f"Cost ({unit_cost})", x_title="What the plan favours")

    d = pareto.sort_values("theta")
    fig.add_trace(go.Scatter(
        x=d["theta"], y=d["cost_usd"] * factor_cost, name=f"Cost ({unit_cost})",
        mode="lines", line=dict(color="#F59E0B", width=2.6),
        hovertemplate="priority %{x:.2f} of 1<br>Cost: %{y:,.2f} " + unit_cost +
                      "<extra>Cost</extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=d["theta"], y=d["co2_t"] * factor_em, name=f"CO₂ ({unit_em})",
        mode="lines", line=dict(color="#14B8A6", width=2.6, dash="dash"),
        hovertemplate="priority %{x:.2f} of 1<br>CO₂: %{y:,.0f} " + unit_em +
                      "<extra>CO₂</extra>",
    ), secondary_y=True)

    if selected_theta is not None:
        fig.add_vline(x=float(selected_theta), line=dict(color="#E2E8F0", width=1.4, dash="dot"),
                      annotation_text="your pick", annotation_position="top",
                      annotation_font_size=9.5, annotation_font_color="#CBD5E1")

    _dark_theme(fig, height=390,
                x_title="What the plan favours (0 = cheapest, 1 = cleanest)")
    # Short ticks: the emission axis is read in tonnes by default, and a seven
    # or eight digit tick label would not fit the right side of a half-width
    # chart.  "~s" keeps "24M" next to a title that says which unit is meant.
    fig.update_yaxes(title_text=f"Cost ({unit_cost})", secondary_y=False,
                     tickformat="~s", gridcolor=_AXIS,
                     tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(title_text=f"CO₂ ({unit_em})", secondary_y=True,
                     tickformat="~s", showgrid=False,
                     tickfont=dict(size=11, color=_TICK))
    return fig


# ═══════════════ V3 -- what moves (diverging bars) ═══════════════════════════

def visual3_shift_bars(
    allocation: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
    base_year: int = 2024,
) -> go.Figure:
    """Plan minus the base-year mix per resource: green grows one, red pulls one
    back."""
    fig = go.Figure()
    if allocation is None or allocation.empty:
        return _empty(fig, "No allocation to show", height=400,
                      x_title=f"Change vs the {int(base_year)} mix ({unit_elec})",
                      y_title="Resource", left=104, right=26)

    d = allocation.assign(
        name=allocation["technology"].map(tech_word),
        delta=allocation["delta_gwh"] * factor_elec,
    ).sort_values("delta")
    colors = [_GREEN if v >= 0 else _RED for v in d["delta"]]

    fig.add_trace(go.Bar(
        y=d["name"], x=d["delta"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+,.0f}" for v in d["delta"]],
        textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=(d["bau_gwh"] * factor_elec, d["optimal_gwh"] * factor_elec),
        hovertemplate="<b>%{y}</b><br>" + str(int(base_year)) + " mix: %{customdata[0]:,.0f} · "
                      "Plan: %{customdata[1]:,.0f} " + unit_elec +
                      "<br>Change: %{x:+,.0f} " + unit_elec + "<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))

    _dark_theme(fig, height=400,
                x_title=f"Change vs the {int(base_year)} mix ({unit_elec})",
                y_title="Resource", left=104, right=26)
    return fig


# ═══════════════ V4 -- is the plan better? (butterfly bars) ══════════════════

def visual4_sustainability_scorecard(radar: pd.DataFrame,
                                     base_year: int = 2024) -> go.Figure:
    """Six plain things, scored 0-100: the old mix reaches left, the plan right."""
    fig = go.Figure()
    if radar is None or radar.empty:
        return _empty(fig, "No scorecard to show", height=420,
                      x_title="Score (0 to 100, old mix ◀ | ▶ plan)",
                      y_title="What is judged", left=96, right=30)

    dims = radar["dimension"].tolist()
    bau = radar["bau"].tolist()
    opt = radar["optimal"].tolist()

    fig.add_trace(go.Bar(
        y=dims, x=[-v for v in bau], orientation="h", name=bau_word(base_year),
        marker=dict(color="rgba(148, 163, 184, 0.70)", line=dict(width=0)),
        text=[f"{v:.0f}" for v in bau], textposition="outside",
        textfont=dict(size=10, color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>" + str(int(base_year)) +
                      " mix: %{customdata:.0f} of 100<extra></extra>",
        customdata=bau,
    ))
    fig.add_trace(go.Bar(
        y=dims, x=opt, orientation="h", name=PLAN_WORD,
        marker=dict(color=_GREEN, line=dict(width=0)),
        text=[f"{v:.0f}" for v in opt], textposition="outside",
        textfont=dict(size=10, color=_GREEN),
        hovertemplate="<b>%{y}</b><br>Plan: %{customdata:.0f} of 100<extra></extra>",
        customdata=opt,
    ))

    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))

    _dark_theme(fig, height=420,
                x_title="Score (0 to 100, old mix ◀ | ▶ plan)",
                y_title="What is judged", left=96, right=30)
    fig.update_layout(barmode="relative")
    return fig


# ═══════════════ V5 -- the cost-CO₂ trade-off shape (scatter) ════════════════

def visual5_tradeoff_scatter(
    pareto: pd.DataFrame,
    selected_theta: Optional[float] = None,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
    unit_em: str = "t",
    factor_em: float = 1.0,
) -> go.Figure:
    """Every priority's plan as one dot on a cost × CO₂ plane, cheapest-first
    to cleanest-first.  The line joins the frontier; the reader's pick is
    ringed.  V2 shows the same sweep as two independent lines against
    priority; this shows what a plan actually costs against what it pollutes,
    so the shape of the trade-off (knee, flat stretch, sharp bend) is visible.
    """
    fig = go.Figure()
    if pareto is None or pareto.empty:
        return _empty(fig, "No sweep to plot", height=390,
                      x_title=f"Yearly CO₂ ({unit_em})",
                      y_title=f"Yearly cost ({unit_cost})")
    d = pareto.sort_values("theta")
    x = d["co2_t"] * factor_em
    y = d["cost_usd"] * factor_cost
    theta = d["theta"].tolist()

    # the frontier itself, thin and muted, so the dots read on top
    fig.add_trace(go.Scatter(
        x=x.tolist(), y=y.tolist(), mode="lines",
        line=dict(color="rgba(200,205,214,0.35)", width=1.4),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x.tolist(), y=y.tolist(), mode="markers",
        marker=dict(
            size=10, color=theta, colorscale=[[0.0, "#F59E0B"],
                                               [1.0, "#14B8A6"]],
            showscale=True, colorbar=dict(
                title=dict(text="Priority<br>cheap→clean", font=dict(size=9.5, color=_TEXT)),
                tickfont=dict(size=9.5, color=_TICK), thickness=10, len=0.7),
            line=dict(color="rgba(255,255,255,0.35)", width=1)),
        customdata=theta,
        hovertemplate=("Priority %{customdata:.2f} of 1<br>"
                       "%{x:,.2f} " + unit_cost + " a year<br>"
                       "%{y:,.0f} " + unit_em + " CO₂ a year"
                       "<extra></extra>"),
        showlegend=False,
    ))
    if selected_theta is not None:
        sub = d.iloc[(d["theta"] - float(selected_theta)).abs().argsort()[:1]]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=[float(sub["co2_t"].iloc[0]) * factor_em],
                y=[float(sub["cost_usd"].iloc[0]) * factor_cost],
                mode="markers", marker=dict(size=18, color="rgba(0,0,0,0)",
                                            line=dict(color="#E2E8F0", width=2)),
                name="your pick", hoverinfo="skip",
            ))

    _dark_theme(fig, height=390,
                x_title=f"Yearly CO₂ ({unit_em})  —  cleaner plans sit left",
                y_title=f"Yearly cost ({unit_cost})  —  cheaper plans sit low",
                left=68, right=30)
    return fig
