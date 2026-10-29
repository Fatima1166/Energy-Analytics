"""
dashboards/q9_operational_bottlenecks/charts.py
Four Plotly visuals for the Operational Bottlenecks dashboard (Q9), in two rows
of two.  Each one answers part of "what are the operational bottlenecks in fossil
and renewable energy supplies?":

V1  Which choke point hurts most      -- ranked 0-100 severity bars
V2  How long plant has sat idle       -- utilisation trends, fossil vs clean
V3  The energy that never came out    -- what plant could make vs what it made
V4  The gas shortfall                 -- gas used vs gas made at home

Charts are dumb: every value is pre-computed by
core/operational_bottlenecks.py -- no analysis happens here.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from core.operational_bottlenecks import severity_color

from .config import (
    CF_SERIES, FAMILIES,
    BLUE, GREEN, ORANGE, SLATE,
    BENCHMARK_FOSSIL_CF_PCT,
)

# ── Dark theme helpers ────────────────────────────────────────────────────────
_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8CDD6"
_PAPER = "#1A1D24"
_PLOT = "#14171E"
_GRID = "rgba(255,255,255,0.10)"


def _dark_theme(fig, height: int = 380, y_title: Optional[str] = None,
                x_title: Optional[str] = "Year", legend_h: bool = True):
    """Shared skin.  Every visual on this page sits in a half-width row, so the
    side margins stay tight and the legend is set small enough to fit the paper."""
    legend_cfg = (
        dict(orientation="h", y=-0.26, x=0.5, xanchor="center",
             font=dict(size=9.5, color=_TEXT))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=9.5, color=_TEXT))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        margin=dict(l=60, r=30, t=45, b=76),
        height=height,
        legend=legend_cfg,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
    )
    fig.update_xaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=x_title, font=dict(size=11, color=_TEXT)) if x_title else None,
                     tickfont=dict(size=10.5, color=_TICK))
    fig.update_yaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=y_title, font=dict(size=11, color=_TEXT)) if y_title else None,
                     tickfont=dict(size=10.5, color=_TICK))
    return fig


def _empty(fig, msg="No data available", **kw):
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, **kw)


def _year_tag(year) -> str:
    """Return ' (2018)' for the year a reading came from, '' when it has none."""
    try:
        y = float(year)
    except (TypeError, ValueError):
        return ""
    return f" ({int(y)})" if y == y else ""


# ══════════════════════ V1: Which choke point hurts most ═════════════════════
def visual1_severity_scorecard(scorecard: pd.DataFrame) -> go.Figure:
    """Ranked horizontal bars: how badly each bottleneck limits supply (0-100)."""
    fig = go.Figure()
    if scorecard is None or scorecard.empty:
        return _empty(fig, "No bottleneck data available", height=420,
                      y_title=None, x_title="How badly it limits supply (0 to 100)")

    sc = scorecard.dropna(subset=["severity"]).sort_values("severity")
    labels = sc["name"].tolist()
    vals = sc["severity"].tolist()
    colors = [severity_color(v) for v in vals]
    fams = [FAMILIES.get(f, f) for f in sc["family"]]
    # Each stream is reported through a different last year, so every reading
    # carries the year it was actually taken -- never one shared snapshot.
    reads = [f"{r}{_year_tag(y)}" for r, y in zip(sc["reading"], sc["obs_year"])]

    fig.add_trace(go.Bar(
        y=labels, x=vals, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.0f}" for v in vals],
        textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=list(zip(reads, fams)),
        hovertemplate="<b>%{y}</b><br>Severity: %{x:.0f}/100 · %{customdata[0]}"
                      "<br>Family: %{customdata[1]}<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=45, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                  annotation_text="45 = serious", annotation_position="top",
                  annotation_font_size=9, annotation_font_color=_TICK)

    # half-width row: the plain-language names are short enough to live inside a
    # narrow left margin, which leaves the bars room to be read at all
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        height=420, margin=dict(l=142, r=36, t=44, b=48),
        font=dict(family="Inter, sans-serif", color=_TEXT, size=10.5),
    )
    fig.update_xaxes(range=[0, 112], gridcolor=_AXIS, showgrid=True,
                     title_text="How badly it limits supply (0 to 100)",
                     title_font_size=10.5, tickfont=dict(size=10, color=_TICK))
    fig.update_yaxes(tickfont=dict(size=10, color="#CBD5E1"))
    return fig


# ══════════════════════ V2: How long plant has sat idle ═════════════════════
def visual2_capacity_factor_trend(df: pd.DataFrame) -> go.Figure:
    """How much of their size fossil and clean plant actually make, year by year."""
    fig = go.Figure()
    if df is None or df.empty:
        return _empty(fig, y_title="Power made (% of what plant could make)",
                      height=380)

    d = df.sort_values("calendar_year")

    for col, label, color in CF_SERIES:
        if col not in d.columns:
            continue
        fig.add_trace(go.Scatter(
            x=d["calendar_year"], y=d[col],
            name=label, mode="lines",
            line=dict(color=color, width=2.4,
                      dash="dash" if col == "re_cf_pct" else "solid"),
            opacity=0.9,
            hovertemplate="%{y:.1f}<extra>" + label + "</extra>",
            connectgaps=False,
        ))

    fig.add_hline(y=BENCHMARK_FOSSIL_CF_PCT, line=dict(color="rgba(255,255,255,0.30)", width=1, dash="dot"),
                  annotation_text=f"{BENCHMARK_FOSSIL_CF_PCT:.0f}% is healthy",
                  annotation_position="top right",
                  annotation_font_size=9, annotation_font_color=_TICK)

    _dark_theme(fig, height=380,
                y_title="Power made (% of what plant could make)", x_title="Year")
    fig.update_yaxes(range=[0, 100])
    return fig


# ══════════════════════ V3: The energy that never came out ═══════════════════
def visual3_capability_gap(df: pd.DataFrame, factor_gwh: float, unit_gwh: str) -> go.Figure:
    """What all the plant could make in a year vs what it made; the gap is idle."""
    fig = go.Figure()
    if df is None or df.empty:
        return _empty(fig, y_title=f"Power ({unit_gwh})", height=390)

    d = df.dropna(subset=["capability_gwh", "total_gen_gwh"], how="all").sort_values("calendar_year")
    if d.empty:
        return _empty(fig, y_title=f"Power ({unit_gwh})", height=390)

    cap = d["capability_gwh"] * factor_gwh
    gen = d["total_gen_gwh"] * factor_gwh

    fig.add_trace(go.Bar(
        x=d["calendar_year"], y=cap, name="Could make",
        marker=dict(color="rgba(100,116,139,0.55)", line=dict(color=SLATE, width=1)),
        hovertemplate="%{y:,.0f} " + unit_gwh + "<extra>Could make</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=gen, name="Actually made",
        mode="lines+markers", fill="tozeroy",
        fillcolor="rgba(0,166,251,0.18)",
        line=dict(color=BLUE, width=3), marker=dict(size=5),
        hovertemplate="%{y:,.0f} " + unit_gwh + "<extra>Actually made</extra>",
        connectgaps=False,
    ))

    _dark_theme(fig, height=390, y_title=f"Power ({unit_gwh})", x_title="Year")
    # energy numbers run to six digits, so the left margin needs the room
    fig.update_layout(margin=dict(l=72, r=30, t=45, b=76))
    return fig


# ══════════════════════ V4: The gas shortfall ════════════════════════════════
def visual4_gas_supply_gap(df: pd.DataFrame, factor_gas: float, unit_gas: str) -> go.Figure:
    """Gas the country uses vs gas it makes at home; the shaded gap must be bought."""
    fig = go.Figure()
    if df is None or df.empty or "gas_prod_bcf" not in df.columns:
        return _empty(fig, "No gas balance data", y_title=f"Gas ({unit_gas})", height=380)

    d = df.dropna(subset=["gas_cons_bcf", "gas_prod_bcf"], how="all").sort_values("calendar_year")
    if d.empty:
        return _empty(fig, "No gas balance data", y_title=f"Gas ({unit_gas})", height=380)

    prod = d["gas_prod_bcf"] * factor_gas
    cons = d["gas_cons_bcf"] * factor_gas

    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=cons, name="Gas used",
        mode="lines", line=dict(color=ORANGE, width=2.6),
        hovertemplate="%{y:,.1f} " + unit_gas + "<extra>Gas used</extra>",
        connectgaps=False,
    ))
    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=prod, name="Gas made at home",
        mode="lines", line=dict(color=GREEN, width=2.6),
        fill="tonexty", fillcolor="rgba(239,68,68,0.16)",
        hovertemplate="%{y:,.1f} " + unit_gas + "<extra>Gas made at home</extra>",
        connectgaps=False,
    ))

    _dark_theme(fig, height=380, y_title=f"Gas ({unit_gas})", x_title="Year")
    return fig

