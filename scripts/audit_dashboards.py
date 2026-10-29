"""
scripts/audit_dashboards.py -- audit all three dashboards against their questions.

For each dashboard it:

  1. reads the question it is supposed to answer (from dashboards/registry.py),
  2. recomputes the headline claims INDEPENDENTLY with raw SQL + numpy,
  3. runs the dashboard's own engine and compares the two,
  4. cross-checks the dashboards against each other (they share fact tables, so
     they must not contradict one another).

Prints PASS / WARN / FAIL per check.  Run from the project root:

    .venv\\Scripts\\python.exe scripts\\audit_dashboards.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mysql.connector                                    # noqa: E402
from dotenv import load_dotenv                            # noqa: E402

from core import queries                                  # noqa: E402

load_dotenv(ROOT / ".env")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)

RESULTS: list = []


def check(name: str, actual, expected, tol: float = 0.0, unit: str = "",
          note: str = ""):
    """Compare an engine number with the independent one."""
    ok = False
    try:
        a, e = float(actual), float(expected)
        if tol == 0.0:
            ok = abs(a - e) <= max(1e-9, abs(e) * 1e-9)
        else:
            ok = abs(a - e) <= tol
    except (TypeError, ValueError):
        ok = str(actual) == str(expected)
        a, e = actual, expected
    status = "PASS" if ok else "FAIL"
    RESULTS.append((status, name, a, e, note))
    shown_a = f"{a:,.4f}" if isinstance(a, float) else str(a)
    shown_e = f"{e:,.4f}" if isinstance(e, float) else str(e)
    print(f"  [{status}] {name:<52} engine={shown_a:<16} independent={shown_e:<16}"
          f"{('±' + str(tol)) if tol else ''} {unit} {note}")
    return ok


def info(text: str):
    print(f"  ....  {text}")


def warn(name: str, detail: str):
    """A finding that is not a numeric mismatch but still needs attention."""
    RESULTS.append(("WARN", name, detail, "", ""))
    print(f"  [WARN] {name}\n         {detail}")


def section(title: str):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"), user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "energy_database_new"),
        port=int(os.getenv("DB_PORT", 3306)), connection_timeout=15)


def load(conn, sql):
    return pd.read_sql(sql, conn)


def main() -> int:
    conn = connect()
    q = lambda sql: load(conn, sql)          # noqa: E731

    # ══════════════════════════════════════════════════════════════════════
    section("A. RAW DATA REALITY (what the dashboards have to work with)")
    # ══════════════════════════════════════════════════════════════════════
    re_raw = q(queries.Q_RENEWABLE_ENERGY)
    RE_COLS = ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
               "gen_other_renewables_gwh", "gen_coal_gwh", "gen_gas_gwh",
               "gen_nuclear_gwh", "demand_gwh", "capacity_mw"]
    other_re_null = int(re_raw["gen_other_renewables_gwh"].isna().sum())
    for c in RE_COLS:
        re_raw[c] = pd.to_numeric(re_raw[c], errors="coerce").fillna(0.0)
    info(f"fact_renewable_energy.gen_other_renewables_gwh is NULL in "
         f"{other_re_null}/{len(re_raw)} rows -> the app treats 'other renewables' "
         f"(bagasse) as 0 GWh everywhere")
    cap_raw = q(queries.Q_RENEWABLE_CAPACITY)
    cap_raw["installed_capacity_mw"] = pd.to_numeric(cap_raw["installed_capacity_mw"],
                                                     errors="coerce").fillna(0.0)
    info(f"fact_renewable_capacity covers "
         f"{int(cap_raw.calendar_year.min())}-{int(cap_raw.calendar_year.max())} "
         f"(sources: {', '.join(sorted(cap_raw.renewable_source.unique()))})")
    info(f"fact_energy_overview covers 2005-2019; fact_natural_gas 1999-2018; "
         f"fact_elec_generation 2002-2023")
    span = lambda df, col: (int(df.loc[df[col].notna(), "calendar_year"].min()),  # noqa: E731
                            int(df.loc[df[col].notna(), "calendar_year"].max()))
    for label, df, col in [
        ("fact_renewable_energy.gen_*", re_raw, "gen_coal_gwh"),
        ("fact_renewable_energy.demand_gwh", re_raw, "demand_gwh"),
        ("fact_economic_indicators", q(queries.Q_ECONOMIC), "gdp_current_usd"),
        ("fact_energy_overview", q(queries.Q_ENERGY_OVERVIEW), "total_primary_supply_toe"),
        ("fact_primary_energy_supply", q(queries.Q_PRIMARY_SUPPLY), "supply_toe"),
        ("fact_natural_gas", q(queries.Q_NATURAL_GAS), "production_bcf"),
        ("fact_elec_generation", q(queries.Q_ELEC_GEN), "generation_gwh"),
        ("fact_final_energy_consumption", q(queries.Q_FINAL_ENERGY_BY_SOURCE), "consumption_toe"),
    ]:
        a, b = span(df, col)
        info(f"{label:<40} reported {a}-{b}  ({df[col].notna().sum()} values)")

    gen = q(queries.Q_ELEC_GEN)
    gen["generation_gwh"] = pd.to_numeric(gen["generation_gwh"], errors="coerce")
    sec = q(queries.Q_ELEC_SECTOR_CONSUMPTION)
    info(f"grid demand (renewable table) 2024 = "
         f"{re_raw.loc[re_raw.calendar_year == 2024, 'demand_gwh'].iloc[0]:,.0f} GWh")
    info(f"generation (elec table) 2023       = "
         f"{gen.loc[gen.calendar_year == 2023, 'generation_gwh'].iloc[0]:,.0f} GWh")
    info(f"sector consumption total 2024      = "
         f"{pd.to_numeric(sec.loc[sec.calendar_year == 2024, 'consumption_gwh']).sum():,.0f} GWh")

    # ══════════════════════════════════════════════════════════════════════
    section("B. Q2 -- 'What are the potential outcomes of installing renewable "
            "energy sources in different energy scenarios?'")
    # ══════════════════════════════════════════════════════════════════════
    from config.settings import EMISSION_FACTORS, SCENARIOS
    from core.projections import (compare_all_scenarios, project_renewable,
                                  project_renewable_capacity)

    r2024 = re_raw[re_raw.calendar_year == 2024].iloc[0]
    re_2024 = sum(float(r2024[c]) for c in ("gen_solar_gwh", "gen_wind_gwh",
                                            "gen_hydro_gwh", "gen_other_renewables_gwh"))
    coal_2024 = float(r2024["gen_coal_gwh"])
    gas_2024 = float(r2024["gen_gas_gwh"])
    nuc_2024 = float(r2024["gen_nuclear_gwh"])
    total_2024 = re_2024 + coal_2024 + gas_2024 + nuc_2024
    share_2024 = re_2024 / total_2024 * 100.0

    info(f"2024 generation mix: RE {re_2024:,.0f} | coal {coal_2024:,.0f} | "
         f"gas {gas_2024:,.0f} | nuclear {nuc_2024:,.0f} GWh | total {total_2024:,.0f} GWh")
    info(f"2024 demand_gwh column = {float(r2024['demand_gwh']):,.0f} GWh "
         f"= {float(r2024['demand_gwh']) / total_2024:.3f}x the generation columns")
    # Q2's 2024 RE share is no longer hard-coded in the page -- it is computed
    # live from fact_renewable_energy, so the meaningful check is the fossil-split
    # constants projections.py assumes (below) and, after the engine runs, that
    # the engine's own 2024 history share matches an independent raw sum.
    fossil_2024 = coal_2024 + gas_2024
    check("Q2 coal share of fossil 0.356 (projections.py split) vs real",
          0.356, coal_2024 / fossil_2024, tol=0.002, note="<- projections.py")
    check("Q2 gas share of fossil 0.644 (projections.py split) vs real",
          0.644, gas_2024 / fossil_2024, tol=0.002, note="<- projections.py")

    proj = project_renewable(re_raw, scenario="Accelerated", end_year=2035,
                             emission_factors=dict(EMISSION_FACTORS))
    row35 = proj[proj.calendar_year == 2035].iloc[0]
    row24 = proj[proj.calendar_year == 2024].iloc[0]
    row25 = proj[proj.calendar_year == 2025].iloc[0]
    # The page now derives its RE share from this engine path; confirm the
    # engine's 2024 history share equals an independent sum of the raw columns.
    check("Q2 2024 RE share computed live (engine history vs raw sum)",
          float(row24["re_share_pct"]), share_2024, tol=0.05, unit="%",
          note="<- was a stale hard-coded '40.95'; page now computes it live")
    info(f"Accelerated 2035: RE share {row35['re_share_pct']:.1f}% | "
         f"CO2 {row35['co2_t'] / 1e6:.1f} Mt | intensity "
         f"{row35['co2_t'] / row35['total_gen_gwh']:.0f} kg/MWh | "
         f"demand {row35['demand_gwh']:,.0f} GWh")

    # history -> projection continuity: a modelled year must not jump
    check("Q2 fossil generation step 2024->2025 (jump = discontinuity)",
          float(row25["fossil_gwh"]), float(row24["fossil_gwh"]),
          tol=float(row24["fossil_gwh"]) * 0.05, unit="GWh",
          note="<- history uses reported generation, projection uses demand_gwh")
    # The reported->modelled basis CHANGES at the seam: history is the reported
    # coal+gas mix, the first modelled year is a demand-based fossil residual
    # (grid demand runs ~1.12x reported generation), so 2024->2025 CO2 steps up by
    # design. That is an expected basis change, not a bug -- note it, then test the
    # thing that must actually hold: a modelled year's CO2 equals its own fuel mix.
    co2_step = (float(row25["co2_t"]) / float(row24["co2_t"]) - 1) * 100
    warn("Q2 CO2 steps at the 2024->2025 history/projection seam",
         f"{co2_step:+.1f}% at the seam is expected: the projection is demand-based "
         f"while 2024 is the reported generation mix. Modelled years are internally "
         f"consistent (check below).")
    _ef = dict(EMISSION_FACTORS)
    co2_25 = (float(row25["coal_gwh"]) * _ef.get("coal", 0.0)
              + float(row25["gas_gwh"]) * _ef.get("gas", 0.0)) * 1000.0
    check("Q2 modelled 2025 CO2 == its own coal/gas split x emission factors",
          float(row25["co2_t"]), co2_25, tol=1.0, unit="t",
          note="<- internal consistency of the projection, not a seam jump")

    # independent recomputation of the 2035 demand, anchored where the engine
    # anchors it: the LAST year that actually reported demand_gwh (2025), not the
    # calendar-last row.  The old check wrongly compounded from the 2024 row.
    _last_dem = (re_raw[["calendar_year", "demand_gwh"]].dropna()
                 .sort_values("calendar_year").iloc[-1])
    _base_dem_year = int(_last_dem["calendar_year"])
    demand_2035 = float(_last_dem["demand_gwh"]) * (1.025 ** (2035 - _base_dem_year))
    check(f"Q2 2035 demand compounds 2.5%/yr from base year {_base_dem_year}",
          demand_2035, float(row35["demand_gwh"]), tol=1.0, unit="GWh")
    check("Q2 zero-fossil artifact: Solar-led 2035 CO2 is exactly zero",
          float(compare_all_scenarios(re_raw, target_year=2035,
                                      emission_factors=dict(EMISSION_FACTORS))
                .set_index("scenario").loc["Solar-led", "co2_t"]),
          0.0, tol=0.001, unit="t")
    warn("Q2 Solar-led 2035 reports 0 t CO2 and 91.4% RE share",
         "RE generation overtakes demand, so fossil is floored at 0 and the "
         "scenario shows a zero-carbon grid. It is a model artefact, not an outcome.")

    # demand-growth assumption vs the Q4 evidence
    grid = re_raw[["calendar_year", "demand_gwh"]].dropna()
    grid = grid[grid.calendar_year >= 2000]
    cagr_all = ((grid.demand_gwh.iloc[-1] / grid.demand_gwh.iloc[0])
                ** (1 / (grid.calendar_year.iloc[-1] - grid.calendar_year.iloc[0])) - 1) * 100
    g19 = grid[grid.calendar_year >= 2019]
    cagr_post = ((g19.demand_gwh.iloc[-1] / g19.demand_gwh.iloc[0])
                 ** (1 / (g19.calendar_year.iloc[-1] - g19.calendar_year.iloc[0])) - 1) * 100
    info(f"Q2 assumes demand grows 2.5%/yr; reported grid demand CAGR is "
         f"{cagr_all:.2f}%/yr (2000-2024) and {cagr_post:.2f}%/yr (2019-2024)")
    warn("Q2 uses a deliberately conservative flat 2.5%/yr demand baseline",
         f"Not an error: the five RE scenarios share one modest demand path so they "
         f"stay comparable on the same basis, while the reported grid CAGR is higher "
         f"({cagr_post:.2f}%/yr, 2019-2024). Q2 answers 'what if we install RE', not "
         f"'what will demand be' -- that is Q4's job. Documented assumption.")

    # renewable capacity KPI: the per-source table stops in 2018, so both the
    # "2024" baseline and the 2035 value the KPI shows are MODELLED.
    cap = cap_raw
    last_cap_year = int(cap.calendar_year.max())
    cap_last = (cap[cap.calendar_year == last_cap_year]
                .groupby("renewable_source")["installed_capacity_mw"].sum())
    info(f"capacity last reported {last_cap_year}: "
         + ", ".join(f"{k}={v:,.0f}MW" for k, v in cap_last.items())
         + f"  (total {cap_last.sum():,.0f} MW)")
    cap_ext = project_renewable_capacity(cap, scenario="Accelerated", end_year=2035)
    cap35 = cap_ext[cap_ext.calendar_year == 2035]["installed_capacity_mw"].sum()
    cap24 = cap_ext[cap_ext.calendar_year == 2024]["installed_capacity_mw"].sum()
    info(f"Q2 'RE Capacity' KPI: 2024 shown = {cap24:,.0f} MW (modelled), "
         f"2035 = {cap35:,.0f} MW (modelled)")
    indep_cap = 0.0
    for source, rate in (("Hydel", 3.0), ("Solar", 15.0), ("Wind", 15.0),
                         ("Bagasse", 5.0)):
        indep_cap += float(cap_last.get(source, 0.0)) * (1 + rate / 100.0) ** (2035 - last_cap_year)
    check(f"Q2 capacity KPI 2035 compounds from {last_cap_year} at per-source rates",
          cap35, indep_cap, tol=cap_last.sum() * 0.02, unit="MW")
    warn(f"Q2 'RE Capacity' KPI is anchored on {last_cap_year}, not 2024",
         f"fact_renewable_capacity has no rows after {last_cap_year}, so the card's "
         f"'vs 2024' delta compares two modelled numbers while the badge says "
         f"'MW Installed'. The reported 2024 renewable capacity is "
         f"{float(r2024['capacity_mw']):,.0f} MW in fact_renewable_energy.")

    comp = compare_all_scenarios(re_raw, target_year=2035,
                                 emission_factors=dict(EMISSION_FACTORS))
    info("Q2 scenario comparison at 2035:")
    print(comp[["scenario", "re_share_pct", "co2_t", "co2_avoided_t",
                "cum_lng_savings_musd"]].round(1).to_string(index=False))
    # The Q2 page does NOT crown a single "best" scenario -- it puts all five
    # side by side and lets the reader choose (and co2_avoided_t ties once fossil
    # floors at zero, so a max-pick would be arbitrary anyway).  The honest
    # structural checks are that every scenario is present and the RE-share
    # ordering is the sensible one the reader sees.
    check("Q2 comparison lists all five scenarios", len(comp), 5,
          note="<- Baseline/Moderate/Accelerated/Solar-led/Wind-led")
    check("Q2 highest 2035 RE share is the Solar-led scenario",
          comp.sort_values("re_share_pct").iloc[-1]["scenario"], "Solar-led",
          note="<- the page shows all five, not a single 'best'")

    # ══════════════════════════════════════════════════════════════════════
    section("C. Q3 -- 'What are the bottlenecks in achieving planned targets?'")
    # ══════════════════════════════════════════════════════════════════════
    from core.bottleneck_metrics import build_dashboard_data as q3_build
    from core.targets import KPI_SPEC, load_targets

    overview = q(queries.Q_ENERGY_OVERVIEW)
    primary = q(queries.Q_PRIMARY_SUPPLY)
    gas = q(queries.Q_NATURAL_GAS)
    targets = load_targets()

    data3 = q3_build(overview, primary, re_raw, gas, targets=targets,
                     year_range=(2002, 2035), project_end=2035)
    series3 = data3["series"]
    readings3 = data3["readings"]

    # K1 losses % -- raw SQL for the last reported year
    ov = overview.copy()
    for c in ("total_primary_supply_toe", "total_losses_toe"):
        ov[c] = pd.to_numeric(ov[c], errors="coerce")
    last_ov = ov.dropna(subset=["total_losses_toe"]).iloc[-1]
    k1_raw = float(last_ov["total_losses_toe"]) / float(last_ov["total_primary_supply_toe"]) * 100
    k1_eng = float(series3.loc[series3.calendar_year == int(last_ov["calendar_year"]),
                               "losses_pct"].iloc[0])
    check(f"Q3 K1 losses % in {int(last_ov['calendar_year'])} (raw vs engine)",
          k1_eng, k1_raw, tol=0.01, unit="%")

    # K4 gas self-sufficiency % -- raw SQL
    g = gas.copy()
    for c in ("production_bcf", "consumption_bcf"):
        g[c] = pd.to_numeric(g[c], errors="coerce")
    last_g = g.dropna(subset=["consumption_bcf"]).iloc[-1]
    k4_raw = float(last_g["production_bcf"]) / float(last_g["consumption_bcf"]) * 100
    k4_eng = float(series3.loc[series3.calendar_year == int(last_g["calendar_year"]),
                               "gas_self_suff_pct"].iloc[0])
    check(f"Q3 K4 gas self-sufficiency % in {int(last_g['calendar_year'])}",
          k4_eng, k4_raw, tol=0.05, unit="%")

    # K3 renewable share % -- raw SQL (same definition as Q2)
    ref_share = [k for k in ("re_share_pct",) if k in series3.columns]
    if ref_share:
        k3_eng = float(series3.loc[series3.calendar_year == 2024, "re_share_pct"].iloc[0])
        check("Q3 K3 renewable share % 2024 vs Q2/raw SQL", k3_eng, share_2024,
              tol=0.05, unit="%")

    for spec in KPI_SPEC:
        reading = readings3.get(spec["key"])
        if reading is None:
            continue
        attrs = {a: getattr(reading, a) for a in
                 ("code", "actual_value", "target", "gap", "achievement", "on_track",
                  "reference_year", "direction") if hasattr(reading, a)}
        info(f"{spec['key']:<20} {attrs}")
    info(f"Q3 ranking: {[r.get('short', r.get('key')) for r in data3.get('ranking', [])]}")

    # ══════════════════════════════════════════════════════════════════════
    section("D. Q4 -- 'What is forecasted energy demand?'")
    # ══════════════════════════════════════════════════════════════════════
    from core.demand_forecast import build_dashboard_data as q4_build

    data4 = q4_build(
        fuel_df=q(queries.Q_FINAL_ENERGY_BY_SOURCE), re_df=re_raw,
        econ_df=q(queries.Q_ECONOMIC), primary_df=primary,
        gen_df=gen, gas_df=gas,
        sector_df=sec, province_df=q(queries.Q_ELEC_PROVINCE_CONSUMPTION))
    hist4 = data4["history"]

    check("Q4 total final energy 2024 (raw SUM vs history)",
          float(hist4.loc[hist4.calendar_year == 2024, "total_final_toe"].iloc[0]),
          float(q("SELECT SUM(consumption_toe) s FROM fact_final_energy_consumption f "
                  "JOIN dim_year y ON f.year_id=y.year_id WHERE y.calendar_year=2024")["s"].iloc[0]),
          tol=1.0, unit="TOE")
    check("Q4 grid demand 2024 vs raw demand_gwh",
          float(hist4.loc[hist4.calendar_year == 2024, "elec_grid_gwh"].iloc[0]),
          float(r2024["demand_gwh"]), tol=1.0, unit="GWh")

    # Independent elasticity, mirroring the engine's DOCUMENTED model exactly --
    # not the naive OLS this check used to run.  The engine (core.demand_forecast.
    # fit_driver_model) fits ln(demand/pop) ~ ln(real GDP/head) + D over the
    # 2012..2024 window, but (a) drops rows where demand/pop/GDP-per-head are
    # missing or non-positive, (b) uses the *detected* reporting-basis break year
    # (2023 for total final energy -- not 2019), and (c) drops the dummy when it is
    # constant in the sample.  Reproducing that spec confirms the engine value.
    from core.demand_forecast import detect_break, break_flags
    win = hist4[(hist4.calendar_year >= 2012) & (hist4.calendar_year <= 2024)].copy()
    for _c in ("total_final_toe", "population", "real_gdp_per_capita"):
        win[_c] = pd.to_numeric(win[_c], errors="coerce")
    win = win[(win["total_final_toe"] > 0) & (win["population"] > 0)
              & (win["real_gdp_per_capita"] > 0)]
    y = np.log(win["total_final_toe"].to_numpy(float) / win["population"].to_numpy(float))
    x = np.log(win["real_gdp_per_capita"].to_numpy(float))
    dummy = break_flags(win["calendar_year"].to_numpy(float),
                        detect_break(hist4, "total_final"))
    _cols = [np.ones(len(win)), x]
    if float(np.ptp(dummy)) > 0.0:          # a constant dummy carries no signal
        _cols.append(dummy)
    design = np.column_stack(_cols)
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    slope = float(coef[1])
    check("Q4 income elasticity (total final energy)",
          data4["models"]["total_final"]["elasticity_income"], slope, tol=0.01,
          note="<- engine fit on its own valid sample + detected 2023 break")
    fitted = design @ coef
    r2_indep = 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    check("Q4 elasticity fit R2", data4["models"]["total_final"]["r2_per_capita"],
          r2_indep, tol=0.005)

    # independent 2035 Base value for total final energy
    grows = data4["grows"]["total_final"]["Base"]["growth_by_year"]
    value = float(hist4.loc[hist4.calendar_year == 2024, "total_final_toe"].iloc[0])
    for year in range(2025, 2036):
        value *= 1 + grows[year] / 100.0
    check("Q4 2035 Base total final energy (recompounded)",
          data4["kpis"]["total_final"]["horizon_value"], value, tol=max(1.0, value * 1e-6),
          unit="TOE")

    gp = data4["gap"]["imports"]
    gp35 = gp[gp.calendar_year == 2035].iloc[0]
    # independent: log-linear trends of production and consumption over 2012-2018,
    # then dependency = (consumption - production) / consumption
    gg = gas.copy()
    for c in ("production_bcf", "consumption_bcf"):
        gg[c] = pd.to_numeric(gg[c], errors="coerce")
    win_g = gg[(gg.calendar_year >= 2012) & (gg.calendar_year <= 2018)].dropna(
        subset=["production_bcf", "consumption_bcf"])
    yrs = win_g.calendar_year.to_numpy(float)
    slope_p, int_p = np.polyfit(yrs, win_g.production_bcf.to_numpy(float), 1)
    slope_c, int_c = np.polyfit(yrs, win_g.consumption_bcf.to_numpy(float), 1)
    prod35 = int_p + slope_p * 2035          # linear, as core.demand_forecast does
    cons35 = int_c + slope_c * 2035
    indep_dep = max(0.0, (cons35 - prod35) / cons35 * 100)
    info(f"independent gas balance 2035: production {prod35:,.0f} BCF, "
         f"consumption {cons35:,.0f} BCF")
    check("Q4 gas import dependency 2035 (balance-based)",
          float(gp35["gas_import_dep_pct"]), indep_dep, tol=4.0, unit="%")

    metrics = data4["backtest"]["metrics"]
    hold = metrics[metrics.window == "hold-out"].set_index(["series", "model"])
    info("Q4 backtest (hold-out 2021-2024):")
    print(hold[["mape", "rmse", "bias", "n"]].round(2).to_string())

    # ══════════════════════════════════════════════════════════════════════
    section("E. CROSS-DASHBOARD CONSISTENCY")
    # ══════════════════════════════════════════════════════════════════════
    q4_grid_growth = data4["grows"]["elec_grid"]["Base"]["demand_growth_pct"]
    warn("'Future demand' differs by design: Q2 flat 2.5%/yr vs Q4 modelled growth",
         f"Not a contradiction: Q2 holds demand to one conservative 2.5%/yr baseline "
         f"so its five RE scenarios stay like-for-like; Q4 answers 'what is forecasted "
         f"demand' with an elasticity+trend model that projects {q4_grid_growth:.2f}%/yr "
         f"for the grid. Two questions, two instruments -- label them, don't force one.")

    q3_self = float(series3.loc[series3.calendar_year == 2035, "gas_self_suff_pct"].iloc[0])
    q4_self = 100.0 - float(gp35["gas_import_dep_pct"])
    warn(f"Gas self-sufficiency 2035: Q3 says {q3_self:.1f}%, Q4 implies {q4_self:.1f}%",
         "Same physical balance, two projections. Q3 clamps production/consumption to "
         "at least -2%/+2% a year (deliberately conservative); Q4 fits an unclamped "
         "linear trend on 2012-2018. Point both at one gas projection if the suite "
         "must give a single 2035 number.")

    q2_share_35 = float(comp.loc[comp.scenario == "Accelerated", "re_share_pct"].iloc[0])
    q3_share_35 = float(series3.loc[series3.calendar_year == 2035, "re_share_pct"].iloc[0])
    warn(f"RE share 2035: Q2 (Accelerated) says {q2_share_35:.1f}%, Q3 says {q3_share_35:.1f}%",
         "Defensible difference, not an error: Q2 answers 'what if we install RE at "
         "15%/yr', Q3 answers 'where does the current trend land'. Both read the same "
         "generation table; label the difference so it is not read as a contradiction.")

    q3_k1_35 = float(series3.loc[series3.calendar_year == 2035, "losses_pct"].iloc[0])
    info(f"Q3 losses 2035 = {q3_k1_35:.2f}% of supply; Q4 supply gap 2035 = "
         f"{data4['kpis']['supply_gap']['gap_pct']:+.2f}% of supply "
         f"(different definitions: losses vs demand-vs-supply)")

    # ══════════════════════════════════════════════════════════════════════
    section("SUMMARY")
    # ══════════════════════════════════════════════════════════════════════
    failed = [r for r in RESULTS if r[0] == "FAIL"]
    warned = [r for r in RESULTS if r[0] == "WARN"]
    numeric = [r for r in RESULTS if r[0] in ("PASS", "FAIL")]
    print(f"  {len(numeric)} numeric checks: {len(numeric) - len(failed)} passed, "
          f"{len(failed)} failed   |   {len(warned)} findings (WARN)")
    for status, name, a, e, note in failed:
        print(f"    FAIL: {name}  (engine={a}, independent={e}) {note}")
    for _, name, detail, _, _ in warned:
        print(f"    WARN: {name}")
    conn.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
