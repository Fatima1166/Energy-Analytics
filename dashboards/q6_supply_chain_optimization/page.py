"""
Supply Chain Optimization dashboard (Question 6).

Question 6 asks how well the fuel and renewable energy supply chains are being
used, so this page keeps only what that answer needs:

  1. Sidebar   -- which part of the chain counts most, and which years to judge
  2. KPI cards -- the overall score, the electricity that reaches people, and how
                  much of the clean plant's potential is actually made
  3. Visuals   -- the score and its four parts year by year, grid losses, clean
                  plant use, the gas chain, and what the target mix would look like

Three things are deliberately not here.  Where the supply comes from -- home
production versus imports -- is Question 5's page, so the import share stays as
one of the four scored parts but gets no chart of its own.  What imported gas
costs is Question 7's page.  And the fifth score this page used to show, "fuel
waste", was worked out from the same grid-loss numbers as the grid part, so it
said the same thing twice; it is gone and four parts remain.

Nothing here is a forecast.  Every number is a reported year judged against a
stated standard, and the only choice the page offers is which part of the chain
the standard is measured against most strictly.

Each card names the year its own figure came from, because the record stops
reporting grid losses, gas and imports in different years.  A year with no report
is left blank rather than read as zero, and the overall score is then the average
of the parts that were reported.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
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
from core.units import display_factor

from .charts import (
    visual1_score_over_time,
    visual2_grid_losses,
    visual3_renewable_plant_use,
    visual4_gas_chain,
    visual5_best_mix,
)
from .config import (
    AMBER,
    BENCHMARK_GAS_SELFSUFFICIENCY,
    BENCHMARK_IMPORT_DEPENDENCY_MAX,
    BENCHMARK_RE_UTILISATION_MIN,
    BLUE,
    DEFAULT_STRATEGY,
    GREEN,
    PURPLE,
    RED,
    SCORE_FAIR,
    SCORE_GOOD,
    STRATEGIES,
)

_FILTERS_KEY = "q6_filters"
_CHART_CONFIG = {"displayModeBar": False}

# The four parts of the overall score, said the way a person would say them.
PART_WORDS = {
    "grid_efficiency": "grid losses",
    "re_utilisation": "clean plant use",
    "import_independence": "less bought abroad",
    "gas_self_sufficiency": "gas made at home",
}

# The shared card sheet in core/styles.py pins every .kpi-balance card to a fixed
# 225px and pushes its detail rows to the bottom, which leaves a dead band across
# the middle of a short card.  These page-scoped selectors carry the same
# !important but match more precisely, so they win -- and only for this page.
_CARD_CSS = """
<style>
  .kpi-balance.q6-kpi {
      height: auto !important;
      min-height: 0 !important;
      max-height: none !important;
      justify-content: flex-start !important;
      padding: 13px 14px 12px !important;
  }
  .kpi-balance.q6-kpi .kpi-balance-details { margin-top: 0 !important; }
</style>
"""


# --- Sidebar controls ---

def sidebar() -> None:
    """Called by app.py before the global unit slicer."""
    st.sidebar.markdown('<div class="dsh-side-title">Supply Chain</div>',
                        unsafe_allow_html=True)

    chosen = st.session_state.get("q6_strategy", DEFAULT_STRATEGY)
    strategy = st.sidebar.selectbox(
        "Which part counts most", list(STRATEGIES),
        index=list(STRATEGIES).index(chosen if chosen in STRATEGIES else DEFAULT_STRATEGY),
        key="q6_strategy",
        help=STRATEGIES.get(chosen, STRATEGIES[DEFAULT_STRATEGY])["desc"],
    )
    preset = STRATEGIES[strategy]

    years = st.sidebar.slider(
        "Years to judge", min_value=1999, max_value=2024, value=(2002, 2024), step=1,
        key="q6_years",
        help=("Which years to score. The cards read the last year in this "
              "window, or the closest year before it that has a record."),
    )

    st.session_state[_FILTERS_KEY] = {
        "strategy": strategy,
        "year_range": (int(years[0]), int(years[1])),
        "re_target": int(preset["re_target"]),
        "fuel_target": int(100 - int(preset["re_target"])),
        "loss_target": float(preset["loss_target"]),
        "weights": preset["weights"],
    }
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = BLUE, icon_name: str = "supply",
              badge: str = "", badge_colour: str = BLUE) -> str:
    """Compact dark glassmorphism KPI card, sized to its own content."""
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
<div class="kpi-balance q6-kpi" style="border: 1px solid {accent}44;">
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
              margin-bottom:4px;min-height:28px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:6px;">
    <span style="color:{accent};font-size:23px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details">{detail}</div>
</div>
"""


