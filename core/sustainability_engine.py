"""
core/sustainability_engine.py -- question 8:
"What optimal strategy may be opted to make energy development sustainable?"

This is the analysis engine behind the Sustainable Energy Strategy dashboard.
Unlike the earlier question dashboards (which compute inside their page
module), Q8 follows a strict engine/presentation split:

    engine (this file)  -- pure pandas/numpy, no Streamlit, no MySQL.
    page (dashboard)    -- fetches frames, calls the engine, renders charts.

Model -- a four-pillar sustainability index (the "extended trilemma"):

    SECURITY     affordability-independent supply: import dependence,
                 gas self-sufficiency, generation diversity (1 - HHI)
    ECONOMY      system economics: grid (T&D) efficiency, LNG unit-price
                 pressure, per-unit cost of delivered electricity trends
    ENVIRONMENT  decarbonisation: renewable generation share
    ACCESS       modern energy access: per-capita electricity consumption,
                 demand coverage

Each component metric is mapped onto a 0-100 score.  Metrics with an
agreed absolute benchmark use it directly; ambiguous metrics are
auto-calibrated against their own 10th-90th percentile envelope, so the
scoring adapts to the data instead of hard-coded ranges.

The engine then:
  1. builds the yearly indicator frame          (build_indicator_frame)
  2. weights pillars per the analyst's strategy (apply_weights)
  3. ranks a strategy library and selects the
     least-cost package within a budget         (select_optimal_package)
  4. projects pillar trajectories to the 2035
     horizon for BAU / announced / optimal
     pathways                                   (project_pathways)

All values are in the base units documented in core/units.py (TOE, GWh,
MW, BCF, t, USD).  Conversion to display units happens at render time.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

# ══════════════════════════════ constants ═══════════════════════════════════

PILLARS: List[str] = ["security", "economy", "environment", "access"]

PILLAR_LABELS = {
    "security":    "Energy Security",
    "economy":     "Economic Viability",
    "environment": "Environmental Sustainability",
    "access":      "Energy Access",
}

HISTORY_START = 1999
HISTORY_END = 2024

# Absolute scoring benchmarks (IEA / SDG7 / Pakistan NEP anchors)
TARGET_IMPORT_DEP_MAX   = 30.0    # % of supply imported  -> 0 score at/above
TARGET_GAS_SS           = 70.0    # % domestic gas / demand
TARGET_RE_SHARE         = 60.0    # % RE in generation  -> full score
TARGET_GRID_EFF         = 90.0    # % delivered / generated -> full score
TARGET_PC_KWH           = 1000.0  # kWh per capita electricity -> full score

GEN_MIX_COLS = [
    "gen_hydro_gwh", "gen_solar_gwh", "gen_wind_gwh",
    "gen_other_renewables_gwh", "gen_nuclear_gwh",
    "gen_coal_gwh", "gen_gas_gwh",
]

RE_COLS = ["gen_hydro_gwh", "gen_solar_gwh", "gen_wind_gwh",
           "gen_other_renewables_gwh"]


# ══════════════════════════ scoring helpers ══════════════════════════════════

def _clip100(x) -> pd.Series:
    return pd.Series(x).clip(0.0, 100.0)


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    """Numeric column as a float Series on the frame index; NaN if absent."""
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index, dtype=float)


def _score_higher_is_better(series: pd.Series, full: float, zero: float) -> pd.Series:
    """Linear map: series>=full -> 100, series<=zero -> 0."""
    s = pd.to_numeric(series, errors="coerce")
    return ((s - zero) / (full - zero) * 100.0).clip(0.0, 100.0)


def _score_lower_is_better(series: pd.Series, best: float, worst: float) -> pd.Series:
    """Linear map: series<=best -> 100, series>=worst -> 0."""
    s = pd.to_numeric(series, errors="coerce")
    return ((worst - s) / (worst - best) * 100.0).clip(0.0, 100.0)


def _auto_calibrate(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Percentile-envelope scoring (robust when no absolute benchmark exists).

    10th percentile -> 0, 90th percentile -> 100 (direction as requested).
    Flat series fall back to a neutral 50.
    """
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series(np.nan, index=s.index, dtype=float)
    lo, hi = s.quantile(0.10), s.quantile(0.90)
    if not np.isfinite(lo) or not np.isfinite(hi) or abs(hi - lo) < 1e-9:
        return pd.Series(50.0, index=s.index)
    norm = (s - lo) / (hi - lo) * 100.0
    if not higher_is_better:
        norm = 100.0 - norm
    return norm.clip(0.0, 100.0)


