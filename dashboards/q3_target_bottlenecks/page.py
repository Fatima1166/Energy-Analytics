"""
Target Bottlenecks dashboard (Question 3).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.database import run_query
from core.bottleneck_metrics import (
    HISTORY_START,
    PROJECTED,
    build_dashboard_data,
)
from core.components import dashboard_footer, section_title
from core.queries import (
    Q_ENERGY_OVERVIEW,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
)
from core.targets import KPI_SPEC, load_targets
from core.unit_slicer import get_units
from core.units import display_factor, normalise

from .charts import (
    visual1_loss_waterfall,
    visual2_losses_path,
    visual3_import_dependence,
    visual4_gas_balance,
    visual5_gap_paths,
    visual6_achievement,
)

HORIZON = 2035
VIEW_START = HISTORY_START
DEFAULT_RANGE = (HISTORY_START, HORIZON)

_FILTERS_KEY = "q3_filters"
_KPI_KEYS = [s["key"] for s in KPI_SPEC]

_GAP_LABELS = {
    "gas_self_suff_pct": "Gas Self-Sufficiency %",
    "losses_pct": "Energy Losses %",
    "import_pct": "Import Dependence %",
    "re_share_pct": "Renewable Share %",
}
_GAP_COLORS = {
    "gas_self_suff_pct": "#00A6FB",
    "losses_pct": "#EF4444",
    "import_pct": "#F59E0B",
    "re_share_pct": "#10B981",
}


def _num(value) -> float:
    """None / NaN safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if out != out else out


# --- Sidebar: Year Range ---

def _sidebar_filters() -> dict:
    st.sidebar.markdown(
        '<div class="dsh-side-title">Analysis Range</div>',
        unsafe_allow_html=True,
    )
    year_range = st.sidebar.slider(
        "Year Range",
        min_value=VIEW_START,
        max_value=HORIZON,
        value=DEFAULT_RANGE,
        step=1,
        key="q3_year_range",
        help=("Charts zoom to this window and the KPI cards are judged on its "
              "final year. Modelled years are drawn dashed."),
    )
    return {"year_range": year_range}


def sidebar():
    st.session_state[_FILTERS_KEY] = _sidebar_filters()
    st.sidebar.divider()


def _kpi_card(reading, rank: int | None) -> str:
    """Target-aware KPI card for one benchmark."""
    sev = reading.sev
    colour = reading.color
    gap = reading.gap

    arrow = "▲" if reading.yoy > 0 else ("▼" if reading.yoy < 0 else "▬")
    yoy_good = (reading.yoy < 0) if reading.direction == "lower" else (reading.yoy > 0)
    yoy_colour = "#10B981" if yoy_good else "#EF4444"

    rank_html = ""
    if rank is not None and rank <= 2 and not reading.on_track:
        rank_html = (f'<span style="background:rgba(239,68,68,0.18);color:#EF4444;'
                     f'font-size:9px;font-weight:800;padding:1px 7px;border-radius:20px;'
                     f'border:1px solid rgba(239,68,68,0.4);">#{rank} BOTTLENECK</span>')

    return f"""
<div style="
    background: linear-gradient(135deg, rgba(22,27,38,0.95) 0%, rgba(14,18,26,0.98) 100%);
    border: 1px solid {sev['color']}55;
    border-radius: 14px;
    padding: 15px 16px 14px;
    position: relative;
    overflow: hidden;
    height: 100%;
">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{colour}00,{colour},{colour}00);"></div>

  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:9px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:31px;height:31px;background:{colour}22;border:1px solid {colour}44;
                  border-radius:8px;display:flex;align-items:center;justify-content:center;
                  color:{colour};font-size:12px;">
        <i class="fa-solid {reading.icon}"></i>
      </div>
      <div>
        <div style="color:#94A3B8;font-size:9.5px;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.8px;">{reading.code} &nbsp;·&nbsp; {reading.reference_year}</div>
        <div style="color:#E2E8F0;font-size:11px;font-weight:600;line-height:1.3;">
          {reading.title}</div>
      </div>
    </div>
    <span style="background:{sev['bg']};color:{sev['color']};font-size:9px;font-weight:700;
                 padding:2px 8px;border-radius:20px;border:1px solid {sev['color']}55;
                 white-space:nowrap;">{sev['label']}</span>
  </div>

  <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:7px;">
    <span style="color:{colour};font-size:27px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">
      {reading.actual_value:,.2f}%</span>
    <span style="color:{yoy_colour};font-size:10.5px;font-weight:700;">
      {arrow} {abs(reading.yoy):.2f}pp</span>
  </div>

  <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
    <span style="color:#64748B;font-size:10px;">Benchmark</span>
    <span style="color:#E2E8F0;font-size:10px;font-weight:600;">{reading.target:,.2f}%</span>
    <span style="flex:1;"></span>
    <span style="background:{sev['bg']};color:{sev['color']};font-size:9.5px;font-weight:700;
                 padding:2px 8px;border-radius:20px;border:1px solid {sev['color']}55;
                 white-space:nowrap;">{gap:+.1f}pp</span>
  </div>

  <div style="display:flex;align-items:center;justify-content:space-between;
              border-top:1px solid rgba(255,255,255,0.06);padding-top:6px;">
    <span style="color:#64748B;font-size:9.5px;">
      {reading.achievement:.0f}% of benchmark</span>
    {rank_html}
  </div>
</div>
"""


