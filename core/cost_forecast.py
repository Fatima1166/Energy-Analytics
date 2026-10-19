"""
core/cost_forecast.py -- question 7: "What is the forecasted cost of energy power producers?"

The analysis engine behind the Forecasted Power Producer Cost dashboard
(1999-2035).  Electricity is bought from power producers (IPPs / GENCOs)
through per-technology purchase contracts, so the total cost of energy from
power producers is decomposed as:

    cost_year = Σ  generation(technology, year) × unit purchase cost(technology, year)

1. Historical reported generation by technology (GWh) is multiplied by a
   calibrated implied unit-purchase-cost table (US$/MWh, anchored on 2024) to
   produce the reported-era producer cost.
2. Future cost is projected under three deployment scenarios mirroring the
   GCIS-style question:  "Minimum RE", "Reference" and "RE 50%".
3. Renewable unit costs follow a learning curve (declining), thermal fuels
   follow an escalation rate chosen by the analyst.
4. Cumulative cost avoidance of the RE 50% path vs the Minimum RE path and
   fuel-price sensitivity bands quantify the answer to the question.

Pure functions: does not interact directly with Streamlit or MySQL.
All monetary values are in constant-USD base units; conversion to bn / mn is
handled at render time by core.units (domain: "cost").
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from core.supply_forecast import (
    ACTUAL,
    DEFAULT_BASE_GDP_GROWTH,
    DEFAULT_CALIB_START,
    FORECAST_START,
    HISTORY_END,
    HORIZON,
    PROJECTED,
    build_history,
    fit_supply_model,
    forecast_supply_path,
    scenario_supply_growth,
)

# ══════════════════════════════ constants ═══════════════════════════════════

COST_TECHS = ["Hydro", "Solar", "Wind", "Other RE", "Nuclear", "Coal", "Gas"]

# Column in the reported history (fact_renewable_energy) for each technology
HIST_COL = {
    "Hydro": "gen_hydro_gwh",
    "Solar": "gen_solar_gwh",
    "Wind": "gen_wind_gwh",
    "Other RE": "gen_other_renewables_gwh",
    "Nuclear": "gen_nuclear_gwh",
    "Coal": "gen_coal_gwh",
    "Gas": "gen_gas_gwh",
}

TECH_COLORS = {
    "Hydro": "#0284C7",
    "Solar": "#F59E0B",
    "Wind": "#10B981",
    "Other RE": "#34D399",
    "Nuclear": "#A78BFA",
    "Coal": "#6B7280",
    "Gas": "#F97316",
}

# Implied average purchase cost paid to power producers, anchored on 2024
# (US$/MWh, includes energy + capacity / fixed-O&M recovery in the tariff).
UNIT_COST_2024: Dict[str, float] = {
    "Hydro": 32.0,
    "Solar": 38.0,
    "Wind": 42.0,
    "Other RE": 55.0,
    "Nuclear": 60.0,
    "Coal": 55.0,
    "Gas": 75.0,
}

# Annual cost drift per technology.  Renewables learn downwards; firm clean
# plant drifts with general O&M inflation.  Thermal entries are None: their
# cost is linked to the analyst's fuel-price escalation setting instead.
UNIT_TREND: Dict[str, Optional[float]] = {
    "Hydro": 0.015,
    "Solar": -0.040,
    "Wind": -0.025,
    "Other RE": -0.010,
    "Nuclear": 0.020,
    "Coal": None,
    "Gas": None,
}

# Sensitivity of each thermal technology's purchase price to the fuel-price
# escalation assumption (Gas / RLNG contracts are the more exposed one).
FUEL_PASSTHROUGH = {"Coal": 1.00, "Gas": 1.15}

MIN_UNIT_COST = 15.0  # floor, US$/MWh, keeps back-casting physically sane

DEFAULT_FUEL_INFL = 3.0
DEFAULT_SPREAD_PP = 2.0

COST_SCENARIO_ORDER = ["Minimum RE", "Reference", "RE 50%"]
COST_SCENARIO_COLORS = {
    "Minimum RE": "#EF4444",   # red    -- thermal-heavy, highest system cost
    "Reference": "#00A6FB",    # blue   -- IGCEP-style reference build-out
    "RE 50%": "#10B981",       # green  -- aggressive renewable deployment
}
COST_SCENARIO_BADGES = {
    "Minimum RE": "stalled RE uptake, thermal-heavy import exposure",
    "Reference": "national reference generation plan",
    "RE 50%": "50% renewable share by the horizon year",
}

# Deployment scenario knobs.  Total generation is identical across scenarios
# (same demand serves every case) -- only the mix, and hence the producer
# cost bill, differs, exactly as in the question's framing.
COST_SCENARIO_PARAMS: Dict[str, dict] = {
    "Minimum RE": {
        "re_target_pct": None,      # None -> grow from 2024 share by re_gain_pp
        "re_gain_pp": 1.0,
        "sw_weight": 0.25,          # share of solar+wind within the RE bucket
        "nuc_shift_pp": 0.0,
        "coal_split": 0.58,         # coal vs gas split of the thermal remainder
    },
    "Reference": {
        "re_target_pct": None,
        "re_gain_pp": 5.0,
        "sw_weight": 0.45,
        "nuc_shift_pp": 0.0,
        "coal_split": 0.50,
    },
    "RE 50%": {
        "re_target_pct": 50.0,
        "re_gain_pp": None,
        "sw_weight": 0.62,
        "nuc_shift_pp": -2.0,
        "coal_split": 0.45,
    },
}

TECH_TO_SCENARIO = {
    "Hydro": "clean", "Solar": "re", "Wind": "re", "Other RE": "re",
    "Nuclear": "clean", "Coal": "thermal", "Gas": "thermal",
}


# ═════════════════════════ small numeric helpers ════════════════════════════

def _num(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _cagr(first: float, last: float, periods: int) -> float:
    if periods <= 0 or first <= 0 or last <= 0:
        return float("nan")
    return ((last / first) ** (1.0 / periods) - 1.0) * 100.0


def _metrics(actual, predicted) -> dict:
    a = np.asarray([float(v) for v in actual], dtype=float)
    p = np.asarray([float(v) for v in predicted], dtype=float)
    mask = np.isfinite(a) & np.isfinite(p) & (a > 0)
    a, p = a[mask], p[mask]
    if a.size == 0:
        return {"mape_pct": float("nan"), "bias_pct": float("nan"), "n": 0}
    pe = (p - a) / a
    return {
        "mape_pct": float(np.abs(pe).mean() * 100.0),
        "bias_pct": float(pe.mean() * 100.0),
        "n": int(a.size),
    }


# ═════════════════════════ unit cost curves ═════════════════════════════════

def unit_cost(tech: str, year: int, fuel_infl_pct: float,
              anchor_year: int = HISTORY_END) -> float:
    """Implied producer purchase price (US$/MWh) for one technology-year."""
    anchor = UNIT_COST_2024.get(tech)
    if anchor is None:
        return float("nan")
    n = year - anchor_year
    trend = UNIT_TREND.get(tech)
    if trend is None:
        rate = (fuel_infl_pct / 100.0) * FUEL_PASSTHROUGH.get(tech, 1.0)
    else:
        rate = trend
    value = anchor * ((1.0 + rate) ** n)
    return max(MIN_UNIT_COST, value)


def unit_cost_table(years: Sequence[int], fuel_infl_pct: float) -> pd.DataFrame:
    """[year × technology] matrix of implied purchase prices (US$/MWh)."""
    rows = {
        tech: [unit_cost(tech, int(y), fuel_infl_pct) for y in years]
        for tech in COST_TECHS
    }
    return pd.DataFrame({"calendar_year": [int(y) for y in years], **rows})


# ═════════════════════════ cost history ═════════════════════════════════════

def build_cost_history(hist: pd.DataFrame, fuel_infl_pct: float) -> pd.DataFrame:
    """Per-year reported generation × implied unit costs -> producer cost bill."""
    h = hist[hist["calendar_year"] >= 2000].copy()
    h = h.dropna(subset=["gen_total_gwh"])
    h = h[h["gen_total_gwh"] > 0].sort_values("calendar_year")
    if h.empty:
        return h

    h = h.reset_index(drop=True)
    for tech in COST_TECHS:
        col = HIST_COL[tech]
        if col in h.columns:
            h[f"gen_{tech.lower().replace(' ', '_')}_gwh"] = (
                pd.to_numeric(h[col], errors="coerce").fillna(0.0)
            )
        else:
            h[f"gen_{tech.lower().replace(' ', '_')}_gwh"] = 0.0

    table = unit_cost_table(h["calendar_year"].values, fuel_infl_pct)
    for tech in COST_TECHS:
        key = tech.lower().replace(" ", "")
        h[f"cost_{key}_usd"] = (
            h[f"gen_{tech.lower().replace(' ', '_')}_gwh"].values * 1000.0
            * table[tech].values
        )
    cost_cols = [f"cost_{t.lower().replace(' ', '')}_usd" for t in COST_TECHS]
    h["cost_total_usd"] = h[cost_cols].sum(axis=1)
    h["avg_usd_per_mwh"] = h["cost_total_usd"] / (h["gen_total_gwh"] * 1000.0)

    gen_cols = [f"gen_{t.lower().replace(' ', '_')}_gwh" for t in COST_TECHS]
    h["gen_re_bucket_gwh"] = (h["gen_solar_gwh"] + h["gen_wind_gwh"]
                              + h["gen_hydro_gwh"] + h["gen_other_re_gwh"])
    h["re_share_pct"] = np.where(h["gen_total_gwh"] > 0,
                                 h["gen_re_bucket_gwh"] / h["gen_total_gwh"] * 100.0, 0.0)
    h["fuel_cost_share_pct"] = np.where(
        h["cost_total_usd"] > 0,
        (h["cost_coal_usd"] + h["cost_gas_usd"]) / h["cost_total_usd"] * 100.0,
        0.0,
    )
    h["provenance"] = ACTUAL
    keep = (["calendar_year", "provenance", "real_gdp_idx", "gen_total_gwh",
             "re_share_pct", "avg_usd_per_mwh", "cost_total_usd",
             "fuel_cost_share_pct"]
            + [f"gen_{t.lower().replace(' ', '_')}_gwh" for t in COST_TECHS]
            + cost_cols)
    return h[keep].reset_index(drop=True)


# ═════════════════════════ scenario mix & cost paths ════════════════════════

def _baseline_mix(hist_cost: pd.DataFrame) -> dict:
    """2024 shares that every deployment scenario branches from."""
    last = hist_cost.iloc[-1]
    tot = _num(last["gen_total_gwh"])
    re_bucket = _num(last["gen_solar_gwh"]) + _num(last["gen_wind_gwh"]) + \
        _num(last["gen_hydro_gwh"]) + _num(last["gen_other_re_gwh"])
    sw = _num(last["gen_solar_gwh"]) + _num(last["gen_wind_gwh"])
    return {
        "year": int(last["calendar_year"]),
        "re_share": (re_bucket / tot) if tot > 0 else 0.35,
        "nuc_share": (_num(last["gen_nuclear_gwh"]) / tot) if tot > 0 else 0.12,
        "sw_weight": (sw / re_bucket) if re_bucket > 0 else 0.35,
    }


def project_cost_scenarios(
    hist_cost: pd.DataFrame,
    total_path: Dict[int, float],
    scenarios: Sequence[str],
    horizon: int,
    fuel_infl_pct: float,
) -> pd.DataFrame:
    """
    For each deployment scenario, project the generation mix on the SAME total
    generation path, price every technology and return per-year cost frames.
    """
    base = _baseline_mix(hist_cost)
    start_year = base["year"]
    span = max(1, horizon - start_year)
    rows: List[dict] = []

    table = unit_cost_table(range(start_year + 1, horizon + 1), fuel_infl_pct)
    ucost = table.set_index("calendar_year")

    for sc in scenarios:
        p = COST_SCENARIO_PARAMS.get(sc, COST_SCENARIO_PARAMS["Reference"])
        target_re = (p["re_target_pct"] / 100.0 if p["re_target_pct"] is not None
                     else base["re_share"] + (p["re_gain_pp"] or 0.0) / 100.0)
        for yr in range(start_year + 1, horizon + 1):
            progress = (yr - start_year) / span
            tot = total_path.get(yr, 0.0)
            re_share = base["re_share"] + (target_re - base["re_share"]) * progress
            nuc_share = max(0.0, base["nuc_share"] + (p["nuc_shift_pp"] / 100.0) * progress)
            re_share = min(max(re_share, 0.0), 1.0 - nuc_share)
            thermal_share = max(0.0, 1.0 - re_share - nuc_share)

            sw_weight = base["sw_weight"] + (p["sw_weight"] - base["sw_weight"]) * progress
            re_gwh = tot * re_share
            sw_gwh = re_gwh * sw_weight
            rest_gwh = re_gwh - sw_gwh
            # Distribute solar+wind in 2024 proportion; balance to hydro / other RE
            sol24 = _num(hist_cost.iloc[-1]["gen_solar_gwh"])
            wnd24 = _num(hist_cost.iloc[-1]["gen_wind_gwh"])
            sol_w = sol24 / (sol24 + wnd24) if (sol24 + wnd24) > 0 else 0.5
            gen = {
                "Solar": sw_gwh * sol_w,
                "Wind": sw_gwh * (1.0 - sol_w),
                "Hydro": rest_gwh * 0.90,
                "Other RE": rest_gwh * 0.10,
                "Nuclear": tot * nuc_share,
                "Coal": thermal_share * tot * p["coal_split"],
                "Gas": thermal_share * tot * (1.0 - p["coal_split"]),
            }
            row = {
                "scenario": sc,
                "calendar_year": yr,
                "provenance": PROJECTED,
                "gen_total_gwh": tot,
                "re_share_pct": re_share * 100.0,
            }
            cost_total = 0.0
            for tech in COST_TECHS:
                uc = float(ucost.loc[yr, tech])
                c = gen[tech] * 1000.0 * uc
                row[f"gen_{tech.lower().replace(' ', '_')}_gwh"] = gen[tech]
                row[f"cost_{tech.lower().replace(' ', '')}_usd"] = c
                cost_total += c
            row["cost_total_usd"] = cost_total
            row["avg_usd_per_mwh"] = (cost_total / (tot * 1000.0)) if tot > 0 else float("nan")
            row["fuel_cost_share_pct"] = (
                (row["cost_coal_usd"] + row["cost_gas_usd"]) / cost_total * 100.0
                if cost_total > 0 else 0.0
            )
            rows.append(row)

    return pd.DataFrame(rows)


# ═════════════════════════ cost avoidance & sensitivity ═════════════════════

def avoided_cost(fc: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Annual + cumulative producer-cost difference between the two bookends."""
    if fc.empty or "Minimum RE" not in set(fc["scenario"]) or "RE 50%" not in set(fc["scenario"]):
        return pd.DataFrame()
    lo = fc[fc["scenario"] == "RE 50%"].sort_values("calendar_year")
    hi = fc[fc["scenario"] == "Minimum RE"].sort_values("calendar_year")
    df = pd.DataFrame({
        "calendar_year": lo["calendar_year"].values,
        "cost_re50_usd": lo["cost_total_usd"].values,
        "cost_minre_usd": hi["cost_total_usd"].values,
    })
    df["delta_usd"] = df["cost_minre_usd"] - df["cost_re50_usd"]
    df["cumulative_usd"] = df["delta_usd"].cumsum()
    return df


