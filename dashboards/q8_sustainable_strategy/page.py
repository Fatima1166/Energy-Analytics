"""
Energy Sustainable Strategy dashboard (Question 8).

"What optimal strategy may be opted to make energy development sustainable?"

Presentation layer only -- the four-pillar indicator frame, the greedy-knapsack
strategy package and the pathway projections are computed in
core/sustainability_engine.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
from core.icons import icon
from core.sustainability_engine import (
    HISTORY_END,
    PILLARS,
    PILLAR_LABELS,
    apply_weights,
    build_indicator_frame,
    build_verdict,
    history_pair,
    latest_pillar_scores,
    project_pathways,
    select_optimal_package,
    snapshot_row,
    strategy_value_density,
)
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_LNG,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)

from .charts import (
    visual1_pillar_scorecard,
    visual2_index_trajectory,
    visual3_value_density,
    visual4_cost_impact_bubbles,
    visual5_pathway_chart,
    visual6_pillar_gain,
    visual7_component_diagnostics,
)
from .config import (
    ACCENT,
    AMBER,
    BLUE,
    COMPONENT_LABELS,
    DEFAULT_BUDGET_BN,
    DEFAULT_EVAL_YEAR,
    DEFAULT_HORIZON,
    DEFAULT_WEIGHTS,
    GREEN,
    BUDGET_RANGE,
    RED,
    STRATEGY_LIBRARY,
    TEAL,
)

FILTERS_KEY = "q8_filters"
_CHART_CONFIG = {"displayModeBar": False}

# Compact KPI skin (same convention as Q10 / Q1 after the spacing fix).
_COMPACT_CSS = """
<style>
.kpi-balance.kpi-compact {
    height: 194px !important;
    min-height: 194px !important;
    max-height: 194px !important;
    justify-content: flex-start !important;
    padding: 12px 14px 12px !important;
    overflow: hidden !important;
}
.kpi-balance.kpi-compact .kpi-balance-details {
    margin-top: auto !important;
    padding-top: 6px !important;
}
</style>
"""


def _unit_for(family: str, stored: str) -> tuple:
    from core.unit_slicer import get_units
    from core.units import display_factor
    units = get_units()
    unit = units.get(family, "")
    return (unit or stored), display_factor(family, unit) if unit else 1.0


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Strategy Optimiser Setup</div>',
                        unsafe_allow_html=True)

    st.sidebar.markdown(
        '<div style="font-size:10.5px;color:#94A3B8;margin:8px 0 4px;">'
        'PILLAR PRIORITIES (NORMALISED)</div>', unsafe_allow_html=True)
    w_sec = st.sidebar.slider("Energy Security weight", 0, 100,
                              int(DEFAULT_WEIGHTS["security"]), key="q8_w_sec")
    w_eco = st.sidebar.slider("Economic Viability weight", 0, 100,
                              int(DEFAULT_WEIGHTS["economy"]), key="q8_w_eco")
    w_env = st.sidebar.slider("Environmental weight", 0, 100,
                              int(DEFAULT_WEIGHTS["environment"]), key="q8_w_env")
    w_acc = st.sidebar.slider("Energy Access weight", 0, 100,
                              int(DEFAULT_WEIGHTS["access"]), key="q8_w_acc")

    st.sidebar.markdown(
        '<div style="font-size:10.5px;color:#94A3B8;margin:8px 0 4px;">'
        'OPTIMISER & PROJECTION</div>', unsafe_allow_html=True)
    budget = st.sidebar.slider("Annual strategy budget ($bn)", *BUDGET_RANGE,
                               DEFAULT_BUDGET_BN, 0.5, key="q8_budget",
                               help="The knapsack fills this yearly envelope with "
                                    "the densest strategies.")
    horizon = st.sidebar.slider("Projection horizon", 2026, 2040,
                                DEFAULT_HORIZON, key="q8_horizon")
    eval_year = st.sidebar.slider("Evaluation year (baseline snapshot)", 2015,
                                  HISTORY_END, DEFAULT_EVAL_YEAR, key="q8_eval",
                                  help="Latest reported year is 2024; each pillar "
                                       "falls back to its own last complete observation.")

    total = float(w_sec + w_eco + w_env + w_acc) or 1.0
    weights = {"security": w_sec / total, "economy": w_eco / total,
               "environment": w_env / total, "access": w_acc / total}

    st.session_state[FILTERS_KEY] = {
        "weights": weights,
        "raw_weights": {"security": w_sec, "economy": w_eco,
                        "environment": w_env, "access": w_acc},
        "budget_bn": float(budget),
        "horizon": int(horizon),
        "eval_year": int(eval_year),
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#00A6FB", icon_name: str = "data",
              badge: str = "", badge_colour: str = "#00A6FB",
              value_size: int = 23) -> str:
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
    <span style="color:{accent};font-size:{value_size}px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details">{detail}</div>
</div>
"""