# --- Small readers ---

def _year_row(df: pd.DataFrame, year: int):
    """The row for one year, or None when that year has no report."""
    if df is None or df.empty:
        return None
    hit = df[df["calendar_year"] == year]
    return None if hit.empty else hit.iloc[0]


def _ratio(numerator: float, denominator: float):
    """numerator / denominator as a %, or NaN when it cannot be worked out."""
    if denominator and np.isfinite(denominator) and denominator > 0:
        value = numerator / denominator * 100.0
        return float(value) if np.isfinite(value) else np.nan
    return np.nan


def _clamp(value: float, top: float = 100.0) -> float:
    return float(min(max(value, 0.0), top))


# --- The score itself ---

def _grid_frame(gen_df: pd.DataFrame, td_df: pd.DataFrame) -> pd.DataFrame:
    """Generation and grid losses side by side by year."""
    if gen_df.empty or td_df.empty:
        return pd.DataFrame()
    merged = pd.merge(
        gen_df[["calendar_year", "generation_gwh"]].rename(
            columns={"generation_gwh": "gen_gwh"}),
        td_df[["calendar_year", "td_losses_gwh"]],
        on="calendar_year", how="inner",
    )
    return merged.sort_values("calendar_year").reset_index(drop=True)


def _supply_frame(ps_df: pd.DataFrame) -> pd.DataFrame:
    """How much supply was there at home and how much was bought, by year."""
    if ps_df.empty:
        return pd.DataFrame()
    agg = ps_df.groupby("calendar_year", as_index=False).agg(
        domestic_supply_toe=("supply_toe", "sum"),
        imports_toe=("imports_toe", "sum"),
    )
    return agg.sort_values("calendar_year").reset_index(drop=True)


