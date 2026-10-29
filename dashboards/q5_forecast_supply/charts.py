"""
dashboards/q5_forecast_supply/charts.py -- the six charts for Forecasted Energy
Supply (question 5).

  V1  Supply so far        -- primary energy by source, and electricity by source
  V2  Three ways supply can go -- slow, planned and fast growth to the horizon
  V3  What the electricity is made of -- each source, and the clean share
  V4  Does supply cover demand -- supply next to the demand question 4 forecasts
  V5  Where the supply comes from -- made at home vs bought from abroad
  V6  How far to trust it   -- average error on years the model had not seen

Every chart is drawn the same way: the years we were told about are solid, the
years the model guesses are dashed, so a guessed figure is never mistaken for a
real one.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.supply_forecast import (
    CLEAN_POLICY_TARGET_DEFAULT,
    HISTORY_END,
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


def _boundary(fig, year: Optional[int] = HISTORY_END, text: str = "Measured here ◀ | ▶ Forecast"):
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


# ═══════════════════════════ V1: supply so far ═══════════════════════════════

def visual1_history_trajectory(
    hist: pd.DataFrame,
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Left: all the energy the country had, by source.  Right: the electricity it
    generated, by source.  Both are stacked, so the height is the total."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"Energy supplied, by source ({unit_energy})",
            f"Electricity generated, by source ({unit_elec})",
        ),
        horizontal_spacing=0.10,
    )

    h_pes = hist[hist["calendar_year"] >= 2002].copy()

    pes_sources = [
        ("pes_gas_toe", "Natural Gas", "#F97316"),
        ("pes_oil_toe", "Oil", "#EF4444"),
        ("pes_coal_toe", "Coal", "#6B7280"),
        ("pes_hydro_toe", "Hydro", "#0284C7"),
        ("pes_nuclear_toe", "Nuclear", "#A78BFA"),
        ("pes_renewables_toe", "Solar & wind", "#10B981"),
    ]
    # A source the record never reports is left off the stack; a source that
    # reports in some years is not -- an unreported year would otherwise be
    # drawn as "that source supplied nothing".
    present_pes = [(c, n, colr) for c, n, colr in pes_sources
                   if c in h_pes.columns and h_pes[c].notna().any()]
    # A stacked area has no way to show a gap, so the stack keeps only the years
    # in which every source it draws has a reading.
    if present_pes:
        _cols = [c for c, _, _ in present_pes]
        h_pes = h_pes[h_pes[_cols].notna().all(axis=1)]
    years_p = h_pes["calendar_year"].values

    for col, name, colr in present_pes:
        vals = h_pes[col].values * factor_energy
        fig.add_trace(
            go.Scatter(
                x=years_p, y=vals, name=name, mode="lines",
                stackgroup="pes", line=dict(width=0.8, color=colr),
                fillcolor=colr, legendgroup="pes",
                hovertemplate=f"{name}: %{{y:,.1f}} {unit_energy}<extra></extra>",
            ),
            row=1, col=1,
        )

    # Right: electricity generated by each source
    h_gen = hist[hist["calendar_year"] >= 2000].copy()

    gen_sources = [
        ("gen_hydro_gwh", "Hydro", "#0284C7"),
        ("gen_solar_gwh", "Solar", "#F59E0B"),
        ("gen_wind_gwh", "Wind", "#10B981"),
        ("gen_nuclear_gwh", "Nuclear", "#A78BFA"),
        ("gen_coal_gwh", "Coal", "#6B7280"),
        ("gen_gas_gwh", "Natural Gas", "#F97316"),
    ]
    present_gen = [(c, n, colr) for c, n, colr in gen_sources
                   if c in h_gen.columns and h_gen[c].notna().any()]
    if present_gen:
        _gcols = [c for c, _, _ in present_gen]
        h_gen = h_gen[h_gen[_gcols].notna().all(axis=1)]
    years_g = h_gen["calendar_year"].values

    for col, name, colr in present_gen:
        vals = h_gen[col].values * factor_elec
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
    fig.update_yaxes(title_text=f"Primary energy ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text=f"Electricity generated ({unit_elec})", row=1, col=2)
    return _dark_theme(fig, height=390, legend_h=True, x_title=None)


# ═══════════════════════ V2: the three supply paths ══════════════════════════

def visual2_scenario_fans(
    hist: pd.DataFrame,
    forecast: pd.DataFrame,
    scenarios: List[str] = SCENARIO_ORDER,
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Left: total energy supply, right: electricity supply.  Both show the years we
    were told about and the slow, planned and fast paths forward."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"How total energy supply grows ({unit_energy})",
            f"How electricity supply grows ({unit_elec})",
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

        # The solid line: years we were told about
        fig.add_trace(
            go.Scatter(
                x=x_hist, y=y_hist, name=f"Measured {unit_lbl}",
                mode="lines+markers",
                marker=dict(size=4, color="#E2E8F0"),
                line=dict(color="#E2E8F0", width=2.4),
                showlegend=(col_idx == 1),
                hovertemplate=f"Measured: %{{y:,.1f}} {unit_lbl}<extra></extra>",
                connectgaps=False,
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
                        name="Between slow and fast",
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
                            x=x_sc, y=y_sc, name=f"{sc} case",
                            mode="lines+markers",
                            marker=dict(size=4, color=clr),
                            line=dict(color=clr, width=2.2, dash="dash" if sc != "Base" else "solid"),
                            showlegend=(col_idx == 1),
                            hovertemplate=f"{sc}: %{{y:,.1f}} {unit_lbl}<extra></extra>",
                            connectgaps=False,
                        ),
                        row=1, col=col_idx,
                    )

        # Where the telling ends and the guessing begins
        _boundary(fig, HISTORY_END)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=f"Primary energy ({unit_energy})", row=1, col=1)
    fig.update_yaxes(title_text=f"Electricity generated ({unit_elec})", row=1, col=2)
    return _dark_theme(fig, height=390, legend_h=True, x_title=None)


# ═══════════════════════ V3: what the electricity is made of ═════════════════

def visual3_technology_mix(
    tech_mix: pd.DataFrame,
    active_scenario: str = "Base",
    clean_target: float = CLEAN_POLICY_TARGET_DEFAULT,
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Stacked areas show which sources generate the power; the line on the right
    axis shows how big a share is clean, next to the two agreed goals."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # The chosen path, with the years we were told about in front of it
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

    # How big a share is clean, on the right axis
    clean_pct = sub["clean_share_pct"].values
    fig.add_trace(
        go.Scatter(
            x=years, y=clean_pct, name="Clean share (%)",
            mode="lines+markers",
            line=dict(color="#22D3EE", width=2.8),
            marker=dict(size=5, color="#22D3EE"),
            hovertemplate="Clean share: %{y:.1f}%<extra></extra>",
            connectgaps=False,
        ),
        secondary_y=True,
    )

    # The two agreed goals (labels on the left so they do not sit on top of the
    # right-axis numbers or the last year on the bottom axis)
    fig.add_hline(
        y=clean_target, line=dict(color="#10B981", width=1.8, dash="dot"),
        annotation_text=f"Clean goal ({clean_target:.0f}%)",
        annotation_position="top left", annotation_font=dict(size=10, color="#10B981"),
        secondary_y=True,
    )
    fig.add_hline(
        y=30.0, line=dict(color="#F59E0B", width=1.5, dash="dot"),
        annotation_text="Renewables goal (30%)",
        annotation_position="bottom left", annotation_font=dict(size=10, color="#F59E0B"),
        secondary_y=True,
    )

    _boundary(fig, HISTORY_END)
    fig.update_yaxes(title_text=f"Electricity generated ({unit_elec})", secondary_y=False)
    fig.update_yaxes(title_text="Clean share of electricity (%)", range=[0, 100], secondary_y=True)

    return _dark_theme(fig, height=400, legend_h=True)


# ═══════════════════════ V4: does supply cover demand ════════════════════════

def visual4_supply_vs_demand(
    adequacy_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_elec: str = "GWh",
    factor_elec: float = 1.0,
) -> go.Figure:
    """Electricity supply next to the demand it has to meet.  Where the blue line
    is above the amber one, there is spare supply."""
    fig = go.Figure()

    sub = adequacy_df[(adequacy_df["scenario"] == active_scenario) | (adequacy_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    supp_vals = sub["supply_gwh"].values * factor_elec
    dem_vals = sub["demand_gwh"].values * factor_elec

    fig.add_trace(
        go.Scatter(
            x=years, y=supp_vals, name="Electricity supply",
            mode="lines+markers",
            line=dict(color="#00A6FB", width=2.5),
            marker=dict(size=4, color="#00A6FB"),
            hovertemplate=f"Supply: %{{y:,.1f}} {unit_elec}<extra></extra>",
            connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=dem_vals, name="Demand",
            mode="lines",
            line=dict(color="#F59E0B", width=2.2, dash="dash"),
            fill="tonexty", fillcolor="rgba(16, 185, 129, 0.13)",
            hovertemplate=f"Demand: %{{y:,.1f}} {unit_elec}<extra></extra>",
            connectgaps=False,
        )
    )

    _boundary(fig, HISTORY_END)
    return _dark_theme(fig, height=380, y_title=f"Electricity ({unit_elec})", legend_h=True)


# ═══════════════════════ V5: where the supply comes from ═════════════════════

def visual5_domestic_vs_imports(
    security_df: pd.DataFrame,
    active_scenario: str = "Base",
    unit_energy: str = "TOE",
    factor_energy: float = 1.0,
) -> go.Figure:
    """Stacked: how much energy was made at home and how much was bought from
    abroad.  The line on the right axis is the imported share."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    sub = security_df[(security_df["scenario"] == active_scenario) | (security_df["scenario"] == "Actual")].copy()
    sub = sub.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
    years = sub["calendar_year"].values

    dom_vals = sub["domestic_toe"].values * factor_energy
    imp_vals = sub["imports_toe"].values * factor_energy
    imp_share = sub["import_share_pct"].values

    fig.add_trace(
        go.Scatter(
            x=years, y=dom_vals, name="Made at home",
            mode="lines", stackgroup="sec",
            line=dict(width=0.8, color="#10B981"), fillcolor="#10B981",
            hovertemplate=f"Made at home: %{{y:,.1f}} {unit_energy}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=years, y=imp_vals, name="Bought from abroad",
            mode="lines", stackgroup="sec",
            line=dict(width=0.8, color="#EF4444"), fillcolor="#EF4444",
            hovertemplate=f"Bought abroad: %{{y:,.1f}} {unit_energy}<extra></extra>",
        ),
        secondary_y=False,
    )

    # How much of the supply is imported, on the right axis
    fig.add_trace(
        go.Scatter(
            x=years, y=imp_share, name="Imported share (%)",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2.4),
            marker=dict(size=4, color="#F59E0B"),
            hovertemplate="Imported share: %{y:.1f}%<extra></extra>",
            connectgaps=False,
        ),
        secondary_y=True,
    )

    _boundary(fig, HISTORY_END)
    fig.update_yaxes(title_text=f"Energy supply ({unit_energy})", secondary_y=False)
    fig.update_yaxes(title_text="Imported share (%)", range=[0, 60], secondary_y=True)

    return _dark_theme(fig, height=380, legend_h=True)


