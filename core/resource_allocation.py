"""
core/resource_allocation.py -- question 10:
"What is optimal resource allocation for sustainable development?"

The analysis engine behind the Optimal Resource Allocation dashboard.  It
answers the question with a transparent, solver-free constrained allocation:

    Given the modelled horizon-year generation requirement, split it across
    the seven production technologies so that a three-pillar sustainability
    utility -- least cost, least carbon, least import dependence -- is
    maximised, subject to real resource ceilings (domestic gas availability,
    historical coal/LNG import logistics, hydro & nuclear build limits).

Method
------
1. Technology profiles: purchase cost (US$/MWh, reused from the Q7 cost
   anchors), CO2 intensity (t/MWh, overridable from dim_emission_factor),
   import dependence of the fuel chain, capacity factor.
2. Utility(tech) = w_cost·(1−costₙ) + w_carbon·(1−co2ₙ) + w_security·(1−impₙ),
   with min-max normalisation across technologies and analyst weights
   normalised to sum to 1.
3. Shares are drawn proportional to Utility^pressure (pressure concentrates
   the allocation towards the best-scoring resources), then a water-filling
   loop clamps every technology to its resource ceiling and re-spreads the
   remainder over the still-unconstrained pool.  Anything that still cannot
   be served inside the ceilings is reported as an honest shortfall.
4. The same requirement is allocated the way things stand today (BAU) -- the
   last reported mix frozen forward -- so every output carries a
   last-mix -> plan delta.
5. A sweep from pure-cost to pure-carbon shows what each priority costs and
   emits, and the plan is then scored on six plain things against that mix.

Pure functions: no Streamlit, no MySQL.  Base units GWh, US$, t, BCF, MW;
display conversion happens at render time via core.units.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

import numpy as np
import pandas as pd

from core.cost_forecast import COST_TECHS, unit_cost

# ══════════════════════════════ constants ═══════════════════════════════════

HISTORY_END = 2024
HORIZON = 2035
DEFAULT_DEMAND_GROWTH = 4.5      # %/yr on the reported generation base
DEFAULT_PRESSURE = 3.0           # concentration of the utility weighting
DEFAULT_W_COST, DEFAULT_W_CARBON, DEFAULT_W_SECURITY = 35.0, 40.0, 25.0
DEFAULT_FUEL_INFL = 3.0          # thermal tariff drift, mirrors the Q7 anchor

GEN_COLS = {
    "Hydro": "gen_hydro_gwh",
    "Solar": "gen_solar_gwh",
    "Wind": "gen_wind_gwh",
    "Other RE": "gen_other_renewables_gwh",
    "Nuclear": "gen_nuclear_gwh",
    "Coal": "gen_coal_gwh",
    "Gas": "gen_gas_gwh",
}

# Cradle-to-grave CO2 intensity, t CO2 per MWh (IPCC AR5 median lifecycle
# values; overridden per technology when dim_emission_factor has a match).
CO2_T_PER_MWH: Dict[str, float] = {
    "Hydro": 0.024, "Solar": 0.041, "Wind": 0.011, "Other RE": 0.030,
    "Nuclear": 0.012, "Coal": 0.900, "Gas": 0.440,
}

# Share of each fuel chain that must be imported (Thar coal ~3% logistics,
# RLNG-dominated gas system ~50% imported as of the reported era).
IMPORT_DEPENDENCE: Dict[str, float] = {
    "Hydro": 0.0, "Solar": 0.0, "Wind": 0.0, "Other RE": 0.0,
    "Nuclear": 0.35, "Coal": 0.97, "Gas": 0.50,
}

# Net capacity factors used to size the required installed capacity (MW).
CAPACITY_FACTOR: Dict[str, float] = {
    "Hydro": 0.42, "Solar": 0.19, "Wind": 0.26, "Other RE": 0.30,
    "Nuclear": 0.75, "Coal": 0.70, "Gas": 0.55,
}

# 1 BCF natural gas burns to ~301.9 GWh thermal; at a 53% combined-cycle
# efficiency the delivered electricity is ~150 GWh per BCF.
GWH_PER_BCF_GAS = 150.0

# Ceiling multiples -- how far each resource may stretch beyond its reported
# era anchor before the water-filling loop clamps it.
CEILING_RULES = {
    "Hydro":   ("hist_max", 1.30),     # Indus flow + existing pipeline
    "Solar":   ("hist_max", 6.00),     # fastest build-out headroom
    "Wind":    ("hist_max", 4.00),     # Sindh/Balochistan potential
    "Other RE": ("hist_max", 2.50),
    "Nuclear": ("hist_max", 2.20),     # K-2/K-3 + planned additions
    "Coal":    ("hist_max", 1.80),     # Thar ramp + import logistics
    "Gas":     ("domestic_bcf", None), # hard national-production ceiling
}


# ═════════════════════════ helpers ══════════════════════════════════════════

def _num(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _reading(value) -> float:
    """A history value the source wrote, else NaN.

    Used for the generation base: a NULL cell is an unreported year, not a year
    that reported zero, and the two must not share the same label.
    """
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _minmax(series: pd.Series) -> pd.Series:
    lo, hi = float(series.min()), float(series.max())
    if hi - lo < 1e-12:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def co2_factors(ef_df: Optional[pd.DataFrame]) -> Dict[str, float]:
    """Lifecycle CO2 intensities, overridden by DB emission factors when the
    fuel_type vocabulary matches a technology."""
    out = dict(CO2_T_PER_MWH)
    if ef_df is None or ef_df.empty:
        return out
    key_map = {"coal": "Coal", "gas": "Gas", "natural gas": "Gas",
               "lignite": "Coal", "diesel": None, " furnace oil": None}
    for _, r in ef_df.iterrows():
        fuel = str(r.get("fuel_type", "")).strip().lower()
        tech = key_map.get(fuel)
        val = _num(r.get("emission_factor_tco2_mwh"), float("nan"))
        if tech and math.isfinite(val) and val > 0:
            out[tech] = max(val, 0.05 if tech == "Coal" else 0.02)
    return out


# ══════════════════════════ technology profiles ══════════════════════════════

def build_profiles(hist: pd.DataFrame, fuel_infl: float,
                   ef: Dict[str, float], year: int = HORIZON) -> pd.DataFrame:
    """Static per-technology profile with cost at the given year."""
    rows = []
    for tech in COST_TECHS:
        rows.append({
            "technology": tech,
            "cost_usd_mwh": unit_cost(tech, year, fuel_infl),
            "co2_t_mwh": ef.get(tech, 0.0),
            "import_dep": IMPORT_DEPENDENCE.get(tech, 0.0),
            "cf": CAPACITY_FACTOR.get(tech, 0.4),
            "hist_gwh": _num(hist[GEN_COLS[tech]].max()) if GEN_COLS[tech] in hist.columns else 0.0,
            # Last reported reading for the technology -- NaN when the column is
            # never filled (other renewables), so it contributes nothing rather
            # than a fake zero.
            "gen_last": (_reading(hist.iloc[-1][GEN_COLS[tech]])
                         if GEN_COLS[tech] in hist.columns else float("nan")),
            "gen_year": (int(hist.iloc[-1]["calendar_year"])
                         if GEN_COLS[tech] in hist.columns else 0),
        })
    return pd.DataFrame(rows)


def resource_ceiling(tech: str, prof_row: pd.Series,
                     domestic_gas_bcf: float) -> float:
    """Absolute GWh ceiling for one technology from the documented rules."""
    rule = CEILING_RULES.get(tech, ("hist_max", 2.0))
    if rule[0] == "domestic_bcf":
        # Domestic fields plus the RLNG logistics that already serve the gas
        # system: never below the reported-era run stretched by 25%.
        hist_floor = max(_num(prof_row["hist_gwh"]),
                         _num(prof_row["gen_last"], 0.0), 1.0)
        return max(domestic_gas_bcf * GWH_PER_BCF_GAS, hist_floor * 1.25)
    base = max(_num(prof_row["hist_gwh"]), _num(prof_row["gen_last"], 0.0), 1.0)
    return base * float(rule[1])


# ═════════════════════════ utility & allocation ══════════════════════════════

def utilities(profiles: pd.DataFrame, w_cost: float, w_carbon: float,
              w_security: float) -> pd.Series:
    """Three-pillar utility in [0, 1] for each technology row, indexed by name."""
    tot = max(w_cost + w_carbon + w_security, 1e-9)
    names = list(profiles["technology"])
    wn = _minmax(profiles["cost_usd_mwh"]).set_axis(names)
    en = _minmax(profiles["co2_t_mwh"]).set_axis(names)
    sn = _minmax(profiles["import_dep"]).set_axis(names)
    return ((w_cost / tot) * (1.0 - wn)
            + (w_carbon / tot) * (1.0 - en)
            + (w_security / tot) * (1.0 - sn))


def water_fill(demand_gwh: float, util: pd.Series, caps: pd.Series,
               pressure: float) -> Dict[str, float]:
    """
    Shares proportional to utility^pressure, clamped by ceilings with the
    remainder re-spread over the unconstrained pool.  Returns tech -> GWh and
    an implicit shortfall when the ceilings cannot absorb the demand.
    """
    pool = list(util.index)
    alloc = {}
    remaining = float(demand_gwh)
    for _ in range(len(pool) + 2):                       # bounded iterations
        if remaining <= 1e-9 or not pool:
            break
        w = util[pool] ** max(pressure, 1e-6)
        w = w / w.sum()
        want = {t: remaining * float(w[t]) for t in pool}
        binding = [t for t in pool if want[t] >= caps[t] - 1e-9]
        if not binding:
            alloc.update(want)
            remaining = 0.0
            break
        for t in binding:                                # clamp and continue
            alloc[t] = float(min(want[t], caps[t]))
            remaining -= alloc[t]
            pool.remove(t)
        remaining = max(remaining, 0.0)
    shortfall = max(remaining, 0.0)
    for t in util.index:
        alloc.setdefault(t, 0.0)
    alloc["_shortfall_gwh"] = shortfall
    return alloc


def score_frame(alloc: Dict[str, float], profiles: pd.DataFrame,
                demand_gwh: float) -> dict:
    """Aggregate the four sustainability KPIs of one allocation."""
    techs = [t for t in profiles["technology"]]
    g = np.array([alloc.get(t, 0.0) for t in techs])
    cost = np.array([profiles.set_index("technology")["cost_usd_mwh"][t] for t in techs])
    co2 = np.array([profiles.set_index("technology")["co2_t_mwh"][t] for t in techs])
    imp = np.array([profiles.set_index("technology")["import_dep"][t] for t in techs])
    served = float(g.sum())
    shares = g / served if served > 0 else g
    return {
        "cost_usd": float((g * 1000.0 * cost).sum()),
        "co2_t": float((g * 1000.0 * co2).sum()),
        "import_gwh": float((g * imp).sum()),
        "import_dep_pct": float((shares * imp).sum() * 100.0),
        "re_share_pct": float(sum(g[i] for i, t in enumerate(techs)
                                  if t in ("Hydro", "Solar", "Wind", "Other RE"))
                              / served * 100.0) if served > 0 else 0.0,
        "diversity_hhi": float((shares ** 2).sum()),
        "coverage_pct": float(served / demand_gwh * 100.0) if demand_gwh > 0 else 100.0,
        "gen_gwh": served,
    }


# ═══════════════════════ what each priority buys ═══════════════════════════

def pareto_frontier(demand_gwh: float, profiles: pd.DataFrame,
                    caps: pd.Series, util_cost_carbon: pd.Series,
                    steps: int = 21, pressure: float = DEFAULT_PRESSURE) -> pd.DataFrame:
    """Sweep theta = pure cost (0) -> pure carbon (1); record (cost, CO2).
    Values stay in base units (US$, t) so the page converts them once, at draw
    time, like every other frame this engine returns."""
    names = list(profiles["technology"])
    wn = _minmax(profiles["cost_usd_mwh"]).set_axis(names)
    en = _minmax(profiles["co2_t_mwh"]).set_axis(names)
    rows = []
    for th in np.linspace(0.0, 1.0, steps):
        u = (1.0 - th) * (1.0 - wn) + th * (1.0 - en)
        alloc = water_fill(demand_gwh, u, caps, pressure)
        sc = score_frame(alloc, profiles, demand_gwh)
        rows.append({"theta": float(th), "cost_usd": sc["cost_usd"],
                     "co2_t": sc["co2_t"]})
    return pd.DataFrame(rows)


# ══════════════════════════ how each way scores ═════════════════════════════

RE_POLICY_TARGET_PCT = 60.0   # ARE-style renewable benchmark for the scorecard


def radar_frame(bau: dict, opt: dict) -> pd.DataFrame:
    """Six plain things, scored 0-100 for the last reported mix and for the
    plan. Fixed references keep the two ways on one comparable scale. The
    dimension names are what the reader sees on the chart."""
    def _s(score: dict) -> dict:
        gen_mwh = max(score["gen_gwh"], 1.0) * 1000.0
        cost_per_mwh = score["cost_usd"] / gen_mwh
        co2_per_mwh = score["co2_t"] / gen_mwh
        return {
            "Cheaper power": max(0.0, 100.0 * (1.0 - cost_per_mwh / 80.0)),
            "Lower CO₂": max(0.0, 100.0 * (1.0 - co2_per_mwh / 0.90)),
            "Fuel from home": max(0.0, 100.0 - score["import_dep_pct"]),
            "Source spread": float((1.0 - score["diversity_hhi"]) * 100.0),
            "Clean share": min(score["re_share_pct"] / RE_POLICY_TARGET_PCT * 100.0, 100.0),
            "Demand served": min(max(score["coverage_pct"], 0.0), 100.0),
        }
    b, o = _s(bau), _s(opt)
    return pd.DataFrame({"dimension": list(b.keys()),
                         "bau": list(b.values()),
                         "optimal": list(o.values())})


# ══════════════════════════ master data builder ══════════════════════════════

def build_allocation_data(
    re_df: pd.DataFrame,
    gas_df: Optional[pd.DataFrame] = None,
    ef_df: Optional[pd.DataFrame] = None,
    horizon: int = HORIZON,
    demand_growth_pct: float = DEFAULT_DEMAND_GROWTH,
    w_cost: float = DEFAULT_W_COST,
    w_carbon: float = DEFAULT_W_CARBON,
    w_security: float = DEFAULT_W_SECURITY,
    pressure: float = DEFAULT_PRESSURE,
    fuel_infl_pct: float = DEFAULT_FUEL_INFL,
) -> dict:
    """Everything the Q10 dashboard renders, from raw query frames."""
    h = re_df.copy()
    h["calendar_year"] = pd.to_numeric(h["calendar_year"], errors="coerce")
    h = h.dropna(subset=["calendar_year"]).sort_values("calendar_year")
    h = h.reset_index(drop=True)

    # The mix the plan is measured against comes from the latest year that
    # genuinely reported generation -- 2024 when it did, an earlier year when it
    # did not -- and that year is returned so the page can label it correctly.
    base, base_year = {}, 0
    for idx in range(len(h) - 1, -1, -1):
        row = h.iloc[idx]
        vals = {t: _reading(row[GEN_COLS[t]]) for t in COST_TECHS
                if GEN_COLS[t] in h.columns}
        if any(not math.isnan(v) and v > 0 for v in vals.values()):
            base = {k: v for k, v in vals.items() if not math.isnan(v)}
            base_year = int(row["calendar_year"])
            break
    # Demand on the same year as the mix, so the growth span and the base it
    # compounds from are one reading, not two different years.
    total_base = float(sum(base.values())) if base else 0.0
    if "demand_gwh" in h.columns and base_year:
        d = _reading(h.loc[h["calendar_year"] == base_year, "demand_gwh"].iloc[0])
        if not math.isnan(d) and d > 0:
            total_base = d

    span = max(1, horizon - (base_year or HISTORY_END))
    demand = total_base * (1.0 + demand_growth_pct / 100.0) ** span

    domestic_gas_bcf = 0.0
    gas_reported_year = 0
    if gas_df is not None and not gas_df.empty and "production_bcf" in gas_df.columns:
        g = gas_df.copy()
        g["calendar_year"] = pd.to_numeric(g["calendar_year"], errors="coerce")
        g = g.dropna(subset=["calendar_year"]).sort_values("calendar_year")
        g["production_bcf"] = pd.to_numeric(g["production_bcf"], errors="coerce")
        g = g.dropna(subset=["production_bcf"])
        if not g.empty:
            # The last year gas was actually reported -- filling the tail with
            # zeros would plan national supply on a production the record never
            # claims.
            last_gas = float(g["production_bcf"].iloc[-1])
            gas_reported_year = int(g["calendar_year"].iloc[-1])
            # Domestic fields are depleting: plan on the reported trend floor.
            domestic_gas_bcf = max(last_gas * 0.9, 0.0)

    profiles = build_profiles(h, fuel_infl_pct, co2_factors(ef_df), year=horizon)
    util = utilities(profiles, w_cost, w_carbon, w_security)
    caps = pd.Series(
        [resource_ceiling(t, profiles.iloc[i], domestic_gas_bcf)
         for i, t in enumerate(profiles["technology"])],
        index=list(profiles["technology"]),
    )

    opt_alloc = water_fill(demand, util, caps, pressure)

    # BAU: the reported mix frozen forward onto the same requirement
    base_total = float(sum(base.values())) if base else 0.0
    bau_alloc = {t: demand * (base.get(t, 0.0) / base_total)
                 for t in COST_TECHS} if base_total > 0 else {}
    bau_alloc["_shortfall_gwh"] = 0.0

    opt_score = score_frame(opt_alloc, profiles, demand)
    bau_score = score_frame(bau_alloc, profiles, demand)

    alloc_tbl = pd.DataFrame([{
        "technology": t,
        "optimal_gwh": opt_alloc.get(t, 0.0),
        "bau_gwh": bau_alloc.get(t, 0.0),
        "ceiling_gwh": float(caps[t]),
        "optimal_share_pct": opt_alloc.get(t, 0.0) / max(opt_score["gen_gwh"], 1.0) * 100.0,
        "cost_usd": opt_alloc.get(t, 0.0) * 1000.0
                    * float(profiles.loc[profiles["technology"] == t, "cost_usd_mwh"].iloc[0]),
        "co2_t": opt_alloc.get(t, 0.0) * 1000.0
                 * float(profiles.loc[profiles["technology"] == t, "co2_t_mwh"].iloc[0]),
        "capacity_mw": opt_alloc.get(t, 0.0) / 8.760
                       / max(float(profiles.loc[profiles["technology"] == t,
                                                "cf"].iloc[0]), 0.05),
    } for t in COST_TECHS])
    alloc_tbl["delta_gwh"] = alloc_tbl["optimal_gwh"] - alloc_tbl["bau_gwh"]
    alloc_tbl["clamped"] = alloc_tbl["optimal_gwh"] >= alloc_tbl["ceiling_gwh"] - 1e-6

    frontier = pareto_frontier(demand, profiles, caps, util, pressure=pressure)
    radar = radar_frame(bau_score, opt_score)

    gas_need_bcf = opt_alloc.get("Gas", 0.0) / GWH_PER_BCF_GAS
    gas_ss_pct = min(domestic_gas_bcf / gas_need_bcf, 1.0) * 100.0 if gas_need_bcf > 0 else 100.0

    return {
        "profiles": profiles,
        "utility": util,
        "allocation": alloc_tbl,
        "bau_score": bau_score,
        "opt_score": opt_score,
        "pareto": frontier,
        "radar": radar,
        "demand_gwh": demand,
        "total_base_gwh": total_base,
        "base_year": base_year,
        "gas_reported_year": gas_reported_year,
        "shortfall_gwh": opt_alloc.get("_shortfall_gwh", 0.0),
        "domestic_gas_bcf": domestic_gas_bcf,
        "gas_need_bcf": gas_need_bcf,
        "gas_self_sufficiency_pct": gas_ss_pct,
        "horizon": horizon,
        "demand_growth_pct": demand_growth_pct,
        "weights": {"cost": w_cost, "carbon": w_carbon, "security": w_security},
        "pressure": pressure,
        "fuel_infl_pct": fuel_infl_pct,
    }
