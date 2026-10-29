"""
Sustainable Energy Strategy dashboard (Question 8).

"What optimal strategy may be opted to make energy development sustainable?"

Presentation only.  The pillar scores, the value-for-money ranking, the chosen
package and the three projected paths are all computed in
core/sustainability_engine.py -- this file reads them and draws them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.icons import icon
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_LNG,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.sustainability_engine import (
    PILLARS,
    apply_weights,
    budget_score_curve,
    build_indicator_frame,
    build_verdict,
    history_pair,
    latest_pillar_scores,
    pillar_last_seen,
    project_pathways,
    select_optimal_package,
    snapshot_row,
    strategy_value_density,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_pillar_scorecard,
    visual2_value_ranking,
    visual3_measure_heatmap,
    visual4_pillar_gain,
    visual5_budget_curve,
)
from .config import (
    AMBER,
    BLUE,
    BUDGET_RANGE,
    DEFAULT_BUDGET_BN,
    DEFAULT_EVAL_YEAR,
    DEFAULT_HORIZON,
    GREEN,
    HORIZON_RANGE,
    PILLAR_WORDS,
    PRESET_ORDER,
    RED,
    STRATEGY_LIBRARY,
    TEAL,
    preset_weights,
)

FILTERS_KEY = "q8_filters"
_CHART_CONFIG = {"displayModeBar": False}

_MUTED = "#94A3B8"
_TEXT = "#CBD5E1"

# Cards are sized by their own content.  The shared skin pins a fixed height and
# pushes the footer rows to the bottom, which leaves a dead band under the number
# whenever a card has fewer rows than the tallest one in the row.
_CARD_CSS = """
<style>
  .kpi-balance.q8-kpi {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      justify-content: flex-start !important;
      padding: 13px 14px 12px !important;
  }
  .kpi-balance.q8-kpi .kpi-balance-details { margin-top: 0 !important; }
</style>
"""


def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = TEAL, icon_name: str = "sustainability",
              badge: str = "", badge_colour: str = TEAL) -> str:
    """Compact dark card, one line of detail per row."""
    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:9px;color:{_MUTED};padding:1px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (f'<span style="background:{badge_colour}22;color:{badge_colour};'
                  f'font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;'
                  f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
                  if badge else "")
    return f"""
<div class="kpi-balance q8-kpi" style="border: 1px solid {accent}44;">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:30px;height:30px;background:{accent}22;border:1px solid {accent}44;
                  border-radius:8px;display:flex;align-items:center;justify-content:center;
                  color:{accent};font-size:12px;">{icon(icon_name)}</div>
      <div style="color:{_MUTED};font-size:9.5px;font-weight:700;text-transform:uppercase;
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


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer.

    Three knobs only: what the plan should favour, the yearly money, and how far
    ahead to look.  Pillar weights come from the pick, and the caption spells the
    four numbers out so nothing is hidden behind a label.
    """
    st.sidebar.markdown('<div class="dsh-side-title">Sustainable Strategy</div>',
                        unsafe_allow_html=True)

    preset = st.sidebar.selectbox("What counts most", PRESET_ORDER, index=0,
                                  key="q8_preset")

    budget = st.sidebar.slider("Money a year for new measures", *BUDGET_RANGE,
                               DEFAULT_BUDGET_BN, 0.5, key="q8_budget",
                               help="Yearly USD bn the plan may commit.  Options are "
                                    "paid for best-value-first until this runs out.")
    horizon = st.sidebar.slider("Plan up to", *HORIZON_RANGE, DEFAULT_HORIZON,
                                key="q8_horizon")

    st.session_state[FILTERS_KEY] = {
        "preset": preset,
        "weights": preset_weights(preset),
        "budget_bn": float(budget),
        "horizon": int(horizon),
        "eval_year": int(DEFAULT_EVAL_YEAR),
    }
    st.sidebar.divider()


# --- Small readers ---

def _ordered_pillars(pillars_now: dict) -> tuple:
    """(lowest, highest) as (label, score, key) triples, or (None, None)."""
    items = [(PILLAR_WORDS.get(p, p), v, p) for p, v in pillars_now.items()
             if v is not None and np.isfinite(v)]
    if not items:
        return None, None
    items.sort(key=lambda t: t[1])
    return items[0], items[-1]


_USD_PER_BN = 1e9  # the engine holds yearly money in constant USD billions


def _money(value_bn: float, factor_cost: float, decimals: int = 2) -> str:
    """One engine amount in the unit the slicer asks for."""
    return fmt(float(value_bn) * _USD_PER_BN * factor_cost, decimals)


def _measures_behind(ind_w: pd.DataFrame, pillar: str, year: int) -> int:
    """How many reported numbers made up this pillar's score in `year`."""
    col = f"{pillar}_n_components"
    if col not in ind_w.columns:
        return 0
    hit = ind_w[ind_w["calendar_year"] == year]
    if hit.empty:
        return 0
    val = hit.iloc[0].get(col)
    return int(val) if pd.notna(val) else 0


