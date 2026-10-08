import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from config.settings import SCENARIOS
from core.units import from_base_series, unit_for

# Base (storage) unit of each measure family
GEN_COLS = ["solar_gwh", "wind_gwh", "hydro_gwh", "other_gwh",
            "nuclear_gwh", "gas_gwh", "coal_gwh"]
DFMT = ",.2f"          # plotly/d3 number format used in hover + text labels


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

    # 1. Historical Actual Line (1999 - 2024)
    hist_df = filtered_df[filtered_df["data_type"] == "Actual"]
    if not hist_df.empty:
        fig.add_trace(go.Scatter(
            x=hist_df["calendar_year"],
            y=hist_df["re_share_pct"],
            name="Actual (1999–2024)",
            mode="lines+markers",
            line=dict(color="#2ECC71", width=3),
            marker=dict(size=5, color="#2ECC71"),
            hovertemplate="Year: %{x}<br>Actual RE Share: <b>%{y:.1f}%</b><extra></extra>",
        ))

    # 2. Add other scenarios as subtle comparison lines
    for sc_name, sc_df in all_scenarios_data.items():
        if sc_name == selected_scenario:
            continue
        sc_slice = sc_df[(sc_df["calendar_year"] >= max(2024, year_range[0])) & (sc_df["calendar_year"] <= year_range[1])]
        if sc_slice.empty:
            sc_slice = sc_df[sc_df["calendar_year"] >= 2024]
        conf = SCENARIOS.get(sc_name, {})
        fig.add_trace(go.Scatter(
            x=sc_slice["calendar_year"],
            y=sc_slice["re_share_pct"],
            name=f"{sc_name}",
            mode="lines",
            line=dict(color=conf.get("color", "#6C7A89"), width=1.5, dash="dot"),
            opacity=0.6,
            hovertemplate=f"Year: %{{x}}<br>{sc_name}: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    # 3. Selected Scenario Projection (2024 to end)
    proj_conn = filtered_df[filtered_df["calendar_year"] >= 2024]
    sc_conf = SCENARIOS.get(selected_scenario, {})
    sc_color = sc_conf.get("color", "#00A6FB")
    if not proj_conn.empty:
        fig.add_trace(go.Scatter(
            x=proj_conn["calendar_year"],
            y=proj_conn["re_share_pct"],
            name=f"{selected_scenario} (Projected)",
            mode="lines+markers",
            line=dict(color=sc_color, width=3.2, dash="dash"),
            marker=dict(size=6, color=sc_color, symbol="diamond"),
            hovertemplate=f"Year: %{{x}}<br>{selected_scenario} RE: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    # Add vertical indicator at 2024
    if year_range[0] <= 2024 <= year_range[1]:
        fig.add_vline(
            x=2024, line_width=1.5, line_dash="dash", line_color="#E74C3C",
            annotation_text="2024 Base",
            annotation_position="top left",
            annotation_font=dict(size=10, color="#E74C3C"),
        )

    return _dark_theme(fig, height=360, y_title="RE Share (%)", legend_h=True)


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

    if year_range[0] <= 2024 <= year_range[1]:
        fig.add_vline(
            x=2024.5, line_width=1.5, line_dash="dash", line_color="#E74C3C",
        )

    fig.update_layout(barmode="stack")
    return _dark_theme(fig, height=360, y_title=f"Generation ({u})", legend_h=True)


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
        name=f"RE Share % ({target_year})",
        marker_color="#2ECC71",
        text=df["re_share_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="Scenario: %{x}<br>RE Share: <b>%{y:.1f}%</b><extra></extra>",
    ))

    # 2. CO2 Avoided
    fig.add_trace(go.Bar(
        x=df["scenario"],
        y=df["co2_avoided_disp"],
        name=f"CO₂ Avoided ({em_u}/yr)",
        marker_color="#FF6B6B",
        text=df["co2_avoided_disp"].apply(lambda v: f"{v:,.2f} {em_u}"),
        textposition="outside",
        hovertemplate=f"Scenario: %{{x}}<br>CO₂ Avoided: <b>%{{y:{DFMT}}} {em_u}</b><extra></extra>",
    ))

    # 3. Fossil Fuel Avoided
    fig.add_trace(go.Bar(
        x=df["scenario"],
        y=df["fossil_avoided_disp"],
        name=f"Fossil Avoided ({e_u}/yr)",
        marker_color="#F4A300",
        text=df["fossil_avoided_disp"].apply(lambda v: f"{v:,.2f} {e_u}"),
        textposition="outside",
        hovertemplate=f"Scenario: %{{x}}<br>Fossil Displaced: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
    ))

    fig.update_layout(barmode="group", bargap=0.2, bargroupgap=0.1)
    return _dark_theme(fig, height=360, y_title=f"{target_year} Outcomes", x_title="Scenario", legend_h=True)


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
            name=f"CO₂ Avoided ({em_u}/yr)",
            marker_color="#FF6B6B",
            text=df["co2_avoided_disp"].apply(lambda v: f"{v:,.1f}"),
            textposition="outside",
            textfont=dict(size=9.5, color="#C8CDD6"),
            hovertemplate=f"Year: %{{x}}<br>CO₂ Avoided: <b>%{{y:{DFMT}}} {em_u}</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Line: fossil generation avoided each year
    fig.add_trace(
        go.Scatter(
            x=df["calendar_year"],
            y=df["fossil_avoided_disp"],
            name=f"Fossil Avoided ({e_u}/yr)",
            mode="lines+markers",
            line=dict(color="#2ECC71", width=3),
            marker=dict(size=6, color="#2ECC71", symbol="diamond"),
            hovertemplate=f"Year: %{{x}}<br>Fossil Avoided: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
        ),
        secondary_y=True,
    )

    fig = _dark_theme(fig, height=360, y_title=f"CO₂ ({em_u})", legend_h=True)
    fig.update_yaxes(title_text=f"CO₂ ({em_u})",
                     title_font=dict(color="#FF6B6B", size=11),
                     tickfont=dict(color="#FF6B6B"),
                     gridcolor="#2A2F3A", secondary_y=False)
    fig.update_yaxes(title_text=f"Fossil Avoided ({e_u})",
                     title_font=dict(color="#2ECC71", size=11),
                     tickfont=dict(color="#2ECC71"),
                     gridcolor="rgba(0,0,0,0)", secondary_y=True)
    return fig


# ---------------- Visual 4: CO₂ vs RE Share % Dual-Axis Line ----------------
def visual4_co2_vs_re_chart(co2_re_df: pd.DataFrame, year_range: tuple,
                            units: dict = None):
    """
    Visual 4: Links renewable growth to emission reduction.
    Left axis: RE Share %. Right axis: CO2 emissions in the selected unit.
    """
    em_u = unit_for(units, "emission")
    df = co2_re_df.copy()

    if "re_share_pct" not in df.columns or "co2_t" not in df.columns:
        num_cols = ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
                    "gen_other_renewables_gwh", "gen_coal_gwh", "gen_gas_gwh",
                    "gen_nuclear_gwh", "co2_emissions_tonnes"]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        re_t = (df.get("gen_solar_gwh", 0) + df.get("gen_wind_gwh", 0)
                + df.get("gen_hydro_gwh", 0) + df.get("gen_other_renewables_gwh", 0))
        tot = (re_t + df.get("gen_coal_gwh", 0) + df.get("gen_gas_gwh", 0)
               + df.get("gen_nuclear_gwh", 0))
        df["re_share_pct"] = (re_t / tot * 100).fillna(0).round(2)
        df["co2_t"] = df.get("co2_emissions_tonnes", 0)

    df_filtered = df[(df["calendar_year"] >= year_range[0]) &
                     (df["calendar_year"] <= year_range[1])].copy()
    if df_filtered.empty:
        df_filtered = df.copy()
    df = df_filtered
    df["co2_disp"] = from_base_series(df["co2_t"], em_u)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Left axis: RE Share %
    fig.add_trace(
        go.Scatter(
            x=df["calendar_year"],
            y=df["re_share_pct"],
            name="RE Share (%)",
            mode="lines+markers",
            line=dict(color="#2ECC71", width=3),
            marker=dict(size=5, color="#2ECC71"),
            hovertemplate="Year: %{x}<br>RE Share: <b>%{y:.1f}%</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Right axis: CO2 emissions
    fig.add_trace(
        go.Scatter(
            x=df["calendar_year"],
            y=df["co2_disp"],
            name=f"CO₂ Emissions ({em_u})",
            mode="lines+markers",
            line=dict(color="#E74C3C", width=3),
            marker=dict(size=5, color="#E74C3C", symbol="square"),
            hovertemplate=f"Year: %{{x}}<br>CO₂ Emissions: <b>%{{y:{DFMT}}} {em_u}</b><extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=40, r=40, t=25, b=55),
        height=360,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.24, x=0.5, xanchor="center", font=dict(size=10.5, color="#C8CDD6")),
        xaxis=dict(gridcolor="#2A2F3A", tickfont=dict(color="#8B95A7"),
                   title=dict(text="Year", font=dict(size=11, color="#8B95A7"))),
    )
    fig.update_yaxes(
        title_text="RE Share (%)",
        title_font=dict(color="#2ECC71", size=11),
        tickfont=dict(color="#2ECC71"),
        gridcolor="#2A2F3A",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text=f"CO₂ ({em_u})",
        title_font=dict(color="#E74C3C", size=11),
        tickfont=dict(color="#E74C3C"),
        gridcolor="rgba(0,0,0,0)",
        secondary_y=True,
    )
    return fig


# ---------------- Visual 5: Renewable Capacity by Source (Stacked Area) ----------------
def visual5_renewable_capacity_chart(cap_df: pd.DataFrame, year_range: tuple,
                                     units: dict = None):
    """
    Visual 5: Which renewable type is growing fastest.
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
    ).fillna(0)

    color_map = {
        "Hydel": "#00A6FB",
        "Wind": "#2ECC71",
        "Solar": "#F4A300",
        "Bagasse": "#9B59B6",
    }

    fig = go.Figure()
    for col in cap_pivot.columns:
        c = color_map.get(col, "#FFFFFF")
        fig.add_trace(go.Scatter(
            x=cap_pivot.index,
            y=cap_pivot[col],
            name=col,
            mode="lines",
            stackgroup="one",
            line=dict(width=1, color=c),
            fillcolor=c,
            hovertemplate=f"{col}: <b>%{{y:{DFMT}}} {u}</b><extra></extra>",
        ))

    return _dark_theme(fig, height=360, y_title=f"Capacity ({u})", x_title="Year", legend_h=True)


# ---------------- Visual 6: Capacity vs Generation vs T&D Losses (Combo Chart) ----------------
def visual6_capacity_gen_td_combo_chart(combo_df: pd.DataFrame, year_range: tuple,
                                        units: dict = None):
    """
    Visual 6: System efficiency as capacity grows.
    Bars: installed capacity (power unit) + generation (electricity unit);
    Line: T&D losses (electricity unit).
    """
    p_u = unit_for(units, "power")
    e_u = unit_for(units, "electricity")

    df = combo_df[(combo_df["calendar_year"] >= year_range[0]) &
                  (combo_df["calendar_year"] <= year_range[1])].copy()
    if df.empty:
        df = combo_df.copy()
    df = _conv(df, ["installed_capacity_mw"], p_u)
    df = _conv(df, ["generation_gwh", "td_losses_gwh"], e_u)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar 1: Installed Capacity
    fig.add_trace(
        go.Bar(
            x=df["calendar_year"],
            y=df["installed_capacity_mw"],
            name=f"Capacity ({p_u})",
            marker_color="#00A6FB",
            hovertemplate=f"Capacity: <b>%{{y:{DFMT}}} {p_u}</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Bar 2: Generation
    fig.add_trace(
        go.Bar(
            x=df["calendar_year"],
            y=df["generation_gwh"],
            name=f"Generation ({e_u})",
            marker_color="#2ECC71",
            hovertemplate=f"Generation: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # Secondary line: T&D losses
    valid_td = df.dropna(subset=["td_losses_gwh"])
    if not valid_td.empty:
        fig.add_trace(
            go.Scatter(
                x=valid_td["calendar_year"],
                y=valid_td["td_losses_gwh"],
                name=f"T&D Losses ({e_u})",
                mode="lines+markers",
                line=dict(color="#FF6B6B", width=3),
                marker=dict(size=6, color="#FF6B6B", symbol="diamond"),
                hovertemplate=f"T&D Losses: <b>%{{y:{DFMT}}} {e_u}</b><extra></extra>",
            ),
            secondary_y=True,
        )

    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=40, r=40, t=25, b=55),
        height=360,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.24, x=0.5, xanchor="center", font=dict(size=10.5, color="#C8CDD6")),
        xaxis=dict(gridcolor="#2A2F3A", tickfont=dict(color="#8B95A7"),
                   title=dict(text="Year", font=dict(size=11, color="#8B95A7"))),
    )
    fig.update_yaxes(
        title_text=f"Capacity ({p_u}) & Generation ({e_u})",
        title_font=dict(color="#00A6FB", size=11),
        tickfont=dict(color="#00A6FB"),
        gridcolor="#2A2F3A",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text=f"T&D Losses ({e_u})",
        title_font=dict(color="#FF6B6B", size=11),
        tickfont=dict(color="#FF6B6B"),
        gridcolor="rgba(0,0,0,0)",
        secondary_y=True,
    )
    return fig
