"""
scripts/verify_q1_relationships.py -- run the Q1 relationship / what-if engine
against MySQL.

Standalone verification and audit trail for Question 1:
"What have been the relationships among different parameters of energy over a
given period of time? What are the predicted values of these parameters based
on the what-if analysis?"

Usage:
    .venv\\Scripts\\python.exe scripts\\verify_q1_relationships.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import mysql.connector
from dotenv import load_dotenv

from core import queries
from core.parameter_relationships import (
    PARAMETERS, build_relationship_data,
)

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
    data = build_relationship_data(
        econ_df=load(conn, queries.Q_ECONOMIC),
        re_df=load(conn, queries.Q_RENEWABLE_ENERGY),
        gen_df=load(conn, queries.Q_ELEC_GEN),
        td_df=load(conn, queries.Q_TD_LOSSES),
        gas_df=load(conn, queries.Q_NATURAL_GAS),
        lng_df=load(conn, queries.Q_LNG),
        overview_df=load(conn, queries.Q_ENERGY_OVERVIEW),
    )
    conn.close()

    frame, corr, fc = data["frame"], data["corr"], data["forecasts"]

    section("Q1 PARAMETER FRAME")
    years = frame["calendar_year"]
    print(f"  Years: {int(years.min())}..{int(years.max())}   rows: {len(frame)}")
    for key, meta in PARAMETERS.items():
        if key in frame:
            n = int(frame[key].notna().sum())
            print(f"  {meta['label']:<32} obs={n:4d}   "
                  f"last={frame.dropna(subset=[key])[key].iloc[-1] if n else float('nan'):14,.1f} "
                  f"({meta['unit']})")

    section("CORRELATION WEB (2002-2024)")
    if data["strongest"]:
        a, b, r = data["strongest"]
        print(f"  Strongest pair: {PARAMETERS[a]['label']} x "
              f"{PARAMETERS[b]['label']}  r = {r:+.3f}")
    n_cells = int(corr.notna().sum().sum() // 2)
    strong = int((corr.where(~np.eye(len(corr), dtype=bool)).abs() >= 0.7
                  ).sum().sum() // 2)
    print(f"  Computable pairs: {n_cells}   strong (|r|>=0.7): {strong}")

    fit = data["fit"]
    section("PAIR EXPLORER (GDP x Electricity Demand)")
    print(f"  n={fit['n']}  r={fit['r']:+.3f}  R2={fit['r2']:.3f}  "
          f"slope={fit['slope']:,.3f}" if np.isfinite(fit.get("r", np.nan))
          else "  (not enough joint observations)")

    section("WHAT-IF FORECASTS (baseline = historic CAGR; case: GDP 4.0%/"
            "Pop 1.9%/Eff 0.0%)")
    for _, r_ in fc.iterrows():
        print(f"  {r_['label']:<32} {int(r_['last_year'])}={r_['last_value']:14,.1f}  "
              f"CAGR={r_['cagr_pct']:+6.1f}%  bG={r_['b_gdp']:5.2f} bP={r_['b_pop']:5.2f}  "
              f"base={r_['baseline_value']:14,.1f}  what={r_['whatif_value']:14,.1f}  "
              f"d={r_['delta_pct']:+6.1f}%")

    section("SANITY CHECKS")
    ok = True
    if frame.empty:
        print("  [FAIL] parameter frame is empty")
        ok = False
    if n_cells == 0:
        print("  [FAIL] no correlations computable")
        ok = False
    if fc.empty:
        print("  [FAIL] no forecasts produced")
        ok = False
    # baseline must reproduce CAGR: value*(1+cagr)^span
    for _, r_ in fc.iterrows():
        span = int(data["horizon"] - r_["last_year"])
        expect = r_["last_value"] * (1.0 + r_["cagr_pct"] / 100.0) ** span
        if abs(expect - r_["baseline_value"]) > max(1e-6, abs(expect) * 1e-6):
            print(f"  [FAIL] baseline drift on {r_['label']}")
            ok = False
            break
    # GDP what-if at its own slider rate must equal last*(1+g)^span
    gdp_row = fc[fc["key"] == "gdp"]
    if not gdp_row.empty:
        r_ = gdp_row.iloc[0]
        span = int(data["horizon"] - r_["last_year"])
        expect = r_["last_value"] * 1.04 ** span
        rel = abs(expect - r_["whatif_value"]) / expect
        if rel > 0.02:
            print(f"  [WARN] GDP what-if off by {rel:.1%} (elasticity clamp?)")
    print("  All structural checks passed." if ok else "  Review the failures above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
