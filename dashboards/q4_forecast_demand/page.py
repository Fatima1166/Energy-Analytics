"""
Forecasted Energy Demand dashboard (Question 4).
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import dashboard_footer, section_title
from core.demand_forecast import (
    DEFAULT_BASE_GDP_GROWTH,
    DEFAULT_CALIB_START,
    DEFAULT_SCENARIO_SPREAD,
    HISTORY_END,
    HORIZON,
    SCENARIO_COLORS,
    SCENARIO_ORDER,
    build_dashboard_data,
    series_spec,
)
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_ELEC_PROVINCE_CONSUMPTION,
    Q_ELEC_SECTOR_CONSUMPTION,
    Q_FINAL_ENERGY_BY_SOURCE,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt, normalise

from .charts import (
    visual1_history_trends,
    visual2_scenario_fans,
    visual3_drivers,
    visual4_decomposition,
    visual5_province_mix,
    visual5_sector_mix,
    visual6_gap,
    visual6_imports,
    visual7_backtest_mape,
    visual7_backtest_path,
)

VIEW_START = 2000
HISTORY_SERIES_FOR_CHARTS = ["total_final", "electricity_final", "gas_final"]
FILTERS_KEY = "q4_filters"

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
    st.sidebar.markdown('<div class="dsh-side-title">Forecast Setup</div>',
                        unsafe_allow_html=True)

    scenarios = st.sidebar.multiselect(
        "Scenarios", SCENARIO_ORDER, default=SCENARIO_ORDER, key="q4_scenarios",
        help="Which Low / Base / High paths to draw and to price the KPI cards with.",
    )
    if not scenarios:
        scenarios = ["Base"]

    model_choice = st.sidebar.radio(
        "Forecast basis", ["Driver", "Trend"], index=0, key="q4_model",
        help=("Driver: demand responds to GDP and population through the fitted "
              "elasticities. Trend: the fitted log-linear growth, shifted by half "
              "the GDP surprise."),
    )

    calib_start = st.sidebar.slider(
        "Calibration start", min_value=2005, max_value=2020,
        value=DEFAULT_CALIB_START, step=1, key="q4_calib",
        help="Elasticities and trends are fitted from this year to 2024.",
    )

    horizon = st.sidebar.slider(
        "Forecast horizon", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q4_horizon",
        help="Last modelled year. The residual drift fades to zero by this year.",
    )

    base_gdp = st.sidebar.slider(
        "Base GDP growth %", min_value=1.0, max_value=8.0,
        value=_data_default_gdp_growth(), step=0.1, key="q4_gdp",
        help="Real GDP growth assumed for the Base scenario.",
    )

    spread = st.sidebar.slider(
        "Scenario spread ±pp", min_value=0.0, max_value=3.0,
        value=DEFAULT_SCENARIO_SPREAD, step=0.25, key="q4_spread",
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


# ═══════════════════════════════ UI helpers ═════════════════════════════════

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#00A6FB", icon_name: str = "demand",
              badge: str = "", badge_colour: str = "#00A6FB") -> str:
    """Compact KPI card: one big number, a unit, and up to three detail rows."""
    from core.icons import icon

    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:10.5px;color:#94A3B8;padding:2px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (f'<span style="background:{badge_colour}22;color:{badge_colour};'
                  f'font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;'
                  f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
                  if badge else "")
    return f"""
<div style="
    background: linear-gradient(135deg, rgba(22,27,38,0.95) 0%, rgba(14,18,26,0.98) 100%);
    border: 1px solid {accent}44; border-radius: 14px; padding: 14px 15px 12px;
    position: relative; overflow: hidden; height: 100%;">
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
    <span style="color:#64748B;font-size:10px;font-weight:600;">{unit}</span>
  </div>
  <div style="border-top:1px solid rgba(255,255,255,0.06);padding-top:5px;">{detail}</div>