def _safe_div(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    return a / b.replace(0, np.nan)


# ══════════════════════ 1. indicator frame construction ═════════════════════

def build_indicator_frame(
    re_df: pd.DataFrame,
    gen_df: pd.DataFrame,
    td_df: pd.DataFrame,
    ps_df: pd.DataFrame,
    gas_df: pd.DataFrame,
    lng_df: pd.DataFrame,
    econ_df: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the per-year component metrics and pillar scores.

    Every input frame is optional; missing metrics degrade to NaN and the
    pillar score renormalises over whatever components are available.
    """
    years = sorted(
        set(_years(re_df)) | set(_years(gen_df)) | set(_years(ps_df))
        | set(_years(gas_df)) | set(_years(econ_df))
    )
    years = [y for y in years if HISTORY_START <= y <= HISTORY_END]
    if not years:
        return pd.DataFrame()

    # calendar_year is the alignment index for every derived column
    idx = pd.DataFrame({"calendar_year": years}).set_index("calendar_year")

    # ── generation mix metrics (fact_renewable_energy) ──────────────────────
    if re_df is not None and not re_df.empty:
        r = re_df.drop_duplicates("calendar_year").set_index("calendar_year")
        r = r.reindex(years)
        # A column the record never filled (gen_other_renewables_gwh is NULL in
        # every year) is not a zero, it is an absent source: drop it instead of
        # summing it, or it would silently hold back a year from being scored.
        gen_cols = [c for c in GEN_MIX_COLS
                    if c in r.columns
                    and pd.to_numeric(r[c], errors="coerce").notna().any()]
        mix = r[gen_cols].apply(pd.to_numeric, errors="coerce")
        # min_count matters more than the sum itself: a year that leaves any
        # reported fuel blank (1999 has no coal/gas/nuclear row) has no total,
        # rather than a total quietly missing three plants.
        total_gen = mix.sum(axis=1, min_count=len(mix.columns))
        re_cols = [c for c in RE_COLS if c in mix.columns]
        re_gen = (mix[re_cols].sum(axis=1, min_count=len(re_cols))
                  if re_cols else np.nan)
        idx["gen_total_gwh"] = total_gen
        idx["re_gen_gwh"] = re_gen
        idx["re_share_pct"] = _safe_div(re_gen, total_gen) * 100.0
        # generation diversity  1 - HHI  (0 = mono-source, ->1 = even mix)
        # No fillna here: blanking the shares to 0 read as "every source equally
        # small", which scored an unreported year as perfect diversity.
        shares = mix.div(total_gen.replace(0, np.nan), axis=0)
        hhi = (shares ** 2).sum(axis=1, min_count=len(mix.columns))
        idx["diversity_idx"] = (1.0 - hhi) * 100.0

    # ── grid efficiency (generation + T&D losses) ───────────────────────────
    if gen_df is not None and not gen_df.empty and td_df is not None and not td_df.empty:
        g = gen_df.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        t = td_df.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        gen = pd.to_numeric(g["generation_gwh"], errors="coerce")
        losses = pd.to_numeric(t["td_losses_gwh"], errors="coerce")
        idx["td_loss_pct"] = _safe_div(losses, gen) * 100.0
        idx["grid_eff_pct"] = 100.0 - idx["td_loss_pct"]
        if "consumption_gwh" in g.columns:
            idx["consumption_gwh"] = pd.to_numeric(g["consumption_gwh"], errors="coerce")

    # ── import dependence (primary supply, all sources) ─────────────────────
    if ps_df is not None and not ps_df.empty:
        # min_count=1 matters: the record stops filling imports_toe after 2022
        # (every row NULL), and a plain sum() turns an all-NULL year into a real
        # 0 -- which then scores as "nothing imported, perfect security".
        p = (ps_df.groupby("calendar_year")[["supply_toe", "imports_toe"]]
             .sum(min_count=1)
             .rename(columns={"supply_toe": "domestic_toe"})
             .reset_index())
        p = p.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        # Both halves have to be on the record for the share to mean anything:
        # a year whose imports rows are absent gets a blank, not "0% imported,
        # perfect security".
        total_supply = p[["domestic_toe", "imports_toe"]].sum(axis=1, min_count=2)
        idx["import_dep_pct"] = _safe_div(p["imports_toe"], total_supply) * 100.0

    # ── gas self-sufficiency ─────────────────────────────────────────────────
    if gas_df is not None and not gas_df.empty:
        gz = gas_df.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        prod = pd.to_numeric(gz["production_bcf"], errors="coerce")
        cons = pd.to_numeric(gz["consumption_bcf"], errors="coerce")
        idx["gas_prod_bcf"] = prod
        idx["gas_cons_bcf"] = cons
        idx["gas_ss_pct"] = (_safe_div(prod, cons) * 100.0).clip(0, 100)

    # ── LNG price pressure (unit cost of marginal gas) ──────────────────────
    if lng_df is not None and not lng_df.empty:
        l = lng_df.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        musd = pd.to_numeric(l["imports_value_musd"], errors="coerce")
        bcf = pd.to_numeric(l["imports_bcf"], errors="coerce")
        idx["lng_musd"] = musd
        # 1 Bcf natural gas ~= 1.036 million MMBtu
        idx["lng_usd_per_mmbtu"] = _safe_div(musd * 1e6, bcf * 1.036e6)
        idx["lng_unit_cost_musd_bcf"] = _safe_div(musd, bcf)

    # ── CO2 intensity of the system + per-capita access ─────────────────────
    if econ_df is not None and not econ_df.empty:
        e = econ_df.drop_duplicates("calendar_year").set_index("calendar_year").reindex(years)
        co2_t = pd.to_numeric(e["co2_emissions_tonnes"], errors="coerce")
        pop = pd.to_numeric(e["population"], errors="coerce")
        idx["co2_tonnes"] = co2_t
        idx["population"] = pop
        if "consumption_gwh" in idx.columns:
            idx["pc_elec_kwh"] = _safe_div(idx["consumption_gwh"] * 1e6, pop)
        elif "gen_total_gwh" in idx.columns:
            idx["pc_elec_kwh"] = _safe_div(idx["gen_total_gwh"] * 1e6, pop)

    if "consumption_gwh" in idx.columns and "gen_total_gwh" in idx.columns:
        idx["coverage_pct"] = (_safe_div(idx["consumption_gwh"], idx["gen_total_gwh"])
                               * 100.0).clip(0, 100)

    # ── component scores ─────────────────────────────────────────────────────
    scores: Dict[str, Dict[str, pd.Series]] = {p: {} for p in PILLARS}

    scores["security"]["imp_dep"] = _score_lower_is_better(
        _col(idx, "import_dep_pct"), 5.0, TARGET_IMPORT_DEP_MAX + 25.0)
    scores["security"]["gas_ss"] = _score_higher_is_better(
        _col(idx, "gas_ss_pct"), TARGET_GAS_SS, 0.0)
    scores["security"]["diversity"] = _auto_calibrate(_col(idx, "diversity_idx"), True)

    scores["economy"]["grid_eff"] = _score_higher_is_better(
        _col(idx, "grid_eff_pct"), TARGET_GRID_EFF, 70.0)
    scores["economy"]["lng_price"] = _auto_calibrate(
        _col(idx, "lng_usd_per_mmbtu"), higher_is_better=False)

    scores["environment"]["re_share"] = _score_higher_is_better(
        _col(idx, "re_share_pct"), TARGET_RE_SHARE, 5.0)
    # A carbon-intensity component was dropped here on purpose.  The warehouse
    # holds national CO2 (all fuels, all sectors) but only electricity
    # generation, so the ratio lands near 1,200-2,200 kg/MWh against a
    # power-sector benchmark of 350 -- every year scored a flat 0 and pulled the
    # Environmental pillar down by a third on a scope error, not on evidence.

    scores["access"]["pc_elec"] = _score_higher_is_better(
        _col(idx, "pc_elec_kwh"), TARGET_PC_KWH, 100.0)
    scores["access"]["coverage"] = _score_higher_is_better(
        _col(idx, "coverage_pct"), 98.0, 60.0)

    for pillar, comp_map in scores.items():
        frame = pd.DataFrame(comp_map, index=idx.index)
        wsum = frame.notna().sum(axis=1)
        # A pillar is only reported for a year when every one of its components
        # was reported for that year.  Averaging over the parts that happen to
        # exist let 2024 print "Supply security 100" out of a single diversity
        # number, with import dependence and gas self-sufficiency unreported.
        idx[f"score_{pillar}"] = frame.mean(axis=1).where(wsum == len(frame.columns))
        idx[f"{pillar}_n_components"] = wsum
        for c in frame.columns:
            idx[f"sc_{pillar}_{c}"] = frame[c]

    # unweighted composite (mean of the four pillars, only when all four scored)
    pillar_cols = [f"score_{p}" for p in PILLARS]
    idx["score_composite"] = idx[pillar_cols].mean(axis=1).where(
        idx[pillar_cols].notna().all(axis=1))

    return idx.reset_index()


def _years(df: Optional[pd.DataFrame]) -> Sequence[int]:
    if df is None or df.empty or "calendar_year" not in df.columns:
        return []
    return [int(y) for y in df["calendar_year"].dropna().unique()]


# ══════════════════════ 2. weighting + evaluation year ═══════════════════════

def apply_weights(ind_df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    """Attach the weighted composite score for one pillar-weighting scheme.

    A year scores only when all four pillars were reported for that year.  Nothing
    is carried forward: the earlier `.ffill()` let 2019-2024 print a composite
    built on pillar scores from 2018, so the card's year and the number's year
    disagreed -- the year label said 2024, the evidence said 2018.

    The last honest reading is found by `snapshot_row`, which returns the row it
    actually read, so the page can label the card with that year.
    """
    if ind_df.empty:
        return ind_df
    out = ind_df.copy()
    known = {p: f"score_{p}" for p in weights if f"score_{p}" in out.columns}
    if not known:
        out["score_weighted"] = np.nan
        return out
    pillars = pd.DataFrame({p: pd.to_numeric(out[c], errors="coerce")
                            for p, c in known.items()}, index=out.index)
    total_w = sum(float(weights[p]) for p in pillars.columns) or 1.0
    num = sum(pillars[p] * float(weights[p]) for p in pillars.columns)
    complete = pillars.notna().all(axis=1) & (len(pillars.columns) == len(PILLARS))
    out["score_weighted"] = ((num / total_w).clip(0, 100)).where(complete)
    return out


def pillar_last_seen(ind_df: pd.DataFrame, year: int) -> Dict[str, int]:
    """The year each pillar's most recent score up to `year` actually came from.

    Reporting years differ by pillar (each stops wherever its own sources stop), so
    a "current" pillar score is often several years old and the page has to say
    which year it is reading.
    """
    out: Dict[str, int] = {}
    hist = ind_df[ind_df["calendar_year"] <= year]
    if hist.empty:
        hist = ind_df
    for p in PILLARS:
        col = f"score_{p}"
        year_seen = 0
        if col in hist.columns:
            s = hist[["calendar_year", col]].dropna()
            if not s.empty:
                year_seen = int(s["calendar_year"].iloc[-1])
        out[p] = year_seen
    return out


def snapshot_row(ind_df: pd.DataFrame, year: int) -> pd.Series:
    """Indicator values at the evaluation year.

    If the requested year has no complete weighted score (sparse reporting
    in the final years), the latest earlier year with a finite weighted
    composite is returned instead.
    """
    if ind_df.empty:
        return pd.Series(dtype=float)
    rows = ind_df[ind_df["calendar_year"] == year]
    if rows.empty:
        rows = ind_df[ind_df["calendar_year"] <= year]
        if rows.empty:
            rows = ind_df.iloc[[-1]]
    row = rows.iloc[-1]
    col = "score_weighted" if "score_weighted" in ind_df.columns else "score_composite"
    if pd.isna(row.get(col)):
        ok = ind_df[(ind_df["calendar_year"] <= year)
                    & ind_df[col].notna()]
        if not ok.empty:
            row = ok.iloc[-1]
    return row


def latest_pillar_scores(ind_df: pd.DataFrame, year: int) -> Dict[str, float]:
    """Last observed pillar score up to `year` per pillar (sparse reporting safe).

    The warehouse does not report every component through the same final year
    (e.g. T&D losses stop earlier than generation), so each pillar falls back
    to its own most recent complete observation.
    """
    out: Dict[str, float] = {}
    hist = ind_df[ind_df["calendar_year"] <= year]
    if hist.empty:
        hist = ind_df
    for p in PILLARS:
        col = f"score_{p}"
        val = np.nan
        if col in hist.columns:
            s = hist[col].dropna()
            if not s.empty:
                val = float(s.iloc[-1])
        out[p] = val
    return out


def history_pair(ind_df: pd.DataFrame, col: str, year: int,
                 back: int = 10) -> tuple:
    """Latest value of `col` up to `year`, plus the value `back` years earlier.

    Returns (now, then, then_year); NaN-safe for sparse columns.
    """
    if col not in ind_df.columns:
        return (np.nan, np.nan, year - back)
    hist = ind_df[ind_df["calendar_year"] <= year][["calendar_year", col]].dropna()
    if hist.empty:
        return (np.nan, np.nan, year - back)
    now = float(hist[col].iloc[-1])
    before = hist[hist["calendar_year"] <= year - back]
    if before.empty:
        first = hist.iloc[0]
        return now, float(first[col]), int(first["calendar_year"])
    then_row = before.iloc[-1]
    return now, float(then_row[col]), int(then_row["calendar_year"])


# ══════════════════════ 3. strategy portfolio optimiser ══════════════════════

def strategy_value_density(strategies: List[dict], weights: Dict[str, float]) -> pd.DataFrame:
    """Rank the strategy library by feasibility-discounted weighted impact per $."""
    rows = []
    for s in strategies:
        weighted_impact = sum(weights.get(p, 0.0) * s["pillar_impacts"].get(p, 0.0)
                              for p in PILLARS)
        cost = max(float(s.get("cost_bn_per_year", 1.0)), 0.05)
        feas = float(s.get("feasibility", 60)) / 100.0
        density = weighted_impact / cost * feas
        rows.append({
            "id": s["id"],
            "name": s["name"],
            "short": s.get("short", s["name"][:22]),
            "category": s["category"],
            "cost_bn_per_year": s["cost_bn_per_year"],
            "feasibility": s["feasibility"],
            "lead_years": s["lead_years"],
            "phase": s["phase"],
            "weighted_impact": weighted_impact,
            "density": density,
            **{f"imp_{p}": s["pillar_impacts"].get(p, 0.0) for p in PILLARS},
        })
    df = pd.DataFrame(rows).sort_values("density", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df


def select_optimal_package(strategies: List[dict], weights: Dict[str, float],
                           budget_bn: float) -> dict:
    """Greedy knapsack: fill the annual budget with the densest strategies."""
    ranked = strategy_value_density(strategies, weights)
    chosen: List[dict] = []
    remaining = float(budget_bn)
    for _, r in ranked.iterrows():
        if r["cost_bn_per_year"] <= remaining + 1e-9:
            chosen.append(r.to_dict())
            remaining -= r["cost_bn_per_year"]
    skipped = [r.to_dict() for _, r in ranked.iterrows()
               if r["id"] not in {c["id"] for c in chosen}]
    committed = sum(c["cost_bn_per_year"] for c in chosen)
    pillar_uplift = {
        p: sum(c[f"imp_{p}"] * (c["feasibility"] / 100.0) for c in chosen)
        for p in PILLARS
    }
    return {
        "budget_bn": float(budget_bn),
        "committed_bn": float(committed),
        "unallocated_bn": float(max(budget_bn - committed, 0.0)),
        "chosen": chosen,
        "skipped": skipped,
        "pillar_uplift": pillar_uplift,
    }


# ══════════════════════ 4. pathway projection to horizon ═════════════════════

def _pillar_base_and_slope(ind_df: pd.DataFrame, base_year: int,
                           window: int = 8) -> Dict[str, tuple]:
    """Starting score and yearly drift per pillar, slope clamped for BAU.

    The base is the pillar's own last reported score up to `base_year`, because
    a pillar's record ends whenever its sources end (security trails economy and
    environment).  The projection continues that number, and the page says which year it
    came from -- the years between that last report and 2024 stay blank instead
    of being drawn as a flat line.
    """
    out = {}
    hist = ind_df[ind_df["calendar_year"] <= base_year]
    for p in PILLARS:
        col = f"score_{p}"
        base = 50.0
        slope = 0.0
        if col in hist.columns and not hist.empty:
            sub = hist[["calendar_year", col]].dropna().tail(window)
            if len(sub) >= 3:
                ys = sub["calendar_year"].astype(float)
                vs = sub[col].astype(float)
                base = float(vs.iloc[-1])
                slope = float(np.polyfit(ys, vs, 1)[0])
            elif len(sub) == 1:
                base = float(sub[col].iloc[-1])
        out[p] = (base, float(np.clip(slope, -1.0, 1.5)))
    return out


def project_pathways(ind_df: pd.DataFrame, weights: Dict[str, float],
                     package: dict, base_year: int, horizon: int,
                     strategies: List[dict]) -> pd.DataFrame:
    """Project pillar scores to `horizon` under three development pathways.

    BAU                 -- last observed trend continues, no new strategy.
    Announced Pledges   -- current-policy subset (feasibility >= 60) at half
                          effect, mirroring stated-but-unfunded targets.
    Optimal Package     -- the engine-selected strategies at full effect.

    Strategy effect ramps in linearly over 3 years after each strategy's
    lead time, so near-term years are not over-credited.
    """
    if ind_df.empty:
        return pd.DataFrame()

    strat_by_id = {s["id"]: s for s in strategies}
    baselines = _pillar_base_and_slope(ind_df, base_year)

    def ramp(year: int, lead: int, full: float) -> float:
        dt = year - (base_year + lead)
        if dt < 0:
            return 0.0
        return full * min(dt / 3.0, 1.0)

    def pathway_uplift(pillar: str, year: int, effect: float,
                       ids: Optional[set] = None) -> float:
        total = 0.0
        for c in package["chosen"]:
            if ids is not None and c["id"] not in ids:
                continue
            s = strat_by_id.get(c["id"], c)
            impact = float(s.get("pillar_impacts", {}).get(pillar, 0.0))
            feas = float(s.get("feasibility", 60)) / 100.0
            total += ramp(year, int(s.get("lead_years", 3)), impact * feas) * effect
        return total

    announced_ids = {c["id"] for c in package["chosen"] if c["feasibility"] >= 60}

    rows = []
    for y in range(HISTORY_START, horizon + 1):
        rec = {"calendar_year": y}
        for p in PILLARS:
            base, slope = baselines[p]
            if y <= base_year:
                # Reported years only.  A year whose pillar was not reported
                # stays blank -- holding the last score flat through 2019-2024
                # would draw an unreported year as if the record said it.
                actual = _pillar_actual(ind_df, y, p)
                rec[f"{p}_bau"] = (actual if actual is not None else np.nan)
                rec[f"{p}_announced"] = rec[f"{p}_bau"]
                rec[f"{p}_optimal"] = rec[f"{p}_bau"]
            else:
                bau = np.clip(base + slope * (y - base_year), 0, 100)
                ann = np.clip(bau + pathway_uplift(p, y, 0.5, announced_ids), 0, 100)
                opt = np.clip(bau + pathway_uplift(p, y, 1.0), 0, 100)
                rec[f"{p}_bau"] = bau
                rec[f"{p}_announced"] = ann
                rec[f"{p}_optimal"] = opt
        for pathway in ("bau", "announced", "optimal"):
            vals = [rec[f"{p}_{pathway}"] for p in PILLARS]
            if any(v is None or pd.isna(v) for v in vals):
                # no composite for a year that is missing one of its pillars
                rec[f"composite_{pathway}"] = np.nan
                continue
            num = sum(weights.get(p, 0) * v for p, v in zip(PILLARS, vals))
            den = sum(weights.get(p, 0) for p in PILLARS) or 1.0
            rec[f"composite_{pathway}"] = num / den
        rec["is_actual"] = y <= min(base_year, HISTORY_END)
        rows.append(rec)
    return pd.DataFrame(rows)


def _pillar_actual(ind_df: pd.DataFrame, year: int, pillar: str) -> Optional[float]:
    col = f"score_{pillar}"
    if col not in ind_df.columns:
        return None
    r = ind_df[ind_df["calendar_year"] == year]
    if r.empty:
        return None
    v = r.iloc[0][col]
    return None if pd.isna(v) else float(v)


# ══════════════════════ 5. verdict synthesis ═════════════════════════════════

def build_verdict(ind_df: pd.DataFrame, weights: Dict[str, float], package: dict,
                  pathways: pd.DataFrame, base_year: int, horizon: int) -> dict:
    """One structured answer to Q8 -- what the dashboard's verdict panel shows."""
    if pathways.empty:
        return {}
    hor = pathways[pathways["calendar_year"] == horizon]
    hor = hor.iloc[0] if not hor.empty else pathways.iloc[-1]
    base = snapshot_row(ind_df, base_year)
    now_comp = float(base.get("score_weighted", base.get("score_composite", np.nan)))

    lift = float(hor["composite_optimal"]) - (now_comp if np.isfinite(now_comp)
                                              else float(hor["composite_bau"]))
    avoided_bau_gap = float(hor["composite_optimal"] - hor["composite_bau"])
    pillar_gain = {
        p: float(hor[f"{p}_optimal"] - hor[f"{p}_bau"]) for p in PILLARS
    }
    return {
        "index_now": now_comp,
        "index_optimal": float(hor["composite_optimal"]),
        "index_bau": float(hor["composite_bau"]),
        "lift_to_horizon": lift,
        "gap_vs_bau": avoided_bau_gap,
        "pillar_gain_vs_bau": pillar_gain,
        "top_strategies": [c["name"] for c in package["chosen"][:3]],
        "committed_bn": package["committed_bn"],
        "budget_bn": package["budget_bn"],
        "horizon": horizon,
    }


# ══════════════════════ 6. budget score curve (for Q8 V5) ═══════════════════

def budget_score_curve(ind_df: pd.DataFrame, weights: Dict[str, float],
                       strategies: List[dict], base_year: int, horizon: int,
                       budgets: List[float]) -> pd.DataFrame:
    """For each annual budget, what composite score does the optimal package
    reach at the horizon?  Same engine (select_optimal_package +
    project_pathways), just run once per budget.  The curve answers
    "how much more does the next bn of spend actually buy?" — the shape
    (steep then flat) shows where the money stops helping."""
    rows = []
    for b in budgets:
        if b <= 0:
            rows.append({"budget_bn": float(b), "committed_bn": 0.0,
                         "n_chosen": 0, "composite_at_horizon": np.nan})
            continue
        pkg = select_optimal_package(strategies, weights, float(b))
        pw = project_pathways(ind_df, weights, pkg, base_year, horizon, strategies)
        if pw.empty:
            comp = np.nan
        else:
            hor = pw[pw["calendar_year"] == horizon]
            hor = hor.iloc[0] if not hor.empty else pw.iloc[-1]
            comp = float(hor.get("composite_optimal", np.nan))
        rows.append({
            "budget_bn": float(b),
            "committed_bn": float(pkg["committed_bn"]),
            "n_chosen": int(len(pkg["chosen"])),
            "composite_at_horizon": comp,
        })
    return pd.DataFrame(rows)
