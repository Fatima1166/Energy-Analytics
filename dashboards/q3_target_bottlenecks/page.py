"""
Target Bottlenecks dashboard (Question 3).

Question 3 asks what is blocking the planned targets, so this page keeps only
the three ingredients of that answer:

  1. Sidebar       -- which years to look at
  2. KPI cards     -- the four planned targets, each with its benchmark, its
                      gap, the direction of travel and how severe the miss is
  3. Visuals       -- where the energy is lost, what we import, the gas
                      shortfall, and all four distances to target together

Benchmarks come from the database (dim_target) through core.targets, and every
number is computed by core.bottleneck_metrics -- this page only lays it out.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.database import run_query
from core.bottleneck_metrics import (
    HISTORY_START,
    build_dashboard_data,
)
from core.components import conclusion_card, section_title
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
    visual2_import_dependence,
    visual3_gas_balance,
    visual4_gap_paths,
    visual5_bottleneck_slope,
)

HORIZON = 2035
VIEW_START = HISTORY_START
DEFAULT_RANGE = (HISTORY_START, HORIZON)

_FILTERS_KEY = "q3_filters"

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
        '<div class="dsh-side-title">Years</div>',
        unsafe_allow_html=True,
    )
    year_range = st.sidebar.slider(
        "Years to show",
        min_value=VIEW_START,
        max_value=HORIZON,
        value=DEFAULT_RANGE,
        step=1,
        key="q3_year_range",
        help=("Charts show these years. The cards use the last year you pick."),
    )
    return {"year_range": year_range}


def sidebar():
    st.session_state[_FILTERS_KEY] = _sidebar_filters()
    st.sidebar.divider()


_CARD_CSS = """
<style>
  .q3-kpi {
      --acc: #64748B;
      --acc-soft: rgba(100, 116, 139, 0.16);
      background: linear-gradient(145deg, rgba(28, 33, 44, 0.95) 0%, rgba(18, 22, 30, 0.98) 100%) !important;
      border-radius: 12px !important;
      padding: 13px 14px 12px 17px !important;
      height: 128px !important;
      min-height: 128px !important;
      max-height: 128px !important;
      box-sizing: border-box !important;
      display: flex !important;
      flex-direction: column !important;
      justify-content: space-between !important;
      position: relative !important;
      overflow: hidden !important;
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
      border: 1px solid rgba(255, 255, 255, 0.07) !important;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
      width: 100% !important;
  }
  /* Per-metric accent bar + hover glow -- the same skin the other
     dashboards' KPI cards wear, so Q3 no longer looks plainer. */
  .q3-kpi::before {
      content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
      background: linear-gradient(180deg, var(--acc) 0%, var(--acc) 55%, transparent 100%);
      border-radius: 4px 0 0 4px;
  }
  .q3-kpi:hover {
      transform: translateY(-4px) !important;
      border-color: var(--acc) !important;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.5), 0 0 16px var(--acc-soft) !important;
  }
  .q3-kpi-footer {
      display: flex !important;
      align-items: center !important;
      gap: 6px !important;
      margin-top: auto !important;
      border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
      padding-top: 6px !important;
      min-height: 20px !important;
  }
</style>
"""


def _kpi_card(reading, rank: int | None) -> str:
    """Target-aware KPI card for one benchmark.

    Power BI style blank: when the reference year has no source row for this
    metric the value, YoY and gap cells render as empty strings -- never a
    silent 0.0 that could be mistaken for a real measurement.
    """
    sev = reading.sev
    colour = reading.color
    is_missing = (reading.actual_value is None) or pd.isna(reading.actual_value)

    # Every span below carries text. An empty inline <span> (the old flex
    # spacer) made Streamlit's markdown parser leak the raw tag as literal
    # text on a "no data" year, so the footer is built from non-empty bits
    # and right-alignment uses margin-left:auto instead of a spacer span.
    target_html = ""
    if reading.target is not None and not pd.isna(reading.target):
        target_html = f"{reading.target:,.1f}%"

    if is_missing:
        # Rule 4: the reference year reported nothing for this metric, so the
        # value area says "no reading" -- never a silent 0.0.
        value_block = (
            '<div style="min-height:22px;margin-bottom:8px;">'
            '<span style="color:#64748B;font-size:13px;font-weight:700;'
            "font-family:'JetBrains Mono','Courier New',monospace;\">"
            'no reading</span></div>')
        gap_html = ""
        rank_html = ""
    else:
        gap = reading.gap
        arrow = "\u25b2" if reading.yoy > 0 else ("\u25bc" if reading.yoy < 0 else "\u25ac")
        yoy_good = (reading.yoy < 0) if reading.direction == "lower" else (reading.yoy > 0)
        yoy_colour = "#10B981" if yoy_good else "#EF4444"
        yoy_html = (f'<span style="color:{yoy_colour};font-size:8px;font-weight:600;">'
                    f'{arrow} {abs(reading.yoy):.1f}pp</span>')
        value_block = (
            '<div style="display:flex;align-items:baseline;gap:8px;'
            'min-height:22px;margin-bottom:8px;">'
            f'<span style="color:{colour};font-size:22px;font-weight:800;line-height:1;'
            "font-family:'JetBrains Mono','Courier New',monospace;\">"
            f'{reading.actual_value:,.1f}%</span>{yoy_html}</div>')
        gap_html = (f'<span style="color:{sev["color"]};font-size:8px;font-weight:700;">'
                    f'({gap:+.1f}pp)</span>')
        if rank is not None and rank <= 2 and not reading.on_track:
            rank_html = (f'<span style="color:#EF4444;font-size:8px;font-weight:700;">'
                         f'#{rank} bottleneck</span>')
        else:
            rank_html = ""

    footer_bits = ""
    if target_html:
        footer_bits += ('<span style="color:#64748B;font-size:8px;">Target</span>'
                        f'<span style="color:#B0BAC9;font-size:8.5px;font-weight:600;">'
                        f'{target_html}</span>')
    if gap_html:
        footer_bits += gap_html
    if rank_html:
        footer_bits += f'<span style="margin-left:auto;">{rank_html}</span>'

    return f"""
