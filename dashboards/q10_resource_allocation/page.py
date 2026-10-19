"""
Optimal Resource Allocation for Sustainable Development dashboard (Question 10).

Presentation layer only -- the constrained water-filling optimiser lives in
core/resource_allocation.py and every frame here arrives pre-computed.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
from core.icons import icon
from core.queries import (
    Q_ELEC_SECTOR_CONSUMPTION,
    Q_EMISSION_FACTORS,
    Q_NATURAL_GAS,
    Q_RENEWABLE_ENERGY,
)
from core.resource_allocation import (
    DEFAULT_DEMAND_GROWTH,
    DEFAULT_FUEL_INFL,
    DEFAULT_PRESSURE,
    DEFAULT_W_CARBON,
    DEFAULT_W_COST,
    DEFAULT_W_SECURITY,
    HISTORY_END,
    HORIZON,
    build_allocation_data,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_allocation_bars,
    visual2_tradeoff_lines,
    visual3_shift_bars,
    visual4_sector_stacked,
    visual5_scorecard_butterfly,
    visual6_concentration_pareto,
)

FILTERS_KEY = "q10_filters"
_CHART_CONFIG = {"displayModeBar": False}

# Compact KPI skin (same convention introduced on Q7 after the spacing fix).
# Uniform fixed height + details pinned to the bottom => the five cards align
# on their lower edge even when a title wraps to a different number of lines.
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


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Allocation Optimiser Setup</div>',
                        unsafe_allow_html=True)

    horizon = st.sidebar.slider(
        "Planning horizon", min_value=2026, max_value=2040, value=HORIZON,
        step=1, key="q10_horizon",
        help="Year whose generation requirement the optimiser must allocate.",
    )

    growth = st.sidebar.slider(
        "Demand growth %/yr", min_value=2.0, max_value=8.0,
        value=DEFAULT_DEMAND_GROWTH, step=0.1, key="q10_growth",
        help="Compound growth applied to the reported 2024 generation base.",
    )

    st.sidebar.markdown(
        '<div style="font-size:10.5px;color:#94A3B8;margin:2px 0 4px;">'
        'SUSTAINABILITY WEIGHTS (auto-normalised)</div>', unsafe_allow_html=True)
    w_cost = st.sidebar.slider("Least cost", 0.0, 100.0, DEFAULT_W_COST, 1.0,
                               key="q10_w_cost",
                               help="Weight on cheap purchase tariffs in the utility.")
    w_carbon = st.sidebar.slider("Low carbon", 0.0, 100.0, DEFAULT_W_CARBON, 1.0,
                                 key="q10_w_carbon",
                                 help="Weight on low lifecycle CO₂ intensity.")
    w_security = st.sidebar.slider("Fuel security", 0.0, 100.0, DEFAULT_W_SECURITY, 1.0,
                                   key="q10_w_security",
                                   help="Weight on low import dependence of the fuel chain.")

    pressure = st.sidebar.slider(
        "Optimisation pressure", min_value=1.0, max_value=8.0,
        value=DEFAULT_PRESSURE, step=0.5, key="q10_pressure",
        help="Concentration exponent: 1 = gentle tilt toward the best resources, "
             "8 = winner-takes-most before ceilings clamp.",
    )

    with st.sidebar.expander("Advanced Model Settings", expanded=False):
        fuel_infl = st.sidebar.slider(
            "Fuel price escalation %/yr", 0.0, 8.0, DEFAULT_FUEL_INFL, 0.25,
            key="q10_fuel_infl",
            help="Horizon-year thermal tariff drift used in the cost pillar.",
        )

    st.session_state[FILTERS_KEY] = {
        "horizon": int(horizon),
        "growth": float(growth),
        "w_cost": float(w_cost),
        "w_carbon": float(w_carbon),
        "w_security": float(w_security),
        "pressure": float(pressure),
        "fuel_infl": float(fuel_infl),
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#10B981", icon_name: str = "sustainability",
              badge: str = "", badge_colour: str = "#10B981",
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


def _pct_delta(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0 if old else 0.0


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Optimal Resource Allocation dashboard."""
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
    flt = st.session_state.get(FILTERS_KEY, {})
    horizon = flt.get("horizon", HORIZON)
    growth = flt.get("growth", DEFAULT_DEMAND_GROWTH)
    w_cost = flt.get("w_cost", DEFAULT_W_COST)
    w_carbon = flt.get("w_carbon", DEFAULT_W_CARBON)
    w_security = flt.get("w_security", DEFAULT_W_SECURITY)
    pressure = flt.get("pressure", DEFAULT_PRESSURE)
    fuel_infl = flt.get("fuel_infl", DEFAULT_FUEL_INFL)

    re_df = run_query(Q_RENEWABLE_ENERGY)
    gas_df = run_query(Q_NATURAL_GAS)
    sector_df = run_query(Q_ELEC_SECTOR_CONSUMPTION)
    ef_df = run_query(Q_EMISSION_FACTORS)

    data = build_allocation_data(
        re_df=re_df,
        gas_df=gas_df,
        sector_df=sector_df,
        ef_df=ef_df,
        horizon=horizon,
        demand_growth_pct=growth,
        w_cost=w_cost,
        w_carbon=w_carbon,
        w_security=w_security,
        pressure=pressure,
        fuel_infl_pct=fuel_infl,
    )

    alloc = data["allocation"]
    opt, bau = data["opt_score"], data["bau_score"]

    # Display units
    units = get_units()
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_cost = units.get("cost", "USD bn")
    factor_cost = display_factor("cost", unit_cost)
    unit_em = units.get("emission", "Mt")
    factor_em = display_factor("emission", unit_em)
    unit_gas = units.get("gas", "BCF")
    factor_gas = display_factor("gas", unit_gas)

    shortfall = data["shortfall_gwh"]
    coverage = opt["coverage_pct"]

    # ---- KPI strip ----
    kpi_cols = st.columns(5)

    with kpi_cols[0]:
        st.markdown(
            _kpi_card(
                code="K1",
                title=f"Resource Requirement ({horizon})",
                value=fmt(data["demand_gwh"] * factor_elec, 0),
                unit=unit_elec,
                rows=[
                    (f"Reported {HISTORY_END}", f"{fmt(data['total_2024_gwh'] * factor_elec, 0)} {unit_elec}", "#CBD5E1"),
                    ("Growth Path", f"{growth:.1f}%/yr", "#14B8A6"),
                    ("vs BAU Mix", "same energy, different split", "#94A3B8"),
                ],
                accent="#14B8A6",
                icon_name="demand",
                badge=f"×{data['demand_gwh'] / max(data['total_2024_gwh'], 1):.2f}",
                badge_colour="#14B8A6",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        d_cost = _pct_delta(opt["cost_usd"], bau["cost_usd"])
        st.markdown(
            _kpi_card(
                code="K2",
                title=f"Optimal Annual Purchase Cost ({horizon})",
                value=fmt(opt["cost_usd"] * factor_cost, 2),
                unit=unit_cost,
                rows=[
                    ("BAU (2024 mix)", f"{fmt(bau['cost_usd'] * factor_cost, 2)} {unit_cost}", "#CBD5E1"),
                    ("Cost vs BAU", f"{d_cost:+.1f}%", "#10B981" if d_cost < 0 else "#EF4444"),
                    ("Weights C/CO₂/S", f"{w_cost:.0f}/{w_carbon:.0f}/{w_security:.0f}", "#94A3B8"),
                ],
                accent="#F59E0B",
                icon_name="cost",
                badge=f"{d_cost:+.1f}% vs BAU",
                badge_colour="#F59E0B",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[2]:
        d_co2 = _pct_delta(opt["co2_t"], bau["co2_t"])
        st.markdown(
            _kpi_card(
                code="K3",
                title=f"Optimal Annual CO₂ ({horizon})",
                value=fmt(opt["co2_t"] * factor_em, 1),
                unit=unit_em,
                rows=[
                    ("BAU (2024 mix)", f"{fmt(bau['co2_t'] * factor_em, 1)} {unit_em}", "#CBD5E1"),
                    ("CO₂ vs BAU", f"{d_co2:+.1f}%", "#10B981" if d_co2 < 0 else "#EF4444"),
                    ("RE Share", f"{opt['re_share_pct']:.1f}% (target 60%)", "#22D3EE"),
                ],
                accent="#10B981",
                icon_name="co2",
                badge=f"{d_co2:+.1f}% vs BAU",
                badge_colour="#10B981",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[3]:
        st.markdown(
            _kpi_card(
                code="K4",
                title=f"Import-Dependent Power ({horizon})",
                value=f"{opt['import_dep_pct']:.1f}",
                unit="% of Generation",
                rows=[
                    ("BAU dependence", f"{bau['import_dep_pct']:.1f}%", "#CBD5E1"),
                    ("Diversity 1−HHI", f"{(1 - opt['diversity_hhi']):.2f}", "#14B8A6"),
                    ("Clamped Resources", f"{int(alloc['clamped'].sum())} at ceiling", "#F59E0B"),
                ],
                accent="#22D3EE",
                icon_name="imports",
                badge=f"{opt['import_dep_pct'] - bau['import_dep_pct']:+.1f} pp",
                badge_colour="#22D3EE",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[4]:
        st.markdown(
            _kpi_card(
                code="K5",
                title=f"Demand Coverage Inside Ceilings ({horizon})",
                value=f"{coverage:.1f}",
                unit="% Allocated",
                rows=[
                    ("Shortfall", f"{fmt(shortfall * factor_elec, 0)} {unit_elec}",
                     "#EF4444" if shortfall > 1 else "#10B981"),
                    ("Gas Self-Sufficiency", f"{data['gas_self_sufficiency_pct']:.0f}%", "#F97316"),
                    ("Domestic Gas Cap", f"{fmt(data['domestic_gas_bcf'] * factor_gas, 1)} {unit_gas}", "#94A3B8"),
                ],
                accent="#A78BFA",
                icon_name="sustainability",
                badge="Feasible plan" if shortfall <= 1 else "Ceilings bind",
                badge_colour="#A78BFA",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ---- Row 1: allocation bars + trade-off sweep lines ----
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown(section_title(f"Allocation Split - BAU vs Optimal ({horizon})",
                                  "sustainability", "Objective 1"), unsafe_allow_html=True)
        st.caption(f"Grey bars are the frozen 2024 mix, coloured bars the optimiser's plan "
                   f"for the same energy requirement ({unit_elec}).")
        fig1 = visual1_allocation_bars(allocation=alloc, unit_elec=unit_elec,
                                       factor_elec=factor_elec)
        st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    with r1c2:
        st.markdown(section_title("The Trade-off Map - Cost vs Carbon Sweep",
                                  "scenario", "Objective 1"), unsafe_allow_html=True)
        st.caption("Each point re-runs the optimiser under a different priority, from pure "
                   "least-cost to pure low-carbon; the dotted marker is your sidebar weights.")
        theta_sel = (w_carbon / (w_cost + w_carbon)) if (w_cost + w_carbon) > 0 else 0.5
        fig2 = visual2_tradeoff_lines(
            pareto=data["pareto"], selected_theta=theta_sel,
            unit_cost=unit_cost, factor_cost=factor_cost,
            unit_em=unit_em, factor_em=factor_em,
        )
        st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 2: reallocation shift + sector supply mix ----
    r2c1, r2c2 = st.columns(2)

    with r2c1:
        st.markdown(section_title(f"Reallocation Shift - What Moves Where ({horizon})",
                                  "route", "Objective 2"), unsafe_allow_html=True)
        st.caption(f"Optimal minus BAU per resource ({unit_elec}): emerald bars scale a "
                   f"resource up, red bars claw it back.")
        fig3 = visual3_shift_bars(allocation=alloc, unit_elec=unit_elec,
                                  factor_elec=factor_elec)
        st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    with r2c2:
        st.markdown(section_title("Optimal Energy Flowed to End-Use Sectors",
                                  "data", "Objective 4"), unsafe_allow_html=True)
        st.caption("The optimised generation carved into consumption sectors in proportion "
                   "to their reported demand shares, split by resource group.")
        fig4 = visual4_sector_stacked(sankey=data["sankey"], unit_elec=unit_elec,
                                      factor_elec=factor_elec)
        st.plotly_chart(fig4, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 3: scorecard butterfly + intensity matrix ----
    r3c1, r3c2 = st.columns(2)

    with r3c1:
        st.markdown(section_title("Sustainability Scorecard - Six Axes, Two Pathways",
                                  "strategy", "Objective 2"), unsafe_allow_html=True)
        st.caption("Cost efficiency, low carbon, fuel security, diversity, renewable share and "
                   "coverage, each scored 0–100 for the frozen BAU mix and the optimal allocation.")
        fig5 = visual5_scorecard_butterfly(radar=data["radar"])
        st.plotly_chart(fig5, use_container_width=True, config=_CHART_CONFIG)

    with r3c2:
        st.markdown(section_title("Allocation Concentration - Who Carries the Plan",
                                  "insights", "Objective 3"), unsafe_allow_html=True)
        st.caption(f"Resources ranked by optimal generation ({unit_elec}) with the running "
                   f"cumulative share - how few technologies the plan leans on.")
        fig6 = visual6_concentration_pareto(allocation=alloc, unit_elec=unit_elec,
                                            factor_elec=factor_elec)
        st.plotly_chart(fig6, use_container_width=True, config=_CHART_CONFIG)

    if shortfall > 1:
        st.warning(f"Resource ceilings bind: {fmt(shortfall * factor_elec, 0)} {unit_elec} of the "
                   f"{horizon} requirement cannot be served under current caps. Raise the "
                   f"optimisation pressure, ease fuel escalation, or plan demand-side savings.")

    # ---- Allocation ledger ----
    st.markdown(section_title("Allocation Ledger — Technology-Level Verdict",
                              "insights", "Objective 5"), unsafe_allow_html=True)
    ledger = alloc.copy()
    ledger["Optimal"] = (ledger["optimal_gwh"] * factor_elec).map(lambda v: fmt(v, 0))
    ledger["BAU"] = (ledger["bau_gwh"] * factor_elec).map(lambda v: fmt(v, 0))
    ledger["Δ vs BAU"] = (ledger["delta_gwh"] * factor_elec).map(lambda v: fmt(v, 0))
    ledger["Ceiling"] = (ledger["ceiling_gwh"] * factor_elec).map(lambda v: fmt(v, 0))
    ledger["Cost"] = (ledger["cost_usd"] * factor_cost).map(lambda v: fmt(v, 2))
    ledger["CO₂"] = (ledger["co2_t"] * factor_em).map(lambda v: fmt(v, 1))
    ledger["Capacity"] = (ledger["capacity_mw"] / 1000.0).map(lambda v: f"{v:,.1f} GW")
    ledger["At ceiling?"] = ledger["clamped"].map({True: "◤ clamped", False: ""})
    show = ledger[["technology", "Optimal", "BAU", "Δ vs BAU", "Ceiling",
                   "Cost", "CO₂", "Capacity", "At ceiling?"]].rename(
        columns={"technology": "Technology",
                 "Cost": f"Cost ({unit_cost})", "CO₂": f"CO₂ ({unit_em})",
                 "Optimal": f"Optimal ({unit_elec})", "BAU": f"BAU ({unit_elec})",
                 "Δ vs BAU": f"Δ ({unit_elec})", "Ceiling": f"Ceiling ({unit_elec})"})
    st.dataframe(show, use_container_width=True, hide_index=True)
