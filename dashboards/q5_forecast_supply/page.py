"""
Forecasted Energy Supply dashboard (Question 5).

Question 5 asks what energy supply will be, so this page keeps only what that
answer needs:

  1. Sidebar    -- which scenarios to draw, and how far ahead to forecast
  2. KPI cards  -- supply now, supply at the horizon, and whether it covers demand
  3. Visuals    -- where supply has been, the three paths to the horizon, what the
                   supply is made of, whether it keeps up with demand, where it
                   comes from, and how far the forecast can be trusted

Two things are deliberately not here.  How much demand there will be is Question
4's answer; this page does not refit it, it only carries the last measured demand
forward at a flat 4.8% a year as the line supply is measured against.  And
installed plant capacity (MW) is a build-plan number rather than a supply, so it
gets no card and no chart.  The model is fitted on the whole record with the
data-driven defaults, so there are no fitting knobs to turn.
"""

from __future__ import annotations

import math
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
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
    visual4_supply_vs_demand,
    visual5_domestic_vs_imports,
    visual6_reliability,
)

FILTERS_KEY = "q5_filters"
_CHART_CONFIG = {"displayModeBar": False}

# The engine's adequacy labels, said the way a person would say them.
STATUS_WORDS = {
    "Deficit Risk": "Not enough supply",
    "Optimal Reserve": "Comfortable margin",
    "Capacity Trap Burden": "More built than needed",
}

