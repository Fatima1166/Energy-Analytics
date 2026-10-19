"""
charts.py -- visuals for the Forecasted Energy Demand dashboard (question 4).

Seven figures, matching the eight dashboard elements (the KPI strip is element
one and is rendered by ``page.py``):

V1  History 1999-2024          -- electricity, gas and total final energy
V2  Scenario fan 2025-2035     -- Low / Base / High demand paths
V3  Demand drivers             -- demand vs real GDP, GDP per head and population
V4  Driver decomposition       -- income, population and intensity contributions
V5  Sector and province mix    -- who consumes, reported and to 2035
V6  Supply-demand gap          -- supply vs demand, and import dependency
V7  Forecast reliability       -- hold-out MAPE / RMSE and predicted vs actual

Every projected year is drawn dashed or hatched and every reported year solid,
so a modelled point is never mistaken for a measured one.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.demand_forecast import (
    ACTUAL,
    PROJECTED,
    PROVENANCE_COLORS,
    SCENARIO_COLORS,
    SCENARIO_ORDER,
    SERIES_SPEC,
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


def _boundary(fig, year: Optional[int], text: str = "Reported ◀ | ▶ Modelled"):
    if year is None:
        return fig
    fig.add_vline(x=year + 0.5, line=dict(color="#64748B", width=1.3, dash="dash"))
    fig.add_annotation(x=year + 0.5, y=1.0, yref="paper", yanchor="bottom",
                       text=text, showarrow=False, font=dict(size=9.5, color="#94A3B8"),
                       bgcolor="rgba(20,23,30,0.85)", borderpad=3, xanchor="center")
    return fig


def _provenance_line(fig, x, y, provenance, name: str, color: str, width: float = 2.4,
                     mode: str = "lines", row=None, col=None, secondary_y=False,
                     showlegend: bool = True):
    """One series drawn solid where reported and dashed where modelled."""
    frame = pd.DataFrame({"x": list(x), "y": list(y),
                          "p": [p if isinstance(p, str) else ACTUAL for p in provenance]})
    if frame.empty:
        return fig
    boundaries = [i for i in range(1, len(frame)) if frame["p"].iloc[i] != frame["p"].iloc[i - 1]]
    starts = [0] + boundaries
    ends = boundaries + [len(frame)]
    for seg_index, (start, end) in enumerate(zip(starts, ends)):
        low = max(0, start - 1) if seg_index > 0 else start
        segment = frame.iloc[low:end]
        tag = frame["p"].iloc[end - 1]
        style = dict(color=color, width=width)
        if tag == PROJECTED:
            style["dash"] = "dash"
        trace = go.Scatter(
            x=segment["x"], y=segment["y"], mode=mode, name=name,
            line=style, showlegend=showlegend and seg_index == 0,
            legendgroup=name,
            marker=dict(size=5, color=color) if "markers" in mode else None,
            hovertemplate=f"{name}<br>%{{x}}: <b>%{{y:,.2f}}</b><extra></extra>",
            connectgaps=False,
        )
        if row is not None:
            fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
        else:
            fig.add_trace(trace)
    return fig


# ═════════════════ V1: history 1999-2024 (objective 1) ═══════════════════════

def visual1_history_trends(hist: pd.DataFrame, keys: Sequence[str],
                           year_range: tuple, unit_energy: str = "TOE",
                           break_year: Optional[int] = None,
                           factor: float = 1.0):
    """Absolute and indexed reported demand for the final-energy series."""
    if hist is None or hist.empty:
        return _empty_fig()

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Reported demand", "Indexed (first year = 100)"))
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
        ), row=1, col=1)

        if values[0]:
            indexed = values / values[0] * 100.0
            fig.add_trace(go.Scatter(
                x=path["calendar_year"], y=indexed, mode="lines", name=spec["short"],
                line=dict(color=colour, width=2.2, dash="dot"), showlegend=False,
                hovertemplate=f"{spec['short']} index<br>%{{x}}: <b>%{{y:,.1f}}</b><extra></extra>",
            ), row=1, col=2)
        plotted += 1

    if not plotted:
        return _empty_fig()

    fig.add_hline(y=100, line=dict(color="#475569", width=1, dash="dot"), row=1, col=2)
    _boundary(fig, break_year, "basis change 2019")
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Demand ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text="Index (first year = 100)", row=1, col=2)
    return _dark_theme(fig, height=380, x_title=None)


# ════════════ V2: scenario fan to the horizon (objective 2) ══════════════════

def visual2_scenario_fans(bands: Dict[str, pd.DataFrame], hist: pd.DataFrame,
                          keys: Sequence[str], scenarios: Sequence[str],
                          unit_energy: str = "TOE", factor: float = 1.0,
                          break_year: Optional[int] = None):
    """Low / Base / High paths per series, band-shaded, with reported history."""
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
                mode="lines+markers", name="Reported",
                marker=dict(size=4, color="#E2E8F0"),
                line=dict(color="#E2E8F0", width=2.4),
                legendgroup="reported", showlegend=index == 1,
                hovertemplate="Reported<br>%{x}: <b>%{y:,.0f}</b><extra></extra>",
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
                ), row=1, col=index)
        _boundary(fig, break_year, "reported | modelled")
        fig.update_xaxes(title_text="Year", row=1, col=index)

    fig.update_yaxes(title_text=f"Demand ({unit_energy})", row=1, col=1)
    return _dark_theme(fig, height=380, x_title=None)


# ═════════════ V3: demand drivers (objective 3) ══════════════════════════════

def visual3_drivers(hist: pd.DataFrame, model: dict, key: str, year_range: tuple,
                    unit_energy: str = "TOE", factor: float = 1.0):
    """
    Left: demand against real GDP and population on a shared indexed scale.
    Right: the estimated relationship -- demand per head against real GDP per
    head, with the constant-elasticity curve the projection uses.
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
                        subplot_titles=("Demand vs its drivers (indexed)",
                                        "Demand per head vs income per head"))

    demand = window[spec["column"]].to_numpy(dtype=float)
    gdp_index = window["gdp_real_index"].to_numpy(dtype=float)
    pop = window["population"].to_numpy(dtype=float)
    years = window["calendar_year"].to_numpy(dtype=int)

    demand_index = demand / demand[0] * 100.0
    gdp_norm = gdp_index / gdp_index[0] * 100.0
    pop_norm = pop / pop[0] * 100.0

    fig.add_trace(go.Scatter(
        x=years, y=demand_index, mode="lines+markers", name=f"{spec['short']} (index)",
        line=dict(color=spec["color"], width=3),
        marker=dict(size=6, color=spec["color"]),
        hovertemplate=f"{spec['short']} index<br>%{{x}}: <b>%{{y:,.1f}}</b><extra></extra>",
    ), row=1, col=1, secondary_y=False)

    fig.add_trace(go.Scatter(
        x=years, y=gdp_norm, mode="lines+markers", name="Real GDP (index)",
        line=dict(color="#F472B6", width=2.4),
        marker=dict(size=5, color="#F472B6"),
        hovertemplate="Real GDP index<br>%{x}: <b>%{y:,.1f}</b><extra></extra>",
    ), row=1, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(
        x=years, y=pop_norm, mode="lines+markers", name="Population (index)",
        line=dict(color="#94A3B8", width=2, dash="dot"),
        marker=dict(size=4, color="#94A3B8"),
        hovertemplate="Population index<br>%{x}: <b>%{y:,.1f}</b><extra></extra>",
    ), row=1, col=1, secondary_y=True)

    # ── right: per-capita relationship ─────────────────────────────────────
    rgdppc = (window["real_gdp_per_capita"].to_numpy(dtype=float))
    per_capita = (demand / pop) * factor * 1e6      # per million people, readable
    valid = np.isfinite(rgdppc) & np.isfinite(per_capita) & (rgdppc > 0)
    rgdppc, per_capita = rgdppc[valid], per_capita[valid]

    fig.add_trace(go.Scatter(
        x=rgdppc, y=per_capita, mode="markers", name="Reported years",
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
            x=grid, y=curve, mode="lines", name=f"Elasticity fit (ε = {float(eps):.2f})",
            line=dict(color="#F472B6", width=2.2, dash="dash"), hoverinfo="skip",
        ), row=1, col=2)
        annotation = (f"income elasticity ε = {float(eps):.2f}<br>"
                      f"R² = {float(r2):.3f}" if r2 is not None and np.isfinite(r2)
                      else f"income elasticity ε = {float(eps):.2f}")
        fig.add_annotation(x=0.04, y=0.96, xref="x2 domain", yref="y2 domain",
                           text=annotation, showarrow=False, align="left",
                           font=dict(size=11, color="#E2E8F0"),
                           bgcolor="rgba(35,40,48,0.9)", borderpad=6)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_yaxes(title_text="Index (first year = 100)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Real GDP / population (index)", showgrid=False,
                     row=1, col=1, secondary_y=True)
    fig.update_xaxes(title_text="Real GDP per head (index)", row=1, col=2)
    fig.update_yaxes(title_text=f"Demand per million people ({unit_energy})", row=1, col=2)
    return _dark_theme(fig, height=400, x_title=None)


