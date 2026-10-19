"""
core/operational_bottlenecks.py -- analytical engine for Q9.

Q9: What are the operational bottlenecks in fossil and renewable energy supplies?

An *operational bottleneck* is any constraint that stops installed energy
capability from becoming delivered energy.  This engine turns the raw warehouse
frames into two things:

  1. build_bottleneck_frame()  -- a tidy per-year frame of utilisation, supply
     and loss metrics (everything in database base units: MW, GWh, TOE, BCF).

  2. score_bottlenecks()       -- a ranked scorecard that expresses each
     bottleneck as a 0-100 *severity* (higher = more binding), tagged fossil /
     renewable / delivery, so the dashboard can answer "where is the choke point"
     directly.

Design rules
------------
* Pure pandas / numpy -- no Streamlit, no presentation.  Testable headless via
  scripts/verify_q9_bottlenecks.py.
* Direction-aware severity -- low capacity factor and high import dependence are
  both "bad", but they are normalised on their own reference bands, never a
  hard-coded 0-100 assumption.
* Honest gaps -- a missing denominator yields NaN, never a silent 0.
* One reference year -- the scorecard is evaluated at a single `base_year` so the
  ranking is internally consistent, exactly like Q3.

Hours in a year: 8760.  GWh per (MW-year) = 8760 / 1000 = 8.76.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────
HOURS = 8760.0
GWH_PER_MW_YEAR = HOURS / 1000.0          # 8.76 GWh delivered by 1 MW running all year

HISTORY_START = 2002
HISTORY_END = 2024                        # last year with real generation/supply data
DEFAULT_BASE_YEAR = 2024

# Fossil fuel streams (TOE domain) whose import dependence is a supply bottleneck
FOSSIL_SOURCES = {"Oil", "Gas", "LNG Imports", "LPG", "Coal"}

# Renewable-capacity source name -> the generation column it maps onto
RE_CAP_TO_GEN = {
    "Hydel": "hydro_gen_gwh",
    "Wind": "wind_gen_gwh",
    "Solar": "solar_gen_gwh",
    "Bagasse": "other_re_gen_gwh",
}

# Reference bands used to normalise raw metrics into 0-100 severities.
# (worst_case, best_case) -- severity is linear between them and clamped to 0-100.
UTILISATION_BANDS = {
    "fossil_cf_pct":      (15.0, 80.0),    # thermal fleet: <15% = severe under-use, 80% = none
    "re_cf_pct":          (8.0, 55.0),     # RE: solar/wind low by nature; 55% = no bottleneck
    "sys_load_factor_pct": (30.0, 85.0),
}


# ── Numeric helpers ──────────────────────────────────────────────────────────
def _num(value) -> float:
    """None / NaN / '' safe float (returns NaN rather than a misleading 0)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return np.nan
    return np.nan if f != f else f


def _col(df: pd.DataFrame, name: str) -> np.ndarray:
    """Numeric column as float array, or NaN array if the column is absent."""
    if df is None or name not in df.columns:
        return np.full(len(df) if df is not None else 0, np.nan)
    return pd.to_numeric(df[name], errors="coerce").to_numpy(dtype=float)


def _safe_div(num, den):
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    out = np.full(num.shape, np.nan)
    ok = np.isfinite(num) & np.isfinite(den) & (den != 0)
    out[ok] = num[ok] / den[ok]
    return out


