"""
Renewable Energy Scenarios dashboard (Question 2).
"""

import streamlit as st
import pandas as pd

from config.database import run_query
from config.settings import SCENARIOS, EMISSION_FACTORS
from core.queries import (
    Q_RENEWABLE_ENERGY,
    Q_ECONOMIC,
    Q_TD_LOSSES,
    Q_LNG,
    Q_RENEWABLE_CAPACITY,
    Q_COMBO_ELEC_TD,
    Q_CO2_VS_RE,
    Q_EMISSION_FACTORS,
)
from core.projections import (
    project_renewable,
    compare_all_scenarios,
    project_renewable_capacity,
    project_system_metrics,
    merge_co2_vs_re,
)
from core.components import kpi_card, section_title, impact_metric
from core.icons import icon
from core.units import DOMAINS, DOMAIN_ORDER, fmt, from_base
from core.unit_slicer import get_units

from .charts import (
    visual1_re_share_chart,
    visual2_generation_mix_chart,
    visual3_scenario_comparison_chart,
    visual3_yearly_outcomes_chart,
    visual4_co2_vs_re_chart,
    visual5_renewable_capacity_chart,
    visual6_capacity_gen_td_combo_chart,
)
from .config import KPI_CONFIG

FILTERS_KEY = "q2_filters"


