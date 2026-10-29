"""
Operational Bottlenecks dashboard (Question 9).

Q9: What are the operational bottlenecks in fossil and renewable energy supplies?

Thin presentation shell over the pure engine `core/operational_bottlenecks.py`:

    fetch frames (config.database.run_query)
        -> engine.build_bottleneck_frame   (per-year utilisation / supply / loss)
        -> engine.score_bottlenecks        (ranked 0-100 severity scorecard)
        -> engine.snapshot_metrics         (headline values, each its own year)
        -> charts.py renders the engine outputs

What is left on the page is the question and nothing more: three cards, four
charts in two rows.  No analytics and no prose verdict live here.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.icons import icon
from core.queries import (
    Q_ELEC_GEN,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_CAPACITY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.operational_bottlenecks import (
    build_bottleneck_frame,
    score_bottlenecks,
    snapshot_metrics,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from . import charts
from .config import (
    AMBER, BLUE, GREEN, ORANGE, RED,
    BASE_YEAR_MAX, BASE_YEAR_MIN, DEFAULT_BASE_YEAR,
    HISTORY_END, HISTORY_START,
)

_FILTERS_KEY = "q9_filters"
_CHART_CONFIG = {"displayModeBar": False}

_MUTED = "#94A3B8"
_TEXT = "#CBD5E1"

# The source behind each "weakest link" row, in words a reader already knows.
SOURCE_WORDS = {"solar_cf": "Solar", "wind_cf": "Wind", "hydro_cf": "Hydro"}

# Cards are sized by their own content.  The shared skin pins a fixed height and
# pushes the footer rows to the bottom, which leaves a dead band under the number
# whenever a card has fewer rows than the tallest one in the row.
_CARD_CSS = """
<style>
  .kpi-balance.q9-kpi {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      justify-content: flex-start !important;
      padding: 13px 14px 12px !important;
  }
  .kpi-balance.q9-kpi .kpi-balance-details { margin-top: 0 !important; }
