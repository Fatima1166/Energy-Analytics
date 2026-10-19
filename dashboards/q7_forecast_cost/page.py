"""
Forecasted Cost of Energy Power Producers dashboard (Question 7).

Presentation layer only -- every number rendered here is produced by the
pure analysis engine in core/cost_forecast.py.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
from core.cost_forecast import (
    COST_SCENARIO_ORDER,
    COST_TECHS,
    DEFAULT_BASE_GDP_GROWTH,
    DEFAULT_CALIB_START,
    DEFAULT_FUEL_INFL,
    DEFAULT_SPREAD_PP,
    HISTORY_END,
    HORIZON,
    build_cost_dashboard_data,
    unit_cost_table,
)
from core.icons import icon
from core.queries import Q_ECONOMIC, Q_ELEC_GEN, Q_LNG, Q_RENEWABLE_ENERGY
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_historical_cost_bill,
    visual2_sensitivity_backtest,
    visual3a_avoided_cost,
    visual3b_learning_curves,
    visual4_price_heatmap,
    visual5_scenario_fan,
    visual6_cost_bridge,
)

FILTERS_KEY = "q7_filters"
_CHART_CONFIG = {"displayModeBar": False}

# Compact override for the shared .kpi-balance skin: Q7 cards size to their
# content (auto height, flex-start, no bottom pinning) so no empty space is
# distributed between value and detail rows.
_COMPACT_CSS = """
<style>
.kpi-balance.kpi-compact {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    justify-content: flex-start !important;
    padding: 11px 14px 10px !important;
}
.kpi-balance.kpi-compact .kpi-balance-details {
    margin-top: 6px !important;
    padding-top: 6px !important;
}
</style>
"""


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Producer Cost Forecast Setup</div>',
                        unsafe_allow_html=True)

    scenarios = st.sidebar.multiselect(
        "Deployment scenarios", COST_SCENARIO_ORDER,
        default=list(COST_SCENARIO_ORDER), key="q7_scenarios",
        help=("Which build-out cases to price: Minimum RE (thermal-heavy), "
              "Reference (IGCEP-style) or RE 50% (aggressive renewables)."),
    )
    if not scenarios:
        scenarios = ["Reference"]

    horizon = st.sidebar.slider(
        "Forecast horizon", min_value=2026, max_value=2035, value=HORIZON,
        step=1, key="q7_horizon",
        help="Target year for the producer cost outlook.",
    )

    fuel_infl = st.sidebar.slider(
        "Fuel price escalation %/yr", min_value=0.0, max_value=8.0,
        value=DEFAULT_FUEL_INFL, step=0.25, key="q7_fuel_infl",
        help=("Annual drift of coal and gas purchase tariffs, passed through "
              "from imported fuel prices."),
    )

    spread = st.sidebar.slider(
        "Sensitivity band ±pp", min_value=0.5, max_value=4.0,
        value=DEFAULT_SPREAD_PP, step=0.5, key="q7_spread",
        help="Fuel-escalation rates tested above and below the base assumption.",
    )

    with st.sidebar.expander("Advanced Model Settings", expanded=False):
        calib_start = st.slider(
            "Calibration start", min_value=2002, max_value=2020,
            value=DEFAULT_CALIB_START, step=1, key="q7_calib",
            help="Elasticities and trends are fitted from this year to 2024.",
        )

        base_gdp = st.slider(
            "Base GDP growth %", min_value=1.0, max_value=8.0,
            value=DEFAULT_BASE_GDP_GROWTH, step=0.1, key="q7_gdp",
            help="Real GDP growth driving the shared generation path.",
        )

    st.session_state[FILTERS_KEY] = {
        "scenarios": list(scenarios),
        "horizon": int(horizon),
        "fuel_infl_pct": float(fuel_infl),
        "spread_pp": float(spread),
        "calib_start": int(calib_start),
        "base_gdp_growth": float(base_gdp),
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#F59E0B", icon_name: str = "cost",
              badge: str = "", badge_colour: str = "#F59E0B") -> str:
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
<div class="kpi-balance kpi-compact" style="border: 1px solid {accent}44;">
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
              margin-bottom:4px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;">
    <span style="color:{accent};font-size:23px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details">{detail}</div>
</div>
"""


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Forecasted Power Producer Cost dashboard."""
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
    flt = st.session_state.get(FILTERS_KEY, {})
    scenarios = flt.get("scenarios", list(COST_SCENARIO_ORDER))
    horizon = flt.get("horizon", HORIZON)
    fuel_infl = flt.get("fuel_infl_pct", DEFAULT_FUEL_INFL)
    spread = flt.get("spread_pp", DEFAULT_SPREAD_PP)
    calib_start = flt.get("calib_start", DEFAULT_CALIB_START)
    base_gdp = flt.get("base_gdp_growth", DEFAULT_BASE_GDP_GROWTH)
    active_sc = "Reference" if "Reference" in scenarios else scenarios[0]

    # Fetch raw reported frames
    re_df = run_query(Q_RENEWABLE_ENERGY)
    ec_df = run_query(Q_ECONOMIC)
    gen_df = run_query(Q_ELEC_GEN)
    lng_df = run_query(Q_LNG)

    data = build_cost_dashboard_data(
        re_df=re_df,
        econ_df=ec_df,
        gen_df=gen_df,
        lng_df=lng_df,
        scenarios=scenarios,
        calib_start=calib_start,
        horizon=horizon,
        base_gdp_growth=base_gdp,
        fuel_infl_pct=fuel_infl,
        sensitivity_spread_pp=spread,
    )

    hist = data["history"]
    fc = data["forecast"]
    if hist.empty or fc.empty:
        st.warning("Not enough reported data to build the producer cost model.")
        return

    # Display units (cost domain: USD bn / mn / USD)
    units = get_units()
    unit_cost = units.get("cost", "USD bn")
    factor_cost = display_factor("cost", unit_cost)

    # ---- KPI inputs ----
    last = hist.iloc[-1]
    cost_2024 = float(last["cost_total_usd"])
    avg_2024 = float(last["avg_usd_per_mwh"])
    gen_2024 = float(last["gen_total_gwh"])
    fuel_share_2024 = float(last["fuel_cost_share_pct"])

    sc_h = fc[(fc["scenario"] == active_sc) & (fc["calendar_year"] == horizon)]
    if sc_h.empty:
        sc_h = fc[fc["scenario"] == active_sc].iloc[[-1]]
    cost_h = float(sc_h.iloc[0]["cost_total_usd"])
    avg_h = float(sc_h.iloc[0]["avg_usd_per_mwh"])
    re_share_h = float(sc_h.iloc[0]["re_share_pct"])
    fuel_share_h = float(sc_h.iloc[0]["fuel_cost_share_pct"])
    span = max(1, horizon - HISTORY_END)
    cost_cagr = ((cost_h / cost_2024) ** (1.0 / span) - 1.0) * 100.0 if cost_2024 > 0 else float("nan")

    avoided = data["avoided"]
    cum_avoided = 0.0
    delta_h = 0.0
    if avoided is not None and not avoided.empty:
        av_h = avoided[avoided["calendar_year"] == horizon]
        if av_h.empty:
            av_h = avoided.iloc[[-1]]
        cum_avoided = float(av_h.iloc[0]["cumulative_usd"])
        delta_h = float(av_h.iloc[0]["delta_usd"])

    sens = data["sensitivity"]
    exposure_hi, exposure_lo = float("nan"), float("nan")
    if sens is not None and not sens.empty:
        cost_cols = [c for c in sens.columns if c != "calendar_year"]
        sr = sens[sens["calendar_year"] == horizon]
        if sr.empty:
            sr = sens.iloc[[-1]]
        vals = sr[cost_cols].values[0].astype(float) * factor_cost
        exposure_lo, exposure_hi = float(min(vals)), float(max(vals))

    # ---- KPI strip ----
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        st.markdown(
            _kpi_card(
                code="K1",
                title=f"Reported Producer Cost Bill ({HISTORY_END})",
                value=fmt(cost_2024 * factor_cost, 2),
                unit=unit_cost,
                rows=[
                    ("Blended Buying Price", f"{avg_2024:,.1f} US$/MWh", "#F59E0B"),
                    ("Generation Bought", f"{fmt(gen_2024, 0)} GWh", "#CBD5E1"),
                    ("Fuel-Cost Share", f"{fuel_share_2024:.1f}% of bill", "#EF4444"),
                ],
                accent="#F59E0B",
                icon_name="cost",
                badge="Reported",
                badge_colour="#F59E0B",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        st.markdown(
            _kpi_card(
                code="K2",
                title=f"Projected Cost Bill ({active_sc}, {horizon})",
                value=fmt(cost_h * factor_cost, 2),
                unit=unit_cost,
                rows=[
                    ("Implied CAGR", f"{cost_cagr:+.2f}%/yr", "#00A6FB"),
                    ("vs Reported 2024", f"+{fmt((cost_h - cost_2024) * factor_cost, 2)} {unit_cost}", "#CBD5E1"),
                    ("Fuel Escalation", f"{fuel_infl:.2f}%/yr", "#94A3B8"),
                ],
                accent="#00A6FB",
                icon_name="scenario",
                badge=f"{cost_cagr:+.1f}% p.a.",
                badge_colour="#00A6FB",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[2]:
        st.markdown(
            _kpi_card(
                code="K3",
                title=f"Blended Purchase Price ({horizon})",
                value=f"{avg_h:,.1f}",
                unit="US$/MWh",
                rows=[
                    (f"Reported {HISTORY_END}", f"{avg_2024:,.1f} US$/MWh", "#CBD5E1"),
                    ("RE Share of Gen", f"{re_share_h:.1f}%", "#10B981"),
                    ("Fuel-Cost Share", f"{fuel_share_h:.1f}% of bill", "#EF4444"),
                ],
                accent="#22D3EE",
                icon_name="renewables",
                badge=f"{avg_h - avg_2024:+.1f} US$/MWh",
                badge_colour="#22D3EE",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[3]:
        st.markdown(
            _kpi_card(
                code="K4",
                title=f"Cumulative Cost Avoided ({horizon})",
                value=fmt(cum_avoided * factor_cost, 2),
                unit=unit_cost,
                rows=[
                    ("RE 50% vs Minimum RE", f"by {horizon}", "#10B981"),
                    ("Annual Saving", f"{fmt(delta_h * factor_cost, 2)} {unit_cost}", "#22D3EE"),
                    ("Fuel Exposure Range", f"{fmt(exposure_lo, 1)} – {fmt(exposure_hi, 1)}", "#F59E0B"),
                ],
                accent="#10B981",
                icon_name="sustainability",
                badge="RE 50% pathway",
                badge_colour="#10B981",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ---- V1: Historical producer cost bill ----
    st.markdown(section_title(f"Cost Purchased from Power Producers — History (2002–{HISTORY_END})",
                              "cost", "Objective 1"), unsafe_allow_html=True)
    st.caption(f"Reported generation by technology priced at implied per-MWh purchase tariffs; "
               f"the right panel tracks the blended buying price and the fuel-driven share of the bill ({unit_cost}).")
    fig1 = visual1_historical_cost_bill(hist=hist, unit_cost=unit_cost, factor_cost=factor_cost)
    st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    # ---- V2: Fuel exposure, sensitivity & reliability (full width, table below) ----
    st.markdown(section_title("Fuel Price Exposure, Sensitivity & Forecast Reliability",
                              "imports", "Objective 2"), unsafe_allow_html=True)
    st.caption(f"Left: Reference cost bill under fuel escalation of {fuel_infl - spread:.2f}% / "
               f"{fuel_infl:.2f}% / {fuel_infl + spread:.2f}% per year. Right: hold-out backtest "
               f"(trained ≤ 2020, tested 2021–{HISTORY_END}) of the GDP-driver and trend cost models.")
    fig2 = visual2_sensitivity_backtest(sensitivity=sens, backtest=data["backtest"],
                                        unit_cost=unit_cost, factor_cost=factor_cost)
    st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    st.markdown("<div style='font-size:12px;font-weight:700;color:#CBD5E1;margin:8px 0 8px;'>Cost-Model Hold-Out Performance (2021–2024)</div>", unsafe_allow_html=True)
    bt_table = (data["backtest"] or {}).get("table", pd.DataFrame())
    if bt_table is not None and not bt_table.empty:
        disp = pd.DataFrame({
            "Model": bt_table["model"],
            "MAPE %": bt_table["mape_pct"].map(lambda x: f"{x:.2f}%"),
            "Bias %": bt_table["bias_pct"].map(lambda x: f"{x:+.1f}%"),
            "Result": bt_table["is_winner"].map(lambda x: "◀ Lower Error" if x else ""),
        })
        st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("Insufficient data for hold-out comparison.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ---- V3: Cost avoided + learning curves, side by side ----
    row3_c1, row3_c2 = st.columns(2)

    with row3_c1:
        st.markdown(section_title("Cumulative Cost Avoided (RE 50% vs Minimum RE)",
                                  "sustainability", "Objective 3"), unsafe_allow_html=True)
        st.caption("Annual producer-cost saved by the aggressive renewable pathway and its running total.")
        fig3a = visual3a_avoided_cost(avoided=avoided, unit_cost=unit_cost, factor_cost=factor_cost)
        st.plotly_chart(fig3a, use_container_width=True, config=_CHART_CONFIG)

    with row3_c2:
        st.markdown(section_title("Blended Price Learning Curves",
                                  "scenario", "Objective 3"), unsafe_allow_html=True)
        st.caption("Weighted average purchase price (US$/MWh): renewables learn downwards while "
                   "thermal tariffs drift with imported fuel escalation.")
        fig3b = visual3b_learning_curves(hist=hist, fc=fc, scenarios=scenarios)
        st.plotly_chart(fig3b, use_container_width=True, config=_CHART_CONFIG)

    # ---- V4: Implied purchase-tariff heat-map ----
    st.markdown(section_title("Implied Purchase-Tariff Heat-Map — Technology vs Year",
                              "data", "Objective 4"), unsafe_allow_html=True)
    st.caption("US$/MWh paid to producers across the full timeline: solar and wind learning "
               "curves cool down, while coal and gas tariffs heat up with the fuel-price "
               "escalation assumption driving the contract drift.")
    ucost_table = unit_cost_table(range(2002, horizon + 1), fuel_infl)
    fig4 = visual4_price_heatmap(ucost_table=ucost_table)
    st.plotly_chart(fig4, use_container_width=True, config=_CHART_CONFIG)

    # ---- V5 + V6: deployment-case fan and cost bridge, one analytical row ----
    # Bridge steps: what each technology adds to (or shaves off) the bill between
    # the reported 2024 level and the modelled horizon under the active case.
    steps = []
    for tech in COST_TECHS:
        col = f"cost_{tech.lower().replace(' ', '')}_usd"
        v24 = float(last[col]) if col in last.index else 0.0
        vh = float(sc_h.iloc[0][col]) if col in sc_h.columns else 0.0
        steps.append((tech, (vh - v24) * factor_cost))
    steps.sort(key=lambda s: -s[1])  # growth drivers first, then savings
    bridge_labels = [f"Reported {HISTORY_END}"] + [t for t, _ in steps] + [f"{active_sc} {horizon}"]
    bridge_measures = ["absolute"] + ["relative"] * len(steps) + ["total"]
    bridge_values = ([cost_2024 * factor_cost]
                     + [d for _, d in steps]
                     + [cost_h * factor_cost])

    row5_c1, row5_c2 = st.columns([1.08, 1])

    with row5_c1:
        st.markdown(section_title(f"Forecasted Producer Cost by Deployment Case (2025–{horizon})",
                                  "overview", "Objective 5"), unsafe_allow_html=True)
        st.caption("The same generation requirement priced under three deployment pathways — "
                   "the shaded envelope spans Minimum RE (thermal-heavy) to RE 50%.")
        fig5 = visual5_scenario_fan(hist=hist, fc=fc, scenarios=scenarios,
                                    unit_cost=unit_cost, factor_cost=factor_cost)
        st.plotly_chart(fig5, use_container_width=True, config=_CHART_CONFIG)

    with row5_c2:
        st.markdown(section_title(f"Cost Bridge — {HISTORY_END} to {horizon} ({active_sc})",
                                  "insights", "Objective 5"), unsafe_allow_html=True)
        st.caption("Technology-by-technology walk from the reported bill to the modelled one: "
                   "red bars grow the cheque, green bars claw it back through learning curves.")
        fig6 = visual6_cost_bridge(labels=bridge_labels, measures=bridge_measures,
                                   values=bridge_values, unit_cost=unit_cost)
        st.plotly_chart(fig6, use_container_width=True, config=_CHART_CONFIG)
