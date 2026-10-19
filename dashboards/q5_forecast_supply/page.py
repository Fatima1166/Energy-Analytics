"""
Forecasted Energy Supply dashboard (Question 5).
"""

from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
from core.icons import icon
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
)
from core.supply_forecast import (
    CLEAN_POLICY_TARGET_DEFAULT,
    DEFAULT_BASE_GDP_GROWTH,
    DEFAULT_CALIB_START,
    DEFAULT_SCENARIO_SPREAD,
    HISTORY_END,
    HORIZON,
    SCENARIO_ORDER,
    build_supply_dashboard_data,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_history_trajectory,
    visual2_scenario_fans,
    visual3_technology_mix,
    visual4_capacity_expansion,
    visual5_supply_adequacy,
    visual5_supply_vs_demand,
    visual5_reserve_margin,
    visual6_indigenous_vs_imports,
    visual7_reliability_backtest,
)

FILTERS_KEY = "q5_filters"
_CHART_CONFIG = {"displayModeBar": False}


# --- Sidebar controls ---

def _data_default_gdp_growth() -> float:
    """Median real GDP growth of the last ten reported years, as a % default."""
    try:
        frame = run_query(Q_ECONOMIC)
        series = pd.to_numeric(frame["gdp_growth_pct"], errors="coerce").dropna().tail(10)
        if not series.empty:
            value = float(series.median())
            if math.isfinite(value):
                return float(min(max(round(value, 1), 1.0), 8.0))
    except Exception:
        pass
    return DEFAULT_BASE_GDP_GROWTH


