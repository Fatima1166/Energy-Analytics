"""
core/demand_forecast.py -- question 4: "What is forecasted energy demand?"

The analysis engine behind the Forecasted Energy Demand dashboard (1999-2035).
It is pure: every function takes DataFrames straight from :mod:`core.queries`
and returns DataFrames / dicts.  Nothing here talks to Streamlit or MySQL, so
the whole pipeline is testable from a script (see
``scripts/verify_demand_forecast.py``).

What it produces
----------------
``build_history``       tidy demand history (total final energy, electricity,
                        gas, grid demand) with the drivers -- real GDP, real GDP
                        per head, GDP growth, population -- on one year axis.
``detect_break``        the reporting-basis break in the final-energy series
                        (a coverage change in 2019, see README).
``fit_trend_model``     log-linear trend with a level dummy for that break.
``fit_driver_model``    income elasticity in per-capita space plus population,
                        with the break dummy, and the post-break residual drift
                        (the part of demand GDP and population do not explain).
``scenario_growth``     Low / Base / High annual growth paths, with the residual
                        drift decaying to zero by the horizon.
``forecast_series``     demand paths from the last reported year to the horizon.
``backtest``            in-sample fit and a hold-out forecast -> MAPE, RMSE, R2.
``decompose_growth``    each year's demand growth split into an income-per-head
                        part, a population part and an intensity residual.
``project_composition`` sector / province demand to 2035 from trended shares.
``build_supply_gap``    primary supply vs demand, and gas / electricity import
                        dependency, to 2035.

Methodological choices, all documented in the dashboard footer and README:

* Elasticities are estimated on **real** GDP chained from ``gdp_growth_pct``,
  not on current-USD GDP, which is distorted by the rupee's depreciation.
* The 2019 level shift in ``fact_final_energy_consumption`` is a coverage
  change, so it is modelled with a level dummy instead of being allowed to
  masquerade as demand growth.
* The post-break residual drift fades linearly to zero by the horizon, so a
  one-off contraction is not compounded for eleven years.
* Projected sector / province shares drift at most 5% per year, which keeps
  small categories from exploding.

Units: everything stays in the storage base unit of its domain (TOE, GWh, BCF,
USD, persons).  The sidebar unit selection is applied at render time by
:mod:`core.units`.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

# ══════════════════════════════ constants ═══════════════════════════════════

ACTUAL = "Actual"
ESTIMATED = "Estimated"
PROJECTED = "Projected"

PROVENANCE_COLORS = {
    ACTUAL: "#00A6FB",
    ESTIMATED: "#F59E0B",
    PROJECTED: "#A78BFA",
}

HISTORY_START = 1999          # first year in dim_year
ELECTRICITY_START = 2000      # first year with grid demand reported
FINAL_ENERGY_START = 2002     # first year with final-energy-by-source rows
HISTORY_END = 2024            # last reported year
FORECAST_START = 2025
HORIZON = 2035

DEFAULT_CALIB_START = 2012    # calibration window default (start)
DEFAULT_TEST_YEARS = 4        # hold-out = the last 4 reported years
BACKTEST_TRAIN_END = HISTORY_END - DEFAULT_TEST_YEARS   # 2020

SCENARIO_ORDER = ["Low", "Base", "High"]
SCENARIO_COLORS = {"Low": "#F59E0B", "Base": "#00A6FB", "High": "#10B981"}
SCENARIO_BADGES = {
    "Low": "slow reform",
    "Base": "trend",
    "High": "industrial push",
}

# Guard rails.  A short annual sample can produce explosive coefficients; the
# raw fits are still reported, but projection uses the clamped values.
# The lower bound is negative on purpose: in the reported data gas demand moves
# *against* income (rationing and substitution), and clamping that to zero would
# make every gas scenario identical.
ELASTICITY_CLAMP = (-0.6, 2.5)
GROWTH_CLAMP = (-8.0, 14.0)    # annual demand growth (%) stays inside -8%..+14%
SHARE_TREND_CLAMP = 0.03       # a projected share moves at most 3% per year
MIN_SHARE = 1e-6               # floor used only to keep logarithms finite
BREAK_THRESHOLD = 0.20         # |d ln y| that counts as a basis change
BREAK_RATIO = 2.5              # ... and how far it must stand out
DEFAULT_SCENARIO_SPREAD = 1.5  # ± percentage points of GDP growth
DEFAULT_BASE_GDP_GROWTH = 4.0  # % p.a. fallback when the DB has no GDP series
POPULATION_FALLBACK = 2.0      # % p.a. fallback population growth

# ═══════════════════════════ series definitions ═════════════════════════════

SERIES_SPEC: List[dict] = [
    {
        "key": "total_final",
        "label": "Total Final Energy Demand",
        "short": "Total final energy",
        "domain": "energy",
        "column": "total_final_toe",
        "start": FINAL_ENERGY_START,
        "color": "#00A6FB",
        "icon": "primary_energy",
    },
    {
        "key": "electricity_final",
        "label": "Electricity Demand (final energy)",
        "short": "Electricity",
        "domain": "energy",
        "column": "electricity_toe",
        "start": FINAL_ENERGY_START,
        "color": "#10B981",
        "icon": "generation",
    },
    {
        "key": "gas_final",
        "label": "Gas Demand (final energy)",
        "short": "Gas",
        "domain": "energy",
        "column": "gas_toe",
        "start": FINAL_ENERGY_START,
        "color": "#F59E0B",
        "icon": "gas",
    },
    {
        "key": "elec_grid",
        "label": "Grid Electricity Demand",
        "short": "Grid demand",
        "domain": "electricity",
        "column": "elec_grid_gwh",
        "start": ELECTRICITY_START,
        "color": "#A78BFA",
        "icon": "generation",
    },
]

SERIES_BY_KEY: Dict[str, dict] = {s["key"]: s for s in SERIES_SPEC}
HISTORY_SERIES_KEYS = ["total_final", "electricity_final", "gas_final", "elec_grid"]


def series_spec(key: str) -> dict:
    """Spec for one series key."""
    return SERIES_BY_KEY[key]


# ═════════════════════════════ small maths ══════════════════════════════════

def _num(value, default: float = 0.0) -> float:
    """None / NaN safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if not math.isfinite(out) else out


def _clean(value) -> float:
    """Like ``_num`` but yields NaN instead of a default -- for regressions."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp, passing NaN through untouched."""
    if value is None or not math.isfinite(_clean(value)):
        return float("nan")
    return float(min(max(float(value), lo), hi))


def _cagr(first: float, last: float, periods: int) -> float:
    """Compound annual growth rate, in percent."""
    if periods <= 0 or not math.isfinite(_clean(first)) or not math.isfinite(_clean(last)):
        return float("nan")
    if first <= 0 or last <= 0:
        return float("nan")
    return ((last / first) ** (1.0 / periods) - 1.0) * 100.0


