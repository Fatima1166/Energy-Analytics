"""
Optimal Resource Allocation dashboard (Question 10).

Q10: What is optimal resource allocation for sustainable development?

Thin presentation shell over the pure engine `core/resource_allocation.py`:

    fetch frames (config.database.run_query)
        -> engine.build_allocation_data   (profiles, utility, water-filling,
                                           priority sweep, six-way scorecard)
        -> charts.py renders the engine outputs

What is left on the page answers the question and nothing more: three cards,
four charts in two rows, and the plan itself as a table.  No analytics and no
prose verdict live here.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.icons import icon
from core.queries import Q_EMISSION_FACTORS, Q_NATURAL_GAS, Q_RENEWABLE_ENERGY
from core.resource_allocation import (
    HISTORY_END,
    HORIZON,
    RE_POLICY_TARGET_PCT,
    build_allocation_data,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from . import charts
from .config import (
    AMBER, BLUE, DEFAULT_GROWTH_PCT, GREEN, GROWTH_RANGE, HORIZON_RANGE,
    PRESET_ORDER, RED, SLATE, TEAL, bau_word, preset_weights, tech_word,
)

_FILTERS_KEY = "q10_filters"
_CHART_CONFIG = {"displayModeBar": False}

_MUTED = SLATE

# Balanced fixed height and bottom-anchored details so every card in the row
# aligns strictly along the bottom edge.
_CARD_CSS = """
<style>
  .kpi-balance.q10-kpi {
      height: 195px !important;
      min-height: 195px !important;
      max-height: 195px !important;
      justify-content: space-between !important;
      padding: 13px 14px 12px !important;
      box-sizing: border-box !important;
  }
  .kpi-balance.q10-kpi .kpi-balance-details {
      margin-top: auto !important;
      border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
      padding-top: 6px !important;
  }
