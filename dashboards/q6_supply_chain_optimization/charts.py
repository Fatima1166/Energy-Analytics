"""
dashboards/q6_supply_chain_optimization/charts.py
Five Plotly figures for Question 6 (how well the fuel and renewable supply
chains are being used).

V1  Score over time          -- the overall score and its four parts, year by year
V2  Grid losses              -- electricity made vs electricity that arrives
V3  Clean plant use          -- plant built vs what it actually makes
V4  The gas chain            -- gas made at home, gas used, and the gas bought by ship
V5  Best mix                 -- what is made now and what the target mix looks like
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import (
    BENCHMARK_GAS_SELFSUFFICIENCY,
    BLUE, GREEN, AMBER, RED, PURPLE, TEAL, CYAN, ORANGE, ROSE,
    SCORE_FAIR, SCORE_GOOD,
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


def _empty(message: str) -> go.Figure:
    """A dark panel that simply says there is nothing to draw."""
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, height=380, x_title=None)


# ── V1: Score over time ──────────────────────────────────────────────────────

_PART_WORDS = {
    "grid_efficiency": "Electricity that arrives",
    "re_utilisation": "Clean plant used well",
    "import_independence": "Less bought from abroad",
    "gas_self_sufficiency": "Gas made at home",
}
_PART_COLOURS = {
    "grid_efficiency": BLUE,
    "re_utilisation": GREEN,
    "import_independence": ORANGE,
    "gas_self_sufficiency": CYAN,
}


def visual1_score_over_time(score_df: pd.DataFrame) -> go.Figure:
    """The overall score (thick line) and each of its four parts (thin lines)."""
    if score_df.empty:
        return _empty("No scores to show for these years")

    df = score_df.sort_values("calendar_year")

    fig = go.Figure()
    for part, label in _PART_WORDS.items():
        if part not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["calendar_year"], y=df[part],
            name=label,
            mode="lines",
            line=dict(color=_PART_COLOURS[part], width=1.5, dash="dot"),
            opacity=0.7,
            hovertemplate=f"%{{y:.0f}}/100<extra>{label}</extra>",
            connectgaps=False,
        ))

    if "composite_score" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["calendar_year"], y=df["composite_score"],
            name="Overall score",
            mode="lines+markers",
            fill="tozeroy",
            fillcolor="rgba(0,166,251,0.14)",
            line=dict(color=BLUE, width=3),
            marker=dict(size=6, color=BLUE),
            hovertemplate="%{y:.1f}/100<extra>Overall score</extra>",
            connectgaps=False,
        ))

    fig.add_hline(y=SCORE_GOOD, line=dict(color=GREEN, width=1.4, dash="dot"),
                  annotation_text=f" Working well from {SCORE_GOOD:.0f}",
                  annotation_font_size=9, annotation_font_color=GREEN)
    fig.add_hline(y=SCORE_FAIR, line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" All right from {SCORE_FAIR:.0f}",
                  annotation_font_size=9, annotation_font_color=AMBER)

    _dark_theme(fig, height=400, y_title="Score (0–100)  —  higher is better")
    fig.update_yaxes(range=[0, 105])
    # The legend sits below the chart in its own row (never to the side),
    # wrapping across up to two lines so all five names still fit the
    # half-width slot.
    fig.update_layout(
        margin=dict(l=58, r=46, t=45, b=92),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22,
                    itemsizing="constant", bgcolor="rgba(0,0,0,0)",
                    font=dict(size=9.5, color=_TEXT)),
    )
    return fig


# ── V2: Grid losses ──────────────────────────────────────────────────────────

def visual2_grid_losses(df: pd.DataFrame, unit_elec: str, factor_elec: float,
                        target_loss_benchmark: float = 15.0) -> go.Figure:
    """How much electricity was made, how much was lost on the wires, and
    the share that arrived."""
    if df.empty:
        return _empty("No grid loss records for these years")

    df = df.sort_values("calendar_year").copy()
    df["gen_disp"] = df["gen_gwh"] * factor_elec
    df["loss_disp"] = df["td_losses_gwh"] * factor_elec
    df["arrived_pct"] = (1 - df["td_losses_gwh"] / df["gen_gwh"].replace(0, np.nan)) * 100

    target_arrived = 100.0 - target_loss_benchmark

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["gen_disp"],
        name=f"Electricity made ({unit_elec})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(0,166,251,0.10)",
        line=dict(color=BLUE, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>Made</extra>",
        connectgaps=False,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["loss_disp"],
        name=f"Lost on the wires ({unit_elec})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(239,68,68,0.18)",
        line=dict(color=RED, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>Lost on the wires</extra>",
        connectgaps=False,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=df["arrived_pct"],
        name="Share that arrived (%)",
        mode="lines+markers",
        line=dict(color=GREEN, width=2.5, dash="dot"),
        marker=dict(size=5, color=GREEN),
        hovertemplate="%{y:.1f}%<extra>Share that arrived</extra>",
        connectgaps=False,
    ), secondary_y=True)

    fig.add_hline(y=target_arrived,
                  line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" Aim: at least {target_arrived:.1f}% arrives (loss under {target_loss_benchmark:.1f}%)",
                  annotation_font_size=9, annotation_font_color=AMBER,
                  secondary_y=True)

    _dark_theme(fig, height=380, y_title=f"Electricity ({unit_elec})",
                y2_title="Share that arrived (%)")
    fig.update_layout(yaxis2=dict(range=[60, 100], overlaying="y",
                                  side="right", showgrid=False))
    return fig


# ── V3: Clean plant use ──────────────────────────────────────────────────────

def visual3_renewable_plant_use(re_df: pd.DataFrame, unit_elec: str, factor_elec: float,
                                unit_power: str, factor_power: float) -> go.Figure:
    """Clean plant built, what it actually made, and the share of what it could
    make."""
    if re_df.empty:
        return _empty("No clean plant records for these years")

    df = re_df.sort_values("calendar_year").copy()
    re_gen = (df["gen_solar_gwh"] + df["gen_wind_gwh"] + df["gen_hydro_gwh"]) * factor_elec
    cap_mw = df["capacity_mw"] * factor_power
    potential_gwh = df["capacity_mw"] * 8760 / 1000  # what it could make in a year
    used_pct = ((re_gen / factor_elec) / potential_gwh.replace(0, np.nan)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df["calendar_year"], y=cap_mw,
        name=f"Plant built ({unit_power})",
        marker_color=PURPLE, opacity=0.75,
        hovertemplate=f"%{{y:,.0f}} {unit_power}<extra>Plant built</extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=re_gen,
        name=f"What it made ({unit_elec})",
        mode="lines+markers",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=5, color=GREEN),
        hovertemplate=f"%{{y:,.0f}} {unit_elec}<extra>What it made</extra>",
        connectgaps=False,
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=used_pct,
        name="Share of what it could make (%)",
        mode="lines+markers",
        line=dict(color=CYAN, width=2, dash="dot"),
        marker=dict(size=4, color=CYAN),
        hovertemplate="%{y:.1f}%<extra>Share of what it could make</extra>",
        connectgaps=False,
    ), secondary_y=True)

    _dark_theme(fig, height=380, y_title=f"Plant built ({unit_power})",
                y2_title=f"Made ({unit_elec}) / share made (%)")
    return fig


# ── V4: The gas chain ────────────────────────────────────────────────────────

def visual4_gas_chain(df: pd.DataFrame, lng_df: pd.DataFrame,
                      unit_gas: str = "BCF", factor_gas: float = 1.0) -> go.Figure:
    """Gas made at home, gas used, the gas bought by ship to cover the gap, and
    how much of the demand the country met itself."""
    if df.empty:
        return _empty("No gas made or used in these years")

    df = df.sort_values("calendar_year").copy()
    prod_disp = df["production_bcf"] * factor_gas
    cons_disp = df["consumption_bcf"] * factor_gas
    met_at_home = (df["production_bcf"] / df["consumption_bcf"].replace(0, np.nan)) * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=prod_disp,
        name=f"Made at home ({unit_gas})",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(16,185,129,0.15)",
        line=dict(color=GREEN, width=2),
        hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>Made at home</extra>",
        connectgaps=False,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=cons_disp,
        name=f"Gas used ({unit_gas})",
        mode="lines",
        line=dict(color=ORANGE, width=2, dash="dash"),
        hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>Gas used</extra>",
        connectgaps=False,
    ), secondary_y=False)

    if not lng_df.empty:
        # Left join keeps NaN for a year LNG was not reported; a bar simply is
        # not drawn there.  Filling 0 would print "no gas arrived by ship",
        # which is a claim about an unreported year.
        lng_merged = pd.merge(df[["calendar_year"]], lng_df,
                              on="calendar_year", how="left")
        lng_merged["imports_bcf"] = pd.to_numeric(lng_merged["imports_bcf"],
                                                  errors="coerce")
        fig.add_trace(go.Bar(
            x=lng_merged["calendar_year"],
            y=lng_merged["imports_bcf"] * factor_gas,
            name=f"Gas bought by ship ({unit_gas})",
            marker_color=ROSE, opacity=0.7,
            hovertemplate=f"%{{y:,.0f}} {unit_gas}<extra>Gas bought by ship</extra>",
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df["calendar_year"], y=met_at_home,
        name="Met at home (%)",
        mode="lines+markers",
        line=dict(color=CYAN, width=2.5, dash="dot"),
        marker=dict(size=5, color=CYAN),
        hovertemplate="%{y:.1f}%<extra>Met at home</extra>",
        connectgaps=False,
    ), secondary_y=True)

    fig.add_hline(y=BENCHMARK_GAS_SELFSUFFICIENCY,
                  line=dict(color=AMBER, width=1.4, dash="dot"),
                  annotation_text=f" Aim {BENCHMARK_GAS_SELFSUFFICIENCY:.0f}%",
                  annotation_font_size=9, annotation_font_color=AMBER,
                  secondary_y=True)

    fig.update_layout(barmode="overlay")
    _dark_theme(fig, height=380, y_title=f"Gas ({unit_gas})",
                y2_title="Gas demand met at home (%)")
    fig.update_layout(yaxis2=dict(range=[0, 115], overlaying="y", side="right", showgrid=False))
    return fig


# ── V5: Best mix ─────────────────────────────────────────────────────────────

def visual5_best_mix(re_share_pct: float, fuel_share_pct: float,
                     unit_elec: str, factor_elec: float,
                     baseline_data: Optional[dict] = None) -> go.Figure:
    """What is made now (left) and what the year would look like if the clean and
    fuel targets were met (right)."""
    labels = ["Hydro", "Solar", "Wind", "Nuclear", "Gas", "Coal"]
    colors = [TEAL, AMBER, CYAN, PURPLE, ORANGE, RED]

    if isinstance(baseline_data, dict):
        hydro_g = float(baseline_data.get("gen_hydro_gwh", 0) or 0)
        solar_g = float(baseline_data.get("gen_solar_gwh", 0) or 0)
        wind_g = float(baseline_data.get("gen_wind_gwh", 0) or 0)
        nuc_g = float(baseline_data.get("gen_nuclear_gwh", 0) or 0)
        gas_g = float(baseline_data.get("gen_gas_gwh", 0) or 0)
        coal_g = float(baseline_data.get("gen_coal_gwh", 0) or 0)
        shown_year = baseline_data.get("calendar_year", "")
    else:
        hydro_g = solar_g = wind_g = nuc_g = gas_g = coal_g = 0.0
        shown_year = ""

    total_actual = hydro_g + solar_g + wind_g + nuc_g + gas_g + coal_g
    if total_actual <= 0:
        return _empty("No record of what each source made in that year")

    now = [g / total_actual * 100 for g in (hydro_g, solar_g, wind_g, nuc_g, gas_g, coal_g)]

    clean_now = now[0] + now[1] + now[2]           # hydro + solar + wind
    fuel_now = now[4] + now[5]                     # gas + coal
    nuclear = now[3]                               # held where it is

    # The target splits everything except nuclear, which keeps the share it
    # already has.  Scaling both halves to the target and then squeezing the
    # total back to 100% would land the result under its own target.
    rest = 100.0 - nuclear
    scale_clean = (rest * re_share_pct / 100.0 / clean_now) if clean_now > 0 else 0.0
    scale_fuel = (rest * fuel_share_pct / 100.0 / fuel_now) if fuel_now > 0 else 0.0

    target = [now[0] * scale_clean, now[1] * scale_clean, now[2] * scale_clean,
              nuclear, now[4] * scale_fuel, now[5] * scale_fuel]

    total_vol_disp = total_actual * factor_elec

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=[
            f"What is made now{f' ({shown_year})' if shown_year else ''}",
            f"Target met: {re_share_pct:.0f}% clean, {fuel_share_pct:.0f}% fuel "
            f"(nuclear unchanged)",
        ],
    )

    fig.add_trace(go.Pie(
        labels=labels,
        values=now,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#14171E", width=1.5)),
        textfont=dict(size=10, color="white"),
        hovertemplate="%{label}: %{value:.1f}%<extra>made now</extra>",
        showlegend=True,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=labels, y=target,
        marker=dict(color=colors, opacity=0.88),
        hovertemplate=f"%{{x}}: %{{y:.1f}}% (~%{{customdata:,.0f}} {unit_elec})<extra>if target met</extra>",
        customdata=[v / 100 * total_vol_disp for v in target],
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        height=380,
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                    font=dict(size=10, color=_TEXT)),
        font=dict(family="Inter, sans-serif", color=_TEXT),
        margin=dict(l=40, r=40, t=55, b=80),
    )
    fig.update_annotations(font_size=11.5, font_color=_TEXT)
    fig.update_xaxes(gridcolor=_AXIS, tickfont=dict(size=9.5, color=_TICK),
                     title_text="Source", row=1, col=2)
    fig.update_yaxes(gridcolor=_AXIS, tickfont=dict(size=9.5, color=_TICK),
                     title_text="Share of electricity (%)", row=1, col=2)
    return fig
