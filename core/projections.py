"""
core/projections.py -- scenario projection engine.

Works in the storage base units (GWh, MW, t CO2, Million USD); conversion to a
display unit happens at render time via core.units.
Emission factors are tCO2/MWh, so CO2_t = gen_GWh * 1000 * emission_factor.
"""

from __future__ import annotations

import math

import pandas as pd

from config.settings import SCENARIOS, EMISSION_FACTORS, LNG_SAVING_PER_GAS_TWH_MUSD

MWH_PER_GWH = 1000.0
LNG_SAVING_PER_GAS_GWH_MUSD = LNG_SAVING_PER_GAS_TWH_MUSD / 1000.0


def _num(value) -> float:
    """Safe float cast: None / NaN / '' all become 0.0."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if out != out else out          # NaN check without numpy


def _read(value) -> float:
    """History reading: a number the source wrote, else NaN.

    A NULL cell means the year was never reported.  Turning it into 0.0 would
    print "solar generated nothing in 1999", which is a claim the record does
    not make -- 0 is a reading, absence is not.
    """
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if out == out else float("nan")


def _sum_known(values) -> float:
    """Sum the readings that exist; NaN when none of them do."""
    known = [v for v in values if not math.isnan(v)]
    return float(sum(known)) if known else float("nan")


def _last_known(rows: list, key: str):
    """Last history row that reported `key`, with the year that reported it."""
    for r in reversed(rows):
        v = r.get(key)
        if v is not None and not math.isnan(v):
            return float(v), int(r["calendar_year"])
    return float("nan"), 0


def _co2_t(coal_gwh: float, gas_gwh: float, ef: dict) -> float:
    """tCO2 from coal + gas generation expressed in GWh."""
    return (coal_gwh * ef.get("coal", 0.0) + gas_gwh * ef.get("gas", 0.0)) * MWH_PER_GWH


def project_renewable(
    df: pd.DataFrame,
    scenario: str = "Accelerated",
    custom_growth: float = None,
    end_year: int = 2035,
    demand_growth: float = 2.5,
    emission_factors: dict = None,
) -> pd.DataFrame:
    """
    Project renewable and fossil generation from the last historical year
    (FY2025-26 for generation in the current dump) to `end_year`. Returns both Actual and Projected rows, all in base
    units: generation in GWh, capacity in MW, CO2 in tonnes, savings in M USD.
    """
    ef = emission_factors if emission_factors else EMISSION_FACTORS
    df_sorted = df.copy().sort_values("calendar_year")

    last = df_sorted.iloc[-1]
    last_year = int(last["calendar_year"])

    # ---------------- Historical rows (base units) ----------------
    # A column the whole table leaves NULL (other renewables) is not a source we
    # can require; it is dropped from the "which parts should be here" test
    # first, so only genuinely partly-reported years get blanked.
    present_cols = {c for c in ("gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
                                 "gen_other_renewables_gwh", "gen_coal_gwh",
                                 "gen_gas_gwh", "gen_nuclear_gwh")
                    if c in df_sorted.columns
                    and pd.to_numeric(df_sorted[c], errors="coerce").notna().any()}
    hist_rows = []
    for _, r in df_sorted.iterrows():
        sol = _read(r.get("gen_solar_gwh"))
        wnd = _read(r.get("gen_wind_gwh"))
        hyd = _read(r.get("gen_hydro_gwh"))
        oth = _read(r.get("gen_other_renewables_gwh"))
        col = _read(r.get("gen_coal_gwh"))
        gas = _read(r.get("gen_gas_gwh"))
        nuc = _read(r.get("gen_nuclear_gwh"))
        dem = _read(r.get("demand_gwh"))
        cap = _read(r.get("capacity_mw"))
        re_tot = _sum_known([sol, wnd, hyd, oth])
        tot_gen = _sum_known([sol, wnd, hyd, oth, col, gas, nuc])
        # Only the sources this table actually reports have to be present.
        read = {"solar_gwh": sol, "wind_gwh": wnd, "hydro_gwh": hyd,
                "other_gwh": oth, "coal_gwh": col, "gas_gwh": gas,
                "nuclear_gwh": nuc}
        parts_ok = all(not math.isnan(read[k])
                       for k, c in (("solar_gwh", "gen_solar_gwh"),
                                    ("wind_gwh", "gen_wind_gwh"),
                                    ("hydro_gwh", "gen_hydro_gwh"),
                                    ("other_gwh", "gen_other_renewables_gwh"),
                                    ("coal_gwh", "gen_coal_gwh"),
                                    ("gas_gwh", "gen_gas_gwh"),
                                    ("nuclear_gwh", "gen_nuclear_gwh"))
                       if c in present_cols)
        complete = parts_ok and not math.isnan(dem)

        hist_rows.append({
            "calendar_year": int(r["calendar_year"]),
            "solar_gwh": sol,
            "wind_gwh": wnd,
            "hydro_gwh": hyd,
            "other_gwh": oth,
            "coal_gwh": col,
            "gas_gwh": gas,
            "nuclear_gwh": nuc,
            "demand_gwh": dem,
            "re_gwh": re_tot,
            "fossil_gwh": _sum_known([col, gas]),
            "total_gen_gwh": tot_gen,
            "re_share_pct": round(re_tot / tot_gen * 100, 2)
            if tot_gen > 0 else float("nan"),
            "capacity_mw": cap,
            "co2_t": round(_co2_t(col, gas, ef), 2),
            "fossil_avoided_gwh": 0.0,
            "co2_avoided_t": 0.0,
            "lng_savings_musd": 0.0,
            # "Actual" is reserved for a year that reported everything it is
            # asked to show; an unreported year is tagged "Missing" so charts
            # skip it instead of drawing a generated zero.
            "data_type": "Actual" if complete else "Missing",
        })

    if not hist_rows:
        return pd.DataFrame()

    # ---------------- Growth configuration ----------------
    sc_conf = SCENARIOS.get(scenario, SCENARIOS["Accelerated"])
    g_solar = custom_growth if custom_growth is not None else sc_conf["solar"]
    g_wind = custom_growth if custom_growth is not None else sc_conf["wind"]
    g_hydro = sc_conf.get("hydro", 2.0)
    g_other = sc_conf.get("other", 2.0)

    # Each trajectory starts from the last year that genuinely reported the
    # number, and the year travels with it -- an unreported 2024 does not turn
    # into a 2024 zero that the forecast then grows.
    base_solar, _ = _last_known(hist_rows, "solar_gwh")
    base_wind, _ = _last_known(hist_rows, "wind_gwh")
    base_hydro, _ = _last_known(hist_rows, "hydro_gwh")
    base_other = 0.0
    base_nuc, _ = _last_known(hist_rows, "nuclear_gwh")
    base_dem, base_dem_year = _last_known(hist_rows, "demand_gwh")
    base_cap, _ = _last_known(hist_rows, "capacity_mw")
    base_re_cap_ref = _sum_known([base_solar, base_wind, base_hydro])
    n_base = max(last_year - base_dem_year, 0)

    # ---------------- Projected rows ----------------
    proj_rows = []
    for yr in range(last_year + 1, end_year + 1):
        n = yr - last_year

        sol = base_solar * ((1 + g_solar / 100.0) ** n)
        wnd = base_wind * ((1 + g_wind / 100.0) ** n)
        hyd = base_hydro * ((1 + g_hydro / 100.0) ** n)
        oth = base_other * ((1 + g_other / 100.0) ** n)
        re_tot = sol + wnd + hyd + oth

        dem = base_dem * ((1 + demand_growth / 100.0) ** (n + n_base))
        nuc = base_nuc * ((1 + 0.015) ** n)

        # status-quo baseline used for the "avoided" comparison
        base_sol_n = base_solar * ((1 + 0.02) ** n)
        base_wnd_n = base_wind * ((1 + 0.02) ** n)
        base_hyd_n = base_hydro * ((1 + 0.01) ** n)
        base_re_n = base_sol_n + base_wnd_n + base_hyd_n
        base_fossil_n = max(dem - base_re_n - nuc, 0)
        base_coal_n = base_fossil_n * 0.356
        base_gas_n = base_fossil_n * 0.644

        fossil = max(dem - re_tot - nuc, 0.0)
        coal = fossil * 0.356
        gas = fossil * 0.644
        tot_gen = re_tot + fossil + nuc
        re_share = round((re_tot / tot_gen * 100), 2) if tot_gen > 0 else 0.0

        fossil_avoided = max(base_fossil_n - fossil, 0.0)
        coal_avoided = max(base_coal_n - coal, 0.0)
        gas_avoided = max(base_gas_n - gas, 0.0)

        co2_t = round(_co2_t(coal, gas, ef), 2)
        co2_avoided_t = round(_co2_t(coal_avoided, gas_avoided, ef), 2)
        lng_savings = round(gas_avoided * LNG_SAVING_PER_GAS_GWH_MUSD, 4)

        re_cap = (base_cap * (re_tot / base_re_cap_ref)
                  if base_re_cap_ref > 0 else base_cap)

        proj_rows.append({
            "calendar_year": yr,
            "solar_gwh": round(sol, 2),
            "wind_gwh": round(wnd, 2),
            "hydro_gwh": round(hyd, 2),
            "other_gwh": round(oth, 2),
            "coal_gwh": round(coal, 2),
            "gas_gwh": round(gas, 2),
            "nuclear_gwh": round(nuc, 2),
            "demand_gwh": round(dem, 2),
            "re_gwh": round(re_tot, 2),
            "fossil_gwh": round(fossil, 2),
            "total_gen_gwh": round(tot_gen, 2),
            "re_share_pct": re_share,
            "capacity_mw": round(re_cap, 2),
            "co2_t": co2_t,
            "fossil_avoided_gwh": round(fossil_avoided, 2),
            "co2_avoided_t": co2_avoided_t,
            "lng_savings_musd": lng_savings,
            "data_type": "Projected",
        })

    return pd.DataFrame(hist_rows + proj_rows)


def compare_all_scenarios(
    re_df: pd.DataFrame,
    target_year: int = 2035,
    custom_growth_map: dict = None,
    emission_factors: dict = None,
) -> pd.DataFrame:
    """
    Comparison table of all five scenarios at `target_year`.

    Metrics (base units):
        RE Share (%), RE Generation (GWh), Fossil Avoided (GWh),
        CO2 Emissions (t), CO2 Emissions Avoided (t), LNG Savings ($M)
    """
    records = []
    for sc_name, conf in SCENARIOS.items():
        g_val = custom_growth_map.get(sc_name) if custom_growth_map else None
        proj = project_renewable(
            re_df,
            scenario=sc_name,
            custom_growth=g_val,
            end_year=target_year,
            emission_factors=emission_factors,
        )
        if proj.empty:
            continue
        target_rows = proj[proj["calendar_year"] == target_year]
        if target_rows.empty:
            continue
        row_target = target_rows.iloc[0]

        proj_slice = proj[(proj["calendar_year"] >= 2025) &
                          (proj["calendar_year"] <= target_year)]
        cum_co2_avoided = round(proj_slice["co2_avoided_t"].sum(), 1)
        cum_lng_savings = round(proj_slice["lng_savings_musd"].sum(), 1)
        cum_fossil_avoided = round(proj_slice["fossil_avoided_gwh"].sum(), 1)

        records.append({
            "scenario": sc_name,
            "re_share_pct": row_target["re_share_pct"],
            "re_gwh": row_target["re_gwh"],
            "fossil_gwh": row_target["fossil_gwh"],
            "fossil_avoided_gwh": row_target["fossil_avoided_gwh"],
            "cum_fossil_avoided_gwh": cum_fossil_avoided,
            "co2_t": row_target["co2_t"],
            "co2_avoided_t": row_target["co2_avoided_t"],
            "cum_co2_avoided_t": cum_co2_avoided,
            "lng_savings_musd": row_target["lng_savings_musd"],
            "cum_lng_savings_musd": cum_lng_savings,
            "color": conf["color"],
            "desc": conf["desc"],
        })

    comp_df = pd.DataFrame(records)
    if not comp_df.empty:
        # CO2 is rescaled to Mt only so both terms are comparable in the ranking
        comp_df["composite_score"] = (comp_df["re_share_pct"]
                                      + comp_df["co2_avoided_t"] / 1e6)
    return comp_df


# ---------------------------------------------------------------------------
# Extending the historical-only visuals (4, 5 and 6) up to `end_year`
# ---------------------------------------------------------------------------
CAPACITY_GROWTH_KEY = {
    "solar": "solar",
    "wind": "wind",
    "hydel": "hydro",
    "hydro": "hydro",
    "bagasse": "other",
    "biomass": "other",
}
CAPACITY_COLUMNS = ["calendar_year", "renewable_source", "installed_capacity_mw", "data_type"]


def _scenario_rates(scenario: str, custom_growth: float = None) -> dict:
    conf = SCENARIOS.get(scenario, SCENARIOS["Accelerated"])
    return {
        "solar": custom_growth if custom_growth is not None else conf["solar"],
        "wind": custom_growth if custom_growth is not None else conf["wind"],
        "hydro": conf.get("hydro", 2.0),
        "other": conf.get("other", 2.0),
    }


def project_renewable_capacity(cap_df: pd.DataFrame, scenario: str = "Accelerated",
                               custom_growth: float = None,
                               end_year: int = 2035) -> pd.DataFrame:
    """
    Extend `fact_renewable_capacity` (per source) from its last actual year to
    `end_year`, using the scenario growth rate for each source.
    """
    if cap_df is None or cap_df.empty:
        return pd.DataFrame(columns=CAPACITY_COLUMNS)

    df = cap_df.copy()
    df["calendar_year"] = pd.to_numeric(df["calendar_year"], errors="coerce")
    df = df.dropna(subset=["calendar_year"])
    df["calendar_year"] = df["calendar_year"].astype(int)
    # A NULL capacity stays NULL: filling it with 0.0 reads back as "this source
    # had no plant installed that year", which the record does not say.
    df["installed_capacity_mw"] = pd.to_numeric(
        df["installed_capacity_mw"], errors="coerce")

    rows = [{"calendar_year": int(r["calendar_year"]),
             "renewable_source": r["renewable_source"],
             "installed_capacity_mw": float(r["installed_capacity_mw"]),
             "data_type": "Actual" if not pd.isna(r["installed_capacity_mw"])
             else "Missing"} for _, r in df.iterrows()]

    rates = _scenario_rates(scenario, custom_growth)
    reported = df.dropna(subset=["installed_capacity_mw"])
    last_actual_year = (int(reported["calendar_year"].max())
                        if not reported.empty
                        else int(df["calendar_year"].max()))

    for source, sdf in df.groupby("renewable_source"):
        sdf = sdf.sort_values("calendar_year")
        known = sdf.dropna(subset=["installed_capacity_mw"])
        if known.empty:
            continue
        base = known.iloc[-1]
        base_year = int(base["calendar_year"])
        base_val = float(base["installed_capacity_mw"])
        key = CAPACITY_GROWTH_KEY.get(str(source).strip().lower(), "other")
        g = float(rates.get(key, 2.0))

        for yr in range(last_actual_year + 1, end_year + 1):
            rows.append({
                "calendar_year": yr,
                "renewable_source": source,
                "installed_capacity_mw": round(base_val * ((1 + g / 100.0) ** (yr - base_year)), 2),
                "data_type": "Projected",
            })

    return pd.DataFrame(rows).sort_values(["calendar_year", "renewable_source"])