def fuel_price_sensitivity(
    hist_cost: pd.DataFrame,
    total_path: Dict[int, float],
    horizon: int,
    fuel_infl_pct: float,
    spread_pp: float = DEFAULT_SPREAD_PP,
) -> pd.DataFrame:
    """Reference-scenario cost under low / base / high fuel escalation."""
    frames = []
    for label, rate in ((f"Fuel −{spread_pp:.0f}pp", fuel_infl_pct - spread_pp),
                        ("Base", fuel_infl_pct),
                        (f"Fuel +{spread_pp:.0f}pp", fuel_infl_pct + spread_pp)):
        fc = project_cost_scenarios(hist_cost, total_path, ["Reference"], horizon, rate)
        if fc.empty:
            continue
        fc = fc.rename(columns={"cost_total_usd": f"cost_{label}_usd"})
        frames.append(fc[["calendar_year", f"cost_{label}_usd"]])
    if not frames:
        return pd.DataFrame()
    out = frames[0]
    for f in frames[1:]:
        out = pd.merge(out, f, on="calendar_year", how="outer")
    return out.sort_values("calendar_year").reset_index(drop=True)


# ═════════════════════════ model backtest ═══════════════════════════════════

def backtest_cost_model(hist_cost: pd.DataFrame,
                        calib_start: int = DEFAULT_CALIB_START,
                        train_end: int = 2020,
                        test_end: int = HISTORY_END) -> dict:
    """
    Hold-out validation of the cost model: fit GDP-elasticity and trend growth
    on the cost bill <= train_end, predict 2021-2024, compare with the priced
    actuals.  (Generation mix, unit-cost anchors and the GDP driver chain are
    all frozen at the training cut.)
    """
    train = hist_cost[hist_cost["calendar_year"] <= train_end]
    test = hist_cost[(hist_cost["calendar_year"] > train_end)
                     & (hist_cost["calendar_year"] <= test_end)]
    if len(train[train["calendar_year"] >= calib_start]) < 3 or test.empty:
        return {"table": pd.DataFrame(), "paths": pd.DataFrame()}

    model = fit_supply_model(hist_cost, "cost_total_usd", calib_start, train_end)
    grows = scenario_supply_growth(model, ["Base"], DEFAULT_BASE_GDP_GROWTH, 0.0, "Driver")
    g_driver = grows["Base"]["growth_pct"] / 100.0
    g_trend = model["trend_growth_pct"] / 100.0

    anchor = float(train["cost_total_usd"].iloc[-1])
    rows = []
    for _, r in test.iterrows():
        yr = int(r["calendar_year"])
        rows.append({
            "calendar_year": yr,
            "actual": float(r["cost_total_usd"]),
            "predicted_driver": anchor * (1.0 + g_driver) ** (yr - train_end),
            "predicted_trend": anchor * (1.0 + g_trend) ** (yr - train_end),
        })
    paths = pd.DataFrame(rows)

    met_d = _metrics(paths["actual"], paths["predicted_driver"])
    met_t = _metrics(paths["actual"], paths["predicted_trend"])
    table = pd.DataFrame([
        {"model": "GDP-Driver", "mape_pct": met_d["mape_pct"], "bias_pct": met_d["bias_pct"],
         "is_winner": met_d["mape_pct"] <= met_t["mape_pct"]},
        {"model": "Trend", "mape_pct": met_t["mape_pct"], "bias_pct": met_t["bias_pct"],
         "is_winner": met_t["mape_pct"] < met_d["mape_pct"]},
    ])
    return {"train_end": train_end, "table": table, "paths": paths}