</div>
"""


def _num(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _pct_change(first: float, last: float) -> float:
    if not math.isfinite(first) or not math.isfinite(last) or first == 0:
        return float("nan")
    return (last / first - 1.0) * 100.0


# --- Main Dashboard Render ---

def render() -> None:
    units = get_units()
    filters = st.session_state.get(FILTERS_KEY) or {}
    scenarios = filters.get("scenarios") or ["Base"]
    model_choice = filters.get("model_choice", "Driver")
    calib_start = int(filters.get("calib_start", DEFAULT_CALIB_START))
    horizon = int(filters.get("horizon", HORIZON))
    base_gdp = float(filters.get("base_gdp_growth", DEFAULT_BASE_GDP_GROWTH))
    spread = float(filters.get("spread", DEFAULT_SCENARIO_SPREAD))
    base_scenario = "Base" if "Base" in scenarios else scenarios[0]

    energy_unit = normalise(units.get("energy", "TOE"))
    elec_unit = normalise(units.get("electricity", "GWh"))
    e_factor = display_factor("energy", energy_unit)
    g_factor = display_factor("electricity", elec_unit)

    # Fetch data
    try:
        data = build_dashboard_data(
            fuel_df=run_query(Q_FINAL_ENERGY_BY_SOURCE),
            re_df=run_query(Q_RENEWABLE_ENERGY),
            econ_df=run_query(Q_ECONOMIC),
            primary_df=run_query(Q_PRIMARY_SUPPLY),
            gen_df=run_query(Q_ELEC_GEN),
            gas_df=run_query(Q_NATURAL_GAS),
            sector_df=run_query(Q_ELEC_SECTOR_CONSUMPTION),
            province_df=run_query(Q_ELEC_PROVINCE_CONSUMPTION),
            scenarios=scenarios,
            calib_start=calib_start,
            horizon=horizon,
            base_gdp_growth=base_gdp,
            spread=spread,
            model_choice=model_choice,
        )
    except Exception as exc:
        st.error(f"Could not load demand data: {exc}")
        st.stop()

    hist = data["history"]
    models = data["models"]
    kpis = data["kpis"]
    breaks = data.get("breaks", {})
    total_break = breaks.get("total_final")

    # KPI Strip
    total = kpis.get("total_final", {})
    grid = kpis.get("elec_grid", {})
    elasticity = kpis.get("elasticity", {})
    gap = kpis.get("supply_gap", {})
    cagr = kpis.get("demand_cagr", {})
    imports = kpis.get("imports", {})

    total_now = _num(total.get("value")) * e_factor
    total_horizon = _num(total.get("horizon_value")) * e_factor
    total_change = _pct_change(total_now, total_horizon)
    grid_now = _num(grid.get("value")) * g_factor
    grid_horizon = _num(grid.get("horizon_value")) * g_factor
    grid_change = _pct_change(grid_now, grid_horizon)

    cards = [
        _kpi_card(
            "K1", f"Total final energy demand, {total.get('year', HISTORY_END)}",
            fmt(total_now), energy_unit,
            [("Scenario", base_scenario, SCENARIO_COLORS.get(base_scenario, "#00A6FB")),
             (f"{horizon}", fmt(total_horizon), "#E2E8F0"),
             ("Change", f"{total_change:+.1f}%", "#10B981" if total_change >= 0 else "#EF4444")],
            accent="#00A6FB", icon_name="primary_energy",
            badge=f"{horizon} {base_scenario}", badge_colour="#00A6FB",
        ),
        _kpi_card(
            "K2", f"Grid electricity demand, {grid.get('year', HISTORY_END)}",
            fmt(grid_now), elec_unit,
            [("Scenario", base_scenario, SCENARIO_COLORS.get(base_scenario, "#00A6FB")),
             (f"{horizon}", fmt(grid_horizon), "#E2E8F0"),
             ("Change", f"{grid_change:+.1f}%", "#10B981" if grid_change >= 0 else "#EF4444")],
            accent="#10B981", icon_name="generation",
            badge=f"{_num(grid.get('growth_pct')):+.1f}%/yr", badge_colour="#10B981",
        ),
        _kpi_card(
            "K3", "Demand growth: reported vs forecast",
            f"{_num(cagr.get('forecast_cagr_pct')):+.2f}", "% per year",
            [("Reported CAGR", f"{_num(cagr.get('observed_cagr_pct')):+.2f}%/yr", "#94A3B8"),
             ("Window", f"{int(_num(cagr.get('calib_start')))}–{int(_num(cagr.get('calib_end')))}", "#94A3B8"),
             ("Basis", str(model_choice), "#A78BFA")],
            accent="#A78BFA", icon_name="scenario",
            badge=f"{_num(cagr.get('forecast_years')):.0f} yrs", badge_colour="#A78BFA",
        ),
        _kpi_card(
            "K4", "Income elasticity of demand",
            f"{_num(elasticity.get('elasticity_income')):.2f}", "ε (per-capita)",
            [("ε vs total GDP", f"{_num(elasticity.get('elasticity_gdp')):.2f}", "#E2E8F0"),
             ("Fit R²", f"{_num(elasticity.get('r2_per_capita')):.3f}", "#E2E8F0"),
             ("Drivers", "GDP + population", "#94A3B8")],
            accent="#F472B6", icon_name="insights",
            badge="objective 3", badge_colour="#F472B6",
        ),
        _kpi_card(
            "K5", f"Supply–demand gap, {horizon}",
            f"{_num(gap.get('gap_pct')):+.1f}", "% of primary supply",
            [("Gap", f"{fmt(_num(gap.get('gap')) * e_factor)} {energy_unit}", "#EF4444"),
             ("Supply CAGR", f"{_num(gap.get('supply_cagr_pct')):+.2f}%/yr", "#94A3B8"),
             ("Needed", f"{_num(gap.get('required_supply_cagr_pct')):+.2f}%/yr", "#F59E0B")],
            accent="#F59E0B", icon_name="warning",
            badge=f"gas imports {_num(imports.get('gas_import_dep_pct')):.0f}%",
            badge_colour="#F59E0B",
        ),
    ]

    for column, card in zip(st.columns(len(cards)), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # Visual 1: Reported Demand
    st.markdown(
        section_title("V1 — Reported demand, 1999–2024", "chart",
                      badge=f"{energy_unit} · objective 1"),
        unsafe_allow_html=True)
    st.caption(f"Historical trajectory and indexed growth of total final energy ({energy_unit}), electricity, and natural gas consumption (1999–2024).")
    st.plotly_chart(
        visual1_history_trends(hist, HISTORY_SERIES_FOR_CHARTS, (VIEW_START, HISTORY_END),
                               unit_energy=energy_unit, break_year=total_break,
                               factor=e_factor),
        use_container_width=True, config=_CHART_CONFIG)

    # Visual 2: Scenario Fans
    st.markdown(
        section_title(f"V2 — {horizon} scenarios: Low / Base / High", "scenario",
                      badge=f"2025–{horizon} · GDP {base_gdp:.1f}% ± {spread:.2f}pp · "
                            f"objective 2"),
        unsafe_allow_html=True)
    st.caption(f"Demand fan forecasts (2025–{horizon}) across Low, Base, and High macro-scenarios with confidence envelopes for final energy, electricity, and gas.")
    st.plotly_chart(
        visual2_scenario_fans(data["bands"], hist, HISTORY_SERIES_FOR_CHARTS,
                              scenarios, unit_energy=energy_unit, factor=e_factor,
                              break_year=HISTORY_END),
        use_container_width=True, config=_CHART_CONFIG)

    # Visual 3: Demand Drivers
    st.markdown(
        section_title("V3 — Demand drivers: GDP, GDP growth and population",
                      "insights", badge=f"calibrated {calib_start}–{HISTORY_END} · objective 3"),
        unsafe_allow_html=True)
    st.caption(f"Econometric relationship between energy demand and core drivers: real GDP per capita, population expansion, and log-log elasticity fits.")
    st.plotly_chart(
        visual3_drivers(hist, models.get("total_final", {}), "total_final",
                        (VIEW_START, HISTORY_END), unit_energy=energy_unit,
                        factor=e_factor),
        use_container_width=True, config=_CHART_CONFIG)

    # Visual 4: Driver Decomposition
    st.markdown(
        section_title("V4 — What drives the growth: income, population or intensity",
                      "chart", badge=f"total final energy · objective 3"),
        unsafe_allow_html=True)
    st.caption("Year-by-year decomposition of demand growth into income effect (per-capita GDP), demographic growth (population), and structural energy intensity shifts.")
    st.plotly_chart(
        visual4_decomposition(data["decomposition"].get("total_final"),
                              series_spec("total_final")["short"]),
        use_container_width=True, config=_CHART_CONFIG)

    # Visual 5: Sector and Province Mix
    st.markdown(
        section_title("V5 — Who consumes: end-use sector and province", "demand",
                      badge=f"{elec_unit} · reported vs {horizon} {base_scenario} · objective 4"),
        unsafe_allow_html=True)
    st.caption(f"Electricity consumption distribution ({elec_unit}) across economic sectors (Domestic, Industrial, Commercial, Agriculture) and provincial share paths to {horizon}.")
    sector_col, province_col = st.columns(2)
    with sector_col:
        st.plotly_chart(
            visual5_sector_mix(data["sectors"], horizon, unit_elec=elec_unit,
                               factor=g_factor, scenario=base_scenario),
            use_container_width=True, config=_CHART_CONFIG)
    with province_col:
        st.plotly_chart(
            visual5_province_mix(data["provinces"], horizon, scenario=base_scenario),
            use_container_width=True, config=_CHART_CONFIG)

    # Visual 6: Supply Gap & Import Dependency
    st.markdown(
        section_title("V6 — Supply against demand, and import dependency", "supply",
                      badge=f"{energy_unit} · to {horizon} · objective 5"),
        unsafe_allow_html=True)
    st.caption(f"Projected supply-demand gap ({energy_unit}) and rising fuel import dependency to {horizon} if indigenous supply expansion remains constrained.")
    gap_col, import_col = st.columns(2)
    with gap_col:
        st.plotly_chart(
            visual6_gap(data["gap"].get("total"), unit_energy=energy_unit,
                        factor=e_factor, base_scenario=base_scenario),
            use_container_width=True, config=_CHART_CONFIG)
    with import_col:
        st.plotly_chart(
            visual6_imports(data["gap"].get("imports"), horizon),
            use_container_width=True, config=_CHART_CONFIG)

    # Visual 7: Forecast Reliability
    tests = data["backtest"]
    metrics = tests.get("metrics")
    predictions = tests.get("predictions")
    train_end = int(tests.get("train_end", HISTORY_END - 4))

    st.markdown(
        section_title("V7 — Forecast reliability: backtest", "intensity",
                      badge=f"hold-out {train_end + 1}–{HISTORY_END} · MAPE / RMSE / R² · "
                            f"objective 6"),
        unsafe_allow_html=True)
    st.caption("Hold-out out-of-sample backtesting validation comparing Driver vs Trend models with MAPE, RMSE, and trajectory tracking.")
    reliability_col, path_col = st.columns(2)

    with reliability_col:
        st.plotly_chart(
            visual7_backtest_mape(metrics, train_end, HISTORY_END),
            use_container_width=True, config=_CHART_CONFIG)

    with path_col:
        options = {}
        if predictions is not None and not predictions.empty:
            for _, row in predictions.drop_duplicates("series").iterrows():
                options[str(row["label"])] = str(row["series"])
        if options:
            chosen_label = st.selectbox("Series to inspect", list(options.keys()),
                                        key="q4_backtest_series")
            chosen_key = options[chosen_label]
            spec = series_spec(chosen_key)
            chart_factor = e_factor if spec["domain"] == "energy" else g_factor
            chart_unit = energy_unit if spec["domain"] == "energy" else elec_unit
            st.plotly_chart(
                visual7_backtest_path(predictions, chosen_key, unit=chart_unit,
                                      factor=chart_factor, label=spec["short"]),
                use_container_width=True, config=_CHART_CONFIG)
        else:
            st.plotly_chart(visual7_backtest_path(predictions or pd.DataFrame(),
                                                  "total_final", unit=energy_unit,
                                                  factor=e_factor),
                            use_container_width=True, config=_CHART_CONFIG)

    # Reliability Table
    # Only MAPE and RMSE are read from the four-year hold-out; R² is taken from
    # the calibration fit, where it means something.
    if metrics is not None and not metrics.empty:
        hold_out = metrics[metrics["window"] == "hold-out"].set_index(["series", "model"])
        in_sample = metrics[metrics["window"] == "in-sample"].set_index(["series", "model"])
        best_per_series = (metrics[metrics["window"] == "hold-out"]
                           .groupby("series")["mape"].min().to_dict())
        rows = []
        for (series_key, model_name), row in hold_out.iterrows():
            fit = in_sample.loc[(series_key, model_name)] \
                if (series_key, model_name) in in_sample.index else None
            is_best = abs(row["mape"] - best_per_series.get(series_key, float("nan"))) < 1e-9
            rows.append({
                "Series": series_spec(series_key)["short"],
                "Model": model_name,
                "Hold-out MAPE %": round(float(row["mape"]), 2),
                "Hold-out RMSE": round(float(row["rmse"])),
                "Bias %": round(float(row["bias"]), 1),
                "Calibration R²": round(float(fit["r2"]), 3) if fit is not None else None,
                "Better model": "◀ lower error" if is_best else "",
            })
        table = (pd.DataFrame(rows)
                 .sort_values(["Series", "Hold-out MAPE %"])
                 .reset_index(drop=True))
        st.dataframe(table, use_container_width=True, hide_index=True)

    # ── footer ─────────────────────────────────────────────────────────────
    worst_mape = float("nan")
    best_model = "—"
    if metrics is not None and not metrics.empty:
        hold_out = metrics[metrics["window"] == "hold-out"]
        if not hold_out.empty:
            row = hold_out.loc[hold_out["mape"].idxmin()]
            worst_mape = float(row["mape"])
            best_model = f"{row['label']} · {row['model']}"

    st.markdown(
        dashboard_footer(
            scope_line=(f"Reported {VIEW_START}–{HISTORY_END}, modelled 2025–{horizon} · "
                        f"{len(SCENARIO_ORDER)} scenarios · forecast basis {model_choice} · "
                        f"8 elements covering 6 objectives"),
            method_line=(
                f"Income elasticity from ln(demand/head) ~ ln(real GDP/head) fitted "
                f"{calib_start}–{HISTORY_END} with a 2019 basis dummy; growth = population + "
                f"ε × GDP per head + residual, residual fading to zero by {horizon}. "
                f"Low/Base/High = GDP {base_gdp:.1f}% ∓ {spread:.2f}pp. "
                f"Best hold-out MAPE {worst_mape:.1f}% ({best_model})."
                if math.isfinite(worst_mape) else
                f"Income elasticity from ln(demand/head) ~ ln(real GDP/head) fitted "
                f"{calib_start}–{HISTORY_END} with a 2019 basis dummy."),
            source_line=("World Bank (GDP, population) · Pakistan Energy Yearbook / EIA via "
                         "energy_database_new (final energy, gas balance, electricity)"),
            note=(f"fact_final_energy_consumption changes reporting basis in {total_break} "
                  f"— modelled with a level dummy, so the level gap between primary supply "
                  f"and final demand in V6 is indicative. Hold-out windows are four years "
                  f"long: read MAPE and RMSE from them, R² from the calibration fit."
                  if total_break else
                  "Hold-out windows are four years long: read MAPE and RMSE from them, "
                  "R² from the calibration fit."),
            icon_name="demand",
        ),
        unsafe_allow_html=True,
    )
