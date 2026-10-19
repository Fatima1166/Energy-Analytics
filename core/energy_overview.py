"""
core/energy_overview.py -- engine for the landing "Energy Overview" home
dashboard: headline snapshot values, supply/demand history, the latest-year
primary fuel mix and the CO2 record.

Pure pandas/numpy -- no Streamlit, no MySQL.  The page fetches the frames via
config.database.run_query and passes them in.  All values are returned in the
base units documented in core/units.py (TOE, GWh, tonnes); display conversion
happens at render time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _year_frame(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """One row per calendar_year, sorted, NaN-dropped on the wanted cols."""
    if df is None or df.empty or "calendar_year" not in df.columns:
        return pd.DataFrame()
    keep = ["calendar_year"] + [c for c in cols if c in df.columns]
    out = df[keep].copy()
    out["calendar_year"] = pd.to_numeric(out["calendar_year"], errors="coerce")
    for c in keep[1:]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["calendar_year"]).drop_duplicates("calendar_year")
    return out.sort_values("calendar_year").reset_index(drop=True)


def supply_demand_history(overview_df: pd.DataFrame) -> pd.DataFrame:
    """year, total_primary_supply_toe, total_final_consumption_toe, gap_toe."""
    h = _year_frame(
        overview_df,
        ["total_primary_supply_toe", "total_final_consumption_toe"])
    if h.empty:
        return pd.DataFrame()
    h["gap_toe"] = h["total_primary_supply_toe"] - h["total_final_consumption_toe"]
    return h.dropna(subset=["total_primary_supply_toe",
                            "total_final_consumption_toe"]).reset_index(drop=True)


def co2_history(econ_df: pd.DataFrame) -> pd.DataFrame:
    """year + co2_emissions_tonnes for every reported year."""
    h = _year_frame(econ_df, ["co2_emissions_tonnes"])
    if h.empty:
        return pd.DataFrame()
    return h.dropna(subset=["co2_emissions_tonnes"]).reset_index(drop=True)


def generation_history(gen_df: pd.DataFrame) -> pd.DataFrame:
    """year + generation_gwh for every reported year."""
    h = _year_frame(gen_df, ["generation_gwh"])
    if h.empty:
        return pd.DataFrame()
    return h.dropna(subset=["generation_gwh"]).reset_index(drop=True)


def fuel_mix_latest(ps_df: pd.DataFrame) -> pd.DataFrame:
    """Latest year with source detail: (source_name, supply_toe, share_pct),
    ranked by size.  Sources reporting zero/NaN supply for that year are cut."""
    if ps_df is None or ps_df.empty:
        return pd.DataFrame()
    d = ps_df.copy()
    d["calendar_year"] = pd.to_numeric(d["calendar_year"], errors="coerce")
    d["supply_toe"] = pd.to_numeric(d["supply_toe"], errors="coerce")
    d = d.dropna(subset=["calendar_year", "supply_toe"])
    if d.empty:
        return pd.DataFrame()
    last_year = int(d["calendar_year"].max())
    mix = (d[d["calendar_year"] == last_year]
           .groupby("source_name", as_index=False)["supply_toe"].sum())
    mix = mix[mix["supply_toe"] > 0].sort_values(
        "supply_toe", ascending=False).reset_index(drop=True)
    if mix.empty:
        return mix
    total = mix["supply_toe"].sum()
    mix["share_pct"] = mix["supply_toe"] / total * 100.0
    mix["calendar_year"] = last_year
    return mix


def headline_snapshot(overview_df, gen_df, re_df, econ_df) -> dict:
    """Latest reported values (+ a decade-earlier twin) for the KPI strip.

    Keys: year, supply_toe, demand_toe, generation_gwh, co2_t, re_share_pct
    and *_then counterparts with the year they belong to.
    """
    sd = supply_demand_history(overview_df)
    g = _year_frame(gen_df, ["generation_gwh"])
    c = co2_history(econ_df)
    re = _year_frame(re_df, ["gen_hydro_gwh", "gen_solar_gwh", "gen_wind_gwh",
                             "gen_other_renewables_gwh", "gen_coal_gwh",
                             "gen_gas_gwh", "gen_nuclear_gwh"])

    def _pick(df, col):
        """(year, now, then) for the latest non-NaN row of `col`."""
        if df.empty or col not in df.columns:
            return (np.nan, np.nan, np.nan, None)
        s = df[["calendar_year", col]].dropna()
        if s.empty:
            return (np.nan, np.nan, np.nan, None)
        yr, now = int(s["calendar_year"].iloc[-1]), float(s[col].iloc[-1])
        before = s[s["calendar_year"] <= yr - 10]
        then = float(before[col].iloc[-1]) if not before.empty else np.nan
        then_yr = int(before["calendar_year"].iloc[-1]) if not before.empty else None
        return yr, now, then, then_yr

    snap: dict = {}
    yr, snap["supply_toe"], snap["supply_then"], snap["supply_then_year"] = _pick(
        sd, "total_primary_supply_toe")
    snap["year"] = yr
    _, snap["demand_toe"], snap["demand_then"], snap["demand_then_year"] = _pick(
        sd, "total_final_consumption_toe")
    _, snap["generation_gwh"], snap["generation_then"], snap["generation_then_year"] = _pick(
        g, "generation_gwh")
    snap["co2_year"], snap["co2_t"], snap["co2_then"], snap["co2_then_year"] = _pick(
        c, "co2_emissions_tonnes")

    # renewable share of the generation mix, latest year with RE columns
    snap["re_share_pct"] = np.nan
    snap["re_share_then"] = np.nan
    snap["re_share_year"] = None
    if not re.empty:
        re_cols = [x for x in ["gen_hydro_gwh", "gen_solar_gwh", "gen_wind_gwh",
                               "gen_other_renewables_gwh", "gen_coal_gwh",
                               "gen_gas_gwh", "gen_nuclear_gwh"]
                   if x in re.columns]
        re_cols_h = [x for x in re_cols if "renewables" in x or x in
                     ("gen_hydro_gwh", "gen_solar_gwh", "gen_wind_gwh")]
        total = re[re_cols].sum(axis=1, min_count=1)
        share = re[re_cols_h].sum(axis=1, min_count=0) / total * 100.0
        s = pd.DataFrame({"calendar_year": re["calendar_year"],
                          "share": share}).dropna()
        if not s.empty:
            yr2 = int(s["calendar_year"].iloc[-1])
            snap["re_share_pct"] = float(s["share"].iloc[-1])
            snap["re_share_year"] = yr2
            before = s[s["calendar_year"] <= yr2 - 10]
            snap["re_share_then"] = float(before["share"].iloc[-1]) \
                if not before.empty else np.nan
    return snap


def record_counts(hist_sd, hist_co2, mix) -> dict:
    """Small stats for the hero chips: coverage of the warehouse."""
    years = set()
    for df in (hist_sd, hist_co2):
        if df is not None and not df.empty:
            years |= set(df["calendar_year"].dropna().astype(int))
    return {
        "n_years": len(years),
        "first_year": min(years) if years else None,
        "last_year": max(years) if years else None,
        "n_sources": 0 if mix is None or mix.empty else len(mix),
    }