# ═══════════════════════════ V6: how far to trust it ══════════════════════════

# The plain words the reader sees instead of the engine's series and model names.
_SERIES_WORDS = {
    "Primary Energy Supply": "Total energy supply",
    "Electricity Generation": "Electricity generated",
    "Clean Generation": "Clean electricity",
}
_MODEL_WORDS = {
    "Driver": "follows the economy",
    "Trend": "continues past growth",
}


def visual6_reliability(table: Optional[pd.DataFrame],
                        train_end: int, test_end: int) -> go.Figure:
    """Average error for each series and model, measured on the years the model
    had not been shown.  A shorter bar is a better forecast."""
    if table is None or table.empty:
        fig = go.Figure()
        fig.add_annotation(text="No test results to show", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=13, color=_TICK))
        return _dark_theme(fig, height=420, legend_h=False)

    hold = table.dropna(subset=["mape_pct"]).sort_values("mape_pct")
    if hold.empty:
        fig = go.Figure()
        fig.add_annotation(text="No test results to show", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False,
                           font=dict(size=13, color=_TICK))
        return _dark_theme(fig, height=420, legend_h=False)

    labels = [f"{_SERIES_WORDS.get(row['series_name'], row['series_name'])} · "
              f"{_MODEL_WORDS.get(row['model'], row['model'])}" for _, row in hold.iterrows()]
    colours = ["#10B981" if row["model"] == "Driver" else "#00A6FB"
               for _, row in hold.iterrows()]
    years_tested = max(int(test_end) - int(train_end), 1)

    fig = go.Figure(go.Bar(
        y=labels, x=hold["mape_pct"], orientation="h",
        marker=dict(color=colours),
        text=[f"{v:.1f}%" for v in hold["mape_pct"]], textposition="outside",
        customdata=np.column_stack([hold["bias_pct"], hold["calib_r2"]]),
        hovertemplate=("Average error <b>%{x:.2f}%</b>"
                       "<br>Read as %{customdata[0]:+.1f}% of the real figure"
                       "<br>Fit quality R² %{customdata[1]:.2f}"
                       f"<br>Years tested {years_tested}<extra></extra>"),
    ))
    fig.add_annotation(x=1.0, y=1.12, xref="paper", yref="paper", xanchor="right",
                       text=f"Tested on {int(train_end) + 1}–{int(test_end)}",
                       showarrow=False, font=dict(size=10, color="#94A3B8"))
    return _dark_theme(fig, height=420, legend_h=False,
                       x_title="Average error (%)  — shorter bar is better",
                       y_title="What the model forecasts")
