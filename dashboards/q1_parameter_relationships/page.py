"""
Energy Parameter Relationships & What-If Forecast dashboard (Question 1).

Presentation layer only -- correlations, elasticities and the what-if
projections are computed in core/parameter_relationships.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
from core.icons import icon
from core.parameter_relationships import (
    DEFAULT_EFFICIENCY,
    DEFAULT_GDP_GROWTH,
    DEFAULT_POP_GROWTH,
    DEFAULT_HORIZON,
    FORECAST_KEYS,
    PARAMETERS,
    build_relationship_data,
)
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_ENERGY_OVERVIEW,
    Q_LNG,
    Q_NATURAL_GAS,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_corr_heatmap,
    visual2_pair_scatter,
    visual3_rolling_corr,
    visual4_forecast_path,
    visual5_impact_bars,
    visual6_elasticity_bars,
    visual7_top_pairs,
    visual8_corr_distribution,
)
from .config import DEFAULT_PERIOD, DEFAULT_ROLL_WINDOW

FILTERS_KEY = "q1_filters"
_CHART_CONFIG = {"displayModeBar": False}

# Compact KPI skin (same convention as Q10 after the spacing fix).
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

_LABELS = {k: m["label"] for k, m in PARAMETERS.items()}
_ALL_KEYS = list(PARAMETERS.keys())


def _unit_for(family: str, stored: str) -> tuple:
    """(unit label, display factor) for a parameter's family."""
    if family in ("none", "economic"):
        return stored, 1.0
    units = get_units()
    unit = units.get(family, "")
    return (unit or stored), display_factor(family, unit) if unit else 1.0


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Relationships & What-If Setup</div>',
                        unsafe_allow_html=True)

    start = st.sidebar.slider("Period start", min_value=1999, max_value=2020,
                              value=DEFAULT_PERIOD[0], key="q1_start")
    end = st.sidebar.slider("Period end", min_value=2005, max_value=2024,
                            value=DEFAULT_PERIOD[1], key="q1_end")
    if end <= start:
        end = min(start + 5, 2024)

    pair_x = st.sidebar.selectbox("Driver parameter (X axis)", _ALL_KEYS,
                                  index=_ALL_KEYS.index("gdp"),
                                  format_func=lambda k: _LABELS[k], key="q1_px",
                                  help="First parameter of the pair explorer and "
                                       "rolling-stability charts.")
    pair_y = st.sidebar.selectbox("Response parameter (Y axis)", _ALL_KEYS,
                                  index=_ALL_KEYS.index("demand"),
                                  format_func=lambda k: _LABELS[k], key="q1_py")
    roll_window = st.sidebar.slider("Rolling window (years)", 5, 12,
                                    DEFAULT_ROLL_WINDOW, key="q1_win",
                                    help="Years per correlation recomputation; "
                                         "wider windows are smoother but coarser.")

    st.sidebar.markdown(
        '<div style="font-size:10.5px;color:#94A3B8;margin:8px 0 4px;">'
        'WHAT-IF CASE (DRIVER SLIDERS)</div>', unsafe_allow_html=True)
    horizon = st.sidebar.slider("Projection horizon", min_value=2026,
                                max_value=2040, value=DEFAULT_HORIZON,
                                step=1, key="q1_horizon")
    target = st.sidebar.selectbox("Focus parameter", FORECAST_KEYS,
                                  index=FORECAST_KEYS.index("demand"),
                                  format_func=lambda k: _LABELS[k], key="q1_target",
                                  help="The parameter drawn as the year-by-year "
                                       "baseline vs what-if path.")
    gdp_g = st.sidebar.slider("GDP growth %/yr", 0.0, 8.0, DEFAULT_GDP_GROWTH,
                              0.1, key="q1_gdp_g",
                              help="What future GDP growth rate should the model assume?")
    pop_g = st.sidebar.slider("Population growth %/yr", 0.0, 3.0, DEFAULT_POP_GROWTH,
                              0.05, key="q1_pop_g")
    eff = st.sidebar.slider("Efficiency / decoupling %/yr", 0.0, 3.0,
                            DEFAULT_EFFICIENCY, 0.1, key="q1_eff",
                            help="Annual drag applied only to the what-if path -- "
                                 "e.g. from efficiency programmes or fuel switching.")

    st.session_state[FILTERS_KEY] = {
        "period": (int(start), int(end)),
        "pair_x": pair_x,
        "pair_y": pair_y,
        "roll_window": int(roll_window),
        "horizon": int(horizon),
        "target": target,
        "gdp_growth": float(gdp_g),
        "pop_growth": float(pop_g),
        "efficiency": float(eff),
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


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Parameter Relationships & What-If dashboard."""
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
    flt = st.session_state.get(FILTERS_KEY, {})
    period = flt.get("period", DEFAULT_PERIOD)
    pair_x = flt.get("pair_x", "gdp")
    pair_y = flt.get("pair_y", "demand")
    roll_window = flt.get("roll_window", DEFAULT_ROLL_WINDOW)
    horizon = flt.get("horizon", DEFAULT_HORIZON)
    target = flt.get("target", "demand")
    gdp_g = flt.get("gdp_growth", DEFAULT_GDP_GROWTH)
    pop_g = flt.get("pop_growth", DEFAULT_POP_GROWTH)
    eff = flt.get("efficiency", DEFAULT_EFFICIENCY)

    data = build_relationship_data(
        econ_df=run_query(Q_ECONOMIC),
        re_df=run_query(Q_RENEWABLE_ENERGY),
        gen_df=run_query(Q_ELEC_GEN),
        td_df=run_query(Q_TD_LOSSES),
        gas_df=run_query(Q_NATURAL_GAS),
        lng_df=run_query(Q_LNG),
        overview_df=run_query(Q_ENERGY_OVERVIEW),
        period=period,
        pair_x=pair_x, pair_y=pair_y,
        target_key=target,
        horizon=horizon,
        gdp_growth_pct=gdp_g,
        pop_growth_pct=pop_g,
        efficiency_pct=eff,
        roll_window=roll_window,
    )

    corr = data["corr"]
    fit = data["fit"]
    fc = data["forecasts"]
    strongest = data["strongest"]

    # ---- KPI strip ----
    n_params = int(corr.notna().any(axis=1).sum()) if corr is not None else 0
    strong_links = 0
    if corr is not None and not corr.empty:
        tri = corr.where(~np.eye(len(corr), dtype=bool))
        strong_links = int((tri.abs() >= 0.7).sum().sum() // 2)

    tgt_unit, tgt_factor = _unit_for(PARAMETERS[target]["family"],
                                     PARAMETERS[target]["unit"])
    tgt_row = None
    if fc is not None and not fc.empty and target in set(fc["key"]):
        tgt_row = fc[fc["key"] == target].iloc[0]

    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        st.markdown(
            _kpi_card(
                code="K1",
                title=f"Parameters Analysed ({period[0]}–{period[1]})",
                value=f"{n_params}",
                unit="parameters",
                rows=[
                    ("Pairwise links", f"{n_params * (n_params - 1) // 2}", "#CBD5E1"),
                    ("Strong |r|≥0.7", f"{strong_links}", "#14B8A6"),
                    ("Rolling window", f"{roll_window} yr", "#94A3B8"),
                ],
                accent="#00A6FB",
                icon_name="data",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        if strongest:
            a, b, r = strongest
            st.markdown(
                _kpi_card(
                    code="K2",
                    title="Strongest Relationship",
                    value=f"{r:+.2f}",
                    unit="Pearson r",
                    rows=[
                        ("Driver", _LABELS[a], "#CBD5E1"),
                        ("Response", _LABELS[b], "#CBD5E1"),
                        ("Nature", "co-moving" if r > 0 else "inverse",
                         "#10B981" if r > 0 else "#EF4444"),
                    ],
                    accent="#14B8A6",
                    icon_name="route",
                    badge="max |r|",
                    badge_colour="#14B8A6",
                    value_size=20,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _kpi_card(code="K2", title="Strongest Relationship",
                          value="–", unit="",
                          rows=[("Data", "not enough overlap", "#94A3B8")],
                          accent="#14B8A6", icon_name="route"),
                unsafe_allow_html=True,
            )

    with kpi_cols[2]:
        if tgt_row is not None:
            st.markdown(
                _kpi_card(
                    code="K3",
                    title=f"{_LABELS[target]} — Baseline {horizon}",
                    value=fmt(tgt_row["baseline_value"] * tgt_factor, 1),
                    unit=tgt_unit,
                    rows=[
                        (f"Reported {int(tgt_row['last_year'])}",
                         f"{fmt(tgt_row['last_value'] * tgt_factor, 1)} {tgt_unit}", "#CBD5E1"),
                        ("Historic CAGR", f"{tgt_row['cagr_pct']:+.1f}%/yr", "#14B8A6"),
                        ("β GDP / Pop", f"{tgt_row['b_gdp']:.2f} / {tgt_row['b_pop']:.2f}",
                         "#94A3B8"),
                    ],
                    accent="#10B981",
                    icon_name="up",
                    badge="trend carry-forward",
                    badge_colour="#10B981",
                    value_size=20,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _kpi_card(code="K3", title=f"{_LABELS[target]} — Baseline {horizon}",
                          value="–", unit=tgt_unit,
                          rows=[("Data", "series unavailable", "#94A3B8")],
                          accent="#10B981", icon_name="up"),
                unsafe_allow_html=True,
            )

    with kpi_cols[3]:
        if tgt_row is not None:
            d = tgt_row["delta_pct"]
            st.markdown(
                _kpi_card(
                    code="K4",
                    title=f"{_LABELS[target]} — What-If {horizon}",
                    value=fmt(tgt_row["whatif_value"] * tgt_factor, 1),
                    unit=tgt_unit,
                    rows=[
                        ("vs Baseline", f"{d:+.1f}%",
                         "#10B981" if d >= 0 else "#EF4444"),
                        ("Case drivers", f"GDP {gdp_g:.1f}% · Pop {pop_g:.1f}%", "#CBD5E1"),
                        ("Efficiency drag", f"−{eff:.1f}%/yr", "#F59E0B"),
                    ],
                    accent="#F59E0B",
                    icon_name="scenario",
                    badge=f"{d:+.1f}% vs baseline",
                    badge_colour="#F59E0B",
                    value_size=20,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _kpi_card(code="K4", title=f"{_LABELS[target]} — What-If {horizon}",
                          value="–", unit=tgt_unit,
                          rows=[("Data", "series unavailable", "#94A3B8")],
                          accent="#F59E0B", icon_name="scenario"),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ---- Row 1: correlation heat-map (full-width row) ----
    with st.columns(1)[0]:
        st.markdown(section_title("The Relationship Web — Correlation Matrix",
                                  "data", "Objective 1"), unsafe_allow_html=True)
        st.caption("Pearson r for every parameter pair over the selected period; "
                   "green cells co-move, red cells move apart, blanks lack overlap.")
        fig1 = visual1_corr_heatmap(corr, [_LABELS[k] for k in corr.index])
        st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 2: reading the web (ranking + distribution) ----
    w1, w2 = st.columns(2)

    with w1:
        st.markdown(section_title("Top Relationship Ranking",
                                  "insights", "Objective 1"), unsafe_allow_html=True)
        st.caption("The twelve strongest links ranked by coefficient; every stem "
                   "spans zero to its signed Pearson r.")
        fig7 = visual7_top_pairs(data["pairs"], _LABELS, n=12)
        st.plotly_chart(fig7, use_container_width=True, config=_CHART_CONFIG)

    with w2:
        st.markdown(section_title("Correlation Distribution",
                                  "overview", "Objective 1"), unsafe_allow_html=True)
        st.caption("Every computable pair binned by Pearson r; mass piled at the "
                   "far ends means the system is tightly coupled.")
        fig8 = visual8_corr_distribution(data["pairs"])
        st.plotly_chart(fig8, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 3: pair explorer ----
    p1, p2 = st.columns(2)

    with p1:
        xu, xf = _unit_for(PARAMETERS[pair_x]["family"], PARAMETERS[pair_x]["unit"])
        yu, yf = _unit_for(PARAMETERS[pair_y]["family"], PARAMETERS[pair_y]["unit"])
        st.markdown(section_title(f"Pair Explorer — {_LABELS[pair_x]} vs {_LABELS[pair_y]}",
                                  "route", "Objective 1"), unsafe_allow_html=True)
        st.caption("Each dot is one year; the dashed line is the ordinary-least-squares "
                   "fit with r, R² and slope reported on the plot.")
        fig2 = visual2_pair_scatter(fit, _LABELS[pair_x], _LABELS[pair_y],
                                    xu, yu, xf, yf)
        st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    with p2:
        st.markdown(section_title("Is the Link Stable? — Rolling Correlation",
                                  "scenario", "Objective 2"), unsafe_allow_html=True)
        st.caption(f"The {roll_window}-year window slides across the record; a line "
                   "hovering near ±1 means a dependable relationship, a crossing line "
                   "means the link is regime-dependent.")
        fig3 = visual3_rolling_corr(data["rolling"],
                                    f"{_LABELS[pair_x]} × {_LABELS[pair_y]}",
                                    roll_window)
        st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    f1, f2 = st.columns(2)

    with f1:
        st.markdown(section_title(f"What-If Projection — {_LABELS[target]} to {horizon}",
                                  "strategy", "Objective 3"), unsafe_allow_html=True)
        st.caption(f"Bars are reported history; the green line carries the historic "
                   f"CAGR forward, the amber dash re-prices growth with your sliders.")
        fig4 = visual4_forecast_path(data["path"], _LABELS[target], tgt_unit,
                                     factor=tgt_factor, boundary_year=2024)
        st.plotly_chart(fig4, use_container_width=True, config=_CHART_CONFIG)

    with f2:
        st.markdown(section_title(f"What-If Impact — Every Parameter at {horizon}",
                                  "insights", "Objective 3"), unsafe_allow_html=True)
        st.caption("How the slider case shifts each parameter versus its own baseline "
                   "trajectory (per-cent, not levels).")
        fig5 = visual5_impact_bars(fc, horizon)
        st.plotly_chart(fig5, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 5: elasticity landscape (full width) ----
    with st.columns(1)[0]:
        st.markdown(section_title("Driver Elasticities — Who Answers to Whom",
                                  "sustainability", "Objective 3"), unsafe_allow_html=True)
        st.caption("Fitted d ln(parameter)/d ln(driver): β > 1 means the parameter grows "
                   "faster than its driver, β ≈ 0 means it has decoupled.")
        fig6 = visual6_elasticity_bars(fc)
        st.plotly_chart(fig6, use_container_width=True, config=_CHART_CONFIG)

    # ---- Forecast ledger ----
    st.markdown(section_title("What-If Ledger — Predicted Values, All Parameters",
                              "overview", "Objective 3"), unsafe_allow_html=True)
    if fc is None or fc.empty:
        st.info("No parameters have enough history to project.")
    else:
        ledger = fc.copy()
        ledger["unit"] = ledger.apply(
            lambda r: _unit_for(r["family"], r["unit"])[0], axis=1)
        ledger["factor"] = ledger.apply(
            lambda r: _unit_for(r["family"], r["unit"])[1], axis=1)
        ledger["Reported"] = (ledger["last_value"] * ledger["factor"]).map(lambda v: fmt(v, 1))
        ledger["Baseline"] = (ledger["baseline_value"] * ledger["factor"]).map(lambda v: fmt(v, 1))
        ledger["What-if"] = (ledger["whatif_value"] * ledger["factor"]).map(lambda v: fmt(v, 1))
        show = ledger[["label", "unit", "last_year", "Reported", "cagr_pct",
                       "b_gdp", "b_pop", "Baseline", "What-if", "delta_pct"]].rename(
            columns={"label": "Parameter", "unit": "Unit", "last_year": "Year",
                     "cagr_pct": "CAGR %", "b_gdp": "β GDP", "b_pop": "β Pop",
                     "delta_pct": "Δ What-if %"})
        show["CAGR %"] = show["CAGR %"].map(lambda v: f"{v:+.1f}")
        show["β GDP"] = show["β GDP"].map(lambda v: f"{v:.2f}")
        show["β Pop"] = show["β Pop"].map(lambda v: f"{v:.2f}")
        show["Δ What-if %"] = show["Δ What-if %"].map(lambda v: f"{v:+.1f}")
        st.dataframe(show, use_container_width=True, hide_index=True)
