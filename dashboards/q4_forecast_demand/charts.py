"""
charts.py -- visuals for the Forecasted Energy Demand dashboard (question 4).

Five figures, all of them part of the answer to "what will demand be?":

V1  Demand so far        -- electricity, gas and total energy, in real terms
                            and as growth from the first year
V2  Scenario paths       -- the low, planned and high demand futures
V3  What moves demand    -- demand next to income and population
V4  Sector mix           -- which sectors use the electricity
V5  Trust in the guess   -- how far off the model was on years it had not seen

Every forecast year is drawn dashed and every year we measured is drawn solid,
so a guessed point is never mistaken for a real one.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.demand_forecast import (
    SCENARIO_COLORS,
    SCENARIO_ORDER,
    observed_path,
    series_spec,
)

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8CDD6"


def _dark_theme(fig, height: int = 370, y_title: Optional[str] = None,
                y2_title: Optional[str] = None, legend_h: bool = True,
                x_title: Optional[str] = "Year"):
    legend_cfg = (
        dict(orientation="h", y=-0.26, x=0.5, xanchor="center",
             font=dict(size=10.5, color=_TEXT))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color=_TEXT))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=62, r=46, t=45, b=64),
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
    # Only set the title when one is supplied -- passing title=None would wipe
    # the per-panel titles that multi-axis charts set themselves before this call.
    if x_title:
        fig.update_xaxes(title=dict(text=x_title, font=dict(size=11.5, color=_TEXT)))
    if y_title:
        fig.update_yaxes(title=dict(text=y_title, font=dict(size=11.5, color=_TEXT)))
    if y2_title:
        fig.update_layout(yaxis2=dict(
            title=dict(text=y2_title, font=dict(size=11.5, color=_TEXT)),
            tickfont=dict(size=11, color=_TICK),
            overlaying="y", side="right", showgrid=False, zeroline=False))
    return fig


def _empty_fig(msg: str = "No data available for this selection"):
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=13, color=_TICK))
    return _dark_theme(fig)


def _boundary(fig, year: Optional[int], text: str = "Measured here ◀ | ▶ Forecast"):
    if year is None:
        return fig
    fig.add_vline(x=year + 0.5, line=dict(color="#64748B", width=1.3, dash="dash"))
    fig.add_annotation(x=year + 0.5, y=1.0, yref="paper", yanchor="bottom",
                       text=text, showarrow=False, font=dict(size=9.5, color="#94A3B8"),
                       bgcolor="rgba(20,23,30,0.85)", borderpad=3, xanchor="center")
    return fig


# ═════════════════ V1: demand so far ═════════════════════════════════════════

def visual1_history_trends(hist: pd.DataFrame, keys: Sequence[str],
                           year_range: tuple, unit_energy: str = "TOE",
                           break_year: Optional[int] = None,
                           factor: float = 1.0):
    """How much demand there really was each year, and how it has grown."""
    if hist is None or hist.empty:
        return _empty_fig()

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Energy used each year", "Growth from the first year"))
    plotted = 0
    for key in keys:
        spec = series_spec(key)
        path = observed_path(hist, key)
        path = path[(path["calendar_year"] >= year_range[0])
                    & (path["calendar_year"] <= year_range[1])]
        if path.empty:
            continue
        colour = spec["color"]
        values = path["value"].to_numpy(dtype=float) * factor
        fig.add_trace(go.Scatter(
            x=path["calendar_year"], y=values, mode="lines+markers", name=spec["short"],
            line=dict(color=colour, width=2.6),
            marker=dict(size=6, color=colour, line=dict(width=1, color="#1A1D24")),
            hovertemplate=f"{spec['short']}<br>%{{x}}: <b>%{{y:,.0f}}</b><extra></extra>",
            connectgaps=False,
        ), row=1, col=1)

        if values[0]:
            indexed = values / values[0] * 100.0
            fig.add_trace(go.Scatter(
                x=path["calendar_year"], y=indexed, mode="lines", name=spec["short"],
                line=dict(color=colour, width=2.2, dash="dot"), showlegend=False,
                hovertemplate=f"{spec['short']} index<br>%{{x}}: <b>%{{y:,.1f}}</b><extra></extra>",
                connectgaps=False,
            ), row=1, col=2)
        plotted += 1

    if not plotted:
        return _empty_fig()

    fig.add_hline(y=100, line=dict(color="#475569", width=1, dash="dot"), row=1, col=2)
    _boundary(fig, break_year, "Data basis changes in 2019")
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Demand ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text="Growth (first year = 100)", row=1, col=2)
    return _dark_theme(fig, height=380, x_title=None)


# ════════════ V2: the three demand paths to the horizon ══════════════════════

def visual2_scenario_fans(bands: Dict[str, pd.DataFrame], hist: pd.DataFrame,
                          keys: Sequence[str], scenarios: Sequence[str],
                          unit_energy: str = "TOE", factor: float = 1.0,
                          break_year: Optional[int] = None):
    """Low / Base / High demand paths per series, with the years we measured."""
    if hist is None or hist.empty:
        return _empty_fig()

    keys = list(keys)
    fig = make_subplots(rows=1, cols=len(keys),
                        subplot_titles=[series_spec(k)["short"] for k in keys])
    for index, key in enumerate(keys, start=1):
        spec = series_spec(key)
        path = observed_path(hist, key)
        if not path.empty:
            fig.add_trace(go.Scatter(
                x=path["calendar_year"], y=path["value"] * factor,
                mode="lines+markers", name="Measured",
                marker=dict(size=4, color="#E2E8F0"),
                line=dict(color="#E2E8F0", width=2.4),
                legendgroup="reported", showlegend=index == 1,
                hovertemplate="Measured<br>%{x}: <b>%{y:,.0f}</b><extra></extra>",
                connectgaps=False,
            ), row=1, col=index)
            anchor_year = int(path["calendar_year"].iloc[-1])
            anchor_value = float(path["value"].iloc[-1]) * factor
        else:
            anchor_year, anchor_value = None, None

        band = bands.get(key)
        if band is not None and not band.empty and anchor_year is not None:
            x = [anchor_year] + [int(y) for y in band["calendar_year"]]
            # shaded Low-High envelope
            if "High" in scenarios and "Low" in scenarios:
                high = [anchor_value] + list(band["High"].to_numpy(dtype=float) * factor)
                low = [anchor_value] + list(band["Low"].to_numpy(dtype=float) * factor)
                fig.add_trace(go.Scatter(x=x, y=high, mode="lines",
                                         line=dict(color="rgba(148,163,184,0.35)", width=1),
                                         showlegend=False, hoverinfo="skip"),
                              row=1, col=index)
                fig.add_trace(go.Scatter(x=x, y=low, mode="lines", fill="tonexty",
                                         fillcolor="rgba(148,163,184,0.12)",
                                         line=dict(color="rgba(148,163,184,0.35)", width=1),
                                         showlegend=False, hoverinfo="skip"),
                              row=1, col=index)
            for scenario in SCENARIO_ORDER:
                if scenario not in scenarios or scenario not in band.columns:
                    continue
                y = [anchor_value] + list(band[scenario].to_numpy(dtype=float) * factor)
                fig.add_trace(go.Scatter(
                    x=x, y=y, mode="lines+markers", name=scenario,
                    line=dict(color=SCENARIO_COLORS[scenario], width=2.2, dash="dash"),
                    marker=dict(size=4, color=SCENARIO_COLORS[scenario]),
                    legendgroup=scenario, showlegend=index == 1,
                    hovertemplate=f"{scenario}<br>%{{x}}: <b>%{{y:,.0f}}</b><extra></extra>",
                    connectgaps=False,
                ), row=1, col=index)
        _boundary(fig, break_year, "Measured here ◀ | ▶ Forecast")
        fig.update_xaxes(title_text="Year", row=1, col=index)

    fig.update_yaxes(title_text=f"Demand ({unit_energy})", row=1, col=1)
    return _dark_theme(fig, height=380, x_title=None)


# ═════════════════ V3: what moves demand ═════════════════════════════════════

def visual3_drivers(hist: pd.DataFrame, model: dict, key: str, year_range: tuple,
                    unit_energy: str = "TOE", factor: float = 1.0):
    """
    Left: demand next to the economy and the population, all on one growth scale.
    Right: the link the forecast is built on -- demand per head against income
    per head, with the fitted curve drawn through the points.
    """
    spec = series_spec(key)
    if hist is None or hist.empty or spec["column"] not in hist.columns:
        return _empty_fig()

    window = hist[(hist["calendar_year"] >= year_range[0])
                  & (hist["calendar_year"] <= year_range[1])].copy()
    window = window.dropna(subset=[spec["column"], "gdp_real_index", "population"])
    if window.empty:
        return _empty_fig()

    fig = make_subplots(rows=1, cols=2, specs=[[{"secondary_y": True}, {}]],
                        subplot_titles=("Demand next to what drives it",
                                        "Income per head vs demand per head"))

    demand = window[spec["column"]].to_numpy(dtype=float)
    gdp_index = window["gdp_real_index"].to_numpy(dtype=float)
    pop = window["population"].to_numpy(dtype=float)
    years = window["calendar_year"].to_numpy(dtype=int)

    demand_index = demand / demand[0] * 100.0
    gdp_norm = gdp_index / gdp_index[0] * 100.0
    pop_norm = pop / pop[0] * 100.0

    fig.add_trace(go.Scatter(
        x=years, y=demand_index, mode="lines+markers", name=f"{spec['short']}",
        line=dict(color=spec["color"], width=3),
        marker=dict(size=6, color=spec["color"]),
        hovertemplate=f"{spec['short']}<br>%{{x}}: <b>%{{y:,.1f}}</b><extra></extra>",
        connectgaps=False,
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=years, y=gdp_norm, mode="lines+markers", name="Economy (GDP)",
        line=dict(color="#F472B6", width=2.4),
        marker=dict(size=5, color="#F472B6"),
        hovertemplate="Economy (GDP)<br>%{x}: <b>%{y:,.1f}</b><extra></extra>",
        connectgaps=False,
    ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(
        x=years, y=pop_norm, mode="lines+markers", name="Population",
        line=dict(color="#94A3B8", width=2, dash="dot"),
        marker=dict(size=4, color="#94A3B8"),
        hovertemplate="Population<br>%{x}: <b>%{y:,.1f}</b><extra></extra>",
        connectgaps=False,
    ), row=1, col=1, secondary_y=True)

    # ── right: per-capita relationship ─────────────────────────────────────
    rgdppc = (window["real_gdp_per_capita"].to_numpy(dtype=float))
    per_capita = (demand / pop) * factor * 1e6      # per million people, readable
    valid = np.isfinite(rgdppc) & np.isfinite(per_capita) & (rgdppc > 0)
    rgdppc, per_capita = rgdppc[valid], per_capita[valid]

    fig.add_trace(go.Scatter(
        x=rgdppc, y=per_capita, mode="markers", name="Years we measured",
        marker=dict(size=9, color=spec["color"], line=dict(width=1, color="#1A1D24")),
        text=[str(y) for y in years[valid]],
        hovertemplate="%{text}<br>income per head: %{x:,.0f}<br>demand per head: <b>%{y:,.1f}</b><extra></extra>",
    ), row=1, col=2)

    eps = model.get("elasticity_income")
    r2 = model.get("r2_per_capita")
    if eps is not None and np.isfinite(eps) and len(rgdppc) >= 2:
        grid = np.linspace(rgdppc.min(), rgdppc.max(), 60)
        curve = per_capita[0] * (grid / rgdppc[0]) ** float(eps)
        fig.add_trace(go.Scatter(
            x=grid, y=curve, mode="lines", name="Fitted link",
            line=dict(color="#F472B6", width=2.2, dash="dash"), hoverinfo="skip",
        ), row=1, col=2)
        annotation = (f"Demand per head rises with income per head<br>"
                      f"fit quality R² = {float(r2):.3f}" if r2 is not None and np.isfinite(r2)
                      else "Demand per head rises with income per head")
        fig.add_annotation(x=0.04, y=0.96, xref="x2 domain", yref="y2 domain",
                           text=annotation, showarrow=False, align="left",
                           font=dict(size=11, color="#E2E8F0"),
                           bgcolor="rgba(35,40,48,0.9)", borderpad=6)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_yaxes(title_text="Demand (first year = 100)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Economy / people (first year = 100)", showgrid=False,
                     row=1, col=1, secondary_y=True)
    fig.update_xaxes(title_text="Income per head (index)", row=1, col=2)
    fig.update_yaxes(title_text=f"Demand per million people ({unit_energy})", row=1, col=2)
    return _dark_theme(fig, height=400, x_title=None)


# ═════════════════ V4: who uses the electricity ══════════════════════════════

def visual4_sector_mix(sectors: dict, horizon: int, unit_elec: str = "GWh",
                       factor: float = 1.0, scenario: str = "Base"):
    """Electricity use by end-use sector: the last measured year vs the horizon."""
    history = sectors.get("history") if sectors else None
    projection = sectors.get("projection") if sectors else None
    if history is None or history.empty:
        return _empty_fig("No sector data to show")

    base_year = sectors.get("base_year")
    reported = (history[history["calendar_year"] == base_year]
                .groupby("key")["value"].sum() * factor)
    future = pd.Series(dtype=float)
    if projection is not None and not projection.empty:
        subset = projection[(projection["scenario"] == scenario)
                            & (projection["calendar_year"] == int(horizon))]
        future = subset.groupby("key")["value"].sum() * factor

    order = reported.sort_values(ascending=True).index.tolist()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=order, x=[reported.get(k, 0.0) for k in order], orientation="h",
        name=f"Measured {base_year}", marker=dict(color="#00A6FB"),
        hovertemplate="%{y}<br>measured: <b>%{x:,.0f}</b><extra></extra>",
    ))
    if not future.empty:
        fig.add_trace(go.Bar(
            y=order, x=[future.get(k, 0.0) for k in order], orientation="h",
            name=f"Forecast {int(horizon)}",
            marker=dict(color="#10B981", pattern=dict(shape="/", fgcolor="rgba(255,255,255,0.35)")),
            hovertemplate="%{y}<br>forecast: <b>%{x:,.0f}</b><extra></extra>",
        ))
    fig.update_layout(barmode="group", bargap=0.28)
    fig.update_xaxes(title_text=f"Electricity used ({unit_elec})")
    fig.update_yaxes(title_text="Sector")
    return _dark_theme(fig, height=400, x_title=f"Electricity used ({unit_elec})", y_title="Sector")


# ═════════════════ V5: how far to trust the forecast ═════════════════════════

def visual5_reliability(metrics: pd.DataFrame, train_end: int, test_end: int):
    """Average error per series and model on the years the model had not seen."""
    if metrics is None or metrics.empty:
        return _empty_fig("No test results to show")

    hold_out = metrics[metrics["window"] == "hold-out"].copy()
    if hold_out.empty:
        return _empty_fig("No test results to show")
    hold_out = hold_out.sort_values("mape")

    labels = [f"{row['label']} · {row['model']}" for _, row in hold_out.iterrows()]
    colours = ["#10B981" if row["model"] == "Driver" else "#00A6FB"
               for _, row in hold_out.iterrows()]
    fig = go.Figure(go.Bar(
        y=labels, x=hold_out["mape"], orientation="h",
        marker=dict(color=colours),
        text=[f"{v:.1f}%" for v in hold_out["mape"]], textposition="outside",
        customdata=np.column_stack([hold_out["rmse"], hold_out["bias"], hold_out["n"]]),
        hovertemplate=("Average error <b>%{x:.2f}%</b><br>Typical gap %{customdata[0]:,.0f}"
                       "<br>Read as %{customdata[1]:+.1f}%<br>Years tested %{customdata[2]:.0f}<extra></extra>"),
    ))
    fig.update_xaxes(title_text="Average error (%)  — shorter bar is better")
    fig.update_yaxes(title_text="What the model forecasts")
    fig.add_annotation(x=1.0, y=1.12, xref="paper", yref="paper", xanchor="right",
                       text=f"Tested on {int(train_end) + 1}–{int(test_end)}",
                       showarrow=False, font=dict(size=10, color="#94A3B8"))
    return _dark_theme(fig, height=400, legend_h=False, x_title="Average error (%)  — shorter bar is better", y_title="What the model forecasts")
