"""
dashboards/q6_supply_chain_optimization/charts.py
Eight Plotly visualizations for supply chain optimization analysis (Q6).

V1  Supply Chain Efficiency Scorecard     -- radar/spider with KPI scores vs benchmarks
V2  T&D Loss Trend & Efficiency Gap       -- T&D losses vs optimal benchmark over time
V3  Fuel Import Dependency                -- domestic vs imported fuel split + trend
V4  Renewable Capacity Utilisation        -- MW installed vs GWh generated (utilization rate)
V5  Gas Supply Chain: Production vs Gap   -- gas production, consumption & gap trajectory
V6  LNG Cost vs Domestic Gas              -- LNG import cost (MUSD) vs volumes (unit-aware)
V7  Supply Chain Optimization Score       -- composite weighted score trend 1999-2024
V8  Optimal Mix Simulation                -- what-if: fuel vs renewable optimal balance
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import (
    BENCHMARK_FUEL_WASTE_MAX,
    BENCHMARK_GAS_SELFSUFFICIENCY,
    BENCHMARK_IMPORT_DEPENDENCY_MAX,
    BENCHMARK_RE_UTILISATION_MIN,
    BENCHMARK_TRANSMISSION_EFFICIENCY,
    BLUE, GREEN, AMBER, RED, PURPLE, TEAL, CYAN, ORANGE, ROSE, LIME,
    CF_SOLAR, CF_WIND, CF_HYDRO, CF_NUCLEAR, CF_THERMAL,
    SCE_WEIGHTS,
)

# ── Dark theme helpers ────────────────────────────────────────────────────────

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8CDD6"


def _dark_theme(fig, height: int = 380, y_title: Optional[str] = None,
                y2_title: Optional[str] = None, legend_h: bool = True,
                x_title: Optional[str] = "Year"):
    legend_cfg = (
        dict(orientation="h", y=-0.28, x=0.5, xanchor="center",
             font=dict(size=10.5, color=_TEXT))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color=_TEXT))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=62, r=46, t=45, b=72),
        height=height,
        legend=legend_cfg,
        hovermode="x unified",
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
    if y2_title:
        fig.update_layout(yaxis2=dict(
            title=dict(text=y2_title, font=dict(size=11.5, color=_TEXT)),
            tickfont=dict(size=11, color=_TICK),
            overlaying="y", side="right", showgrid=False, zeroline=False))
    return fig


def _benchmark_line(fig, y: float, label: str, color: str = "#F59E0B", row=None, col=None):
    """Add a horizontal dashed benchmark reference line."""
    kwargs = dict(row=row, col=col) if row else {}
    fig.add_hline(y=y, line=dict(color=color, width=1.4, dash="dot"),
                  annotation_text=f" {label}", annotation_font_size=9,
                  annotation_font_color=color, **kwargs)


# ── V1: Supply Chain Efficiency Radar ────────────────────────────────────────

def visual1_radar_scorecard(scores: dict, year: int) -> go.Figure:
    """
    Radar chart: five supply-chain KPI scores vs benchmark (100 = perfect).
    scores: dict with keys matching SCE_WEIGHTS, values are 0-100.
    """
    categories = [
        "Transmission<br>Efficiency",
        "RE Utilisation",
        "Import<br>Independence",
        "Fuel Waste<br>Reduction",
        "Gas<br>Self-Sufficiency",
    ]
    vals = [
        float(scores.get("transmission_efficiency", 0) or 0),
        float(scores.get("re_utilisation", 0) or 0),
        float(scores.get("import_dependency", 0) or 0),
        float(scores.get("fuel_waste_reduction", 0) or 0),
        float(scores.get("gas_self_sufficiency", 0) or 0),
    ]
    benchmark_vals = [100.0, 100.0, 100.0, 100.0, 100.0]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=benchmark_vals + [benchmark_vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(100,116,139,0.08)",
        line=dict(color="#64748B", width=1.2, dash="dash"),
        name="Target Benchmark (100)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(0,166,251,0.20)",
        line=dict(color=BLUE, width=2.5),
        name=f"Performance ({year})",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        height=360,
        polar=dict(
            bgcolor="#14171E",
            radialaxis=dict(
                visible=True, range=[0, 110], gridcolor="#2A2F3A",
                tickfont=dict(size=9, color=_TICK), ticksuffix="",
                showline=False,
            ),
            angularaxis=dict(gridcolor="#2A2F3A", tickfont=dict(size=9.5, color=_TEXT)),
        ),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                    font=dict(size=10.5, color=_TEXT)),
        font=dict(family="Inter, sans-serif", color=_TEXT),
        margin=dict(l=40, r=40, t=40, b=60),
    )
    return fig


# ── V2: T&D Loss Trend ───────────────────────────────────────────────────────

def visual2_td_loss_trend(df: pd.DataFrame, unit_elec: str, factor_elec: float,
                          target_loss_benchmark: float = 15.0) -> go.Figure:
    """
    Area chart: T&D losses over time + efficiency % on right axis.
    target_loss_benchmark: desired loss benchmark (default 15.0%).
    """
    if df.empty:
        return go.Figure()

    df = df.sort_values("calendar_year").copy()
    df["loss_disp"] = df["td_losses_gwh"] * factor_elec
    df["gen_disp"] = df["gen_gwh"] * factor_elec
    df["efficiency_pct"] = (1 - df["td_losses_gwh"] / df["gen_gwh"].replace(0, np.nan)) * 100

    target_eff = 100.0 - target_loss_benchmark

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["gen_disp"],
        name=f"Total Generation ({unit_elec})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(0,166,251,0.10)",
        line=dict(color=BLUE, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>Generation</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["loss_disp"],
        name=f"T&D Losses ({unit_elec})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(239,68,68,0.18)",
        line=dict(color=RED, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>T&D Losses</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["efficiency_pct"],
        name="Grid Efficiency %",
        mode="lines+markers",
        line=dict(color=GREEN, width=2.5, dash="dot"),
        marker=dict(size=5, color=GREEN),
        hovertemplate="%{y:.1f}%<extra>Grid Efficiency</extra>",
    ), secondary_y=True)

    # Dynamic benchmark line on right axis
    fig.add_hline(y=target_eff,
                  line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" Target {target_eff:.1f}% (Loss ≤{target_loss_benchmark:.1f}%)",
                  annotation_font_size=9, annotation_font_color=AMBER,
                  secondary_y=True)

    _dark_theme(fig, height=380, y_title=f"Energy ({unit_elec})", y2_title="Grid Efficiency (%)")
    fig.update_layout(yaxis2=dict(range=[60, 100], overlaying="y",
                                  side="right", showgrid=False))
    return fig


# ── V3: Import Dependency ─────────────────────────────────────────────────────

def visual3_import_dependency(df: pd.DataFrame, unit_energy: str, factor_energy: float) -> go.Figure:
    """
    Stacked bar: domestic supply vs import share with dependency % line.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No supply stream data for selected filters",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TEXT, size=13))
        _dark_theme(fig, height=380)
        return fig

    df = df.sort_values("calendar_year").copy()
    domestic = df["domestic_supply_toe"] * factor_energy
    imports = df["imports_toe"] * factor_energy
    total = domestic + imports
    dep_pct = (imports / total.replace(0, np.nan)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df["calendar_year"], y=domestic,
        name=f"Domestic Supply ({unit_energy})",
        marker_color=GREEN, opacity=0.85,
        hovertemplate=f"%{{y:,.0f}} {unit_energy}<extra>Domestic</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        x=df["calendar_year"], y=imports,
        name=f"Imports ({unit_energy})",
        marker_color=ORANGE, opacity=0.85,
        hovertemplate=f"%{{y:,.0f}} {unit_energy}<extra>Imports</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=dep_pct,
        name="Import Dependency %",
        mode="lines+markers",
        line=dict(color=RED, width=2.5),
        marker=dict(size=5, color=RED),
        hovertemplate="%{y:.1f}%<extra>Import Dependency</extra>",
    ), secondary_y=True)

    fig.add_hline(y=BENCHMARK_IMPORT_DEPENDENCY_MAX,
                  line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" Benchmark Max ≤{BENCHMARK_IMPORT_DEPENDENCY_MAX:.0f}%",
                  annotation_font_size=9, annotation_font_color=AMBER,
                  secondary_y=True)

    fig.update_layout(barmode="stack")
    _dark_theme(fig, height=380, y_title=f"Primary Supply ({unit_energy})",
                y2_title="Import Dependency (%)")
    fig.update_layout(yaxis2=dict(range=[0, 100], overlaying="y", side="right", showgrid=False))
    return fig