# ═════════════════════════ master data builder ══════════════════════════════

def build_cost_dashboard_data(
    re_df: pd.DataFrame,
    econ_df: pd.DataFrame,
    gen_df: Optional[pd.DataFrame] = None,
    lng_df: Optional[pd.DataFrame] = None,
    scenarios: Sequence[str] = tuple(COST_SCENARIO_ORDER),
    calib_start: int = DEFAULT_CALIB_START,
    horizon: int = HORIZON,
    base_gdp_growth: float = DEFAULT_BASE_GDP_GROWTH,
    fuel_infl_pct: float = DEFAULT_FUEL_INFL,
    sensitivity_spread_pp: float = DEFAULT_SPREAD_PP,
) -> dict:
    """Everything the Q7 dashboard needs, from raw query frames."""
    hist = build_history(pd.DataFrame(), re_df, econ_df, gen_df)

    # Total generation path: one demand story shared by every cost scenario
    model = fit_supply_model(hist, "gen_total_gwh", calib_start, HISTORY_END)
    grows = scenario_supply_growth(model, ["Base"], base_gdp_growth, 0.0, "Driver")
    fc_total = forecast_supply_path(hist, "gen_total_gwh", grows, horizon)

    total_path: Dict[int, float] = {}
    for _, r in hist.iterrows():
        v = _num(r.get("gen_total_gwh"), float("nan"))
        if not math.isnan(v) and v > 0:
            total_path[int(r["calendar_year"])] = v
    for _, r in fc_total.iterrows():
        total_path[int(r["calendar_year"])] = float(r["value"])

    hist_cost = build_cost_history(hist, fuel_infl_pct)
    fc_cost = project_cost_scenarios(hist_cost, total_path, scenarios, horizon, fuel_infl_pct)
    delta = avoided_cost(fc_cost, horizon)
    sensitivity = fuel_price_sensitivity(hist_cost, total_path, horizon,
                                         fuel_infl_pct, sensitivity_spread_pp)
    backtest = backtest_cost_model(hist_cost, calib_start=calib_start)

    # Fuel-price context from the reported LNG bill (volume + value)
    lng = lng_df.copy() if lng_df is not None and not lng_df.empty else pd.DataFrame()
    if not lng.empty:
        lng["calendar_year"] = pd.to_numeric(lng["calendar_year"], errors="coerce")
        lng = lng.dropna(subset=["calendar_year"])
        lng["calendar_year"] = lng["calendar_year"].astype(int)
        for c in ("imports_bcf", "imports_value_musd"):
            lng[c] = pd.to_numeric(lng[c], errors="coerce")
        lng = lng.sort_values("calendar_year").reset_index(drop=True)

    return {
        "history": hist_cost,
        "forecast": fc_cost,
        "avoided": delta,
        "sensitivity": sensitivity,
        "backtest": backtest,
        "lng": lng,
        "total_path": total_path,
        "models": {"gen_total_gwh": model},
        "calib_start": calib_start,
        "horizon": horizon,
        "base_gdp_growth": base_gdp_growth,
        "fuel_infl_pct": fuel_infl_pct,
        "sensitivity_spread_pp": sensitivity_spread_pp,
        "scenarios": list(scenarios),
        "history_end": HISTORY_END,
    }
