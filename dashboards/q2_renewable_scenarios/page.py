"""
Renewable Energy Scenarios dashboard (Question 2).

Question 2 asks what happens if renewables are installed under different energy
scenarios, so this page keeps only the three ingredients of that answer:

  1. Sidebar    -- which scenario is active, and over which years
  2. KPI strip  -- the scenario's four outcome numbers at the horizon year
  3. Visuals    -- RE share across all 5 scenarios, generation mix,
                   year-by-year / cross-scenario outcomes, capacity by source

Everything is computed from the same projections, and each scenario keeps its
own growth rates so the five stay comparable on one basis.
"""

import streamlit as st
import pandas as pd

from config.database import run_query
from config.settings import SCENARIOS, EMISSION_FACTORS
from core.queries import (
    Q_RENEWABLE_ENERGY,
    Q_RENEWABLE_CAPACITY,
    Q_EMISSION_FACTORS,
)
from core.projections import (
    project_renewable,
    compare_all_scenarios,
    project_renewable_capacity,
)
from core.components import conclusion_card, kpi_card, section_title
from core.units import fmt, from_base
from core.unit_slicer import get_units

from .charts import (
    visual1_re_share_chart,
    visual2_generation_mix_chart,
    visual3_scenario_comparison_chart,
    visual3_yearly_outcomes_chart,
    visual4_renewable_capacity_chart,
)
from .config import KPI_CONFIG, DEFAULT_SCENARIO

FILTERS_KEY = "q2_filters"