# ═════════ V4: growth decomposition (objective 3) ════════════════════════════

def visual4_decomposition(decomposition: pd.DataFrame, label: str):
    """Income-per-head, population and residual contributions to annual growth."""
    if decomposition is None or decomposition.empty:
        return _empty_fig("Not enough reported years to decompose growth")

    frame = decomposition.copy()
    fig = go.Figure()
    for column, name, colour in (("income_pp", "Income per head (ε × ΔGDP/head)", "#F472B6"),
                                 ("pop_pp", "Population", "#00A6FB"),
                                 ("residual_pp", "Intensity residual", "#F59E0B")):
        if column not in frame.columns:
            continue
        fig.add_trace(go.Bar(
            x=frame["calendar_year"], y=frame[column], name=name,
            marker=dict(color=colour, line=dict(width=0)),
            hovertemplate=f"{name}<br>%{{x}}: <b>%{{y:+.2f}} pp</b><extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=frame["calendar_year"], y=frame["total_pct"], mode="lines+markers",
        name="Reported demand growth", line=dict(color="#E2E8F0", width=2.6),
        marker=dict(size=6, color="#E2E8F0"),
        hovertemplate="Reported growth<br>%{x}: <b>%{y:+.2f}%</b><extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color="#475569", width=1))
    fig.update_layout(barmode="relative", bargap=0.25)
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Contribution to growth (pp)")
    fig.update_layout(title=dict(text=f"{label} — decomposition of annual demand growth",
                                 font=dict(size=11.5, color="#94A3B8"), x=0.01))
    return _dark_theme(fig, height=380, x_title="Year")


# ═════════ V5: sector and province mix (objective 4) ═════════════════════════

def visual5_sector_mix(sectors: dict, horizon: int, unit_elec: str = "GWh",
                       factor: float = 1.0, scenario: str = "Base"):
    """Reported vs horizon electricity demand by end-use sector."""
    history = sectors.get("history") if sectors else None
    projection = sectors.get("projection") if sectors else None
    if history is None or history.empty:
        return _empty_fig("No sector consumption data")

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
        name=f"Reported {base_year}", marker=dict(color="#00A6FB"),
        hovertemplate="%{y}<br>reported: <b>%{x:,.0f}</b><extra></extra>",
    ))
    if not future.empty:
        fig.add_trace(go.Bar(
            y=order, x=[future.get(k, 0.0) for k in order], orientation="h",
            name=f"{scenario} {int(horizon)}",
            marker=dict(color="#10B981", pattern=dict(shape="/", fgcolor="rgba(255,255,255,0.35)")),
            hovertemplate="%{y}<br>modelled: <b>%{x:,.0f}</b><extra></extra>",
        ))
    fig.update_layout(barmode="group", bargap=0.28)
    fig.update_xaxes(title_text=f"Electricity demand ({unit_elec})")
    fig.update_yaxes(title_text="Sector")
    return _dark_theme(fig, height=400, x_title=f"Electricity demand ({unit_elec})", y_title="Sector")