# Balanced fixed height and bottom-anchored details so every card in the row
# aligns strictly along the bottom edge.
_CARD_CSS = """
<style>
  .kpi-balance.q5-kpi {
      height: 195px !important;
      min-height: 195px !important;
      max-height: 195px !important;
      justify-content: space-between !important;
      padding: 13px 14px 12px !important;
      box-sizing: border-box !important;
  }
  .kpi-balance.q5-kpi .kpi-balance-details {
      margin-top: auto !important;
      border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
      padding-top: 6px !important;
  }
</style>
"""


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
    st.sidebar.markdown('<div class="dsh-side-title">Supply</div>',
                        unsafe_allow_html=True)

    scenarios = st.sidebar.multiselect(
        "Scenarios to show", SCENARIO_ORDER, default=SCENARIO_ORDER, key="q5_scenarios",
        help=("Which paths to draw: slow supply growth, the planned one, "
              "or fast supply growth."),
    )
    if not scenarios:
        scenarios = ["Base"]

    horizon = st.sidebar.slider(
        "Forecast up to", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q5_horizon",
        help="The last year the model looks ahead to.",
    )

    st.session_state[FILTERS_KEY] = {
        "scenarios": list(scenarios),
        "horizon": int(horizon),
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
<div class="kpi-balance q5-kpi" style="border: 1px solid {accent}44;">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
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
              margin-bottom:4px;min-height:28px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:6px;">
    <span style="color:{accent};font-size:23px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details">{detail}</div>
</div>
"""


# --- Small readers --

def _num(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _signed(value: float, suffix: str = "") -> str:
    """A plus-or-minus number in words a reader can trust, or '--'."""
    return f"{value:+.1f}{suffix}" if math.isfinite(value) else "--"


def _change(first: float, last: float) -> float:
    if not math.isfinite(first) or not math.isfinite(last) or first == 0:
        return float("nan")
    return (last / first - 1.0) * 100.0


def _growth_a_year(first: float, last: float, years: int) -> float:
    if not math.isfinite(first) or not math.isfinite(last) or first <= 0 or years <= 0:
        return float("nan")
    return ((last / first) ** (1.0 / years) - 1.0) * 100.0


def _row_at(frame: pd.DataFrame, year: int, scenario: str):
    """The row of `frame` for that year and scenario, or None."""
    if frame is None or frame.empty:
        return None
    sub = frame[(frame["calendar_year"] == int(year)) & (frame["scenario"] == scenario)]
    return sub.iloc[0] if not sub.empty else None


def _forecast_value(forecast: pd.DataFrame, series: str, scenario: str, year: int) -> float:
    """The modelled level for one series, scenario and year."""
    if forecast is None or forecast.empty:
        return float("nan")
    sub = forecast[(forecast["series"] == series) & (forecast["scenario"] == scenario)
                   & (forecast["calendar_year"] == int(year))]
    return _num(sub.iloc[0]["value"], float("nan")) if not sub.empty else float("nan")


def _last_reported(frame: pd.DataFrame, col: str):
    """(value, year) from the most recent year that actually reported `col`.

    Rule 4: the card wears the year its number really came from.  When no year
    has a reading the value stays NaN (rendered '--') and the year is 0, so the
    page never prints a make-believe 0 under a year that gave nothing.
    """
    if frame is None or frame.empty or col not in frame.columns:
        return float("nan"), 0
    series = pd.to_numeric(frame[col], errors="coerce")
    reported = series[series.notna()]
    if reported.empty:
        return float("nan"), 0
    idx = reported.index[-1]
    return float(reported.iloc[-1]), int(frame.loc[idx, "calendar_year"])


def _year_phrase(year: int, base_value: float) -> str:
    """The year to put in a title, or 'no reading' when there is no value."""
    if year and math.isfinite(base_value):
        return str(year)
    return "no reading"


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Forecasted Energy Supply dashboard."""
    flt = st.session_state.get(FILTERS_KEY) or {}
    scenarios = flt.get("scenarios") or list(SCENARIO_ORDER)
    horizon = int(flt.get("horizon", HORIZON))
    clean_target_pct = CLEAN_POLICY_TARGET_DEFAULT
    active_sc = "Base" if "Base" in scenarios else scenarios[0]

    # Fetch data -- four tables, and every one of them ends up on a card or a chart.
    try:
        ec_df = run_query(Q_ECONOMIC)
        data = build_supply_dashboard_data(
            primary_df=run_query(Q_PRIMARY_SUPPLY),
            re_df=run_query(Q_RENEWABLE_ENERGY),
            econ_df=ec_df,
            gen_df=run_query(Q_ELEC_GEN),
            scenarios=scenarios,
            calib_start=DEFAULT_CALIB_START,
            horizon=horizon,
            base_gdp_growth=_recent_gdp_growth(ec_df),
            spread=DEFAULT_SCENARIO_SPREAD,
            clean_target_pct=clean_target_pct,
            model_choice="Driver",
        )
    except Exception as exc:
        st.error(f"Could not load supply data: {exc}")
        st.stop()

    # Unit conversions
    units = get_units()
    unit_energy = units.get("energy", "TOE")
    factor_energy = display_factor("energy", unit_energy)

    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)

    # The numbers the three cards read: supply now, supply at the horizon, and
    # whether that supply covers demand.
    hist = data["history"]
    forecast = data["forecast"]
    adequacy = data["adequacy"]
    if hist.empty:
        st.error("No reported supply history to forecast from.")
        st.stop()

    # Each card wears the year its own series last reported, so a supply number
    # and a generation number never wear the same label when their data years
    # differ, and neither prints a 0 for a year that gave no reading.
    tpes_base_now, tpes_year = _last_reported(hist, "tpes_toe")
    gen_base_now, gen_year = _last_reported(hist, "gen_total_gwh")
    years_ahead = max(horizon - gen_year, 1) if gen_year else 1

    tpes_base_next = _forecast_value(forecast, "tpes_toe", active_sc, horizon)
    if not math.isfinite(tpes_base_next):
        tpes_base_next = tpes_base_now
    gen_base_next = _forecast_value(forecast, "gen_total_gwh", active_sc, horizon)
    if not math.isfinite(gen_base_next):
        gen_base_next = gen_base_now

    tpes_now = tpes_base_now * factor_energy
    tpes_next = tpes_base_next * factor_energy
    gen_now = gen_base_now * factor_elec
    gen_next = gen_base_next * factor_elec
    tpes_change = _change(tpes_now, tpes_next)
    gen_change = _change(gen_now, gen_next)
    gen_pace = _growth_a_year(gen_base_now, gen_base_next, years_ahead)

    energy_decimals = 1 if unit_energy == "MTOE" else 0
    elec_decimals = 1 if unit_elec == "TWh" else 0

    adeq = _row_at(adequacy, horizon, active_sc)
    if adeq is None and not adequacy.empty:
        adeq = adequacy.iloc[-1]
    if adeq is None:
        st.error("Supply could not be compared with demand.")
        st.stop()
    margin_pct = _num(adeq.get("reserve_margin_pct"))
    supply_next = _num(adeq.get("supply_gwh")) * factor_elec
    demand_next = _num(adeq.get("demand_gwh")) * factor_elec
    status_word = STATUS_WORDS.get(str(adeq.get("adequacy_status")),
                                   str(adeq.get("adequacy_status")))
    status_colour = str(adeq.get("status_color") or "#10B981")

    cards = [
        _kpi_card(
            code="K1",
            title=f"Total primary energy supply, {_year_phrase(tpes_year, tpes_base_now)}",
            value=fmt(tpes_now, energy_decimals),
            unit=unit_energy,
            rows=[
                (f"By {horizon}", fmt(tpes_next, energy_decimals), "#E2E8F0"),
                ("Change", _signed(tpes_change, "%"),
                 "#10B981" if tpes_change >= 0 else "#EF4444"),
                ("Scenario", active_sc, "#00A6FB"),
            ],
            accent="#00A6FB",
            icon_name="primary_energy",
            badge=f"{active_sc} case to {horizon}",
            badge_colour="#00A6FB",
        ),
        _kpi_card(
            code="K2",
            title=f"Electricity generation, {_year_phrase(gen_year, gen_base_now)}",
            value=fmt(gen_now, elec_decimals),
            unit=unit_elec,
            rows=[
                (f"By {horizon}", fmt(gen_next, elec_decimals), "#E2E8F0"),
                ("Change", _signed(gen_change, "%"),
                 "#10B981" if gen_change >= 0 else "#EF4444"),
                ("Scenario", active_sc, "#10B981"),
            ],
            accent="#10B981",
            icon_name="supply",
            badge=(f"grows {gen_pace:+.1f}% a year" if math.isfinite(gen_pace) else ""),
            badge_colour="#10B981",
        ),
        _kpi_card(
            code="K3",
            title=f"Does supply cover demand in {horizon}",
            value=f"{margin_pct:+.1f}",
            unit="% margin over demand",
            rows=[
                ("Supply", f"{fmt(supply_next, 0)} {unit_elec}", "#00A6FB"),
                ("Demand", f"{fmt(demand_next, 0)} {unit_elec}", "#F59E0B"),
                ("Comfortable band", "15% – 25%", "#94A3B8"),
            ],
            accent=status_colour,
            icon_name="intensity",
            badge=status_word,
            badge_colour=status_colour,
        ),
    ]

    # Four slots like every other KPI strip, but only three cards go in it, so the
    # fourth slot stays blank and each card keeps the width of a four-up row.
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # --- Visual 1: what supply has actually done ---
    st.markdown(
        section_title("Visual 1 – Supply so far", "chart",
                      badge=f"up to {HISTORY_END}"),
        unsafe_allow_html=True)
    st.caption("Energy the country had each year, by source, and the electricity it generated.")
    st.plotly_chart(
        visual1_history_trajectory(hist=hist, unit_energy=unit_energy,
                                   factor_energy=factor_energy,
                                   unit_elec=unit_elec, factor_elec=factor_elec),
        use_container_width=True, config=_CHART_CONFIG)

    # --- Visual 2: the forecast itself ---
    st.markdown(
        section_title(f"Visual 2 – Three ways supply can go", "scenario",
                      badge=f"{HISTORY_END + 1}–{horizon} · {', '.join(scenarios)}"),
        unsafe_allow_html=True)
    st.caption(f"Supply so far, then three paths to {horizon}: slow, planned and fast. The dashed part is the model's guess.")
    st.plotly_chart(
        visual2_scenario_fans(hist=hist, forecast=forecast, scenarios=scenarios,
                              unit_energy=unit_energy, factor_energy=factor_energy,
                              unit_elec=unit_elec, factor_elec=factor_elec),
        use_container_width=True, config=_CHART_CONFIG)

    # --- Visuals 3 and 4: what the electricity is made of, and does it cover demand ---
    mix_col, cover_col = st.columns(2)

    with mix_col:
        st.markdown(
            section_title("Visual 3 – What the electricity is made of", "renewables",
                          badge=f"{active_sc} to {horizon}"),
            unsafe_allow_html=True)
        st.caption(f"Which sources generate the power, and the clean share next to the {clean_target_pct:.0f}% and 30% goals.")
        st.plotly_chart(
            visual3_technology_mix(tech_mix=data["tech_mix"],
                                   active_scenario=active_sc,
                                   clean_target=clean_target_pct,
                                   unit_elec=unit_elec, factor_elec=factor_elec),
            use_container_width=True, config=_CHART_CONFIG)

    with cover_col:
        st.markdown(
            section_title("Visual 4 – Does supply cover demand", "intensity",
                          badge=f"{active_sc} to {horizon}"),
            unsafe_allow_html=True)
        st.caption("Blue is the electricity supply, amber is the demand. The shaded part is spare supply.")
        st.plotly_chart(
            visual4_supply_vs_demand(adequacy_df=adequacy, active_scenario=active_sc,
                                     unit_elec=unit_elec, factor_elec=factor_elec),
            use_container_width=True, config=_CHART_CONFIG)

    # --- Visuals 5 and 6: where it comes from, and how far to trust the guess ---
    tests = data["backtest"]
    train_end = int(tests.get("train_end", HISTORY_END - 4))
    test_end = int(tests.get("test_end", HISTORY_END))

    source_col, trust_col = st.columns(2)

    with source_col:
        st.markdown(
            section_title("Visual 5 – Where the supply comes from", "imports",
                          badge=f"{active_sc} to {horizon}"),
            unsafe_allow_html=True)
        st.caption("Energy made at home and energy bought from abroad, with the imported share.")
        st.plotly_chart(
            visual5_domestic_vs_imports(security_df=data["security"],
                                        active_scenario=active_sc,
                                        unit_energy=unit_energy,
                                        factor_energy=factor_energy),
            use_container_width=True, config=_CHART_CONFIG)

    with trust_col:
        st.markdown(
            section_title("Visual 6 – How far to trust the forecast", "insights",
                          badge=f"tested on {train_end + 1}–{test_end}"),
            unsafe_allow_html=True)
        st.caption("Both models guessed four years they had not been shown. A shorter bar means a better guess.")
        st.plotly_chart(
            visual6_reliability(tests.get("table"), train_end, test_end),
            use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    line1 = (f"In the {active_sc} case, {horizon} supply of "
             f"{fmt(supply_next, 0)} {unit_elec} covers demand of "
             f"{fmt(demand_next, 0)} {unit_elec} — a {margin_pct:+.1f}% spare "
             "margin.")
    line2 = (f"Under 15% spare is risky in a bad year, over 25% pays for plant "
             f"that sits idle. This case lands at {margin_pct:+.1f}%, rated "
             f"{status_word.lower()}.")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