def _num(value) -> float:
    """None / NaN safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if out != out else out


def _mass(value_t: float, preferred: str = "t") -> tuple:
    """Convert value_t to formatted mass tuple (display_value, unit_label)."""
    v = _num(value_t)
    chain = ["t", "kt", "Mt"]
    unit = preferred if preferred in chain else "t"
    disp = from_base(v, unit)
    if abs(disp) >= 1000 and unit != "Mt":
        unit = chain[chain.index(unit) + 1]
        disp = from_base(v, unit)
    return disp, f"{unit}CO₂"


# --- Sidebar Slicers ---

def _sidebar_filters():
    """A plain animated title, then the three slicers. No surrounding cards."""
    st.sidebar.markdown(
        '<div class="dsh-side-title">Slicers &amp; Parameters</div>',
        unsafe_allow_html=True,
    )

    scenario_keys = list(SCENARIOS.keys())
    selected_scenario = st.sidebar.selectbox(
        "Scenario",
        scenario_keys,
        index=scenario_keys.index("Accelerated") if "Accelerated" in scenario_keys else 0,
    )

    year_range = st.sidebar.slider(
        "Year Range",
        min_value=2000,
        max_value=2035,
        value=(2000, 2035),
        step=1,
        help=("Charts zoom to this window. The KPI cards report the final year "
              "you pick, so narrowing the range moves them."),
    )

    default_growth = float(SCENARIOS[selected_scenario]["solar"])
    with st.sidebar.expander("Custom Growth Parameter", expanded=False):
        custom_growth = st.slider(
            "Growth Rate %",
            min_value=0.0,
            max_value=30.0,
            value=default_growth,
            step=0.5,
            help="Annual solar and wind growth applied to the selected scenario.",
        )

    return {
        "scenario": selected_scenario,
        "growth_rate": custom_growth,
        "year_range": year_range,
    }


def sidebar():
    """
    This dashboard's own sidebar slicers (Scenario / Growth Rate / Year Range).
    Called by app.py BEFORE the global unit slicer so that both stay reachable
    at the top of the sidebar.
    """
    st.session_state[FILTERS_KEY] = _sidebar_filters()
    st.sidebar.divider()


# ================= Compute 5 KPI Values (unit aware) =================
def _compute_kpis(active_proj, cap_ext, econ_df, years, units):
    """
    Scenario outcome KPIs, evaluated at the FINAL year of the selected range.

    Every card reads the SELECTED scenario's projection and the range's last
    year, so changing the sidebar Year Range, Scenario or Growth Rate all move
    the cards.  Values are compared with the last reported year (2024) so the
    direction of travel is visible; when the range ends before that, the card
    reports the scenario's own pre-baseline state instead.

    All maths is done in the database BASE units; each value is converted to the
    user-selected display unit at the end.
    """
    p_u  = units["power"]
    em_u = units["emission"]

    ref_year, target_year = years

    def _row(df, year):
        if df is None or df.empty:
            return None
        r = df[df["calendar_year"] == year]
        return r.iloc[0] if not r.empty else None

    def _pct_delta(now, before):
        if before:
            return (now - before) / before * 100.0
        return 0.0

    # ── horizon row and baseline row of the ACTIVE scenario ──────────────
    r_end = _row(active_proj, target_year)
    r_ref = _row(active_proj, ref_year)

    re_share_end = _num(r_end.get("re_share_pct")) if r_end is not None else 0.0
    re_share_ref = _num(r_ref.get("re_share_pct")) if r_ref is not None else 0.0
    delta_share = re_share_end - re_share_ref

    # ── renewable capacity at the horizon (sum across sources) ───────────
    cap_end = cap_ref = 0.0
    if cap_ext is not None and not cap_ext.empty:
        cap_end_rows = cap_ext[cap_ext["calendar_year"] == target_year]
        cap_ref_rows = cap_ext[cap_ext["calendar_year"] == ref_year]
        cap_end = float(pd.to_numeric(cap_end_rows["installed_capacity_mw"],
                                      errors="coerce").fillna(0).sum())
        cap_ref = float(pd.to_numeric(cap_ref_rows["installed_capacity_mw"],
                                      errors="coerce").fillna(0).sum())
    delta_cap = _pct_delta(cap_end, cap_ref)

    # ── CO2 at the horizon, and how much this scenario avoids ────────────
    co2_end_t = _num(r_end.get("co2_t")) if r_end is not None else 0.0
    co2_avoid_t = _num(r_end.get("co2_avoided_t")) if r_end is not None else 0.0
    co2_ref_t = 0.0
    if econ_df is not None and not econ_df.empty:
        e_ref = _row(econ_df, ref_year)
        if e_ref is not None:
            co2_ref_t = _num(e_ref.get("co2_emissions_tonnes"))
    if not co2_ref_t:
        co2_ref_t = co2_end_t + co2_avoid_t
    delta_co2 = _pct_delta(co2_end_t, co2_ref_t)

    # ── cumulative LNG savings over the projection window ────────────────
    cum_lng = 0.0
    lng_end = 0.0
    if active_proj is not None and not active_proj.empty:
        win = active_proj[(active_proj["calendar_year"] > ref_year) &
                          (active_proj["calendar_year"] <= target_year)]
        cum_lng = _num(win["lng_savings_musd"].sum())
        lng_end = _num(r_end.get("lng_savings_musd")) if r_end is not None else 0.0

    # ── grid carbon intensity = total emissions / total generation ───────
    def _intensity(row):
        if row is None:
            return 0.0
        gen_gwh = _num(row.get("total_gen_gwh"))
        # tCO2 / GWh == kgCO2 / MWh
        return (_num(row.get("co2_t")) / gen_gwh) if gen_gwh else 0.0

    int_end = _intensity(r_end)
    int_ref = _intensity(r_ref)
    delta_int = _pct_delta(int_end, int_ref)

    def _fmt_delta(pct, invert=False):
        """+x% / -x% with green when the movement is an improvement."""
        better = (pct < 0) if not invert else (pct > 0)
        return f"{pct:+.1f}% vs {ref_year}", ("down" if better else "up")

    # When the range ends before the last reported year there is no meaningful
    # "vs 2024" comparison: the card is reporting the scenario's pre-baseline
    # state, so say so instead of labelling a backward delta.
    future_of_ref = target_year >= ref_year

    d_share_txt = (f"{delta_share:+.2f} pp vs {ref_year}" if future_of_ref
                   else f"actual {target_year}")
    if future_of_ref:
        d_cap_txt, t_cap = _fmt_delta(delta_cap, invert=True)
        d_co2_txt, t_co2 = _fmt_delta(delta_co2)
        d_int_txt, t_int = _fmt_delta(delta_int)
    else:
        d_cap_txt, t_cap = f"actual {target_year}", "up"
        d_co2_txt, t_co2 = f"actual {target_year}", "up"
        d_int_txt, t_int = f"actual {target_year}", "up"

    co2_disp, co2_unit = _mass(co2_end_t, em_u)

    return {
        "re_share": {
            "value": f"{re_share_end:.1f}%",
            "unit": "",
            "delta": d_share_txt,
            "delta_type": "up" if delta_share >= 0 else "down",
        },
        "re_capacity": {
            "value": fmt(from_base(cap_end, p_u)),
            "unit": p_u,
            "delta": d_cap_txt,
            "delta_type": t_cap,
        },
        "co2_emissions": {
            "value": fmt(co2_disp),
            "unit": co2_unit,
            "delta": d_co2_txt,
            "delta_type": t_co2,
        },
        "lng_savings": {
            "value": f"${cum_lng:,.0f}",
            "unit": "M USD",
            "delta": f"${lng_end:,.0f}M in {target_year}",
            "delta_type": "down" if lng_end else "up",
        },
        "co2_intensity": {
            "value": f"{int_end:,.0f}",
            "unit": "kgCO₂/MWh",
            "delta": d_int_txt,
            "delta_type": t_int,
        },
    }


# --- Main Dashboard Render ---
def render():
    units = get_units()
    filters = st.session_state.get(FILTERS_KEY) or _sidebar_filters()

    # Load data
    re_df = run_query(Q_RENEWABLE_ENERGY)
    econ_df = run_query(Q_ECONOMIC)
    td_df = run_query(Q_TD_LOSSES)
    lng_df = run_query(Q_LNG)
    cap_df = run_query(Q_RENEWABLE_CAPACITY)
    combo_df = run_query(Q_COMBO_ELEC_TD)
    co2_re_raw = run_query(Q_CO2_VS_RE)
    ef_df = run_query(Q_EMISSION_FACTORS)

    e_u = units["electricity"]
    em_u = units["emission"]

    # Emission factors (tCO2/MWh)
    ef_map = dict(EMISSION_FACTORS)
    if not ef_df.empty:
        for _, row in ef_df.iterrows():
            f_type = str(row.get("fuel_type", "")).strip().lower()
            factor = _num(row.get("emission_factor_tco2_mwh"))
            if f_type in ef_map and factor > 0:
                ef_map[f_type] = factor

    # Process historical data
    co2_re_df = co2_re_raw.copy()
    num_cols = ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
                "gen_other_renewables_gwh", "gen_coal_gwh", "gen_gas_gwh",
                "gen_nuclear_gwh", "co2_emissions_tonnes"]
    for c in num_cols:
        if c in co2_re_df.columns:
            co2_re_df[c] = pd.to_numeric(co2_re_df[c], errors="coerce").fillna(0.0)

    co2_re_df["re_gwh"] = (co2_re_df["gen_solar_gwh"] + co2_re_df["gen_wind_gwh"]
                           + co2_re_df["gen_hydro_gwh"]
                           + co2_re_df["gen_other_renewables_gwh"])
    co2_re_df["total_gen_gwh"] = (co2_re_df["re_gwh"] + co2_re_df["gen_coal_gwh"]
                                  + co2_re_df["gen_gas_gwh"] + co2_re_df["gen_nuclear_gwh"])
    co2_re_df["re_share_pct"] = (co2_re_df["re_gwh"] / co2_re_df["total_gen_gwh"] * 100).round(2)
    co2_re_df["co2_t"] = co2_re_df["co2_emissions_tonnes"]

    horizon_year = 2035
    view_year = int(filters["year_range"][1])
    filters["target_year"] = view_year

    # Projections for scenarios
    all_scenarios_proj = {}
    for sc_name in SCENARIOS.keys():
        g_rate = filters["growth_rate"] if sc_name == filters["scenario"] else None
        all_scenarios_proj[sc_name] = project_renewable(
            re_df,
            scenario=sc_name,
            custom_growth=g_rate,
            end_year=horizon_year,
            emission_factors=ef_map,
        )

    active_proj = all_scenarios_proj[filters["scenario"]]
    comparison_df = compare_all_scenarios(
        re_df,
        target_year=view_year,
        custom_growth_map={filters["scenario"]: filters["growth_rate"]},
        emission_factors=ef_map,
    )

    best_row = comparison_df.sort_values(
        by=["co2_avoided_t", "re_share_pct"], ascending=False).iloc[0]
    active_target_row = active_proj[
        active_proj["calendar_year"] == view_year].iloc[0]

    # Projections for visuals 4, 5, 6
    co2_re_ext = merge_co2_vs_re(co2_re_df, active_proj)
    cap_ext = project_renewable_capacity(
        cap_df,
        scenario=filters["scenario"],
        custom_growth=filters["growth_rate"],
        end_year=filters["target_year"],
    )
    combo_ext = project_system_metrics(
        combo_df, active_proj, end_year=filters["target_year"],
    )

    # Cumulative metrics
    proj_window = active_proj[(active_proj["calendar_year"] >= 2025) &
                              (active_proj["calendar_year"] <= filters["target_year"])]
    cum_fossil_avoided_gwh = proj_window["fossil_avoided_gwh"].sum()
    cum_co2_avoided_t = proj_window["co2_avoided_t"].sum()
    cum_lng_savings = proj_window["lng_savings_musd"].sum()

    # --- Top Row: 5 KPI Cards ---
    actual_years = active_proj[active_proj["data_type"] == "Actual"]["calendar_year"]
    last_actual = int(actual_years.max()) if len(actual_years) else filters["year_range"][0]
    ref_year = int(min(max(last_actual, filters["year_range"][0]),
                       filters["year_range"][1]))
    kpi_cols = st.columns(len(KPI_CONFIG))
    kpi_data = _compute_kpis(
        active_proj, cap_ext, econ_df,
        (ref_year, filters["target_year"]), units,
    )

    for col, cfg in zip(kpi_cols, KPI_CONFIG):
        k_info = kpi_data[cfg["key"]]
        unit_label = cfg["unit"] if not cfg["unit"].startswith("of ") \
            else f"{cfg['unit']} in {filters['target_year']}"
        col.markdown(
            kpi_card(
                title=f"{cfg['title']} ({filters['target_year']})",
                value=k_info["value"],
                unit=unit_label,
                delta=k_info["delta"],
                delta_type=k_info["delta_type"],
                icon_name=cfg["icon"],
                color=cfg["color"],
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- Scenario Impact Summary Row ---
    m1 = impact_metric("re_share", "green", f"{filters['target_year']} RE Share",
                       f"{active_target_row['re_share_pct']:.1f}%",
                       f"{active_target_row['re_share_pct'] - 40.95:+.1f}% vs 2024")
    m2 = impact_metric(
        "impact_gen", "orange", "Fossil Gen Avoided",
        f"{fmt(from_base(cum_fossil_avoided_gwh, e_u))} {e_u}",
        f"{fmt(from_base(active_target_row['fossil_avoided_gwh'], e_u))} {e_u}/yr in {filters['target_year']}")
    m3 = impact_metric(
        "impact_co2", "red", "CO₂ Emissions Avoided",
        f"{fmt(from_base(cum_co2_avoided_t, em_u))} {em_u}",
        f"{fmt(from_base(active_target_row['co2_avoided_t'], em_u))} {em_u}/yr in {filters['target_year']}")
    m4 = impact_metric("impact_bill", "blue", "Cumulative LNG Savings",
                       f"${cum_lng_savings:,.0f} M", "From reduced gas fuel")

    sim_card_html = (
        f'<div class="section-card" style="margin-bottom:14px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="color:#FFFFFF;font-size:13px;font-weight:600;">{icon("scenario")} Scenario: <strong>{filters["scenario"]}</strong> ({filters["growth_rate"]:.1f}% p.a. ➔ {filters["target_year"]})</div>'
        f'<span class="section-badge" style="background:rgba(0,166,251,0.18);border-color:#00A6FB;color:#00A6FB;">Best 2035 Strategy: {best_row["scenario"]}</span>'
        f'</div>'
        f'<div class="impact-summary-container">{m1}{m2}{m3}{m4}</div>'
        f'</div>'
    )
    st.markdown(sim_card_html, unsafe_allow_html=True)

    # --- Row 1: Visual 1 & Visual 2 ---
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown(section_title("Visual 1 – RE Share % Line Chart", "scenario", badge="Actual + Projected"), unsafe_allow_html=True)
        st.caption("Historical and projected renewable generation share (%) across all 5 policy scenarios compared against the 2030 (30%) and 2035 targets.")
        fig1 = visual1_re_share_chart(all_scenarios_proj, filters["scenario"], filters["year_range"], units)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown(section_title("Visual 2 – Generation Mix Stacked Column", "generation", badge=f"{filters['scenario']} · {e_u}"), unsafe_allow_html=True)
        st.caption(f"Annual power generation mix ({e_u}) breakdown by technology (Hydro, Solar, Wind, Nuclear, Thermal) under the active scenario.")
        fig2 = visual2_generation_mix_chart(active_proj, filters["year_range"], units)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --- Row 2: Visual 3 & Visual 4 ---
    view_col, _spacer = st.columns([1.05, 1])
    with view_col:
        view = st.radio(
            "Visual 3 – outcome view",
            ["Year by year", "Scenario comparison (2035)"],
            horizontal=True,
            key="outcome_view",
        )

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        if view == "Year by year":
            v3_title = "Visual 3 – Annual Outcomes (year by year)"
            v3_badge = f"{filters['scenario']} · to {filters['target_year']} · {em_u} / {e_u}"
            v3_caption = f"Year-by-year trajectory of avoided fossil generation ({e_u}), avoided CO₂ emissions ({em_u}), and annual LNG import bill savings."
            fig3 = visual3_yearly_outcomes_chart(active_proj, filters["year_range"], units)
        else:
            v3_title = "Visual 3 – Scenario Comparison Clustered Bar"
            v3_badge = f"Target {filters['target_year']} · {em_u} / {e_u}"
            v3_caption = f"Multi-scenario benchmark of renewable share, avoided fossil generation, cumulative CO₂ reduction, and economic savings by {filters['target_year']}."
            fig3 = visual3_scenario_comparison_chart(
                comparison_df, target_year=filters["target_year"], units=units)

        st.markdown(section_title(v3_title, "chart", badge=v3_badge), unsafe_allow_html=True)
        st.caption(v3_caption)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown(section_title("Visual 4 – CO₂ vs RE Share % Dual-Axis Line", "co2", badge=f"Correlation · {em_u} · to {filters['target_year']}"), unsafe_allow_html=True)
        st.caption(f"Historical and projected inverse correlation between rising renewable share (%) and total power sector CO₂ emissions ({em_u}).")
        fig4 = visual4_co2_vs_re_chart(co2_re_ext, filters["year_range"], units)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --- Row 3: Visual 5 & Visual 6 ---
    r3c1, r3c2 = st.columns(2)

    with r3c1:
        st.markdown(section_title("Visual 5 – Renewable Capacity by Source (Stacked Area)", "renewables", badge=f"Hydel, Wind, Solar, Bagasse · {units['power']} · to {filters['target_year']}"), unsafe_allow_html=True)
        st.caption(f"Cumulative installed renewable generation capacity ({units['power']}) expansion trajectory by source (Hydel, Solar, Wind, Bagasse).")
        fig5 = visual5_renewable_capacity_chart(cap_ext, filters["year_range"], units)
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    with r3c2:
        st.markdown(section_title("Visual 6 – Capacity vs Generation vs T&D Losses (Combo Chart)", "primary_energy", badge=f"{units['power']} / {e_u} · to {filters['target_year']}"), unsafe_allow_html=True)
        st.caption(f"System tri-metric view comparing total installed capacity ({units['power']}), total generation ({e_u}), and transmission & distribution losses (%).")
        fig6 = visual6_capacity_gen_td_combo_chart(combo_ext, filters["year_range"], units)
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

    # --- Footer ---
    # Everything below is read from the live projection, so it tracks the
    # Scenario / Growth Rate / Year Range slicers.
    end_share = _num(active_target_row["re_share_pct"])
    end_co2 = _num(active_target_row["co2_t"])
    end_gen = _num(active_target_row["total_gen_gwh"])
    end_intensity = (end_co2 / end_gen) if end_gen else 0.0

    best_name = best_row["scenario"]
    best_share = _num(best_row["re_share_pct"])
    lead = (f"{filters['scenario']} reaches {end_share:.1f}% renewable share by "
            f"{view_year} at {end_intensity:,.0f} kgCO₂/MWh"
            + (f"; {best_name} leads on avoided CO₂."
               if best_name != filters["scenario"] else ", the strongest scenario here."))
