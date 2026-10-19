"""
dashboards/q7_forecast_cost/charts.py -- visuals for Forecasted Power Producer Cost (question 7).

Presentation-only ("dumb") figures: every value is pre-computed by the
core/cost_forecast.py engine and arrives fully formed.

V1  Historical producer cost bill           -- stacked cost by technology + blended price
V2  Fuel exposure, sensitivity & backtest   -- fuel-price band + hold-out validation
V3a Cumulative cost avoided                 -- annual delta bars + cumulative line
V3b Unit-cost learning curves               -- blended US$/MWh per deployment case
V4  Implied unit-price heat-map             -- technology × year purchase tariff matrix
V5  Forecasted cost by deployment case      -- Minimum RE / Reference / RE 50% fan
V6  Cost bridge waterfall                   -- what pushes the 2024 bill to the horizon
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.cost_forecast import (
    COST_SCENARIO_COLORS,
    COST_TECHS,
    HISTORY_END,
    TECH_COLORS,
)

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8D0DA"


def _dark_theme(fig, height: int = 380, y_title: Optional[str] = None,
                legend_h: bool = True, x_title: Optional[str] = "Year"):
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
    # Only assign titles when non-None so per-panel titles set manually are
    # never cleared by the shared theme.
    if x_title:
        fig.update_xaxes(title=dict(text=x_title, font=dict(size=11.5, color=_TEXT)))
    if y_title:
        fig.update_yaxes(title=dict(text=y_title, font=dict(size=11.5, color=_TEXT)))
    return fig


def _boundary(fig, year: int = HISTORY_END, text: str = "Reported ◀ | ▶ Modelled"):
    fig.add_vline(x=year + 0.5, line=dict(color="#64748B", width=1.3, dash="dash"))
    fig.add_annotation(
        x=year + 0.5, y=0.04, yref="paper", yanchor="bottom",
        text=text, showarrow=False,
        font=dict(size=9.5, color="#94A3B8", family="Inter, sans-serif"),
        bgcolor="rgba(20, 23, 30, 0.90)",
        bordercolor="#334155", borderwidth=1, borderpad=3,
        xanchor="center",
    )
    return fig


def _ccol(tech: str) -> str:
    """Cost column key emitted by the engine for one technology."""
    return f"cost_{tech.lower().replace(' ', '')}_usd"


# ═════════════════ V1 -- historical producer cost bill ═══════════════════════

def visual1_historical_cost_bill(
    hist: pd.DataFrame,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
) -> go.Figure:
    """Left: reported purchase-cost bill stacked by technology.
    Right: blended average buying price (US$/MWh) vs fuel-driven share of the bill."""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[1.35, 1.0],
        horizontal_spacing=0.14,
        specs=[[{}, {"secondary_y": True}]],
    )
    h = hist[hist["calendar_year"] >= 2002]
    years = h["calendar_year"].values

    for tech in COST_TECHS:
        col = _ccol(tech)
        if col not in h.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=years, y=h[col].fillna(0.0) * factor_cost, name=tech, mode="lines",
                stackgroup="bill", line=dict(width=0.9, color=TECH_COLORS[tech]),
                fillcolor=TECH_COLORS[tech], legendgroup=tech,
                hovertemplate=f"{tech}: %{{y:,.2f}} {unit_cost}<extra></extra>",
            ),
            row=1, col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=years, y=h["avg_usd_per_mwh"], name="Blended price", mode="lines",
            line=dict(color="#F59E0B", width=2.6),
            hovertemplate="Blended: %{y:,.1f} US$/MWh<extra></extra>",
        ),
        row=1, col=2, secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=h["fuel_cost_share_pct"], name="Fuel-cost share", mode="lines",
            line=dict(color="#EF4444", width=2.0, dash="dot"),
            hovertemplate="Fuel share: %{y:,.1f} % of bill<extra></extra>",
        ),
        row=1, col=2, secondary_y=True,
    )

    fig.update_xaxes(title_text="Calendar Year", row=1, col=1)
    fig.update_xaxes(title_text="Calendar Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Cost Purchased ({unit_cost})", row=1, col=1)
    fig.update_yaxes(title_text="US$/MWh", row=1, col=2, secondary_y=False)
    fig.update_yaxes(title_text="% of Bill", row=1, col=2, secondary_y=True)
    _boundary(fig)
    return _dark_theme(fig, height=400, x_title=None, legend_h=True)


# ═════════════ V2 -- fuel exposure, sensitivity & backtest ═══════════════════

def visual2_sensitivity_backtest(
    sensitivity: pd.DataFrame,
    backtest: dict,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
) -> go.Figure:
    """Left: Reference-case cost band under low / base / high fuel escalation.
    Right: hold-out backtest (2021-2024) of modelled vs reported cost bill."""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[1.1, 1.0],
        horizontal_spacing=0.12,
    )

    band_colors = ["#10B981", "#00A6FB", "#EF4444"]
    if sensitivity is not None and not sensitivity.empty:
        sens = sensitivity.sort_values("calendar_year")
        years = sens["calendar_year"].values
        cost_cols = [c for c in sens.columns if c != "calendar_year"]
        for idx, col in enumerate(cost_cols):
            label = col.replace("cost_", "").replace("_usd", "").replace("Fuel ", "Fuel ")
            is_base = "Base" in label
            fig.add_trace(
                go.Scatter(
                    x=years, y=sens[col] * factor_cost, name=label, mode="lines",
                    line=dict(color=band_colors[idx % 3],
                              width=2.6 if is_base else 1.6,
                              dash=None if is_base else "dash"),
                    fill=("tonexty" if idx == 2 else None),
                    fillcolor="rgba(0, 166, 251, 0.10)" if idx == 2 else None,
                    hovertemplate=f"{label}: %{{y:,.2f}} {unit_cost}<extra></extra>",
                ),
                row=1, col=1,
            )

    paths = (backtest or {}).get("paths", pd.DataFrame())
    if paths is not None and not paths.empty:
        fig.add_trace(
            go.Bar(
                x=paths["calendar_year"], y=paths["actual"] * factor_cost,
                name="Reported", marker=dict(color="rgba(203, 213, 225, 0.55)",
                                             line=dict(color="#CBD5E1", width=1)),
                hovertemplate="Reported: %{y:,.2f} " + unit_cost + "<extra></extra>",
            ),
            row=1, col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=paths["calendar_year"], y=paths["predicted_driver"] * factor_cost,
                name="GDP-Driver", mode="lines+markers",
                line=dict(color="#F59E0B", width=2.4),
                hovertemplate="Driver: %{y:,.2f} " + unit_cost + "<extra></extra>",
            ),
            row=1, col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=paths["calendar_year"], y=paths["predicted_trend"] * factor_cost,
                name="Trend", mode="lines+markers",
                line=dict(color="#A78BFA", width=2.2, dash="dot"),
                hovertemplate="Trend: %{y:,.2f} " + unit_cost + "<extra></extra>",
            ),
            row=1, col=2,
        )

    fig.update_xaxes(title_text="Calendar Year", row=1, col=1)
    fig.update_xaxes(title_text="Hold-Out Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Reference Cost ({unit_cost})", row=1, col=1)
    fig.update_yaxes(title_text=f"Cost Bill ({unit_cost})", row=1, col=2)
    return _dark_theme(fig, height=400, x_title=None)


# ══════════════ V3a -- cumulative cost avoided (RE 50%) ══════════════════════

def visual3a_avoided_cost(
    avoided: pd.DataFrame,
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
) -> go.Figure:
    """Annual producer-cost saved (bars) and the running cumulative saving (line)."""
    fig = go.Figure()
    if avoided is None or avoided.empty:
        return _dark_theme(fig, height=380, y_title=f"Cost ({unit_cost})")
    years = avoided["calendar_year"].values
    fig.add_trace(
        go.Bar(
            x=years, y=avoided["delta_usd"] * factor_cost, name="Annual saving",
            marker=dict(color="rgba(16, 185, 129, 0.55)",
                        line=dict(color="#10B981", width=1)),
            hovertemplate="Annual: %{y:,.2f} " + unit_cost + "<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=avoided["cumulative_usd"] * factor_cost, name="Cumulative",
            mode="lines", line=dict(color="#22D3EE", width=2.8),
            hovertemplate="Cumulative: %{y:,.2f} " + unit_cost + "<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis2=dict(title=dict(text=f"Cumulative ({unit_cost})",
                               font=dict(size=11.5, color=_TEXT)),
                    overlaying="y", side="right", showgrid=False, zeroline=False,
                    tickfont=dict(size=11, color=_TICK)),
    )
    fig.data[1].yaxis = "y2"
    fig.update_xaxes(title_text="Calendar Year")
    fig.update_yaxes(title_text=f"Annual Saving ({unit_cost})")
    return _dark_theme(fig, height=380, x_title=None)


# ═══════════════ V3b -- blended price learning curves ════════════════════════

def visual3b_learning_curves(
    hist: pd.DataFrame,
    fc: pd.DataFrame,
    scenarios: List[str],
) -> go.Figure:
    """Blended purchase price (US$/MWh): reported history + one path per deployment case."""
    fig = go.Figure()
    h = hist[hist["calendar_year"] >= 2002]
    fig.add_trace(
        go.Scatter(
            x=h["calendar_year"], y=h["avg_usd_per_mwh"], name="Reported",
            mode="lines", line=dict(color="#E2E8F0", width=2.6),
            hovertemplate="Reported: %{y:,.1f} US$/MWh<extra></extra>",
        )
    )
    for sc in scenarios:
        sub = fc[fc["scenario"] == sc].sort_values("calendar_year")
        if sub.empty:
            continue
        colr = COST_SCENARIO_COLORS.get(sc, "#00A6FB")
        fig.add_trace(
            go.Scatter(
                x=sub["calendar_year"], y=sub["avg_usd_per_mwh"], name=sc,
                mode="lines", line=dict(color=colr, width=2.2, dash="dash"),
                hovertemplate=f"{sc}: %{{y:,.1f}} US$/MWh<extra></extra>",
            )
        )
    fig.update_xaxes(title_text="Calendar Year")
    fig.update_yaxes(title_text="Blended Purchase Price (US$/MWh)")
    _boundary(fig)
    return _dark_theme(fig, height=380, x_title=None)


# ════════════════ V4 -- implied unit-price heat-map ═════════════════════════

def visual4_price_heatmap(
    ucost_table: pd.DataFrame,
) -> go.Figure:
    """Technology × year matrix of implied purchase tariffs (US$/MWh).
    Pre-computed by the engine's unit_cost_table; the picture is purely render."""
    fig = go.Figure()
    if ucost_table is None or ucost_table.empty:
        return _dark_theme(fig, height=360, y_title="Technology")
    techs = [t for t in COST_TECHS if t in ucost_table.columns]
    z = [ucost_table[t].values for t in techs]
    fig.add_trace(
        go.Heatmap(
            z=z,
            x=ucost_table["calendar_year"].values,
            y=techs,
            colorscale=[[0.0, "#0B1220"], [0.30, "#0E7490"],
                        [0.55, "#0284C7"], [0.78, "#F59E0B"], [1.0, "#EF4444"]],
            colorbar=dict(title=dict(text="US$/MWh",
                                     font=dict(size=11, color=_TEXT)),
                          tickfont=dict(size=10.5, color=_TICK),
                          thickness=13, len=0.92, outlinewidth=0),
            hovertemplate="%{y} · %{x}: %{z:,.1f} US$/MWh<extra></extra>",
        )
    )
    fig.update_xaxes(title_text="Calendar Year", dtick=4)
    fig.update_yaxes(title_text="Technology", autorange="reversed")
    return _dark_theme(fig, height=360, x_title=None, legend_h=True)