def _lstsq(columns: Sequence[Sequence[float]], y: Sequence[float]) -> dict:
    """
    Least squares for ``y = b0 + b1*x1 + ...``.

    Columns whose values are constant inside the sample (e.g. an all-zero break
    dummy) are dropped, so a dummy that never switches on cannot destabilise the
    fit.  Returns the coefficients, R2 and the number of usable rows.
    """
    arrays = [np.asarray([_clean(v) for v in col], dtype=float) for col in columns]
    ys = np.asarray([_clean(v) for v in y], dtype=float)
    if not arrays:
        return {"coef": [], "r2": float("nan"), "n": 0, "used": []}

    mask = np.isfinite(ys)
    for arr in arrays:
        mask &= np.isfinite(arr)
    arrays = [arr[mask] for arr in arrays]
    ys = ys[mask]
    n = int(ys.size)
    if n < 3:
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"),
                "n": n, "used": []}

    used, design_cols = [], []
    for i, arr in enumerate(arrays):
        if float(np.ptp(arr)) == 0.0:
            continue                       # constant column carries no signal
        used.append(i)
        design_cols.append(arr)

    design = np.column_stack([np.ones(n)] + design_cols)
    if design.shape[1] > n:
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"),
                "n": n, "used": used}
    try:
        coef, *_ = np.linalg.lstsq(design, ys, rcond=None)
    except np.linalg.LinAlgError:          # pragma: no cover - degenerate input
        return {"coef": [float("nan")] * (len(arrays) + 1), "r2": float("nan"),
                "n": n, "used": used}

    fitted = design @ coef
    ss_res = float(((ys - fitted) ** 2).sum())
    ss_tot = float(((ys - ys.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    full = [float(coef[0])]
    index = 1
    for i in range(len(arrays)):
        if i in used:
            full.append(float(coef[index]))
            index += 1
        else:
            full.append(0.0)
    return {"coef": full, "r2": float(r2), "n": n, "used": used}


def _metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict:
    """MAPE %, RMSE, R2 (levels) and bias % for one window."""
    a = np.asarray([_clean(v) for v in actual], dtype=float)
    p = np.asarray([_clean(v) for v in predicted], dtype=float)
    mask = np.isfinite(a) & np.isfinite(p) & (a != 0)
    a, p = a[mask], p[mask]
    n = int(a.size)
    if n == 0:
        return {"mape": float("nan"), "rmse": float("nan"), "r2": float("nan"),
                "bias": float("nan"), "n": 0}
    mape = float(np.mean(np.abs((a - p) / a)) * 100.0)
    rmse = float(np.sqrt(np.mean((a - p) ** 2)))
    ss_res = float(((a - p) ** 2).sum())
    ss_tot = float(((a - a.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    bias = float(np.mean((p - a) / a) * 100.0)
    return {"mape": mape, "rmse": rmse, "r2": float(r2), "bias": bias, "n": n}


# ═════════════════════════ 1. history + drivers ═════════════════════════════

def build_history(fuel_df: pd.DataFrame,
                  re_df: pd.DataFrame,
                  econ_df: pd.DataFrame) -> pd.DataFrame:
    """
    One calendar-year row per year, demand and drivers side by side.

    Columns
    -------
    total_final_toe, electricity_toe, gas_toe, oil_toe, coal_toe, lpg_toe : TOE
    elec_grid_gwh                                                        : GWh
    gdp_usd, gdp_per_capita                                              : current USD
    gdp_growth_pct, gdp_real_index, real_gdp_per_capita                  : %, index, index/head
    population                                                           : persons
    """
    out = pd.DataFrame()

    # ── final energy demand by source (TOE) ────────────────────────────────
    if fuel_df is not None and not fuel_df.empty:
        f = fuel_df.copy()
        f["calendar_year"] = pd.to_numeric(f["calendar_year"], errors="coerce")
        f["consumption_toe"] = pd.to_numeric(f["consumption_toe"], errors="coerce")
        f = f.dropna(subset=["calendar_year"])
        f["calendar_year"] = f["calendar_year"].astype(int)

        total = (f.groupby("calendar_year")["consumption_toe"]
                 .sum().rename("total_final_toe"))
        pivot = f.pivot_table(index="calendar_year", columns="source_name",
                              values="consumption_toe", aggfunc="sum")
        out = total.to_frame()
        for source, column in (("Electricity (Final)", "electricity_toe"),
                               ("Gas", "gas_toe"),
                               ("Oil", "oil_toe"),
                               ("Coal", "coal_toe"),
                               ("LPG", "lpg_toe")):
            if source in pivot.columns:
                out[column] = pivot[source]
        out = out.reset_index()

    # ── grid electricity demand (GWh) ──────────────────────────────────────
    if re_df is not None and not re_df.empty and "demand_gwh" in re_df.columns:
        e = re_df[["calendar_year", "demand_gwh"]].copy()
        e["calendar_year"] = pd.to_numeric(e["calendar_year"], errors="coerce")
        e["elec_grid_gwh"] = pd.to_numeric(e["demand_gwh"], errors="coerce")
        e = e.dropna(subset=["calendar_year", "elec_grid_gwh"])
        e["calendar_year"] = e["calendar_year"].astype(int)
        e = e[["calendar_year", "elec_grid_gwh"]]
        out = e if out.empty else out.merge(e, on="calendar_year", how="outer")

    # ── economic drivers ───────────────────────────────────────────────────
    if econ_df is not None and not econ_df.empty:
        ec = econ_df.copy()
        ec["calendar_year"] = pd.to_numeric(ec["calendar_year"], errors="coerce")
        ec = ec.dropna(subset=["calendar_year"])
        ec["calendar_year"] = ec["calendar_year"].astype(int)
        for column in ("gdp_current_usd", "gdp_growth_pct", "population"):
            if column in ec.columns:
                ec[column] = pd.to_numeric(ec[column], errors="coerce")
        keep = [c for c in ("calendar_year", "gdp_current_usd", "gdp_growth_pct",
                            "population") if c in ec.columns]
        ec = ec[keep].drop_duplicates(subset=["calendar_year"], keep="last")
        out = ec if out.empty else out.merge(ec, on="calendar_year", how="outer")

    if out.empty:
        return pd.DataFrame(columns=["calendar_year", "total_final_toe",
                                     "electricity_toe", "gas_toe", "elec_grid_gwh",
                                     "gdp_usd", "gdp_growth_pct", "population",
                                     "gdp_per_capita", "gdp_real_index",
                                     "real_gdp_per_capita"])

    out = out.sort_values("calendar_year").reset_index(drop=True)
    out["calendar_year"] = out["calendar_year"].astype(int)

    if "gdp_current_usd" in out.columns:
        out = out.rename(columns={"gdp_current_usd": "gdp_usd"})
        if "population" in out.columns:
            out["gdp_per_capita"] = out["gdp_usd"] / out["population"]

    if "gdp_usd" in out.columns:
        growth = out["gdp_usd"].pct_change() * 100.0
        if "gdp_growth_pct" in out.columns:
            out["gdp_growth_pct"] = out["gdp_growth_pct"].fillna(growth)
            # fill remaining holes from the level series
            out["gdp_growth_pct"] = out["gdp_growth_pct"].fillna(growth)
        else:
            out["gdp_growth_pct"] = growth

    # ── real GDP index, chained from the growth rates ──────────────────────
    # Current-USD GDP moves with the exchange rate: it fell 9.9% in 2019 while
    # real GDP grew 2.5%, so elasticities are estimated on a real index instead:
    # index_t = index_(t-1) * (1 + g_t).
    level = 100.0
    index = []
    for i, growth in enumerate(out["gdp_growth_pct"].tolist()):
        if i > 0 and math.isfinite(_clean(growth)):
            level = level * (1.0 + float(growth) / 100.0)
        index.append(level)
    out["gdp_real_index"] = index
    if "population" in out.columns:
        out["real_gdp_per_capita"] = out["gdp_real_index"] / out["population"] * 1e6

    return out


def _column_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if frame is None or frame.empty or column not in frame.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def observed_path(hist: pd.DataFrame, key: str) -> pd.DataFrame:
    """Reported history of one series: ``calendar_year, value, provenance``."""
    spec = series_spec(key)
    if hist is None or hist.empty or spec["column"] not in hist.columns:
        return pd.DataFrame(columns=["calendar_year", "value", "provenance"])
    frame = hist[["calendar_year", spec["column"]]].copy()
    frame["value"] = pd.to_numeric(frame[spec["column"]], errors="coerce")
    frame = frame.dropna(subset=["value"]).sort_values("calendar_year")
    frame["provenance"] = ACTUAL
    return frame[["calendar_year", "value", "provenance"]].reset_index(drop=True)


def last_actual(hist: pd.DataFrame, key: str) -> tuple:
    """``(year, value)`` of the most recent reported point of one series."""
    path = observed_path(hist, key)
    if path.empty:
        return None, float("nan")
    row = path.iloc[-1]
    return int(row["calendar_year"]), float(row["value"])


def detect_break(hist: pd.DataFrame, key: str,
                 threshold: float = BREAK_THRESHOLD,
                 ratio: float = BREAK_RATIO) -> Optional[int]:
    """
    Year of a reporting-basis level shift in one series, or ``None``.

    A break is the largest year-on-year log jump that both exceeds
    ``threshold`` (20%) and stands out from the typical year by ``ratio``
    (2.5x).  For the final-energy series this finds 2019, where the coverage of
    ``fact_final_energy_consumption`` changes.
    """
    path = observed_path(hist, key)
    if len(path) < 6:
        return None
    values = path["value"].to_numpy(dtype=float)
    years = path["calendar_year"].to_numpy(dtype=int)
    if (values <= 0).any():
        return None
    deltas = np.diff(np.log(values))
    typical = float(np.median(np.abs(deltas)))
    idx = int(np.argmax(np.abs(deltas)))
    jump = abs(float(deltas[idx]))
    if jump >= threshold and jump >= ratio * max(typical, 1e-6):
        return int(years[idx + 1])
    return None


def break_flags(years: Sequence[int], break_year: Optional[int]) -> np.ndarray:
    """Dummy column: 1.0 for years at or after the break."""
    if break_year is None:
        return np.zeros(len(years), dtype=float)
    return np.asarray([1.0 if int(y) >= int(break_year) else 0.0 for y in years],
                      dtype=float)


def _window(hist: pd.DataFrame, calib_start: int, calib_end: int) -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame()
    mask = (hist["calendar_year"] >= calib_start) & (hist["calendar_year"] <= calib_end)
    return hist.loc[mask].copy()


# ══════════════════════════ 2. trend model ══════════════════════════════════

def fit_trend_model(hist: pd.DataFrame, key: str,
                    calib_start: int = DEFAULT_CALIB_START,
                    calib_end: int = HISTORY_END) -> dict:
    """
    Log-linear trend with a break dummy: ``ln(demand) = b0 + b1*year + b2*D``.

    ``D`` switches on at the detected basis change, so ``b1`` is the trend of
    the underlying series rather than a jump in coverage.  ``growth_pct`` is
    ``exp(b1) - 1``.
    """
    spec = series_spec(key)
    frame = _window(hist, calib_start, calib_end)
    break_year = detect_break(hist, key)
    years = frame["calendar_year"].to_numpy(dtype=float) if not frame.empty else np.array([])
    values = _column_series(frame, spec["column"]).to_numpy(dtype=float)

    mask = np.isfinite(values) & (values > 0)
    years, values = years[mask], values[mask]

    growth, sigma, r2, n = float("nan"), 0.0, float("nan"), int(years.size)
    if years.size >= 3:
        fit = _lstsq([years, break_flags(years, break_year)], np.log(values))
        slope = fit["coef"][1]
        if math.isfinite(_clean(slope)):
            growth = math.expm1(slope) * 100.0
            resid = np.log(values) - (fit["coef"][0]
                                      + slope * years
                                      + fit["coef"][2] * break_flags(years, break_year))
            sigma = float(np.std(resid, ddof=1)) if resid.size > 1 else 0.0
        r2, n = fit["r2"], fit["n"]

    anchor_year, anchor_value = last_actual(hist, key)
    observed = _cagr(values[0], values[-1], int(years.size) - 1) if years.size >= 2 else float("nan")

    return {
        "series": key,
        "model": "Trend",
        "growth_pct": growth,
        "observed_cagr_pct": observed,
        "sigma": sigma,
        "r2": r2,
        "n": n,
        "break_year": break_year,
        "anchor_year": anchor_year,
        "anchor_value": anchor_value,
        "calib_start": calib_start,
        "calib_end": calib_end,
    }


# ══════════════════════════ 3. driver model ═════════════════════════════════

def fit_driver_model(hist: pd.DataFrame, key: str,
                     calib_start: int = DEFAULT_CALIB_START,
                     calib_end: int = HISTORY_END) -> dict:
    """
    Demand-driver model (objective 3).

    Estimated in **per-capita** space, because a two-factor fit of
    ``ln(demand)`` on ``ln(GDP)`` *and* ``ln(population)`` is collinear over a
    short annual sample and produces unusable (even negative) elasticities:

        ``ln(demand / population) = b0 + eps * ln(real GDP per head) + b2 * D``

    ``eps`` is the income elasticity of per-capita demand; population then enters
    the projection with the coefficient ``1`` (people consume):

        ``g_demand = g_population + eps * (g_realGDP - g_population) + residual``

    The ``residual`` is the post-break drift -- the part of demand growth that
    income and population do not explain (energy intensity, efficiency, the
    2022-24 gas/LNG squeeze).  It is measured only in years *after* the break
    year, so the coverage jump cannot inflate it.

    Also reported: the single-factor ``ln(demand) ~ ln(real GDP)`` elasticity,
    the R2 of the per-capita fit, and the correlation of annual growth rates.
    """
    spec = series_spec(key)
    frame = _window(hist, calib_start, calib_end)
    break_year = detect_break(hist, key)

    value = _column_series(frame, spec["column"])
    pop = _column_series(frame, "population")
    rgdppc = _column_series(frame, "real_gdp_per_capita")
    rgdp = _column_series(frame, "gdp_real_index")

    valid = (value > 0) & (pop > 0) & (rgdppc > 0)
    frame_v = frame.loc[valid]
    value, pop, rgdppc, rgdp = (value.loc[valid], pop.loc[valid],
                                rgdppc.loc[valid], rgdp.loc[valid])
    years_v = frame_v["calendar_year"].to_numpy(dtype=float) if not frame_v.empty else np.array([])
    dummy_v = break_flags(years_v, break_year)

    # ── per-capita elasticity ──────────────────────────────────────────────
    per_capita = (value / pop) if pop.size else pd.Series(dtype=float)
    fit_pc = _lstsq([np.log(rgdppc.to_numpy(dtype=float)) if rgdppc.size else [],
                     dummy_v],
                    np.log(per_capita.to_numpy(dtype=float)) if per_capita.size else [])
    eps_raw = fit_pc["coef"][1] if len(fit_pc["coef"]) > 1 else float("nan")
    eps = _clamp(eps_raw, *ELASTICITY_CLAMP)

    # ── single-factor elasticity of demand w.r.t. real GDP ─────────────────
    fit_gdp = _lstsq([np.log(rgdp.to_numpy(dtype=float)) if rgdp.size else [], dummy_v],
                     np.log(value.to_numpy(dtype=float)) if value.size else [])
    eps_gdp_raw = fit_gdp["coef"][1] if len(fit_gdp["coef"]) > 1 else float("nan")
    eps_gdp = _clamp(eps_gdp_raw, *ELASTICITY_CLAMP)

    # ── growth rates and the post-break residual drift ─────────────────────
    growth = value.pct_change() * 100.0
    gdp_growth = rgdp.pct_change() * 100.0
    pop_growth = pop.pct_change() * 100.0

    years_all = frame_v["calendar_year"].to_numpy(dtype=int) if not frame_v.empty else np.array([])
    if break_year is not None:
        resid_mask = years_all > int(break_year)          # skip the jump year
    else:
        resid_mask = np.ones(len(years_all), dtype=bool)

    if math.isfinite(_clean(eps)) and growth.size >= 3:
        expected = pop_growth + eps * (gdp_growth - pop_growth)   # in %
        residual = (growth - expected).to_numpy(dtype=float)
        usable = residual[resid_mask] if resid_mask.size == residual.size else residual
        usable = usable[np.isfinite(usable)]
        drift = float(np.mean(usable)) if usable.size else 0.0
        drift_sigma = float(np.std(usable, ddof=1)) if usable.size > 1 else 0.0
        resid_n = int(usable.size)
    else:
        drift, drift_sigma, resid_n = 0.0, 0.0, 0

    pair = pd.DataFrame({"d": growth, "g": gdp_growth}).dropna()
    corr = float(pair["d"].corr(pair["g"])) if len(pair) >= 3 else float("nan")

    trend = fit_trend_model(hist, key, calib_start, calib_end)
    anchor_year, anchor_value = last_actual(hist, key)

    driver_ok = (math.isfinite(_clean(eps)) and fit_pc["n"] >= 4)
    model_used = "Driver" if driver_ok else "Trend"

    return {
        "series": key,
        "model": model_used,
        "elasticity_income": eps,
        "elasticity_income_raw": eps_raw,
        "elasticity_gdp": eps_gdp,
        "elasticity_gdp_raw": eps_gdp_raw,
        "population_coef": 1.0,           # people consume one-for-one
        "r2_per_capita": fit_pc["r2"],
        "r2_gdp": fit_gdp["r2"],
        "growth_corr": corr,
        "residual_pct": drift,
        "residual_sigma": drift_sigma,
        "residual_years": resid_n,
        "observed_cagr_pct": trend["observed_cagr_pct"],
        "trend_growth_pct": trend["growth_pct"],
        "n": fit_pc["n"],
        "break_year": break_year,
        "anchor_year": anchor_year,
        "anchor_value": anchor_value,
        "calib_start": calib_start,
        "calib_end": calib_end,
    }


def driver_table(hist: pd.DataFrame,
                 calib_start: int = DEFAULT_CALIB_START,
                 calib_end: int = HISTORY_END,
                 keys: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """One row per demand series with the driver diagnostics."""
    keys = list(keys or HISTORY_SERIES_KEYS)
    rows = []
    for key in keys:
        model = fit_driver_model(hist, key, calib_start, calib_end)
        rows.append({
            "series": key,
            "label": series_spec(key)["short"],
            "observations": model["n"],
            "observed_cagr_pct": model["observed_cagr_pct"],
            "elasticity_income": model["elasticity_income"],
            "elasticity_income_raw": model["elasticity_income_raw"],
            "elasticity_gdp": model["elasticity_gdp"],
            "r2_per_capita": model["r2_per_capita"],
            "r2_gdp": model["r2_gdp"],
            "growth_corr": model["growth_corr"],
            "residual_pct": model["residual_pct"],
            "break_year": model["break_year"],
            "model": model["model"],
        })
    return pd.DataFrame(rows)


def decompose_growth(hist: pd.DataFrame, key: str,
                     calib_start: int = DEFAULT_CALIB_START,
                     calib_end: int = HISTORY_END) -> pd.DataFrame:
    """
    Per-year split of demand growth (objective 3):

    ``g = eps * (g_realGDP - g_population)  +  g_population  +  residual``
       =   income per head effect          +  population    +  intensity

    Columns: ``calendar_year, income_pp, pop_pp, residual_pp, total_pct``.
    The break year is dropped -- a coverage jump is not demand growth.
    """
    model = fit_driver_model(hist, key, calib_start, calib_end)
    frame = _window(hist, calib_start, calib_end)
    empty = pd.DataFrame(columns=["calendar_year", "income_pp", "pop_pp",
                                  "residual_pp", "total_pct"])
    if frame.empty:
        return empty

    eps = _num(model["elasticity_income"], 0.0)
    value = _column_series(frame, series_spec(key)["column"])
    pop = _column_series(frame, "population")
    rgdppc = _column_series(frame, "real_gdp_per_capita")

    growth = value.pct_change() * 100.0
    g_pop = pop.pct_change() * 100.0
    g_pc = rgdppc.pct_change() * 100.0

    out = pd.DataFrame({
        "calendar_year": frame["calendar_year"].to_numpy(dtype=int),
        "income_pp": (eps * g_pc).to_numpy(dtype=float),
        "pop_pp": g_pop.to_numpy(dtype=float),
        "total_pct": growth.to_numpy(dtype=float),
    })
    out["residual_pp"] = out["total_pct"] - out["income_pp"] - out["pop_pp"]
    out = out.dropna(subset=["total_pct"])

    if model["break_year"] is not None:
        out = out[out["calendar_year"] != int(model["break_year"])]
    return out.reset_index(drop=True)


# ═══════════════════════ 4. scenario growth + forecast ══════════════════════

def population_growth(hist: pd.DataFrame,
                      calib_start: int = DEFAULT_CALIB_START,
                      calib_end: int = HISTORY_END) -> float:
    """Population CAGR (%) over the calibration window."""
    frame = _window(hist, calib_start, calib_end)
    pop = _column_series(frame, "population").dropna()
    years_col = frame.loc[pop.index, "calendar_year"] if len(pop) else pd.Series(dtype=int)
    if len(pop) < 2 or pop.iloc[0] <= 0:
        return POPULATION_FALLBACK
    span = int(years_col.iloc[-1] - years_col.iloc[0])
    cagr = _cagr(float(pop.iloc[0]), float(pop.iloc[-1]), max(span, 1))
    return cagr if math.isfinite(_clean(cagr)) else POPULATION_FALLBACK


def scenario_growth(model: dict,
                    scenarios: Sequence[str] = tuple(SCENARIO_ORDER),
                    base_gdp_growth: float = DEFAULT_BASE_GDP_GROWTH,
                    spread: float = DEFAULT_SCENARIO_SPREAD,
                    pop_growth: float = POPULATION_FALLBACK,
                    horizon: int = HORIZON,
                    start_year: int = FORECAST_START,
                    model_choice: str = "Driver") -> Dict[str, dict]:
    """
    Annual demand growth (%) each scenario implies, per year.

    Driver basis: ``g = g_pop + eps * (g_gdp - g_pop) + residual * decay``,
    where the residual drift fades linearly to zero by ``horizon`` so a one-off
    contraction is not compounded for a decade.

    Trend basis: the fitted log-linear growth, shifted by half of the GDP
    surprise, so the scenarios still differ but without elasticities.

    Returns ``{scenario: {..., growth_by_year: {year: pct}}}``.
    """
    eps = model.get("elasticity_income", float("nan"))
    residual = _num(model.get("residual_pct"), 0.0)
    trend_growth = _num(model.get("trend_growth_pct"), float("nan"))
    driver_ok = (model_choice == "Driver"
                 and model.get("model") == "Driver"
                 and math.isfinite(_clean(eps)))
    span = max(int(horizon) - int(start_year), 1)

    out: Dict[str, dict] = {}
    for scenario in SCENARIO_ORDER:
        if scenario not in scenarios:
            continue
        gdp = _num(base_gdp_growth, DEFAULT_BASE_GDP_GROWTH)
        if scenario == "Low":
            gdp -= _num(spread, 0.0)
        elif scenario == "High":
            gdp += _num(spread, 0.0)

        growth_by_year: Dict[int, float] = {}
        for year in range(int(start_year), int(horizon) + 1):
            decay = max(0.0, (int(horizon) - year) / span)
            if driver_ok:
                g = (pop_growth
                     + eps * (gdp - pop_growth)
                     + residual * decay)
                basis = "Driver model"
            elif math.isfinite(_clean(trend_growth)):
                # Trend basis: shift the fitted growth by half the GDP surprise.
                g = trend_growth + (gdp - _num(base_gdp_growth, DEFAULT_BASE_GDP_GROWTH)) * 0.5
                basis = "Trend model"
            else:
                g = 2.0
                basis = "Fallback 2%"
            growth_by_year[year] = _clamp(g, *GROWTH_CLAMP)

        finite = [v for v in growth_by_year.values() if math.isfinite(v)]
        average = float(np.mean(finite)) if finite else 0.0
        out[scenario] = {
            "scenario": scenario,
            "gdp_growth_pct": gdp,
            "population_growth_pct": pop_growth,
            "demand_growth_pct": average,
            "first_year_growth_pct": growth_by_year.get(int(start_year), average),
            "last_year_growth_pct": growth_by_year.get(int(horizon), average),
            "growth_by_year": growth_by_year,
            "basis": basis,
        }
    return out


def forecast_series(hist: pd.DataFrame, key: str,
                    grows: Dict[str, dict],
                    horizon: int = HORIZON,
                    start_year: int = FORECAST_START) -> pd.DataFrame:
    """
    Low / Base / High paths for one series, compounded from the last reported
    value.  ``calendar_year, series, scenario, value, growth_pct, provenance``.
    """
    anchor_year, anchor_value = last_actual(hist, key)
    empty = pd.DataFrame(columns=["calendar_year", "series", "scenario", "value",
                                  "growth_pct", "provenance"])
    if anchor_year is None or not math.isfinite(_clean(anchor_value)):
        return empty
    first = max(int(start_year), anchor_year + 1)

    rows = []
    for scenario in SCENARIO_ORDER:
        info = grows.get(scenario)
        if not info:
            continue
        value = anchor_value
        for year in range(first, int(horizon) + 1):
            rate = _num((info.get("growth_by_year") or {}).get(year),
                        _num(info.get("demand_growth_pct"), 0.0)) / 100.0
            value = value * (1.0 + rate)
            rows.append({"calendar_year": year, "series": key, "scenario": scenario,
                         "value": value, "growth_pct": rate * 100.0,
                         "provenance": PROJECTED})
    return pd.DataFrame(rows)


def forecast_band(hist: pd.DataFrame, key: str,
                  grows: Dict[str, dict], horizon: int = HORIZON) -> pd.DataFrame:
    """Wide frame ``calendar_year, Low, Base, High`` for a fan chart."""
    path = forecast_series(hist, key, grows, horizon)
    if path.empty:
        return pd.DataFrame(columns=["calendar_year", "Low", "Base", "High"])
    band = path.pivot_table(index="calendar_year", columns="scenario",
                            values="value", aggfunc="last")
    for scenario in SCENARIO_ORDER:
        if scenario not in band.columns:
            band[scenario] = np.nan
    return band[SCENARIO_ORDER].reset_index()


def horizon_values(hist: pd.DataFrame, key: str, grows: Dict[str, dict],
                   horizon: int = HORIZON) -> Dict[str, float]:
    """``{scenario: value at the horizon}``."""
    path = forecast_series(hist, key, grows, horizon)
    if path.empty:
        return {}
    last_year = path["calendar_year"].max()
    last = path[path["calendar_year"] == last_year]
    return {str(row["scenario"]): float(row["value"]) for _, row in last.iterrows()}


# ══════════════════════ 5. backtesting (objective 6) ════════════════════════

def backtest(hist: pd.DataFrame, key: str,
             calib_start: int = DEFAULT_CALIB_START,
             train_end: int = BACKTEST_TRAIN_END,
             test_end: int = HISTORY_END) -> dict:
    """
    Validate both models for one series.

    * **in-sample** -- fitted values over the calibration window, i.e. how well
      the model describes the reported years it was given.
    * **hold-out**  -- fit on ``calib_start .. train_end`` and predict
      ``train_end+1 .. test_end``.  The trend model extrapolates; the driver
      model is handed the *actual* real-GDP-per-head and population growth of
      the test years but not the demand answer.

    Returns ``{"metrics": DataFrame, "predictions": DataFrame}`` with MAPE %,
    RMSE, R2 and bias % per model per window.
    """
    spec = series_spec(key)
    metric_cols = ["series", "model", "window", "mape", "rmse", "r2", "bias", "n"]
    if hist is None or hist.empty or spec["column"] not in hist.columns:
        return {"metrics": pd.DataFrame(columns=metric_cols), "predictions": pd.DataFrame()}

    frame = hist[["calendar_year", spec["column"]]].copy()
    for column in ("real_gdp_per_capita", "population"):
        frame[column] = _column_series(hist, column)
    frame["value"] = pd.to_numeric(frame[spec["column"]], errors="coerce")
    frame = frame.dropna(subset=["value"]).sort_values("calendar_year")
    frame = frame[frame["calendar_year"] <= int(test_end)]
    if frame.empty:
        return {"metrics": pd.DataFrame(columns=metric_cols), "predictions": pd.DataFrame()}

    break_year = detect_break(hist, key)
    train = frame[(frame["calendar_year"] >= calib_start)
                  & (frame["calendar_year"] <= train_end)]
    test = frame[frame["calendar_year"] > train_end]
    if len(train) < 4 or test.empty:
        return {"metrics": pd.DataFrame(columns=metric_cols), "predictions": pd.DataFrame()}

    metrics: List[dict] = []
    predictions: List[dict] = []

    train_years = train["calendar_year"].to_numpy(dtype=float)
    test_years = test["calendar_year"].to_numpy(dtype=float)

    # ── trend model ────────────────────────────────────────────────────────
    trend_fit = _lstsq([train_years, break_flags(train_years, break_year)],
                       np.log(train["value"].to_numpy(dtype=float)))
    if math.isfinite(_clean(trend_fit["coef"][1])):
        base, slope = trend_fit["coef"][0], trend_fit["coef"][1]
        dummy_coef = trend_fit["coef"][2] if len(trend_fit["coef"]) > 2 else 0.0

        fitted = np.exp(base + slope * train_years
                        + dummy_coef * break_flags(train_years, break_year))
        metrics.append({"series": key, "model": "Trend", "window": "in-sample",
                        **_metrics(train["value"].to_numpy(dtype=float), fitted)})

        predicted = np.exp(base + slope * test_years
                           + dummy_coef * break_flags(test_years, break_year))
        metrics.append({"series": key, "model": "Trend", "window": "hold-out",
                        **_metrics(test["value"].to_numpy(dtype=float), predicted)})
        for year, actual, pred in zip(test["calendar_year"], test["value"], predicted):
            predictions.append({"series": key, "model": "Trend",
                                "calendar_year": int(year),
                                "actual": float(actual), "predicted": float(pred)})

    # ── driver model, recursed on actual driver growth ─────────────────────
    train_pop = train["population"].to_numpy(dtype=float)
    train_pc = train["real_gdp_per_capita"].to_numpy(dtype=float)
    driver_fit = _lstsq([np.log(train_pc), break_flags(train_years, break_year)],
                        np.log(train["value"].to_numpy(dtype=float) / train_pop))
    eps_train = _clamp(driver_fit["coef"][1] if len(driver_fit["coef"]) > 1 else float("nan"),
                       *ELASTICITY_CLAMP)

    if math.isfinite(_clean(eps_train)):
        # post-break drift inside the training window (else its last 3 years)
        train_growth = train["value"].pct_change() * 100.0
        g_pop_train = train["population"].pct_change() * 100.0
        g_pc_train = pd.Series(train_pc, index=train.index).pct_change() * 100.0
        residual = train_growth - (g_pop_train + eps_train * (g_pc_train - g_pop_train))
        if break_year is not None:
            keep = train["calendar_year"] > int(break_year)
            resid_series = residual[keep.to_numpy()]
        else:
            resid_series = residual
        resid_series = resid_series.dropna()
        drift = float(resid_series.mean()) if len(resid_series) else 0.0

        # in-sample fit: rebuild the per-capita level from the dummy model
        dummy_coef = driver_fit["coef"][2] if len(driver_fit["coef"]) > 2 else 0.0
        base = driver_fit["coef"][0]
        fitted = np.exp(base + eps_train * np.log(train_pc)
                        + dummy_coef * break_flags(train_years, break_year)) * train_pop
        metrics.append({"series": key, "model": "Driver", "window": "in-sample",
                        **_metrics(train["value"].to_numpy(dtype=float), fitted)})

        # hold-out: step forward on the reported drivers
        value = float(train["value"].iloc[-1])
        rows = []
        for year in test["calendar_year"]:
            previous = frame[frame["calendar_year"] == year - 1]
            current = frame[frame["calendar_year"] == year]
            d_pc = d_pop = 0.0
            if not previous.empty and not current.empty:
                pc_prev = _clean(previous["real_gdp_per_capita"].iloc[0])
                pc_now = _clean(current["real_gdp_per_capita"].iloc[0])
                pop_prev = _clean(previous["population"].iloc[0])
                pop_now = _clean(current["population"].iloc[0])
                if math.isfinite(pc_prev) and math.isfinite(pc_now) and pc_prev > 0:
                    d_pc = pc_now / pc_prev - 1.0
                if math.isfinite(pop_prev) and math.isfinite(pop_now) and pop_prev > 0:
                    d_pop = pop_now / pop_prev - 1.0
            value = value * (1.0 + d_pop + eps_train * (d_pc - d_pop) + drift / 100.0)
            rows.append({"calendar_year": int(year), "predicted": value})

        pred_frame = pd.DataFrame(rows).merge(
            test[["calendar_year", "value"]].rename(columns={"value": "actual"}),
            on="calendar_year", how="inner")
        metrics.append({"series": key, "model": "Driver", "window": "hold-out",
                        **_metrics(pred_frame["actual"].to_numpy(dtype=float),
                                   pred_frame["predicted"].to_numpy(dtype=float))})
        for _, row in pred_frame.iterrows():
            predictions.append({"series": key, "model": "Driver",
                                "calendar_year": int(row["calendar_year"]),
                                "actual": float(row["actual"]),
                                "predicted": float(row["predicted"])})

    return {
        "metrics": pd.DataFrame(metrics, columns=metric_cols),
        "predictions": pd.DataFrame(predictions),
        "train_end": int(train_end),
        "test_end": int(test_end),
        "break_year": break_year,
    }


def backtest_all(hist: pd.DataFrame,
                 keys: Optional[Iterable[str]] = None,
                 calib_start: int = DEFAULT_CALIB_START,
                 train_end: int = BACKTEST_TRAIN_END,
                 test_end: int = HISTORY_END) -> dict:
    """Backtest every series; pooled metrics plus per-series predictions."""
    keys = list(keys or HISTORY_SERIES_KEYS)
    metrics, predictions = [], []
    for key in keys:
        result = backtest(hist, key, calib_start, train_end, test_end)
        if not result["metrics"].empty:
            m = result["metrics"].copy()
            m["label"] = series_spec(key)["short"]
            m["domain"] = series_spec(key)["domain"]
            metrics.append(m)
        if not result["predictions"].empty:
            p = result["predictions"].copy()
            p["label"] = series_spec(key)["short"]
            p["domain"] = series_spec(key)["domain"]
            predictions.append(p)
    return {
        "metrics": pd.concat(metrics, ignore_index=True) if metrics else pd.DataFrame(),
        "predictions": pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame(),
        "train_end": int(train_end),
        "test_end": int(test_end),
    }


# ═══════════════ 6. sector / province demand to 2035 (objective 4) ══════════

def _share_projection(shares: pd.DataFrame, calib_start: int, horizon: int,
                      clamp: float = SHARE_TREND_CLAMP,
                      min_share: float = MIN_SHARE) -> pd.DataFrame:
    """
    Project composition shares, anchored on the last reported share and drifting
    at the fitted rate, clamped to ``clamp`` per year so small categories cannot
    explode.  Shares are then renormalised to sum to one.
    """
    if shares.empty:
        return pd.DataFrame(columns=["calendar_year", "key", "share"])

    last_year = int(shares["calendar_year"].max())
    first_year = int(shares["calendar_year"].min())
    target_years = list(range(first_year, int(horizon) + 1))

    projections: Dict[str, pd.Series] = {}
    for key, group in shares.groupby("key"):
        group = group.sort_values("calendar_year")
        window = group[group["calendar_year"] >= calib_start]
        if len(window) < 3:
            window = group.tail(4)
        fit = _lstsq([window["calendar_year"].to_numpy(dtype=float)],
                     np.log(np.clip(window["share"].to_numpy(dtype=float), min_share, None)))
        slope = _clamp(fit["coef"][1] if len(fit["coef"]) > 1 else float("nan"),
                       -clamp, clamp)
        # Anchor on the share actually reported last -- never inflate a small
        # category up to a floor, which is what makes tiny groups explode.
        last_share = max(float(group["share"].iloc[-1]), min_share)
        values = {}
        for year in target_years:
            if math.isfinite(_clean(slope)) and year > last_year:
                values[year] = last_share * (1.0 + slope) ** (year - last_year)
            else:
                rows = group.loc[group["calendar_year"] == year, "share"]
                values[year] = float(rows.iloc[0]) if len(rows) else last_share
        projections[key] = pd.Series(values)

    proj = pd.DataFrame(projections)
    proj.index.name = "calendar_year"
    proj = proj.clip(lower=min_share)
    proj = proj.div(proj.sum(axis=1), axis=0)
    long = proj.reset_index().melt(id_vars="calendar_year", var_name="key",
                                   value_name="share")
    long = long[long["calendar_year"] > last_year]
    observed = shares[shares["calendar_year"] <= last_year][["calendar_year", "key", "share"]]
    return pd.concat([observed, long], ignore_index=True).sort_values(
        ["calendar_year", "key"]).reset_index(drop=True)


def project_composition(comp_df: pd.DataFrame, key_col: str, value_col: str,
                        grows: Dict[str, dict],
                        calib_start: int = DEFAULT_CALIB_START,
                        horizon: int = HORIZON,
                        base_year: int = HISTORY_END,
                        min_share: float = MIN_SHARE) -> dict:
    """
    Sector or province demand to the horizon.

    Group *shares* are trended (clamped, renormalised); the group *total* follows
    the electricity scenario growth anchored on this table's own last reported
    year, so the parts always add up to the whole.

    Returns ``{"history", "projection", "shares", "base_year", "base_total",
    "groups"}``.
    """
    empty = pd.DataFrame(columns=["calendar_year", "key", "value", "share",
                                  "scenario", "provenance"])
    blank = {"history": empty, "projection": empty, "shares": empty,
             "base_year": None, "base_total": float("nan"), "groups": []}
    if comp_df is None or comp_df.empty or key_col not in comp_df.columns:
        return blank

    frame = comp_df.copy()
    frame["calendar_year"] = pd.to_numeric(frame["calendar_year"], errors="coerce")
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.dropna(subset=["calendar_year", value_col])
    if frame.empty:
        return blank
    frame["calendar_year"] = frame["calendar_year"].astype(int)

    totals = frame.groupby("calendar_year")[value_col].sum()
    history = frame.rename(columns={key_col: "key", value_col: "value"})
    history["share"] = history["value"] / history["calendar_year"].map(totals)
    history["provenance"] = ACTUAL
    history = history[["calendar_year", "key", "value", "share", "provenance"]]
    groups = sorted(history["key"].unique().tolist())

    if base_year not in totals.index:
        base_year = int(totals.index.max())
    base_total = float(totals.loc[base_year])

    shares = _share_projection(history[["calendar_year", "key", "share"]],
                               calib_start, horizon, min_share=min_share)

    rows = []
    for scenario, info in (grows or {}).items():
        growth_by_year = info.get("growth_by_year") or {}
        total = base_total
        for year in range(int(base_year) + 1, int(horizon) + 1):
            rate = _num(growth_by_year.get(year),
                        _num(info.get("demand_growth_pct"), 0.0)) / 100.0
            total = total * (1.0 + rate)
            year_shares = shares[shares["calendar_year"] == year]
            for _, row in year_shares.iterrows():
                share = max(_num(row["share"]), min_share)
                rows.append({"calendar_year": year, "key": row["key"],
                             "value": total * share, "share": share,
                             "scenario": scenario, "provenance": PROJECTED})
    projection = pd.DataFrame(rows) if rows else empty

    return {"history": history, "projection": projection, "shares": shares,
            "base_year": int(base_year), "base_total": base_total,
            "groups": groups}


# ═══════════════ 7. supply vs demand + import dependency (objective 5) ══════

def _project_trend(frame: pd.DataFrame, value_col: str, calib_start: int,
                   horizon: int, floor: float = 0.0) -> pd.DataFrame:
    """Linear trend projection of one column, floored, tagged 'Projected'."""
    out = frame[["calendar_year", value_col, "provenance"]].copy()
    if frame.empty:
        return out
    window = frame[(frame["calendar_year"] >= calib_start) & frame[value_col].notna()]
    fit = _lstsq([window["calendar_year"].to_numpy(dtype=float)],
                 window[value_col].to_numpy(dtype=float))
    slope = fit["coef"][1] if len(fit["coef"]) > 1 else float("nan")
    if not math.isfinite(_clean(slope)):
        return out
    base = fit["coef"][0]
    last_year = int(frame["calendar_year"].max())
    rows = [{"calendar_year": year,
             value_col: max(base + slope * year, floor),
             "provenance": PROJECTED}
            for year in range(last_year + 1, int(horizon) + 1)]
    if not rows:
        return out
    return pd.concat([out, pd.DataFrame(rows)], ignore_index=True)


def build_supply_gap(primary_df: pd.DataFrame,
                     gen_df: pd.DataFrame,
                     gas_df: pd.DataFrame,
                     demand_forecast: pd.DataFrame,
                     calib_start: int = DEFAULT_CALIB_START,
                     horizon: int = HORIZON) -> dict:
    """
    Supply-demand gap and import dependency to the horizon.

    * ``total``   -- primary supply (TOE) vs total final energy demand, the gap,
      and the gap as a share of supply.  Supply is trend-projected on its
      calibration window, demand comes from the scenario fan.
    * ``imports`` -- gas import dependency ``(consumption - production) /
      consumption`` and the electricity import share ``imports / (generation +
      imports)``, each trend-projected from its last reported year.
    """
    result = {"total": pd.DataFrame(), "imports": pd.DataFrame(),
              "last_supply_year": None, "supply_cagr_pct": float("nan"),
              "last_gas_year": None, "last_elec_import_year": None}

    # ── total energy: primary supply vs demand ─────────────────────────────
    if primary_df is not None and not primary_df.empty:
        p = primary_df.copy()
        p["calendar_year"] = pd.to_numeric(p["calendar_year"], errors="coerce")
        value_col = "supply_toe" if "supply_toe" in p.columns else "imports_toe"
        p[value_col] = pd.to_numeric(p[value_col], errors="coerce")
        supply = (p.dropna(subset=["calendar_year", value_col])
                  .groupby("calendar_year")[value_col].sum().reset_index())
        supply.columns = ["calendar_year", "supply"]
        supply["provenance"] = ACTUAL
        if not supply.empty:
            supply["calendar_year"] = supply["calendar_year"].astype(int)
            last_year = int(supply["calendar_year"].max())
            result["last_supply_year"] = last_year
            window = supply[supply["calendar_year"] >= calib_start]
            fit = _lstsq([window["calendar_year"].to_numpy(dtype=float)],
                         np.log(np.clip(window["supply"].to_numpy(dtype=float), 1e-9, None)))
            slope = fit["coef"][1] if len(fit["coef"]) > 1 else float("nan")
            if math.isfinite(_clean(slope)):
                result["supply_cagr_pct"] = math.expm1(slope) * 100.0
                anchor = float(supply["supply"].iloc[-1])
                rows = []
                for year in range(last_year + 1, int(horizon) + 1):
                    anchor = anchor * (1.0 + math.expm1(slope))
                    rows.append({"calendar_year": year, "supply": anchor,
                                 "provenance": PROJECTED})
                if rows:
                    supply = pd.concat([supply, pd.DataFrame(rows)], ignore_index=True)

            if demand_forecast is not None and not demand_forecast.empty \
                    and "series" in demand_forecast.columns:
                demand_all = demand_forecast[demand_forecast["series"] == "total_final"]
                for scenario in sorted(demand_all["scenario"].unique()):
                    path = demand_all[demand_all["scenario"] == scenario]
                    if path.empty:
                        continue
                    merged = supply.merge(
                        path[["calendar_year", "value"]].rename(columns={"value": "demand"}),
                        on="calendar_year", how="left").sort_values("calendar_year")
                    merged["demand"] = merged["demand"].ffill()
                    merged = merged.dropna(subset=["demand"])
                    merged["gap"] = merged["supply"] - merged["demand"]
                    merged["gap_pct"] = merged["gap"] / merged["supply"] * 100.0
                    merged["scenario"] = scenario
                    result["total"] = pd.concat([result["total"], merged],
                                                ignore_index=True)

            # Supply growth that would be needed to close the horizon gap.
            last_supply = float(supply.loc[supply["calendar_year"] == last_year,
                                           "supply"].iloc[0])
            result["last_supply"] = last_supply
            years = max(int(horizon) - last_year, 1)
            required: Dict[str, float] = {}
            if not result["total"].empty:
                for scenario, group in result["total"].groupby("scenario"):
                    horizon_rows = group[group["calendar_year"] == int(horizon)]
                    if horizon_rows.empty or last_supply <= 0:
                        continue
                    demand_h = float(horizon_rows.iloc[0]["demand"])
                    required[str(scenario)] = ((demand_h / last_supply) ** (1.0 / years) - 1.0) * 100.0
            result["required_supply_cagr"] = required

    # ── gas import dependency ──────────────────────────────────────────────
    # Measured from the reported supply balance: production and consumption are
    # each trend-projected, then dependency = (consumption - production) /
    # consumption.  Pakistan crossed from surplus to deficit in 2018, so the
    # dependency only becomes positive at the end of the reported window; a
    # balance-based projection is far more meaningful than trending a series
    # that is zero for nineteen of its years.  (The LNG volume column in
    # fact_lng_imports is inconsistent with its own value column -- 3.7 BCF for
    # USD 3.4bn of imports -- so it is deliberately not used here.)
    if gas_df is not None and not gas_df.empty and "consumption_bcf" in gas_df.columns:
        g = gas_df.copy()
        g["calendar_year"] = pd.to_numeric(g["calendar_year"], errors="coerce")
        for column in ("consumption_bcf", "production_bcf"):
            g[column] = pd.to_numeric(g[column], errors="coerce")
        g = g.dropna(subset=["calendar_year", "consumption_bcf"])
        g = g[g["consumption_bcf"] > 0]
        if not g.empty:
            g["calendar_year"] = g["calendar_year"].astype(int)
            g = g.sort_values("calendar_year")
            dependency = ((g["consumption_bcf"] - g["production_bcf"])
                          / g["consumption_bcf"] * 100.0)
            gas_dep = pd.DataFrame({
                "calendar_year": g["calendar_year"].to_numpy(),
                "gas_import_dep_pct": np.clip(dependency.to_numpy(dtype=float), 0.0, None),
                "provenance": ACTUAL,
            }).reset_index(drop=True)
            result["last_gas_year"] = int(gas_dep["calendar_year"].max())

            cons_frame = pd.DataFrame({
                "calendar_year": g["calendar_year"].to_numpy(),
                "consumption_bcf": g["consumption_bcf"].to_numpy(dtype=float),
                "provenance": ACTUAL,
            })
            prod_frame = pd.DataFrame({
                "calendar_year": g["calendar_year"].to_numpy(),
                "production_bcf": g["production_bcf"].to_numpy(dtype=float),
                "provenance": ACTUAL,
            })
            cons_proj = _project_trend(cons_frame, "consumption_bcf", calib_start,
                                       horizon, floor=0.0)
            prod_proj = _project_trend(prod_frame, "production_bcf", calib_start,
                                       horizon, floor=0.0)
            balance = cons_proj.merge(
                prod_proj[["calendar_year", "production_bcf"]],
                on="calendar_year", how="outer").sort_values("calendar_year")
            balance["consumption_bcf"] = balance["consumption_bcf"].ffill()
            balance["production_bcf"] = balance["production_bcf"].ffill()
            balance = balance.dropna(subset=["consumption_bcf", "production_bcf"])
            balance = balance[balance["consumption_bcf"] > 0]
            projected_dep = np.clip(
                (balance["consumption_bcf"] - balance["production_bcf"])
                / balance["consumption_bcf"] * 100.0, 0.0, None)
            gas_projected = pd.DataFrame({
                "calendar_year": balance["calendar_year"].to_numpy(),
                "gas_import_dep_pct": projected_dep.to_numpy(dtype=float),
                "provenance": balance["provenance"].to_numpy(),
            })
            gas_projected.loc[gas_projected["calendar_year"] > result["last_gas_year"],
                              "provenance"] = PROJECTED
            result["imports"] = (gas_dep.merge(gas_projected, on="calendar_year",
                                               how="outer", suffixes=("_rep", "_bal"))
                                 .assign(gas_import_dep_pct=lambda d: d["gas_import_dep_pct_bal"]
                                         .fillna(d["gas_import_dep_pct_rep"]),
                                         provenance=lambda d: d["provenance_bal"]
                                         .fillna(d["provenance_rep"]))
                                 [["calendar_year", "gas_import_dep_pct", "provenance"]]
                                 .sort_values("calendar_year").reset_index(drop=True))
            result["gas_production_bcf"] = float(g["production_bcf"].iloc[-1])
            result["gas_consumption_bcf"] = float(g["consumption_bcf"].iloc[-1])

    # ── electricity import share ───────────────────────────────────────────
    if gen_df is not None and not gen_df.empty and "imports_gwh" in gen_df.columns:
        e = gen_df.copy()
        e["calendar_year"] = pd.to_numeric(e["calendar_year"], errors="coerce")
        for column in ("imports_gwh", "generation_gwh"):
            e[column] = pd.to_numeric(e[column], errors="coerce")
        e = e.dropna(subset=["calendar_year", "imports_gwh", "generation_gwh"])
        e = e[(e["generation_gwh"] + e["imports_gwh"]) > 0]
        if not e.empty:
            e["calendar_year"] = e["calendar_year"].astype(int)
            share = e["imports_gwh"] / (e["generation_gwh"] + e["imports_gwh"]) * 100.0
            elec = pd.DataFrame({
                "calendar_year": e["calendar_year"].to_numpy(),
                "elec_import_share_pct": share.to_numpy(dtype=float),
                "provenance": ACTUAL,
            }).sort_values("calendar_year").reset_index(drop=True)
            result["last_elec_import_year"] = int(elec["calendar_year"].max())
            elec_proj = _project_trend(elec, "elec_import_share_pct", calib_start,
                                       horizon, floor=0.0)
            if result["imports"].empty:
                result["imports"] = elec_proj
            else:
                merged = result["imports"].merge(elec_proj, on="calendar_year", how="outer")
                merged["provenance"] = merged["provenance_x"].fillna(merged["provenance_y"])
                result["imports"] = (merged.drop(columns=["provenance_x", "provenance_y"])
                                     .sort_values("calendar_year"))

    if not result["imports"].empty:
        result["imports"] = result["imports"].sort_values("calendar_year").reset_index(drop=True)

    return result


# ═══════════════════════════════ 8. KPIs ════════════════════════════════════

def kpi_readings(models: Dict[str, dict],
                 grows: Dict[str, Dict[str, dict]],
                 gap: dict,
                 hist: pd.DataFrame,
                 horizon: int = HORIZON,
                 base_scenario: str = "Base") -> Dict[str, dict]:
    """
    The headline numbers: demand now and at the horizon (total and electricity),
    the reported vs forecast growth rate, the income elasticity, and the
    horizon supply gap and import dependency.
    """
    out: Dict[str, dict] = {}

    for key in ("total_final", "elec_grid"):
        year, value = last_actual(hist, key)
        band = horizon_values(hist, key, grows.get(key, {}), horizon)
        out[key] = {
            "year": year,
            "value": value,
            "horizon_value": band.get(base_scenario, float("nan")),
            "scenarios": band,
            "domain": series_spec(key)["domain"],
            "label": series_spec(key)["label"],
            "short": series_spec(key)["short"],
            "growth_pct": _num((grows.get(key, {}).get(base_scenario) or {})
                               .get("demand_growth_pct"), float("nan")),
            "first_year_growth_pct": _num((grows.get(key, {}).get(base_scenario) or {})
                                          .get("first_year_growth_pct"), float("nan")),
        }

    model = models.get("total_final", {})
    total = out.get("total_final", {})
    forecast_years = max(int(horizon) - int(total.get("year") or HISTORY_END), 0)
    out["demand_cagr"] = {
        "observed_cagr_pct": _num(model.get("observed_cagr_pct"), float("nan")),
        "forecast_cagr_pct": _num(total.get("growth_pct"), float("nan")),
        "forecast_years": forecast_years,
        "calib_start": _num(model.get("calib_start"), DEFAULT_CALIB_START),
        "calib_end": _num(model.get("calib_end"), HISTORY_END),
    }

    out["elasticity"] = {
        "elasticity_income": _num(model.get("elasticity_income"), float("nan")),
        "elasticity_gdp": _num(model.get("elasticity_gdp"), float("nan")),
        "r2_per_capita": _num(model.get("r2_per_capita"), float("nan")),
        "r2_gdp": _num(model.get("r2_gdp"), float("nan")),
        "growth_corr": _num(model.get("growth_corr"), float("nan")),
        "residual_pct": _num(model.get("residual_pct"), float("nan")),
        "model": model.get("model", "Trend"),
        "break_year": model.get("break_year"),
    }

    total_gap = gap.get("total", pd.DataFrame()) if gap else pd.DataFrame()
    if isinstance(total_gap, pd.DataFrame) and not total_gap.empty:
        horizon_rows = total_gap[total_gap["calendar_year"] == int(horizon)]
        if not horizon_rows.empty:
            base_rows = horizon_rows[horizon_rows["scenario"] == base_scenario]
            row = base_rows.iloc[0] if not base_rows.empty else horizon_rows.iloc[0]
            out["supply_gap"] = {
                "year": int(row["calendar_year"]),
                "supply": float(row["supply"]),
                "demand": float(row["demand"]),
                "gap": float(row["gap"]),
                "gap_pct": float(row["gap_pct"]),
                "scenario": str(row.get("scenario", base_scenario)),
                "supply_cagr_pct": _num(gap.get("supply_cagr_pct"), float("nan")),
                "required_supply_cagr_pct": _num(
                    (gap.get("required_supply_cagr") or {}).get(base_scenario), float("nan")),
                "last_supply_year": gap.get("last_supply_year"),
                "last_supply": _num(gap.get("last_supply"), float("nan")),
            }

    imports = gap.get("imports", pd.DataFrame()) if gap else pd.DataFrame()
    if isinstance(imports, pd.DataFrame) and not imports.empty:
        horizon_rows = imports[imports["calendar_year"] == int(horizon)]
        if not horizon_rows.empty:
            row = horizon_rows.iloc[0]
            out["imports"] = {
                "year": int(row["calendar_year"]),
                "gas_import_dep_pct": _num(row.get("gas_import_dep_pct"), float("nan")),
                "elec_import_share_pct": _num(row.get("elec_import_share_pct"), float("nan")),
                "last_gas_year": gap.get("last_gas_year"),
                "last_elec_import_year": gap.get("last_elec_import_year"),
            }

    return out


# ═══════════════════════════ 9. one-call pipeline ═══════════════════════════

def build_dashboard_data(fuel_df: pd.DataFrame,
                         re_df: pd.DataFrame,
                         econ_df: pd.DataFrame,
                         primary_df: pd.DataFrame,
                         gen_df: pd.DataFrame,
                         gas_df: pd.DataFrame,
                         sector_df: pd.DataFrame,
                         province_df: pd.DataFrame,
                         scenarios: Sequence[str] = tuple(SCENARIO_ORDER),
                         calib_start: int = DEFAULT_CALIB_START,
                         horizon: int = HORIZON,
                         base_gdp_growth: float = DEFAULT_BASE_GDP_GROWTH,
                         spread: float = DEFAULT_SCENARIO_SPREAD,
                         model_choice: str = "Driver") -> dict:
    """
    Fetch-free, one call: everything the page needs.

    The page fetches the eight DataFrames, calls this, and renders the result.
    ``model_choice`` picks the forecast basis ("Driver" or "Trend").
    """
    hist = build_history(fuel_df, re_df, econ_df)
    pop_growth = population_growth(hist, calib_start, HISTORY_END)

    models = {key: fit_driver_model(hist, key, calib_start, HISTORY_END)
              for key in HISTORY_SERIES_KEYS}
    grows = {key: scenario_growth(models[key], scenarios, base_gdp_growth,
                                  spread, pop_growth, horizon,
                                  model_choice=model_choice)
             for key in HISTORY_SERIES_KEYS}

    forecast_parts = []
    for key in HISTORY_SERIES_KEYS:
        path = forecast_series(hist, key, grows[key], horizon)
        if not path.empty:
            path = path.copy()
            anchor_year, anchor_value = last_actual(hist, key)
            path["anchor_year"] = anchor_year
            path["anchor_value"] = anchor_value
            forecast_parts.append(path)
    forecast = pd.concat(forecast_parts, ignore_index=True) if forecast_parts else pd.DataFrame()

    sectors = project_composition(sector_df, "sector_name", "consumption_gwh",
                                  grows.get("elec_grid", {}), calib_start, horizon)
    provinces = project_composition(province_df, "province_name", "consumption_gwh",
                                    grows.get("elec_grid", {}), calib_start, horizon)

    gap = build_supply_gap(primary_df, gen_df, gas_df, forecast, calib_start, horizon)

    test_years = min(DEFAULT_TEST_YEARS, max(HISTORY_END - FINAL_ENERGY_START - 4, 3))
    tests = backtest_all(hist, HISTORY_SERIES_KEYS, calib_start=calib_start,
                         train_end=HISTORY_END - test_years, test_end=HISTORY_END)

    decomposition = {key: decompose_growth(hist, key, calib_start, HISTORY_END)
                     for key in ("total_final", "electricity_final", "gas_final")}

    return {
        "history": hist,
        "models": models,
        "grows": grows,
        "forecast": forecast,
        "bands": {key: forecast_band(hist, key, grows[key], horizon)
                  for key in HISTORY_SERIES_KEYS},
        "drivers": driver_table(hist, calib_start, HISTORY_END),
        "decomposition": decomposition,
        "sectors": sectors,
        "provinces": provinces,
        "gap": gap,
        "backtest": tests,
        "kpis": kpi_readings(models, grows, gap, hist, horizon),
        "population_growth_pct": pop_growth,
        "calib_start": int(calib_start),
        "horizon": int(horizon),
        "base_gdp_growth": float(base_gdp_growth),
        "spread": float(spread),
        "model_choice": model_choice,
        "scenarios": list(scenarios),
        "history_end": int(hist["calendar_year"].max()) if not hist.empty else HISTORY_END,
        "breaks": {key: detect_break(hist, key) for key in HISTORY_SERIES_KEYS},
    }
