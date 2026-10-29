"""
core/supply_forecast.py -- question 5: "What is forecasted energy supply?"

The analysis engine behind the Forecasted Energy Supply dashboard (1999-2035).
Takes raw query DataFrames and computes:
1. Historical supply trajectory (Primary Energy Supply TOE, Power Generation GWh, Capacity MW)
2. Econometric driver & trend models (GDP elasticity, capacity factor expansion)
3. Scenario projections (Low / Base / High) to 2035
4. Fuel and technology supply mix evolution (Hydro, Solar, Wind, Nuclear, Coal, Gas)
5. Clean Energy (60% benchmark) & Alternative Renewable Energy (ARE 30%) policy tracking
6. Generation capacity additions (MW) & technology requirements
7. Supply adequacy & system reserve margin (Supply vs Demand GWh)
8. Energy security & import vulnerability (Domestic vs Imported supply)
9. Hold-out backtesting (MAPE, RMSE, Bias, R²)

Pure functions: does not interact directly with Streamlit or MySQL, ensuring testability.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# ══════════════════════════════ constants ═══════════════════════════════════

ACTUAL = "Actual"
PROJECTED = "Projected"

HISTORY_START = 1999
PRIMARY_START = 2002
HISTORY_END = 2024
FORECAST_START = 2025
HORIZON = 2035

DEFAULT_CALIB_START = 2012
DEFAULT_TEST_YEARS = 4
BACKTEST_TRAIN_END = HISTORY_END - DEFAULT_TEST_YEARS  # 2020

SCENARIO_ORDER = ["Low", "Base", "High"]
SCENARIO_COLORS = {
    "Low": "#F59E0B",     # amber
    "Base": "#00A6FB",    # bright cyan/blue
    "High": "#10B981",    # emerald green
}
SCENARIO_BADGES = {
    "Low": "conservative / delayed capex",
    "Base": "IGCEP reference plan",
    "High": "accelerated green transition",
}

DEFAULT_BASE_GDP_GROWTH = 4.0
DEFAULT_SCENARIO_SPREAD = 1.5
CLEAN_POLICY_TARGET_DEFAULT = 60.0  # 60% clean energy by 2030/2035
ARE_POLICY_TARGET = 30.0            # 30% solar + wind by 2030

# Colors for fuel sources
FUEL_COLORS = {
    "Hydro": "#0284C7",        # blue
    "Solar": "#F59E0B",        # amber/gold
    "Wind": "#10B981",         # green
    "Other RE": "#34D399",     # light green
    "Nuclear": "#A78BFA",      # purple
    "Coal": "#6B7280",         # slate/grey
    "Gas / RLNG": "#F97316",   # orange
    "Oil / Thermal": "#EF4444",# red
    "Domestic Gas": "#FB923C",
    "LNG Imports": "#EA580C",
    "Indigenous Coal": "#4B5563",
    "Imported Coal": "#9CA3AF",
}


# ═════════════════════════════ small maths ══════════════════════════════════

def _num(value, default: float = 0.0) -> float:
    """None / NaN safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _clean(value) -> float:
    """Float or NaN."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _cagr(first: float, last: float, periods: int) -> float:
    """Compound annual growth rate, in percent."""
    if periods <= 0 or not math.isfinite(_clean(first)) or not math.isfinite(_clean(last)):
        return float("nan")
    if first <= 0 or last <= 0:
        return float("nan")
    return ((last / first) ** (1.0 / periods) - 1.0) * 100.0


def _lstsq(columns: Sequence[Sequence[float]], y: Sequence[float]) -> dict:
    """
    Least squares regression: y = b0 + b1*x1 + ...
    """
    arrays = [np.asarray([_clean(v) for v in col], dtype=float) for col in columns]
    ys = np.asarray([_clean(v) for v in y], dtype=float)
    if not arrays:
        return {"coef": [], "r2": float("nan"), "n": 0}

    mask = np.isfinite(ys)
    for arr in arrays:
        mask &= np.isfinite(arr)
    arrays = [arr[mask] for arr in arrays]
    ys = ys[mask]
    n = int(ys.size)
    if n < 3:
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"), "n": n}

    used, design_cols = [], []
    for i, arr in enumerate(arrays):
        if float(np.ptp(arr)) == 0.0:
            continue
        used.append(i)
        design_cols.append(arr)

    design = np.column_stack([np.ones(n)] + design_cols)
    if design.shape[1] > n:
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"), "n": n}
    try:
        coef, *_ = np.linalg.lstsq(design, ys, rcond=None)
    except np.linalg.LinAlgError:
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"), "n": n}

    fitted = design @ coef
    ss_res = float(((ys - fitted) ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    full = [float(coef[0])]
    idx = 1
    for i in range(len(arrays)):
        if i in used:
            full.append(float(coef[idx]))
            idx += 1
        else:
            full.append(0.0)
    return {"coef": full, "r2": float(r2), "n": n}


def _metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict:
    """MAPE %, RMSE, R2 and bias % for hold-out comparison."""
    a = np.asarray([_clean(v) for v in actual], dtype=float)
    p = np.asarray([_clean(v) for v in predicted], dtype=float)
    mask = np.isfinite(a) & np.isfinite(p) & (a > 0)
    a, p = a[mask], p[mask]
    if a.size == 0:
        return {"mape_pct": float("nan"), "rmse": float("nan"),
                "r2": float("nan"), "bias_pct": float("nan"), "n": 0}
    pe = (p - a) / a
    mape = float(np.abs(pe).mean() * 100.0)
    rmse = float(np.sqrt(((p - a) ** 2).mean()))
    bias = float(pe.mean() * 100.0)
    ss_res = float(((a - p) ** 2).sum())
    ss_tot = float(((a - a.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"mape_pct": mape, "rmse": rmse, "r2": r2, "bias_pct": bias, "n": int(a.size)}


# ═════════════════════════════ history assembly ═════════════════════════════

def build_history(
    primary_df: pd.DataFrame,
    re_df: pd.DataFrame,
    econ_df: pd.DataFrame,
    gen_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Assembles historical energy supply and economic indicators on a single year axis (1999–2024).
    All data is kept in canonical base storage units:
    - Primary supply in TOE
    - Power generation in GWh
    - Capacity in MW
    - GDP in current USD, GDP growth in %, Population in persons.
    """
    years = pd.DataFrame({"calendar_year": range(HISTORY_START, HISTORY_END + 1)})

    # 1. Economic indicators & chained real GDP index
    ec = econ_df.copy()
    if not ec.empty and "calendar_year" in ec.columns:
        ec = ec.sort_values("calendar_year").drop_duplicates(subset=["calendar_year"])
        ec["calendar_year"] = ec["calendar_year"].astype(int)
        ec["gdp_usd"] = pd.to_numeric(ec["gdp_current_usd"], errors="coerce")
        ec["gdp_growth_pct"] = pd.to_numeric(ec["gdp_growth_pct"], errors="coerce")
        ec["population"] = pd.to_numeric(ec["population"], errors="coerce")
    else:
        ec = pd.DataFrame(columns=["calendar_year", "gdp_usd", "gdp_growth_pct", "population"])

    merged = pd.merge(years, ec[["calendar_year", "gdp_usd", "gdp_growth_pct", "population"]],
                      on="calendar_year", how="left")

    # Chain real GDP index (100 in 2000)
    rates = merged["gdp_growth_pct"].fillna(DEFAULT_BASE_GDP_GROWTH).values
    factors = 1.0 + np.clip(rates, -20.0, 30.0) / 100.0
    real_gdp = np.ones(len(factors), dtype=float) * 100.0
    idx_2000 = list(merged["calendar_year"]).index(2000) if 2000 in list(merged["calendar_year"]) else 0
    for i in range(idx_2000 + 1, len(real_gdp)):
        real_gdp[i] = real_gdp[i - 1] * factors[i]
    for i in range(idx_2000 - 1, -1, -1):
        real_gdp[i] = real_gdp[i + 1] / factors[i + 1]
    merged["real_gdp_idx"] = real_gdp

    # 2. Primary energy supply (TOE)
    if not primary_df.empty:
        pdf = primary_df.copy()
        pdf["calendar_year"] = pd.to_numeric(pdf["calendar_year"], errors="coerce")
        pdf = pdf.dropna(subset=["calendar_year"])
        pdf["calendar_year"] = pdf["calendar_year"].astype(int)
        pdf["supply_toe"] = pd.to_numeric(pdf["supply_toe"], errors="coerce")
        pdf["imports_toe"] = pd.to_numeric(pdf["imports_toe"], errors="coerce")

        # Total primary supply & total imports per year.  min_count=1 keeps a
        # year whose import rows are absent blank instead of reporting "imported
        # nothing", which is the difference between a zero and no evidence.
        tpes_tot = pdf.groupby("calendar_year")[['supply_toe', 'imports_toe']].sum(
            min_count=1).reset_index()
        tpes_tot.rename(columns={"supply_toe": "tpes_toe", "imports_toe": "imports_toe"}, inplace=True)
        tpes_tot["domestic_toe"] = np.maximum(0.0, tpes_tot["tpes_toe"] - tpes_tot["imports_toe"])
        tpes_tot["import_share_pct"] = np.where(
            tpes_tot["tpes_toe"] > 0,
            (tpes_tot["imports_toe"] / tpes_tot["tpes_toe"]) * 100.0,
            np.nan
        )

        # Source breakdown.  A (year, source) cell the table never wrote stays
        # blank in the stack instead of being drawn as a zero-supply source.
        p_piv = pdf.pivot_table(index="calendar_year", columns="source_name",
                                values="supply_toe", aggfunc="sum",
                                fill_value=np.nan).reset_index()
        # Clean column names
        rename_map = {
            "Gas": "pes_gas_toe",
            "Oil": "pes_oil_toe",
            "Coal": "pes_coal_toe",
            "Hydro Electricity": "pes_hydro_toe",
            "Nuclear Electricity": "pes_nuclear_toe",
            "Renewable Electricity": "pes_renewables_toe",
            "LNG Imports": "pes_lng_toe",
            "Imported Electricity": "pes_imported_elec_toe",
            "LPG": "pes_lpg_toe",
        }
        p_piv.rename(columns=rename_map, inplace=True)
        primary_agg = pd.merge(tpes_tot, p_piv, on="calendar_year", how="left")
        merged = pd.merge(merged, primary_agg, on="calendar_year", how="left")
    else:
        merged["tpes_toe"] = np.nan
        merged["imports_toe"] = np.nan
        merged["domestic_toe"] = np.nan
        merged["import_share_pct"] = np.nan

    # 3. Power Generation Supply by source (GWh) & Capacity (MW)
    if not re_df.empty:
        rdf = re_df.copy()
        rdf["calendar_year"] = pd.to_numeric(rdf["calendar_year"], errors="coerce")
        rdf = rdf.dropna(subset=["calendar_year"])
        rdf["calendar_year"] = rdf["calendar_year"].astype(int)
        for col in ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh", "gen_other_renewables_gwh",
                    "gen_nuclear_gwh", "gen_coal_gwh", "gen_gas_gwh", "capacity_mw", "demand_gwh"]:
            if col in rdf.columns:
                rdf[col] = pd.to_numeric(rdf[col], errors="coerce")
            else:
                rdf[col] = float("nan")

        # Summed across the sources that report at all, with min_count so a year
        # that leaves one of them blank has no total either.  Averaging over the
        # parts that exist would let 1999 -- a year with no coal, gas or nuclear
        # row -- print a generation total it never reported.
        def _sum_strict(cols):
            cols = [c for c in cols if rdf[c].notna().any()]
            return (rdf[cols].sum(axis=1, min_count=len(cols))
                    if cols else float("nan"))

        rdf["gen_clean_gwh"] = _sum_strict(["gen_hydro_gwh", "gen_solar_gwh",
                                            "gen_wind_gwh", "gen_other_renewables_gwh",
                                            "gen_nuclear_gwh"])
        rdf["gen_variable_re_gwh"] = _sum_strict(["gen_solar_gwh", "gen_wind_gwh"])
        rdf["gen_re_total_gwh"] = _sum_strict(["gen_solar_gwh", "gen_wind_gwh",
                                               "gen_hydro_gwh", "gen_other_renewables_gwh"])
        rdf["gen_thermal_gwh"] = _sum_strict(["gen_coal_gwh", "gen_gas_gwh"])
        rdf["gen_total_gwh"] = _sum_strict(["gen_hydro_gwh", "gen_solar_gwh",
                                             "gen_wind_gwh", "gen_other_renewables_gwh",
                                             "gen_nuclear_gwh", "gen_coal_gwh", "gen_gas_gwh"])

        _den = rdf["gen_total_gwh"].replace(0, np.nan)
        rdf["clean_share_pct"] = rdf["gen_clean_gwh"] / _den * 100.0
        rdf["re_share_pct"] = rdf["gen_re_total_gwh"] / _den * 100.0
        rdf["variable_re_share_pct"] = rdf["gen_variable_re_gwh"] / _den * 100.0

        # Merge with main table
        gen_cols = ["calendar_year", "capacity_mw", "demand_gwh",
                    "gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh", "gen_other_renewables_gwh",
                    "gen_nuclear_gwh", "gen_coal_gwh", "gen_gas_gwh",
                    "gen_clean_gwh", "gen_variable_re_gwh", "gen_re_total_gwh",
                    "gen_thermal_gwh", "gen_total_gwh",
                    "clean_share_pct", "re_share_pct", "variable_re_share_pct"]
        merged = pd.merge(merged, rdf[gen_cols], on="calendar_year", how="left")

    # 4. Optional total grid capacity from fact_elec_generation
    if gen_df is not None and not gen_df.empty:
        gdf = gen_df.copy()
        gdf["calendar_year"] = pd.to_numeric(gdf["calendar_year"], errors="coerce")
        gdf = gdf.dropna(subset=["calendar_year"])
        gdf["calendar_year"] = gdf["calendar_year"].astype(int)
        gdf["installed_capacity_mw"] = pd.to_numeric(gdf["installed_capacity_mw"], errors="coerce")
        merged = pd.merge(merged, gdf[["calendar_year", "installed_capacity_mw"]],
                          on="calendar_year", how="left")
        # Fall back to re_df capacity if installed_capacity_mw missing
        merged["grid_capacity_mw"] = merged["installed_capacity_mw"].combine_first(merged.get("capacity_mw", pd.Series(np.nan)))
    else:
        merged["grid_capacity_mw"] = merged.get("capacity_mw", pd.Series(np.nan))

    return merged.sort_values("calendar_year").reset_index(drop=True)