def _num(value) -> float:
    """None / NaN safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if out != out else out


def _read(value) -> float:
    """None / NaN safe float that keeps a missing reading missing.

    A card built with this shows "--" for an unreported year instead of the 0.0
    _num would print, because "no reading" and "reading was zero" are two
    different claims.
    """
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if out == out else float("nan")


# Spoken off the t -> kt -> Mt ladder, so a card unit reads as words and not
# as a symbol the reader has to look up.
_MASS_WORDS = {"t": "tonnes of CO\u2082", "kt": "thousand tonnes of CO\u2082",
               "Mt": "million tonnes of CO\u2082"}


def _mass(value_t: float, preferred: str = "t") -> tuple:
    """Convert value_t to formatted mass tuple (display_value, unit_words).

    Keeps the unit the slicer asks for, but climbs the t -> kt -> Mt chain
    while the number would still read as four digits or more, so a large total
    never shows as "258,570 kt".
    """
    v = _num(value_t)
    chain = ["t", "kt", "Mt"]
    i = chain.index(preferred) if preferred in chain else 0
    unit = chain[i]
    disp = from_base(v, unit)
    while abs(disp) >= 1000 and i < len(chain) - 1:
        i += 1
        unit = chain[i]
        disp = from_base(v, unit)
    return disp, _MASS_WORDS[unit]


# --- Sidebar Slicers ---

def _sidebar_filters():
    """Two controls only: which scenario, and which years to look at."""
    st.sidebar.markdown(
        '<div class="dsh-side-title">Scenario &amp; Years</div>',
        unsafe_allow_html=True,
    )

    scenario_keys = list(SCENARIOS.keys())
    selected_scenario = st.sidebar.selectbox(
        "Pick a scenario",
        scenario_keys,
        index=scenario_keys.index(DEFAULT_SCENARIO) if DEFAULT_SCENARIO in scenario_keys else 0,
    )

    year_range = st.sidebar.slider(
        "Years to show",
        min_value=2000,
        max_value=2035,
        value=(2000, 2035),
        step=1,
        help=("Charts show these years. The cards use the last year you pick."),
    )

    # Each scenario brings its own growth rates -- no manual override, so the
    # five stay a like-for-like comparison instead of one tweaked contender.
    sc_conf = SCENARIOS[selected_scenario]
    solar_r = float(sc_conf["solar"])
    wind_r = float(sc_conf["wind"])
    st.sidebar.caption(
        f"Solar and wind grow {solar_r:.0f}% a year."
        if solar_r == wind_r else
        f"Solar grows {solar_r:.0f}% a year, wind {wind_r:.0f}% a year."
    )

    return {
        "scenario": selected_scenario,
        "year_range": year_range,
    }


def sidebar():
    """
    This dashboard's own sidebar slicers (Scenario / Year Range), called by
    app.py BEFORE the global unit slicer so both stay reachable at the top.
    """
    st.session_state[FILTERS_KEY] = _sidebar_filters()
    st.sidebar.divider()


# ================= Compute 4 KPI Values (unit aware) =================
def _compute_kpis(active_proj, cap_ext, years, units):
    """
    Scenario outcome KPIs, evaluated at the FINAL year of the selected range.

    Four cards, one per outcome Question 2 asks about: how much of the grid is
    renewable, how much capacity that took, how much CO2 the scenario avoided
    and what that saved on gas imports. Every card reads the SELECTED
    scenario's projection and the range's last year, so changing the sidebar
    Scenario or Year Range moves them. Values are compared with the last
    reported year (the projection's own base) so the direction of travel is
    visible; when the range
    ends before that, the cards that need a future year say so instead of
    showing a zero.

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
        if not before or pd.isna(now) or pd.isna(before):
            return float("nan")
        return (now - before) / before * 100.0

    # ── horizon row and baseline row of the ACTIVE scenario ──────────────
    r_end = _row(active_proj, target_year)
    r_ref = _row(active_proj, ref_year)

    re_share_end = _read(r_end.get("re_share_pct")) if r_end is not None else float("nan")
    re_share_ref = _read(r_ref.get("re_share_pct")) if r_ref is not None else float("nan")
    delta_share = (re_share_end - re_share_ref
                   if not (pd.isna(re_share_end) or pd.isna(re_share_ref))
                   else float("nan"))

    # ── renewable capacity at the horizon (sum across sources) ───────────
    cap_end = cap_ref = float("nan")
    if cap_ext is not None and not cap_ext.empty:
        cap_end_rows = cap_ext[cap_ext["calendar_year"] == target_year]
        cap_ref_rows = cap_ext[cap_ext["calendar_year"] == ref_year]
        # min_count=1: no rows at all is "nothing reported for that year", not a
        # reported zero capacity.
        cap_end = pd.to_numeric(cap_end_rows["installed_capacity_mw"],
                                errors="coerce").sum(min_count=1)
        cap_ref = pd.to_numeric(cap_ref_rows["installed_capacity_mw"],
                                errors="coerce").sum(min_count=1)
    delta_cap = _pct_delta(cap_end, cap_ref)

    # ── what the scenario avoids, over the projection window ─────────────
    # The cumulative totals count only the years after the last actual, so a
    # scenario is never credited with reductions it did not have to deliver.
    cum_co2_avoid_t = 0.0
    cum_lng = 0.0
    co2_avoid_end_t = 0.0
    lng_end = 0.0
    if active_proj is not None and not active_proj.empty:
        win = active_proj[(active_proj["calendar_year"] > ref_year) &
                          (active_proj["calendar_year"] <= target_year)]
        cum_co2_avoid_t = _num(win["co2_avoided_t"].sum())
        cum_lng = _num(win["lng_savings_musd"].sum())
        co2_avoid_end_t = _num(r_end.get("co2_avoided_t")) if r_end is not None else 0.0
        lng_end = _num(r_end.get("lng_savings_musd")) if r_end is not None else 0.0

    def _fmt_delta(pct, invert=False):
        """Plain-English movement, with green when the change is an improvement."""
        if pct is None or pd.isna(pct):
            return "no reading", "up"
        better = (pct < 0) if not invert else (pct > 0)
        word = "more" if pct >= 0 else "less"
        return f"{abs(pct):.1f}% {word} than {ref_year}", ("down" if better else "up")

    # When the range ends before the last reported year there is no meaningful
    # "vs 2024" comparison: the card is reporting the scenario's pre-baseline
    # state, so say so instead of labelling a backward delta.
    future_of_ref = target_year >= ref_year

    if pd.isna(delta_share):
        d_share_txt = "no reading for this year"
    elif future_of_ref:
        share_word = "more" if delta_share >= 0 else "less"
        d_share_txt = (f"{abs(delta_share):.1f} percentage points "
                       f"{share_word} than {ref_year}")
    else:
        d_share_txt = f"recorded {target_year}"
    if future_of_ref:
        d_cap_txt, t_cap = _fmt_delta(delta_cap, invert=True)
    else:
        d_cap_txt, t_cap = f"recorded {target_year}", "up"

    co2_disp, co2_unit   = _mass(cum_co2_avoid_t, em_u)
    co2_end_disp, co2_end_unit = _mass(co2_avoid_end_t, em_u)

    # The two saving cards can only answer for years that are still ahead. If
    # the range stops at a recorded year there is nothing avoided yet to total,
    # so the card says that instead of showing a confident-looking zero.
    has_forecast = target_year > ref_year
    if has_forecast:
        co2_text = fmt(co2_disp)
    else:
        co2_text, co2_unit = "--", "needs a later end year"

    co2_delta = (f"{target_year} alone: {fmt(co2_end_disp)} {co2_end_unit}"
                 if has_forecast else None)
    lng_delta = (f"{target_year} alone: ${lng_end:,.0f} million"
                 if has_forecast else None)

    return {
        "re_share": {
            "value": "--" if pd.isna(re_share_end) else f"{re_share_end:.1f}%",
            "unit": "",
            "delta": d_share_txt,
            "delta_type": ("up" if pd.isna(delta_share)
                            else ("up" if delta_share >= 0 else "down")),
        },
        "re_capacity": {
            "value": fmt(from_base(cap_end, p_u)),
            "unit": p_u,
            "delta": d_cap_txt,
            "delta_type": t_cap,
        },
        "co2_avoided": {
            "value": co2_text,
            "unit": co2_unit,
            "delta": co2_delta,
            "delta_type": "down" if co2_avoid_end_t else "up",
        },
        "lng_savings": {
            "value": f"${cum_lng:,.0f}" if has_forecast else "--",
            "unit": "million USD" if has_forecast else "needs a later end year",
            "delta": lng_delta,
            "delta_type": "down" if lng_end else "up",
        },
    }


# --- Main Dashboard Render ---
def render():
    units = get_units()
    filters = st.session_state.get(FILTERS_KEY) or _sidebar_filters()

    # Load data -- only the three queries this page actually reads
    re_df = run_query(Q_RENEWABLE_ENERGY)
    cap_df = run_query(Q_RENEWABLE_CAPACITY)
    ef_df = run_query(Q_EMISSION_FACTORS)

    e_u = units["electricity"]

    # Emission factors (tCO2/MWh)
    ef_map = dict(EMISSION_FACTORS)
    if not ef_df.empty:
        for _, row in ef_df.iterrows():
            f_type = str(row.get("fuel_type", "")).strip().lower()
            factor = _num(row.get("emission_factor_tco2_mwh"))
            if f_type in ef_map and factor > 0:
                ef_map[f_type] = factor

    horizon_year = 2035
    view_year = int(filters["year_range"][1])
    filters["target_year"] = view_year

    # Project all five scenarios straight from their own declared rates -- with
    # no manual override, nothing tilts one scenario in favour of another.
    all_scenarios_proj = {
        sc_name: project_renewable(
            re_df,
            scenario=sc_name,
            end_year=horizon_year,
            emission_factors=ef_map,
        )
        for sc_name in SCENARIOS
    }

    active_proj = all_scenarios_proj[filters["scenario"]]
    comparison_df = compare_all_scenarios(
        re_df,
        target_year=view_year,
        emission_factors=ef_map,
    )

    # Capacity build-out, shared by the KPI strip and Visual 4
    cap_ext = project_renewable_capacity(
        cap_df,
        scenario=filters["scenario"],
        end_year=filters["target_year"],
    )

    # --- Top Row: 4 outcome KPI Cards ---
    # The shared .kpi-card sizes to its own content, so a card whose title
    # wraps to two lines ("Renewable Power Built (2035)") ends lower than one
    # that fits a line ("Renewable Share (2035)"). Balance comes from reserving
    # the variable element -- the title gets the same two lines the delta block
    # already reserves (min-height:30px) -- so every card shares one natural
    # height and one bottom baseline. height/flex still let a card fill its
    # column when the row stretches, which never hurts.
    st.markdown(
        "<style>.kpi-card{height:100% !important;min-height:0 !important;"
        "flex:1 1 auto !important;}"
        ".kpi-card .kpi-title{min-height:28px;}</style>",
        unsafe_allow_html=True,
    )
    actual_years = active_proj[active_proj["data_type"] == "Actual"]["calendar_year"]
    last_actual = int(actual_years.max()) if len(actual_years) else filters["year_range"][0]
    ref_year = int(min(max(last_actual, filters["year_range"][0]),
                       filters["year_range"][1]))
    kpi_cols = st.columns(len(KPI_CONFIG))
    kpi_data = _compute_kpis(
        active_proj, cap_ext, (ref_year, filters["target_year"]), units,
    )

    for col, cfg in zip(kpi_cols, KPI_CONFIG):
        k_info = kpi_data[cfg["key"]]
        # The unit computed with the value wins, so a card tracks the unit
        # slicer instead of wearing a fixed label; KPI_CONFIG only backstops it.
        unit_label = k_info["unit"] or cfg["unit"]
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

    # --- Row 1: Visual 1 & Visual 2 ---
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown(section_title("Visual 1 – Renewable Share Over Time", "scenario", badge="History + Forecast"), unsafe_allow_html=True)
        st.caption("How much of our power comes from renewables. Solid line is what was recorded, dashed lines are what could happen next.")
        fig1 = visual1_re_share_chart(all_scenarios_proj, filters["scenario"], filters["year_range"], units)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown(section_title("Visual 2 – Where the Power Comes From", "generation", badge=f"{filters['scenario']} · {e_u}"), unsafe_allow_html=True)
        st.caption(f"Power from each source every year ({e_u}) under the chosen scenario: solar, wind, hydro, nuclear, gas and coal.")
        fig2 = visual2_generation_mix_chart(active_proj, filters["year_range"], units)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --- Row 2: the outcomes, then the build-out behind them ---
    view_col, _spacer = st.columns([1.05, 1])
    with view_col:
        view = st.radio(
            "Visual 3 – see the results two ways",
            ["One year at a time", "All five scenarios"],
            horizontal=True,
            key="outcome_view",
        )

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        if view == "One year at a time":
            v3_title = "Visual 3 – Results, One Year at a Time"
            v3_badge = f"{filters['scenario']} · up to {filters['target_year']}"
            v3_caption = f"Each year: how much fossil power renewables replace, how much CO₂ is kept out of the air, and what that saves on gas imports."
            fig3 = visual3_yearly_outcomes_chart(active_proj, filters["year_range"], units)
        else:
            v3_title = "Visual 3 – All Five Scenarios Compared"
            v3_badge = f"Year {filters['target_year']}"
            v3_caption = f"The five paths side by side in {filters['target_year']}: renewable share, fossil power replaced and CO₂ avoided in a single year."
            fig3 = visual3_scenario_comparison_chart(
                comparison_df, target_year=filters["target_year"], units=units)

        st.markdown(section_title(v3_title, "chart", badge=v3_badge), unsafe_allow_html=True)
        st.caption(v3_caption)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown(section_title("Visual 4 – Renewable Power Plants Built", "renewables", badge=f"By source · {units['power']} · up to {filters['target_year']}"), unsafe_allow_html=True)
        st.caption(f"Total renewable plant capacity ({units['power']}) split by source. This is the build-out the chosen scenario needs.")
        fig4 = visual4_renewable_capacity_chart(cap_ext, filters["year_range"], units)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # ---- Bottom line ----
    co2_v = kpi_data["co2_avoided"]["value"]
    line1 = (f"Under the {filters['scenario']} case, renewables reach "
             f"{kpi_data['re_share']['value']} of power supply by "
             f"{filters['target_year']}.")
    if co2_v != "--":
        line2 = (f"On the way they keep {co2_v} "
                 f"{kpi_data['co2_avoided']['unit']} out of the air and cut "
                 f"{kpi_data['lng_savings']['value']} "
                 f"{kpi_data['lng_savings']['unit']} off the fuel-import bill.")
    else:
        line2 = (f"Pick an end year after {ref_year} to see the CO\u2082 avoided "
                 "and the import savings.")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
