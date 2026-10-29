"""
dashboards/q7_forecast_cost/page.py

Question 7 asks: what does electricity bought from power producers cost, and what
will it cost?

This page keeps only what that answer needs:

  Sidebar -- which build-out cases to price, and how far ahead to look
  Cards   -- the bill for the years already reported, the bill the model points
            to, and what one unit of electricity costs in each
  Visuals -- what each source was paid, where the money goes, the forecast
            bill, the price of one unit, and how fuel prices and the model's
            own error change the answer

Four things were taken off the page.  The cost avoided by renewables is
Question 8's answer, not this one.  The tariff heat-map only repeated the price
assumption that was fed to the model.  The hold-out table showed the same numbers
as the bars in Visual 5.  And the fuel-escalation, sensitivity-band, calibration
and GDP sliders were model settings rather than part of the question, so the page
now uses the model's own stated values (3% fuel escalation a year, tested at 1%
and 5%).

Nothing here is measured past the last reported year: the line splits at 2024,
and everything to the right of it is a modelled outlook.  Every number comes from
core/cost_forecast.py; this file only draws.
"""

from __future__ import annotations

import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.cost_forecast import (
    COST_SCENARIO_ORDER,
    DEFAULT_FUEL_INFL,
    DEFAULT_SPREAD_PP,
    HORIZON,
    build_cost_dashboard_data,
)
from core.icons import icon
from core.queries import Q_ECONOMIC, Q_RENEWABLE_ENERGY
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_cost_so_far,
    visual2_forecast_bill,
    visual3_where_money_goes,
    visual4_unit_price,
    visual5_fuel_and_trust,
)
from .config import (
    AMBER,
    BLUE,
    CASE_WORDS,
    CYAN,
    DEFAULT_CASE,
    GREEN,
    LIGHT,
    RED,
    TECHS_SHOWN,
)

_FILTERS_KEY = "q7_filters"
_CHART_CONFIG = {"displayModeBar": False}

# The shared card sheet in core/styles.py pins every .kpi-balance card to a fixed
# 225px and pushes its detail rows to the bottom, which leaves a dead band across
# the middle of a short card.  These page-scoped selectors carry the same
# !important but match more precisely, so they win -- and only for this page.
_CARD_CSS = """
<style>
  .kpi-balance.q7-kpi {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      justify-content: flex-start !important;
      padding: 13px 14px 12px !important;
  }
  .kpi-balance.q7-kpi .kpi-balance-details { margin-top: 0 !important; }
</style>
"""


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Producer Cost</div>',
                        unsafe_allow_html=True)

    cases = st.sidebar.multiselect(
        "Build-out cases to show", list(COST_SCENARIO_ORDER),
        default=list(COST_SCENARIO_ORDER), key="q7_cases",
        format_func=lambda case: CASE_WORDS.get(case, case),
        help=("All three cases buy the same amount of electricity.  Only the mix "
              "of sources differs, so the difference between the lines is the "
              "difference in what is bought from where."),
    )
    if not cases:
        cases = [DEFAULT_CASE]

    horizon = st.sidebar.slider(
        "Forecast up to", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q7_horizon",
        help="The year the outlook is read at.",
    )

    st.session_state[_FILTERS_KEY] = {
        "cases": list(cases),
        "horizon": int(horizon),
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = AMBER, icon_name: str = "cost",
              badge: str = "", badge_colour: str = AMBER) -> str:
    """Compact dark glassmorphism KPI card, sized to its own content."""
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
<div class="kpi-balance q7-kpi" style="border: 1px solid {accent}44;">
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


# --- Small readers ---

def _row_at_year(df, year: int, case: str | None = None):
    """The forecast row for one case in one year, or the last year it has."""
    if df is None or df.empty:
        return None
    sub = df if case is None else df[df["scenario"] == case]
    if sub.empty:
        return None
    hit = sub[sub["calendar_year"] == year]
    return sub.iloc[[-1]] if hit.empty else hit


# --- Main dashboard render ---