# ═════════════════════════════ forecasting models ═══════════════════════════

def fit_supply_model(
    hist: pd.DataFrame,
    series_col: str,
    calib_start: int = DEFAULT_CALIB_START,
    calib_end: int = HISTORY_END,
) -> dict:
    """
    Fits both Driver (GDP-elasticity) and Trend (log-linear) models on the calibration window.
    ln(y) = alpha + beta * ln(real_gdp)
    ln(y) = a + b * (year - calib_start)
    """
    sample = hist[(hist["calendar_year"] >= calib_start) & (hist["calendar_year"] <= calib_end)].copy()
    sample = sample.dropna(subset=[series_col, "real_gdp_idx"])
    sample = sample[sample[series_col] > 0]

    n = len(sample)
    if n < 3:
        return {
            "series": series_col, "calib_start": calib_start, "calib_end": calib_end,
            "elasticity": 1.0, "r2_driver": 0.0, "trend_growth_pct": 3.0, "r2_trend": 0.0,
            "n": n, "cagr_historical": 3.0,
        }

    ln_y = np.log(sample[series_col].values)
    ln_gdp = np.log(sample["real_gdp_idx"].values)
    t = (sample["calendar_year"].values - calib_start).astype(float)

    # 1. Driver model: ln(y) ~ ln(gdp)
    fit_driver = _lstsq([ln_gdp], ln_y)
    elasticity = float(np.clip(fit_driver["coef"][1], 0.1, 2.5))
    r2_driver = float(fit_driver["r2"])

    # 2. Trend model: ln(y) ~ t
    fit_trend = _lstsq([t], ln_y)
    trend_growth_pct = float(np.clip(fit_trend["coef"][1] * 100.0, -2.0, 12.0))
    r2_trend = float(fit_trend["r2"])

    # Historical CAGR
    cagr_hist = _cagr(sample[series_col].iloc[0], sample[series_col].iloc[-1], n - 1)

    return {
        "series": series_col,
        "calib_start": calib_start,
        "calib_end": calib_end,
        "elasticity": elasticity,
        "r2_driver": r2_driver,
        "trend_growth_pct": trend_growth_pct,
        "r2_trend": r2_trend,
        "cagr_historical": cagr_hist,
        "n": n,
        "last_value": float(sample[series_col].iloc[-1]),
        "last_year": int(sample["calendar_year"].iloc[-1]),
    }


