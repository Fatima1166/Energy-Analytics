"""
dashboards/q1_parameter_relationships/charts.py -- visuals for Question 1
(energy-parameter relationships + what-if predicted values).

Simple chart types, one per analytical job:
V1  Correlation heat-map        -- parameter x parameter Pearson r
V2  Pair scatter + OLS trend    -- two parameters, fitted line + R² note
V3  Rolling correlation line    -- stability of one pair across sliding windows
V4  History + baseline + what-if-- bars (reported) continued by two forecast lines
V5  What-if impact bars         -- diverging % change vs baseline per parameter
V6  Driver elasticity bars      -- grouped β_GDP / β_Pop per parameter
V7  Top relationship ranking      -- lollipop of the strongest |r| pairs
V8  Correlation distribution      -- histogram of every pairwise r

Presentation-only ("dumb"): the core/parameter_relationships.py engine
pre-computes every value; these functions only draw.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

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


# ═══════════════════ V1 -- correlation heat-map ══════════════════════════════

def visual1_corr_heatmap(corr: pd.DataFrame, labels: list) -> go.Figure:
    """Parameter x matrix of Pearson r (-1..+1); green = co-move, red = inverse."""
    fig = go.Figure()
    if corr is None or corr.empty:
        return _empty(fig, "No overlapping data in this period", height=520,
                      y_title="Parameter", x_title="Parameter")
    z = corr.to_numpy(float)
    fig.add_trace(go.Heatmap(
        z=z, x=labels, y=labels,
        zmin=-1.0, zmax=1.0,
        colorscale=[[0.0, "#B91C1C"], [0.5, "#14171E"], [1.0, "#10B981"]],
        texttemplate="%{z:.1f}",
        textfont=dict(size=9.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        hovertemplate="%{y} × %{x}<br>r = %{z:.2f}<extra></extra>",
        colorbar=dict(title=dict(text="r", font=dict(size=11, color=_TEXT)),
                      tickfont=dict(size=10, color=_TICK),
                      outlinewidth=0, len=0.9),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=_PAPER, plot_bgcolor=_PLOT,
        height=560, margin=dict(l=190, r=24, t=30, b=150),
        xaxis=dict(tickfont=dict(size=9.5, color=_TEXT), tickangle=-45),
        yaxis=dict(tickfont=dict(size=9.5, color=_TEXT), autorange="reversed"),
    )
    return fig


# ═══════════════════ V2 -- pair scatter + OLS trend ══════════════════════════

def visual2_pair_scatter(fit: dict, x_label: str, y_label: str,
                         x_unit: str, y_unit: str,
                         factor_x: float = 1.0, factor_y: float = 1.0) -> go.Figure:
    """Scatter of the selected pair with the fitted line and an r / R² note."""
    fig = go.Figure()
    pts = fit.get("points") if fit else None
    if pts is None or pts.empty or len(pts) < 2:
        return _empty(fig, "Not enough joint observations", height=400,
                      y_title=f"{y_label} ({y_unit})", x_title=f"{x_label} ({x_unit})")

    # engine returns points as [x_key, y_key, calendar_year] -- positional
    x = pts.iloc[:, 0]
    y = pts.iloc[:, 1]
    xs, ys = x.to_numpy(float) * factor_x, y.to_numpy(float) * factor_y
    yrs = pd.to_numeric(pts["calendar_year"], errors="coerce").to_numpy(float) \
        if "calendar_year" in pts.columns else None

    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers", name="Observed years",
        marker=dict(size=10, color=yrs if yrs is not None else "#00A6FB",
                    colorscale="Deep", showscale=False, opacity=0.9,
                    line=dict(color="rgba(255,255,255,0.35)", width=1)),
        customdata=(yrs.astype(int) if yrs is not None else None),
        hovertemplate=f"{x_label}: %{{x:,.1f}} {x_unit}<br>"
                      f"{y_label}: %{{y:,.1f}} {y_unit}"
                      + ("<br>Year: %{customdata}<extra></extra>"
                         if yrs is not None else "<extra></extra>"),
    ))
    if np.isfinite(fit.get("slope", np.nan)):
        # slope is in base units; scale intercept/slope for display units
        b = fit["slope"] * factor_y / factor_x
        a = fit["intercept"] * factor_y
        xr = np.array([xs.min(), xs.max()])
        fig.add_trace(go.Scatter(
            x=xr, y=a + b * xr, mode="lines", name="OLS fit",
            line=dict(color="#F59E0B", width=2.4, dash="dash"),
            hoverinfo="skip",
        ))
        note = (f"r = {fit['r']:.2f} · R² = {fit['r2']:.2f}<br>"
                f"slope = {b:,.2f} {y_unit}/{x_unit} · n = {fit['n']}")
        fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.98,
                           text=note, showarrow=False, align="left",
                           font=dict(size=10, color=_TEXT),
                           bgcolor="rgba(20,23,30,0.72)",
                           bordercolor=_AXIS, borderwidth=1, borderpad=6)

    _dark_theme(fig, height=400, y_title=f"{y_label} ({y_unit})",
                x_title=f"{x_label} ({x_unit})")
    return fig


# ═══════════════════ V3 -- rolling correlation line ══════════════════════════

def visual3_rolling_corr(roll: pd.DataFrame, pair_label: str,
                         window: int) -> go.Figure:
    """One line: the pair's correlation recomputed on each sliding window."""
    fig = go.Figure()
    if roll is None or roll.empty:
        return _empty(fig, "Rolling window needs more history", height=360,
                      y_title="Pearson r", x_title="Window end year")
    fig.add_trace(go.Scatter(
        x=roll["year"], y=roll["r"], mode="lines+markers",
        name=f"{window}-yr rolling r",
        line=dict(color="#14B8A6", width=2.8), marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(20,184,166,0.12)",
        hovertemplate="%{x}: r = %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dot"))
    for lvl, col in ((0.7, "rgba(16,185,129,0.55)"), (-0.7, "rgba(239,68,68,0.55)")):
        fig.add_hline(y=lvl, line=dict(color=col, width=1, dash="dash"),
                      annotation_text=f"{'strong +' if lvl > 0 else 'strong −'}",
                      annotation_position="top right",
                      annotation_font_size=9, annotation_font_color=_TICK)
    fig.update_yaxes(range=[-1.05, 1.05])
    _dark_theme(fig, height=360,
                y_title=f"Pearson r ({pair_label})", x_title="Window end year")
    return fig


