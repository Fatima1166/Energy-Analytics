"""
Operational Bottlenecks dashboard (Question 9).

Q9: What are the operational bottlenecks in fossil and renewable energy supplies?

Thin presentation shell over the pure engine `core/operational_bottlenecks.py`:

    fetch frames (config.database.run_query)
        -> engine.build_bottleneck_frame   (per-year utilisation / supply / loss)
        -> engine.score_bottlenecks        (ranked 0-100 severity scorecard)
        -> engine.snapshot_metrics         (headline KPI values at base year)
        -> charts.py renders the engine outputs

This page contains NO analytics of its own.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import section_title
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
    aggregate_by_family,
    build_bottleneck_frame,
    score_bottlenecks,
    snapshot_metrics,
    FAMILY_COLORS,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from . import charts
from .config import (
    AMBER, BLUE, CYAN, GREEN, ORANGE, RED, SLATE,
    BASE_YEAR_MAX, BASE_YEAR_MIN, DEFAULT_BASE_YEAR,
    FAMILIES, FAMILY_COLORS as CFG_FAMILY_COLORS, FAMILY_ICONS,
    HISTORY_END, HISTORY_START,
)

_FILTERS_KEY = "q9_filters"
_CHART_CONFIG = {"displayModeBar": False}


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar() -> None:
    """Q9 controls – called by app.py before the global unit slicer."""
    st.sidebar.markdown(
        '<div class="dsh-side-title">Operational Bottleneck Setup</div>',
        unsafe_allow_html=True,
    )

    base_year = st.sidebar.slider(
        "Analysis Year",
        min_value=BASE_YEAR_MIN,
        max_value=BASE_YEAR_MAX,
        value=DEFAULT_BASE_YEAR,
        step=1,
        key="q9_base_year",
        help="The snapshot year the bottleneck scorecard is evaluated at. "
             f"Data runs {HISTORY_START}–{HISTORY_END}; each stream uses its "
             "latest available observation up to this year.",
    )

    family_keys = list(FAMILIES.keys())
    selected_families = st.sidebar.multiselect(
        "Bottleneck Families",
        family_keys,
        default=family_keys,
        format_func=lambda k: FAMILIES[k],
        key="q9_families",
        help="Which families of choke point to include in the scorecard: "
             "fossil supply, renewable supply, or grid delivery.",
    )
    if not selected_families:
        selected_families = family_keys

    min_severity = st.sidebar.slider(
        "Flag bottlenecks at severity ≥",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        key="q9_min_sev",
        help="Only show bottlenecks whose 0–100 severity meets this threshold. "
             "Raise it to cut through to the most binding constraints.",
    )

    st.session_state[_FILTERS_KEY] = {
        "base_year": int(base_year),
        "families": list(selected_families),
        "min_severity": int(min_severity),
    }
    st.sidebar.divider()


# ── KPI card (house style, self-contained inline styling) ────────────────────

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = BLUE, icon_name: str = "warning",
              badge: str = "", badge_colour: str = BLUE,
              bar_pct: float | None = None) -> str:
    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:9px;color:#94A3B8;padding:1px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (
        f'<span style="background:{badge_colour}22;color:{badge_colour};'
        f'font-size:8.5px;font-weight:700;padding:2px 8px;border-radius:20px;'
        f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
        if badge else ""
    )
    bar_html = ""
    if bar_pct is not None and np.isfinite(bar_pct):
        bar_html = (
            f'<div style="height:4px;background:#232830;border-radius:3px;'
            f'overflow:hidden;margin:3px 0 6px;">'
            f'<div style="height:100%;width:{min(max(bar_pct, 0), 100):.1f}%;'
            f'background:linear-gradient(90deg,{accent}88,{accent});border-radius:3px;"></div></div>'
        )
    return f"""
<div style="
    background: linear-gradient(135deg, rgba(22,27,38,0.95) 0%, rgba(14,18,26,0.98) 100%);
    border-radius: 14px;
    padding: 14px 14px 10px;
    height: 150px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    width: 100%;
    border: 1px solid {accent}55;
">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:28px;height:28px;background:{accent}22;border:1px solid {accent}44;
                  border-radius:8px;display:flex;align-items:center;justify-content:center;
                  color:{accent};font-size:11px;">{icon(icon_name)}</div>
      <div style="color:#94A3B8;font-size:8px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.6px;">{code}</div>
    </div>
    {badge_html}
  </div>
  <div style="color:#E2E8F0;font-size:10px;font-weight:600;line-height:1.25;
              margin-bottom:6px;min-height:26px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;">
    <span style="color:{accent};font-size:20px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  {bar_html}
  <div style="margin-top:auto;">{detail}</div>
