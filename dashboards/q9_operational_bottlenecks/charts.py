"""
dashboards/q9_operational_bottlenecks/charts.py
Six Plotly visuals for the Operational Bottlenecks dashboard (Q9).

V1  Bottleneck Severity Scorecard  -- ranked 0-100 severity bars, family-coloured
V2  Capacity Factor by Source      -- utilisation trajectories (fossil vs RE)
V3  Capability vs Delivered Energy -- nameplate energy vs what actually arrives
V4  Fossil Gas Supply Gap          -- domestic production vs consumption + shortfall
V5  T&D Delivery Loss Drain        -- loss rate with benchmark guide
V6  RE Capability vs Output        -- installed MW vs realised capacity factor
V7  Severity by Bottleneck Family  -- mean severity rollup: fossil vs renewable vs grid
V8  Source Bottleneck Map          -- bubble: capacity vs capacity factor, size = trapped energy

Charts are dumb: every value is pre-computed by
core/operational_bottlenecks.py -- no analysis happens here.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.operational_bottlenecks import (
    FAMILY_COLORS, GWH_PER_MW_YEAR, severity_color,
)

from .config import (
    CF_SERIES, FAMILIES, FAMILY_COLORS,
    AMBER, BLUE, CYAN, GREEN, ORANGE, RED, SLATE, TEAL,
    BENCHMARK_TD_LOSS_PCT, BENCHMARK_FOSSIL_CF_PCT,
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
    legend_cfg = (
        dict(orientation="h", y=-0.28, x=0.5, xanchor="center",
             font=dict(size=10.5, color=_TEXT))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color=_TEXT))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        margin=dict(l=62, r=46, t=45, b=72),
        height=height,
        legend=legend_cfg,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
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


# ══════════════════════ V1: Bottleneck Severity Scorecard ════════════════════
def visual1_severity_scorecard(scorecard: pd.DataFrame, base_year: int) -> go.Figure:
    """Ranked horizontal bars: how binding each operational bottleneck is (0-100)."""
    fig = go.Figure()
    if scorecard is None or scorecard.empty:
        return _empty(fig, "No bottleneck data available", height=420,
                      y_title=None, x_title="Severity (0-100, higher = more binding)")

    sc = scorecard.dropna(subset=["severity"]).sort_values("severity")
    labels = sc["name"].tolist()
    vals = sc["severity"].tolist()
    colors = [severity_color(v) for v in vals]
    fams = [FAMILIES.get(f, f) for f in sc["family"]]

    fig.add_trace(go.Bar(
        y=labels, x=vals, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.0f}" for v in vals],
        textposition="outside",
        textfont=dict(size=11, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=np.stack([sc["reading"], fams], axis=-1),
        hovertemplate="<b>%{y}</b><br>Severity: %{x:.0f}/100 · %{customdata[0]}"
                      "<br>Family: %{customdata[1]}<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=45, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                  annotation_text="binding ≥45", annotation_position="top",
                  annotation_font_size=9, annotation_font_color=_TICK)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        height=420, margin=dict(l=210, r=54, t=30, b=54),
        font=dict(family="Inter, sans-serif", color=_TEXT, size=11),
    )
    fig.update_xaxes(range=[0, 112], gridcolor=_AXIS, showgrid=True,
                     title_text="Severity (0-100, higher = more binding)",
                     title_font_size=11, tickfont=dict(size=10.5, color=_TICK))
    fig.update_yaxes(tickfont=dict(size=10.5, color="#CBD5E1"))
    return fig


# ══════════════════════ V2: Capacity Factor by Source ════════════════════════
def visual2_capacity_factor_trend(df: pd.DataFrame, years: Optional[list] = None) -> go.Figure:
    """Utilisation (capacity factor %) trajectories, fossil vs renewable."""
    fig = go.Figure()
    if df is None or df.empty:
        return _empty(fig, y_title="Capacity Factor (%)", height=380)

    d = df.sort_values("calendar_year")
    if years:
        d = d[d["calendar_year"].isin(years)]

    for col, label, color in CF_SERIES:
        if col not in d.columns:
            continue
        fig.add_trace(go.Scatter(
            x=d["calendar_year"], y=d[col],
            name=label, mode="lines",
            line=dict(color=color, width=2.4,
                      dash="dash" if label == "All Renewables" else "solid"),
            opacity=0.9,
            hovertemplate="%{y:.1f}<extra>" + label + "</extra>",
        ))

    fig.add_hline(y=BENCHMARK_FOSSIL_CF_PCT, line=dict(color="rgba(255,255,255,0.30)", width=1, dash="dot"),
                  annotation_text=f"{BENCHMARK_FOSSIL_CF_PCT:.0f}% target", annotation_position="top right",
                  annotation_font_size=9, annotation_font_color=_TICK)

    _dark_theme(fig, height=380, y_title="Capacity Factor (%)", x_title="Year")
    fig.update_yaxes(range=[0, 100])
    return fig


# ══════════════════════ V3: Capability vs Delivered Energy ═══════════════════
def visual3_capability_gap(df: pd.DataFrame, factor_gwh: float, unit_gwh: str) -> go.Figure:
    """Nameplate energy capability vs delivered generation; the gap is the loss."""
    fig = go.Figure()
    if df is None or df.empty:
        return _empty(fig, y_title=f"Energy ({unit_gwh})", height=390)

    d = df.dropna(subset=["capability_gwh", "total_gen_gwh"]).sort_values("calendar_year")
    if d.empty:
        return _empty(fig, y_title=f"Energy ({unit_gwh})", height=390)

    cap = d["capability_gwh"] * factor_gwh
    gen = d["total_gen_gwh"] * factor_gwh

    fig.add_trace(go.Bar(
        x=d["calendar_year"], y=cap, name="Nameplate Capability",
        marker=dict(color="rgba(100,116,139,0.55)", line=dict(color=SLATE, width=1)),
        hovertemplate="%{y:,.0f} " + unit_gwh + "<extra>Nameplate Capability</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=gen, name="Delivered Generation",
        mode="lines+markers", fill="tozeroy",
        fillcolor="rgba(0,166,251,0.18)",
        line=dict(color=BLUE, width=3), marker=dict(size=5),
        hovertemplate="%{y:,.0f} " + unit_gwh + "<extra>Delivered Generation</extra>",
    ))

    _dark_theme(fig, height=390, y_title=f"Energy ({unit_gwh})", x_title="Year")
    return fig


# ══════════════════════ V4: Fossil Gas Supply Gap ════════════════════════════
def visual4_gas_supply_gap(df: pd.DataFrame, factor_gas: float, unit_gas: str) -> go.Figure:
    """Domestic gas production vs consumption; the shortfall is the fossil bottleneck."""
    fig = go.Figure()
    if df is None or df.empty or "gas_prod_bcf" not in df.columns:
        return _empty(fig, "No gas balance data", y_title=f"Natural Gas ({unit_gas})", height=380)

    d = df.dropna(subset=["gas_cons_bcf"]).sort_values("calendar_year")
    if d.empty:
        return _empty(fig, "No gas balance data", y_title=f"Natural Gas ({unit_gas})", height=380)

    prod = d["gas_prod_bcf"] * factor_gas
    cons = d["gas_cons_bcf"] * factor_gas

    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=cons, name="Gas Consumption (demand)",
        mode="lines", line=dict(color=ORANGE, width=2.6),
        hovertemplate="%{y:,.1f} " + unit_gas + "<extra>Consumption</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=prod, name="Domestic Production",
        mode="lines", line=dict(color=GREEN, width=2.6),
        fill="tonexty", fillcolor="rgba(239,68,68,0.16)",
        hovertemplate="%{y:,.1f} " + unit_gas + "<extra>Production</extra>",
    ))

    _dark_theme(fig, height=380, y_title=f"Natural Gas ({unit_gas})", x_title="Year")
    fig.update_layout(
        annotations=[dict(
            text="Shaded area = shortfall met by LNG imports",
            xref="paper", yref="paper", x=0.5, y=1.12, showarrow=False,
            font=dict(size=10, color=_TICK),
        )]
    )
    return fig


# ══════════════════════ V5: T&D Delivery Loss Drain ══════════════════════════
def visual5_td_loss_drain(df: pd.DataFrame) -> go.Figure:
    """T&D loss rate over time with the benchmark ceiling."""
    fig = go.Figure()
    if df is None or df.empty or "td_loss_pct" not in df.columns:
        return _empty(fig, "No T&D loss data", y_title="Loss Rate (%)", height=360)

    d = df.dropna(subset=["td_loss_pct"]).sort_values("calendar_year")
    if d.empty:
        return _empty(fig, "No T&D loss data", y_title="Loss Rate (%)", height=360)

    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=d["td_loss_pct"], name="T&D Loss Rate",
        mode="lines+markers", fill="tozeroy",
        fillcolor="rgba(0,166,251,0.16)",
        line=dict(color=CYAN, width=3), marker=dict(size=5),
        hovertemplate="%{y:.1f}%<extra>T&D Loss Rate</extra>",
    ))
    fig.add_hline(y=BENCHMARK_TD_LOSS_PCT, line=dict(color=RED, width=1.6, dash="dash"),
                  annotation_text=f"{BENCHMARK_TD_LOSS_PCT:.0f}% benchmark",
                  annotation_position="top left",
                  annotation_font_size=9.5, annotation_font_color=RED)

    _dark_theme(fig, height=360, y_title="Loss Rate (% of generation)", x_title="Year")
    return fig


# ══════════════════════ V6: RE Capability vs Output ══════════════════════════
def visual6_re_capability_output(df: pd.DataFrame, factor_mw: float, unit_mw: str,
                                factor_gwh: float, unit_gwh: str) -> go.Figure:
    """Installed renewable MW vs realised RE generation — the conversion bottleneck."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if df is None or df.empty or "re_cap_mw" not in df.columns:
        base = go.Figure()
        return _empty(base, "No renewable capacity data", y_title=f"RE Capacity ({unit_mw})", height=390)

    d = df.dropna(subset=["re_cap_mw", "re_gen_gwh"]).sort_values("calendar_year")
    if d.empty:
        base = go.Figure()
        return _empty(base, "No renewable capacity data", y_title=f"RE Capacity ({unit_mw})", height=390)

    fig.add_trace(go.Bar(
        x=d["calendar_year"], y=d["re_cap_mw"] * factor_mw, name=f"RE Installed Capacity ({unit_mw})",
        marker=dict(color="rgba(16,185,129,0.55)", line=dict(color=GREEN, width=1)),
        hovertemplate="%{y:,.0f} " + unit_mw + "<extra>RE Capacity</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=d["calendar_year"], y=d["re_gen_gwh"] * factor_gwh, name=f"RE Generation ({unit_gwh})",
        mode="lines+markers", line=dict(color=AMBER, width=3), marker=dict(size=5),
        hovertemplate="%{y:,.0f} " + unit_gwh + "<extra>RE Generation</extra>",
    ), secondary_y=True)

    _dark_theme(fig, height=390, x_title="Year")
    fig.update_yaxes(title_text=f"RE Capacity ({unit_mw})", secondary_y=False,
                     gridcolor=_AXIS, tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(title_text=f"RE Generation ({unit_gwh})", secondary_y=True,
                     showgrid=False, tickfont=dict(size=11, color=_TICK))
    return fig


# ══════════════════════ V7: Severity by Bottleneck Family ════════════════════
def visual7_family_severity_summary(fam_sev: dict, scorecard: pd.DataFrame) -> go.Figure:
    """Mean bottleneck severity per family -- where the supply system is most choked.

    `fam_sev` is the engine's ``aggregate_by_family`` output (family -> mean 0-100
    severity); the ranked `scorecard` supplies the per-family count and the single
    tightest bottleneck shown on hover. No new analytics -- pure display rollup.
    """
    fig = go.Figure()
    fams = ["fossil", "renewable", "delivery"]
    rows = []
    for f in fams:
        try:
            sev = float(fam_sev.get(f, np.nan)) if fam_sev else np.nan
        except (TypeError, ValueError):
            sev = np.nan
        count, top = 0, "--"
        if scorecard is not None and not scorecard.empty:
            sub = scorecard[scorecard["family"] == f].dropna(subset=["severity"])
            count = len(sub)
            if not sub.empty:
                top = sub.iloc[0]["name"]
        rows.append({"label": FAMILIES.get(f, f), "sev": sev,
                     "color": FAMILY_COLORS.get(f, SLATE), "count": count, "top": top})

    if not any(np.isfinite(r["sev"]) for r in rows):
        return _empty(fig, "No family severity data", height=360,
                      y_title=None, x_title="Mean Severity (0-100)")

    rows_sorted = sorted(rows, key=lambda r: (r["sev"] if np.isfinite(r["sev"]) else -1))
    fig.add_trace(go.Bar(
        y=[r["label"] for r in rows_sorted],
        x=[r["sev"] if np.isfinite(r["sev"]) else 0 for r in rows_sorted],
        orientation="h",
        marker=dict(color=[r["color"] for r in rows_sorted], line=dict(width=0)),
        text=[(f"{r['sev']:.0f}" if np.isfinite(r["sev"]) else "n/a") for r in rows_sorted],
        textposition="outside",
        textfont=dict(size=12, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=[[r["count"], r["top"]] for r in rows_sorted],
        hovertemplate="<b>%{y}</b><br>Mean severity: %{x:.0f}/100"
                      "<br>Bottlenecks flagged: %{customdata[0]}"
                      "<br>Tightest: %{customdata[1]}<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=45, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"),
                  annotation_text="binding ≥45", annotation_position="top",
                  annotation_font_size=9, annotation_font_color=_TICK)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        height=360, margin=dict(l=150, r=54, t=30, b=54),
        font=dict(family="Inter, sans-serif", color=_TEXT, size=11),
    )
    fig.update_xaxes(range=[0, 112], gridcolor=_AXIS, showgrid=True,
                     title_text="Mean Severity (0-100, higher = more binding)",
                     title_font_size=11, tickfont=dict(size=10.5, color=_TICK))
    fig.update_yaxes(tickfont=dict(size=11, color="#CBD5E1"))
    return fig


# ══════════════════════ V8: Source Bottleneck Bubble Map ════════════════════
def visual8_source_bottleneck_map(df: pd.DataFrame, base_year: int,
                                  factor_power: float, unit_power: str,
                                  factor_elec: float, unit_elec: str) -> go.Figure:
    """One bubble per source: installed capacity (x) vs capacity factor (y),
    bubble area = energy trapped by that source's bottleneck at the analysis year.

    Reads the engine frame's per-source capacity / capacity-factor / generation
    columns (each source's own latest observation up to ``base_year``); it adds no
    analytics beyond capability-minus-generation. A log x-scale spreads sources
    that differ by orders of magnitude in size. This is deliberately a different
    visual language (scatter) from the dashboard's bar and line charts.
    """
    fig = go.Figure()
    if df is None or df.empty:
        return _empty(fig, "No source-level data", y_title="Capacity Factor (%)", height=380)

    d = df[df["calendar_year"] <= base_year]
    if d.empty:
        d = df
    d = d.sort_values("calendar_year")

    def latest(col):
        if col not in d.columns:
            return np.nan
        s = pd.to_numeric(d[col], errors="coerce").dropna()
        return float(s.iloc[-1]) if not s.empty else np.nan

    sources = [
        ("Thermal", "thermal_cap_mw", "fossil_cf_pct", "thermal_gen_gwh", ORANGE),
        ("Hydro", "Hydel_cap_mw", "hydel_cf_pct", "hydro_gen_gwh", BLUE),
        ("Wind", "Wind_cap_mw", "wind_cf_pct", "wind_gen_gwh", TEAL),
        ("Solar", "Solar_cap_mw", "solar_cf_pct", "solar_gen_gwh", AMBER),
    ]

    pts = []
    for name, cap_col, cf_col, gen_col, color in sources:
        cap, cf, gen = latest(cap_col), latest(cf_col), latest(gen_col)
        if not (np.isfinite(cap) and cap > 0 and np.isfinite(cf)):
            continue
        trapped = max(cap * GWH_PER_MW_YEAR - gen, 0.0) * factor_elec if np.isfinite(gen) else 0.0
        pts.append({"name": name, "cap": cap * factor_power, "cf": cf,
                    "trapped": trapped, "color": color})

    if not pts:
        return _empty(fig, "No source utilisation data", y_title="Capacity Factor (%)", height=380)

    max_t = max((p["trapped"] for p in pts), default=0.0)
    sizeref = (2.0 * max_t / (46.0 ** 2)) if max_t > 0 else 1.0

    fig.add_trace(go.Scatter(
        x=[p["cap"] for p in pts],
        y=[p["cf"] for p in pts],
        mode="markers+text",
        text=[p["name"] for p in pts],
        textposition="top center",
        textfont=dict(size=11, color="#E2E8F0", family="Inter, sans-serif"),
        marker=dict(
            size=[max(p["trapped"], max_t * 0.08) for p in pts],
            sizemode="area", sizeref=sizeref, sizemin=8,
            color=[p["color"] for p in pts],
            opacity=0.82, line=dict(color="rgba(255,255,255,0.35)", width=1),
        ),
        customdata=[[p["name"], p["trapped"]] for p in pts],
        hovertemplate="<b>%{customdata[0]}</b><br>Installed capacity: %{x:,.0f} " + unit_power +
                      "<br>Capacity factor: %{y:.1f}%<br>Trapped energy: %{customdata[1]:,.0f} " +
                      unit_elec + "<extra></extra>",
        showlegend=False,
    ))

    fig.add_hline(y=BENCHMARK_FOSSIL_CF_PCT, line=dict(color="rgba(255,255,255,0.30)", width=1, dash="dot"),
                  annotation_text=f"{BENCHMARK_FOSSIL_CF_PCT:.0f}% healthy utilisation", annotation_position="top left",
                  annotation_font_size=9.5, annotation_font_color=_TICK)

    _dark_theme(fig, height=380, y_title="Capacity Factor (%)",
                x_title=f"Installed Capacity ({unit_power}, log scale)")
    fig.update_xaxes(type="log")
    top_cf = max(p["cf"] for p in pts)
    fig.update_yaxes(range=[0, max(70.0, top_cf * 1.25)])
    return fig
