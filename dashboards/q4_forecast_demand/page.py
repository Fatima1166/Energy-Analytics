"""
Forecasted Energy Demand dashboard (Question 4).

Question 4 asks what energy demand will be, so this page keeps only what that
answer needs:

  1. Sidebar    -- which scenarios to draw, and how far ahead to forecast
  2. KPI cards  -- demand now, demand at the horizon, and how fast it grows
  3. Visuals    -- where demand has been, the three paths to the horizon, what
                   moves it, who uses the electricity, and how far the forecast
                   can be trusted

Two things are deliberately not here.  What supply will do -- the supply gap and
import dependency -- is Question 5's job, and the model is fitted on the whole
record with the data-driven defaults, so there are no fitting knobs to turn.
"""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.demand_forecast import (
    DEFAULT_BASE_GDP_GROWTH,
    DEFAULT_CALIB_START,
    DEFAULT_SCENARIO_SPREAD,
    HISTORY_END,
    HORIZON,
    SCENARIO_COLORS,
    SCENARIO_ORDER,
    build_dashboard_data,
)
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_SECTOR_CONSUMPTION,
    Q_FINAL_ENERGY_BY_SOURCE,
    Q_RENEWABLE_ENERGY,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt, normalise

from .charts import (
    visual1_history_trends,
    visual2_scenario_fans,
    visual3_drivers,
    visual4_sector_mix,
    visual5_reliability,
)

VIEW_START = 2000
HISTORY_SERIES_FOR_CHARTS = ["total_final", "electricity_final", "gas_final"]
FILTERS_KEY = "q4_filters"

_CHART_CONFIG = {"displayModeBar": False}


# --- Sidebar controls ---

def _recent_gdp_growth(econ_df: pd.DataFrame) -> float:
    """Median real GDP growth of the last ten reported years, as a %."""
    try:
        series = (pd.to_numeric(econ_df["gdp_growth_pct"], errors="coerce")
                  .dropna().tail(10))
        if not series.empty:
            value = float(series.median())
            if math.isfinite(value):
                return float(min(max(round(value, 1), 1.0), 8.0))
    except Exception:
        pass
    return DEFAULT_BASE_GDP_GROWTH


def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Forecast</div>',
                        unsafe_allow_html=True)

    scenarios = st.sidebar.multiselect(
        "Scenarios to show", SCENARIO_ORDER, default=SCENARIO_ORDER,
        key="q4_scenarios",
        help=("Which paths to draw: a slow-growing economy, the planned one, "
              "or a fast-growing one."),
    )
    if not scenarios:
        scenarios = ["Base"]

    horizon = st.sidebar.slider(
        "Forecast up to", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q4_horizon",
        help="The last year the model looks ahead to.",
    )

    st.session_state[FILTERS_KEY] = {
        "scenarios": list(scenarios),
        "horizon": int(horizon),
    }
    st.sidebar.divider()


# ═══════════════════════════════ UI helpers ═════════════════════════════════

