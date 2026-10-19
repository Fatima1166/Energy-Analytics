"""
dashboards/q10_resource_allocation/charts.py -- visuals for Optimal Resource
Allocation for Sustainable Development (question 10).

Simple chart types in the same visual language as the rest of the platform
deck (no polar roses, radars, gauges or Sankeys):
V1  BAU vs optimal allocation        -- grouped vertical bars per technology
V2  Cost-carbon trade-off sweep      -- dual-axis line chart
V3  Reallocation shift               -- diverging horizontal bars (+/- vs BAU)
V4  Optimal energy by sector         -- stacked bars of resource groups
V5  Sustainability scorecard         -- butterfly bars, BAU vs optimal
V6  Allocation concentration         -- cumulative-share Pareto (80/20) bars + line

Presentation-only ("dumb"): the core/resource_allocation.py engine pre-computes
every value; these functions only draw.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.cost_forecast import COST_TECHS, TECH_COLORS

from .config import GROUP_COLORS

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


# ═══════════════ V1 -- BAU vs optimal allocation (grouped bars) ═════════════

def visual1_allocation_bars(
    allocation: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Vertical grouped bars: BAU (grey) vs optimal (technology-coloured)
    generation per resource at the planning horizon."""
    fig = go.Figure()
    if allocation is None or allocation.empty:
        return _empty(fig, "No allocation data", height=390,
                      y_title=f"Generation ({unit_elec})", x_title="Technology")

    order = [t for t in COST_TECHS if t in set(allocation["technology"])]
    alloc = allocation.set_index("technology").loc[order]
    bau = alloc["bau_gwh"] * factor_elec
    opt = alloc["optimal_gwh"] * factor_elec
    ceil = alloc["ceiling_gwh"] * factor_elec

    fig.add_trace(go.Bar(
        x=order, y=bau.tolist(), name="BAU (2024 mix)",
        marker=dict(color="rgba(148, 163, 184, 0.55)",
                    line=dict(color="#94A3B8", width=1)),
        customdata=ceil.tolist(),
        hovertemplate="%{x} BAU: %{y:,.0f} " + unit_elec +
                      "<br>Resource ceiling: %{customdata:,.0f} " + unit_elec +
                      "<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=order, y=opt.tolist(), name="Optimal plan",
        marker=dict(color=[TECH_COLORS[t] for t in order],
                    line=dict(color="rgba(255,255,255,0.25)", width=1)),
        customdata=alloc["clamped"].map(lambda c: "clamped at ceiling" if c else "").tolist(),
        hovertemplate="%{x} optimal: %{y:,.0f} " + unit_elec +
                      "<br>%{customdata}<extra></extra>",
    ))

    _dark_theme(fig, height=390, y_title=f"Generation ({unit_elec})",
                x_title="Technology")
    fig.update_layout(barmode="group")
    return fig


# ═══════════════ V2 -- cost-carbon trade-off sweep (lines) ══════════════════