</style>
"""


# ── Sidebar ──────────────────────────────────────────────────────────────────

def sidebar() -> None:
    """Q10 controls -- three of them, no caption text under them.

    What the plan should favour, how fast demand grows, and how far ahead to
    look.  The two solver knobs this page used to carry (how hard the plan
    leans on its best resource, and fuel price drift) stay at their documented
    engine defaults: they change the shape of the answer, not what is possible.
    """
    st.sidebar.markdown('<div class="dsh-side-title">Resource Allocation</div>',
                        unsafe_allow_html=True)

    preset = st.sidebar.selectbox("What the plan should favour", PRESET_ORDER,
                                  index=0, key="q10_preset")

    growth = st.sidebar.slider("How fast demand grows (% a year)", *GROWTH_RANGE,
                               DEFAULT_GROWTH_PCT, 0.1, key="q10_growth",
                               help="Growth put on the power the record last "
                                    "reported.  The amount the plan has to "
                                    "supply comes from this.")

    horizon = st.sidebar.slider("Plan up to", *HORIZON_RANGE, HORIZON, 1,
                                key="q10_horizon",
                                help="The year whose power need is being split "
                                     "between the resources.")

    w_cost, w_carbon, w_security = preset_weights(preset)
    st.session_state[_FILTERS_KEY] = {
        "preset": preset,
        "horizon": int(horizon),
        "growth": float(growth),
        "w_cost": float(w_cost),
        "w_carbon": float(w_carbon),
        "w_security": float(w_security),
    }
    st.sidebar.divider()


# ── KPI card (house style) ───────────────────────────────────────────────────

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
<div class="kpi-balance q10-kpi" style="border: 1px solid {accent}44;">
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


def _dash(v: float, spec: str = ".1f") -> str:
    return "--" if not (isinstance(v, (int, float)) and np.isfinite(v)) else format(v, spec)


def _pct_delta(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0 if old else 0.0


# ── Main render ─────────────────────────────────────────────────────────────

def render() -> None:
    """Renders the Q10 Optimal Resource Allocation dashboard."""
    flt = st.session_state.get(_FILTERS_KEY, {})
    w_cost, w_carbon, w_security = preset_weights(flt.get("preset", PRESET_ORDER[0]))
    horizon = int(flt.get("horizon", HORIZON))
    growth = float(flt.get("growth", DEFAULT_GROWTH_PCT))

    # ── 1. Engine call (the only I/O in this module) ─────────────────────────
    try:
        data = build_allocation_data(
            re_df=run_query(Q_RENEWABLE_ENERGY),
            gas_df=run_query(Q_NATURAL_GAS),
            ef_df=run_query(Q_EMISSION_FACTORS),
            horizon=horizon,
            demand_growth_pct=growth,
            w_cost=w_cost,
            w_carbon=w_carbon,
            w_security=w_security,
        )
    except Exception as exc:  # pragma: no cover — presentation guard
        st.error(f"Allocation engine failed: {exc}")
        return

    alloc = data["allocation"]
    if alloc is None or alloc.empty:
        st.warning("No generation history to allocate — check the MySQL connection.")
        return

    plan, old = data["opt_score"], data["bau_score"]
    shortfall = data["shortfall_gwh"]
    n_clamped = int(alloc["clamped"].sum())

    # ── 2. Units ─────────────────────────────────────────────────────────────
    units = get_units()
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_cost = units.get("cost", "USD bn")
    factor_cost = display_factor("cost", unit_cost)
    unit_em = units.get("emission", "t")
    factor_em = display_factor("emission", unit_em)

    d_cost = _pct_delta(plan["cost_usd"], old["cost_usd"])
    ratio = data["demand_gwh"] / max(data["total_base_gwh"], 1)
    # The year the old mix really comes from.  Every label naming it uses this,
    # so the page cannot print "2024" over a number the 2024 row never gave.
    base_year = int(data["base_year"]) or HISTORY_END
    bau_label = bau_word(base_year)

    # ═══════════════════════ Three cards across four slots ═══════════════════
    # The fourth slot stays empty so each card keeps a four-up row's width.
    cards = [
        _kpi_card(
            code="K1",
            title="Power that has to be supplied",
            value=fmt(data["demand_gwh"] * factor_elec),
            unit=f"{unit_elec} a year · {horizon}",
            rows=[
                (f"Made in {base_year}",
                 f"{fmt(data['total_base_gwh'] * factor_elec)} {unit_elec}", _MUTED),
                ("Growth used", f"{growth:.1f}% a year", TEAL),
                ("Left unserved",
                 f"{fmt(shortfall * factor_elec)} {unit_elec}",
                 GREEN if shortfall <= 1 else RED),
            ],
            accent=TEAL, icon_name="generation",
            badge=f"{ratio:.1f}× the {base_year} need", badge_colour=TEAL,
        ),
        _kpi_card(
            code="K2",
            title="What the plan costs a year",
            value=fmt(plan["cost_usd"] * factor_cost, 2),
            unit=unit_cost,
            rows=[
                (f"Same energy, {bau_label.lower()}",
                 f"{fmt(old['cost_usd'] * factor_cost, 2)} {unit_cost}", _MUTED),
                ("Cost change", f"{d_cost:+.1f}%", GREEN if d_cost < 0 else RED),
                (f"CO₂ vs {base_year} mix",
                 f"{fmt(plan['co2_t'] * factor_em)} / "
                 f"{fmt(old['co2_t'] * factor_em)} {unit_em}", BLUE),
            ],
            accent=AMBER, icon_name="cost",
            badge=f"{d_cost:+.1f}% vs {bau_label.lower()}", badge_colour=AMBER,
        ),
        _kpi_card(
            code="K3",
            title="How clean, and how sure of fuel",
            value=_dash(plan["re_share_pct"]),
            unit=f"% clean power · {horizon}",
            rows=[
                (f"Clean share on {bau_label.lower()}", f"{old['re_share_pct']:.1f}%", _MUTED),
                ("Fuel from abroad",
                 f"{plan['import_dep_pct']:.1f}% (was {old['import_dep_pct']:.1f}%)", AMBER),
                ("Resources at their limit", f"{n_clamped} of {len(alloc)}",
                 RED if n_clamped else _MUTED),
            ],
            accent=GREEN, icon_name="renewables",
            badge=f"{RE_POLICY_TARGET_PCT:.0f}% clean is the mark", badge_colour=GREEN,
        ),
    ]

    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 1 -- the split itself            Visual 2 -- what the pick buys
    # ══════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(section_title("Visual 1 – How the power is split",
                                  "sustainability", badge=f"{horizon} plan"),
                    unsafe_allow_html=True)
        st.caption(f"Grey is what the {base_year} mix would make, colour is the "
                   "plan. Both serve the same energy need.")
        st.plotly_chart(charts.visual1_allocation_bars(alloc, unit_elec, factor_elec,
                                                      base_year),
                        use_container_width=True, config=_CHART_CONFIG)
    with c2:
        st.markdown(section_title("Visual 2 – What the priorities buy",
                                  "scenario", badge="cost and CO₂"),
                    unsafe_allow_html=True)
        st.caption("The same plan run from cheapest-first to cleanest-first; "
                   "the dotted line is your pick.")
        theta = (w_carbon / (w_cost + w_carbon)) if (w_cost + w_carbon) > 0 else 0.5
        st.plotly_chart(charts.visual2_tradeoff_lines(
            data["pareto"], theta, unit_cost, factor_cost, unit_em, factor_em),
            use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 3 -- what moves                 Visual 4 -- is it more sustainable
    # ══════════════════════════════════════════════════════════════════════
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(section_title("Visual 3 – What moves, source by source",
                                  "route", badge=f"{horizon} vs {base_year}"),
                    unsafe_allow_html=True)
        st.caption(f"Plan minus the {base_year} mix for each resource. Green "
                   "grows a source, red pulls one back.")
        st.plotly_chart(charts.visual3_shift_bars(alloc, unit_elec, factor_elec,
                                                  base_year),
                        use_container_width=True, config=_CHART_CONFIG)
    with c4:
        st.markdown(section_title("Visual 4 – Is the plan more sustainable?",
                                  "insights", badge="scored 0 to 100"),
                    unsafe_allow_html=True)
        st.caption("Six things a plan can be judged on, scored for the old mix "
                   "and for the plan. One can go down.")
        st.plotly_chart(charts.visual4_sustainability_scorecard(data["radar"],
                                                                base_year),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 5 -- the cost-CO₂ trade-off shape (companion to V2's dual lines)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    c5, _ = st.columns([1.6, 1])
    with c5:
        st.markdown(section_title("Visual 5 – The cost-CO₂ trade-off shape",
                                  "scenario", badge="one dot per priority"),
                    unsafe_allow_html=True)
        st.caption("Every plan the sweep can build, plotted as cost against CO₂. "
                   "The knee shows where going cleaner stops costing much more.")
        st.plotly_chart(charts.visual5_tradeoff_scatter(
            data["pareto"], theta, unit_cost, factor_cost, unit_em, factor_em),
            use_container_width=True, config=_CHART_CONFIG)

    if shortfall > 1:
        st.warning(f"The limits bind: {fmt(shortfall * factor_elec)} {unit_elec} of the "
                   f"{horizon} need cannot be supplied under them. Either build more "
                   f"than the ceilings allow or save demand.")

    # ═══════════════════════════ The plan, in full ═══════════════════════════
    st.markdown(section_title("The plan, resource by resource", "data",
                              badge=f"{len(alloc)} resources"),
                unsafe_allow_html=True)
    ledger = alloc.copy()
    ledger["Resource"] = ledger["technology"].map(tech_word)
    ledger["Plan"] = (ledger["optimal_gwh"] * factor_elec).map(fmt)
    ledger["Old mix"] = (ledger["bau_gwh"] * factor_elec).map(fmt)
    ledger["Change"] = (ledger["delta_gwh"] * factor_elec).map(fmt)
    ledger["Most possible"] = (ledger["ceiling_gwh"] * factor_elec).map(fmt)
    ledger["Cost"] = (ledger["cost_usd"] * factor_cost).map(lambda v: fmt(v, 2))
    ledger["CO2"] = (ledger["co2_t"] * factor_em).map(fmt)
    ledger["At its limit"] = ledger["clamped"].map({True: "yes", False: ""})
    show = ledger[["Resource", "Plan", "Old mix", "Change", "Most possible",
                   "Cost", "CO2", "At its limit"]].rename(columns={
        "Plan": f"Plan ({unit_elec})",
        "Old mix": f"{base_year} mix ({unit_elec})",
        "Change": f"Change ({unit_elec})",
        "Most possible": f"Most possible ({unit_elec})",
        "Cost": f"Cost ({unit_cost})",
        "CO2": f"CO₂ ({unit_em})",
    })
    st.dataframe(show, use_container_width=True, hide_index=True)

    # ---- Bottom line ----
    if shortfall > 1:
        line1 = (f"Even the best split under these limits leaves "
                 f"{fmt(shortfall * factor_elec)} {unit_elec} of the {horizon} "
                 "need unserved.")
    else:
        extra = (f" {n_clamped} resources sit right at their ceiling." if n_clamped
                 else "")
        line1 = (f"The chosen split serves the full {horizon} demand within every "
                 f"resource limit.{extra}")
    line2 = (f"It costs {d_cost:+.1f}% against the {base_year} mix and takes "
             f"clean power to {_dash(plan['re_share_pct'])}% (from "
             f"{old['re_share_pct']:.1f}%).")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
