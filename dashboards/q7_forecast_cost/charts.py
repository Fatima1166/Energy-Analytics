"""
dashboards/q7_forecast_cost/charts.py

Five Plotly figures for Question 7 (what electricity bought from power producers
costs, and what it will cost).

V1  What is paid now       -- the measured bill by source, and what a unit cost
V2  The forecast bill      -- one path per build-out case up to the horizon
V3  Where the money goes   -- walk from the measured bill to the forecast bill
V4  What one unit costs    -- average buying price, measured then one path per case
V5  Fuel prices and trust  -- the fuel-price band, and the model's average error

Presentation only: every number is computed by core/cost_forecast.py or by the
page, and arrives here ready to draw.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.cost_forecast import COST_SCENARIO_COLORS, HISTORY_END, TECH_COLORS

from .config import AMBER, BLUE, GREEN, LIGHT, RED, SLATE, TECHS_SHOWN

# ── Dark theme helpers ────────────────────────────────────────────────────────

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8D0DA"


def _dark_theme(fig, height: int = 380, x_title: Optional[str] = "Year",
                legend_h: bool = True):
    legend_cfg = (
        dict(orientation="h", y=-0.40, x=0.5, xanchor="center",
             font=dict(size=10.5, color=_TEXT))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color=_TEXT))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=62, r=52, t=52, b=108),
        height=height,
        legend=legend_cfg,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
    )
    fig.update_xaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     tickfont=dict(size=11, color=_TICK))
    # Titles are only set here when given, so titles placed on one panel by the
    # caller are never wiped out by the shared theme.
    if x_title:
        fig.update_xaxes(title=dict(text=x_title, font=dict(size=11.5, color=_TEXT)))
    return fig


def _empty(message: str) -> go.Figure:
    """A dark panel that simply says there is nothing to draw."""
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, height=380, x_title=None)


def _boundary(fig, text: str = "reported years this side  |  forecast from here"):
    """The line between years that happened and years the model expects."""
    fig.add_vline(x=HISTORY_END + 0.5, line=dict(color="#64748B", width=1.3, dash="dash"))
    fig.add_annotation(
        x=HISTORY_END + 0.5, y=0.04, yref="paper", yanchor="bottom",
        text=text, showarrow=False,
        font=dict(size=9.5, color="#94A3B8", family="Inter, sans-serif"),
        bgcolor="rgba(20, 23, 30, 0.90)",
        bordercolor="#334155", borderwidth=1, borderpad=3,
        xanchor="center",
    )
    return fig


def _ccol(tech: str) -> str:
    """The cost column the engine writes for one technology."""
    return f"cost_{tech.lower().replace(' ', '')}_usd"


# ── V1: what is paid now ─────────────────────────────────────────────────────

def visual1_cost_so_far(hist: pd.DataFrame, unit_cost: str = "USD bn",
                        factor_cost: float = 1.0) -> go.Figure:
    """Left: the bill for what was made, stacked by source.
    Right: what one unit cost, and the part of the bill that is fuel."""
    h = hist[hist["calendar_year"] >= 2000]
    if h.empty:
        return _empty("No measured cost years to show yet")

    fig = make_subplots(rows=1, cols=2, column_widths=[1.35, 1.0],
                        horizontal_spacing=0.14,
                        specs=[[{}, {"secondary_y": True}]],
                        subplot_titles=["What each source cost to buy",
                                        "What one unit cost"])
    years = h["calendar_year"].values

    # A stacked area cannot hold a gap, so the bill is drawn only for the years
    # in which every shown source has a reading -- and a source the engine never
    # prices at all is left off the stack instead of being given a zero bill.
    shown = [(t, _ccol(t)) for t in TECHS_SHOWN
             if _ccol(t) in h.columns and h[_ccol(t)].notna().any()]
    if shown:
        cols = [c for _, c in shown]
        keep = h[cols].notna().all(axis=1)
        h = h[keep]
        years = h["calendar_year"].values

    for tech, col in shown:
        fig.add_trace(go.Scatter(
            x=years, y=h[col] * factor_cost, name=tech, mode="lines",
            stackgroup="one", line=dict(width=0.9, color=TECH_COLORS[tech]),
            fillcolor=TECH_COLORS[tech],
            hovertemplate=f"{tech}: %{{y:,.2f}} {unit_cost}<extra></extra>",
        ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=years, y=h["avg_usd_per_mwh"], name="Average price paid", mode="lines",
        line=dict(color=AMBER, width=2.6),
        hovertemplate="Average price: %{y:,.1f} US$/MWh<extra></extra>",
        connectgaps=False,
    ), row=1, col=2, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=years, y=h["fuel_cost_share_pct"], name="Fuel part of the bill", mode="lines",
        line=dict(color=RED, width=2.0, dash="dot"),
        hovertemplate="Fuel part: %{y:,.1f}% of the bill<extra></extra>",
        connectgaps=False,
    ), row=1, col=2, secondary_y=True)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Bill to producers ({unit_cost})", row=1, col=1)
    fig.update_yaxes(title_text="US$ per unit (MWh)", row=1, col=2, secondary_y=False)
    fig.update_yaxes(title_text="Fuel part of bill (%)", row=1, col=2, secondary_y=True)
    return _dark_theme(fig, height=400, x_title=None)


# ── V2: the forecast bill ────────────────────────────────────────────────────

def visual2_forecast_bill(hist: pd.DataFrame, fc: pd.DataFrame, cases: List[str],
                          case_words: dict, unit_cost: str = "USD bn",
                          factor_cost: float = 1.0) -> go.Figure:
    """The bill for the reported years, then one forecast path per build-out case."""
    if fc.empty:
        return _empty("No forecast paths to show -- check the years asked for")

    fig = go.Figure()
    h = hist[hist["calendar_year"] >= 2000]
    fig.add_trace(go.Scatter(
        x=h["calendar_year"], y=h["cost_total_usd"] * factor_cost,
        name="Years already reported", mode="lines",
        line=dict(color=LIGHT, width=2.8),
        hovertemplate="So far: %{y:,.2f} " + unit_cost + "<extra></extra>",
        connectgaps=False,
    ))

    # Shade the gap between the cheapest and dearest case when both are drawn
    order = ["Minimum RE", "Reference", "RE 50%"]
    drawn = sorted([c for c in cases if c in order], key=order.index)
    if "Minimum RE" in drawn and "RE 50%" in drawn:
        years = sorted(set(fc["calendar_year"]))
        lo = fc[fc["scenario"] == "RE 50%"].set_index("calendar_year")["cost_total_usd"]
        hi = fc[fc["scenario"] == "Minimum RE"].set_index("calendar_year")["cost_total_usd"]
        fig.add_trace(go.Scatter(
            x=years, y=[float(hi.get(y, float("nan"))) * factor_cost for y in years],
            mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
            fillcolor="rgba(148, 163, 184, 0.10)"))
        fig.add_trace(go.Scatter(
            x=years, y=[float(lo.get(y, float("nan"))) * factor_cost for y in years],
            mode="lines", line=dict(width=0), fill="tonexty",
            showlegend=False, hoverinfo="skip"))

    for case in drawn:
        sub = fc[fc["scenario"] == case].sort_values("calendar_year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["calendar_year"], y=sub["cost_total_usd"] * factor_cost,
            name=case_words.get(case, case), mode="lines",
            line=dict(color=COST_SCENARIO_COLORS.get(case, BLUE), width=2.4,
                      dash="dash"),
            hovertemplate=f"{case_words.get(case, case)}: %{{y:,.2f}} "
                          f"{unit_cost}<extra></extra>",
            connectgaps=False,
        ))

    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text=f"Bill to producers ({unit_cost})")
    return _boundary(_dark_theme(fig, height=420, x_title=None))


# ── V3: where the money goes ────────────────────────────────────────────────

def visual3_where_money_goes(labels: List[str], measures: List[str],
                             values: List[float], unit_cost: str = "USD bn") -> go.Figure:
    """Step by step, what adds to the bill and what takes away, between the
    last reported year and the horizon year."""
    if not labels or not values:
        return _empty("Nothing to walk yet")

    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measures, x=labels, y=values,
        increasing=dict(marker=dict(color="rgba(239, 68, 68, 0.72)",
                                    line=dict(color=RED, width=1))),
        decreasing=dict(marker=dict(color="rgba(16, 185, 129, 0.72)",
                                    line=dict(color=GREEN, width=1))),
        totals=dict(marker=dict(color="rgba(245, 158, 11, 0.78)",
                                line=dict(color=AMBER, width=1.4))),
        connector=dict(line=dict(color="#475569", width=1.2, dash="dot")),
        textposition="outside", textfont=dict(size=9.5, color=LIGHT),
        texttemplate="%{delta:+,.2f}",
        hovertemplate="%{x}: %{y:,.2f} " + unit_cost + "<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="What changed (biggest additions first)",
                    categoryorder="trace", tickfont=dict(size=10, color=_TICK))
    fig.update_yaxes(title_text=f"Bill to producers ({unit_cost})")
    return _dark_theme(fig, height=420, x_title=None)


# ── V4: what one unit costs ─────────────────────────────────────────────────

def visual4_unit_price(hist: pd.DataFrame, fc: pd.DataFrame, cases: List[str],
                       case_words: dict) -> go.Figure:
    """The average price paid per unit: reported years, then one path per case."""
    h = hist[hist["calendar_year"] >= 2000]
    if h.empty:
        return _empty("No reported prices to show yet")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=h["calendar_year"], y=h["avg_usd_per_mwh"], name="Years already reported",
        mode="lines", line=dict(color=LIGHT, width=2.6),
        hovertemplate="So far: %{y:,.1f} US$/MWh<extra></extra>",
        connectgaps=False,
    ))
    for case in cases:
        sub = fc[fc["scenario"] == case].sort_values("calendar_year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["calendar_year"], y=sub["avg_usd_per_mwh"],
            name=case_words.get(case, case), mode="lines",
            line=dict(color=COST_SCENARIO_COLORS.get(case, BLUE), width=2.2,
                      dash="dash"),
            hovertemplate=f"{case_words.get(case, case)}: %{{y:,.1f}} "
                          f"US$/MWh<extra></extra>",
            connectgaps=False,
        ))

    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Average price paid (US$ per unit)")
    return _boundary(_dark_theme(fig, height=380, x_title=None))


# ── V5: fuel prices and how far to trust the guess ──────────────────────────

_MODEL_WORDS = {
    "GDP-Driver": "Growth tied to the economy",
    "Trend": "Growth carried on from past years",
}


def visual5_fuel_and_trust(sensitivity: pd.DataFrame, backtest: dict,
                           fuel_labels: List[str], unit_cost: str = "USD bn",
                           factor_cost: float = 1.0) -> go.Figure:
    """Left: what the fuel-price assumption does to the forecast bill.
    Right: how far the model was off on years it had not been shown."""
    fig = make_subplots(rows=1, cols=2, column_widths=[1.1, 1.0],
                        horizontal_spacing=0.12,
                        subplot_titles=["If fuel prices rise faster or slower",
                                        "How far the model missed, year by year"])

    band_colors = [GREEN, BLUE, RED]
    if sensitivity is not None and not sensitivity.empty:
        sens = sensitivity.sort_values("calendar_year")
        years = sens["calendar_year"].values
        cost_cols = [c for c in sens.columns if c != "calendar_year"]
        for idx, col in enumerate(cost_cols):
            label = (fuel_labels[idx] if idx < len(fuel_labels)
                     else col.replace("cost_", "").replace("_usd", ""))
            is_base = idx == 1
            fig.add_trace(go.Scatter(
                x=years, y=sens[col] * factor_cost, name=label, mode="lines",
                line=dict(color=band_colors[idx % 3], width=2.6 if is_base else 1.6,
                          dash=None if is_base else "dash"),
                # Filling each half against the line before it shades the whole
                # band from the slowest fuel rise to the fastest one.
                fill="tonexty" if idx in (1, 2) else None,
                fillcolor="rgba(148, 163, 184, 0.10)" if idx in (1, 2) else None,
                hovertemplate=f"{label}: %{{y:,.2f}} {unit_cost}<extra></extra>",
                connectgaps=False,
            ), row=1, col=1)

    metrics = (backtest or {}).get("table", pd.DataFrame())
    if metrics is not None and not metrics.empty:
        names = [_MODEL_WORDS.get(str(m), str(m)) for m in metrics["model"]]
        errors = [float(v) for v in metrics["mape_pct"]]
        best = errors.index(min(errors)) if errors and all(
            e == e for e in errors) else -1
        fig.add_trace(go.Bar(
            x=names, y=errors,
            name="Average error",
            marker_color=[GREEN if i == best else SLATE for i in range(len(errors))],
            text=[f"{e:.1f}%" for e in errors], textposition="outside",
            hovertemplate="%{x}: %{y:.1f}% off<extra>Average error</extra>",
        ), row=1, col=2)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Model tried", row=1, col=2)
    fig.update_yaxes(title_text=f"Forecast bill ({unit_cost})", row=1, col=1)
    fig.update_yaxes(title_text="Average error (%)", range=[0, max(
        12.0, *(float(v) for v in metrics["mape_pct"])) * 1.35]
        if metrics is not None and not metrics.empty else [0, 12],
        row=1, col=2)
    return _dark_theme(fig, height=400, x_title=None)