def visual2_tradeoff_lines(
    pareto: pd.DataFrame,
    selected_theta: Optional[float] = None,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
    unit_em: str = "Mt",
    factor_em: float = 1.0,
) -> go.Figure:
    """Dual-axis lines over the optimiser's weight sweep: annual cost (amber)
    and annual CO2 (teal) as the objective tilts from pure cost to pure carbon."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if pareto is None or pareto.empty:
        base = go.Figure()
        return _empty(base, "No trade-off sweep data", height=390,
                      y_title=f"Cost ({unit_cost})", x_title="Objective weight")

    d = pareto.sort_values("theta")
    fig.add_trace(go.Scatter(
        x=d["theta"], y=d["cost_bn"] * factor_cost, name=f"Cost ({unit_cost})",
        mode="lines", line=dict(color="#F59E0B", width=2.6),
        hovertemplate="θ=%{x:.2f}<br>Cost: %{y:,.2f} " + unit_cost +
                      "<extra>Cost</extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=d["theta"], y=d["co2_mt"] * factor_em, name=f"CO₂ ({unit_em})",
        mode="lines", line=dict(color="#14B8A6", width=2.6, dash="dash"),
        hovertemplate="θ=%{x:.2f}<br>CO₂: %{y:,.1f} " + unit_em +
                      "<extra>CO₂</extra>",
    ), secondary_y=True)

    if selected_theta is not None:
        fig.add_vline(x=float(selected_theta), line=dict(color="#E2E8F0", width=1.4, dash="dot"),
                      annotation_text="selected plan", annotation_position="top",
                      annotation_font_size=9.5, annotation_font_color="#CBD5E1")

    _dark_theme(fig, height=390, x_title="Objective weight θ (0 = least cost → 1 = low carbon)")
    fig.update_yaxes(title_text=f"Cost ({unit_cost})", secondary_y=False,
                     gridcolor=_AXIS, tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(title_text=f"CO₂ ({unit_em})", secondary_y=True,
                     showgrid=False, tickfont=dict(size=11, color=_TICK))
    return fig


# ═══════════════ V3 -- reallocation shift (diverging bars) ═══════════════════

def visual3_shift_bars(
    allocation: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Diverging horizontal bars: optimal minus BAU per technology. Emerald
    bars scale a resource up, red bars claw the resource back."""
    fig = go.Figure()
    if allocation is None or allocation.empty:
        return _empty(fig, "No allocation data", height=400,
                      x_title=f"Change vs BAU ({unit_elec})", y_title="Technology")

    d = allocation.assign(delta=allocation["delta_gwh"] * factor_elec)
    d = d.sort_values("delta")
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in d["delta"]]

    fig.add_trace(go.Bar(
        y=d["technology"], x=d["delta"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+,.0f}" for v in d["delta"]],
        textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=(d["bau_gwh"] * factor_elec, d["optimal_gwh"] * factor_elec),
        hovertemplate="<b>%{y}</b><br>BAU: %{customdata[0]:,.0f} · "
                      "Optimal: %{customdata[1]:,.0f} " + unit_elec +
                      "<br>Shift: %{x:+,.0f} " + unit_elec + "<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))

    _dark_theme(fig, height=400, x_title=f"Change vs BAU ({unit_elec})",
                y_title="Technology")
    return fig


# ═══════════════ V4 -- optimal energy by sector (stacked bars) ══════════════

def visual4_sector_stacked(
    sankey: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Stacked bars: each end-use sector served by the optimal plan, split by
    resource group (the plain-bar reading of the source-to-sector flow)."""
    fig = go.Figure()
    if sankey is None or sankey.empty:
        return _empty(fig, "No sector data", height=400,
                      y_title=f"Energy Supplied ({unit_elec})", x_title="Sector")

    links = sankey.groupby(["source", "target"], as_index=False)["gwh"].sum()
    links = links[links["gwh"] > 0]
    totals = links.groupby("target")["gwh"].sum().sort_values(ascending=False)
    sectors = list(totals.index)
    groups = [g for g in GROUP_COLORS if g in set(links["source"])] + \
             sorted(set(links["source"]) - set(GROUP_COLORS))

    pivot = links.pivot_table(index="target", columns="source", values="gwh",
                              aggfunc="sum").reindex(sectors)
    for grp in groups:
        vals = (pivot[grp] * factor_elec).fillna(0.0).tolist() if grp in pivot else \
            [0.0] * len(sectors)
        if not any(v > 0 for v in vals):
            continue
        fig.add_trace(go.Bar(
            x=sectors, y=vals, name=grp,
            marker=dict(color=GROUP_COLORS.get(grp, "#0EA5E9"), line=dict(width=0)),
            hovertemplate="%{x} ← " + grp + ": %{y:,.0f} " + unit_elec +
                          "<extra></extra>",
        ))

    _dark_theme(fig, height=400, y_title=f"Energy Supplied ({unit_elec})",
                x_title="Sector")
    fig.update_layout(barmode="stack")
    return fig


# ═══════════════ V5 -- sustainability scorecard (butterfly bars) ═════════════

def visual5_scorecard_butterfly(radar: pd.DataFrame) -> go.Figure:
    """Back-to-back horizontal bars per sustainability dimension (0-100):
    BAU reaches left in slate, the optimal plan reaches right in emerald."""
    fig = go.Figure()
    if radar is None or radar.empty:
        return _empty(fig, "No scorecard data", height=420,
                      x_title="Score (0-100, BAU ◀ | ▶ Optimal)", y_title="Dimension")

    dims = radar["dimension"].tolist()
    bau = radar["bau"].tolist()
    opt = radar["optimal"].tolist()

    fig.add_trace(go.Bar(
        y=dims, x=[-v for v in bau], orientation="h", name="BAU pathway",
        marker=dict(color="rgba(148, 163, 184, 0.70)", line=dict(width=0)),
        text=[f"{v:.0f}" for v in bau], textposition="outside",
        textfont=dict(size=10, color="#CBD5E1"),
        hovertemplate="<b>%{y}</b><br>BAU score: %{customdata:.0f}/100<extra></extra>",
        customdata=bau,
    ))
    fig.add_trace(go.Bar(
        y=dims, x=opt, orientation="h", name="Optimal plan",
        marker=dict(color="#10B981", line=dict(width=0)),
        text=[f"{v:.0f}" for v in opt], textposition="outside",
        textfont=dict(size=10, color="#10B981"),
        hovertemplate="<b>%{y}</b><br>Optimal score: %{customdata:.0f}/100<extra></extra>",
        customdata=opt,
    ))

    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))

    _dark_theme(fig, height=420,
                x_title="Score (0-100, BAU ◀ | ▶ Optimal)", y_title="Dimension")
    fig.update_layout(barmode="relative")
    return fig


# ═══════════════ V6 -- allocation concentration (Pareto) ════════════════

def visual6_concentration_pareto(
    allocation: pd.DataFrame,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Cumulative-share Pareto: resources ranked by optimal generation (bars,
    left axis) with the running cumulative share (line, right axis) -- shows how
    few technologies carry most of the plan."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if allocation is None or allocation.empty:
        base = go.Figure()
        return _empty(base, "No allocation data", height=390,
                      y_title=f"Optimal Generation ({unit_elec})", x_title="Technology")

    d = (allocation.assign(opt=allocation["optimal_gwh"] * factor_elec)
                   .sort_values("opt", ascending=False))
    total = d["opt"].sum()
    d["cum_pct"] = (d["opt"].cumsum() / total * 100.0) if total > 0 else 0.0
    order = d["technology"].tolist()

    fig.add_trace(go.Bar(
        x=order, y=d["opt"].tolist(), name=f"Optimal generation ({unit_elec})",
        marker=dict(color=[TECH_COLORS.get(t, "#0EA5E9") for t in order],
                    line=dict(width=0)),
        customdata=d["optimal_share_pct"].tolist(),
        hovertemplate="%{x}: %{y:,.0f} " + unit_elec +
                      " (%{customdata:.1f}% of plan)<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=order, y=d["cum_pct"].tolist(), name="Cumulative share (%)",
        mode="lines+markers", line=dict(color="#E2E8F0", width=2.2),
        marker=dict(size=7, symbol="circle"),
        hovertemplate="%{x}: %{y:.0f}% cumulative<extra></extra>",
    ), secondary_y=True)

    fig.add_hline(y=80, line=dict(color="#F59E0B", width=1.4, dash="dash"),
                  annotation_text="80% line", annotation_position="top left",
                  annotation_font_size=9.5, annotation_font_color="#F59E0B",
                  secondary_y=True)

    _dark_theme(fig, height=390, x_title="Technology (ranked by optimal share)")
    fig.update_yaxes(title_text=f"Optimal Generation ({unit_elec})", secondary_y=False,
                     gridcolor=_AXIS, tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(title_text="Cumulative Share (%)", secondary_y=True,
                     showgrid=False, range=[0, 105],
                     tickfont=dict(size=11, color=_TICK))
    return fig