def _build_scorecard(ind_w: pd.DataFrame, base_year: int) -> pd.DataFrame:
    seen = pillar_last_seen(ind_w, base_year)
    rows = []
    for p in PILLARS:
        now, then, then_year = history_pair(ind_w, f"score_{p}", base_year, back=10)
        if not (np.isfinite(now) and np.isfinite(then)):
            continue
        rows.append({
            "pillar_key": p,
            "pillar": PILLAR_WORDS.get(p, p),
            "now": now, "then": then, "delta": now - then,
            "year": seen.get(p, base_year),
            "n_measures": _measures_behind(ind_w, p, seen.get(p, base_year)),
            "then_year": then_year,
            "now_label": "Latest reported",
            "then_label": "Ten years earlier",
        })
    return pd.DataFrame(rows)


def _build_gain(pathways: pd.DataFrame, verdict: dict, horizon: int) -> pd.DataFrame:
    gains = verdict.get("pillar_gain_vs_bau", {})
    hor = pathways[pathways["calendar_year"] == horizon]
    if hor.empty:
        return pd.DataFrame()
    hor = hor.iloc[0]
    rows = []
    for p in PILLARS:
        bau = float(hor[f"{p}_bau"])
        opt = float(hor[f"{p}_optimal"])
        note = ""
        if bau >= 99.5 and opt >= 99.5:
            note = "Already at the top of the scale, so it cannot show a gain"
        elif opt >= 99.5:
            note = "Reaches the top of the scale"
        rows.append({"pillar": PILLAR_WORDS.get(p, p), "pillar_key": p,
                     "gain": gains.get(p, np.nan), "bau": bau, "optimal": opt,
                     "capped": note or "—"})
    return pd.DataFrame(rows)


# --- Main dashboard render ---