def _weakest_pillar(pillars_now: dict) -> tuple:
    items = [(PILLAR_LABELS[p], v) for p, v in pillars_now.items()
             if v is not None and np.isfinite(v)]
    if not items:
        return ("n/a", np.nan)
    lab, v = min(items, key=lambda t: t[1])
    return lab, v


# --- Main dashboard render ---

def render() -> None:
    """Renders the Sustainable Strategy dashboard."""
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
    flt = st.session_state.get(FILTERS_KEY, {})
    weights = flt.get("weights", {k: v / 100.0 for k, v in DEFAULT_WEIGHTS.items()})
    raw_w = flt.get("raw_weights", DEFAULT_WEIGHTS)
    budget = flt.get("budget_bn", DEFAULT_BUDGET_BN)
    horizon = flt.get("horizon", DEFAULT_HORIZON)
    eval_year = flt.get("eval_year", DEFAULT_EVAL_YEAR)

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
        st.warning("No indicator data could be assembled from the warehouse.")
        return

    ind_w = apply_weights(ind, weights)

    # ---- engine calls ----
    ranked = strategy_value_density(STRATEGY_LIBRARY, weights)
    package = select_optimal_package(STRATEGY_LIBRARY, weights, budget)
    pathways = project_pathways(ind_w, weights, package, eval_year, horizon,
                                STRATEGY_LIBRARY)
    verdict = build_verdict(ind_w, weights, package, pathways, eval_year, horizon)

    pillars_now = latest_pillar_scores(ind_w, eval_year)

    # ---- KPI strip ----
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        idx_now = verdict.get("index_now", np.nan)
        weak_lab, weak_val = _weakest_pillar(pillars_now)
        st.markdown(_kpi_card(
            code="K1", title=f"Sustainability Index @ {eval_year}",
            value=f"{idx_now:.1f}" if np.isfinite(idx_now) else "n/a",
            unit="/ 100",
            rows=[("Weakest pillar", _short(weak_lab), "#EF4444"),
                  ("Its score", f"{weak_val:.1f}" if np.isfinite(weak_val) else "n/a",
                   "#F59E0B"),
                  ("Pillars tracked", f"{len(PILLARS)}", "#94A3B8")],
            accent=TEAL, icon_name="sustainability",
            badge="weighted", badge_colour=TEAL,
        ), unsafe_allow_html=True)

    with k2:
        chosen_names = package["chosen"]
        top1 = chosen_names[0]["short"] if chosen_names else "n/a"
        st.markdown(_kpi_card(
            code="K2", title=f"Optimal Index @ {horizon}",
            value=f"{verdict.get('index_optimal', np.nan):.1f}"
            if np.isfinite(verdict.get("index_optimal", np.nan)) else "n/a",
            unit="/ 100",
            rows=[("vs today", f"{verdict.get('lift_to_horizon', np.nan):+.1f} pts",
                   "#10B981"),
                  ("Lead strategy", _short(top1), "#CBD5E1"),
                  ("Strategies funded", f"{len(chosen_names)}", "#94A3B8")],
            accent=GREEN, icon_name="strategy",
            badge="optimal package", badge_colour=GREEN,
        ), unsafe_allow_html=True)

    with k3:
        gap = verdict.get("gap_vs_bau", np.nan)
        st.markdown(_kpi_card(
            code="K3", title=f"Avoided BAU Drift @ {horizon}",
            value=f"{gap:+.1f}" if np.isfinite(gap) else "n/a",
            unit="index pts vs BAU",
            rows=[("BAU index", f"{verdict.get('index_bau', np.nan):.1f}"
                  if np.isfinite(verdict.get('index_bau', np.nan)) else "n/a", "#EF4444"),
                  ("Optimal index",
                   f"{verdict.get('index_optimal', np.nan):.1f}"
                   if np.isfinite(verdict.get('index_optimal', np.nan)) else "n/a",
                   "#10B981"),
                  ("Announced path", "half-effect subset", "#94A3B8")],
            accent=AMBER, icon_name="scenario",
            badge="cost of inaction", badge_colour=AMBER,
        ), unsafe_allow_html=True)

    with k4:
        st.markdown(_kpi_card(
            code="K4", title="Budget Committed",
            value=f"${package['committed_bn']:.1f}bn",
            unit=f"of ${budget:.1f}bn / yr",
            rows=[("Unallocated", f"${package['unallocated_bn']:.1f}bn",
                   "#F59E0B" if package["unallocated_bn"] > 0.05 else "#10B981"),
                  ("Ranking rule", "impact / $ · feasibility", "#CBD5E1"),
                  ("Library size", f"{len(STRATEGY_LIBRARY)} strategies", "#94A3B8")],
            accent=BLUE, icon_name="cost",
            badge="greedy knapsack", badge_colour=BLUE,
            value_size=20,
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ---- Row 1: where we stand (V1 | V2) ----
    v1 = _build_scorecard(ind_w, eval_year)
    v2 = _build_trajectory(ind_w)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(section_title("Four-Pillar Scorecard", "sustainability",
                                  "Objective 1"), unsafe_allow_html=True)
        st.caption("Latest pillar score against the same pillar a decade back; "
                   "the gap shows momentum, the level shows distance to target.")
        st.plotly_chart(visual1_pillar_scorecard(v1), use_container_width=True,
                        config=_CHART_CONFIG)
    with c2:
        st.markdown(section_title("Index Trajectory — Where Sustainability Moved",
                                  "scenario", "Objective 1"), unsafe_allow_html=True)
        st.caption("Yearly pillar scores with the white line the strategy is "
                   "measured against: the weighted composite index.")
        st.plotly_chart(visual2_index_trajectory(v2), use_container_width=True,
                        config=_CHART_CONFIG)

    # ---- Row 2: the strategy market (V3 | V4) ----
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(section_title("Strategy Value Density — Best Bang per Buck",
                                  "insights", "Objective 2"), unsafe_allow_html=True)
        st.caption("Weighted pillar impact per $bn/yr, discounted by delivery "
                   "feasibility; the optimiser fills the budget top-down.")
        st.plotly_chart(visual3_value_density(ranked), use_container_width=True,
                        config=_CHART_CONFIG)
    with c4:
        st.markdown(section_title("Cost-Impact Map — Selected vs Rejected",
                                  "strategy", "Objective 2"), unsafe_allow_html=True)
        st.caption("Filled bubbles fit the budget package; hollow ones were "
                   "skipped because the envelope ran out or density fell.")
        st.plotly_chart(
            visual4_cost_impact_bubbles(ranked,
                                         {c["id"] for c in package["chosen"]}),
            use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 3: the chosen pathway (V5 | V6) ----
    c5, c6 = st.columns(2)
    with c5:
        st.markdown(section_title(f"Development Pathways to {horizon}",
                                  "route", "Objective 3"), unsafe_allow_html=True)
        st.caption("Same history, three futures: business-as-usual drifts on the "
                   "fitted slope, announced pledges half-fill it, the optimal "
                   "package applies fully after each strategy's lead time.")
        st.plotly_chart(visual5_pathway_chart(pathways, eval_year),
                        use_container_width=True, config=_CHART_CONFIG)
    with c6:
        st.markdown(section_title("Pillar Gain of the Optimal Package", "up",
                                  "Objective 3"), unsafe_allow_html=True)
        st.caption("Score points the package adds over BAU at the horizon, "
                   "pillar by pillar -- the answer in one chart.")
        st.plotly_chart(visual6_pillar_gain(
            _build_gain(pathways, verdict, horizon), horizon),
            use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 4: diagnostics (V7, full width) ----
    st.markdown(section_title("Component Diagnostics — the Nine Underlying Numbers",
                              "data", "Objective 1"), unsafe_allow_html=True)
    st.caption("Every pillar score is the mean of its components; red bars below "
               "40 are the bottlenecks the strategy package must clear.")
    st.plotly_chart(visual7_component_diagnostics(_build_components(ind_w, eval_year)),
                    use_container_width=True, config=_CHART_CONFIG)

    # ---- Package ledger table ----
    st.markdown(section_title("Optimal Strategy Package — Budget Ledger",
                              "overview", "Objective 2"), unsafe_allow_html=True)
    ledger = ranked.copy()
    ledger["selected"] = ledger["id"].isin({c["id"] for c in package["chosen"]})
    ledger["Status"] = np.where(ledger["selected"], "FUNDED", "deferred")
    show = ledger[["Status", "name", "category", "phase", "cost_bn_per_year",
                   "feasibility", "weighted_impact", "density"]].rename(
        columns={"name": "Strategy", "category": "Lead Pillar Area",
                 "phase": "Deployment Phase",
                 "cost_bn_per_year": "$bn / yr", "feasibility": "Feas %",
                 "weighted_impact": "Weighted Impact", "density": "Density pts/$bn"})
    st.dataframe(show, use_container_width=True, hide_index=True,
                 column_config={
                     "$bn / yr": st.column_config.NumberColumn(format="%.1f"),
                     "Weighted Impact": st.column_config.NumberColumn(format="%.1f"),
                     "Density pts/$bn": st.column_config.NumberColumn(format="%.2f"),
                 })


# --- small presentation helpers (frame shaping only, no analytics) ---

def _short(text: str, n: int = 22) -> str:
    text = str(text)
    return text if len(text) <= n else text[: n - 1] + "…"


def _build_scorecard(ind_w: pd.DataFrame, eval_year: int) -> pd.DataFrame:
    rows = []
    for p in PILLARS:
        now, then, then_year = history_pair(ind_w, f"score_{p}", eval_year, back=10)
        rows.append({"pillar_key": p, "pillar": PILLAR_LABELS[p].replace("Energy ", ""),
                     "now": now, "then": then,
                     "delta": (now - then) if np.isfinite(now) and np.isfinite(then)
                     else np.nan,
                     "now_label": f"Latest (<= {eval_year})",
                     "then_label": f"Then ({then_year})"})
    df = pd.DataFrame(rows)
    return df.dropna(subset=["now", "then"]) if not df.empty else df


def _build_trajectory(ind_w: pd.DataFrame) -> pd.DataFrame:
    cols = ["calendar_year"] + [f"score_{p}" for p in PILLARS] + ["score_weighted"]
    out = ind_w[[c for c in cols if c in ind_w.columns]].copy()
    out = out.rename(columns={f"score_{p}": p for p in PILLARS})
    out = out.rename(columns={"score_weighted": "composite"})
    return out.dropna(subset=["composite"]) if "composite" in out.columns else out


def _build_gain(pathways: pd.DataFrame, verdict: dict, horizon: int) -> pd.DataFrame:
    gains = verdict.get("pillar_gain_vs_bau", {})
    hor = pathways[pathways["calendar_year"] == horizon]
    if hor.empty:
        return pd.DataFrame()
    hor = hor.iloc[0]
    return pd.DataFrame([
        {"pillar": PILLAR_LABELS[p].replace("Energy ", ""),
         "gain": gains.get(p, np.nan),
         "bau": float(hor[f"{p}_bau"]), "optimal": float(hor[f"{p}_optimal"])}
        for p in PILLARS
    ])


def _build_components(ind_w: pd.DataFrame, eval_year: int) -> pd.DataFrame:
    hist = ind_w[ind_w["calendar_year"] <= eval_year]
    rows = []
    for col, lab in COMPONENT_LABELS.items():
        if col not in hist.columns:
            continue
        s = hist[["calendar_year", col]].dropna()
        if s.empty:
            continue
        pillar = col.split("_")[1].capitalize()
        rows.append({"label": lab, "score": float(s[col].iloc[-1]),
                     "year": int(s["calendar_year"].iloc[-1]), "pillar": pillar})
    return pd.DataFrame(rows)