# ── 1. Per-year bottleneck frame ─────────────────────────────────────────────
def build_bottleneck_frame(
    gen_df: pd.DataFrame,          # Q_ELEC_GEN: installed_capacity_mw, generation_gwh
    re_df: pd.DataFrame,           # Q_RENEWABLE_ENERGY: per-fuel gen columns
    re_cap_df: pd.DataFrame,       # Q_RENEWABLE_CAPACITY: renewable_source, installed_capacity_mw
    td_df: pd.DataFrame,           # Q_TD_LOSSES: td_losses_gwh
    gas_df: pd.DataFrame,          # Q_NATURAL_GAS: production_bcf, consumption_bcf, gap_bcf
    ps_df: pd.DataFrame,           # Q_PRIMARY_SUPPLY: source_name, supply_toe, imports_toe
) -> pd.DataFrame:
    """Return one tidy row per calendar year of operational-supply metrics.

    All quantities are base units: MW, GWh, TOE, BCF.  Percentages are 0-100.
    """
    frames = []

    # ---- electricity: total capability vs delivered generation -------------
    if gen_df is not None and not gen_df.empty:
        g = gen_df.copy()
        g["calendar_year"] = pd.to_numeric(g["calendar_year"], errors="coerce")
        cap = pd.to_numeric(g.get("installed_capacity_mw"), errors="coerce")
        gen = pd.to_numeric(g.get("generation_gwh"), errors="coerce")
        out = pd.DataFrame({
            "calendar_year": g["calendar_year"],
            "total_cap_mw": cap,
            "total_gen_gwh": gen,
        })
        frames.append(out)

    # ---- renewable-energy generation by fuel -------------------------------
    if re_df is not None and not re_df.empty:
        r = re_df.copy()
        r["calendar_year"] = pd.to_numeric(r["calendar_year"], errors="coerce")
        re_out = pd.DataFrame({"calendar_year": r["calendar_year"]})
        colmap = {
            "gen_solar_gwh": "solar_gen_gwh",
            "gen_wind_gwh": "wind_gen_gwh",
            "gen_hydro_gwh": "hydro_gen_gwh",
            "gen_other_renewables_gwh": "other_re_gen_gwh",
            "gen_coal_gwh": "coal_gen_gwh",
            "gen_gas_gwh": "gas_gen_gwh",
            "gen_nuclear_gwh": "nuclear_gen_gwh",
        }
        for src, dst in colmap.items():
            re_out[dst] = pd.to_numeric(r.get(src), errors="coerce")
        frames.append(re_out)

    if not frames:
        return pd.DataFrame()

    # merge the year-indexed frames
    df = frames[0]
    for extra in frames[1:]:
        df = df.merge(extra, on="calendar_year", how="outer")

    # ---- renewable installed capacity per source (pivot) -------------------
    if re_cap_df is not None and not re_cap_df.empty:
        rc = re_cap_df.copy()
        rc["calendar_year"] = pd.to_numeric(rc["calendar_year"], errors="coerce")
        rc["installed_capacity_mw"] = pd.to_numeric(rc["installed_capacity_mw"], errors="coerce")
        piv = rc.pivot_table(index="calendar_year", columns="renewable_source",
                             values="installed_capacity_mw", aggfunc="sum")
        piv = piv.rename(columns={k: f"{k}_cap_mw" for k in piv.columns})
        piv = piv.reset_index()
        df = df.merge(piv, on="calendar_year", how="left")

    # ---- T&D losses --------------------------------------------------------
    if td_df is not None and not td_df.empty:
        t = td_df.copy()
        t["calendar_year"] = pd.to_numeric(t["calendar_year"], errors="coerce")
        t = pd.DataFrame({
            "calendar_year": t["calendar_year"],
            "td_loss_gwh": pd.to_numeric(t.get("td_losses_gwh"), errors="coerce"),
        })
        df = df.merge(t, on="calendar_year", how="left")

    # ---- natural gas balance ----------------------------------------------
    if gas_df is not None and not gas_df.empty:
        ga = gas_df.copy()
        ga["calendar_year"] = pd.to_numeric(ga["calendar_year"], errors="coerce")
        ga_out = pd.DataFrame({
            "calendar_year": ga["calendar_year"],
            "gas_prod_bcf": pd.to_numeric(ga.get("production_bcf"), errors="coerce"),
            "gas_cons_bcf": pd.to_numeric(ga.get("consumption_bcf"), errors="coerce"),
        })
        df = df.merge(ga_out, on="calendar_year", how="left")

    # ---- fossil import dependence (TOE) -----------------------------------
    if ps_df is not None and not ps_df.empty:
        p = ps_df.copy()
        p["calendar_year"] = pd.to_numeric(p["calendar_year"], errors="coerce")
        p["supply_toe"] = pd.to_numeric(p.get("supply_toe"), errors="coerce")
        p["imports_toe"] = pd.to_numeric(p.get("imports_toe"), errors="coerce")
        fossil = p[p["source_name"].isin(FOSSIL_SOURCES)]
        if not fossil.empty:
            agg = fossil.groupby("calendar_year", as_index=False).agg(
                fossil_supply_toe=("supply_toe", "sum"),
                fossil_import_toe=("imports_toe", "sum"),
            )
            df = df.merge(agg, on="calendar_year", how="left")

    df = df.sort_values("calendar_year").reset_index(drop=True)

    # ---- derived utilisation metrics --------------------------------------
    # RE capacity & generation aggregates
    cap_cols = [f"{k}_cap_mw" for k in RE_CAP_TO_GEN]
    df["re_cap_mw"] = df[[c for c in cap_cols if c in df.columns]].sum(axis=1, min_count=1)
    gen_re_cols = list(RE_CAP_TO_GEN.values())
    df["re_gen_gwh"] = df[[c for c in gen_re_cols if c in df.columns]].sum(axis=1, min_count=1)

    fossil_gen_cols = [c for c in ("coal_gen_gwh", "gas_gen_gwh", "nuclear_gen_gwh") if c in df.columns]
    if fossil_gen_cols:
        df["thermal_gen_gwh"] = df[fossil_gen_cols].sum(axis=1, min_count=1)
    df["thermal_cap_mw"] = df["total_cap_mw"] - df["re_cap_mw"]

    # nameplate energy capability and the undelivered gap
    df["capability_gwh"] = df["total_cap_mw"] * GWH_PER_MW_YEAR
    df["undelivered_gwh"] = df["capability_gwh"] - df["total_gen_gwh"]

    # capacity / load factors (%), each NaN-safe
    df["sys_load_factor_pct"] = _safe_div(df["total_gen_gwh"], df["capability_gwh"]) * 100.0
    df["fossil_cf_pct"] = _safe_div(df["thermal_gen_gwh"], df["thermal_cap_mw"] * GWH_PER_MW_YEAR) * 100.0
    df["re_cf_pct"] = _safe_div(df["re_gen_gwh"], df["re_cap_mw"] * GWH_PER_MW_YEAR) * 100.0

    for cap_src, gen_col in RE_CAP_TO_GEN.items():
        cap_col = f"{cap_src}_cap_mw"
        if cap_col in df.columns and gen_col in df.columns:
            df[f"{cap_src.lower()}_cf_pct"] = _safe_div(df[gen_col], df[cap_col] * GWH_PER_MW_YEAR) * 100.0

    # gas self-sufficiency + shortfall (deficit derived from the same row so it
    # stays internally consistent with the self-sufficiency ratio)
    df["gas_self_suff_pct"] = _safe_div(df["gas_prod_bcf"], df["gas_cons_bcf"]) * 100.0
    df["gas_gap_bcf"] = df["gas_cons_bcf"] - df["gas_prod_bcf"]

    # T&D loss rate (% of generation)
    df["td_loss_pct"] = _safe_div(df["td_loss_gwh"], df["total_gen_gwh"]) * 100.0

    # fossil import dependence (%)
    # The warehouse records zero imported fossil quantities for recent years, so a
    # 0% reading means "no import data", not "no bottleneck". Treat recorded-zero as
    # unavailable (NaN) to avoid a misleadingly benign severity.
    imp = df.get("fossil_import_toe", pd.Series(np.nan, index=df.index))
    imp = imp.where(imp.fillna(0) > 0, np.nan)
    df["fossil_import_dep_pct"] = _safe_div(imp, df["fossil_supply_toe"]) * 100.0

    # keep only the reported analysis window
    df = df[(df["calendar_year"] >= HISTORY_START) & (df["calendar_year"] <= HISTORY_END)]
    df = df.reset_index(drop=True)
    return df


