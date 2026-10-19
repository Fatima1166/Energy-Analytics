"""
dashboards/q5_forecast_supply/charts.py -- visuals for Forecasted Energy Supply (question 5).

Seven visualization figures covering the analytical objectives:
V1  Historical supply trajectory (1999-2024) -- Primary Supply & Generation by fuel
V2  Supply scenario fan (2025-2035)          -- Low / Base / High trajectories with envelope
V3  Fuel & technology supply mix evolution   -- Technology shares and clean target tracking
V4  Installed generation capacity (MW/GW)    -- Technology-wise capacity expansion
V5  Supply adequacy & reserve margin         -- Supply vs demand and system reserve corridor
V6  Energy security & import vulnerability   -- Indigenous domestic vs imported fuel trajectory
V7  Forecast reliability & backtesting       -- Hold-out validation (2021-2024) vs actuals
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.supply_forecast import (
    ACTUAL,
    CLEAN_POLICY_TARGET_DEFAULT,
    FUEL_COLORS,
    HISTORY_END,
    PROJECTED,
    SCENARIO_COLORS,
    SCENARIO_ORDER,
)

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8CDD6"


def _dark_theme(fig, height: int = 380, y_title: Optional[str] = None,
                y2_title: Optional[str] = None, legend_h: bool = True,
                x_title: Optional[str] = "Year"):
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
        margin=dict(l=62, r=52, t=48, b=108),
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
    # Only assign title when a non-None string is given, so that multi-panel
    # charts which set their own per-row/col titles are not overwritten.
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


def _boundary(fig, year: Optional[int] = HISTORY_END, text: str = "Reported ◀ | ▶ Modelled"):
    if year is None:
        return fig
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


# ═══════════════════════════ Visual 1: History ═══════════════════════════════

def visual1_history_trajectory(
    hist: pd.DataFrame,
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """
    Subplots:
    Panel 1: Primary Energy Supply by Fuel Source (stacked area in chosen energy unit)
    Panel 2: Power Generation Supply by Technology (stacked area in chosen electricity unit)
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Primary Energy Supply by Source ({unit_energy})",
            f"Power Generation by Technology ({unit_elec})",
        ),
        horizontal_spacing=0.10,
    )

    h_pes = hist[hist["calendar_year"] >= 2002].copy()
    years_p = h_pes["calendar_year"].values

    pes_sources = [
        ("pes_gas_toe", "Natural Gas", "#F97316"),
        ("pes_oil_toe", "Oil & Petroleum", "#EF4444"),
        ("pes_coal_toe", "Coal", "#6B7280"),
        ("pes_hydro_toe", "Hydro Electricity", "#0284C7"),
        ("pes_nuclear_toe", "Nuclear Electricity", "#A78BFA"),
        ("pes_renewables_toe", "Renewables (Solar/Wind)", "#10B981"),
    ]

    for col, name, colr in pes_sources:
        if col in h_pes.columns:
            vals = h_pes[col].fillna(0.0).values * factor_energy
            fig.add_trace(
                go.Scatter(
                    x=years_p, y=vals, name=name, mode="lines",
                    stackgroup="pes", line=dict(width=0.8, color=colr),
                    fillcolor=colr, legendgroup="pes",
                    hovertemplate=f"{name}: %{{y:,.1f}} {unit_energy}<extra></extra>",
                ),
                row=1, col=1,
            )

    # Panel 2: Electricity Generation by Technology
    h_gen = hist[hist["calendar_year"] >= 2000].copy()
    years_g = h_gen["calendar_year"].values

    gen_sources = [
        ("gen_hydro_gwh", "Hydro", "#0284C7"),
        ("gen_solar_gwh", "Solar", "#F59E0B"),
        ("gen_wind_gwh", "Wind", "#10B981"),
        ("gen_nuclear_gwh", "Nuclear", "#A78BFA"),
        ("gen_coal_gwh", "Coal", "#6B7280"),
        ("gen_gas_gwh", "Natural Gas / RLNG", "#F97316"),
    ]

    for col, name, colr in gen_sources:
        if col in h_gen.columns:
            vals = h_gen[col].fillna(0.0).values * factor_elec
            fig.add_trace(
                go.Scatter(
                    x=years_g, y=vals, name=name, mode="lines",
                    stackgroup="gen", line=dict(width=0.8, color=colr),
                    fillcolor=colr, legendgroup="gen",
                    hovertemplate=f"{name}: %{{y:,.1f}} {unit_elec}<extra></extra>",
                ),
                row=1, col=2,
            )

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Primary Energy Supply ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text=f"Power Generation ({unit_elec})", row=1, col=2)
    return _dark_theme(fig, height=390, legend_h=True, x_title=None)


