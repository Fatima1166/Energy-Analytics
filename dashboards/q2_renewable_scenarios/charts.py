import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

from config.settings import SCENARIOS
from core.units import from_base_series, unit_for

# Base (storage) unit of each measure family
GEN_COLS = ["solar_gwh", "wind_gwh", "hydro_gwh", "other_gwh",
            "nuclear_gwh", "gas_gwh", "coal_gwh"]
DFMT = ",.2f"          # plotly/d3 number format used in hover + text labels

# The emission unit codes off the sidebar slider, said in words, so a legend
# or axis title reads "million tonnes" instead of "Mt".
EM_WORDS = {"t": "tonnes", "kt": "thousand tonnes", "Mt": "million tonnes"}


def _conv(df: pd.DataFrame, cols, unit: str, units=None) -> pd.DataFrame:
    """Return a copy of `df` with `cols` converted from base unit -> `unit`."""
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = from_base_series(out[c], unit)
    return out


def _dark_theme(fig, height=360, y_title=None, x_title="Year", legend_h=True):
    """Apply consistent premium dark theme to Plotly figures."""
    legend_cfg = (
        dict(
            orientation="h",
            y=-0.24,
            x=0.5,
            xanchor="center",
            font=dict(size=10.5, color="#C8CDD6"),
        )
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color="#C8CDD6"))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=40, r=30, t=25, b=55),
        height=height,
        legend=legend_cfg,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#232830", font_size=11, font_family="Inter, sans-serif"),
        xaxis=dict(
            gridcolor="#2A2F3A",
            zerolinecolor="#2A2F3A",
            title=dict(text=x_title, font=dict(size=11, color="#8B95A7")) if x_title else None,
            tickfont=dict(size=11, color="#8B95A7"),
        ),
        yaxis=dict(
            gridcolor="#2A2F3A",
            zerolinecolor="#2A2F3A",
            title=dict(text=y_title, font=dict(size=11, color="#8B95A7")) if y_title else None,
            tickfont=dict(size=11, color="#8B95A7"),
        ),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#C8CDD6"),
    )
    return fig


# ---------------- Visual 1: RE Share % Line Chart (Actual + Projected) ----------------
def visual1_re_share_chart(all_scenarios_data: dict, selected_scenario: str,
                           year_range: tuple, units: dict = None):
    """
    Visual 1: Tracks renewable share over time and projects future share under
    the selected scenario. A share is dimensionless, so this chart is not
    affected by the unit slicer.
    """
    fig = go.Figure()
    sel_df = all_scenarios_data[selected_scenario]
    filtered_df = sel_df[(sel_df["calendar_year"] >= year_range[0]) & (sel_df["calendar_year"] <= year_range[1])]
    if filtered_df.empty:
        filtered_df = sel_df.copy()

    # 1. Historical Actual Line (1999 - last reported year)
    hist_df = filtered_df[filtered_df["data_type"] == "Actual"]
    # FY2025-26 is now recorded for generation, so the reported/projection
    # boundary follows the data instead of a hardcoded year.
    actual_end = int(hist_df["calendar_year"].max()) if not hist_df.empty else 2024
    if not hist_df.empty:
        fig.add_trace(go.Scatter(
            x=hist_df["calendar_year"],
            y=hist_df["re_share_pct"],
            name=f"History ({int(hist_df['calendar_year'].min())}–{actual_end})",
            mode="lines+markers",
            line=dict(color="#2ECC71", width=3),
            marker=dict(size=5, color="#2ECC71"),
            hovertemplate="Year: %{x}<br>Renewable share: <b>%{y:.1f}%</b><extra></extra>",
            connectgaps=False,
        ))

    # 2. Add other scenarios as subtle comparison lines
    for sc_name, sc_df in all_scenarios_data.items():
        if sc_name == selected_scenario:
            continue
        sc_slice = sc_df[(sc_df["calendar_year"] >= max(actual_end, year_range[0])) & (sc_df["calendar_year"] <= year_range[1])]
        if sc_slice.empty:
            sc_slice = sc_df[sc_df["calendar_year"] >= actual_end]
        conf = SCENARIOS.get(sc_name, {})
        fig.add_trace(go.Scatter(
            x=sc_slice["calendar_year"],
            y=sc_slice["re_share_pct"],
            name=f"{sc_name}",
            mode="lines",
            line=dict(color=conf.get("color", "#6C7A89"), width=1.5, dash="dot"),
            opacity=0.6,
            hovertemplate=f"Year: %{{x}}<br>{sc_name}: <b>%{{y:.1f}}%</b><extra></extra>",
            connectgaps=False,
        ))

    # 3. Selected Scenario Projection (last actual onwards)
    proj_conn = filtered_df[filtered_df["calendar_year"] >= actual_end]
    sc_conf = SCENARIOS.get(selected_scenario, {})
    sc_color = sc_conf.get("color", "#00A6FB")
    if not proj_conn.empty:
        fig.add_trace(go.Scatter(
            x=proj_conn["calendar_year"],
            y=proj_conn["re_share_pct"],
            name=f"{selected_scenario} (forecast)",
            mode="lines+markers",
            line=dict(color=sc_color, width=3.2, dash="dash"),
            marker=dict(size=6, color=sc_color, symbol="diamond"),
            hovertemplate=f"Year: %{{x}}<br>{selected_scenario}: <b>%{{y:.1f}}%</b><extra></extra>",
            connectgaps=False,
        ))

    # Add vertical indicator at the last reported year
    if year_range[0] <= actual_end <= year_range[1]:
        fig.add_vline(
            x=actual_end, line_width=1.5, line_dash="dash", line_color="#E74C3C",
            annotation_text="Forecast starts here",
            annotation_position="top left",
            annotation_font=dict(size=10, color="#E74C3C"),
        )

    return _dark_theme(fig, height=360, y_title="Renewable share (%)", legend_h=True)


