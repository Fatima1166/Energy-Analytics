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
from core.resource_allocation import HORIZON, build_allocation_data

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
        sector_df=load(conn, queries.Q_ELEC_SECTOR_CONSUMPTION),
        ef_df=load(conn, queries.Q_EMISSION_FACTORS),
    )
    conn.close()

    opt, bau = data["opt_score"], data["bau_score"]

    section("Q10 REQUIREMENT")
    print(f"2024 generation base:    {data['total_2024_gwh']:14,.0f} GWh")
    print(f"Horizon {HORIZON} requirement:  {data['demand_gwh']:14,.0f} GWh  "
          f"(x{data['demand_gwh'] / max(data['total_2024_gwh'], 1):.2f})")

    section("OPTIMAL ALLOCATION vs BAU (GWh)")
    for _, r in data["allocation"].iterrows():
        clamp = "  ◤ clamped at ceiling" if r["clamped"] else ""
        print(f"  {r['technology']:<9} optimal={r['optimal_gwh']:12,.0f}   "
              f"bau={r['bau_gwh']:12,.0f}   ceiling={r['ceiling_gwh']:12,.0f}{clamp}")
    print(f"  Shortfall: {data['shortfall_gwh']:,.0f} GWh  "
          f"(coverage {opt['coverage_pct']:.1f}%)")

    section("KPI PAIRS (optimal vs BAU)")
    print(f"  Cost  bn USD:  {opt['cost_usd']/1e9:10,.2f}  vs BAU {bau['cost_usd']/1e9:10,.2f}")
    print(f"  CO2       Mt:  {opt['co2_t']/1e6:10,.1f}  vs BAU {bau['co2_t']/1e6:10,.1f}")
    print(f"  Import dep %:  {opt['import_dep_pct']:10,.1f}  vs BAU {bau['import_dep_pct']:10,.1f}")
    print(f"  RE share    %:  {opt['re_share_pct']:10,.1f}  vs BAU {bau['re_share_pct']:10,.1f}")

    section("PARETO ENDPOINTS")
    p = data["pareto"]
    print(f"  Pure cost  : {p['cost_bn'].min():8,.2f} bn USD at "
          f"{p.loc[p['cost_bn'].idxmin(), 'co2_mt']:8,.1f} Mt")
    print(f"  Pure carbon: {p.loc[p['co2_mt'].idxmin(), 'cost_bn']:8,.2f} bn USD at "
          f"{p['co2_mt'].min():8,.1f} Mt")

    section("GAS FEASIBILITY & SECTORS")
    print(f"  Domestic gas planning cap: {data['domestic_gas_bcf']:8,.1f} BCF")
    print(f"  Gas run needed:            {data['gas_need_bcf']:8,.1f} BCF  "
          f"(self-sufficiency {data['gas_self_sufficiency_pct']:.0f}%)")
    if not data["sectors"].empty:
        for _, r in data["sectors"].iterrows():
            print(f"  sector {r['sector']:<22} {r['demand_gwh']:12,.0f} GWh "
                  f"({r['share_pct']:5.1f}%)")
    else:
        print("  (no sector dimension returned)")

    section("SANITY CHECKS")
    ok = True
    if opt["cost_usd"] > bau["cost_usd"] * 1.001 and opt["co2_t"] > bau["co2_t"] * 1.001:
        print("  [WARN] optimal is worse than BAU on BOTH pillars -- check weights/ceilings")
    total_alloc = data["allocation"]["optimal_gwh"].sum() + data["shortfall_gwh"]
    if abs(total_alloc - data["demand_gwh"]) > max(1.0, data["demand_gwh"] * 1e-6):
        print(f"  [FAIL] allocation {total_alloc:,.0f} does not sum to demand "
              f"{data['demand_gwh']:,.0f}")
        ok = False
    if (data["allocation"]["optimal_gwh"] > data["allocation"]["ceiling_gwh"] + 1.0).any():
        print("  [FAIL] some technology exceeds its resource ceiling")
        ok = False
    if not data["pareto"].empty:
        po = data["pareto"]
        if po["cost_bn"].iloc[0] <= po["cost_bn"].iloc[-1]:
            print("  [OK] frontier cost rises as theta shifts to pure carbon")
        else:
            print("  [WARN] frontier cost ordering looks inverted -- review")
    print("  All structural checks passed." if ok else "  Review the failures above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
