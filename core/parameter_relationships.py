"""
core/parameter_relationships.py -- analysis engine for Question 1:

    "What have been the relationships among different parameters of energy
     over a given period of time?  What are the predicted values of these
     parameters based on the what-if analysis?"

Two halves, both solver-free and pure (raw query frames in, pandas frames out):

RELATIONSHIPS
  build_parameter_frame()  annual tidy frame of every tracked parameter
  correlation_matrix()     pairwise Pearson r over a chosen period
  pairwise_fit()           OLS line + r / R² for one parameter pair
  rolling_correlation()    stability of a pair's r across moving windows

WHAT-IF FORECAST
  Each parameter grows by   autonomy + β_gdp·gdp_growth + β_pop·pop_growth
  (minus an optional efficiency/decoupling drag in the what-if case).  The
  elasticities β come from log-log regressions on the reported history, and
  the autonomy term is back-solved so the BASELINE path reproduces the
  parameter's own historical CAGR exactly.  Moving the GDP / population /
  efficiency sliders therefore re-prices every linked parameter at once.

Presentation code must do no analytics -- everything lives here.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

HISTORY_END = 2024
DEFAULT_HORIZON = 2035
DEFAULT_GDP_GROWTH = 4.0      # %/yr what-if
DEFAULT_POP_GROWTH = 1.9      # %/yr what-if
DEFAULT_EFFICIENCY = 0.0      # %/yr decoupling drag (what-if only)

MIN_PAIR_OBS = 6              # correlations below this are blanked
MIN_FIT_OBS = 8               # elasticity regressions need at least this many
CAGR_WINDOW = 10              # years of history used for the growth anchor
GROWTH_CLAMP = (-0.15, 0.20)  # sane bounds on annual growth rates
BETA_CLAMP = (0.0, 2.5)       # elasticities: no negative coupling
FALLBACK_B_GDP = 0.8          # used when a log-log fit is impossible
FALLBACK_B_POP = 1.0

# key -> (label, unit family, storage unit, forecastable?)
#   family "none"  -> dimensionless, never unit-converted
#   gdp / population are pre-scaled to USD bn / millions in the frame
PARAMETERS: Dict[str, dict] = {
    "gdp":              {"label": "GDP", "family": "economic", "unit": "USD bn", "forecast": True},
    "population":       {"label": "Population", "family": "economic", "unit": "M people", "forecast": True},
    "gdp_growth":       {"label": "GDP Growth Rate", "family": "none", "unit": "%/yr", "forecast": False},
    "demand":           {"label": "Electricity Demand", "family": "electricity", "unit": "GWh", "forecast": True},
    "generation":       {"label": "Electricity Generation", "family": "electricity", "unit": "GWh", "forecast": True},
    "consumption":      {"label": "Electricity Consumption", "family": "electricity", "unit": "GWh", "forecast": True},
    "capacity":         {"label": "Installed Capacity", "family": "power", "unit": "MW", "forecast": True},
    "elec_imports":     {"label": "Electricity Imports", "family": "electricity", "unit": "GWh", "forecast": True},
    "td_losses":        {"label": "T&D Losses", "family": "electricity", "unit": "GWh", "forecast": True},
    "gas_production":   {"label": "Gas Production", "family": "gas", "unit": "BCF", "forecast": True},
    "gas_consumption":  {"label": "Gas Consumption", "family": "gas", "unit": "BCF", "forecast": True},
    "lng_imports":      {"label": "LNG Imports", "family": "gas", "unit": "BCF", "forecast": True},
    "co2":              {"label": "CO₂ Emissions", "family": "emission", "unit": "t", "forecast": True},
    "primary_supply":   {"label": "Primary Energy Supply", "family": "energy", "unit": "TOE", "forecast": True},
    "final_consumption": {"label": "Final Energy Consumption", "family": "energy", "unit": "TOE", "forecast": True},
    "re_share":         {"label": "Renewable Share of Generation", "family": "none", "unit": "%", "forecast": False},
    "elec_intensity":   {"label": "Electricity Intensity", "family": "none", "unit": "GWh/USD bn", "forecast": False},
    "pc_demand":        {"label": "Per-Capita Electricity Demand", "family": "none", "unit": "kWh/person", "forecast": False},
    "gas_self_suff":    {"label": "Gas Self-Sufficiency", "family": "none", "unit": "%", "forecast": False},
}

FORECAST_KEYS = [k for k, m in PARAMETERS.items() if m["forecast"]]
CORR_KEYS = list(PARAMETERS.keys())

# Ratios that are computed from other parameters on this page, so a link
# involving one is partly self-referential (e.g. per-capita demand IS demand
# divided by population).  They stay in the matrix, ranking and distribution,
# but are never allowed to become the headline "strongest relationship".
DERIVED_KEYS = {"pc_demand", "elec_intensity", "re_share", "gas_self_suff"}

GEN_COLS = {
    "Solar": "gen_solar_gwh", "Wind": "gen_wind_gwh", "Hydro": "gen_hydro_gwh",
    "Other RE": "gen_other_renewables_gwh", "Coal": "gen_coal_gwh",
    "Gas": "gen_gas_gwh", "Nuclear": "gen_nuclear_gwh",
}
RE_COLS = ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
           "gen_other_renewables_gwh"]


# ══════════════════════════ parameter frame ══════════════════════════════════

def _clean(df: Optional[pd.DataFrame], cols: List[str]) -> pd.DataFrame:
    """Numeric-ise calendar_year + the wanted columns; drop year-less rows."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["calendar_year"] + cols)
    d = df.copy()
    d["calendar_year"] = pd.to_numeric(d["calendar_year"], errors="coerce")
    d = d.dropna(subset=["calendar_year"]).astype({"calendar_year": int})
    for c in cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        else:
            d[c] = np.nan
    return d[["calendar_year"] + cols].sort_values("calendar_year")