def render() -> None:
    """Renders the Sustainable Strategy dashboard (Question 8)."""
    flt = st.session_state.get(FILTERS_KEY, {})
    weights = flt.get("weights", preset_weights(PRESET_ORDER[0]))
    budget = flt.get("budget_bn", DEFAULT_BUDGET_BN)
    horizon = flt.get("horizon", DEFAULT_HORIZON)
    base_year = flt.get("eval_year", DEFAULT_EVAL_YEAR)
    preset = flt.get("preset", PRESET_ORDER[0])

    ind = build_indicator_frame(
        re_df=run_query(Q_RENEWABLE_ENERGY),
        gen_df=run_query(Q_ELEC_GEN),
        td_df=run_query(Q_TD_LOSSES),
        ps_df=run_query(Q_PRIMARY_SUPPLY),
        gas_df=run_query(Q_NATURAL_GAS),
        lng_df=run_query(Q_LNG),
        econ_df=run_query(Q_ECONOMIC),
    )
    if ind is None or ind.empty:
        st.warning("The warehouse did not return enough years to score the pillars.")
        return

    ind_w = apply_weights(ind, weights)
    if ind_w["score_weighted"].dropna().empty:
        st.warning("A pillar is missing, so no overall score could be made.")
        return

    ranked = strategy_value_density(STRATEGY_LIBRARY, weights)
    package = select_optimal_package(STRATEGY_LIBRARY, weights, budget)
    pathways = project_pathways(ind_w, weights, package, base_year, horizon,
                                STRATEGY_LIBRARY)
    verdict = build_verdict(ind_w, weights, package, pathways, base_year, horizon)
    if not verdict:
        st.warning("No path could be projected to that year.")
        return

    units = get_units()
    unit_cost = units.get("cost", "USD bn")
    factor_cost = display_factor("cost", unit_cost)

    pillars_now = latest_pillar_scores(ind_w, base_year)
    seen = pillar_last_seen(ind_w, base_year)
    reported = sum(1 for p in PILLARS if seen.get(p) == base_year)
    # The number a card prints must belong to the year the card names, so the
    # label comes off the row the engine actually read, not off the slider.
    base_row = snapshot_row(ind_w, base_year)
    score_year = int(base_row["calendar_year"]) if pd.notna(base_row.get("calendar_year")) else base_year
    low, high = _ordered_pillars(pillars_now)
    funded = package["chosen"]
    deferred = package["skipped"]

    # ---- Three cards across four slots ----
    # The fourth slot stays empty so each card keeps a four-up row's width.
    cards = [
        _kpi_card(
            code="K1",
            title=f"Where things stand, {score_year}",
            value=(f"{verdict['index_now']:.1f}"
                   if np.isfinite(verdict["index_now"]) else "--"),
            unit="/ 100",
            rows=[
                ("Lowest pillar",
                 f"{low[0]} {low[1]:.0f} ({seen.get(low[2])})" if low else "--", RED),
                ("Highest pillar",
                 f"{high[0]} {high[1]:.0f} ({seen.get(high[2])})" if high else "--",
                 BLUE),
                (f"Pillars reporting in {base_year}",
                 f"{reported} of {len(PILLARS)} pillars", AMBER),
            ],
            accent=TEAL, icon_name="sustainability",
            badge=f"{score_year} score", badge_colour=TEAL,
        ),
        _kpi_card(
            code="K2",
            title=f"What the plan reaches by {horizon}",
            value=(f"{verdict['index_optimal']:.1f}"
                   if np.isfinite(verdict["index_optimal"]) else "--"),
            unit="/ 100",
            rows=[
                ("If nothing changes", f"{verdict['index_bau']:.1f}", RED),
                ("Better than that", f"{verdict['gap_vs_bau']:+.1f} points", GREEN),
                ("Measures paid for", f"{len(funded)} of {len(STRATEGY_LIBRARY)}",
                 _TEXT),
            ],
            accent=GREEN, icon_name="route",
            badge=f"{horizon} outlook", badge_colour=GREEN,
        ),
        _kpi_card(
            code="K3",
            title="What the plan costs a year",
            value=_money(package["committed_bn"], factor_cost),
            unit=f"{unit_cost} / year",
            rows=[
                ("Asked for", f"{_money(budget, factor_cost)} {unit_cost}", BLUE),
                ("Left over",
                 f"{_money(package['unallocated_bn'], factor_cost)} {unit_cost}",
                 AMBER if package["unallocated_bn"] > 0.05 else GREEN),
                ("Put off for want of it", f"{len(deferred)} measures", _MUTED),
            ],
            accent=BLUE, icon_name="cost",
            badge=preset.split(" counts")[0], badge_colour=BLUE,
        ),
    ]

    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 1 -- where each pillar stands      Visual 2 -- what each option buys
    # ══════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(section_title("Visual 1 – Where each pillar stands",
                                  "sustainability", badge=f"to {base_year}"),
                    unsafe_allow_html=True)
        st.caption("Latest score per pillar against ten years earlier. The label "
                   "shows the year it came from and how many measures back it.")
        st.plotly_chart(visual1_pillar_scorecard(_build_scorecard(ind_w, base_year)),
                        use_container_width=True, config=_CHART_CONFIG)
    with c2:
        st.markdown(section_title("Visual 2 – What each option buys per dollar",
                                  "insights",
                                  badge=f"{_money(budget, factor_cost)} {unit_cost} / yr"),
                    unsafe_allow_html=True)
        st.caption("Best value on top. Green is paid for at this budget, grey is "
                   "put off until the budget grows.")
        st.plotly_chart(visual2_value_ranking(
            ranked, {c["id"] for c in funded}, unit_cost, factor_cost),
            use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 3 -- the measures behind each pillar      Visual 4 -- what the plan changes
    # ══════════════════════════════════════════════════════════════════════
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(section_title("Visual 3 – The measures behind each pillar",
                                  "overview", badge="latest reported year"),
                    unsafe_allow_html=True)
        st.caption("Each cell is one measure's score out of 100 in its pillar's "
                   "latest reported year.  Low cells are what hold the pillar down.")
        st.plotly_chart(visual3_measure_heatmap(ind_w, pillars_now, seen),
                        use_container_width=True, config=_CHART_CONFIG)
    with c4:
        st.markdown(section_title("Visual 4 – What the plan changes by "
                                  f"{horizon}", "up",
                                  badge=f"{len(funded)} measures"),
                    unsafe_allow_html=True)
        st.caption("Points each pillar gains because of the plan, against the "
                   "same pillar if nothing changes.")
        st.plotly_chart(visual4_pillar_gain(_build_gain(pathways, verdict, horizon),
                                            horizon),
                        use_container_width=True, config=_CHART_CONFIG)

    # ════════════════════════════════════════════════════════════════════
    # Visual 5 -- how much the next bn of spend actually buys
    # ════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    c5, _ = st.columns([1.6, 1])
    with c5:
        st.markdown(section_title("Visual 5 – Where the money stops helping",
                                  "overview",
                                  badge=f"{BUDGET_RANGE[0]:.0f}–{BUDGET_RANGE[1]:.0f} bn sweep"),
                    unsafe_allow_html=True)
        st.caption("For every yearly budget, the score the plan reaches at "
                   "this horizon.  Steep means the next bn is buying real "
                   "measures; flat means the good ones are already funded.")
        _budget_ticks = [round(b, 2) for b in
                         np.linspace(BUDGET_RANGE[0], BUDGET_RANGE[1], 20)]
        _curve = budget_score_curve(ind_w, weights, STRATEGY_LIBRARY,
                                    base_year, horizon, _budget_ticks)
        st.plotly_chart(visual5_budget_curve(_curve, budget),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # The answer -- the measures the yearly money pays for
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(section_title("The measures this budget pays for", "overview",
                              badge=f"{_money(budget, factor_cost)} {unit_cost} / year"),
                unsafe_allow_html=True)
    st.caption("In the order the money was spent, best value first.")
    if funded:
        table = pd.DataFrame(funded)[["name", "category", "phase",
                                      "cost_bn_per_year", "feasibility",
                                      "weighted_impact"]].rename(columns={
            "name": "Measure",
            "category": "Works on",
            "phase": "Starts",
            "cost_bn_per_year": "Cost / year",
            "feasibility": "Can be done (%)",
            "weighted_impact": "Adds (points)",
        })
        table["Works on"] = table["Works on"].map(PILLAR_WORDS)
        table["Cost / year"] = table["Cost / year"] * _USD_PER_BN * factor_cost
        st.dataframe(table, use_container_width=True, hide_index=True,
                     column_config={
                         "Cost / year": st.column_config.NumberColumn(
                             f"Cost / year ({unit_cost})", format="%.2f"),
                         "Adds (points)": st.column_config.NumberColumn(
                             format="%.1f"),
                         "Can be done (%)": st.column_config.NumberColumn(
                             format="%d"),
                     })
    else:
        st.info("This budget is too small to start any measure.")

    # ---- Bottom line ----
    now_s = (f"{verdict['index_now']:.1f}"
             if np.isfinite(verdict["index_now"]) else "--")
    opt_s = (f"{verdict['index_optimal']:.1f}"
             if np.isfinite(verdict["index_optimal"]) else "--")
    bau_s = (f"{verdict['index_bau']:.1f}"
             if np.isfinite(verdict["index_bau"]) else "--")
    line1 = (f"The plan lifts the sustainability score from {now_s} "
             f"({score_year}) to {opt_s} by {horizon}; doing nothing lands at "
             f"{bau_s}.")
    weak_txt = (f" Weakest pillar now: {low[0]} ({low[1]:.0f} points)."
                if low else "")
    line2 = (f"It pays for {len(funded)} of {len(STRATEGY_LIBRARY)} measures at "
             f"{_money(package['committed_bn'], factor_cost)} {unit_cost} a "
             f"year.{weak_txt}")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
