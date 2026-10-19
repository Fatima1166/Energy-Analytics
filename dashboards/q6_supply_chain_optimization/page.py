"""
Supply Chain Optimization dashboard (Question 6).

Q6: What is the optimal utilization of fuel and renewable energy supply chains?

This dashboard analyzes:
  1. Supply-chain efficiency scorecard (radar) across 5 KPI dimensions
  2. T&D transmission loss trend and grid efficiency gap vs user benchmark
  3. Fuel import dependency vs domestic supply across selectable fuel streams
  4. Renewable capacity utilisation rates (installed MW vs generated GWh)
  5. Gas supply chain: production, consumption & LNG dependency (unit-aware)
  6. LNG cost efficiency (cost per unit volume)
  7. Composite supply-chain optimization score (1999–2024) across strategy weights
  8. What-if optimal fuel vs renewable generation mix simulator
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
    Q_LNG,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.unit_slicer import get_units
from core.units import display_factor, fmt

from .charts import (
    visual1_radar_scorecard,
    visual2_td_loss_trend,
    visual3_import_dependency,
    visual4_re_utilisation,
    visual5_gas_supply_chain,
    visual6_lng_cost,
    visual7_optimization_score,
    visual8_optimal_mix,
)
from .config import (
    BENCHMARK_FUEL_WASTE_MAX,
    BENCHMARK_GAS_SELFSUFFICIENCY,
    BENCHMARK_IMPORT_DEPENDENCY_MAX,
    BENCHMARK_RE_UTILISATION_MIN,
    BENCHMARK_TRANSMISSION_EFFICIENCY,
    FUEL_STREAM_MAP,
    GREEN, BLUE, AMBER, RED, PURPLE, TEAL, CYAN, ORANGE,
    PRIORITY_WEIGHTS,
    SCE_WEIGHTS,
    STRATEGY_PRESETS,
)

_FILTERS_KEY = "q6_filters"
_CHART_CONFIG = {"displayModeBar": False}


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar() -> None:
    """Supply chain controls – called by app.py before the global unit slicer."""
    st.sidebar.markdown(
        '<div class="dsh-side-title">Supply Chain Optimization Setup</div>',
        unsafe_allow_html=True,
    )

    strategy_options = list(STRATEGY_PRESETS.keys())
    selected_strategy = st.sidebar.selectbox(
        "Optimization Strategy",
        strategy_options,
        index=0,
        key="q6_strategy",
        help="Select a supply chain optimization pathway or choose Custom Policy Mix.",
    )

    preset = STRATEGY_PRESETS[selected_strategy]

    # Synchronize default presets when user switches strategy
    last_strategy = st.session_state.get("_q6_last_strategy")
    if last_strategy != selected_strategy:
        st.session_state["_q6_last_strategy"] = selected_strategy
        if selected_strategy != "Custom Policy Mix":
            st.session_state["q6_re_target"] = preset["re_target"]
            st.session_state["q6_loss_target"] = preset["loss_target"]

    year_range = st.sidebar.slider(
        "Analysis Period",
        min_value=1999,
        max_value=2024,
        value=(2002, 2024),
        step=1,
        key="q6_year_range",
        help="Filter historical supply chain data window (1999–2024). KPIs evaluate the final year.",
    )

    # Supply & Fuel streams filter
    all_stream_names = list(FUEL_STREAM_MAP.keys())

    with st.sidebar.expander("Advanced Policy Controls", expanded=False):
        selected_streams = st.multiselect(
            "Supply & Fuel Streams",
            all_stream_names,
            default=all_stream_names,
            key="q6_streams",
            help="Filter which primary fuel and power supply streams are included in the import dependency and balance calculations.",
        )
        if not selected_streams:
            selected_streams = all_stream_names

        # Target RE Generation Share
        re_kw = {} if "q6_re_target" in st.session_state else {"value": preset["re_target"]}
        re_target = st.slider(
            "Target RE Generation Share (%)",
            min_value=20,
            max_value=85,
            step=5,
            key="q6_re_target",
            help="Target renewable generation share (hydro + solar + wind) for the optimal mix simulator.",
            **re_kw,
        )
        fuel_target = 100 - re_target

        # Transmission Loss Benchmark
        loss_kw = {} if "q6_loss_target" in st.session_state else {"value": preset["loss_target"]}
        loss_target = st.slider(
            "Target T&D Loss Benchmark (%)",
            min_value=8.0,
            max_value=22.0,
            step=0.5,
            key="q6_loss_target",
            help="Benchmark loss percentage used for grid transmission scoring (Default standard: 15.0%).",
            **loss_kw,
        )

    # Priority is derived from the selected strategy preset
    priority = preset["priority"]

    st.session_state[_FILTERS_KEY] = {
        "strategy": selected_strategy,
        "year_range": year_range,
        "selected_streams": selected_streams,
        "re_target": re_target,
        "fuel_target": fuel_target,
        "loss_target": loss_target,
        "priority": priority,
    }
    st.sidebar.divider()


# ── KPI card ─────────────────────────────────────────────────────────────────

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = BLUE, icon_name: str = "supply",
              badge: str = "", badge_colour: str = BLUE) -> str:
    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:9px;color:#94A3B8;padding:1px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (
        f'<span style="background:{badge_colour}22;color:{badge_colour};'
        f'font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;'
        f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
        if badge else ""
    )
    return f"""