def visual5_province_mix(provinces: dict, horizon: int, scenario: str = "Base",
                         factor: float = 1.0):
    """Province shares of electricity demand, reported then projected."""
    history = provinces.get("history") if provinces else None
    projection = provinces.get("projection") if provinces else None
    if history is None or history.empty:
        return _empty_fig("No province consumption data")

    rows = history[["calendar_year", "key", "value"]].copy()
    rows["scenario"] = ACTUAL
    if projection is not None and not projection.empty:
        projected = projection[projection["scenario"] == scenario][["calendar_year", "key", "value"]]
        projected = projected.copy()
        projected["scenario"] = PROJECTED
        rows = pd.concat([rows, projected], ignore_index=True)

    totals = rows.groupby("calendar_year")["value"].transform("sum")
    rows["share"] = rows["value"] / totals * 100.0

    palette = ["#00A6FB", "#10B981", "#F59E0B", "#A78BFA", "#F472B6", "#22D3EE", "#EF4444"]
    fig = go.Figure()
    keys = (rows.groupby("key")["value"].sum().sort_values(ascending=False).index.tolist())
    for index, key in enumerate(keys):
        subset = rows[rows["key"] == key].sort_values("calendar_year")
        fig.add_trace(go.Scatter(
            x=subset["calendar_year"], y=subset["share"], mode="lines",
            name=str(key), stackgroup="province",
            line=dict(width=0.6, color=palette[index % len(palette)]),
            hovertemplate=f"{key}<br>%{{x}}: <b>%{{y:.1f}}%</b><extra></extra>",
        ))
    _boundary(fig, 2024, "reported | modelled")
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Share of electricity demand (%)", range=[0, 100])
    return _dark_theme(fig, height=400, x_title="Year", y_title="Share of electricity demand (%)")