# ── V4: Renewable Capacity Utilisation ───────────────────────────────────────

def visual4_re_utilisation(re_df: pd.DataFrame, unit_elec: str, factor_elec: float,
                            unit_power: str, factor_power: float) -> go.Figure:
    """
    Combo chart: RE installed capacity vs actual generation with utilisation rate (%) line.
    """
    if re_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No renewable energy data available",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TEXT, size=13))
        _dark_theme(fig, height=380)
        return fig

    df = re_df.sort_values("calendar_year").copy()
    re_gen = (df["gen_solar_gwh"].fillna(0) + df["gen_wind_gwh"].fillna(0) +
              df["gen_hydro_gwh"].fillna(0)) * factor_elec
    cap_mw = df["capacity_mw"].fillna(0) * factor_power
    theoretical_gwh = df["capacity_mw"].fillna(0) * 8760 / 1000  # theoretical max GWh
    utilisation = ((re_gen / factor_elec) / theoretical_gwh.replace(0, np.nan)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df["calendar_year"], y=cap_mw,
        name=f"Installed Capacity ({unit_power})",
        marker_color=PURPLE, opacity=0.75,
        hovertemplate=f"%{{y:,.0f}} {unit_power}<extra>Installed Capacity</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=re_gen,
        name=f"RE Generation ({unit_elec})",
        mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=5, color=GREEN),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>RE Generation</extra>",
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=utilisation,
        name="Utilisation Rate %",
        mode="lines+markers",
        line=dict(color=CYAN, width=2, dash="dot"),
        marker=dict(size=4, color=CYAN),
        hovertemplate="%{y:.1f}%<extra>Utilisation Rate</extra>",
    ), secondary_y=True)

    _dark_theme(fig, height=380, y_title=f"Installed Capacity ({unit_power})",
                y2_title=f"Generation ({unit_elec}) / Utilisation (%)")
    return fig


