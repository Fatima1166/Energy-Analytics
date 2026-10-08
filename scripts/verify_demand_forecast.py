"""
scripts/verify_demand_forecast.py -- run the Q4 analysis engine against MySQL.

Standalone smoke test / audit trail for the Forecasted Energy Demand dashboard.
It calls exactly the same pipeline the page calls and prints the numbers the
dashboard will show, so the figures in a report can be reproduced without
opening the browser.

Usage (from the project root):

    .venv\\Scripts\\python.exe scripts\\verify_demand_forecast.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mysql.connector                                    # noqa: E402
from dotenv import load_dotenv                            # noqa: E402

from core import queries                                  # noqa: E402
from core.demand_forecast import build_dashboard_data     # noqa: E402

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
    data = build_dashboard_data(
        fuel_df=load(conn, queries.Q_FINAL_ENERGY_BY_SOURCE),
        re_df=load(conn, queries.Q_RENEWABLE_ENERGY),
        econ_df=load(conn, queries.Q_ECONOMIC),
        primary_df=load(conn, queries.Q_PRIMARY_SUPPLY),
        gen_df=load(conn, queries.Q_ELEC_GEN),
        gas_df=load(conn, queries.Q_NATURAL_GAS),
        sector_df=load(conn, queries.Q_ELEC_SECTOR_CONSUMPTION),
        province_df=load(conn, queries.Q_ELEC_PROVINCE_CONSUMPTION),
    )

    hist = data["history"]

    section("1. DEMAND HISTORY + DRIVERS (TOE / GWh / USD)")
    cols = [c for c in ("calendar_year", "total_final_toe", "electricity_toe",
                        "gas_toe", "elec_grid_gwh", "gdp_usd", "gdp_growth_pct",
                        "population", "gdp_per_capita") if c in hist.columns]
    print(hist[cols].to_string(index=False))

    section("2. DRIVER MODELS (elasticities, fit)")
    print(data["drivers"].to_string(index=False))

    section("3. SCENARIO ASSUMPTIONS AND ANNUAL DEMAND GROWTH")
    rows = []
    for key, grows in data["grows"].items():
        for scenario, info in grows.items():
            rows.append({"series": key, "scenario": scenario,
                         "gdp_growth_pct": info["gdp_growth_pct"],
                         "pop_growth_pct": info["population_growth_pct"],
                         "demand_growth_pct": info["demand_growth_pct"],
                         "basis": info["basis"]})
    print(pd.DataFrame(rows).to_string(index=False))

    section("4. FORECAST TO 2035 (values at the horizon)")
    forecast = data["forecast"]
    last = forecast[forecast["calendar_year"] == forecast["calendar_year"].max()]
    print(last[["series", "scenario", "calendar_year", "value",
                "anchor_year", "anchor_value"]].to_string(index=False))

    section("5. BACKTEST -- MAPE / RMSE / R2 (hold-out {}".format(
        f"{data['backtest']['train_end'] + 1}-{data['backtest']['test_end']})"))
    print(data["backtest"]["metrics"].to_string(index=False))

    section("6. GROWTH DECOMPOSITION -- total final energy (pp of annual growth)")
    print(data["decomposition"]["total_final"].round(3).to_string(index=False))

    section("7. SECTOR DEMAND -- top groups, reported vs 2035 Base (GWh)")
    sectors = data["sectors"]
    hist_sec = sectors["history"]
    base_year = sectors["base_year"]
    now = (hist_sec[hist_sec["calendar_year"] == base_year]
           .groupby("key")["value"].sum().rename("reported"))
    proj = sectors["projection"]
    proj_base = proj[(proj["scenario"] == "Base")
                     & (proj["calendar_year"] == data["horizon"])]
    future = proj_base.groupby("key")["value"].sum().rename("forecast_2035")
    table = pd.concat([now, future], axis=1)
    table["change_pct"] = (table["forecast_2035"] / table["reported"] - 1) * 100
    print(table.sort_values("reported", ascending=False).round(0).to_string())
    print(f"reported total {base_year}: {table['reported'].sum():,.0f} GWh   "
          f"2035 base total: {table['forecast_2035'].sum():,.0f} GWh")

    section("8. PROVINCE DEMAND -- reported vs 2035 Base (GWh)")
    provinces = data["provinces"]
    now_p = (provinces["history"][provinces["history"]["calendar_year"] == base_year]
             .groupby("key")["value"].sum().rename("reported"))
    future_p = (provinces["projection"][(provinces["projection"]["scenario"] == "Base")
                                        & (provinces["projection"]["calendar_year"] == data["horizon"])]
                .groupby("key")["value"].sum().rename("forecast_2035"))
    table_p = pd.concat([now_p, future_p], axis=1)
    table_p["share_2035_pct"] = table_p["forecast_2035"] / table_p["forecast_2035"].sum() * 100
    print(table_p.sort_values("reported", ascending=False).round(1).to_string())

    section("9. SUPPLY vs DEMAND GAP")
    gap_total = data["gap"]["total"]
    print(gap_total[gap_total["scenario"] == "Base"].tail(14).round(0).to_string(index=False))

    section("10. IMPORT DEPENDENCY (%, projected after the reported year)")
    print(data["gap"]["imports"].round(2).to_string(index=False))

    section("11. KPI READINGS")
    for name, reading in data["kpis"].items():
        print(f"{name:14s} {reading}")

    section("12. SANITY CHECKS")
    problems = []
    print("detected reporting-basis breaks:", data["breaks"])
    for key, model in data["models"].items():
        if model["model"] == "Trend":
            problems.append(f"{key}: driver fit unusable -> trend fallback")
        for field in ("elasticity_income", "elasticity_gdp"):
            value = model[field]
            if value != value:
                problems.append(f"{key}: {field} is NaN")
        if not -0.6 <= model["elasticity_income"] <= 2.5:
            problems.append(f"{key}: income elasticity outside the clamped band")
        if model["residual_years"] < 3:
            problems.append(f"{key}: only {model['residual_years']} residual years")

    # scenario separation must be real
    for key, grows in data["grows"].items():
        spread = abs(grows["High"]["demand_growth_pct"] - grows["Low"]["demand_growth_pct"])
        print(f"{key:18s} Low {grows['Low']['demand_growth_pct']:+.2f}%  "
              f"Base {grows['Base']['demand_growth_pct']:+.2f}%  "
              f"High {grows['High']['demand_growth_pct']:+.2f}%   spread {spread:.2f}pp")
        if spread < 0.5:
            problems.append(f"{key}: scenarios barely differ ({spread:.2f}pp)")
    if not data["gap"]["total"].empty:
        base = data["gap"]["total"]
        base = base[(base["scenario"] == "Base") & (base["calendar_year"] == data["horizon"])]
        if not base.empty and abs(float(base.iloc[0]["gap_pct"])) > 100:
            problems.append(f"horizon gap is {float(base.iloc[0]['gap_pct']):.0f}% of supply")
    mape = data["backtest"]["metrics"]
    if not mape.empty:
        worst = mape.loc[mape["mape"].idxmax()]
        print(f"worst backtest MAPE: {worst['label']} / {worst['model']} "
              f"= {worst['mape']:.2f}%   best R2 = {mape['r2'].max():.3f}")
    print("issues:", problems or "none")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