# ---------------- Visual 2: Generation Mix Stacked Column ----------------
def visual2_generation_mix_chart(proj_df: pd.DataFrame, year_range: tuple,
                                 units: dict = None):
    """
    Visual 2: Source-wise generation (Solar, Wind, Hydro, Nuclear, Gas, Coal)
    rendered in the electricity unit chosen in the sidebar.
    """
    u = unit_for(units, "electricity")
    df = proj_df[(proj_df["calendar_year"] >= year_range[0]) &
                 (proj_df["calendar_year"] <= year_range[1])].copy()
    if df.empty:
        df = proj_df.copy()
    df = _conv(df, GEN_COLS, u)

    fig = go.Figure()
    sources = [
        ("Solar", "solar_gwh", "#F4A300"),
        ("Wind", "wind_gwh", "#00A6FB"),
        ("Hydro", "hydro_gwh", "#2ECC71"),
        ("Nuclear", "nuclear_gwh", "#9B59B6"),
        ("Gas", "gas_gwh", "#E67E22"),
        ("Coal", "coal_gwh", "#5C677D"),
    ]

    for label, col, color in sources:
        if col in df.columns:
            fig.add_trace(go.Bar(
                x=df["calendar_year"],
                y=df[col],
                name=label,
                marker_color=color,
                hovertemplate=f"{label}: <b>%{{y:{DFMT}}} {u}</b><extra></extra>",
            ))

    # Boundary follows the last reported year, same as Visual 1.
    if "data_type" in proj_df.columns:
        _a = proj_df.loc[proj_df["data_type"] == "Actual", "calendar_year"]
        boundary = int(_a.max()) if len(_a) else 2024
    else:
        boundary = 2024
    if year_range[0] <= boundary <= year_range[1]:
        fig.add_vline(
            x=boundary + 0.5, line_width=1.5, line_dash="dash", line_color="#E74C3C",
        )

    fig.update_layout(barmode="stack")
    return _dark_theme(fig, height=360, y_title=f"Power made ({u})", legend_h=True)


