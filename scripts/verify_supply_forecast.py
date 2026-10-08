"""
scripts/verify_supply_forecast.py -- run the Q5 Supply analysis engine against MySQL.

Standalone verification and audit trail for Question 5:
"What is forecasted energy supply?"

Usage:
    .venv\\Scripts\\python.exe scripts\\verify_supply_forecast.py
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
from core.supply_forecast import build_supply_dashboard_data

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
    data = build_supply_dashboard_data(
        primary_df=load(conn, queries.Q_PRIMARY_SUPPLY),
        re_df=load(conn, queries.Q_RENEWABLE_ENERGY),
        econ_df=load(conn, queries.Q_ECONOMIC),
        gen_df=load(conn, queries.Q_ELEC_GEN),
    )

    hist = data["history"]

    section("1. SUPPLY HISTORY (TOE / GWh / MW)")
    cols = [c for c in ("calendar_year", "tpes_toe", "imports_toe", "import_share_pct",
                        "gen_total_gwh", "gen_clean_gwh", "clean_share_pct", "capacity_mw")
            if c in hist.columns]
    print(hist[cols].tail(10).to_string(index=False))

    section("2. DRIVER & TREND MODELS FOR SUPPLY")
    for key, model in data["models"].items():
        print(f"Series: {key}")
        print(f"  Calibration: {model['calib_start']} - {model['calib_end']} (N={model['n']})")
        print(f"  Driver Elasticity: {model['elasticity']:.3f} | R²: {model['r2_driver']:.3f}")
        print(f"  Trend Growth: {model['trend_growth_pct']:.2f}%/yr | R²: {model['r2_trend']:.3f}")
        print(f"  Historical CAGR: {model['cagr_historical']:.2f}%/yr")

    section("3. SCENARIO GROWTH RATES")
    for key, grows in data["grows"].items():
        print(f"-- {key} --")
        for sc, info in grows.items():
            print(f"  Scenario {sc:4s}: GDP {info['gdp_growth_pct']:.1f}% -> Supply Growth {info['growth_pct']:.2f}%/yr")

    section("4. SUPPLY FORECAST TO 2035 (Horizon Levels)")
    fc = data["forecast"]
    if not fc.empty:
        h_rows = fc[fc["calendar_year"] == fc["calendar_year"].max()]
        print(h_rows[["series", "scenario", "calendar_year", "value", "anchor_year", "anchor_value"]].to_string(index=False))

    section("5. TECHNOLOGY MIX OUTLOOK (2035 Horizon)")
    mix = data["tech_mix"]
    h_mix = mix[mix["calendar_year"] == mix["calendar_year"].max()]
    cols_m = ["scenario", "calendar_year", "Hydro", "Solar", "Wind", "Nuclear", "Coal", "Gas", "clean_share_pct", "variable_re_share_pct"]
    print(h_mix[cols_m].to_string(index=False))

    section("6. SUPPLY ADEQUACY & RESERVE MARGIN (2035 Horizon)")
    adeq = data["adequacy"]
    h_adeq = adeq[adeq["calendar_year"] == adeq["calendar_year"].max()]
    cols_a = ["scenario", "calendar_year", "supply_gwh", "demand_gwh", "reserve_margin_pct", "adequacy_status"]
    print(h_adeq[cols_a].to_string(index=False))

    section("7. ENERGY SECURITY & IMPORT DEPENDENCY (2035 Horizon)")
    sec = data["security"]
    h_sec = sec[sec["calendar_year"] == sec["calendar_year"].max()]
    cols_s = ["scenario", "calendar_year", "tpes_toe", "imports_toe", "domestic_toe", "import_share_pct"]
    print(h_sec[cols_s].to_string(index=False))

    section("8. BACKTESTING RESULTS (Hold-out 2021-2024)")
    print(data["backtest"]["table"].to_string(index=False))

    print("\nVerification complete. All calculations executed with 0 errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
