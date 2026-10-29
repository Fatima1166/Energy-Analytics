"""
scripts/verify_q10_allocation.py -- run the Q10 allocation optimiser against MySQL.

Standalone verification and audit trail for Question 10:
"What is optimal resource allocation for sustainable development?"

Usage:
    .venv\\Scripts\\python.exe scripts\\verify_q10_allocation.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The audit trail prints arrows and check marks; a cp1252 console would raise.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import mysql.connector
from dotenv import load_dotenv

from core import queries
from core.resource_allocation import HORIZON, HISTORY_END, build_allocation_data

load_dotenv(ROOT / ".env")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)


def connect():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "energy_database_new"),
        port=int(os.getenv("DB_PORT", 3306)),
        connection_timeout=15,
    )


def load(conn, sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, conn)


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def main() -> int:
    conn = connect()
    data = build_allocation_data(
        re_df=load(conn, queries.Q_RENEWABLE_ENERGY),
        gas_df=load(conn, queries.Q_NATURAL_GAS),
        ef_df=load(conn, queries.Q_EMISSION_FACTORS),
    )
    conn.close()

    opt, bau = data["opt_score"], data["bau_score"]

    section("Q10 THE JOB TO BE DONE")
    base_year = int(data["base_year"]) or HISTORY_END
    print(f"{base_year} generation base: {data['total_base_gwh']:14,.0f} GWh")
    print(f"Horizon {HORIZON} need:      {data['demand_gwh']:14,.0f} GWh  "
          f"(x{data['demand_gwh'] / max(data['total_base_gwh'], 1):.2f})")

    section("HOW THE POWER IS SPLIT (GWh)")
    for _, r in data["allocation"].iterrows():
        clamp = "  ◤ at its limit" if r["clamped"] else ""
        print(f"  {r['technology']:<9} plan={r['optimal_gwh']:12,.0f}   "
              f"{base_year} mix={r['bau_gwh']:12,.0f}   limit={r['ceiling_gwh']:12,.0f}{clamp}")
    print(f"  Left unserved: {data['shortfall_gwh']:,.0f} GWh  "
          f"(demand served {opt['coverage_pct']:.1f}%)")

    section(f"WHAT THE PLAN BUYS (plan vs the {base_year} mix)")
    print(f"  Cost       :  {opt['cost_usd']/1e9:10,.2f} bn USD  vs "
          f"{bau['cost_usd']/1e9:10,.2f} on the {base_year} mix")
    print(f"  CO2        :  {opt['co2_t']/1e6:10,.1f} Mt      vs "
          f"{bau['co2_t']/1e6:10,.1f} on the {base_year} mix")
    print(f"  Fuel bought:  {opt['import_dep_pct']:10,.1f} %    vs "
          f"{bau['import_dep_pct']:10,.1f} on the {base_year} mix")
    print(f"  Clean share:  {opt['re_share_pct']:10,.1f} %    vs "
          f"{bau['re_share_pct']:10,.1f} on the {base_year} mix")

    section("WHAT THE PRIORITIES BUY (cheapest-first vs cleanest-first)")
    p = data["pareto"]
    print(f"  Cheapest : {p['cost_usd'].min() / 1e9:8,.2f} bn USD at "
          f"{p.loc[p['cost_usd'].idxmin(), 'co2_t'] / 1e6:8,.1f} Mt")
    print(f"  Cleanest : {p.loc[p['co2_t'].idxmin(), 'cost_usd'] / 1e9:8,.2f} bn "
          f"USD at {p['co2_t'].min() / 1e6:8,.1f} Mt")

    section("SCORECARD (0-100, the 2024 mix | the plan)")
    for _, r in data["radar"].iterrows():
        arrow = "up" if r["optimal"] >= r["bau"] else "DOWN"
        print(f"  {r['dimension']:<16} {r['bau']:6.1f} | {r['optimal']:6.1f}   {arrow}")

    section("GAS FEASIBILITY")
    print(f"  Home gas planning cap: {data['domestic_gas_bcf']:8,.1f} BCF")
    print(f"  Gas the plan needs:    {data['gas_need_bcf']:8,.1f} BCF  "
          f"(home supply covers {data['gas_self_sufficiency_pct']:.0f}%)")

    section("SANITY CHECKS")
    ok = True
    if opt["cost_usd"] > bau["cost_usd"] * 1.001 and opt["co2_t"] > bau["co2_t"] * 1.001:
        print("  [WARN] the plan is worse than the 2024 mix on BOTH pillars"
              " -- check the weights and limits")
    total_alloc = data["allocation"]["optimal_gwh"].sum() + data["shortfall_gwh"]
    if abs(total_alloc - data["demand_gwh"]) > max(1.0, data["demand_gwh"] * 1e-6):
        print(f"  [FAIL] allocation {total_alloc:,.0f} does not sum to demand "
              f"{data['demand_gwh']:,.0f}")
        ok = False
    if (data["allocation"]["optimal_gwh"] > data["allocation"]["ceiling_gwh"] + 1.0).any():
        print("  [FAIL] some resource is drawn above its limit")
        ok = False
    dims = set(data["radar"]["dimension"])
    want = {"Cheaper power", "Lower CO₂", "Fuel from home", "Source spread",
            "Clean share", "Demand served"}
    if dims != want:
        print(f"  [FAIL] scorecard axes changed: {sorted(dims)}")
        ok = False
    else:
        print("  [OK] scorecard carries the six plain axes")
    if not data["pareto"].empty:
        po = data["pareto"]
        if po["cost_usd"].iloc[0] <= po["cost_usd"].iloc[-1]:
            print("  [OK] cost rises as the plan tilts to cleanest-first")
        else:
            print("  [WARN] the sweep's cost ordering looks inverted -- review")
        # The sweep must hand back base units (US$, t); the page converts them
        # once.  A pre-scaled column here would be multiplied a second time.
        if po["cost_usd"].max() < 1e6 or po["co2_t"].max() < 1e3:
            print("  [FAIL] the priority sweep is not in base units")
            ok = False
        else:
            print("  [OK] priority sweep returns base units (US$, t)")
    print("  All structural checks passed." if ok else "  Review the failures above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