def scenario_supply_growth(
    model: dict,
    scenarios: Sequence[str] = tuple(SCENARIO_ORDER),
    base_gdp_growth: float = DEFAULT_BASE_GDP_GROWTH,
    spread: float = DEFAULT_SCENARIO_SPREAD,
    model_choice: str = "Driver",
) -> Dict[str, dict]:
    """
    Computes annual percentage supply growth rates for Low, Base, High scenarios.
    """
    grows = {}
    elasticity = model.get("elasticity", 1.0)
    trend_growth = model.get("trend_growth_pct", 3.5)

    gdp_assumptions = {
        "Low": base_gdp_growth - spread,
        "Base": base_gdp_growth,
        "High": base_gdp_growth + spread,
    }

    for sc in scenarios:
        gdp_g = gdp_assumptions.get(sc, base_gdp_growth)
        if model_choice == "Driver":
            # Growth driven by real GDP * elasticity
            growth_pct = float(np.clip(gdp_g * elasticity, 0.5, 12.0))
        else:
            # Trend model shifted by GDP surprise relative to baseline
            surprise = (gdp_g - base_gdp_growth) * 0.5
            growth_pct = float(np.clip(trend_growth + surprise, 0.5, 12.0))

        grows[sc] = {
            "scenario": sc,
            "gdp_growth_pct": gdp_g,
            "growth_pct": growth_pct,
            "model_choice": model_choice,
            "elasticity": elasticity,
        }
    return grows