# ---------------- Visual 3: Scenario Comparison Clustered Bar ----------------
def visual3_scenario_comparison_chart(comparison_df: pd.DataFrame,
                                      target_year: int = 2035,
                                      units: dict = None):
    """
    Visual 3: Compares RE Share (%), CO2 Emissions Avoided and Fossil Avoided
    across all five scenarios, in the selected emission / electricity units.
    """
    e_u = unit_for(units, "electricity")
    em_u = unit_for(units, "emission")

    df = comparison_df.copy()
    df["co2_avoided_disp"] = from_base_series(df["co2_avoided_t"], em_u)
    df["fossil_avoided_disp"] = from_base_series(df["fossil_avoided_gwh"], e_u)

    fig = go.Figure()

    # 1. RE Share %
    fig.add_trace(go.Bar(
        x=df["scenario"],
        y=df["re_share_pct"],
        name=f"Renewable share ({target_year})",
        marker_color="#2ECC71",
        text=df["re_share_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="Scenario: %{x}<br>Renewable share: <b>%{y:.1f}%</b><extra></extra>",
    ))

    # 2. CO2 Avoided
    fig.add_trace(go.Bar(
        x=df["scenario"],
        y=df["co2_avoided_disp"],
        name=f"CO₂ avoided ({EM_WORDS.get(em_u, em_u)} in a year)",
        marker_color="#FF6B6B",
        text=df["co2_avoided_disp"].apply(lambda v: f"{v:,.2f} {em_u}"),
        textposition="outside",
        hovertemplate=f"Scenario: %{{x}}<br>CO₂ avoided: <b>%{{y:{DFMT}}} {em_u}</b><extra></extra>",
    ))

    # 3. Fossil Fuel Avoided
    fig.add_trace(go.Bar(
        x=df["scenario"],
        y=df["fossil_avoided_disp"],
        name=f"Fossil power replaced ({e_u} in a year)",
        marker_color="#F4A300",
        text=df["fossil_avoided_disp"].apply(lambda v: f"{v:,.2f} {e_u}"),
        textposition="outside",
        hovertemplate=f"Scenario: %{{x}}<br>Fossil power replaced: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
    ))

    fig.update_layout(barmode="group", bargap=0.2, bargroupgap=0.1)
    return _dark_theme(fig, height=360, y_title=f"Results in {target_year}", x_title="Scenario", legend_h=True)


# ---------------- Visual 3 (year by year): annual outcomes to the target year ----------------
def visual3_yearly_outcomes_chart(proj_df: pd.DataFrame, year_range: tuple,
                                  units: dict = None):
    """
    Visual 3 (year by year): the annual CO2 emissions avoided and fossil
    generation avoided for the selected scenario, one bar per year up to the
    target year.
    """
    e_u = unit_for(units, "electricity")
    em_u = unit_for(units, "emission")

    df = proj_df.copy()
    if "data_type" in df.columns:
        df = df[df["data_type"] == "Projected"]
    df = df[(df["calendar_year"] >= year_range[0]) &
            (df["calendar_year"] <= year_range[1])].copy()
    if df.empty:
        df = proj_df.copy()

    df["co2_avoided_disp"] = from_base_series(df["co2_avoided_t"], em_u)
    df["fossil_avoided_disp"] = from_base_series(df["fossil_avoided_gwh"], e_u)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bars: CO2 avoided each year
    fig.add_trace(
        go.Bar(
            x=df["calendar_year"],
            y=df["co2_avoided_disp"],
            name=f"CO₂ avoided ({EM_WORDS.get(em_u, em_u)} in a year)",
            marker_color="#FF6B6B",
            text=df["co2_avoided_disp"].apply(lambda v: f"{v:,.1f}"),
            textposition="outside",
            textfont=dict(size=9.5, color="#C8CDD6"),
            hovertemplate=f"Year: %{{x}}<br>CO₂ avoided: <b>%{{y:{DFMT}}} {em_u}</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Line: fossil generation avoided each year
    fig.add_trace(
        go.Scatter(
            x=df["calendar_year"],
            y=df["fossil_avoided_disp"],
            name=f"Fossil power replaced ({e_u} in a year)",
            mode="lines+markers",
            line=dict(color="#2ECC71", width=3),
            marker=dict(size=6, color="#2ECC71", symbol="diamond"),
            hovertemplate=f"Year: %{{x}}<br>Fossil power replaced: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
            connectgaps=False,
        ),
        secondary_y=True,
    )

    # One string for the left axis, so the theme and the colour override agree.
    co2_axis = f"CO₂ avoided, {EM_WORDS.get(em_u, em_u)} a year"
    fig = _dark_theme(fig, height=360, y_title=co2_axis, legend_h=True)
    fig.update_yaxes(title_text=co2_axis,
                     title_font=dict(color="#FF6B6B", size=11),
                     tickfont=dict(color="#FF6B6B"),
                     gridcolor="#2A2F3A", secondary_y=False)
    fig.update_yaxes(title_text=f"Fossil power replaced, {e_u} a year",
                     title_font=dict(color="#2ECC71", size=11),
                     tickfont=dict(color="#2ECC71"),
                     gridcolor="rgba(0,0,0,0)", secondary_y=True)
    return fig


# ---------------- Visual 4: Renewable Capacity by Source (Stacked Area) ----------------
def visual4_renewable_capacity_chart(cap_df: pd.DataFrame, year_range: tuple,
                                     units: dict = None):
    """
    Visual 4: Which renewable type is growing fastest.
    installed_capacity_mw by source and year, in the selected power unit.
    """
    u = unit_for(units, "power")
    df = cap_df[(cap_df["calendar_year"] >= year_range[0]) &
                (cap_df["calendar_year"] <= year_range[1])].copy()
    if df.empty:
        df = cap_df.copy()
    df = _conv(df, ["installed_capacity_mw"], u)

    cap_pivot = df.pivot_table(
        index="calendar_year",
        columns="renewable_source",
        values="installed_capacity_mw",
        aggfunc="sum",
        fill_value=np.nan,
    )
    # A stacked area cannot hold a gap, so a year where one source has no
    # reading is left out of the stack entirely rather than drawn as if that
    # source had zero plant installed.
    cap_pivot = cap_pivot.dropna()

    color_map = {
        "Hydel": "#00A6FB",
        "Wind": "#2ECC71",
        "Solar": "#F4A300",
        "Bagasse": "#9B59B6",
    }
    # The database calls hydropower "Hydel"; the legend says the common word.
    name_map = {"Hydel": "Hydropower", "Bagasse": "Bagasse (sugarcane)"}

    fig = go.Figure()
    for col in cap_pivot.columns:
        c = color_map.get(col, "#FFFFFF")
        fig.add_trace(go.Scatter(
            x=cap_pivot.index,
            y=cap_pivot[col],
            name=name_map.get(col, col),
            mode="lines",
            stackgroup="one",
            line=dict(width=1, color=c),
            fillcolor=c,
            hovertemplate=f"{name_map.get(col, col)}: <b>%{{y:{DFMT}}} {u}</b><extra></extra>",
        ))

    return _dark_theme(fig, height=360, y_title=f"Power plants built ({u})", x_title="Year", legend_h=True)