# The shared card sheet in core/styles.py pins every .kpi-balance card to a fixed
# 225px and pushes its detail rows to the bottom, which leaves a dead band across
# the middle of a short card.  These page-scoped selectors carry the same
# !important but match more precisely, so they win -- and only for this page.
# Cards in the row stay level because each one carries three detail rows and the
# title block reserves two lines, not because a card height is forced.
_CARD_CSS = """
<style>
  .kpi-balance.q4-kpi {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      justify-content: flex-start !important;
      padding: 13px 14px 12px !important;
  }
  .kpi-balance.q4-kpi .kpi-balance-details { margin-top: 0 !important; }
</style>
"""


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
<div class="kpi-balance q4-kpi" style="border: 1px solid {accent}44;">
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
  <div class="kpi-balance-details">{detail}</div>
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
    horizon = int(filters.get("horizon", HORIZON))
    base_scenario = "Base" if "Base" in scenarios else scenarios[0]

    energy_unit = normalise(units.get("energy", "TOE"))
    elec_unit = normalise(units.get("electricity", "GWh"))
    e_factor = display_factor("energy", energy_unit)
    g_factor = display_factor("electricity", elec_unit)

    # Fetch data.  The supply and province tables are handed over empty on
    # purpose: what supply will do is Question 5's answer, and every table here
    # is a MySQL round trip this page would otherwise throw away.
    try:
        econ_df = run_query(Q_ECONOMIC)
        data = build_dashboard_data(
            fuel_df=run_query(Q_FINAL_ENERGY_BY_SOURCE),
            re_df=run_query(Q_RENEWABLE_ENERGY),
            econ_df=econ_df,
            primary_df=pd.DataFrame(),
            gen_df=pd.DataFrame(),
            gas_df=pd.DataFrame(),
            sector_df=run_query(Q_ELEC_SECTOR_CONSUMPTION),
            province_df=pd.DataFrame(),
            scenarios=scenarios,
            calib_start=DEFAULT_CALIB_START,
            horizon=horizon,
            base_gdp_growth=_recent_gdp_growth(econ_df),
            spread=DEFAULT_SCENARIO_SPREAD,
            model_choice="Driver",
        )
    except Exception as exc:
        st.error(f"Could not load demand data: {exc}")
        st.stop()

    hist = data["history"]
    models = data["models"]
    kpis = data["kpis"]
    breaks = data.get("breaks", {})
    total_break = breaks.get("total_final")

    # KPI cards -- the three numbers the question asks for
    total = kpis.get("total_final", {})
    grid = kpis.get("elec_grid", {})
    cagr = kpis.get("demand_cagr", {})

    total_now = _num(total.get("value")) * e_factor
    total_horizon = _num(total.get("horizon_value")) * e_factor
    total_change = _pct_change(total_now, total_horizon)
    grid_now = _num(grid.get("value")) * g_factor
    grid_horizon = _num(grid.get("horizon_value")) * g_factor
    grid_change = _pct_change(grid_now, grid_horizon)

    cards = [
        _kpi_card(
            "K1", f"Total energy demand, {total.get('year', HISTORY_END)}",
            fmt(total_now), energy_unit,
            [(f"By {horizon}", fmt(total_horizon), "#E2E8F0"),
             ("Change", f"{total_change:+.1f}%", "#10B981" if total_change >= 0 else "#EF4444"),
             ("Scenario", base_scenario, SCENARIO_COLORS.get(base_scenario, "#00A6FB"))],
            accent="#00A6FB", icon_name="primary_energy",
            badge=f"{base_scenario} case to {horizon}", badge_colour="#00A6FB",
        ),
        _kpi_card(
            "K2", f"Electricity demand, {grid.get('year', HISTORY_END)}",
            fmt(grid_now), elec_unit,
            [(f"By {horizon}", fmt(grid_horizon), "#E2E8F0"),
             ("Change", f"{grid_change:+.1f}%", "#10B981" if grid_change >= 0 else "#EF4444"),
             ("Scenario", base_scenario, SCENARIO_COLORS.get(base_scenario, "#00A6FB"))],
            accent="#10B981", icon_name="generation",
            badge=f"grows {_num(grid.get('growth_pct')):+.1f}% a year",
            badge_colour="#10B981",
        ),
        _kpi_card(
            "K3", "How fast demand grows",
            f"{_num(cagr.get('forecast_cagr_pct')):+.2f}", "% a year",
            [("Seen in the data", f"{_num(cagr.get('observed_cagr_pct')):+.2f}% a year", "#94A3B8"),
             ("Fitted on", f"{int(_num(cagr.get('calib_start')))}–{int(_num(cagr.get('calib_end')))}", "#94A3B8"),
             ("Years ahead", f"{_num(cagr.get('forecast_years')):.0f}", "#E2E8F0")],
            accent="#A78BFA", icon_name="scenario",
            badge=f"to {horizon}", badge_colour="#A78BFA",
        ),
    ]

    # The row is cut into four slots like every other dashboard's KPI strip, but
    # only three cards go in it -- the fourth slot stays blank, so each card keeps
    # the width a four-up row gives it instead of stretching over the space.
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # --- Visual 1: what demand has actually done ---
    st.markdown(
        section_title("Visual 1 – Demand so far", "chart",
                      badge=f"{VIEW_START}–{HISTORY_END} · {energy_unit}"),
        unsafe_allow_html=True)
    st.caption(f"How much energy the country has used each year — all energy, electricity and gas — and how each one has grown since {VIEW_START}.")
    st.plotly_chart(
        visual1_history_trends(hist, HISTORY_SERIES_FOR_CHARTS, (VIEW_START, HISTORY_END),
                               unit_energy=energy_unit, break_year=total_break,
                               factor=e_factor),
        use_container_width=True, config=_CHART_CONFIG)

    # --- Visual 2: the forecast itself ---
    st.markdown(
        section_title(f"Visual 2 – Three ways demand can go", "scenario",
                      badge=f"{HISTORY_END + 1}–{horizon} · {', '.join(scenarios)}"),
        unsafe_allow_html=True)
    st.caption(f"Where demand has been, and the three paths it can take to {horizon}: a slow-growing economy, the planned one, and a fast-growing one. Dashed lines are the model's guess, not a measurement.")
    st.plotly_chart(
        visual2_scenario_fans(data["bands"], hist, HISTORY_SERIES_FOR_CHARTS,
                              scenarios, unit_energy=energy_unit, factor=e_factor,
                              break_year=HISTORY_END),
        use_container_width=True, config=_CHART_CONFIG)

    # --- Visual 3: why the forecast moves ---
    st.markdown(
        section_title("Visual 3 – What moves demand", "insights",
                      badge=f"fitted {DEFAULT_CALIB_START}–{HISTORY_END}"),
        unsafe_allow_html=True)
    st.caption("Demand next to the two things that push it up: how much the economy makes, and how many people there are. The dots on the right show that when income per head rises, energy per head rises with it.")
    st.plotly_chart(
        visual3_drivers(hist, models.get("total_final", {}), "total_final",
                        (VIEW_START, HISTORY_END), unit_energy=energy_unit,
                        factor=e_factor),
        use_container_width=True, config=_CHART_CONFIG)

    # --- Visuals 4 and 5: who uses it, and how far to trust the guess ---
    tests = data["backtest"]
    metrics = tests.get("metrics")
    train_end = int(tests.get("train_end", HISTORY_END - 4))

    use_col, trust_col = st.columns(2)
    with use_col:
        st.markdown(
            section_title("Visual 4 – Who uses the electricity", "demand",
                          badge=f"{elec_unit} · {base_scenario} to {horizon}"),
            unsafe_allow_html=True)
        st.caption(f"Electricity used by each sector in the last measured year, and what the same sectors use in {horizon}.")
        st.plotly_chart(
            visual4_sector_mix(data["sectors"], horizon, unit_elec=elec_unit,
                               factor=g_factor, scenario=base_scenario),
            use_container_width=True, config=_CHART_CONFIG)

    with trust_col:
        st.markdown(
            section_title("Visual 5 – How far to trust the forecast", "intensity",
                          badge=f"tested on {train_end + 1}–{HISTORY_END}"),
            unsafe_allow_html=True)
        st.caption("The models were asked to predict the last four years without having seen them. Each bar is how far off that guess was on average — a shorter bar is a better forecast.")
        st.plotly_chart(
            visual5_reliability(metrics, train_end, HISTORY_END),
            use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    line1 = (f"In the {base_scenario} case, total energy demand grows "
             f"{total_change:+.1f}% to {fmt(total_horizon)} {energy_unit} by "
             f"{horizon}.")
    line2 = (f"Electricity demand moves {grid_change:+.1f}% to "
             f"{fmt(grid_horizon)} {elec_unit} — new plants should be planned "
             "around that bigger number.")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