def render():
    units = get_units()
    filters = st.session_state.get(_FILTERS_KEY) or {"year_range": DEFAULT_RANGE}
    year_range = tuple(filters.get("year_range") or DEFAULT_RANGE)

    # Fetch data
    try:
        overview_df = run_query(Q_ENERGY_OVERVIEW)
        primary_df = run_query(Q_PRIMARY_SUPPLY)
        re_df = run_query(Q_RENEWABLE_ENERGY)
        gas_df = run_query(Q_NATURAL_GAS)
    except Exception as exc:
        st.error(f"Could not load energy data: {exc}")
        st.stop()

    targets = load_targets()
    data = build_dashboard_data(
        overview_df, primary_df, re_df, gas_df,
        targets=targets,
        year_range=year_range,
        project_end=HORIZON,
    )
    series = data["series"]
    readings = data["readings"]
    ref = data["reference_year"]

    # Unit conversion
    e_u = normalise(units.get("energy", "TOE"))
    g_u = normalise(units.get("gas", "BCF"))
    e_factor = display_factor("energy", e_u)
    g_factor = display_factor("gas", g_u)

    chart_series = series.copy()
    for col in ("supply_toe", "import_toe", "losses_toe", "td_losses_toe"):
        chart_series[col] = pd.to_numeric(chart_series[col], errors="coerce") * e_factor
    for col in ("gas_production_bcf", "gas_consumption_bcf"):
        chart_series[col] = pd.to_numeric(chart_series[col], errors="coerce") * g_factor

    span = f"{year_range[0]}–{year_range[1]}"
    wf_year = int(year_range[1])

    # KPI cards
    rank_of = {d["key"]: d["rank"] for d in data["ranking"]}
    cols = st.columns(len(KPI_SPEC))
    for col, spec in zip(cols, KPI_SPEC):
        reading = readings.get(spec["key"])
        if reading is None:
            col.warning(f"{spec['code']}: no data")
            continue
        col.markdown(_kpi_card(reading, rank_of.get(spec["key"])), unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Visual 1: Energy Loss Waterfall & Visual 2: Losses vs Benchmark
    r1c1, r1c2 = st.columns(2)
    loss_t = targets.get("losses_pct", {})

    with r1c1:
        st.markdown(
            section_title("V1 — Energy Loss Waterfall", "warning",
                          badge=f"{wf_year} · {e_u}"),
            unsafe_allow_html=True)
        st.caption(f"Step-by-step energy flow in {wf_year} from primary supply to final consumption ({e_u}), highlighting transformation and T&D loss deductions.")
        st.plotly_chart(
            visual1_loss_waterfall(chart_series, wf_year, unit=e_u),
            use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown(
            section_title("V2 — Losses vs Benchmark", "chart",
                          badge=f"{span} · {_num(loss_t.get('target')):.1f}%"),
            unsafe_allow_html=True)
        st.caption(f"Evolution of total system energy loss percentage against national policy benchmark ({_num(loss_t.get('target')):.1f}%), showing reported actuals and modelled projections.")
        st.plotly_chart(
            visual2_losses_path(series, year_range,
                                target=_num(loss_t.get("target")),
                                direction=loss_t.get("direction", "lower")),
            use_container_width=True, config={"displayModeBar": False})

    # Visual 3: Import Dependence & Visual 4: Gas Balance
    r2c1, r2c2 = st.columns(2)
    imp_t = targets.get("import_pct", {})
    gas_t = targets.get("gas_self_suff_pct", {})

    with r2c1:
        st.markdown(
            section_title("V3 — Import Dependence", "imports",
                          badge=f"{span} · {e_u} · {_num(imp_t.get('target')):.1f}%"),
            unsafe_allow_html=True)
        st.caption(f"Total primary energy imports vs indigenous domestic energy supply ({e_u}) and import dependency % compared to target benchmark.")
        st.plotly_chart(
            visual3_import_dependence(
                chart_series, year_range,
                target=_num(imp_t.get("target")),
                unit_energy=e_u,
                last_reported_year=data["last_reported_import_year"],
                benchmark_note=""),
            use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown(
            section_title("V4 — Gas Production vs Consumption", "gas",
                          badge=f"{span} · {g_u} · {_num(gas_t.get('target')):.0f}%"),
            unsafe_allow_html=True)
        st.caption(f"Natural gas domestic field production vs nationwide consumption ({g_u}), highlighting the structural gas deficit and self-sufficiency trajectory.")
        st.plotly_chart(
            visual4_gas_balance(chart_series, year_range,
                                target=_num(gas_t.get("target")), unit_gas=g_u),
            use_container_width=True, config={"displayModeBar": False})

    # Visual 5: Benchmark Gaps & Visual 6: Achievement
    r3c1, r3c2 = st.columns(2)

    with r3c1:
        st.markdown(
            section_title("V5 — Benchmark Gaps", "insights", badge=span),
            unsafe_allow_html=True)
        st.caption("Percentage-point performance gaps over time across all four strategic policy indicators relative to national target benchmarks.")
        st.plotly_chart(
            visual5_gap_paths(data["timeline"], year_range,
                              _GAP_LABELS, _GAP_COLORS),
            use_container_width=True, config={"displayModeBar": False})

    with r3c2:
        st.markdown(
            section_title("V6 — Achievement vs Benchmark", "intensity",
                          badge=span),
            unsafe_allow_html=True)
        st.caption(f"Target achievement percentages across key indicators for reference year {ref}, classifying bottleneck severity and progress.")
        st.plotly_chart(
            visual6_achievement(readings, _KPI_KEYS, year=ref),
            use_container_width=True, config={"displayModeBar": False})

    # Footer
    last_actual = data.get("last_actual_losses_year")
    imp_end = data.get("last_reported_import_year")

    worst = data["ranking"][0] if data["ranking"] else None
    if worst is not None:
        lead = (f'Most urgent in {ref}: {worst["short"]} at '
                f'{worst["achievement"]:.0f}% of its benchmark'
                f' ({worst["gap"]:+.1f}pp).' if not worst["on_track"]
                else f'All benchmarks met in {ref}; thinnest margin is '
                     f'{worst["short"]} at {worst["achievement"]:.0f}%.')
    else:
        lead = f"No benchmark data for {ref}."

    reporting = (f"losses reported to {last_actual}, imports to {imp_end}"
                 if last_actual else "reported history only")

    st.markdown(
        dashboard_footer(
            scope_line=(f"Showing {span} · benchmark year {ref} · four KPIs "
                        f"and six charts"),
            method_line=(f"Gaps are direction-aware and measured against "
                         f"dim_target; years after {imp_end} are trend-projected "
                         f"and drawn dashed. {lead}"),
            source_line=("World Bank · EIA · Pakistan Energy Yearbook "
                         f"({reporting})"),
            note=(f"Modelled, not measured: losses beyond {last_actual} and all "
                  f"import figures beyond {imp_end} are estimates."
                  if last_actual else None),
            icon_name="insights",
        ),
        unsafe_allow_html=True,
    )
