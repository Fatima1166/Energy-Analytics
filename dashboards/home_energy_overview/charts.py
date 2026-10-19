"""
dashboards/home_energy_overview/charts.py -- landing visuals for the Energy
Overview home page.

Visuals:
H1  Supply vs Demand Area Lines  -- The national energy balance & conversion gap
H2  Fuel-Mix Donut               -- Latest-year primary supply by energy carrier
H3  CO2 Emission Profile         -- Annual emissions with recent-year emphasis
H4  Power Generation Trajectory  -- Historical grid output growth (GWh)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import FUEL_COLOURS, FALLBACK_RING

_AXIS = "rgba(255, 255, 255, 0.08)"
_TICK = "#8B95A7"
_TEXT = "#E2E8F0"
_PAPER = "rgba(17, 22, 34, 0.6)"
_PLOT = "rgba(13, 17, 26, 0.7)"
_FONT_FAMILY = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif"


def _dark_theme(fig, height: int = 330, y_title=None, x_title=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=_PLOT,
        margin=dict(l=54, r=24, t=32, b=48),
        height=height,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#161D2C",
            bordercolor="rgba(255, 255, 255, 0.15)",
            font_size=11.5,
            font_family=_FONT_FAMILY,
            font_color="#FFFFFF"
        ),
        font=dict(family=_FONT_FAMILY, color=_TEXT),
        legend=dict(
            orientation="h",
            y=-0.22,
            x=0.5,
            xanchor="center",
            font=dict(size=11, color=_TEXT),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(
        gridcolor=_AXIS,
        zerolinecolor=_AXIS,
        title=dict(text=x_title, font=dict(size=11.5, color="#94A3B8")) if x_title else None,
        tickfont=dict(size=11, color=_TICK),
        showline=False,
    )
    fig.update_yaxes(
        gridcolor=_AXIS,
        zerolinecolor=_AXIS,
        title=dict(text=y_title, font=dict(size=11.5, color="#94A3B8")) if y_title else None,
        tickfont=dict(size=11, color=_TICK),
        showline=False,
    )
    return fig


def _empty(fig, msg="No data available", **kw):
    fig.add_annotation(
        text=msg,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=_TEXT, size=13),
    )
    return _dark_theme(fig, **kw)


# ═══════════════ H1 -- supply vs demand (area lines) ════════════════════════

def visual1_supply_demand(hist: pd.DataFrame, unit: str, factor: float) -> go.Figure:
    """Two filled lines: primary supply above final demand; the widening or
    narrowing band between them represents conversion, refining & T&D losses."""
    fig = go.Figure()
    if hist is None or hist.empty:
        return _empty(fig, "No supply/demand history", height=330,
                      y_title=f"Energy ({unit})", x_title="Calendar Year")
    x = hist["calendar_year"].astype(int)
    sup = hist["total_primary_supply_toe"] * factor
    dem = hist["total_final_consumption_toe"] * factor

    fig.add_trace(go.Scatter(
        x=x, y=sup, mode="lines+markers", name="Primary Supply (TPES)",
        line=dict(color="#00A6FB", width=2.8, shape="spline", smoothing=0.7),
        marker=dict(size=4, color="#00A6FB"),
        fill="tozeroy", fillcolor="rgba(0, 166, 251, 0.12)",
        hovertemplate="Supply: <b>%{y:,.1f}</b> " + unit + "<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=dem, mode="lines+markers", name="Final Consumption (TFC)",
        line=dict(color="#F59E0B", width=2.8, shape="spline", smoothing=0.7),
        marker=dict(size=4, color="#F59E0B"),
        fill="tozeroy", fillcolor="rgba(245, 158, 11, 0.12)",
        hovertemplate="Demand: <b>%{y:,.1f}</b> " + unit + "<extra></extra>",
    ))
    _dark_theme(fig, height=330, y_title=f"Energy Balance ({unit})", x_title="Year")
    return fig


# ═══════════════ H2 -- fuel mix donut ════════════════════════════════════════

def visual2_fuel_donut(mix: pd.DataFrame) -> go.Figure:
    """Latest-year primary supply share by source as a modern donut."""
    fig = go.Figure()
    if mix is None or mix.empty:
        return _empty(fig, "No source-level supply for the latest year", height=330)

    # Curated palette
    color_map = {
        "gas": "#00A6FB",
        "oil": "#F59E0B",
        "coal": "#64748B",
        "hydro": "#14B8A6",
        "nuclear": "#A78BFA",
        "renewable": "#10B981",
        "solar": "#FBBF24",
        "wind": "#34D399",
    }
    colours = []
    for i, src in enumerate(mix["source_name"]):
        src_lower = str(src).lower()
        matched = None
        for k, col in color_map.items():
            if k in src_lower:
                matched = col
                break
        colours.append(matched or FALLBACK_RING[i % len(FALLBACK_RING)])

    yr = int(mix["calendar_year"].iloc[0])
    total_supply = mix["supply_toe"].sum()

    fig.add_trace(go.Pie(
        labels=mix["source_name"],
        values=mix["share_pct"],
        hole=0.62,
        marker=dict(colors=colours, line=dict(color="#0D111A", width=2.5)),
        textinfo="percent",
        textfont=dict(size=11, color="#FFFFFF", family=_FONT_FAMILY),
        sort=False,
        customdata=mix["supply_toe"],
        hovertemplate="<b>%{label}</b><br>Share: <b>%{value:.1f}%</b><br>Supply: <b>%{customdata:,.0f}</b> TOE<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b style='font-size:18px;color:#FFFFFF;'>{total_supply/1e6:.1f}M</b><br><span style='font-size:10px;color:#8B95A7;'>TOE Supply</span><br><b style='font-size:11px;color:#10B981;'>{yr}</b>",
        x=0.5, y=0.5,
        font=dict(family=_FONT_FAMILY, color=_TEXT),
        showarrow=False,
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=330,
        margin=dict(l=10, r=10, t=28, b=10),
        font=dict(family=_FONT_FAMILY, color=_TEXT),
        legend=dict(
            orientation="v",
            y=0.5,
            x=1.02,
            xanchor="left",
            font=dict(size=10.5, color=_TEXT),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ═══════════════ H3 -- CO2 emissions (vertical bars) ════════════════════════

def visual3_co2_bars(hist: pd.DataFrame, unit: str, factor: float) -> go.Figure:
    """Annual CO2 emissions; modern gradient-styled bars with latest highlight."""
    fig = go.Figure()
    if hist is None or hist.empty:
        return _empty(fig, "No emissions record", height=330,
                      y_title=f"CO2 ({unit})", x_title="Year")
    x = hist["calendar_year"].astype(int)
    y = hist["co2_emissions_tonnes"] * factor
    n = len(y)
    colors = ["rgba(239, 68, 68, 0.65)"] * (n - 1) + ["#F59E0B"] if n > 0 else []

    fig.add_trace(go.Bar(
        x=x, y=y, name="CO₂ Emissions",
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.08)", width=1)),
        hovertemplate="Year %{x}: <b>%{y:,.1f}</b> " + unit + "<extra>Emissions</extra>",
    ))
    _dark_theme(fig, height=330, y_title=f"Emissions ({unit})",
                x_title="Calendar Year (Latest Year Highlighted in Amber)")
    return fig


# ═══════════════ H4 -- Electricity Generation Trajectory ══════════════════════

def visual4_generation_trajectory(hist: pd.DataFrame, unit: str, factor: float) -> go.Figure:
    """Annual power generation (GWh) trajectory."""
    fig = go.Figure()
    if hist is None or hist.empty:
        return _empty(fig, "No generation history", height=330,
                      y_title=f"Generation ({unit})", x_title="Year")
    x = hist["calendar_year"].astype(int)
    y = hist["generation_gwh"] * factor

    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", name="Total Grid Generation",
        line=dict(color="#10B981", width=2.8, shape="spline", smoothing=0.7),
        marker=dict(size=4.5, color="#10B981"),
        fill="tozeroy", fillcolor="rgba(16, 185, 129, 0.12)",
        hovertemplate="Generation: <b>%{y:,.1f}</b> " + unit + "<extra></extra>",
    ))
    _dark_theme(fig, height=330, y_title=f"Generation ({unit})", x_title="Calendar Year")
    return fig