# ── V5: Gas Supply Chain ─────────────────────────────────────────────────────

def visual5_gas_supply_chain(df: pd.DataFrame, lng_df: pd.DataFrame,
                             unit_gas: str = "BCF", factor_gas: float = 1.0) -> go.Figure:
    """
    Gas production, consumption, gap, and LNG top-up with self-sufficiency %.
    Unit-aware (BCF, MMSCF, TCF).
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No natural gas balance data available",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TEXT, size=13))
        _dark_theme(fig, height=380)
        return fig

    df = df.sort_values("calendar_year").copy()
    prod_disp = df["production_bcf"] * factor_gas
    cons_disp = df["consumption_bcf"] * factor_gas
    self_suf = (df["production_bcf"] / df["consumption_bcf"].replace(0, np.nan)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=prod_disp,
        name=f"Domestic Production ({unit_gas})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(16,185,129,0.15)",
        line=dict(color=GREEN, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>Production</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=cons_disp,
        name=f"Total Consumption ({unit_gas})",
        mode="lines",
        line=dict(color=ORANGE, width=2, dash="dash"),
        hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>Consumption</extra>",
    ), secondary_y=False)

    # LNG imports if available
    if not lng_df.empty:
        lng_merged = pd.merge(df[["calendar_year"]], lng_df, on="calendar_year", how="left").fillna(0)
        lng_disp = lng_merged["imports_bcf"] * factor_gas
        fig.add_trace(go.Bar(
            x=lng_merged["calendar_year"], y=lng_disp,
            name=f"LNG Imports ({unit_gas})",
            marker_color=ROSE, opacity=0.7,
            hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>LNG Imports</extra>",
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=self_suf,
        name="Gas Self-Sufficiency %",
        mode="lines+markers",
        line=dict(color=CYAN, width=2.5, dash="dot"),
        marker=dict(size=5, color=CYAN),
        hovertemplate="%{y:.1f}%<extra>Self-Sufficiency</extra>",
    ), secondary_y=True)

    fig.add_hline(y=BENCHMARK_GAS_SELFSUFFICIENCY,
                  line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" Target {BENCHMARK_GAS_SELFSUFFICIENCY:.0f}%",
                  annotation_font_size=9, annotation_font_color=AMBER,
                  secondary_y=True)

    fig.update_layout(barmode="overlay")
    _dark_theme(fig, height=380, y_title=f"Volume ({unit_gas})", y2_title="Self-Sufficiency (%)")
    fig.update_layout(yaxis2=dict(range=[0, 115], overlaying="y", side="right", showgrid=False))
    return fig


# ── V6: LNG Cost vs Volume ────────────────────────────────────────────────────

def visual6_lng_cost(lng_df: pd.DataFrame, unit_gas: str = "BCF", factor_gas: float = 1.0) -> go.Figure:
    """
    Dual-axis: LNG import volumes vs cost (MUSD) line,
    with unit-cost efficiency trend.
    """
    if lng_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No LNG import data available",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TEXT, size=14))
        _dark_theme(fig, height=380)
        return fig

    df = lng_df.sort_values("calendar_year").copy()
    vol_disp = df["imports_bcf"] * factor_gas
    cost_per_unit = df["imports_value_musd"] / vol_disp.replace(0, np.nan)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df["calendar_year"], y=vol_disp,
        name=f"LNG Volume ({unit_gas})",
        marker=dict(color=BLUE, opacity=0.8),
        hovertemplate=f"%{{y:,.1f}} {unit_gas}<extra>LNG Volume</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["imports_value_musd"],
        name="Import Cost (MUSD)",
        mode="lines+markers",
        line=dict(color=RED, width=2.5),
        marker=dict(size=6, color=RED),
        hovertemplate="$%{y:,.0f}M<extra>LNG Cost</extra>",
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=cost_per_unit,
        name=f"Cost per {unit_gas} (MUSD/{unit_gas})",
        mode="lines+markers",
        line=dict(color=AMBER, width=2, dash="dot"),
        marker=dict(size=4, color=AMBER),
        hovertemplate=f"$%{{y:,.2f}}M/{unit_gas}<extra>Unit Cost</extra>",
    ), secondary_y=True)

    _dark_theme(fig, height=380, y_title=f"LNG Volume ({unit_gas})",
                y2_title=f"Cost (MUSD) / Unit Cost (MUSD/{unit_gas})")
    return fig


# ── V7: Composite Optimization Score ─────────────────────────────────────────

def visual7_optimization_score(score_df: pd.DataFrame, strategy_name: str = "Balanced") -> go.Figure:
    """
    Area chart of the composite supply-chain optimization score (0-100)
    over time with individual dimension lines.
    """
    if score_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No optimization scores computed",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TEXT, size=13))
        _dark_theme(fig, height=380)
        return fig

    df = score_df.sort_values("calendar_year").copy()
    dim_colors = {
        "transmission_efficiency": BLUE,
        "re_utilisation": GREEN,
        "import_dependency": ORANGE,
        "fuel_waste_reduction": TEAL,
        "gas_self_sufficiency": CYAN,
    }
    dim_labels = {
        "transmission_efficiency": "Transmission Efficiency",
        "re_utilisation": "RE Utilisation",
        "import_dependency": "Import Independence",
        "fuel_waste_reduction": "Fuel Waste Reduction",
        "gas_self_sufficiency": "Gas Self-Sufficiency",
    }

    fig = go.Figure()

    # Individual dimensions
    for dim, color in dim_colors.items():
        if dim in df.columns:
            fig.add_trace(go.Scatter(
                x=df["calendar_year"], y=df[dim],
                name=dim_labels[dim],
                mode="lines",
                line=dict(color=color, width=1.5, dash="dot"),
                opacity=0.65,
                hovertemplate=f"%{{y:.1f}}/100<extra>{dim_labels[dim]}</extra>",
            ))

    # Composite score
    if "composite_score" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["calendar_year"], y=df["composite_score"],
            name=f"Composite Score ({strategy_name})",
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0,166,251,0.14)",
            line=dict(color=BLUE, width=3),
            marker=dict(size=6, color=BLUE),
            hovertemplate="%{y:.1f}/100<extra>Composite Score</extra>",
        ))

    fig.add_hline(y=75, line=dict(color=GREEN, width=1.4, dash="dot"),
                  annotation_text=" Optimal ≥75", annotation_font_size=9,
                  annotation_font_color=GREEN)
    fig.add_hline(y=50, line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=" Adequate ≥50", annotation_font_size=9,
                  annotation_font_color=AMBER)

    _dark_theme(fig, height=380, y_title="Score (0–100)")
    fig.update_yaxes(range=[0, 105])
    return fig


# ── V8: Optimal Mix Simulation ───────────────────────────────────────────────

def visual8_optimal_mix(re_share_pct: float, fuel_share_pct: float,
                         unit_elec: str, baseline_gen_gwh: float,
                         factor_elec: float,
                         baseline_data: dict | None = None) -> go.Figure:
    """
    Donut + bar comparison: actual reported generation mix vs user-defined optimal mix.
    baseline_data: dictionary of real generation GWh by source from the database.
    """
    labels = ["Hydro", "Solar", "Wind", "Nuclear", "Gas Thermal", "Coal"]
    colors = [TEAL, AMBER, CYAN, PURPLE, ORANGE, RED]

    # Read actual values or defaults
    if baseline_data and isinstance(baseline_data, dict):
        hydro_g = float(baseline_data.get("gen_hydro_gwh", 38270.0) or 38270.0)
        solar_g = float(baseline_data.get("gen_solar_gwh", 19830.0) or 19830.0)
        wind_g = float(baseline_data.get("gen_wind_gwh", 5500.0) or 5500.0)
        nuc_g = float(baseline_data.get("gen_nuclear_gwh", 22400.0) or 22400.0)
        gas_g = float(baseline_data.get("gen_gas_gwh", 43980.0) or 43980.0)
        coal_g = float(baseline_data.get("gen_coal_gwh", 24360.0) or 24360.0)
        target_year = baseline_data.get("calendar_year", 2024)
    else:
        hydro_g, solar_g, wind_g, nuc_g, gas_g, coal_g = 38270.0, 19830.0, 5500.0, 22400.0, 43980.0, 24360.0
        target_year = 2024

    total_actual = hydro_g + solar_g + wind_g + nuc_g + gas_g + coal_g
    if total_actual <= 0:
        total_actual = 154340.0

    # Calculate actual percentage shares
    values_current = [
        (hydro_g / total_actual) * 100,
        (solar_g / total_actual) * 100,
        (wind_g / total_actual) * 100,
        (nuc_g / total_actual) * 100,
        (gas_g / total_actual) * 100,
        (coal_g / total_actual) * 100,
    ]

    # Current renewable vs fossil components
    re_curr = values_current[0] + values_current[1] + values_current[2]  # Hydro + Solar + Wind
    fossil_curr = values_current[4] + values_current[5]                  # Gas + Coal
    nuc_curr = values_current[3]                                         # Nuclear baseload

    # Scale to optimal targets
    scale_re = (re_share_pct / re_curr) if re_curr > 0 else 1.0
    scale_fossil = (fuel_share_pct / fossil_curr) if fossil_curr > 0 else 1.0

    values_optimal = [
        values_current[0] * scale_re,     # Hydro
        values_current[1] * scale_re,     # Solar
        values_current[2] * scale_re,     # Wind
        nuc_curr,                         # Nuclear kept stable
        values_current[4] * scale_fossil, # Gas
        values_current[5] * scale_fossil, # Coal
    ]
    total_opt = sum(values_optimal)
    values_optimal = [(v / total_opt) * 100 for v in values_optimal]

    # Converted volumes in selected unit
    total_vol_disp = (baseline_gen_gwh if baseline_gen_gwh > 0 else total_actual) * factor_elec

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=[
            f"Historical Baseline Mix ({target_year})",
            f"Optimized Target Portfolio ({re_share_pct:.0f}% RE / {fuel_share_pct:.0f}% Conv)",
        ],
    )

    fig.add_trace(go.Pie(
        labels=labels,
        values=values_current,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#14171E", width=1.5)),
        textfont=dict(size=10, color="white"),
        hovertemplate="%{label}: %{value:.1f}%<extra>Reported Baseline</extra>",
        showlegend=True,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=labels, y=values_optimal,
        marker=dict(color=colors, opacity=0.88),
        hovertemplate=f"%{{x}}: %{{y:.1f}}% (~%{{customdata:,.0f}} {unit_elec})<extra>Optimized Target</extra>",
        customdata=[v / 100 * total_vol_disp for v in values_optimal],
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        height=360,
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                    font=dict(size=10, color=_TEXT)),
        font=dict(family="Inter, sans-serif", color=_TEXT),
        margin=dict(l=40, r=40, t=55, b=80),
    )
    fig.update_annotations(font_size=11.5, font_color=_TEXT)
    fig.update_xaxes(gridcolor=_AXIS, tickfont=dict(size=9.5, color=_TICK),
                     title_text="Generation Source", row=1, col=2)
    fig.update_yaxes(gridcolor=_AXIS, tickfont=dict(size=9.5, color=_TICK),
                     title_text="Generation Share (%)", row=1, col=2)
    return fig