# ═══════════════════ V4 -- history + baseline + what-if ══════════════════════

def visual4_forecast_path(path: pd.DataFrame, label: str, unit: str,
                          factor: float = 1.0, boundary_year: Optional[int] = None
                          ) -> go.Figure:
    """Reported history as bars; baseline and what-if projections as lines from
    the last reported year to the horizon."""
    fig = go.Figure()
    if path is None or path.empty:
        return _empty(fig, f"No forecast for {label}", height=400,
                      y_title=f"{label} ({unit})", x_title="Year")

    colors = {"History": "#00A6FB", "Baseline": "#10B981", "What-if": "#F59E0B"}
    dashes = {"History": None, "Baseline": "solid", "What-if": "dash"}
    for series in ("History", "Baseline", "What-if"):
        d = path[path["series"] == series]
        if d.empty:
            continue
        vals = d["value"] * factor
        if series == "History":
            fig.add_trace(go.Bar(
                x=d["year"], y=vals, name="Reported",
                marker=dict(color="rgba(0,166,251,0.55)",
                            line=dict(color="#00A6FB", width=1)),
                hovertemplate="%{x}: %{y:,.1f} " + unit + "<extra>Reported</extra>",
            ))
        else:
            # anchor the forecast lines onto the last history point
            hist = path[path["series"] == "History"]
            if not hist.empty:
                x = np.concatenate([[hist["year"].iloc[-1]], d["year"].to_numpy()])
                y = np.concatenate([[hist["value"].iloc[-1] * factor],
                                    vals.to_numpy()])
            else:
                x, y = d["year"].to_numpy(), vals.to_numpy()
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines+markers", name=series,
                line=dict(color=colors[series], width=2.8, dash=dashes[series]),
                marker=dict(size=5),
                hovertemplate="%{x}: %{y:,.1f} " + unit + "<extra>" + series + "</extra>",
            ))

    if boundary_year:
        fig.add_vline(x=boundary_year + 0.5,
                      line=dict(color="rgba(255,255,255,0.30)", width=1.2, dash="dot"),
                      annotation_text="Reported ◀ | ▶ Modelled",
                      annotation_position="top",
                      annotation_font_size=9, annotation_font_color=_TICK)

    _dark_theme(fig, height=400, y_title=f"{label} ({unit})", x_title="Year")
    return fig


# ═══════════════════ V5 -- what-if impact (diverging bars) ═══════════════════

def visual5_impact_bars(fc: pd.DataFrame, horizon: int) -> go.Figure:
    """What-if vs baseline change at the horizon, one diverging bar per parameter."""
    fig = go.Figure()
    if fc is None or fc.empty:
        return _empty(fig, "No forecast rows", height=430,
                      x_title=f"What-if vs Baseline at {horizon} (%)",
                      y_title="Parameter")
    d = fc.sort_values("delta_pct")
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in d["delta_pct"]]
    fig.add_trace(go.Bar(
        y=d["label"], x=d["delta_pct"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+.1f}%" for v in d["delta_pct"]],
        textposition="outside",
        textfont=dict(size=10, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=np.stack([d["baseline_value"], d["whatif_value"]], axis=-1),
        hovertemplate="<b>%{y}</b><br>Δ: %{x:+.1f}%<br>"
                      "Baseline: %{customdata[0]:,.1f} · What-if: %{customdata[1]:,.1f}"
                      "<extra></extra>",
        showlegend=False,
    ))
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))
    _dark_theme(fig, height=430,
                x_title=f"What-if vs Baseline at {horizon} (%)", y_title="Parameter")
    fig.update_yaxes(tickfont=dict(size=10, color="#CBD5E1"))
    return fig