<div class="q3-kpi" style="--acc:{colour}; --acc-soft:{colour}26;">
  <!-- header: icon + title + severity -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <div style="width:24px;height:24px;flex-shrink:0;background:{colour}18;
                border-radius:6px;display:flex;align-items:center;justify-content:center;
                color:{colour};font-size:10px;">
      <i class="fa-solid {reading.icon}"></i>
    </div>
    <span style="color:#CBD5E1;font-size:9.5px;font-weight:600;flex:1;min-width:0;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
      {reading.title}</span>
    <span style="background:{sev['bg']};color:{sev['color']};font-size:7.5px;font-weight:700;
                 padding:2px 6px;border-radius:10px;white-space:nowrap;flex-shrink:0;">
      {sev['label']}</span>
  </div>

  {value_block}

  <!-- footer: target + gap + rank (only the parts that carry a value) -->
  <div class="q3-kpi-footer">{footer_bits}</div>
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
    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    rank_of = {d["key"]: d["rank"] for d in data["ranking"]}
    cols = st.columns(len(KPI_SPEC))
    for col, spec in zip(cols, KPI_SPEC):
        reading = readings.get(spec["key"])
        if reading is None:
            col.warning(f"{spec['code']}: no data")
            continue
        col.markdown(_kpi_card(reading, rank_of.get(spec["key"])), unsafe_allow_html=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # --- Row 1: where the energy is lost, and what we buy from abroad ---
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown(
            section_title("Visual 1 – Where the Energy Is Lost", "warning",
                          badge=f"{wf_year} · {e_u}"),
            unsafe_allow_html=True)
        st.caption(f"Energy the country gets in {wf_year}, split into the parts lost on the way and the part that actually reaches users ({e_u}).")
        st.plotly_chart(
            visual1_loss_waterfall(chart_series, wf_year, unit=e_u),
            use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown(
            section_title("Visual 2 – Energy We Import", "imports",
                          badge=f"{span} · {e_u}"),
            unsafe_allow_html=True)
        st.caption(f"How much energy arrives from abroad ({e_u}, bars) and what share of our total supply that is (line).")
        st.plotly_chart(
            visual2_import_dependence(chart_series, year_range, unit_energy=e_u),
            use_container_width=True, config={"displayModeBar": False})

    # --- Row 2: the gas shortfall, then all four targets on one chart ---
    r2c1, r2c2 = st.columns(2)
    gas_t = targets.get("gas_self_suff_pct", {})

    with r2c1:
        st.markdown(
            section_title("Visual 3 – Gas Made vs Gas Used", "gas",
                          badge=f"{span} · {g_u} · target {_num(gas_t.get('target')):.0f}%"),
            unsafe_allow_html=True)
        st.caption(f"Gas we pump from our own fields against gas we burn ({g_u}). The red dip below the bars is the amount we cannot cover.")
        st.plotly_chart(
            visual3_gas_balance(chart_series, year_range,
                                target=_num(gas_t.get("target")), unit_gas=g_u),
            use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown(
            section_title("Visual 4 – Distance to Each Target", "insights",
                          badge=span),
            unsafe_allow_html=True)
        st.caption("All four targets on one chart. A line above the middle means that target is met; below it means missed.")
        st.plotly_chart(
            visual4_gap_paths(data["timeline"], year_range,
                              _GAP_LABELS, _GAP_COLORS),
            use_container_width=True, config={"displayModeBar": False})

    # --- Visual 5: better or worse, first reported year to last reported ---
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    r3c1, _ = st.columns([1.6, 1])
    with r3c1:
        st.markdown(
            section_title("Visual 5 – Are the bottlenecks getting better or worse?",
                          "warning", badge="first reported → last reported"),
            unsafe_allow_html=True)
        st.caption("One line per metric. Green means it moved the right way over "
                   "the chosen years; red means it moved the wrong way.")
        st.plotly_chart(
            visual5_bottleneck_slope(chart_series, year_range),
            use_container_width=True, config={"displayModeBar": False})

    # ---- Bottom line ----
    ranking = data["ranking"]
    if not ranking:
        lines = ["Not enough readings in this year range to judge the targets."]
    else:
        top = ranking[0]
        missed = [d for d in ranking if not d["on_track"]]
        if top["gap"] < 0:
            lines = [
                f"Biggest hold-up: {top['title']}, {abs(top['gap']):.1f} "
                "percentage points short of its target.",
                f"{len(missed)} of {len(ranking)} checks are behind target here — "
                "the cards rank them worst first.",
            ]
        else:
            lines = [
                f"No target is missed in this view — {top['title']} has the least "
                "slack to lean on.",
                "All four checks are holding their targets.",
            ]
    st.markdown(conclusion_card(lines), unsafe_allow_html=True)