def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Supply Forecast Setup</div>',
                        unsafe_allow_html=True)

    scenarios = st.sidebar.multiselect(
        "Scenarios", SCENARIO_ORDER, default=SCENARIO_ORDER, key="q5_scenarios",
        help="Which Low / Base / High paths to draw and evaluate.",
    )
    if not scenarios:
        scenarios = ["Base"]

    horizon = st.sidebar.slider(
        "Forecast horizon", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q5_horizon",
        help="Target horizon year for the supply outlook.",
    )

    with st.sidebar.expander("Advanced Model Settings", expanded=False):
        model_choice = st.radio(
            "Forecast basis", ["Driver", "Trend"], index=0, key="q5_model",
            help=("Driver: supply responds to GDP and industrial activity through fitted "
                  "elasticities. Trend: log-linear historical expansion path."),
        )

        calib_start = st.slider(
            "Calibration start", min_value=2002, max_value=2020,
            value=DEFAULT_CALIB_START, step=1, key="q5_calib",
            help="Elasticities and trends are fitted from this year to 2024.",
        )

        base_gdp = st.slider(
            "Base GDP growth %", min_value=1.0, max_value=8.0,
            value=_data_default_gdp_growth(), step=0.1, key="q5_gdp",
            help="Real GDP growth assumed for the Base scenario.",
        )

        spread = st.slider(
            "Scenario spread ±pp", min_value=0.0, max_value=3.0,
            value=DEFAULT_SCENARIO_SPREAD, step=0.25, key="q5_spread",
            help="Low = Base − spread, High = Base + spread, in percentage points of GDP growth.",
        )

    st.session_state[FILTERS_KEY] = {
        "scenarios": list(scenarios),
        "model_choice": model_choice,
        "calib_start": int(calib_start),
        "horizon": int(horizon),
        "base_gdp_growth": float(base_gdp),
        "spread": float(spread),
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#00A6FB", icon_name: str = "supply",
              badge: str = "", badge_colour: str = "#00A6FB") -> str:
    """Compact dark glassmorphism KPI card."""
    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:9px;color:#94A3B8;padding:1px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (f'<span style="background:{badge_colour}22;color:{badge_colour};'
                  f'font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;'
                  f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
                  if badge else "")
    return f"""
<div class="kpi-balance" style="border: 1px solid {accent}44;">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:30px;height:30px;background:{accent}22;border:1px solid {accent}44;
                  border-radius:8px;display:flex;align-items:center;justify-content:center;
                  color:{accent};font-size:12px;">{icon(icon_name)}</div>
      <div style="color:#94A3B8;font-size:9.5px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.7px;">{code}</div>
    </div>
    {badge_html}
  </div>
  <div style="color:#E2E8F0;font-size:11px;font-weight:600;line-height:1.3;
              margin-bottom:6px;min-height:28px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:8px;">
    <span style="color:{accent};font-size:23px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details" style="margin-top:auto;">{detail}</div>
</div>
"""


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Forecasted Energy Supply dashboard."""
    flt = st.session_state.get(FILTERS_KEY, {})
    scenarios = flt.get("scenarios", list(SCENARIO_ORDER))
    model_choice = flt.get("model_choice", "Driver")
    calib_start = flt.get("calib_start", DEFAULT_CALIB_START)
    horizon = flt.get("horizon", HORIZON)
    base_gdp_growth = flt.get("base_gdp_growth", DEFAULT_BASE_GDP_GROWTH)
    spread = flt.get("spread", DEFAULT_SCENARIO_SPREAD)
    clean_target_pct = CLEAN_POLICY_TARGET_DEFAULT
    active_sc = "Base" if "Base" in scenarios else (scenarios[0] if scenarios else "Base")

    # Fetch data
    p_df = run_query(Q_PRIMARY_SUPPLY)
    re_df = run_query(Q_RENEWABLE_ENERGY)
    ec_df = run_query(Q_ECONOMIC)
    gen_df = run_query(Q_ELEC_GEN)

    # Compute model data
    data = build_supply_dashboard_data(
        primary_df=p_df,
        re_df=re_df,
        econ_df=ec_df,
        gen_df=gen_df,
        scenarios=scenarios,
        calib_start=calib_start,
        horizon=horizon,
        base_gdp_growth=base_gdp_growth,
        spread=spread,
        clean_target_pct=clean_target_pct,
        model_choice=model_choice,
    )

    # Unit conversions
    units = get_units()
    unit_energy = units.get("energy", "TOE")
    factor_energy = display_factor("energy", unit_energy)

    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)

    unit_power = units.get("power", "MW")
    factor_power = display_factor("power", unit_power)

    # Extract horizon numbers for KPI strip
    hist = data["history"]
    h2024 = hist[hist["calendar_year"] == HISTORY_END].iloc[0] if (hist["calendar_year"] == HISTORY_END).any() else hist.iloc[-1]

    # Primary supply values
    tpes_2024 = float(h2024.get("tpes_toe", 75727780.0))
    fc_tpes = data["forecast"][(data["forecast"]["series"] == "tpes_toe") &
                               (data["forecast"]["scenario"] == active_sc) &
                               (data["forecast"]["calendar_year"] == horizon)]
    tpes_horizon = float(fc_tpes.iloc[0]["value"]) if not fc_tpes.empty else tpes_2024 * 1.2
    tpes_cagr = ((tpes_horizon / tpes_2024) ** (1.0 / (horizon - HISTORY_END)) - 1.0) * 100.0

    # Electricity generation values
    gen_2024 = float(h2024.get("gen_total_gwh", 154480.0))
    fc_gen = data["forecast"][(data["forecast"]["series"] == "gen_total_gwh") &
                              (data["forecast"]["scenario"] == active_sc) &
                              (data["forecast"]["calendar_year"] == horizon)]
    gen_horizon = float(fc_gen.iloc[0]["value"]) if not fc_gen.empty else gen_2024 * 1.5
    gen_cagr = ((gen_horizon / gen_2024) ** (1.0 / (horizon - HISTORY_END)) - 1.0) * 100.0

    # Clean share values
    clean_2024 = float(h2024.get("clean_share_pct", 55.7))
    mix_horizon = data["tech_mix"][(data["tech_mix"]["scenario"] == active_sc) &
                                   (data["tech_mix"]["calendar_year"] == horizon)]
    clean_horizon = float(mix_horizon.iloc[0]["clean_share_pct"]) if not mix_horizon.empty else 60.0
    var_re_horizon = float(mix_horizon.iloc[0]["variable_re_share_pct"]) if not mix_horizon.empty else 20.0

    # Capacity values
    cap_sub = data["capacity"][(data["capacity"]["scenario"] == active_sc) &
                               (data["capacity"]["calendar_year"] == horizon)]
    cap_horizon = float(cap_sub.iloc[0]["total_capacity_mw"]) if not cap_sub.empty else 65000.0
    cap_2024 = float(h2024.get("grid_capacity_mw", 45000.0))
    if cap_2024 <= 0 or math.isnan(cap_2024):
        cap_2024 = 43775.0

    # Adequacy reserve margin
    adeq_sub = data["adequacy"][(data["adequacy"]["scenario"] == active_sc) &
                                (data["adequacy"]["calendar_year"] == horizon)]
    margin_horizon = float(adeq_sub.iloc[0]["reserve_margin_pct"]) if not adeq_sub.empty else 18.0
    adeq_status = str(adeq_sub.iloc[0]["adequacy_status"]) if not adeq_sub.empty else "Optimal Reserve"
    adeq_color = str(adeq_sub.iloc[0]["status_color"]) if not adeq_sub.empty else "#10B981"

    # KPI Strip
    kpi_cols = st.columns(5)

    with kpi_cols[0]:
        val_disp = fmt(tpes_horizon * factor_energy, decimals=1 if unit_energy == "MTOE" else 0)
        st.markdown(
            _kpi_card(
                code="K1",
                title=f"Total Primary Supply ({horizon})",
                value=val_disp,
                unit=unit_energy,
                rows=[
                    ("Reported 2024", f"{fmt(tpes_2024 * factor_energy, 1)} {unit_energy}", "#CBD5E1"),
                    ("Implied CAGR", f"+{tpes_cagr:.2f}%/yr", "#00A6FB"),
                    ("Scenario", f"{active_sc} ({model_choice})", "#94A3B8"),
                ],
                accent="#00A6FB",
                icon_name="primary_energy",
                badge=f"{tpes_cagr:+.1f}% p.a.",
                badge_colour="#00A6FB",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        gen_disp = fmt(gen_horizon * factor_elec, decimals=1 if unit_elec == "TWh" else 0)
        st.markdown(
            _kpi_card(
                code="K2",
                title=f"Power Generation Supply ({horizon})",
                value=gen_disp,
                unit=unit_elec,
                rows=[
                    ("Reported 2024", f"{fmt(gen_2024 * factor_elec, 1)} {unit_elec}", "#CBD5E1"),
                    ("Implied CAGR", f"+{gen_cagr:.2f}%/yr", "#10B981"),
                    ("Horizon Delta", f"+{fmt((gen_horizon - gen_2024) * factor_elec, 1)} {unit_elec}", "#10B981"),
                ],
                accent="#10B981",
                icon_name="supply",
                badge=f"+{gen_cagr:.1f}% p.a.",
                badge_colour="#10B981",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[2]:
        clean_delta = clean_horizon - clean_2024
        st.markdown(
            _kpi_card(
                code="K3",
                title=f"Clean Generation Share ({horizon})",
                value=f"{clean_horizon:.1f}%",
                unit="of Total Generation",
                rows=[
                    ("Reported 2024", f"{clean_2024:.1f}%", "#CBD5E1"),
                    ("ARE Solar+Wind", f"{var_re_horizon:.1f}% (target 30%)", "#F59E0B"),
                    ("Clean Policy Target", f"{clean_target_pct:.0f}%", "#22D3EE"),
                ],
                accent="#22D3EE",
                icon_name="re_share",
                badge=f"{clean_delta:+.1f} pp",
                badge_colour="#22D3EE",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[3]:
        cap_disp = fmt(cap_horizon * factor_power, decimals=1 if unit_power == "GW" else 0)
        cap_delta = (cap_horizon - cap_2024) * factor_power
        st.markdown(
            _kpi_card(
                code="K4",
                title=f"Installed Capacity ({horizon})",
                value=cap_disp,
                unit=unit_power,
                rows=[
                    ("Reported 2024", f"{fmt(cap_2024 * factor_power, 1)} {unit_power}", "#CBD5E1"),
                    ("Capex Additions", f"+{fmt(cap_delta, 1)} {unit_power}", "#A78BFA"),
                    ("Dispatch Factor", "Capacity Expansion CF", "#94A3B8"),
                ],
                accent="#A78BFA",
                icon_name="generation",
                badge=f"+{fmt(cap_delta, 0)} {unit_power}",
                badge_colour="#A78BFA",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[4]:
        st.markdown(
            _kpi_card(
                code="K5",
                title=f"Reserve Margin Adequacy ({horizon})",
                value=f"{margin_horizon:+.1f}%",
                unit="Supply over Demand",
                rows=[
                    ("Adequacy Status", adeq_status, adeq_color),
                    ("Safe Corridor", "15.0% – 25.0%", "#10B981"),
                    ("Scenario Demand", f"{fmt(adeq_sub.iloc[0]['demand_gwh'] * factor_elec, 0)} {unit_elec}", "#94A3B8"),
                ],
                accent=adeq_color,
                icon_name="intensity",
                badge=adeq_status,
                badge_colour=adeq_color,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Visual 1: Historical Supply Trajectory
    st.markdown(section_title("Historical Energy Supply Trajectory (1999–2024)", "overview", "Objective 1"),
                unsafe_allow_html=True)
    st.caption("Primary energy supply evolution (TOE) across fuel sources and grid power generation supply (GWh) by technology over the recorded era.")
    fig1 = visual1_history_trajectory(
        hist=hist,
        unit_energy=unit_energy, factor_energy=factor_energy,
        unit_elec=unit_elec, factor_elec=factor_elec,
    )
    st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    # Visual 2: Scenario Fans
    st.markdown(section_title(f"Supply Scenario Projections (2025–{horizon})", "scenario", "Objective 2"),
                unsafe_allow_html=True)
    st.caption(f"Low, Base, and High scenario fan envelopes for Total Primary Supply ({unit_energy}) and Power Generation ({unit_elec}) calibrated from {calib_start} to 2024.")
    fig2 = visual2_scenario_fans(
        hist=hist, forecast=data["forecast"], scenarios=scenarios,
        unit_energy=unit_energy, factor_energy=factor_energy,
        unit_elec=unit_elec, factor_elec=factor_elec,
    )
    st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    # Visual 3 (Tech Mix) & Visual 4 (Capacity Expansion)
    row2_c1, row2_c2 = st.columns(2)

    with row2_c1:
        st.markdown(section_title(f"Technology Supply Mix ({active_sc})", "renewables", "Objective 3"),
                    unsafe_allow_html=True)
        st.caption(f"Generation dispatch by technology ({unit_elec}) and clean energy share trajectory against the {clean_target_pct:.0f}% policy benchmark and 30% ARE target.")
        fig3 = visual3_technology_mix(
            tech_mix=data["tech_mix"],
            active_scenario=active_sc,
            clean_target=clean_target_pct,
            unit_elec=unit_elec,
            factor_elec=factor_elec,
        )
        st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    with row2_c2:
        st.markdown(section_title(f"Installed Generation Capacity ({active_sc})", "generation", "Objective 4"),
                    unsafe_allow_html=True)
        st.caption(f"Required installed capacity additions ({unit_power}) across Hydro, Solar, Wind, Nuclear and Thermal assets to reliably support generation.")
        fig4 = visual4_capacity_expansion(
            capacity_df=data["capacity"],
            active_scenario=active_sc,
            unit_power=unit_power,
            factor_power=factor_power,
        )
        st.plotly_chart(fig4, use_container_width=True, config=_CHART_CONFIG)

    # Visual 5: Supply Adequacy & Reserve Margin
    st.markdown(section_title(f"Supply Adequacy & Reserve Margin ({active_sc})", "intensity", "Objective 5"),
                unsafe_allow_html=True)
    st.caption("Left: Generation supply vs forecasted demand. Right: System reserve margin % evaluated against the safe 15%–25% planning corridor.")
    adeq_c1, adeq_c2 = st.columns(2)

    with adeq_c1:
        fig5_supply = visual5_supply_vs_demand(
            adequacy_df=data["adequacy"],
            active_scenario=active_sc,
            unit_elec=unit_elec,
            factor_elec=factor_elec,
        )
        st.plotly_chart(fig5_supply, use_container_width=True, config=_CHART_CONFIG)

    with adeq_c2:
        fig5_margin = visual5_reserve_margin(
            adequacy_df=data["adequacy"],
            active_scenario=active_sc,
        )
        st.plotly_chart(fig5_margin, use_container_width=True, config=_CHART_CONFIG)

    # Visuals 6 & 7: side by side in one row, backtest table below
    row4_c1, row4_c2 = st.columns(2)

    with row4_c1:
        st.markdown(section_title(f"Energy Security & Import Vulnerability ({active_sc})", "imports", "Objective 5"),
                    unsafe_allow_html=True)
        st.caption(f"Indigenous domestic production vs imported fuel exposure ({unit_energy}) and import share % trajectory under the transition.")
        fig6 = visual6_indigenous_vs_imports(
            security_df=data["security"],
            active_scenario=active_sc,
            unit_energy=unit_energy,
            factor_energy=factor_energy,
        )
        st.plotly_chart(fig6, use_container_width=True, config=_CHART_CONFIG)

    with row4_c2:
        st.markdown(section_title("Supply Forecast Reliability & Model Backtesting", "insights", "Objective 6"),
                    unsafe_allow_html=True)
        st.caption("Hold-out validation (calibrated on data ≤ 2020, tested on 2021–2024 reported data) comparing the Macro-Driver model against the Trend model.")
        fig7 = visual7_reliability_backtest(
            backtest=data["backtest"],
            unit_elec=unit_elec,
            factor_elec=factor_elec,
        )
        st.plotly_chart(fig7, use_container_width=True, config=_CHART_CONFIG)

    # Model performance table: full width, below the two charts
    st.markdown("<div style='font-size:12px;font-weight:700;color:#CBD5E1;margin:8px 0 8px;'>Model Performance Comparison (2021–2024 Hold-Out)</div>", unsafe_allow_html=True)
    bt_table = data["backtest"]["table"].copy()
    if not bt_table.empty:
        bt_table["Hold-out MAPE %"] = bt_table["mape_pct"].map(lambda x: f"{x:.2f}%")
        bt_table["Bias %"] = bt_table["bias_pct"].map(lambda x: f"{x:+.1f}%")
        bt_table["In-sample R²"] = bt_table["calib_r2"].map(lambda x: f"{x:.3f}")
        bt_table["Winner"] = bt_table["is_winner"].map(lambda x: "◀ Lower Error" if x else "")

        disp_df = bt_table[["series_name", "model", "Hold-out MAPE %", "Bias %", "In-sample R²", "Winner"]]
        disp_df.columns = ["Series", "Model", "MAPE %", "Bias %", "R²", "Result"]
        st.dataframe(disp_df, use_container_width=True, hide_index=True)
    else:
        st.info("Insufficient data for hold-out comparison.")