# ═════════ V6: supply-demand gap (objective 5) ═══════════════════════════════

def visual6_gap(gap_total: pd.DataFrame, unit_energy: str = "TOE",
                factor: float = 1.0, base_scenario: str = "Base"):
    """Primary supply against demand, with the gap as a share of supply."""
    if gap_total is None or gap_total.empty:
        return _empty_fig("No supply data available")

    base = gap_total[gap_total["scenario"] == base_scenario].sort_values("calendar_year")
    if base.empty:
        base = gap_total.sort_values("calendar_year")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    _provenance_line(fig, base["calendar_year"], base["supply"] * factor,
                     base["provenance"], "Primary supply", "#00A6FB", row=1, col=1)
    _provenance_line(fig, base["calendar_year"], base["demand"] * factor,
                     base["provenance"], f"Demand ({base_scenario})", "#F472B6", row=1, col=1)

    fig.add_trace(go.Bar(
        x=base["calendar_year"], y=base["gap_pct"], name="Gap (% of supply)",
        marker=dict(color=["#EF4444" if v < 0 else "#10B981" for v in base["gap_pct"]]),
        opacity=0.45, hovertemplate="%{x}: gap <b>%{y:+.1f}%</b> of supply<extra></extra>",
    ), row=1, col=1, secondary_y=True)

    _boundary(fig, None)
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_yaxes(title_text=f"Energy ({unit_energy})", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Gap (% of supply)", showgrid=False,
                     row=1, col=1, secondary_y=True)
    fig.update_layout(barmode="overlay")
    return _dark_theme(fig, height=400, x_title=None)


def visual6_imports(imports: pd.DataFrame, horizon: int):
    """Gas import dependency and the electricity import share."""
    if imports is None or imports.empty:
        return _empty_fig("No import dependency data")

    frame = imports.sort_values("calendar_year")
    fig = go.Figure()
    if "gas_import_dep_pct" in frame.columns:
        gas = frame.dropna(subset=["gas_import_dep_pct"])
        _provenance_line(fig, gas["calendar_year"], gas["gas_import_dep_pct"],
                         gas["provenance"], "Gas import dependency", "#F59E0B")
    if "elec_import_share_pct" in frame.columns:
        elec = frame.dropna(subset=["elec_import_share_pct"])
        _provenance_line(fig, elec["calendar_year"], elec["elec_import_share_pct"],
                         elec["provenance"], "Electricity import share", "#A78BFA")
    _boundary(fig, 2024, "reported | modelled")
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text="Import dependency (%)")
    return _dark_theme(fig, height=370, x_title="Year", y_title="Import dependency (%)")