</div>
"""


def _sev_color(sev: float) -> str:
    if not np.isfinite(sev):
        return SLATE
    if sev >= 66:
        return RED
    if sev >= 45:
        return ORANGE
    if sev >= 25:
        return AMBER
    return GREEN


def _dash(v: float, spec: str = ".1f") -> str:
    return "--" if not (isinstance(v, (int, float)) and np.isfinite(v)) else format(v, spec)


def _lv(snap: dict, key: str) -> float:
    v = snap.get(key, np.nan)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return np.nan
    return f


# ── Answer / verdict hero ────────────────────────────────────────────────────

def _answer_hero(scorecard: pd.DataFrame, base_year: int) -> str:
    if scorecard is None or scorecard.empty:
        return ""
    top = scorecard.iloc[0]
    fam_label = FAMILIES.get(top["family"], top["family"])
    fam_color = CFG_FAMILY_COLORS.get(top["family"], BLUE)
    sev = float(top["severity"])
    # next two ranked, as chips
    chips = ""
    for _, r in scorecard.iloc[1:4].iterrows():
        c = CFG_FAMILY_COLORS.get(r["family"], SLATE)
        chips += (
            f'<div style="display:flex;align-items:center;gap:8px;'
            f'background:rgba(148,163,184,0.06);border:1px solid {c}44;'
            f'border-radius:10px;padding:6px 12px;margin:3px 6px 3px 0;">'
            f'<span style="color:{c};font-weight:800;font-size:10px;'
            f'font-family:\'JetBrains Mono\',monospace;">{float(r["severity"]):.0f}</span>'
            f'<span style="color:#E2E8F0;font-size:11px;font-weight:600;">{r["name"]}</span>'
            f'<span style="color:#64748B;font-size:9.5px;">{r["reading"]}</span></div>'
        )
    return f"""
<div style="position:relative;background:linear-gradient(135deg,{fam_color}18,rgba(0,166,251,0.05) 45%,rgba(14,18,26,0.92));
            border:1px solid {fam_color}55;border-radius:16px;padding:18px 22px;margin-top:6px;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,{fam_color},#06B6D4,#F59E0B);border-radius:16px 16px 0 0;"></div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
    <div style="width:34px;height:34px;background:{fam_color}22;border:1px solid {fam_color}55;border-radius:10px;
                display:flex;align-items:center;justify-content:center;color:{fam_color};font-size:14px;">
      {icon("warning")}</div>
    <div>
      <div style="color:#94A3B8;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;">
        Answer to Question 9 — Most Binding Bottleneck ({base_year})</div>
      <div style="color:#E2E8F0;font-size:14px;font-weight:800;">
        <span style="color:{fam_color};">{top['name']}</span>
        is the tightest operational constraint at severity
        <span style="color:{fam_color};font-family:'JetBrains Mono',monospace;">{sev:.0f}/100</span>
        ({fam_label}) — currently <b>{top['reading']}</b>.
      </div>
    </div>
  </div>
  <div style="color:#94A3B8;font-size:11px;line-height:1.5;margin-bottom:8px;">{top['note']}</div>
  <div style="display:flex;flex-wrap:wrap;align-items:center;">{chips}</div>