# ═══════════ V5 -- forecasted producer cost by deployment case ═══════════════

def visual5_scenario_fan(
    hist: pd.DataFrame,
    fc: pd.DataFrame,
    scenarios: List[str],
    unit_cost: str = "USD bn",
    factor_cost: float = 1.0,
) -> go.Figure:
    """Total purchase-cost fan: reported bill + one trajectory per deployment case,
    with the Minimum RE -> RE 50% uncertainty envelope shaded."""
    fig = go.Figure()
    h = hist[hist["calendar_year"] >= 2002]
    fig.add_trace(
        go.Scatter(
            x=h["calendar_year"], y=h["cost_total_usd"] * factor_cost,
            name="Reported bill", mode="lines",
            line=dict(color="#E2E8F0", width=2.8),
            hovertemplate="Reported: %{y:,.2f} " + unit_cost + "<extra></extra>",
        )
    )

    # Shade the spread between the two bookend pathways when both are drawn
    order = {sc: i for i, sc in enumerate(["Minimum RE", "Reference", "RE 50%"])}
    drawn = sorted([s for s in scenarios if s in order], key=lambda s: order[s])
    if "Minimum RE" in drawn and "RE 50%" in drawn:
        yr = sorted(set(fc["calendar_year"]))
        lo = fc[fc["scenario"] == "Minimum RE"].set_index("calendar_year")["cost_total_usd"]
        hi = fc[fc["scenario"] == "RE 50%"].set_index("calendar_year")["cost_total_usd"]
        band_lo = [float(lo.get(y, float("nan"))) * factor_cost for y in yr]
        band_hi = [float(hi.get(y, float("nan"))) * factor_cost for y in yr]
        fig.add_trace(
            go.Scatter(x=yr, y=band_hi, mode="lines", line=dict(width=0),
                       showlegend=False, hoverinfo="skip",
                       fillcolor="rgba(148, 163, 184, 0.10)"),
        )
        fig.add_trace(
            go.Scatter(x=yr, y=band_lo, mode="lines", line=dict(width=0),
                       fill="tonexty", showlegend=False, hoverinfo="skip"),
        )

    for sc in drawn:
        sub = fc[fc["scenario"] == sc].sort_values("calendar_year")
        if sub.empty:
            continue
        colr = COST_SCENARIO_COLORS.get(sc, "#00A6FB")
        fig.add_trace(
            go.Scatter(
                x=sub["calendar_year"], y=sub["cost_total_usd"] * factor_cost,
                name=sc, mode="lines",
                line=dict(color=colr, width=2.4, dash="dash"),
                hovertemplate=f"{sc}: %{{y:,.2f}} {unit_cost}<extra></extra>",
            )
        )

    fig.update_xaxes(title_text="Calendar Year")
    fig.update_yaxes(title_text=f"Total Producer Cost ({unit_cost})")
    _boundary(fig)
    return _dark_theme(fig, height=420, x_title=None)