def _compute_scores(grid_df: pd.DataFrame, supply_df: pd.DataFrame,
                    re_df: pd.DataFrame, gas_df: pd.DataFrame,
                    year_range: tuple, weights: dict,
                    loss_target: float) -> pd.DataFrame:
    """Score each of the four parts (0-100, 100 = the standard is met) for every
    year in the window, and weigh them into the overall score.  The raw figures
    the cards read travel along in the same frame, and a part with no report for
    a year stays blank instead of being scored as zero or as perfect."""
    aim_arrived = 100.0 - float(loss_target)

    # This record stops filling the import column after one year; a later zero
    # means "not reported", not "nothing was bought".
    if supply_df.empty or not (supply_df["imports_toe"] > 0).any():
        last_import_year = 0
    else:
        last_import_year = int(supply_df.loc[supply_df["imports_toe"] > 0,
                                             "calendar_year"].max())
    records = []

    for year in range(int(year_range[0]), int(year_range[1]) + 1):
        row = {"calendar_year": year,
               "arrived_pct": np.nan, "loss_pct": np.nan, "grid_efficiency": np.nan,
               "used_pct": np.nan, "re_utilisation": np.nan,
               "clean_made_gwh": np.nan, "plant_built_mw": np.nan,
               "import_share": np.nan, "import_independence": np.nan,
               "gas_met_pct": np.nan, "gas_self_sufficiency": np.nan,
               "gas_made_bcf": np.nan, "gas_used_bcf": np.nan}

        # 1. Electricity that arrives -- judged against the loss aim.
        grid = _year_row(grid_df, year)
        if grid is not None:
            generated = float(grid["gen_gwh"] or 0)
            lost = float(grid["td_losses_gwh"] or 0)
            row["loss_pct"] = _ratio(lost, generated)
            row["arrived_pct"] = (100.0 - row["loss_pct"]) if np.isfinite(row["loss_pct"]) else np.nan
            if np.isfinite(row["arrived_pct"]) and aim_arrived > 0:
                row["grid_efficiency"] = _clamp(row["arrived_pct"] / aim_arrived * 100.0)

        # 2. Clean plant -- what it made against what it could have made.
        clean = _year_row(re_df, year)
        if clean is not None:
            made = float(clean["gen_solar_gwh"] or 0) + float(clean["gen_wind_gwh"] or 0) \
                + float(clean["gen_hydro_gwh"] or 0)
            capacity = float(clean["capacity_mw"] or 0)
            potential = capacity * 8760.0 / 1000.0  # GWh if it ran every hour
            row["clean_made_gwh"] = made
            row["plant_built_mw"] = capacity
            row["used_pct"] = _ratio(made, potential)
            if np.isfinite(row["used_pct"]):
                row["re_utilisation"] = _clamp(
                    row["used_pct"] / BENCHMARK_RE_UTILISATION_MIN * 100.0)

        # 3. How little of the supply is bought from abroad.
        supply = _year_row(supply_df, year)
        if supply is not None and year <= last_import_year:
            home = float(supply["domestic_supply_toe"] or 0)
            bought = float(supply["imports_toe"] or 0)
            row["import_share"] = _ratio(bought, home + bought)
            if np.isfinite(row["import_share"]):
                row["import_independence"] = _clamp(
                    (BENCHMARK_IMPORT_DEPENDENCY_MAX - row["import_share"])
                    / BENCHMARK_IMPORT_DEPENDENCY_MAX * 100.0 + 50.0)

        # 4. Gas demand met at home.
        gas = _year_row(gas_df, year)
        if gas is not None:
            produced = float(gas["production_bcf"] or 0)
            used = float(gas["consumption_bcf"] or 0)
            row["gas_made_bcf"] = produced
            row["gas_used_bcf"] = used
            row["gas_met_pct"] = _ratio(produced, used) if used > 0 else 100.0
            if np.isfinite(row["gas_met_pct"]):
                row["gas_self_sufficiency"] = _clamp(
                    row["gas_met_pct"] / BENCHMARK_GAS_SELFSUFFICIENCY * 100.0)

        # Overall score: the weighted average of the parts that have data.
        total, weight_used, parts_reported = 0.0, 0.0, 0
        for part, weight in weights.items():
            value = row.get(part, np.nan)
            if value is not None and np.isfinite(value):
                total += value * weight
                weight_used += weight
                parts_reported += 1
        row["composite_score"] = total / weight_used if weight_used > 0 else np.nan
        row["parts_reported"] = float(parts_reported)

        records.append(row)

    return pd.DataFrame(records)


def _band(score: float):
    """The plain words and colour for a 0-100 score."""
    if score >= SCORE_GOOD:
        return "Working well", GREEN
    if score >= SCORE_FAIR:
        return "Room to improve", AMBER
    return "Needs work", RED


# --- Main render ---