# ═══════════════════ V6 -- driver elasticities (grouped bars) ════════════════

def visual6_elasticity_bars(fc: pd.DataFrame) -> go.Figure:
    """Fitted d ln(param)/d ln(driver) for GDP and population, per parameter."""
    fig = go.Figure()
    if fc is None or fc.empty:
        return _empty(fig, "No elasticity fits available", height=430,
                      y_title="Elasticity (β)", x_title="Parameter")
    d = fc.sort_values("b_gdp", ascending=False)
    fig.add_trace(go.Bar(
        x=d["label"], y=d["b_gdp"], name="β vs GDP",
        marker=dict(color="#F59E0B", line=dict(width=0)),
        hovertemplate="%{x} β(GDP): %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=d["label"], y=d["b_pop"], name="β vs Population",
        marker=dict(color="#22D3EE", line=dict(width=0)),
        hovertemplate="%{x} β(Pop): %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(barmode="group")
    _dark_theme(fig, height=430, y_title="Elasticity (β)", x_title="Parameter")
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═══════════════ V7 -- top relationship ranking (lollipop) ══════════════

def visual7_top_pairs(pairs: pd.DataFrame, labels: dict, n: int = 12) -> go.Figure:
    """Lollipop ranking of the strongest parameter links: the stem spans 0 → r
    and the dot carries the exact coefficient."""
    fig = go.Figure()
    if pairs is None or pairs.empty:
        return _empty(fig, "No computable pairs in this period", height=430,
                      x_title="Pearson r", y_title="Parameter pair")

    d = pairs.head(n).iloc[::-1]          # weakest of the top-n at the bottom
    lab = [f"{labels.get(a, a)} × {labels.get(b, b)}"
           for a, b in zip(d["param_a"], d["param_b"])]
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in d["r"]]

    for y, r in zip(lab, d["r"]):
        fig.add_shape(type="line", x0=0.0, x1=float(r), y0=y, y1=y,
                      line=dict(color="rgba(200,208,218,0.45)", width=1.6))
    fig.add_trace(go.Scatter(
        x=d["r"], y=lab, mode="markers", showlegend=False,
        marker=dict(size=13, color=colors, line=dict(color="#E2E8F0", width=1)),
        customdata=np.stack([d["abs_r"], d["param_a"], d["param_b"]], axis=-1),
        hovertemplate="<b>%{customdata[1]} × %{customdata[2]}</b>"
                      "<br>r = %{x:+.2f}<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))

    _dark_theme(fig, height=430, x_title="Pearson r (green co-move · red inverse)",
                y_title="Parameter pair")
    fig.update_xaxes(range=[-1.05, 1.05])
    fig.update_yaxes(tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═══════════════ V8 -- correlation distribution (histogram) ═════════════

def visual8_corr_distribution(pairs: pd.DataFrame) -> go.Figure:
    """How connected is the system? Histogram of every computable pairwise r,
    positive links in emerald and inverse links in red."""
    fig = go.Figure()
    if pairs is None or pairs.empty:
        return _empty(fig, "No computable pairs in this period", height=380,
                      y_title="Number of Parameter Pairs", x_title="Pearson r")

    pos = pairs[pairs["r"] >= 0]["r"]
    neg = pairs[pairs["r"] < 0]["r"]
    bins = dict(size=0.1)
    fig.add_trace(go.Histogram(
        x=pos, name="Co-moving (r ≥ 0)",
        xbins=bins, marker_color="rgba(16,185,129,0.75)",
        hovertemplate="r %{x}: %{y} pairs<extra>Co-moving</extra>",
    ))
    fig.add_trace(go.Histogram(
        x=neg, name="Inverse (r < 0)",
        xbins=bins, marker_color="rgba(239,68,68,0.75)",
        hovertemplate="r %{x}: %{y} pairs<extra>Inverse</extra>",
    ))
    for lvl in (-0.7, 0.7):
        fig.add_vline(x=lvl, line=dict(color="rgba(255,255,255,0.35)",
                                       width=1.2, dash="dot"),
                      annotation_text="strong" if lvl < 0 else "strong",
                      annotation_position="top",
                      annotation_font_size=9, annotation_font_color=_TICK)

    _dark_theme(fig, height=380, y_title="Number of Parameter Pairs",
                x_title="Pearson r (0.1-wide bins)")
    fig.update_layout(barmode="overlay", bargap=0.06)
    return fig