# ── 2. Severity normalisation ────────────────────────────────────────────────
def _severity_from_pct(value: float, band: tuple[float, float]) -> float:
    """Map a 'higher is better' percentage (e.g. capacity factor) to 0-100 severity.

    `band` = (worst_value -> severity 100, best_value -> severity 0).  Because
    utilisation is higher-is-better, worst < best: value at `worst` scores 100
    (fully binding), value at `best` scores 0 (no bottleneck).
    """
    v = _num(value)
    if not np.isfinite(v):
        return np.nan
    worst, best = band
    if best == worst:
        return np.nan
    s = (best - v) / (best - worst) * 100.0
    return float(np.clip(s, 0.0, 100.0))


def _severity_from_ratio(value: float, worst: float, best: float) -> float:
    """Map a 'lower is better' percentage (loss, import dependence) to 0-100 severity."""
    v = _num(value)
    if not np.isfinite(v):
        return np.nan
    if worst == best:
        return np.nan
    s = (v - best) / (worst - best) * 100.0
    return float(np.clip(s, 0.0, 100.0))


def _row_at_or_before(df: pd.DataFrame, base_year: int) -> pd.Series:
    """Latest available row up to `base_year` (data lags differ per stream)."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    sub = df[df["calendar_year"] <= base_year]
    if sub.empty:
        sub = df
    return sub.iloc[-1]


def latest_obs(df: pd.DataFrame, col: str, base_year: int) -> tuple[float, Optional[int]]:
    """Latest non-null value of `col` up to `base_year`, and the year it was read.

    Each warehouse stream reports through a different last year (generation to
    2023, T&D to 2019, gas to 2018 ...), so every metric is anchored to its own
    most recent observation rather than a single shared snapshot row.
    """
    if df is None or df.empty or col not in df.columns:
        return np.nan, None
    sub = df.loc[df["calendar_year"] <= base_year, ["calendar_year", col]].dropna()
    if sub.empty:
        sub = df[["calendar_year", col]].dropna()
    if sub.empty:
        return np.nan, None
    last = sub.iloc[-1]
    val = _num(last[col])
    yr = _num(last["calendar_year"])
    return val, (int(yr) if np.isfinite(yr) else None)


# ── 3. Bottleneck scorecard ──────────────────────────────────────────────────
def score_bottlenecks(df: pd.DataFrame, base_year: int = DEFAULT_BASE_YEAR) -> pd.DataFrame:
    """Ranked bottleneck scorecard evaluated at `base_year`.

    Returns columns:
      id, name, family ('fossil'|'renewable'|'delivery'), metric_value,
      metric_unit, severity (0-100), band ('Severe'|'Binding'|'Moderate'|'Mild'),
      reading (human string), note.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Each metric reads its own latest observation up to base_year (the streams
    # are reported with different lags), paired with the year it came from.
    obs = {
        "fossil_cf_pct":      latest_obs(df, "fossil_cf_pct", base_year),
        "gas_self_suff_pct":  latest_obs(df, "gas_self_suff_pct", base_year),
        "fossil_import_dep_pct": latest_obs(df, "fossil_import_dep_pct", base_year),
        "re_cf_pct":          latest_obs(df, "re_cf_pct", base_year),
        "solar_cf_pct":       latest_obs(df, "solar_cf_pct", base_year),
        "wind_cf_pct":        latest_obs(df, "wind_cf_pct", base_year),
        "hydel_cf_pct":       latest_obs(df, "hydel_cf_pct", base_year),
        "td_loss_pct":        latest_obs(df, "td_loss_pct", base_year),
    }

    def gv(col: str) -> float:
        return obs[col][0]

    items = [
        {
            "id": "fossil_cf",
            "name": "Thermal Fleet Under-Utilisation",
            "family": "fossil",
            "metric_value": gv("fossil_cf_pct"),
            "metric_unit": "% cap factor",
            "severity": _severity_from_pct(gv("fossil_cf_pct"), UTILISATION_BANDS["fossil_cf_pct"]),
            "note": "Coal/gas/nuclear plant that is built but not run -- locked-in "
                    "capability, typically starved of fuel or dispatched down by cost.",
        },
        {
            "id": "gas_gap",
            "name": "Domestic Gas Supply Shortfall",
            "family": "fossil",
            "metric_value": gv("gas_self_suff_pct"),
            "metric_unit": "% self-sufficient",
            "severity": _severity_from_pct(gv("gas_self_suff_pct"), (20.0, 100.0)),
            "note": "Indigenous production below consumption forces costlier LNG "
                    "imports and idles gas-fired capacity.",
        },
        {
            "id": "fossil_import",
            "name": "Fossil Import Dependence",
            "family": "fossil",
            "metric_value": gv("fossil_import_dep_pct"),
            "metric_unit": "% of fossil supply",
            "severity": _severity_from_ratio(gv("fossil_import_dep_pct"), 90.0, 10.0),
            "note": "Share of oil / gas / coal / LNG requirement met from abroad -- "
                    "exposure to price and shipping shocks.",
        },
        {
            "id": "re_cf",
            "name": "Renewable Capacity Not Converting",
            "family": "renewable",
            "metric_value": gv("re_cf_pct"),
            "metric_unit": "% cap factor",
            "severity": _severity_from_pct(gv("re_cf_pct"), UTILISATION_BANDS["re_cf_pct"]),
            "note": "Installed hydro / wind / solar / bagasse delivering well under "
                    "nameplate -- resource variability and grid-integration limits.",
        },
        {
            "id": "solar_cf",
            "name": "Solar Intermittency",
            "family": "renewable",
            "metric_value": gv("solar_cf_pct"),
            "metric_unit": "% cap factor",
            "severity": _severity_from_pct(gv("solar_cf_pct"), (6.0, 30.0)),
            "note": "Day-only, weather-dependent output; low capacity factor is "
                    "structural for PV and needs storage / firming.",
        },
        {
            "id": "wind_cf",
            "name": "Wind Variability",
            "family": "renewable",
            "metric_value": gv("wind_cf_pct"),
            "metric_unit": "% cap factor",
            "severity": _severity_from_pct(gv("wind_cf_pct"), (10.0, 45.0)),
            "note": "Resource-driven swings in wind output constrain firm supply.",
        },
        {
            "id": "hydro_cf",
            "name": "Hydro Flow / Seasonality",
            "family": "renewable",
            "metric_value": gv("hydel_cf_pct"),
            "metric_unit": "% cap factor",
            "severity": _severity_from_pct(gv("hydel_cf_pct"), (15.0, 55.0)),
            "note": "Run-of-river and reservoir output tracks water availability; "
                    "dry seasons cut delivered hydro energy.",
        },
        {
            "id": "td_loss",
            "name": "T&D Delivery Losses",
            "family": "delivery",
            "metric_value": gv("td_loss_pct"),
            "metric_unit": "% of generation",
            "severity": _severity_from_ratio(gv("td_loss_pct"), 25.0, 8.0),
            "note": "Energy generated but never reaching consumers through the grid -- "
                    "a cross-cutting supply-delivery bottleneck.",
        },
    ]

    sc = pd.DataFrame(items)
    # attach the observation year each metric was read from
    col_by_id = {
        "fossil_cf": "fossil_cf_pct", "gas_gap": "gas_self_suff_pct",
        "fossil_import": "fossil_import_dep_pct", "re_cf": "re_cf_pct",
        "solar_cf": "solar_cf_pct", "wind_cf": "wind_cf_pct",
        "hydro_cf": "hydel_cf_pct", "td_loss": "td_loss_pct",
    }
    sc["obs_year"] = [obs[col_by_id[i]][1] if i in col_by_id else None
                      for i in sc["id"]]
    sc["band"] = sc["severity"].apply(_band_label)
    sc["reading"] = sc.apply(_reading, axis=1)
    sc = sc.sort_values("severity", ascending=False, na_position="last").reset_index(drop=True)
    return sc


def _band_label(sev: float) -> str:
    if not np.isfinite(sev):
        return "n/a"
    if sev >= 66:
        return "Severe"
    if sev >= 45:
        return "Binding"
    if sev >= 25:
        return "Moderate"
    return "Mild"


def _reading(r: pd.Series) -> str:
    v = _num(r.get("metric_value", np.nan))
    if not np.isfinite(v):
        return "--"
    return f"{v:,.1f} {r.get('metric_unit', '')}".strip()


def severity_color(sev: float) -> str:
    """House palette by severity band (used by charts + page)."""
    if not np.isfinite(sev):
        return "#64748B"
    if sev >= 66:
        return "#EF4444"     # red   -- severe
    if sev >= 45:
        return "#F97316"     # orange-- binding
    if sev >= 25:
        return "#F59E0B"     # amber -- moderate
    return "#10B981"         # green -- mild


FAMILY_COLORS = {
    "fossil": "#F97316",
    "renewable": "#10B981",
    "delivery": "#00A6FB",
}


def aggregate_by_family(scorecard: pd.DataFrame) -> dict:
    """Mean severity per family (fossil / renewable / delivery), NaN-safe."""
    out = {"fossil": np.nan, "renewable": np.nan, "delivery": np.nan}
    if scorecard is None or scorecard.empty:
        return out
    for fam in out:
        s = scorecard[scorecard["family"] == fam]["severity"].dropna()
        out[fam] = float(s.mean()) if not s.empty else np.nan
    return out


def snapshot_metrics(df: pd.DataFrame, base_year: int) -> dict:
    """Key headline values for the KPI deck, each from its own latest observation.

    Returns a dict of `metric` -> value plus `metric_year` -> observation year,
    because the warehouse streams are reported with different lags.
    """
    if df is None or df.empty:
        return {}
    keys = [
        "sys_load_factor_pct", "fossil_cf_pct", "re_cf_pct",
        "gas_self_suff_pct", "gas_gap_bcf", "td_loss_pct",
        "fossil_import_dep_pct", "undelivered_gwh", "total_cap_mw",
        "total_gen_gwh", "re_cap_mw", "re_gen_gwh",
    ]
    out: dict = {}
    years: list[int] = []
    for k in keys:
        v, y = latest_obs(df, k, base_year)
        out[k] = v
        out[f"{k}_year"] = y
        if y is not None:
            years.append(y)
    out["year"] = max(years) if years else base_year
    return out