# ═══════════════════════════ Visual 2: Scenario Fans ═════════════════════════

def visual2_scenario_fans(
    hist: pd.DataFrame,
    forecast: pd.DataFrame,
    scenarios: List[str] = SCENARIO_ORDER,
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """
    Subplots:
    Panel 1: Total Primary Energy Supply Scenario Fan (Low / Base / High)
    Panel 2: Power Generation Supply Scenario Fan (Low / Base / High)
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Total Primary Energy Supply Outlook ({unit_energy})",
            f"Power Generation Supply Outlook ({unit_elec})",
        ),
        horizontal_spacing=0.10,
    )

    panels = [
        (1, "tpes_toe", factor_energy, unit_energy, 2002),
        (2, "gen_total_gwh", factor_elec, unit_elec, 2005),
    ]

    for col_idx, series_name, factor, unit_lbl, start_yr in panels:
        h_sub = hist[hist["calendar_year"] >= start_yr].copy()
        x_hist = h_sub["calendar_year"].values
        y_hist = h_sub[series_name].values * factor

        # Solid historical reported line
        fig.add_trace(
            go.Scatter(
                x=x_hist, y=y_hist, name=f"Reported {unit_lbl}",
                mode="lines+markers",
                marker=dict(size=4, color="#E2E8F0"),
                line=dict(color="#E2E8F0", width=2.4),
                showlegend=(col_idx == 1),
                hovertemplate=f"Reported: %{{y:,.1f}} {unit_lbl}<extra></extra>",
            ),
            row=1, col=col_idx,
        )

        fc_sub = forecast[forecast["series"] == series_name].copy()
        if not fc_sub.empty:
            # Low and High envelope if available
            has_low = "Low" in fc_sub["scenario"].values and "Low" in scenarios
            has_high = "High" in fc_sub["scenario"].values and "High" in scenarios

            if has_low and has_high:
                low_p = fc_sub[fc_sub["scenario"] == "Low"].sort_values("calendar_year")
                high_p = fc_sub[fc_sub["scenario"] == "High"].sort_values("calendar_year")

                x_env = [x_hist[-1]] + list(low_p["calendar_year"])
                y_low = [y_hist[-1]] + list(low_p["value"] * factor)
                y_high = [y_hist[-1]] + list(high_p["value"] * factor)

                fig.add_trace(
                    go.Scatter(
                        x=x_env + x_env[::-1],
                        y=y_high + y_low[::-1],
                        fill="toself",
                        fillcolor="rgba(0, 166, 251, 0.12)",
                        line=dict(color="rgba(255,255,255,0)"),
                        name="Scenario Envelope",
                        showlegend=(col_idx == 1),
                        hoverinfo="skip",
                    ),
                    row=1, col=col_idx,
                )

            for sc in scenarios:
                sc_df = fc_sub[fc_sub["scenario"] == sc].sort_values("calendar_year")
                if not sc_df.empty:
                    x_sc = [x_hist[-1]] + list(sc_df["calendar_year"])
                    y_sc = [y_hist[-1]] + list(sc_df["value"] * factor)
                    clr = SCENARIO_COLORS.get(sc, "#00A6FB")
                    fig.add_trace(
                        go.Scatter(
                            x=x_sc, y=y_sc, name=f"{sc} Scenario",
                            mode="lines+markers",
                            marker=dict(size=4, color=clr),
                            line=dict(color=clr, width=2.2, dash="dash" if sc != "Base" else "solid"),
                            showlegend=(col_idx == 1),
                            hovertemplate=f"{sc}: %{{y:,.1f}} {unit_lbl}<extra></extra>",
                        ),
                        row=1, col=col_idx,
                    )

        # Boundary line
        _boundary(fig, HISTORY_END)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Primary Energy Supply ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text=f"Power Generation ({unit_elec})", row=1, col=2)
    return _dark_theme(fig, height=390, legend_h=True, x_title=None)


# ═══════════════════════════ Visual 3: Tech Mix Evolution ═════════════════════

def visual3_technology_mix(
    tech_mix: pd.DataFrame,
    active_scenario: str = "Base",
    clean_target: float = CLEAN_POLICY_TARGET_DEFAULT,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """
    Subplots / Dual-Axis:
    Left: Generation Mix Breakdown by Source (Hydro, Solar, Wind, Nuclear, Coal, Gas) in GWh/TWh.
    Right: Clean Energy Share % vs Policy Target Benchmarks (60% Clean Target line & 30% ARE line).
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Filter for active scenario or Actual
    sub = tech_mix[(tech_mix["scenario"] == active_scenario) | (tech_mix["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    techs = [
        ("Hydro", "#0284C7"),
        ("Solar", "#F59E0B"),
        ("Wind", "#10B981"),
        ("Nuclear", "#A78BFA"),
        ("Coal", "#6B7280"),
        ("Gas", "#F97316"),
    ]

    for tech, clr in techs:
        if tech in sub.columns:
            vals = sub[tech].values * factor_elec
            fig.add_trace(
                go.Scatter(
                    x=years, y=vals, name=tech, mode="lines",
                    stackgroup="tech", line=dict(width=0.6, color=clr),
                    fillcolor=clr,
                    hovertemplate=f"{tech}: %{{y:,.1f}} {unit_elec}<extra></extra>",
                ),
                secondary_y=False,
            )

    # Clean Energy Share % on secondary axis
    clean_pct = sub["clean_share_pct"].values
    fig.add_trace(
        go.Scatter(
            x=years, y=clean_pct, name="Clean Share %",
            mode="lines+markers",
            line=dict(color="#22D3EE", width=2.8),
            marker=dict(size=5, color="#22D3EE"),
            hovertemplate="Clean Share: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    # Policy Target horizontal benchmarks (labels on the left to avoid the
    # right-axis ticks and the last x-axis year colliding with the text)
    fig.add_hline(
        y=clean_target, line=dict(color="#10B981", width=1.8, dash="dot"),
        annotation_text=f"Clean Target ({clean_target:.0f}%)",
        annotation_position="top left", annotation_font=dict(size=10, color="#10B981"),
        secondary_y=True,
    )
    fig.add_hline(
        y=30.0, line=dict(color="#F59E0B", width=1.5, dash="dot"),
        annotation_text="ARE Target (30%)",
        annotation_position="bottom left", annotation_font=dict(size=10, color="#F59E0B"),
        secondary_y=True,
    )

    _boundary(fig, HISTORY_END)
    fig.update_yaxes(title_text=f"Generation ({unit_elec})", secondary_y=False)
    fig.update_yaxes(title_text="Clean Energy Share (%)", range=[0, 100], secondary_y=True)

    return _dark_theme(fig, height=400, legend_h=True)


# ═══════════════════════════ Visual 4: Capacity Expansion ════════════════════

def visual4_capacity_expansion(
    capacity_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_power: str = "MW",
    factor_power: float = 1.0,
) -> go.Figure:
    """
    Installed Generation Capacity expansion (MW/GW) breakdown across technologies:
    Hydro, Solar, Wind, Nuclear, Coal, Gas.
    """
    fig = go.Figure()

    sub = capacity_df[(capacity_df["scenario"] == active_scenario) | (capacity_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    cap_techs = [
        ("cap_hydro_mw", "Hydro Capacity", "#0284C7"),
        ("cap_solar_mw", "Solar Capacity", "#F59E0B"),
        ("cap_wind_mw", "Wind Capacity", "#10B981"),
        ("cap_nuclear_mw", "Nuclear Capacity", "#A78BFA"),
        ("cap_coal_mw", "Coal Capacity", "#6B7280"),
        ("cap_gas_mw", "Gas / Peaking Capacity", "#F97316"),
    ]

    for col, name, clr in cap_techs:
        if col in sub.columns:
            vals = sub[col].values * factor_power
            fig.add_trace(
                go.Scatter(
                    x=years, y=vals, name=name, mode="lines",
                    stackgroup="cap", line=dict(width=0.6, color=clr),
                    fillcolor=clr,
                    hovertemplate=f"{name}: %{{y:,.1f}} {unit_power}<extra></extra>",
                ),
            )

    # Total line
    tot_cap = sub["total_capacity_mw"].values * factor_power
    fig.add_trace(
        go.Scatter(
            x=years, y=tot_cap, name="Total Capacity",
            mode="lines",
            line=dict(color="#FFFFFF", width=2.0, dash="dash"),
            hovertemplate=f"Total: %{{y:,.1f}} {unit_power}<extra></extra>",
        ),
    )

    _boundary(fig, HISTORY_END)
    return _dark_theme(fig, height=380, y_title=f"Installed Capacity ({unit_power})", legend_h=True)


# ═══════════════════════════ Visual 5: Supply Adequacy ═══════════════════════

def visual5_supply_vs_demand(
    adequacy_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Standalone clean chart for Generation Supply vs Grid Demand."""
    fig = go.Figure()

    sub = adequacy_df[(adequacy_df["scenario"] == active_scenario) | (adequacy_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    supp_vals = sub["supply_gwh"].values * factor_elec
    dem_vals = sub["demand_gwh"].values * factor_elec

    fig.add_trace(
        go.Scatter(
            x=years, y=supp_vals, name="Generation Supply",
            mode="lines+markers",
            line=dict(color="#00A6FB", width=2.5),
            marker=dict(size=4, color="#00A6FB"),
            hovertemplate=f"Supply: %{{y:,.1f}} {unit_elec}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=dem_vals, name="Grid Demand",
            mode="lines",
            line=dict(color="#F59E0B", width=2.2, dash="dash"),
            hovertemplate=f"Demand: %{{y:,.1f}} {unit_elec}<extra></extra>",
        )
    )

    _boundary(fig, HISTORY_END)
    fig.update_layout(
        title=dict(
            text=f"Generation Supply vs Demand ({unit_elec})",
            font=dict(size=13, color="#F1F5F9"),
            x=0.03, y=0.96,
        ),
        margin=dict(l=62, r=40, t=55, b=60),
    )
    return _dark_theme(fig, height=380, y_title=f"Generation ({unit_elec})", legend_h=True)


def visual5_reserve_margin(
    adequacy_df: pd.DataFrame,
    active_scenario: str = "Base",
) -> go.Figure:
    """Standalone clean chart for System Reserve Margin (%) with safe corridor."""
    fig = go.Figure()

    sub = adequacy_df[(adequacy_df["scenario"] == active_scenario) | (adequacy_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values
    margin_pct = sub["reserve_margin_pct"].values

    bar_colors = [
        "#EF4444" if m < 10.0 else ("#10B981" if m <= 25.0 else "#F59E0B")
        for m in margin_pct
    ]

    fig.add_trace(
        go.Bar(
            x=years, y=margin_pct, name="Reserve Margin %",
            marker_color=bar_colors,
            hovertemplate="Reserve Margin: %{y:.1f}%<extra></extra>",
        )
    )

    # Safe Corridor (15% - 25%)
    fig.add_hrect(
        y0=15.0, y1=25.0,
        fillcolor="rgba(16, 185, 129, 0.15)", line_width=0,
        annotation_text="Safe Corridor (15–25%)",
        annotation_position="top left",
        annotation_font=dict(size=9.5, color="#10B981"),
    )
    fig.add_hline(
        y=15.0, line=dict(color="#10B981", width=1.2, dash="dot"),
    )

    _boundary(fig, HISTORY_END)
    fig.update_layout(
        title=dict(
            text="System Reserve Margin Trajectory (%)",
            font=dict(size=13, color="#F1F5F9"),
            x=0.03, y=0.96,
        ),
        margin=dict(l=62, r=40, t=55, b=60),
    )
    return _dark_theme(fig, height=380, y_title="Reserve Margin (%)", legend_h=True)


def visual5_supply_adequacy(
    adequacy_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """
    Subplots:
    Panel 1: Generation Supply vs Grid Demand (GWh/TWh) under active scenario.
    Panel 2: Reserve Margin % trajectory vs Safe Corridor (15% - 25%).
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Generation Supply vs Demand ({unit_elec})",
            "System Reserve Margin Trajectory (%)",
        ),
        horizontal_spacing=0.14,
    )

    sub = adequacy_df[(adequacy_df["scenario"] == active_scenario) | (adequacy_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    supp_vals = sub["supply_gwh"].values * factor_elec
    dem_vals = sub["demand_gwh"].values * factor_elec

    # Panel 1: Supply vs Demand
    fig.add_trace(
        go.Scatter(
            x=years, y=supp_vals, name="Supply",
            mode="lines+markers",
            line=dict(color="#00A6FB", width=2.4),
            marker=dict(size=4),
            hovertemplate=f"Supply: %{{y:,.1f}} {unit_elec}<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=dem_vals, name="Grid Demand",
            mode="lines",
            line=dict(color="#F59E0B", width=2.2, dash="dash"),
            hovertemplate=f"Demand: %{{y:,.1f}} {unit_elec}<extra></extra>",
        ),
        row=1, col=1,
    )

    # Panel 2: Reserve margin %
    margin_pct = sub["reserve_margin_pct"].values

    bar_colors = [
        "#EF4444" if m < 10.0 else ("#10B981" if m <= 25.0 else "#F59E0B")
        for m in margin_pct
    ]

    fig.add_trace(
        go.Bar(
            x=years, y=margin_pct, name="Reserve Margin %",
            marker_color=bar_colors,
            hovertemplate="Reserve Margin: %{y:.1f}%<extra></extra>",
        ),
        row=1, col=2,
    )

    # Target Corridor (15% - 25%)
    fig.add_hrect(
        y0=15.0, y1=25.0,
        fillcolor="rgba(16, 185, 129, 0.15)", line_width=0,
        row=1, col=2,
    )
    fig.add_hline(
        y=15.0, line=dict(color="#10B981", width=1.2, dash="dot"),
        annotation_text="Adequacy Floor (15%)", annotation_position="top left",
        annotation_font=dict(size=9.5, color="#10B981"),
        row=1, col=2,
    )

    _boundary(fig, HISTORY_END)
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Generation ({unit_elec})", row=1, col=1)
    fig.update_yaxes(title_text="Reserve Margin (%)", row=1, col=2)
    return _dark_theme(fig, height=380, legend_h=True, x_title=None)


# ═══════════════════════════ Visual 6: Energy Security ═══════════════════════

def visual6_indigenous_vs_imports(
    security_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
) -> go.Figure:
    """
    Subplots / Dual-Axis:
    Left: Indigenous Domestic Energy vs Imported Energy (stacked area in TOE).
    Right: Import Dependency % trajectory.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    sub = security_df[(security_df["scenario"] == active_scenario) | (security_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    dom_vals = sub["domestic_toe"].values * factor_energy
    imp_vals = sub["imports_toe"].values * factor_energy
    imp_share = sub["import_share_pct"].values

    fig.add_trace(
        go.Scatter(
            x=years, y=dom_vals, name="Indigenous Domestic Energy",
            mode="lines", stackgroup="sec",
            line=dict(width=0.8, color="#10B981"), fillcolor="#10B981",
            hovertemplate=f"Indigenous: %{{y:,.1f}} {unit_energy}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=imp_vals, name="Imported Energy (Oil, LNG, Coal)",
            mode="lines", stackgroup="sec",
            line=dict(width=0.8, color="#EF4444"), fillcolor="#EF4444",
            hovertemplate=f"Imports: %{{y:,.1f}} {unit_energy}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Import Share % on right axis
    fig.add_trace(
        go.Scatter(
            x=years, y=imp_share, name="Import Dependency %",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2.4),
            marker=dict(size=4, color="#F59E0B"),
            hovertemplate="Import Share: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    _boundary(fig, HISTORY_END)
    fig.update_yaxes(title_text=f"Energy Supply ({unit_energy})", secondary_y=False)
    fig.update_yaxes(title_text="Import Dependency (%)", range=[0, 60], secondary_y=True)

    return _dark_theme(fig, height=380, legend_h=True)


# ═══════════════════════════ Visual 7: Reliability Backtest ══════════════════

def visual7_reliability_backtest(
    backtest: dict,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """
    Compares Actual Reported generation (2021-2024 hold-out) vs Driver model and Trend model predictions.
    """
    fig = go.Figure()
    path_df = backtest.get("paths", pd.DataFrame())

    if path_df.empty:
        return _dark_theme(fig, height=350)

    gen_paths = path_df[path_df["col"] == "gen_total_gwh"].sort_values("calendar_year")
    if gen_paths.empty:
        return _dark_theme(fig, height=350)

    years = gen_paths["calendar_year"].values
    acts = gen_paths["actual"].values * factor_elec
    driv = gen_paths["predicted_driver"].values * factor_elec
    tren = gen_paths["predicted_trend"].values * factor_elec

    fig.add_trace(
        go.Scatter(
            x=years, y=acts, name="Actual Reported",
            mode="lines+markers",
            marker=dict(size=8, color="#FFFFFF"),
            line=dict(color="#FFFFFF", width=3.0),
            hovertemplate=f"Actual: %{{y:,.1f}} {unit_elec}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=driv, name="Driver Model (Macro/Elasticity)",
            mode="lines+markers",
            marker=dict(size=6, color="#00A6FB"),
            line=dict(color="#00A6FB", width=2.2, dash="dash"),
            hovertemplate=f"Driver Predicted: %{{y:,.1f}} {unit_elec}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=tren, name="Trend Model (Log-Linear)",
            mode="lines+markers",
            marker=dict(size=6, color="#F59E0B"),
            line=dict(color="#F59E0B", width=2.2, dash="dot"),
            hovertemplate=f"Trend Predicted: %{{y:,.1f}} {unit_elec}<extra></extra>",
        )
    )

    return _dark_theme(fig, height=350, y_title=f"Power Generation ({unit_elec})", legend_h=True, x_title="Hold-out Year (2021–2024)")
