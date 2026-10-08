"""
core/projections.py -- scenario projection engine.

Works in the storage base units (GWh, MW, t CO2, Million USD); conversion to a
display unit happens at render time via core.units.
Emission factors are tCO2/MWh, so CO2_t = gen_GWh * 1000 * emission_factor.
"""

from __future__ import annotations

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
    (2024) to `end_year`. Returns both Actual and Projected rows, all in base
    units: generation in GWh, capacity in MW, CO2 in tonnes, savings in M USD.
    """
    ef = emission_factors if emission_factors else EMISSION_FACTORS
    df_sorted = df.copy().sort_values("calendar_year")

    last = df_sorted.iloc[-1]
    last_year = int(last["calendar_year"])

    # ---------------- Historical rows (base units) ----------------
    hist_rows = []
    for _, r in df_sorted.iterrows():
        sol = _num(r.get("gen_solar_gwh"))
        wnd = _num(r.get("gen_wind_gwh"))
        hyd = _num(r.get("gen_hydro_gwh"))
        oth = _num(r.get("gen_other_renewables_gwh"))
        col = _num(r.get("gen_coal_gwh"))
        gas = _num(r.get("gen_gas_gwh"))
        nuc = _num(r.get("gen_nuclear_gwh"))
        dem = _num(r.get("demand_gwh"))
        cap = _num(r.get("capacity_mw"))
        re_tot = sol + wnd + hyd + oth
        tot_gen = re_tot + col + gas + nuc

        hist_rows.append({
            "calendar_year": int(r["calendar_year"]),
            "solar_gwh": sol,
            "wind_gwh": wnd,
            "hydro_gwh": hyd,
            "other_gwh": oth,
            "coal_gwh": col,
            "gas_gwh": gas,
            "nuclear_gwh": nuc,
            "demand_gwh": dem if dem > 0 else tot_gen,
            "re_gwh": re_tot,
            "fossil_gwh": col + gas,
            "total_gen_gwh": tot_gen,
            "re_share_pct": round((re_tot / tot_gen * 100), 2) if tot_gen > 0 else 0.0,
            "capacity_mw": cap,
            "co2_t": round(_co2_t(col, gas, ef), 2),
            "fossil_avoided_gwh": 0.0,
            "co2_avoided_t": 0.0,
            "lng_savings_musd": 0.0,
            "data_type": "Actual",
        })

    if not hist_rows:
        return pd.DataFrame()

    # ---------------- Growth configuration ----------------
    sc_conf = SCENARIOS.get(scenario, SCENARIOS["Accelerated"])
    g_solar = custom_growth if custom_growth is not None else sc_conf["solar"]
    g_wind = custom_growth if custom_growth is not None else sc_conf["wind"]
    g_hydro = sc_conf.get("hydro", 2.0)
    g_other = sc_conf.get("other", 2.0)

    base = hist_rows[-1]
    base_solar = base["solar_gwh"]
    base_wind = base["wind_gwh"]
    base_hydro = base["hydro_gwh"]
    base_other = base["other_gwh"]
    base_nuc = base["nuclear_gwh"]
    base_dem = base["demand_gwh"]
    base_cap = base["capacity_mw"]
    base_re_cap_ref = base_solar + base_wind + base_hydro

    # ---------------- Projected rows ----------------
    proj_rows = []
    for yr in range(last_year + 1, end_year + 1):
        n = yr - last_year

        sol = base_solar * ((1 + g_solar / 100.0) ** n)
        wnd = base_wind * ((1 + g_wind / 100.0) ** n)
        hyd = base_hydro * ((1 + g_hydro / 100.0) ** n)
        oth = base_other * ((1 + g_other / 100.0) ** n)
        re_tot = sol + wnd + hyd + oth

        dem = base_dem * ((1 + demand_growth / 100.0) ** n)
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
    df["installed_capacity_mw"] = pd.to_numeric(
        df["installed_capacity_mw"], errors="coerce").fillna(0.0)
    df["calendar_year"] = pd.to_numeric(df["calendar_year"], errors="coerce")
    df = df.dropna(subset=["calendar_year"])
    df["calendar_year"] = df["calendar_year"].astype(int)

    rows = [{"calendar_year": int(r["calendar_year"]),
             "renewable_source": r["renewable_source"],
             "installed_capacity_mw": float(r["installed_capacity_mw"]),
             "data_type": "Actual"} for _, r in df.iterrows()]

    rates = _scenario_rates(scenario, custom_growth)
    last_actual_year = int(df["calendar_year"].max())

    for source, sdf in df.groupby("renewable_source"):
        sdf = sdf.sort_values("calendar_year")
        base = sdf.iloc[-1]
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


def project_system_metrics(combo_df: pd.DataFrame, proj_df: pd.DataFrame,
                           end_year: int = 2035) -> pd.DataFrame:
    """
    Extend the capacity / generation / T&D-loss series to `end_year`.

    Installation capacity follows generation, and the last observed T&D loss
    ratio is held constant (a documented assumption, not a measured value).
    """
    cols = ["calendar_year", "installed_capacity_mw", "generation_gwh",
            "td_losses_gwh", "data_type"]
    if combo_df is None or combo_df.empty:
        return pd.DataFrame(columns=cols)

    df = combo_df.copy().sort_values("calendar_year")
    for c in ("installed_capacity_mw", "generation_gwh", "td_losses_gwh"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["calendar_year"] = pd.to_numeric(df["calendar_year"], errors="coerce")
    df = df.dropna(subset=["calendar_year"])
    df["calendar_year"] = df["calendar_year"].astype(int)

    rows = [{**{c: r.get(c) for c in cols if c != "data_type"},
             "calendar_year": int(r["calendar_year"]), "data_type": "Actual"}
            for _, r in df.iterrows()]

    gen_rows = df.dropna(subset=["generation_gwh"])
    if gen_rows.empty:
        return pd.DataFrame(rows)[cols].sort_values("calendar_year")

    base = gen_rows.iloc[-1]
    base_gen = float(base["generation_gwh"]) or 0.0
    base_cap = float(base["installed_capacity_mw"] or 0.0)
    td_rows = df.dropna(subset=["td_losses_gwh"])
    loss_ratio = (float(td_rows.iloc[-1]["td_losses_gwh"]) / base_gen
                  if not td_rows.empty and base_gen else 0.0)

    if proj_df is not None and not proj_df.empty:
        proj_base = proj_df[proj_df["data_type"] == "Actual"]
        proj_base_gen = (float(proj_base.iloc[-1]["total_gen_gwh"])
                         if not proj_base.empty else 0.0)
        future = proj_df[proj_df["calendar_year"] > int(base["calendar_year"])]
        for _, r in future.iterrows():
            gen = float(r.get("total_gen_gwh") or 0.0)
            scale = (gen / proj_base_gen) if proj_base_gen else 1.0
            rows.append({
                "calendar_year": int(r["calendar_year"]),
                "installed_capacity_mw": round(base_cap * scale, 2),
                "generation_gwh": round(gen, 2),
                "td_losses_gwh": round(gen * loss_ratio, 2),
                "data_type": "Projected",
            })

    return pd.DataFrame(rows)[cols].sort_values("calendar_year")


def merge_co2_vs_re(co2_hist_df: pd.DataFrame, proj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reported CO2 history (fact_economic_indicators) plus the scenario-projected
    CO2 / RE-share, so visual 4 also reaches `end_year`.
    """
    cols = ["calendar_year", "re_share_pct", "co2_t", "data_type"]
    if co2_hist_df is None or co2_hist_df.empty:
        return pd.DataFrame(columns=cols)

    hist = co2_hist_df.copy().sort_values("calendar_year")
    rows = [{"calendar_year": int(r["calendar_year"]),
             "re_share_pct": float(r["re_share_pct"]),
             "co2_t": float(r["co2_t"]),
             "data_type": "Actual"} for _, r in hist.iterrows()]

    last_year = int(hist["calendar_year"].max())
    if proj_df is not None and not proj_df.empty:
        future = proj_df[proj_df["calendar_year"] > last_year]
        for _, r in future.iterrows():
            rows.append({"calendar_year": int(r["calendar_year"]),
                         "re_share_pct": float(r["re_share_pct"]),
                         "co2_t": float(r["co2_t"]),
                         "data_type": "Projected"})

    return pd.DataFrame(rows)[cols].sort_values("calendar_year")