def build_parameter_frame(
    econ_df: Optional[pd.DataFrame] = None,
    re_df: Optional[pd.DataFrame] = None,
    gen_df: Optional[pd.DataFrame] = None,
    td_df: Optional[pd.DataFrame] = None,
    gas_df: Optional[pd.DataFrame] = None,
    lng_df: Optional[pd.DataFrame] = None,
    overview_df: Optional[pd.DataFrame] = None,
    co2_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """One annual row per calendar year, one column per tracked parameter,
    all in the storage units declared in PARAMETERS."""
    parts: List[pd.DataFrame] = []

    # The dedicated emissions table (fact_co2_emissions, OWID totals) is the
    # authoritative CO2 series; the economic frame's co2 column is only a
    # fallback for years the country table does not cover.
    c = _clean(co2_df, ["co2_emissions_t"])
    if not c.empty:
        parts.append(c.rename(columns={"co2_emissions_t": "co2"})[
            ["calendar_year", "co2"]])

    e = _clean(econ_df, ["gdp_current_usd", "gdp_growth_pct", "population",
                         "co2_emissions_tonnes"])
    if not e.empty:
        e = e.assign(
            gdp=e["gdp_current_usd"] / 1e9,
            population_m=e["population"] / 1e6,
            gdp_growth=e["gdp_growth_pct"],
            co2=e["co2_emissions_tonnes"],
        )[["calendar_year", "gdp", "population_m", "gdp_growth", "co2"]]
        if not c.empty:
            e = e.drop(columns="co2")
        parts.append(e)

    r = _clean(re_df, ["demand_gwh"] + list(GEN_COLS.values()))
    if not r.empty:
        gen_total = r[list(GEN_COLS.values())].sum(axis=1, min_count=1)
        re_gen = r[RE_COLS].sum(axis=1, min_count=1)
        r = r.assign(
            demand=r["demand_gwh"],
            re_share=np.where(gen_total > 0, re_gen / gen_total * 100.0, np.nan),
        )[["calendar_year", "demand", "re_share"]]
        parts.append(r)

    g = _clean(gen_df, ["installed_capacity_mw", "generation_gwh",
                        "imports_gwh", "consumption_gwh"])
    if not g.empty:
        g = g.rename(columns={"installed_capacity_mw": "capacity",
                              "generation_gwh": "generation",
                              "imports_gwh": "elec_imports",
                              "consumption_gwh": "consumption"})
        parts.append(g[["calendar_year", "capacity", "generation",
                        "elec_imports", "consumption"]])

    t = _clean(td_df, ["td_losses_gwh"])
    if not t.empty:
        parts.append(t.rename(columns={"td_losses_gwh": "td_losses"}))

    n = _clean(gas_df, ["production_bcf", "consumption_bcf"])
    if not n.empty:
        n = n.assign(
            gas_production=n["production_bcf"],
            gas_consumption=n["consumption_bcf"],
            gas_self_suff=np.where(n["consumption_bcf"] > 0,
                                   n["production_bcf"] / n["consumption_bcf"] * 100.0,
                                   np.nan),
        )[["calendar_year", "gas_production", "gas_consumption", "gas_self_suff"]]
        parts.append(n)

    l = _clean(lng_df, ["imports_bcf"])
    if not l.empty:
        parts.append(l.rename(columns={"imports_bcf": "lng_imports"}))

    o = _clean(overview_df, ["total_primary_supply_toe", "total_final_consumption_toe"])
    if not o.empty:
        o = o.rename(columns={"total_primary_supply_toe": "primary_supply",
                              "total_final_consumption_toe": "final_consumption"})
        parts.append(o[["calendar_year", "primary_supply", "final_consumption"]])

    if not parts:
        return pd.DataFrame(columns=["calendar_year"] + CORR_KEYS)

    df = parts[0]
    for p in parts[1:]:
        df = pd.merge(df, p, on="calendar_year", how="outer")
    df = df.sort_values("calendar_year").reset_index(drop=True)

    # cross-frame derived ratios
    df["elec_intensity"] = np.where(df["gdp"] > 0,
                                    df["demand"] / df["gdp"], np.nan)
    df["pc_demand"] = np.where(df["population_m"] > 0,
                               df["demand"] / df["population_m"], np.nan)
    # 'population' is the frame column name expected downstream
    df["population"] = df["population_m"]
    return df


# ══════════════════════════ relationships ════════════════════════════════════

def _window(df: pd.DataFrame, y0: int, y1: int) -> pd.DataFrame:
    return df[(df["calendar_year"] >= y0) & (df["calendar_year"] <= y1)]


def correlation_matrix(df: pd.DataFrame, keys: List[str],
                       y0: int, y1: int) -> pd.DataFrame:
    """Pairwise Pearson r on the shared non-missing rows of each pair;
    pairs with too few joint observations are NaN."""
    d = _window(df, y0, y1)
    n = len(keys)
    mat = np.full((n, n), np.nan)
    for i, a in enumerate(keys):
        for j, b in enumerate(keys):
            if i >= j or a not in d or b not in d:
                continue
            pair = d[[a, b]].dropna()
            pair = pair[(pair != 0).any(axis=1)]
            if len(pair) < MIN_PAIR_OBS or pair[a].nunique() < 2 \
                    or pair[b].nunique() < 2:
                continue
            mat[i, j] = mat[j, i] = float(np.corrcoef(pair[a], pair[b])[0, 1])
    return pd.DataFrame(mat, index=keys, columns=keys)


def strongest_pair(corr: pd.DataFrame, ignore: Optional[set] = None) -> Optional[tuple]:
    """(key_a, key_b, r) of the largest |r| cell in the matrix.

    Cells pairing a key listed in `ignore` are skipped, so a derived ratio
    can never be picked as the headline relationship.
    """
    if corr is None or corr.empty:
        return None
    ignore = ignore or set()
    c = corr.where(~np.eye(len(corr), dtype=bool))
    if ignore:
        drop = [k for k in c.index if k in ignore]
        c = c.drop(index=drop, columns=drop)
    if c.notna().sum().sum() == 0:
        return None
    abs_c = c.abs()
    a, b = np.unravel_index(np.nanargmax(abs_c.to_numpy()), abs_c.shape)
    return c.index[a], c.columns[b], float(c.iloc[a, b])


def pair_samples(corr: pd.DataFrame) -> pd.DataFrame:
    """Every computable upper-triangle pair as (param_a, param_b, r),
    sorted by |r| descending -- feeds the ranking and distribution charts."""
    rows = []
    keys = list(corr.index)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            v = corr.loc[a, b]
            if pd.notna(v):
                rows.append({"param_a": a, "param_b": b, "r": float(v)})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_r"] = out["r"].abs()
        out = out.sort_values("abs_r", ascending=False).reset_index(drop=True)
    return out


def pairwise_fit(df: pd.DataFrame, x_key: str, y_key: str,
                 y0: int, y1: int) -> dict:
    """OLS y = a + b·x over the period, plus r / R² / n and the scatter points
    (columns ordered [x_key, y_key, calendar_year])."""
    d = _window(df, y0, y1)[[x_key, y_key, "calendar_year"]].dropna()
    d = d[(d[x_key] != 0) | (d[y_key] != 0)]
    out = {"points": d, "slope": np.nan, "intercept": np.nan,
           "r": np.nan, "r2": np.nan, "n": int(len(d)),
           "x_range": (np.nan, np.nan)}
    if len(d) < MIN_PAIR_OBS:
        return out
    x, y = d[x_key].to_numpy(float), d[y_key].to_numpy(float)
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    r = float(np.corrcoef(x, y)[0, 1])
    out.update(slope=float(b), intercept=float(a), r=r, r2=r * r,
               x_range=(float(x.min()), float(x.max())))
    return out


def rolling_correlation(df: pd.DataFrame, x_key: str, y_key: str,
                        window: int = 7, y0: Optional[int] = None,
                        y1: Optional[int] = None) -> pd.DataFrame:
    """Pearson r of one pair computed over a sliding year window.

    The slide stays inside the caller's selected period when y0/y1 are given,
    so this chart answers the same question as the rest of the page.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["year", "r"])
    lo = int(df["calendar_year"].min()) if y0 is None else int(y0)
    hi = int(df["calendar_year"].max()) if y1 is None else int(y1)
    d = _window(df, lo, hi)
    years = [int(y) for y in d["calendar_year"].tolist()]
    rows = []
    for end in years[window - 1:]:
        seg = d[(d["calendar_year"] > end - window) &
                (d["calendar_year"] <= end)][[x_key, y_key]].dropna()
        if len(seg) < max(4, int(window * 0.6)) or seg[x_key].nunique() < 2 \
                or seg[y_key].nunique() < 2:
            continue
        r = float(np.corrcoef(seg[x_key], seg[y_key])[0, 1])
        rows.append({"year": end, "r": r})
    return pd.DataFrame(rows)


# ══════════════════════════ what-if forecasting ══════════════════════════════

def _cagr(series: pd.Series, years: pd.Series) -> float:
    """Compound annual growth over the last CAGR_WINDOW observations."""
    s = pd.DataFrame({"v": series, "y": years}).dropna()
    s = s[s["v"] > 0].sort_values("y")
    if len(s) < 3:
        return 0.0
    s = s.tail(CAGR_WINDOW + 1)
    n = float(s["y"].iloc[-1] - s["y"].iloc[0])
    if n <= 0:
        return 0.0
    return float((s["v"].iloc[-1] / s["v"].iloc[0]) ** (1.0 / n) - 1.0)


def _loglog_beta(df: pd.DataFrame, target: str, driver: str) -> float:
    """Elasticity d ln(target) / d ln(driver) via single-variable OLS."""
    d = df[[target, driver]].dropna()
    d = d[(d[target] > 0) & (d[driver] > 0)]
    if len(d) < MIN_FIT_OBS:
        return np.nan
    lx, ly = np.log(d[driver].to_numpy(float)), np.log(d[target].to_numpy(float))
    if np.std(lx) < 1e-9:
        return np.nan
    b = float(np.polyfit(lx, ly, 1)[0])
    return float(np.clip(b, *BETA_CLAMP))


def _last(df: pd.DataFrame, key: str):
    s = df[["calendar_year", key]].dropna().sort_values("calendar_year")
    if s.empty:
        return None, np.nan, np.nan
    return int(s["calendar_year"].iloc[-1]), float(s[key].iloc[-1]), s


def forecast_parameters(
    df: pd.DataFrame,
    keys: Optional[List[str]] = None,
    horizon: int = DEFAULT_HORIZON,
    gdp_growth_pct: float = DEFAULT_GDP_GROWTH,
    pop_growth_pct: float = DEFAULT_POP_GROWTH,
    efficiency_pct: float = DEFAULT_EFFICIENCY,
) -> pd.DataFrame:
    """Baseline vs what-if horizon projection per parameter.

    growth_baseline = own historical CAGR
    growth_whatif   = autonomy + β_gdp·gdp_g + β_pop·pop_g − efficiency
    where autonomy = CAGR − β_gdp·gdp_hist − β_pop·pop_hist, so the baseline
    is untouched and the what-if delta flows purely from the three sliders.
    """
    keys = [k for k in (keys or FORECAST_KEYS) if k in df.columns]
    if df.empty:
        return pd.DataFrame()

    gdp_hist = _cagr(df["gdp"], df["calendar_year"]) if "gdp" in df else 0.0
    pop_hist = _cagr(df["population"], df["calendar_year"]) if "population" in df else 0.0

    rows = []
    for key in keys:
        last_year, last_val, _ = _last(df, key)
        if last_year is None or not np.isfinite(last_val) or last_val <= 0:
            continue
        c = _cagr(df[key], df["calendar_year"])

        if key == "gdp":                      # drivers set themselves directly;
            b_gdp, b_pop = 1.0, 0.0            # no collinear pop-feedback
        elif key == "population":
            b_gdp, b_pop = 0.0, 1.0
        else:
            b_gdp = _loglog_beta(df, key, "gdp")
            b_pop = _loglog_beta(df, key, "population")
            if not np.isfinite(b_gdp):
                b_gdp = FALLBACK_B_GDP
            if not np.isfinite(b_pop):
                b_pop = FALLBACK_B_POP

        autonomy = c - b_gdp * gdp_hist - b_pop * pop_hist
        g_base = float(np.clip(c, *GROWTH_CLAMP))
        g_what = float(np.clip(autonomy + b_gdp * gdp_growth_pct / 100.0
                               + b_pop * pop_growth_pct / 100.0
                               - efficiency_pct / 100.0, *GROWTH_CLAMP))

        span = max(0, horizon - last_year)
        base_val = last_val * (1.0 + g_base) ** span
        what_val = last_val * (1.0 + g_what) ** span
        rows.append({
            "key": key,
            "label": PARAMETERS[key]["label"],
            "family": PARAMETERS[key]["family"],
            "unit": PARAMETERS[key]["unit"],
            "last_year": last_year,
            "last_value": last_val,
            "cagr_pct": g_base * 100.0,   # clamped growth actually used for baseline
            "b_gdp": b_gdp,
            "b_pop": b_pop,
            "baseline_value": base_val,
            "whatif_value": what_val,
            "delta_pct": (what_val / base_val - 1.0) * 100.0 if base_val > 0 else 0.0,
        })
    return pd.DataFrame(rows)


def forecast_path(df: pd.DataFrame, key: str, fc_row: pd.Series,
                  horizon: int) -> pd.DataFrame:
    """Year-by-year baseline vs what-if path for one parameter (history is
    read from the frame; the two projections continue from its last value)."""
    hist = df[["calendar_year", key]].dropna().sort_values("calendar_year")
    rows = [{"year": int(y), "value": float(v), "series": "History"}
            for y, v in zip(hist["calendar_year"], hist[key])]
    start, base0 = int(fc_row["last_year"]), float(fc_row["last_value"])
    g_base = (1.0 + float(fc_row["cagr_pct"]) / 100.0)
    # what-if growth is embedded in the horizon value; interpolate geometrically
    span = max(1, horizon - start)
    g_what = (float(fc_row["whatif_value"]) / base0) ** (1.0 / span) if base0 > 0 else 1.0
    for t in range(start + 1, horizon + 1):
        n = t - start
        rows.append({"year": t, "value": base0 * g_base ** n, "series": "Baseline"})
        rows.append({"year": t, "value": base0 * g_what ** n, "series": "What-if"})
    return pd.DataFrame(rows)


# ══════════════════════════ master builder ═══════════════════════════════════

def build_relationship_data(
    econ_df=None, re_df=None, gen_df=None, td_df=None,
    gas_df=None, lng_df=None, overview_df=None, co2_df=None,
    period: tuple = (1999, HISTORY_END),
    pair_x: str = "gdp", pair_y: str = "demand",
    target_key: str = "demand",
    horizon: int = DEFAULT_HORIZON,
    gdp_growth_pct: float = DEFAULT_GDP_GROWTH,
    pop_growth_pct: float = DEFAULT_POP_GROWTH,
    efficiency_pct: float = DEFAULT_EFFICIENCY,
    roll_window: int = 7,
) -> dict:
    """Everything the Q1 dashboard renders, from raw query frames."""
    df = build_parameter_frame(econ_df, re_df, gen_df, td_df,
                               gas_df, lng_df, overview_df, co2_df)
    y0 = int(min(period)) if period else int(df["calendar_year"].min())
    y1 = int(max(period)) if period else int(df["calendar_year"].max())

    corr = correlation_matrix(df, CORR_KEYS, y0, y1)
    fit = pairwise_fit(df, pair_x, pair_y, y0, y1)
    roll = rolling_correlation(df, pair_x, pair_y, roll_window, y0, y1) \
        if pair_x in df and pair_y in df else pd.DataFrame()
    fc = forecast_parameters(df, None, horizon, gdp_growth_pct,
                             pop_growth_pct, efficiency_pct)
    path = pd.DataFrame()
    if not fc.empty and target_key in set(fc["key"]):
        row = fc[fc["key"] == target_key].iloc[0]
        path = forecast_path(df, target_key, row, horizon)

    return {
        "frame": df,
        "corr": corr,
        "strongest": strongest_pair(corr, DERIVED_KEYS),
        "pairs": pair_samples(corr),
        "fit": fit,
        "rolling": roll,
        "forecasts": fc,
        "path": path,
        "target_key": target_key,
        "pair": (pair_x, pair_y),
        "period": (y0, y1),
        "horizon": horizon,
        "inputs": {"gdp_growth_pct": gdp_growth_pct,
                   "pop_growth_pct": pop_growth_pct,
                   "efficiency_pct": efficiency_pct},
    }