</style>
"""


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar() -> None:
    """Q9 controls – called by app.py before the global unit slicer.

    One knob only: the year to judge the system as at.  Which measures answer
    the question is fixed, so family and severity filters would only hide rows
    the ranking already sorts for the reader.
    """
    st.sidebar.markdown('<div class="dsh-side-title">Operational Bottlenecks</div>',
                        unsafe_allow_html=True)

    base_year = st.sidebar.slider(
        "Year to judge",
        min_value=BASE_YEAR_MIN,
        max_value=BASE_YEAR_MAX,
        value=DEFAULT_BASE_YEAR,
        step=1,
        key="q9_base_year",
        help="Everything is read no later than this year.  Each measure then uses "
             "the newest year it actually has data for -- some series (like gas "
             f"reserves) stop earlier.  Data runs {HISTORY_START}–{HISTORY_END}.",
    )

    st.session_state[_FILTERS_KEY] = {"base_year": int(base_year)}
    st.sidebar.divider()


# ── KPI card (house style) ────────────────────────────────────────────────────

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = BLUE, icon_name: str = "warning",
              badge: str = "", badge_colour: str = BLUE) -> str:
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
<div class="kpi-balance q9-kpi" style="border: 1px solid {accent}44;">
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


def _lv(snap: dict, key: str) -> float:
    try:
        return float(snap.get(key, np.nan))
    except (TypeError, ValueError):
        return np.nan


def _yr(snap: dict, key: str) -> int | None:
    """The year this measure was actually read in."""
    y = snap.get(f"{key}_year")
    return int(y) if isinstance(y, (int, float)) and np.isfinite(float(y)) else None


def _row(label: str, text: str, colour: str, snap: dict, key: str,
         anchor: int | None) -> tuple:
    """A card row that names its own year when that year differs from the card."""
    y = _yr(snap, key)
    if y and anchor and y != anchor:
        label = f"{label} ({y})"
    return (label, text, colour)


def _weakest(scorecard, ids: dict) -> str | None:
    """The most binding clean-source row as "Solar 20.8%", or None if unreadable."""
    if scorecard is None or scorecard.empty:
        return None
    sub = scorecard[scorecard["id"].isin(ids)].dropna(subset=["severity"])
    if sub.empty:
        return None
    top = sub.iloc[0]
    value = float(top["metric_value"])
    if not np.isfinite(value):
        return None
    return f"{ids[top['id']]} {value:.1f}%"


# ── Main render ──────────────────────────────────────────────────────────────

def render() -> None:
    """Renders the Q9 Operational Bottlenecks dashboard."""
    base_year = int(st.session_state.get(_FILTERS_KEY, {})
                    .get("base_year", DEFAULT_BASE_YEAR))

    # ── 1. Fetch raw frames (the only I/O in this module) ────────────────────
    try:
        df = build_bottleneck_frame(
            gen_df=run_query(Q_ELEC_GEN),
            re_df=run_query(Q_RENEWABLE_ENERGY),
            re_cap_df=run_query(Q_RENEWABLE_CAPACITY),
            td_df=run_query(Q_TD_LOSSES),
            gas_df=run_query(Q_NATURAL_GAS),
            ps_df=run_query(Q_PRIMARY_SUPPLY),
        )
    except Exception as exc:  # pragma: no cover — presentation guard
        st.error(f"Bottleneck engine failed: {exc}")
        return
    if df.empty:
        st.warning("No operational data available — check the MySQL connection.")
        return

    # ── 2. Engine calls ──────────────────────────────────────────────────────
    scorecard = score_bottlenecks(df, base_year)
    snap = snapshot_metrics(df, base_year)

    # ── 3. Units ─────────────────────────────────────────────────────────────
    units = get_units()
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_power = units.get("power", "MW")
    factor_power = display_factor("power", unit_power)
    unit_gas = units.get("gas", "BCF")
    factor_gas = display_factor("gas", unit_gas)

    lf = _lv(snap, "sys_load_factor_pct")
    lf_year = _yr(snap, "sys_load_factor_pct") or base_year
    fossil_cf = _lv(snap, "fossil_cf_pct")
    fossil_year = _yr(snap, "fossil_cf_pct")
    re_cf = _lv(snap, "re_cf_pct")
    re_year = _yr(snap, "re_cf_pct")

    weak_reading = _weakest(scorecard, SOURCE_WORDS)

    # ═══════════════════════ Three cards across four slots ═══════════════════
    # The fourth slot stays empty so each card keeps a four-up row's width.
    cards = [
        _kpi_card(
            code="K1",
            title="Whole system: how much gets made",
            value=_dash(lf),
            unit=f"% of what it could make · {lf_year}",
            rows=[
                _row("Plant built",
                     f"{fmt(_lv(snap, 'total_cap_mw') * factor_power, 0)} {unit_power}",
                     _MUTED, snap, "total_cap_mw", lf_year),
                _row("Power made",
                     f"{fmt(_lv(snap, 'total_gen_gwh') * factor_elec, 0)} {unit_elec}",
                     BLUE, snap, "total_gen_gwh", lf_year),
                _row("Power never made",
                     f"{fmt(_lv(snap, 'undelivered_gwh') * factor_elec, 0)} {unit_elec}",
                     RED, snap, "undelivered_gwh", lf_year),
            ],
            accent=BLUE, icon_name="intensity",
            badge="Utilisation", badge_colour=BLUE,
        ),
        _kpi_card(
            code="K2",
            title="Fossil supply: idle plant, bought fuel",
            value=_dash(fossil_cf),
            unit=f"% of what it could make · {fossil_year or base_year}",
            rows=[
                _row("Home gas met", _dash(_lv(snap, "gas_self_suff_pct")) + "%",
                     GREEN, snap, "gas_self_suff_pct", fossil_year),
                _row("Gas short by",
                     f"{fmt(_lv(snap, 'gas_gap_bcf') * factor_gas, 1)} {unit_gas}",
                     RED, snap, "gas_gap_bcf", fossil_year),
                _row("Fuel bought abroad",
                     _dash(_lv(snap, "fossil_import_dep_pct")) + "%",
                     AMBER, snap, "fossil_import_dep_pct", fossil_year),
            ],
            accent=ORANGE, icon_name="primary_energy",
            badge="Fossil supply", badge_colour=ORANGE,
        ),
        _kpi_card(
            code="K3",
            title="Clean supply: plant built, power made",
            value=_dash(re_cf),
            unit=f"% of what it could make · {re_year or base_year}",
            rows=[
                _row("Plant built",
                     f"{fmt(_lv(snap, 're_cap_mw') * factor_power, 0)} {unit_power}",
                     _MUTED, snap, "re_cap_mw", re_year),
                _row("Power made",
                     f"{fmt(_lv(snap, 're_gen_gwh') * factor_elec, 0)} {unit_elec}",
                     GREEN, snap, "re_gen_gwh", re_year),
                ("Weakest clean source", weak_reading or "--", RED),
            ],
            accent=GREEN, icon_name="renewables",
            badge="Renewable supply", badge_colour=GREEN,
        ),
    ]

    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 1 -- which choke point hurts most   Visual 2 -- how long it has run
    # ══════════════════════════════════════════════════════════════════════
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(section_title("Visual 1 – Which choke point hurts most",
                                  "warning", badge=f"read up to {base_year}"),
                    unsafe_allow_html=True)
        st.caption("How badly each choke point limits supply. Hover shows its "
                   "reading and the year it came from.")
        st.plotly_chart(charts.visual1_severity_scorecard(scorecard),
                        use_container_width=True, config=_CHART_CONFIG)
    with c2:
        st.markdown(section_title("Visual 2 – How long plant has sat idle",
                                  "intensity",
                                  badge=f"{HISTORY_START}–{HISTORY_END}"),
                    unsafe_allow_html=True)
        st.caption("What each kind of plant makes as a share of its size. Low and "
                   "flat means a lasting bottleneck.")
        st.plotly_chart(charts.visual2_capacity_factor_trend(df),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 3 -- the trapped energy             Visual 4 -- the gas shortfall
    # ══════════════════════════════════════════════════════════════════════
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(section_title("Visual 3 – The power that never came out",
                                  "generation", badge=f"to {lf_year}"),
                    unsafe_allow_html=True)
        st.caption("Grey is what the plant could make in a year, blue is what it "
                   "made. The gap in between is idle.")
        st.plotly_chart(charts.visual3_capability_gap(df, factor_elec, unit_elec),
                        use_container_width=True, config=_CHART_CONFIG)
    with c4:
        st.markdown(section_title("Visual 4 – The gas shortfall", "gas",
                                  badge=f"to {_yr(snap, 'gas_gap_bcf') or base_year}"),
                    unsafe_allow_html=True)
        st.caption("Orange is gas used, green is gas made at home. The shaded gap "
                   "has to be bought as LNG.")
        st.plotly_chart(charts.visual4_gas_supply_gap(df, factor_gas, unit_gas),
                        use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    lf_txt = _dash(lf)
    if lf_txt != "--":
        line1 = (f"Plant across the country ran at {lf_txt}% of its size in "
                 f"{lf_year} — the rest of the built capacity sat idle.")
    else:
        line1 = "No load-factor reading for this year yet."
    gap_raw = _lv(snap, "gas_gap_bcf")
    if np.isfinite(gap_raw):
        line2 = (f"Home gas meets {_dash(_lv(snap, 'gas_self_suff_pct'))}% of what "
                 f"is used; about {_dash(gap_raw * factor_gas, ',.1f')} {unit_gas} "
                 "a year still has to arrive as imported LNG.")
    else:
        line2 = "Gas balance is not reported for this year yet."
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