def render() -> None:
    """Renders the Forecasted Producer Cost dashboard (Question 7)."""
    flt = st.session_state.get(_FILTERS_KEY, {})
    cases = flt.get("cases", list(COST_SCENARIO_ORDER))
    horizon = flt.get("horizon", HORIZON)
    active = DEFAULT_CASE if DEFAULT_CASE in cases else cases[0]
    active_word = CASE_WORDS.get(active, active)

    data = build_cost_dashboard_data(
        re_df=run_query(Q_RENEWABLE_ENERGY),
        econ_df=run_query(Q_ECONOMIC),
        scenarios=cases,
        horizon=horizon,
    )

    hist = data["history"]
    fc = data["forecast"]
    if hist is None or hist.empty or fc is None or fc.empty:
        st.warning("Not enough reported years to work out what producers were paid.")
        return

    units = get_units()
    unit_cost = units.get("cost", "USD bn")
    factor_cost = display_factor("cost", unit_cost)

    # ---- Numbers behind the cards ----
    # The engine already keeps the reported years it could price, from 2000 on.
    last = hist.iloc[-1]
    first_year = int(hist["calendar_year"].iloc[0])
    paid_year = int(last["calendar_year"])
    paid_bill = float(last["cost_total_usd"])
    paid_price = float(last["avg_usd_per_mwh"])
    paid_gen = float(last["gen_total_gwh"])
    paid_fuel = float(last["fuel_cost_share_pct"])

    sc_h = _row_at_year(fc, horizon, active)
    if sc_h is None:
        st.warning("That build-out case has no path for the years asked for.")
        return
    fc_row = sc_h.iloc[0]
    next_bill = float(fc_row["cost_total_usd"])
    next_price = float(fc_row["avg_usd_per_mwh"])
    next_re = float(fc_row["re_share_pct"])
    years_ahead = max(1, horizon - paid_year)
    growth = ((next_bill / paid_bill) ** (1.0 / years_ahead) - 1.0) * 100.0 \
        if paid_bill > 0 else float("nan")

    # ---- Three cards across four slots ----
    # The fourth slot stays blank so each card keeps the width of a four-up row.
    cards = [
        _kpi_card(
            code="K1",
            title=f"What buying electricity cost, {paid_year}",
            value=fmt(paid_bill * factor_cost, 2),
            unit=unit_cost,
            rows=[
                ("Average price paid", f"{paid_price:,.1f} US$ per unit", AMBER),
                ("Electricity bought", f"{fmt(paid_gen, 0)} GWh", LIGHT),
                ("Fuel part of the bill", f"{paid_fuel:.0f}%", RED),
            ],
            accent=AMBER,
            icon_name="cost",
            badge=f"{first_year}–{paid_year}",
            badge_colour=AMBER,
        ),
        _kpi_card(
            code="K2",
            title=f"The bill it points to, {horizon}",
            value=fmt(next_bill * factor_cost, 2),
            unit=unit_cost,
            rows=[
                ("Build-out case", active_word, BLUE),
                ("Grows by", f"{growth:+.1f}% a year", BLUE),
                (f"More than {paid_year}",
                 f"{fmt((next_bill - paid_bill) * factor_cost, 2)} {unit_cost}", LIGHT),
            ],
            accent=BLUE,
            icon_name="scenario",
            badge=f"{horizon} outlook",
            badge_colour=BLUE,
        ),
        _kpi_card(
            code="K3",
            title=f"What one unit costs, {horizon}",
            value=f"{next_price:,.1f}",
            unit="US$ per unit",
            rows=[
                (f"In {paid_year}", f"{paid_price:,.1f} US$ per unit", LIGHT),
                ("Change per unit", f"{next_price - paid_price:+,.1f} US$", CYAN),
                ("Clean share of the mix", f"{next_re:.0f}%", GREEN),
            ],
            accent=CYAN,
            icon_name="renewables",
            badge=active_word,
            badge_colour=CYAN,
        ),
    ]

    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 1 -- what each source was paid, and what a unit cost
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Visual 1 – What producers were paid", "cost",
                      badge=f"{first_year}–{paid_year}"),
        unsafe_allow_html=True)
    st.caption("Yearly bill stacked by the source it bought from. Right: the price of one unit and the fuel part.")
    st.plotly_chart(visual1_cost_so_far(hist, unit_cost, factor_cost),
                    use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 2 -- where the change comes from (full width)
    # ══════════════════════════════════════════════════════════════════════
    steps = []
    for tech in TECHS_SHOWN:
        col = f"cost_{tech.lower().replace(' ', '')}_usd"
        now = float(last[col]) if col in last.index else 0.0
        then = float(fc_row[col]) if col in fc_row.index else 0.0
        steps.append((tech, (then - now) * factor_cost))
    steps.sort(key=lambda step: -step[1])
    bridge_labels = [f"{paid_year} paid"] + [name for name, _ in steps] + [f"{horizon} plan"]
    bridge_measures = ["absolute"] + ["relative"] * len(steps) + ["total"]
    bridge_values = ([paid_bill * factor_cost] + [change for _, change in steps]
                     + [next_bill * factor_cost])

    st.markdown(
        section_title("Visual 2 – Where the extra money goes", "insights",
                      badge=f"{active_word}"),
        unsafe_allow_html=True)
    st.caption(f"One step per source, {paid_year} to {horizon}. Red adds to the bill, green takes away, biggest first.")
    st.plotly_chart(visual3_where_money_goes(bridge_labels, bridge_measures,
                                             bridge_values, unit_cost),
                    use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visuals 3 + 4 -- the price per unit, and the forecast bill
    # ══════════════════════════════════════════════════════════════════════
    price_col, bill_col = st.columns([1, 1.12])

    with price_col:
        st.markdown(
            section_title("Visual 3 – What one unit costs", "data",
                          badge=f"up to {horizon}"),
            unsafe_allow_html=True)
        st.caption("The same bill per unit, so demand growth drops out. A falling line means a cheaper mix.")
        st.plotly_chart(visual4_unit_price(hist, fc, cases, CASE_WORDS),
                        use_container_width=True, config=_CHART_CONFIG)

    with bill_col:
        st.markdown(
            section_title("Visual 4 – The bill from here on", "scenario",
                          badge=f"up to {horizon}"),
            unsafe_allow_html=True)
        st.caption("Pale line: reported years. Dashed lines: the cases ahead, all buying the same electricity from different mixes.")
        st.plotly_chart(visual2_forecast_bill(hist, fc, cases, CASE_WORDS,
                                              unit_cost, factor_cost),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 5 -- the fuel-price band, and how far the model misses
    # ══════════════════════════════════════════════════════════════════════
    rate_lo = DEFAULT_FUEL_INFL - DEFAULT_SPREAD_PP
    rate_hi = DEFAULT_FUEL_INFL + DEFAULT_SPREAD_PP
    fuel_labels = [f"Fuel up {rate_lo:.0f}% a year",
                   f"Fuel up {DEFAULT_FUEL_INFL:.0f}% a year (used here)",
                   f"Fuel up {rate_hi:.0f}% a year"]
    st.markdown(
        section_title("Visual 5 – How sure is this bill?", "imports",
                      badge=f"fuel {rate_lo:.0f}%–{rate_hi:.0f}% a year"),
        unsafe_allow_html=True)
    st.caption(f"Left: the bill with fuel up {rate_lo:.0f}% and up {rate_hi:.0f}% a year instead of {DEFAULT_FUEL_INFL:.0f}%. Right: how wrong each model was on years it never saw.")
    st.plotly_chart(visual5_fuel_and_trust(data["sensitivity"], data["backtest"],
                                           fuel_labels, unit_cost, factor_cost),
                    use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    line1 = (f"The power bill grows from {fmt(paid_bill * factor_cost, 2)} "
             f"{unit_cost} in {paid_year} to about "
             f"{fmt(next_bill * factor_cost, 2)} {unit_cost} by {horizon} in "
             f"the {active_word} case.")
    if steps and steps[0][1] > 0:
        line2 = (f"{steps[0][0]} adds the most to that rise — about "
                 f"{steps[0][1]:,.2f} {unit_cost} more than {paid_year}.")
    else:
        line2 = "No source pushes that bill up — every step takes money off it."
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