def render() -> None:
    """Renders the Question 6 supply chain page."""
    flt = st.session_state.get(_FILTERS_KEY, {})
    strategy = flt.get("strategy", DEFAULT_STRATEGY)
    year_range = flt.get("year_range", (2002, 2024))
    re_target = int(flt.get("re_target", STRATEGIES[DEFAULT_STRATEGY]["re_target"]))
    fuel_target = int(flt.get("fuel_target", 100 - re_target))
    loss_target = float(flt.get("loss_target", STRATEGIES[DEFAULT_STRATEGY]["loss_target"]))
    weights = flt.get("weights", STRATEGIES[DEFAULT_STRATEGY]["weights"])
    year_start, year_end = int(year_range[0]), int(year_range[1])

    # --- Reported data ---
    gen_df = run_query(Q_ELEC_GEN)
    td_df = run_query(Q_TD_LOSSES)
    ps_df = run_query(Q_PRIMARY_SUPPLY)
    re_df = run_query(Q_RENEWABLE_ENERGY)
    gas_df = run_query(Q_NATURAL_GAS)
    lng_df = run_query(Q_LNG)

    def _window(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "calendar_year" not in df.columns:
            return df
        return df[(df["calendar_year"] >= year_start) &
                  (df["calendar_year"] <= year_end)].copy()

    gen_filt, td_filt = _window(gen_df), _window(td_df)
    ps_filt, re_filt = _window(ps_df), _window(re_df)
    gas_filt, lng_filt = _window(gas_df), _window(lng_df)

    if re_filt.empty and gen_filt.empty:
        st.error("Nothing was recorded for these years.")
        st.stop()

    # --- Units (electricity, plant size, gas) ---
    units = get_units()
    unit_elec = units.get("electricity", "GWh")
    factor_elec = display_factor("electricity", unit_elec)
    unit_power = units.get("power", "MW")
    factor_power = display_factor("power", unit_power)
    unit_gas = units.get("gas", "BCF")
    factor_gas = display_factor("gas", unit_gas)

    # --- Score the years ---
    grid_df = _grid_frame(gen_filt, td_filt)
    supply_df = _supply_frame(ps_filt)
    score_df = _compute_scores(grid_df, supply_df, re_filt, gas_filt,
                               year_range, weights, loss_target)

    def _pick(column: str, default: float = np.nan):
        """The value from the last year in the window that reports this figure,
        and that year, so a gap in the record never prints as a zero and never
        borrows a year label it does not belong to."""
        if score_df.empty or column not in score_df.columns:
            return default, year_end
        series = pd.to_numeric(score_df[column], errors="coerce").dropna()
        if series.empty:
            return default, year_end
        return float(series.iloc[-1]), int(score_df.loc[series.index[-1], "calendar_year"])

    composite, composite_year = _pick("composite_score", 0.0)
    arrived, arrived_year = _pick("arrived_pct", 0.0)
    loss_pct, _ = _pick("loss_pct", 0.0)
    grid_score, _ = _pick("grid_efficiency", 0.0)
    used_pct, used_year = _pick("used_pct", 0.0)
    clean_score, _ = _pick("re_utilisation", 0.0)
    clean_made, _ = _pick("clean_made_gwh", 0.0)
    plant_built, _ = _pick("plant_built_mw", 0.0)
    parts_reported, _ = _pick("parts_reported", 0.0)

    clean_made *= factor_elec
    plant_built *= factor_power

    # The part the chosen strategy leans on hardest.  When all four carry the
    # same weight there is no favourite, and the card says so.
    spread = max(weights.values()) - min(weights.values())
    if spread < 0.05:
        top_text = "All four parts equal"
    else:
        top_part = max(weights, key=lambda key: weights[key])
        top_text = f"{PART_WORDS.get(top_part, top_part)} · {weights[top_part]:.0%}"

    # Which sources made the electricity in the year the mix chart shows.
    mix_row = _year_row(re_filt, used_year)
    if mix_row is None and not re_filt.empty:
        mix_row = re_filt.iloc[-1]
    mix_data = mix_row.to_dict() if mix_row is not None else None

    comp_word, comp_colour = _band(composite)
    _, grid_colour = _band(grid_score)
    clean_word, clean_colour = _band(clean_score)

    # The grid part is scored as "how much of the aim was reached", which sits
    # high even when the loss aim is missed, so the card's own badge reads the
    # loss against the aim directly instead.
    grid_ok = loss_pct <= loss_target
    grid_badge_word = "On target" if grid_ok else "Over the aim"
    grid_badge_colour = GREEN if grid_ok else (
        AMBER if loss_pct <= loss_target * 1.25 else RED)

    # ══════════════════════════════════════════════════════════════════════
    # Three cards across four slots -- the fourth slot stays blank so each card
    # keeps the width of a four-up row.
    # ══════════════════════════════════════════════════════════════════════
    cards = [
        _kpi_card(
            code="K1",
            title=f"How well the chains are used, {composite_year}",
            value=f"{composite:.1f}",
            unit="/ 100",
            rows=[
                ("Counted hardest", top_text, BLUE),
                ("Scored from", f"{parts_reported:.0f} of 4 parts",
                 GREEN if parts_reported >= 4 else AMBER),
                ("Good from", f"{SCORE_GOOD:.0f} / 100", GREEN),
            ],
            accent=comp_colour,
            icon_name="insights",
            badge=comp_word,
            badge_colour=comp_colour,
        ),
        _kpi_card(
            code="K2",
            title=f"Electricity that reached people, {arrived_year}",
            value=f"{arrived:.1f}",
            unit="% of what was generated",
            rows=[
                ("Lost on the wires", f"{loss_pct:.1f}%",
                 RED if not grid_ok else AMBER),
                ("The aim", f"under {loss_target:.1f}% lost", GREEN),
                ("Aim reached", f"{grid_score:.0f}%", grid_colour),
            ],
            accent=grid_badge_colour,
            icon_name="generation",
            badge=grid_badge_word,
            badge_colour=grid_badge_colour,
        ),
        _kpi_card(
            code="K3",
            title=f"Clean plant made vs what it could make, {used_year}",
            value=f"{used_pct:.1f}",
            unit="% of what it could make",
            rows=[
                ("What it made", f"{clean_made:,.0f} {unit_elec}", GREEN),
                ("Plant built", f"{plant_built:,.0f} {unit_power}", PURPLE),
                ("Aim reached", f"{clean_score:.0f}%", clean_colour),
            ],
            accent=clean_colour,
            icon_name="re_share",
            badge=clean_word,
            badge_colour=clean_colour,
        ),
    ]

    st.markdown(_CARD_CSS, unsafe_allow_html=True)
    for column, card in zip(st.columns(4), cards):
        column.markdown(card, unsafe_allow_html=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 1 -- the score and its four parts      Visual 4 -- the gas chain
    # ══════════════════════════════════════════════════════════════════════
    score_col, gas_col = st.columns(2)

    with score_col:
        st.markdown(
            section_title("Visual 1 – The score, year by year", "insights",
                          badge=f"{strategy} · {year_start}–{year_end}"),
            unsafe_allow_html=True)
        st.caption("Thick line: the overall score. Thin lines: its four parts. "
                   "The low part holds the score down.")
        st.plotly_chart(visual1_score_over_time(score_df),
                        use_container_width=True, config=_CHART_CONFIG)

    with gas_col:
        st.markdown(
            section_title("Visual 4 – The gas chain", "gas",
                          badge=f"{year_start}–{year_end}"),
            unsafe_allow_html=True)
        st.caption("Green: gas made at home. Orange: gas used. Bars: gas bought "
                   "by ship. Dotted: share met at home.")
        st.plotly_chart(visual4_gas_chain(gas_filt, lng_filt, unit_gas, factor_gas),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visuals 2 + 3 -- where the electricity goes to waste
    # ══════════════════════════════════════════════════════════════════════
    loss_col, plant_col = st.columns(2)

    with loss_col:
        st.markdown(
            section_title("Visual 2 – Electricity lost on the wires", "generation",
                          badge=f"{year_start}–{year_end}"),
            unsafe_allow_html=True)
        st.caption("Blue: power made. Red: power lost on the way. "
                   "Green line: share that arrived.")
        st.plotly_chart(visual2_grid_losses(grid_df, unit_elec, factor_elec, loss_target),
                        use_container_width=True, config=_CHART_CONFIG)

    with plant_col:
        st.markdown(
            section_title("Visual 3 – Clean plant built, and what it made", "renewables",
                          badge=f"{year_start}–{year_end}"),
            unsafe_allow_html=True)
        st.caption("Purple bars: plant built. Green line: what it made. "
                   "Dotted line: share of what it could make.")
        st.plotly_chart(visual3_renewable_plant_use(re_filt, unit_elec, factor_elec,
                                                    unit_power, factor_power),
                        use_container_width=True, config=_CHART_CONFIG)

    # ══════════════════════════════════════════════════════════════════════
    # Visual 5 -- what is made now and the target mix
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        section_title("Visual 5 – What is made now and the target mix", "scenario",
                      badge=f"{re_target}% clean / {fuel_target}% fuel"),
        unsafe_allow_html=True)
    st.caption(f"Left: what each source made in {used_year}. Right: the same "
               "year with both targets met.")
    st.plotly_chart(visual5_best_mix(re_target, fuel_target, unit_elec,
                                     factor_elec, mix_data),
                    use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    line1 = (f"The chains score {composite:.1f} of 100 in {composite_year} — "
             f"{comp_word}.")
    if grid_ok:
        line2 = (f"The grid keeps losses to {loss_pct:.1f}%, inside the aim of "
                 f"under {loss_target:.1f}%.")
    else:
        line2 = (f"The grid still loses {loss_pct:.1f}% on the wires against an "
                 f"aim of {loss_target:.1f}% — the chain's weakest link.")
    st.markdown(conclusion_card([line1, line2]), unsafe_allow_html=True)