</div>
"""


# ── Main render ──────────────────────────────────────────────────────────────

def render() -> None:
    """Renders the Q9 Operational Bottlenecks dashboard."""
    flt = st.session_state.get(_FILTERS_KEY, {})
    base_year = int(flt.get("base_year", DEFAULT_BASE_YEAR))
    families = flt.get("families", list(FAMILIES.keys()))
    min_sev = int(flt.get("min_severity", 0))

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
    if not scorecard.empty:
        scorecard = scorecard[scorecard["family"].isin(families)]
        scorecard = scorecard[scorecard["severity"] >= min_sev].reset_index(drop=True)
    snap = snapshot_metrics(df, base_year)
    fam_sev = aggregate_by_family(scorecard)

    # ── 3. Units ─────────────────────────────────────────────────────────────
    units = get_units()
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_power = units.get("power", "MW")
    factor_power = display_factor("power", unit_power)
    unit_gas = units.get("gas", "BCF")
    factor_gas = display_factor("gas", unit_gas)

    lf = _lv(snap, "sys_load_factor_pct")
    fossil_cf = _lv(snap, "fossil_cf_pct")
    re_cf = _lv(snap, "re_cf_pct")
    gas_ss = _lv(snap, "gas_self_suff_pct")
    gas_gap = _lv(snap, "gas_gap_bcf")
    td_loss = _lv(snap, "td_loss_pct")
    import_dep = _lv(snap, "fossil_import_dep_pct")
    undelivered = _lv(snap, "undelivered_gwh")
    yr = int(snap.get("year", base_year))

    # ═══════════════════════ KPI Strip ═══════════════════════
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.markdown(_kpi_card(
            code="OB1", title="System Load Factor",
            value=_dash(lf), unit="% · " + str(yr),
            rows=[("Nameplate", f"{fmt(_lv(snap, 'total_cap_mw') * factor_power, 0)} {unit_power}", "#94A3B8"),
                  ("Undelivered", f"{fmt(undelivered * factor_elec, 0)} {unit_elec}", RED),
                  ("Gap vs 85%", _dash(85 - lf) + " pts", AMBER)],
            accent=_sev_color(100 - lf if np.isfinite(lf) else np.nan),
            icon_name="intensity",
            badge="Utilisation", badge_colour=BLUE,
            bar_pct=lf,
        ), unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(_kpi_card(
            code="OB2", title="Fossil / Thermal Capacity Factor",
            value=_dash(fossil_cf), unit="% cap factor",
            rows=[("Family", "Fossil Supply", ORANGE),
                  ("Undelivered cap", _dash((fossil_cf - 60) if np.isfinite(fossil_cf) else np.nan) + " pts vs target", AMBER),
                  ("Import Depend.", _dash(import_dep) + "%", RED)],
            accent=ORANGE, icon_name="primary_energy",
            badge="Fossil", badge_colour=ORANGE,
            bar_pct=fossil_cf,
        ), unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(_kpi_card(
            code="OB3", title="Renewable Capacity Factor",
            value=_dash(re_cf), unit="% cap factor",
            rows=[("Family", "Renewable Supply", GREEN),
                  ("RE Capacity", f"{fmt(_lv(snap, 're_cap_mw') * factor_power, 0)} {unit_power}", "#94A3B8"),
                  ("RE Generation", f"{fmt(_lv(snap, 're_gen_gwh') * factor_elec, 0)} {unit_elec}", GREEN)],
            accent=GREEN, icon_name="renewables",
            badge="Renewable", badge_colour=GREEN,
            bar_pct=re_cf,
        ), unsafe_allow_html=True)
    with kpi_cols[3]:
        st.markdown(_kpi_card(
            code="OB4", title="Gas Self-Sufficiency",
            value=_dash(gas_ss), unit="% · " + str(yr),
            rows=[("Family", "Fossil Supply", ORANGE),
                  ("Supply Gap", f"{fmt(gas_gap * factor_gas, 1)} {unit_gas}", RED),
                  ("Shortfall met by", "LNG imports", AMBER)],
            accent=_sev_color(100 - gas_ss if np.isfinite(gas_ss) else np.nan),
            icon_name="gas",
            badge="Fossil", badge_colour=ORANGE,
            bar_pct=gas_ss,
        ), unsafe_allow_html=True)
    with kpi_cols[4]:
        st.markdown(_kpi_card(
            code="OB5", title="T&D Delivery Losses",
            value=_dash(td_loss), unit="% of gen",
            rows=[("Family", "Grid Delivery", CYAN),
                  ("Benchmark", "15.0%", "#94A3B8"),
                  ("Over benchmark", _dash((td_loss - 15) if np.isfinite(td_loss) else np.nan) + " pts",
                   RED if (np.isfinite(td_loss) and td_loss > 15) else GREEN)],
            accent=CYAN, icon_name="supply",
            badge="Delivery", badge_colour=CYAN,
            bar_pct=(td_loss / 25 * 100) if np.isfinite(td_loss) else None,
        ), unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ═══════════════════════ Answer + Scorecard ═══════════════════════
    st.markdown(
        section_title("Where the Supply System Is Choked", "warning", "Step 1 · Diagnose"),
        unsafe_allow_html=True,
    )
    st.markdown(_answer_hero(scorecard, yr), unsafe_allow_html=True)
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.caption(
            "Every bottleneck ranked 0–100 by how badly it limits supply — the tallest bar is the biggest problem."
        )
        st.plotly_chart(charts.visual1_severity_scorecard(scorecard, yr),
                        use_container_width=True, config=_CHART_CONFIG)
    with c2:
        st.caption(
            "How much power each source really delivers vs its capacity — flat, low lines mean a long-term bottleneck."
        )
        st.plotly_chart(charts.visual2_capacity_factor_trend(df),
                        use_container_width=True, config=_CHART_CONFIG)

    # ═══════════════════════ Physical gap charts ═══════════════════════
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        section_title("Fossil Supply Gaps", "primary_energy", "Step 2 · Quantify"),
        unsafe_allow_html=True,
    )
    c3, c4 = st.columns(2)
    with c3:
        st.caption(
            "Energy the system could make vs what it actually makes — the gap is wasted capacity."
        )
        st.plotly_chart(charts.visual3_capability_gap(df, factor_elec, unit_elec),
                        use_container_width=True, config=_CHART_CONFIG)
    with c4:
        st.caption(
            "Gas we use vs gas we produce at home — the shaded gap is filled by costly LNG imports."
        )
        st.plotly_chart(charts.visual4_gas_supply_gap(df, factor_gas, unit_gas),
                        use_container_width=True, config=_CHART_CONFIG)

    # ═══════════════════════ Delivery + Renewable conversion ═══════════════════════
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        section_title("Delivery Losses & Renewable Conversion", "supply", "Step 3 · Trace"),
        unsafe_allow_html=True,
    )
    c5, c6 = st.columns(2)
    with c5:
        st.caption(
            "Power lost in transmission and distribution — anything above the 15% line never reaches consumers."
        )
        st.plotly_chart(charts.visual5_td_loss_drain(df),
                        use_container_width=True, config=_CHART_CONFIG)
    with c6:
        st.caption(
            "Renewable capacity (bars) is growing faster than real output (line) — the widening gap shows grid limits."
        )
        st.plotly_chart(charts.visual6_re_capability_output(df, factor_power, unit_power,
                                                            factor_elec, unit_elec),
                        use_container_width=True, config=_CHART_CONFIG)

    # ═══════════════════════ Family rollup + source map ═════════════════
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        section_title("Bottleneck Focus by Family & Source", "warning", "Step 4 · Focus"),
        unsafe_allow_html=True,
    )
    c7, c8 = st.columns(2)
    with c7:
        st.caption(
            "Average severity of each family — shows whether fossil, renewable or grid supply is the dominant choke point."
        )
        st.plotly_chart(charts.visual7_family_severity_summary(fam_sev, scorecard),
                        use_container_width=True, config=_CHART_CONFIG)
    with c8:
        st.caption(
            "Each source plotted by capacity vs capacity factor, bubble size = trapped energy — big, low-efficiency sources are the priority bottlenecks."
        )
        st.plotly_chart(charts.visual8_source_bottleneck_map(df, base_year, factor_power, unit_power, factor_elec, unit_elec),
                        use_container_width=True, config=_CHART_CONFIG)

    # ═══════════════════════ Insights ═══════════════════════
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown(
        section_title("Operational Bottleneck Findings", "insights", "Synthesis"),
        unsafe_allow_html=True,
    )

    top = scorecard.iloc[0] if (scorecard is not None and not scorecard.empty) else None
    worst_fam = max(
        ((k, v) for k, v in fam_sev.items() if np.isfinite(v)),
        key=lambda kv: kv[1], default=(None, np.nan),
    )

    insight_cards = []
    if top is not None:
        insight_cards.append({
            "icon": "warning", "color": CFG_FAMILY_COLORS.get(top["family"], RED),
            "title": f"Tightest bottleneck: {top['name']}",
            "value": f"{float(top['severity']):.0f} / 100",
            "text": (f"Measured at {top['reading']} in {yr}. {top['note']} "
                     "Relieving this constraint releases the most trapped supply capacity."),
        })
    insight_cards.append({
        "icon": "primary_energy", "color": ORANGE,
        "title": "Fossil supply: fuel & import exposure",
        "value": (f"{_dash(fossil_cf)}% CF" if np.isfinite(fossil_cf) else "--"),
        "text": (f"Thermal plant runs at {_dash(fossil_cf)}% capacity factor while gas self-sufficiency "
                 f"sits at {_dash(gas_ss)}% and fossil import dependence at {_dash(import_dep)}% — "
                 "capacity is built but starved of affordable domestic fuel."),
    })
    insight_cards.append({
        "icon": "renewables", "color": GREEN,
        "title": "Renewable supply: capability not converting",
        "value": (f"{_dash(re_cf)}% CF" if np.isfinite(re_cf) else "--"),
        "text": (f"Renewables deliver {_dash(re_cf)}% capacity factor against rising installed "
                 f"{fmt(_lv(snap, 're_cap_mw') * factor_power, 0)} {unit_power}. Intermittency and grid "
                 "integration — not capital — are the binding constraint on renewable supply."),
    })

    i_cols = st.columns(max(1, len(insight_cards)))
    for col, ins in zip(i_cols, insight_cards):
        with col:
            st.markdown(
                f"""<div style="background:linear-gradient(135deg,rgba(22,27,38,0.95),rgba(14,18,26,0.98));
                    border:1px solid {ins['color']}44;border-radius:14px;padding:16px;height:100%;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                    <div style="width:32px;height:32px;background:{ins['color']}22;border:1px solid {ins['color']}55;
                                border-radius:8px;display:flex;align-items:center;justify-content:center;
                                color:{ins['color']};font-size:13px;">{icon(ins['icon'])}</div>
                    <div style="color:#E2E8F0;font-size:11.5px;font-weight:700;">{ins['title']}</div>
                  </div>
                  <div style="color:{ins['color']};font-size:17px;font-weight:800;
                              font-family:'JetBrains Mono',monospace;margin-bottom:8px;">{ins['value']}</div>
                  <div style="color:#94A3B8;font-size:11px;line-height:1.55;">{ins['text']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