<div class="kpi-balance" style="border: 1px solid {accent}44;">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
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
              margin-bottom:6px;min-height:28px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:8px;">
    <span style="color:{accent};font-size:23px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details" style="margin-top:auto;">{detail}</div>
</div>
"""


# ── Data helpers ──────────────────────────────────────────────────────────────

def _compute_td_combined(gen_df: pd.DataFrame, td_df: pd.DataFrame) -> pd.DataFrame:
    """Merge generation + T&D losses into one frame."""
    if gen_df.empty or td_df.empty:
        return pd.DataFrame()
    merged = pd.merge(
        gen_df[["calendar_year", "generation_gwh", "installed_capacity_mw"]].rename(
            columns={"generation_gwh": "gen_gwh", "installed_capacity_mw": "capacity_mw"}
        ),
        td_df[["calendar_year", "td_losses_gwh"]],
        on="calendar_year", how="inner",
    )
    return merged.sort_values("calendar_year").reset_index(drop=True)


def _compute_import_dep(ps_df: pd.DataFrame, allowed_sources: list | None = None) -> pd.DataFrame:
    """Aggregate primary supply into domestic vs imported per year for selected streams."""
    if ps_df.empty:
        return pd.DataFrame()
    df = ps_df.copy()
    if allowed_sources:
        df = df[df["source_name"].isin(allowed_sources)]
    if df.empty:
        return pd.DataFrame()

    agg = df.groupby("calendar_year", as_index=False).agg(
        domestic_supply_toe=("supply_toe", "sum"),
        imports_toe=("imports_toe", "sum"),
    )
    return agg.sort_values("calendar_year").reset_index(drop=True)


def _compute_scores(td_combined: pd.DataFrame, import_dep: pd.DataFrame,
                    re_df: pd.DataFrame, gas_df: pd.DataFrame,
                    year_range: tuple,
                    weights: dict,
                    target_loss_benchmark: float = 15.0) -> pd.DataFrame:
    """
    Compute normalised supply-chain KPI scores (0-100) per year.
    Higher = better for all dimensions.
    """
    years = list(range(year_range[0], year_range[1] + 1))
    target_eff_benchmark = 100.0 - target_loss_benchmark

    records = []
    for yr in years:
        row = {"calendar_year": yr}

        # 1. Transmission efficiency (benchmark-aware)
        td_row = td_combined[td_combined["calendar_year"] == yr] if not td_combined.empty else pd.DataFrame()
        if not td_row.empty:
            gen = float(td_row.iloc[0]["gen_gwh"])
            loss = float(td_row.iloc[0]["td_losses_gwh"])
            eff = (1 - loss / gen) * 100 if gen > 0 else 0.0
            row["transmission_efficiency"] = min(eff / target_eff_benchmark * 100, 100.0)
        else:
            row["transmission_efficiency"] = np.nan

        # 2. RE utilisation (proxy: RE gen fraction of total capacity × ideal CF)
        re_row = re_df[re_df["calendar_year"] == yr] if not re_df.empty else pd.DataFrame()
        if not re_row.empty:
            cap = float(re_row.iloc[0].get("capacity_mw", 0) or 0)
            re_gen = float((re_row.iloc[0].get("gen_solar_gwh", 0) or 0) +
                           (re_row.iloc[0].get("gen_wind_gwh", 0) or 0) +
                           (re_row.iloc[0].get("gen_hydro_gwh", 0) or 0))
            theoretical = cap * 8760 / 1000
            util = (re_gen / theoretical * 100) if theoretical > 0 else 0.0
            row["re_utilisation"] = min(util / BENCHMARK_RE_UTILISATION_MIN * 100, 100.0)
        else:
            row["re_utilisation"] = np.nan

        # 3. Import independence (lower import dep = higher score)
        imp_row = import_dep[import_dep["calendar_year"] == yr] if not import_dep.empty else pd.DataFrame()
        if not imp_row.empty:
            dom = float(imp_row.iloc[0].get("domestic_supply_toe", 0) or 0)
            imp = float(imp_row.iloc[0].get("imports_toe", 0) or 0)
            dep_pct = (imp / (dom + imp) * 100) if (dom + imp) > 0 else 0.0
            score = max(0.0, (BENCHMARK_IMPORT_DEPENDENCY_MAX - dep_pct) /
                        BENCHMARK_IMPORT_DEPENDENCY_MAX * 100.0 + 50.0)
            row["import_dependency"] = min(score, 100.0)
        else:
            row["import_dependency"] = np.nan

        # 4. Fuel waste reduction (lower loss % = higher score)
        if not td_row.empty:
            gen = float(td_row.iloc[0]["gen_gwh"])
            loss = float(td_row.iloc[0]["td_losses_gwh"])
            loss_pct = (loss / gen * 100) if gen > 0 else 100.0
            row["fuel_waste_reduction"] = max(0.0, min(
                (target_loss_benchmark - loss_pct) / target_loss_benchmark * 100.0 + 50.0, 100.0))
        else:
            row["fuel_waste_reduction"] = np.nan

        # 5. Gas self-sufficiency
        gas_row = gas_df[gas_df["calendar_year"] == yr] if not gas_df.empty else pd.DataFrame()
        if not gas_row.empty:
            prod = float(gas_row.iloc[0].get("production_bcf", 0) or 0)
            cons = float(gas_row.iloc[0].get("consumption_bcf", 0) or 0)
            ss = (prod / cons * 100) if cons > 0 else 100.0
            row["gas_self_sufficiency"] = min(ss / BENCHMARK_GAS_SELFSUFFICIENCY * 100.0, 100.0)
        else:
            row["gas_self_sufficiency"] = np.nan

        # Composite weighted score using active strategy weights
        composite = 0.0
        total_w = 0.0
        for dim, w in weights.items():
            v = row.get(dim, np.nan)
            if not np.isnan(v):
                composite += v * w
                total_w += w
        row["composite_score"] = composite / total_w if total_w > 0 else np.nan

        records.append(row)

    return pd.DataFrame(records)


# ── Main render ───────────────────────────────────────────────────────────────

def render() -> None:
    """Renders the Q6 Supply Chain Optimization dashboard."""
    flt = st.session_state.get(_FILTERS_KEY, {})
    strategy = flt.get("strategy", "Balanced Optimization")
    year_range = flt.get("year_range", (2002, 2024))
    selected_streams = flt.get("selected_streams", list(FUEL_STREAM_MAP.keys()))
    re_target = flt.get("re_target", 40)
    fuel_target = flt.get("fuel_target", 60)
    loss_target = flt.get("loss_target", 15.0)
    priority = flt.get("priority", "Balanced (Equal Emphasis)")

    # Resolve database source_name filters
    allowed_sources = []
    for stream in selected_streams:
        allowed_sources.extend(FUEL_STREAM_MAP.get(stream, []))
    if not allowed_sources:
        allowed_sources = None

    active_weights = PRIORITY_WEIGHTS.get(priority, SCE_WEIGHTS)
    target_year = int(year_range[1])

    # ── Fetch raw data ────────────────────────────────────────────────────────
    re_df = run_query(Q_RENEWABLE_ENERGY)
    gen_df = run_query(Q_ELEC_GEN)
    td_df = run_query(Q_TD_LOSSES)
    ps_df = run_query(Q_PRIMARY_SUPPLY)
    gas_df = run_query(Q_NATURAL_GAS)
    lng_df = run_query(Q_LNG)

    # ── Filter to selected year range ─────────────────────────────────────────
    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "calendar_year" not in df.columns:
            return df
        return df[(df["calendar_year"] >= year_range[0]) &
                  (df["calendar_year"] <= year_range[1])].copy()

    re_filt = _filter(re_df)
    gen_filt = _filter(gen_df)
    td_filt = _filter(td_df)
    ps_filt = _filter(ps_df)
    gas_filt = _filter(gas_df)
    lng_filt = _filter(lng_df)

    # ── Units ─────────────────────────────────────────────────────────────────
    units = get_units()
    unit_energy = units.get("energy", "TOE")
    factor_energy = display_factor("energy", unit_energy)
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_power = units.get("power", "MW")
    factor_power = display_factor("power", unit_power)
    unit_gas = units.get("gas", "BCF")
    factor_gas = display_factor("gas", unit_gas)

    # ── Derived frames ────────────────────────────────────────────────────────
    td_combined = _compute_td_combined(gen_filt, td_filt)
    import_dep = _compute_import_dep(ps_filt, allowed_sources)
    score_df = _compute_scores(td_combined, import_dep, re_filt, gas_filt,
                               year_range, active_weights, loss_target)

    # ── Target year snapshot for KPIs and Scorecard ───────────────────────────
    target_score_df = score_df[score_df["calendar_year"] == target_year]
    if target_score_df.empty:
        target_score_df = score_df.iloc[[-1]] if not score_df.empty else pd.DataFrame()

    def _lv(col: str, default: float = 0.0) -> float:
        if target_score_df.empty or col not in target_score_df.columns:
            return default
        v = target_score_df.iloc[0].get(col, default)
        return float(v) if not pd.isna(v) else default

    composite = _lv("composite_score", 55.0)
    tx_eff = _lv("transmission_efficiency", 70.0)
    re_util = _lv("re_utilisation", 30.0)
    imp_ind = _lv("import_dependency", 50.0)
    fuel_waste = _lv("fuel_waste_reduction", 60.0)
    gas_ss = _lv("gas_self_sufficiency", 65.0)

    # T&D loss rate at target year
    td_target = td_combined[td_combined["calendar_year"] == target_year]
    if not td_target.empty:
        r_td = td_target.iloc[0]
        loss_pct_raw = (r_td["td_losses_gwh"] / r_td["gen_gwh"] * 100
                        if r_td["gen_gwh"] > 0 else 0.0)
        eff_raw = 100.0 - loss_pct_raw
    elif not td_combined.empty:
        r_td = td_combined.iloc[-1]
        loss_pct_raw = (r_td["td_losses_gwh"] / r_td["gen_gwh"] * 100
                        if r_td["gen_gwh"] > 0 else 0.0)
        eff_raw = 100.0 - loss_pct_raw
    else:
        loss_pct_raw, eff_raw = 0.0, 100.0

    # Import dependency at target year
    imp_target = import_dep[import_dep["calendar_year"] == target_year]
    if not imp_target.empty:
        r_imp = imp_target.iloc[0]
        imp_dep_raw = (r_imp["imports_toe"] /
                       (r_imp["domestic_supply_toe"] + r_imp["imports_toe"]) * 100
                       if (r_imp["domestic_supply_toe"] + r_imp["imports_toe"]) > 0 else 0.0)
    elif not import_dep.empty:
        r_imp = import_dep.iloc[-1]
        imp_dep_raw = (r_imp["imports_toe"] /
                       (r_imp["domestic_supply_toe"] + r_imp["imports_toe"]) * 100
                       if (r_imp["domestic_supply_toe"] + r_imp["imports_toe"]) > 0 else 0.0)
    else:
        imp_dep_raw = 0.0

    # Gas self-sufficiency at target year
    gas_target = gas_filt[gas_filt["calendar_year"] == target_year]
    if not gas_target.empty:
        r_gas = gas_target.iloc[0]
        gas_ss_raw = (r_gas["production_bcf"] / r_gas["consumption_bcf"] * 100
                      if r_gas["consumption_bcf"] > 0 else 0.0)
        gas_prod_disp = float(r_gas["production_bcf"]) * factor_gas
        gas_cons_disp = float(r_gas["consumption_bcf"]) * factor_gas
    elif not gas_filt.empty:
        r_gas = gas_filt.iloc[-1]
        gas_ss_raw = (r_gas["production_bcf"] / r_gas["consumption_bcf"] * 100
                      if r_gas["consumption_bcf"] > 0 else 0.0)
        gas_prod_disp = float(r_gas["production_bcf"]) * factor_gas
        gas_cons_disp = float(r_gas["consumption_bcf"]) * factor_gas
    else:
        gas_ss_raw, gas_prod_disp, gas_cons_disp = 0.0, 0.0, 0.0

    # Renewable generation & capacity at target year
    re_target_row = re_filt[re_filt["calendar_year"] == target_year]
    if not re_target_row.empty:
        r_re = re_target_row.iloc[0]
        re_gen_val = float((r_re.get("gen_solar_gwh", 0) or 0) +
                           (r_re.get("gen_wind_gwh", 0) or 0) +
                           (r_re.get("gen_hydro_gwh", 0) or 0)) * factor_elec
        re_cap_val = float(r_re.get("capacity_mw", 0) or 0) * factor_power
    elif not re_filt.empty:
        r_re = re_filt.iloc[-1]
        re_gen_val = float((r_re.get("gen_solar_gwh", 0) or 0) +
                           (r_re.get("gen_wind_gwh", 0) or 0) +
                           (r_re.get("gen_hydro_gwh", 0) or 0)) * factor_elec
        re_cap_val = float(r_re.get("capacity_mw", 0) or 0) * factor_power
    else:
        re_gen_val, re_cap_val = 0.0, 0.0

    # ── Score badge color ──────────────────────────────────────────────────────
    def _score_color(s: float) -> str:
        if s >= 75:
            return GREEN
        if s >= 50:
            return AMBER
        return RED

    def _score_label(s: float) -> str:
        if s >= 75:
            return "Optimal"
        if s >= 50:
            return "Adequate"
        return "Critical"

    comp_color = _score_color(composite)

    # ════════════════════════════════════════════════════════════════════════
    # KPI Strip
    # ════════════════════════════════════════════════════════════════════════
    kpi_cols = st.columns(5)

    with kpi_cols[0]:
        st.markdown(
            _kpi_card(
                code="SC1",
                title="Composite Supply Chain Score",
                value=f"{composite:.1f}",
                unit="/ 100",
                rows=[
                    ("Status", _score_label(composite), comp_color),
                    ("Target Year", str(target_year), "#94A3B8"),
                    ("Strategy", strategy[:18], BLUE),
                    ("Optimal ≥", "75 / 100", GREEN),
                ],
                accent=comp_color,
                icon_name="insights",
                badge=_score_label(composite),
                badge_colour=comp_color,
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        eff_color = GREEN if eff_raw >= (100.0 - loss_target) else (
            AMBER if eff_raw >= 75.0 else RED)
        st.markdown(
            _kpi_card(
                code="SC2",
                title="Grid Transmission Efficiency",
                value=f"{eff_raw:.1f}%",
                unit="delivered to end-users",
                rows=[
                    ("T&D Loss Rate", f"{loss_pct_raw:.1f}%", RED if loss_pct_raw > loss_target else AMBER),
                    ("Target Loss", f"≤{loss_target:.1f}% target", GREEN),
                    ("Efficiency Score", f"{tx_eff:.0f}/100", eff_color),
                ],
                accent=eff_color,
                icon_name="generation",
                badge=f"{eff_raw:.1f}%",
                badge_colour=eff_color,
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[2]:
        imp_color = GREEN if imp_dep_raw <= BENCHMARK_IMPORT_DEPENDENCY_MAX else (
            AMBER if imp_dep_raw <= 50.0 else RED)
        st.markdown(
            _kpi_card(
                code="SC3",
                title="Fuel Import Dependency",
                value=f"{imp_dep_raw:.1f}%",
                unit="of analyzed supply imported",
                rows=[
                    ("Streams", f"{len(selected_streams)} Streams", "#94A3B8"),
                    ("Threshold", f"≤{BENCHMARK_IMPORT_DEPENDENCY_MAX:.0f}% target", GREEN),
                    ("Independence Score", f"{imp_ind:.0f}/100", imp_color),
                ],
                accent=imp_color,
                icon_name="imports",
                badge=f"{imp_dep_raw:.1f}%",
                badge_colour=imp_color,
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[3]:
        re_color = GREEN if re_util >= 60.0 else (AMBER if re_util >= 35.0 else RED)
        st.markdown(
            _kpi_card(
                code="SC4",
                title="Renewable Utilisation Rate",
                value=f"{re_util:.0f}",
                unit="/ 100 score",
                rows=[
                    ("RE Generation", f"{re_gen_val:,.0f} {unit_elec}", GREEN),
                    ("Installed Capacity", f"{re_cap_val:,.0f} {unit_power}", PURPLE),
                    ("Target Ambition", f"{re_target}% RE target", CYAN),
                ],
                accent=re_color,
                icon_name="re_share",
                badge=f"{re_util:.0f}/100",
                badge_colour=re_color,
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[4]:
        ss_color = GREEN if gas_ss_raw >= BENCHMARK_GAS_SELFSUFFICIENCY else (
            AMBER if gas_ss_raw >= 50.0 else RED)
        st.markdown(
            _kpi_card(
                code="SC5",
                title="Gas Self-Sufficiency",
                value=f"{gas_ss_raw:.1f}%",
                unit="domestic production / demand",
                rows=[
                    (f"Production ({target_year})", f"{gas_prod_disp:,.0f} {unit_gas}", "#CBD5E1"),
                    (f"Consumption ({target_year})", f"{gas_cons_disp:,.0f} {unit_gas}", "#CBD5E1"),
                    ("Target", f"≥{BENCHMARK_GAS_SELFSUFFICIENCY:.0f}%", GREEN),
                ],
                accent=ss_color,
                icon_name="gas",
                badge=f"{gas_ss_raw:.1f}%",
                badge_colour=ss_color,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # V1 + V2 — Radar + T&D Loss Trend
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Supply Chain Efficiency Overview", "insights", "Objective 1"),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Left: Multi-dimensional efficiency scorecard for evaluated year ({target_year}) comparing 5 KPI dimensions against benchmark (100). "
        f"Right: Grid transmission loss trend and grid efficiency gap vs user-defined loss benchmark (≤{loss_target:.1f}%)."
    )

    c1, c2 = st.columns(2)
    with c1:
        scores_dict = {
            "transmission_efficiency": tx_eff,
            "re_utilisation": re_util,
            "import_dependency": imp_ind,
            "fuel_waste_reduction": fuel_waste,
            "gas_self_sufficiency": gas_ss,
        }
        fig1 = visual1_radar_scorecard(scores_dict, target_year)
        st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    with c2:
        fig2 = visual2_td_loss_trend(td_combined, unit_elec, factor_elec, loss_target)
        st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    # ════════════════════════════════════════════════════════════════════════
    # V3 + V4 — Import Dependency + RE Utilisation
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Fuel Import Dependency & Renewable Utilisation", "supply", "Objective 2"),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Left: Domestic supply vs imported volumes across selected streams ({', '.join(selected_streams[:4])}) with import dependency % trajectory. "
        f"Right: Installed RE capacity ({unit_power}) vs actual generation ({unit_elec}) with utilisation efficiency rate."
    )

    c3, c4 = st.columns(2)
    with c3:
        fig3 = visual3_import_dependency(import_dep, unit_energy, factor_energy)
        st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    with c4:
        fig4 = visual4_re_utilisation(re_filt, unit_elec, factor_elec, unit_power, factor_power)
        st.plotly_chart(fig4, use_container_width=True, config=_CHART_CONFIG)

    # ════════════════════════════════════════════════════════════════════════
    # V5 + V6 — Gas Supply Chain + LNG Cost
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Gas Supply Chain & LNG Cost Efficiency", "gas", "Objective 3"),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Left: Domestic gas production vs consumption gap with LNG top-up volumes and self-sufficiency % ({unit_gas}). "
        f"Right: LNG import volumes ({unit_gas}) vs total cost (MUSD) and cost-per-{unit_gas} efficiency."
    )

    c5, c6 = st.columns(2)
    with c5:
        fig5 = visual5_gas_supply_chain(gas_filt, lng_filt, unit_gas, factor_gas)
        st.plotly_chart(fig5, use_container_width=True, config=_CHART_CONFIG)

    with c6:
        fig6 = visual6_lng_cost(lng_filt, unit_gas, factor_gas)
        st.plotly_chart(fig6, use_container_width=True, config=_CHART_CONFIG)

    # ════════════════════════════════════════════════════════════════════════
    # V7 — Composite Optimization Score Trend
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title(
            f"Composite Supply Chain Optimization Score ({year_range[0]}–{year_range[1]})",
            "data", "Objective 4"
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        f"Weighted composite score (0–100) tracking supply chain efficiency over time for active strategy: <b>{strategy}</b>. "
        f"Weights: Transmission {active_weights['transmission_efficiency']:.0%}, RE Utilisation {active_weights['re_utilisation']:.0%}, "
        f"Import Independence {active_weights['import_dependency']:.0%}, Fuel Waste {active_weights['fuel_waste_reduction']:.0%}, "
        f"Gas Self-Sufficiency {active_weights['gas_self_sufficiency']:.0%}."
    )
    fig7 = visual7_optimization_score(score_df, strategy)
    st.plotly_chart(fig7, use_container_width=True, config=_CHART_CONFIG)

    # ════════════════════════════════════════════════════════════════════════
    # V8 — Optimal Mix Simulator
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Optimal Fuel vs Renewable Mix Simulator", "scenario", "Objective 5"),
        unsafe_allow_html=True,
    )
    st.caption(
        f"What-if analysis: Reported generation mix ({target_year}) vs user-defined optimal portfolio "
        f"({re_target}% RE / {fuel_target}% Conventional). "
        "Adjust RE target and strategy presets in the sidebar to simulate alternative supply chain configurations."
    )

    baseline_data_dict = r_re.to_dict() if not re_target_row.empty else (
        re_filt.iloc[-1].to_dict() if not re_filt.empty else None
    )
    if baseline_data_dict:
        baseline_data_dict["calendar_year"] = target_year
        baseline_gen = float(baseline_data_dict.get("primary_energy_gwh", 154000.0) or 154000.0)
    else:
        baseline_gen = 154000.0

    fig8 = visual8_optimal_mix(re_target, fuel_target, unit_elec, baseline_gen, factor_elec, baseline_data_dict)
    st.plotly_chart(fig8, use_container_width=True, config=_CHART_CONFIG)

    # ── Optimization Insights panel ───────────────────────────────────────────
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        section_title("Key Optimization Insights & Policy Recommendations", "insights", "Summary"),
        unsafe_allow_html=True,
    )

    insights_cols = st.columns(3)

    insight_cards = [
        {
            "icon": "generation",
            "color": RED if loss_pct_raw > loss_target else (AMBER if loss_pct_raw > 12.0 else GREEN),
            "title": f"T&D Loss Reduction (Target ≤{loss_target:.1f}%)",
            "value": f"{loss_pct_raw:.1f}% loss in {target_year}",
            "text": (
                f"Grid transmission losses of {loss_pct_raw:.1f}% in {target_year} vs active target benchmark of {loss_target:.1f}%. "
                f"Meeting this loss benchmark would preserve an estimated {((loss_pct_raw - loss_target)/100.0 * 140000.0 * factor_elec):,.0f} {unit_elec} annually, "
                "reducing reliance on peak thermal dispatch."
            ),
        },
        {
            "icon": "imports",
            "color": RED if imp_dep_raw > BENCHMARK_IMPORT_DEPENDENCY_MAX else GREEN,
            "title": f"Import Exposure ({len(selected_streams)} Streams)",
            "value": f"{imp_dep_raw:.1f}% import share",
            "text": (
                f"Across analyzed streams, import dependency stands at {imp_dep_raw:.1f}% vs safe threshold of ≤{BENCHMARK_IMPORT_DEPENDENCY_MAX:.0f}%. "
                f"Targeting {re_target}% domestic renewable energy directly reduces spot LNG and imported coal foreign exchange outflow."
            ),
        },
        {
            "icon": "re_share",
            "color": GREEN if re_target >= 45 else AMBER,
            "title": f"Strategy: {strategy[:22]}",
            "value": f"{re_target}% RE / {fuel_target}% Conv",
            "text": (
                f"Under the {strategy} pathway, shifting to {re_target}% clean energy improves the composite supply chain score "
                f"to {composite:.1f}/100. Prioritizing hydro base-generation and rapid solar deployment yields the highest resilience."
            ),
        },
    ]

    for col, ins in zip(insights_cols, insight_cards):
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
                  <div style="color:{ins['color']};font-size:18px;font-weight:800;
                              font-family:'JetBrains Mono',monospace;margin-bottom:8px;">{ins['value']}</div>
                  <div style="color:#94A3B8;font-size:11px;line-height:1.55;">{ins['text']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