def forecast_supply_path(
    hist: pd.DataFrame,
    series_col: str,
    grows: Dict[str, dict],
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """
    Produces annual forecast paths from last actual year (2024) to horizon (2035)
    for each scenario.
    """
    valid_hist = hist.dropna(subset=[series_col])
    if valid_hist.empty:
        return pd.DataFrame()

    last_row = valid_hist.iloc[-1]
    last_year = int(last_row["calendar_year"])
    last_val = float(last_row[series_col])

    future_years = list(range(last_year + 1, horizon + 1))
    rows = []

    for sc, g_info in grows.items():
        g_rate = g_info["growth_pct"] / 100.0
        cur_val = last_val
        for yr in future_years:
            cur_val = cur_val * (1.0 + g_rate)
            rows.append({
                "series": series_col,
                "scenario": sc,
                "calendar_year": yr,
                "value": cur_val,
                "provenance": PROJECTED,
                "growth_pct": g_info["growth_pct"],
                "anchor_year": last_year,
                "anchor_value": last_val,
            })

    return pd.DataFrame(rows)


# ═════════════════════════════ fuel & technology mix ════════════════════════

def project_technology_mix(
    hist: pd.DataFrame,
    gen_forecast: pd.DataFrame,
    clean_target_pct: float = CLEAN_POLICY_TARGET_DEFAULT,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """
    Projects the electricity generation supply breakdown across technologies:
    Hydro, Solar, Wind, Other RE, Nuclear, Coal, Gas.
    Alings with Pakistan's IGCEP expansion trajectory and national Clean Energy targets:
    - Hydro expands steadily with Dasu, Mohmand, Diamer-Bhasha additions
    - Solar & Wind accelerate towards 30% ARE target
    - Nuclear provides reliable clean baseload
    - Thermal (Coal & Gas) provides dispatchable balancing
    """
    # Baseline generation.  Each technology starts from its own last reported
    # year, never from a hand-written stand-in: the record stops filling some
    # columns before others (and never fills gen_other_renewables_gwh at all),
    # so an invented base would be the model talking, not the data.
    tech_cols = {
        "hyd": "gen_hydro_gwh", "sol": "gen_solar_gwh", "wnd": "gen_wind_gwh",
        "oth": "gen_other_renewables_gwh", "nuc": "gen_nuclear_gwh",
        "col": "gen_coal_gwh", "gas": "gen_gas_gwh",
    }
    base = {}
    for k, col in tech_cols.items():
        series = (pd.to_numeric(hist[col], errors="coerce").dropna()
                  if col in hist.columns else pd.Series(dtype=float))
        series = series[series > 0]
        base[k] = float(series.iloc[-1]) if not series.empty else 0.0
    hyd_2024, sol_2024, wnd_2024, oth_2024 = (base["hyd"], base["sol"],
                                              base["wnd"], base["oth"])
    nuc_2024, col_2024, gas_2024 = base["nuc"], base["col"], base["gas"]
    tot_2024 = hyd_2024 + sol_2024 + wnd_2024 + nuc_2024 + col_2024 + gas_2024

    rows = []
    # Add historical rows (from 2012 or PRIMARY_START)
    for _, r in hist[hist["calendar_year"] >= DEFAULT_CALIB_START].iterrows():
        yr = int(r["calendar_year"])
        # _clean keeps a blank reading blank; _num would have turned it into a
        # reported zero of generation.
        hyd = _clean(r.get("gen_hydro_gwh"))
        sol = _clean(r.get("gen_solar_gwh"))
        wnd = _clean(r.get("gen_wind_gwh"))
        oth = _clean(r.get("gen_other_renewables_gwh"))
        nuc = _clean(r.get("gen_nuclear_gwh"))
        col = _clean(r.get("gen_coal_gwh"))
        gas = _clean(r.get("gen_gas_gwh"))
        # summed over the sources that actually reported (Other RE never does)
        parts = [v for v in (hyd, sol, wnd, oth, nuc, col, gas)
                 if not pd.isna(v)]
        tot = float(np.sum(parts)) if parts else float("nan")
        clean_parts = [v for v in (hyd, sol, wnd, oth, nuc) if not pd.isna(v)]
        clean = float(np.sum(clean_parts)) if clean_parts else float("nan")
        re_var = sum(v for v in (sol, wnd) if not pd.isna(v))
        rows.append({
            "scenario": "Actual",
            "calendar_year": yr,
            "provenance": ACTUAL,
            "Hydro": hyd, "Solar": sol, "Wind": wnd, "Other RE": oth,
            "Nuclear": nuc, "Coal": col, "Gas": gas,
            "total_gen_gwh": tot,
            "clean_gen_gwh": clean,
            "clean_share_pct": (clean / tot * 100.0) if tot and tot > 0 else float("nan"),
            "variable_re_share_pct": (re_var / tot * 100.0) if tot and tot > 0 else float("nan"),
        })

    # Future projection per scenario
    scenarios = gen_forecast["scenario"].unique() if not gen_forecast.empty else SCENARIO_ORDER
    years_future = range(FORECAST_START, horizon + 1)
    n_years = horizon - HISTORY_END

    # Expansion rates by technology depending on scenario
    # High: rapid RE + Nuclear expansion
    # Base: IGCEP reference expansion
    # Low: slower hydro/solar capex
    tech_profiles = {
        "High": {"hydro_g": 0.052, "solar_g": 0.14, "wind_g": 0.12, "nuc_g": 0.05, "target_clean": clean_target_pct + 4.0},
        "Base": {"hydro_g": 0.038, "solar_g": 0.10, "wind_g": 0.08, "nuc_g": 0.04, "target_clean": clean_target_pct},
        "Low":  {"hydro_g": 0.022, "solar_g": 0.06, "wind_g": 0.05, "nuc_g": 0.025, "target_clean": clean_target_pct - 6.0},
    }

    for sc in scenarios:
        prof = tech_profiles.get(sc, tech_profiles["Base"])
        cur_hyd = hyd_2024
        cur_sol = sol_2024
        cur_wnd = wnd_2024
        cur_oth = oth_2024
        cur_nuc = nuc_2024

        sc_path = gen_forecast[(gen_forecast["scenario"] == sc) & (gen_forecast["series"] == "gen_total_gwh")]
        tot_lookup = dict(zip(sc_path["calendar_year"], sc_path["value"])) if not sc_path.empty else {}

        for yr in years_future:
            # Compound clean sources
            cur_hyd *= (1.0 + prof["hydro_g"])
            cur_sol *= (1.0 + prof["solar_g"])
            cur_wnd *= (1.0 + prof["wind_g"])
            cur_oth *= 1.02
            cur_nuc *= (1.0 + prof["nuc_g"])

            clean_sum = cur_hyd + cur_sol + cur_wnd + cur_oth + cur_nuc
            # Total generation for this year
            tot_req = tot_lookup.get(yr, clean_sum * 1.5)

            # Thermal remainder (Coal & Gas)
            thermal_rem = max(0.0, tot_req - clean_sum)
            # Gas vs Coal split: Coal prioritized for Thar indigenous baseload, Gas for peaking
            col_share = 0.45 if sc == "High" else (0.50 if sc == "Base" else 0.55)
            cur_col = thermal_rem * col_share
            cur_gas = thermal_rem * (1.0 - col_share)

            tot_actual = clean_sum + cur_col + cur_gas
            clean_share = (clean_sum / tot_actual * 100.0) if tot_actual > 0 else 0.0
            var_re_share = ((cur_sol + cur_wnd) / tot_actual * 100.0) if tot_actual > 0 else 0.0

            rows.append({
                "scenario": sc,
                "calendar_year": yr,
                "provenance": PROJECTED,
                "Hydro": cur_hyd, "Solar": cur_sol, "Wind": cur_wnd, "Other RE": cur_oth,
                "Nuclear": cur_nuc, "Coal": cur_col, "Gas": cur_gas,
                "total_gen_gwh": tot_actual,
                "clean_gen_gwh": clean_sum,
                "clean_share_pct": clean_share,
                "variable_re_share_pct": var_re_share,
            })

    return pd.DataFrame(rows)


# ═════════════════════════════ capacity expansion ══════════════════════════

def project_capacity_expansion(
    hist: pd.DataFrame,
    tech_mix_df: pd.DataFrame,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """
    Calculates installed generation capacity (MW) required to deliver generation,
    using technology capacity factors (CF):
    - Hydro: 46% CF
    - Solar: 21% CF
    - Wind: 32% CF
    - Nuclear: 82% CF
    - Coal: 58% CF
    - Gas: 48% CF
    Capacity (MW) = Generation (GWh) * 1000 / (8760 * CF)
    """
    CF = {
        "Hydro": 0.46,
        "Solar": 0.21,
        "Wind": 0.32,
        "Other RE": 0.40,
        "Nuclear": 0.82,
        "Coal": 0.58,
        "Gas": 0.48,
    }
    HOURS = 8760.0

    df = tech_mix_df.copy()
    for tech, cf in CF.items():
        if tech in df.columns:
            df[f"cap_{tech.lower().replace(' ', '_')}_mw"] = (df[tech] * 1000.0) / (HOURS * cf)

    cap_cols = [c for c in df.columns if c.startswith("cap_") and c.endswith("_mw")]
    df["total_capacity_mw"] = df[cap_cols].sum(axis=1)

    return df


# ═════════════════════════════ supply adequacy ══════════════════════════════

def compute_supply_adequacy(
    hist: pd.DataFrame,
    tech_mix_df: pd.DataFrame,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """
    Compares Generation Supply (GWh) against Grid Demand (GWh) to assess:
    - Supply-Demand balance (Net Margin GWh)
    - Reserve Margin % = (Supply GWh - Demand GWh) / Demand GWh * 100
    - Adequacy Status:
        < 10%: 'Deficit Risk / Load Shedding Vulnerability'
        10% - 25%: 'Optimal / Healthy Reserve Corridor'
        > 25%: 'Overcapacity / Capacity Payment Burden'
    """
    # Reported demand path from history.  A year with no demand reading stays
    # blank -- substituting that year's generation would label one quantity's
    # number as another quantity's name.
    _dem = pd.to_numeric(hist["demand_gwh"], errors="coerce")
    h_dem = {int(y): v for y, v in zip(hist["calendar_year"], _dem)
             if not pd.isna(v)}

    # Demand projected at Base GDP elasticity (~4.8%/yr) for benchmark
    # comparison, compounded from the last year demand was actually reported.
    _dem_years = [y for y in h_dem if y <= HISTORY_END]
    dem_anchor_year = max(_dem_years) if _dem_years else 0
    last_dem = h_dem.get(dem_anchor_year, float("nan"))
    dem_growth = 0.048

    rows = []
    for _, r in tech_mix_df.iterrows():
        yr = int(r["calendar_year"])
        sc = r["scenario"]
        prov = r["provenance"]
        supply_gwh = r["total_gen_gwh"]

        if yr <= HISTORY_END:
            demand_gwh = h_dem.get(yr, float("nan"))
        elif not h_dem:
            demand_gwh = float("nan")
        else:
            demand_gwh = last_dem * ((1.0 + dem_growth) ** (yr - dem_anchor_year))

        has_demand = isinstance(demand_gwh, (int, float)) and not pd.isna(demand_gwh)
        gap_gwh = (supply_gwh - demand_gwh) if has_demand else float("nan")
        margin_pct = (gap_gwh / demand_gwh * 100.0) if has_demand and demand_gwh > 0 \
            else float("nan")

        if not has_demand:
            status = "No demand reading"
            status_color = "#64748B"
        elif margin_pct < 10.0:
            status = "Deficit Risk"
            status_color = "#EF4444"
        elif margin_pct <= 25.0:
            status = "Optimal Reserve"
            status_color = "#10B981"
        else:
            status = "Capacity Trap Burden"
            status_color = "#F59E0B"

        rows.append({
            "scenario": sc,
            "calendar_year": yr,
            "provenance": prov,
            "supply_gwh": supply_gwh,
            "demand_gwh": demand_gwh,
            "reserve_margin_gwh": gap_gwh,
            "reserve_margin_pct": margin_pct,
            "adequacy_status": status,
            "status_color": status_color,
        })

    return pd.DataFrame(rows)


# ═════════════════════════════ energy security ══════════════════════════════

def project_indigenous_vs_imports(
    hist: pd.DataFrame,
    tpes_forecast: pd.DataFrame,
    horizon: int = HORIZON,
) -> pd.DataFrame:
    """
    Projects Indigenous Energy Production vs Imported Energy (TOE) to 2035.
    Evaluates whether Pakistan's energy transition successfully curtails foreign exchange
    vulnerability and reduces import dependence.
    """
    rows = []

    # Historical
    for _, r in hist[hist["calendar_year"] >= PRIMARY_START].iterrows():
        yr = int(r["calendar_year"])
        tpes = _clean(r.get("tpes_toe"))
        imp = _clean(r.get("imports_toe"))
        known = pd.notna(tpes) and pd.notna(imp)
        dom = (tpes - imp) if known else float("nan")
        imp_share = (imp / tpes * 100.0) if known and tpes > 0 else float("nan")
        rows.append({
            "scenario": "Actual",
            "calendar_year": yr,
            "provenance": ACTUAL,
            "tpes_toe": tpes,
            "imports_toe": imp,
            "domestic_toe": dom,
            "import_share_pct": imp_share,
        })

    # Projections per scenario
    scenarios = tpes_forecast["scenario"].unique() if not tpes_forecast.empty else SCENARIO_ORDER

    # Baseline for the paths: the last year the record actually reported the
    # number, not "2024" by assumption.  Imports stop being filled after 2018,
    # so the import trajectory starts from the 2018 share and the page says so.
    def _last_report(col: str, positive_only: bool = False) -> tuple:
        if col not in hist.columns:
            return float("nan"), 0
        s = hist[["calendar_year", col]].copy()
        s[col] = pd.to_numeric(s[col], errors="coerce")
        s = s.dropna()
        if positive_only:
            s = s[s[col] > 0]
        if s.empty:
            return float("nan"), 0
        return float(s[col].iloc[-1]), int(s["calendar_year"].iloc[-1])

    tpes_base, tpes_base_year = _last_report("tpes_toe")
    imp_share_base, imp_share_year = _last_report("import_share_pct",
                                                  positive_only=True)

    # Trajectories under scenarios:
    # High green transition: import share drops to 16% by 2035 (indigenous hydro, solar, Thar coal)
    # Base reference: import share moderates to 22%
    # Low reform: import share remains elevated around 31%
    target_shares = {"High": 16.0, "Base": 22.0, "Low": 31.0}
    span = max(horizon - tpes_base_year, 1)

    for sc in scenarios:
        sc_path = tpes_forecast[(tpes_forecast["scenario"] == sc) & (tpes_forecast["series"] == "tpes_toe")]
        tpes_lookup = dict(zip(sc_path["calendar_year"], sc_path["value"])) if not sc_path.empty else {}
        t_target = target_shares.get(sc, 22.0)

        for yr in range(FORECAST_START, horizon + 1):
            tpes_val = (tpes_lookup.get(yr) if yr in tpes_lookup
                        else tpes_base * ((1.0 + 0.03) ** (yr - tpes_base_year)))
            progress = (yr - tpes_base_year) / span
            cur_imp_share = (imp_share_base + (t_target - imp_share_base) * progress
                             if pd.notna(imp_share_base) else float("nan"))
            imp_val = tpes_val * (cur_imp_share / 100.0)
            dom_val = max(0.0, tpes_val - imp_val)

            rows.append({
                "scenario": sc,
                "calendar_year": yr,
                "provenance": PROJECTED,
                "tpes_toe": tpes_val,
                "imports_toe": imp_val,
                "domestic_toe": dom_val,
                "import_share_pct": cur_imp_share,
            })

    return pd.DataFrame(rows)


# ═════════════════════════════ backtesting ══════════════════════════════════

def backtest_supply_models(
    hist: pd.DataFrame,
    calib_start: int = DEFAULT_CALIB_START,
    train_end: int = BACKTEST_TRAIN_END,
    test_end: int = HISTORY_END,
) -> dict:
    """
    Splits data at train_end (2020). Fits Driver & Trend models on <= train_end,
    generates 2021-2024 predictions, and computes hold-out validation metrics.
    """
    train_df = hist[(hist["calendar_year"] >= calib_start) & (hist["calendar_year"] <= train_end)]
    test_df = hist[(hist["calendar_year"] > train_end) & (hist["calendar_year"] <= test_end)]

    series_to_test = [
        ("tpes_toe", "Primary Energy Supply"),
        ("gen_total_gwh", "Electricity Generation"),
        ("gen_clean_gwh", "Clean Generation"),
    ]

    results = []
    pred_paths = []

    for col, name in series_to_test:
        if col not in hist.columns or train_df[col].dropna().count() < 3:
            continue

        actuals = test_df[col].values
        test_years = test_df["calendar_year"].values

        # 1. Driver model fit
        m_driver = fit_supply_model(hist, col, calib_start=calib_start, calib_end=train_end)
        g_driver = scenario_supply_growth(m_driver, scenarios=["Base"], model_choice="Driver")["Base"]["growth_pct"] / 100.0
        val_anchor = train_df[col].iloc[-1]
        p_driver = [val_anchor * ((1.0 + g_driver) ** (yr - train_end)) for yr in test_years]

        # 2. Trend model fit
        m_trend = fit_supply_model(hist, col, calib_start=calib_start, calib_end=train_end)
        g_trend = m_trend["trend_growth_pct"] / 100.0
        p_trend = [val_anchor * ((1.0 + g_trend) ** (yr - train_end)) for yr in test_years]

        # Metrics
        met_d = _metrics(actuals, p_driver)
        met_t = _metrics(actuals, p_trend)

        better_m = "Driver" if met_d["mape_pct"] <= met_t["mape_pct"] else "Trend"

        results.append({
            "series_name": name,
            "col": col,
            "model": "Driver",
            "mape_pct": met_d["mape_pct"],
            "rmse": met_d["rmse"],
            "bias_pct": met_d["bias_pct"],
            "calib_r2": m_driver["r2_driver"],
            "is_winner": (better_m == "Driver"),
        })
        results.append({
            "series_name": name,
            "col": col,
            "model": "Trend",
            "mape_pct": met_t["mape_pct"],
            "rmse": met_t["rmse"],
            "bias_pct": met_t["bias_pct"],
            "calib_r2": m_trend["r2_trend"],
            "is_winner": (better_m == "Trend"),
        })

        for yr, act, pd_d, pd_t in zip(test_years, actuals, p_driver, p_trend):
            pred_paths.append({
                "series_name": name,
                "col": col,
                "calendar_year": int(yr),
                "actual": act,
                "predicted_driver": pd_d,
                "predicted_trend": pd_t,
            })

    table_df = pd.DataFrame(results)
    path_df = pd.DataFrame(pred_paths)
    return {
        "train_end": train_end,
        "test_end": test_end,
        "table": table_df,
        "paths": path_df,
    }


# ═════════════════════════════ master data builder ══════════════════════════

def build_supply_dashboard_data(
    primary_df: pd.DataFrame,
    re_df: pd.DataFrame,
    econ_df: pd.DataFrame,
    gen_df: Optional[pd.DataFrame] = None,
    scenarios: Sequence[str] = tuple(SCENARIO_ORDER),
    calib_start: int = DEFAULT_CALIB_START,
    horizon: int = HORIZON,
    base_gdp_growth: float = DEFAULT_BASE_GDP_GROWTH,
    spread: float = DEFAULT_SCENARIO_SPREAD,
    clean_target_pct: float = CLEAN_POLICY_TARGET_DEFAULT,
    model_choice: str = "Driver",
) -> dict:
    """
    Single fetch-free call returning everything required for the Q5 Supply Dashboard.
    """
    hist = build_history(primary_df, re_df, econ_df, gen_df)

    # 1. Fit models for key supply aggregates
    models = {
        "tpes_toe": fit_supply_model(hist, "tpes_toe", calib_start, HISTORY_END),
        "gen_total_gwh": fit_supply_model(hist, "gen_total_gwh", calib_start, HISTORY_END),
        "gen_clean_gwh": fit_supply_model(hist, "gen_clean_gwh", calib_start, HISTORY_END),
    }

    # 2. Scenario annual growth rates
    grows = {
        key: scenario_supply_growth(models[key], scenarios, base_gdp_growth, spread, model_choice)
        for key in models
    }

    # 3. Forecast paths
    fc_parts = []
    for key in ("tpes_toe", "gen_total_gwh"):
        part = forecast_supply_path(hist, key, grows[key], horizon)
        if not part.empty:
            fc_parts.append(part)
    forecast = pd.concat(fc_parts, ignore_index=True) if fc_parts else pd.DataFrame()

    # 4. Detailed technology generation mix & clean share tracking
    tech_mix = project_technology_mix(hist, forecast, clean_target_pct, horizon)

    # 5. Capacity expansion (MW)
    capacity = project_capacity_expansion(hist, tech_mix, horizon)

    # 6. Supply adequacy & reserve margin
    adequacy = compute_supply_adequacy(hist, tech_mix, horizon)

    # 7. Indigenous vs imported energy supply
    security = project_indigenous_vs_imports(hist, forecast, horizon)

    # 8. Holdout model backtesting
    backtest = backtest_supply_models(hist, calib_start=calib_start,
                                      train_end=BACKTEST_TRAIN_END, test_end=HISTORY_END)

    return {
        "history": hist,
        "models": models,
        "grows": grows,
        "forecast": forecast,
        "tech_mix": tech_mix,
        "capacity": capacity,
        "adequacy": adequacy,
        "security": security,
        "backtest": backtest,
        "calib_start": calib_start,
        "horizon": horizon,
        "base_gdp_growth": base_gdp_growth,
        "spread": spread,
        "clean_target_pct": clean_target_pct,
        "model_choice": model_choice,
        "scenarios": list(scenarios),
        "history_end": HISTORY_END,
    }