# ═════════ V7: backtest reliability (objective 6) ════════════════════════════

def visual7_backtest_mape(metrics: pd.DataFrame, train_end: int, test_end: int):
    """Hold-out MAPE per series and model, with RMSE on the hover."""
    if metrics is None or metrics.empty:
        return _empty_fig("Backtest not available")

    hold_out = metrics[metrics["window"] == "hold-out"].copy()
    if hold_out.empty:
        return _empty_fig("Backtest not available")
    hold_out = hold_out.sort_values("mape")

    labels = [f"{row['label']} · {row['model']}" for _, row in hold_out.iterrows()]
    colours = ["#10B981" if row["model"] == "Driver" else "#00A6FB"
               for _, row in hold_out.iterrows()]
    fig = go.Figure(go.Bar(
        y=labels, x=hold_out["mape"], orientation="h",
        marker=dict(color=colours),
        text=[f"{v:.1f}%" for v in hold_out["mape"]], textposition="outside",
        customdata=np.column_stack([hold_out["rmse"], hold_out["bias"], hold_out["n"]]),
        hovertemplate=("MAPE <b>%{x:.2f}%</b><br>RMSE %{customdata[0]:,.0f}"
                       "<br>bias %{customdata[1]:+.1f}%<br>n = %{customdata[2]:.0f}<extra></extra>"),
    ))
    fig.update_xaxes(title_text="Hold-out MAPE (%)  — lower is better")
    fig.update_yaxes(title_text="Forecast Model / Series")
    fig.add_annotation(x=1.0, y=1.12, xref="paper", yref="paper", xanchor="right",
                       text=f"hold-out window {int(train_end) + 1}–{int(test_end)}",
                       showarrow=False, font=dict(size=10, color="#94A3B8"))
    return _dark_theme(fig, height=400, legend_h=False, x_title="Hold-out MAPE (%)  — lower is better", y_title="Forecast Model / Series")


def visual7_backtest_path(predictions: pd.DataFrame, key: str, unit: str = "TOE",
                          factor: float = 1.0, label: str = ""):
    """Predicted vs reported demand over the hold-out window, per model."""
    if predictions is None or predictions.empty:
        return _empty_fig("Backtest not available")
    subset = predictions[predictions["series"] == key]
    if subset.empty:
        return _empty_fig("Backtest not available")

    fig = go.Figure()
    actual = subset.sort_values("calendar_year").drop_duplicates("calendar_year")
    fig.add_trace(go.Scatter(
        x=actual["calendar_year"], y=actual["actual"] * factor, mode="lines+markers",
        name="Reported", line=dict(color="#E2E8F0", width=3),
        marker=dict(size=8, color="#E2E8F0"),
        hovertemplate="Reported<br>%{x}: <b>%{y:,.0f}</b><extra></extra>",
    ))
    for model, colour in (("Trend", "#00A6FB"), ("Driver", "#10B981")):
        model_rows = subset[subset["model"] == model].sort_values("calendar_year")
        if model_rows.empty:
            continue
        fig.add_trace(go.Scatter(
            x=model_rows["calendar_year"], y=model_rows["predicted"] * factor,
            mode="lines+markers", name=f"{model} model",
            line=dict(color=colour, width=2.2, dash="dash"),
            marker=dict(size=5, color=colour, symbol="diamond"),
            hovertemplate=f"{model}<br>%{{x}}: <b>%{{y:,.0f}}</b><extra></extra>",
        ))
    fig.update_xaxes(title_text="Year")
    fig.update_yaxes(title_text=f"{label} ({unit})")
    return _dark_theme(fig, height=400)
