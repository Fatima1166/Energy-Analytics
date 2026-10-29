"""
scripts/verify_q7_cost.py -- run the Q7 power-producer cost engine against MySQL.

Standalone verification and audit trail for Question 7:
"What is the forecasted cost of energy power producers?"

Usage:
    .venv\\Scripts\\python.exe scripts\\verify_q7_cost.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mysql.connector
from dotenv import load_dotenv

from core import queries
from core.cost_forecast import (
    COST_SCENARIO_ORDER,
    COST_TECHS,
    HISTORY_END,
    HORIZON,
    build_cost_dashboard_data,
)

load_dotenv(ROOT / ".env")

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)

BN = 1e9  # USD -> USD bn for printing


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
    data = build_cost_dashboard_data(
        re_df=load(conn, queries.Q_RENEWABLE_ENERGY),
        econ_df=load(conn, queries.Q_ECONOMIC),
        gen_df=load(conn, queries.Q_ELEC_GEN),
        lng_df=load(conn, queries.Q_LNG),
    )
    conn.close()

    hist, fc = data["history"], data["forecast"]

    section("THE THREE CARDS")
    last = hist.iloc[-1]
    print(f"Paid to producers {HISTORY_END}:   {last['cost_total_usd']/BN:12,.2f} USD bn")
    print(f"Average price paid {HISTORY_END}:   {last['avg_usd_per_mwh']:12,.1f} US$/MWh")
    print(f"Fuel part of the bill:         {last['fuel_cost_share_pct']:12,.1f} %")

    section(f"THE BILL IT POINTS TO BY {HORIZON} (USD bn)")
    for sc in COST_SCENARIO_ORDER:
        row = fc[(fc["scenario"] == sc) & (fc["calendar_year"] == HORIZON)]
        if row.empty:
            continue
        r = row.iloc[0]
        print(f"{sc:<12} cost={r['cost_total_usd']/BN:>10,.2f}   "
              f"avg={r['avg_usd_per_mwh']:>6,.1f} US$/MWh   "
              f"RE share={r['re_share_pct']:>5,.1f}%")

    section(f"WHERE THE MONEY GOES -- each source, {HISTORY_END} paid vs {HORIZON} planned")
    ref_row = fc[(fc["scenario"] == "Reference") & (fc["calendar_year"] == HORIZON)]
    if ref_row.empty:
        print("  (empty -- the planned build-out case was not drawn)")
    else:
        ref_row = ref_row.iloc[0]
        for tech in COST_TECHS:
            key = tech.lower().replace(" ", "")
            now = float(last[f"cost_{key}_usd"])
            then = float(ref_row[f"cost_{key}_usd"])
            print(f"  {tech:<10} {now/BN:>9,.2f} -> {then/BN:>9,.2f} USD bn  "
                  f"({(then - now)/BN:+.2f})")

    section("IF FUEL PRICES RISE FASTER OR SLOWER (planned build-out, USD bn)")
    sens = data["sensitivity"]
    if not sens.empty:
        row = sens[sens["calendar_year"] == HORIZON]
        if row.empty:
            row = sens.iloc[[-1]]
        for c in [c for c in sens.columns if c != "calendar_year"]:
            print(f"  {c.replace('cost_', '').replace('_usd', ''):<14} {row.iloc[0][c]/BN:>10,.2f}")

    section("HOW FAR THE MODEL MISSES (2021-2024, years it had not been shown)")
    bt = data["backtest"]["table"]
    if bt.empty:
        print("  (insufficient data)")
    else:
        for _, r in bt.iterrows():
            win = " <- winner" if r["is_winner"] else ""
            print(f"  {r['model']:<12} MAPE={r['mape_pct']:6.2f}%  "
                  f"Bias={r['bias_pct']:+6.2f}%{win}")

    section("SANITY CHECKS")
    ok = True
    book = fc[fc["calendar_year"] == HORIZON].set_index("scenario")["cost_total_usd"]
    if {"Minimum RE", "RE 50%"} <= set(book.index) and book["RE 50%"] >= book["Minimum RE"]:
        print("  [FAIL] Half clean power bill should be the cheaper one")
        ok = False
    if last["cost_total_usd"] <= 0:
        print("  [FAIL] non-positive reported cost bill")
        ok = False
    if hist["avg_usd_per_mwh"].min() < 15.0:
        print("  [FAIL] blended price fell below the unit-cost floor")
        ok = False
    # A source the record never reported carries no cost: it reads blank (NaN)
    # under the no-bridge rule, which is correct.  Only a genuine non-zero cost
    # attributed to it would be wrong.
    _other_re_cost = float(last["cost_otherre_usd"])
    if not pd.isna(_other_re_cost) and _other_re_cost != 0.0:
        print("  [FAIL] cost charged to a source the record never reported")
        ok = False
    print("  All sanity checks passed." if ok else "  Review the failures above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