# ═══════════════════ V6 -- cost bridge waterfall ═════════════════════════

def visual6_cost_bridge(
    labels: List[str],
    measures: List[str],
    values: List[float],
    unit_cost: str = "USD bn",
) -> go.Figure:
    """Bridge from the reported 2024 producer bill to the modelled horizon bill,
    decomposed technology by technology. Steps arrive pre-computed."""
    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            increasing=dict(marker=dict(color="rgba(239, 68, 68, 0.72)",
                                        line=dict(color="#EF4444", width=1))),
            decreasing=dict(marker=dict(color="rgba(16, 185, 129, 0.72)",
                                        line=dict(color="#10B981", width=1))),
            totals=dict(marker=dict(color="rgba(245, 158, 11, 0.78)",
                                    line=dict(color="#F59E0B", width=1.4))),
            connector=dict(line=dict(color="#475569", width=1.2, dash="dot")),
            textposition="outside",
            textfont=dict(size=9.5, color="#CBD5E1"),
            texttemplate="%{delta:+,.2f}",
            hovertemplate="%{x}: %{y:,.2f} " + unit_cost + "<extra></extra>",
        )
    )
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="Bridge Step (growth drivers first)",
                     categoryorder="trace",
                     tickfont=dict(size=10, color=_TICK))
    fig.update_yaxes(title_text=f"Producer Cost Bill ({unit_cost})")
    return _dark_theme(fig, height=420, x_title=None)
