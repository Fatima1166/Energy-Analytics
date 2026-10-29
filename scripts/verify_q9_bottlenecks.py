"""scripts/verify_q9_bottlenecks.py -- headless check of the Q9 bottleneck engine + charts.

Pulls the real query frames from MySQL, runs core.operational_bottlenecks
end-to-end and builds every visual from dashboards.q9_operational_bottlenecks.charts.
"""

import os
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from core.operational_bottlenecks import (
    aggregate_by_family,
    build_bottleneck_frame,
    score_bottlenecks,
    snapshot_metrics,
)
from core.queries import (
    Q_ELEC_GEN,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_CAPACITY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.units import display_factor
from dashboards.q9_operational_bottlenecks.charts import (
    visual1_severity_scorecard,
    visual2_capacity_factor_trend,
    visual3_capability_gap,
    visual4_gas_supply_gap,
)


def main() -> int:
    conn_kwargs = dict(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "energy_database_new"),
        port=int(os.getenv("DB_PORT", 3306)),
    )

    def _q(sql):
        warnings.filterwarnings("ignore")
        return pd.read_sql(sql, mysql.connector.connect(**conn_kwargs))

    df = build_bottleneck_frame(
        gen_df=_q(Q_ELEC_GEN),
        re_df=_q(Q_RENEWABLE_ENERGY),
        re_cap_df=_q(Q_RENEWABLE_CAPACITY),
        td_df=_q(Q_TD_LOSSES),
        gas_df=_q(Q_NATURAL_GAS),
        ps_df=_q(Q_PRIMARY_SUPPLY),
    )
    assert not df.empty, "empty bottleneck frame"

    base_year = 2024
    print(f"years           : {int(df.calendar_year.min())}-{int(df.calendar_year.max())}")

    snap = snapshot_metrics(df, base_year)
    print(f"{base_year} load factor  : {snap['sys_load_factor_pct']:.1f}%  "
          f"(read {snap['sys_load_factor_pct_year']})")
    print(f"{base_year} fossil CF   : {snap['fossil_cf_pct']:.1f}%  "
          f"(read {snap['fossil_cf_pct_year']})")
    print(f"{base_year} RE CF       : {snap['re_cf_pct']:.1f}%  "
          f"(read {snap['re_cf_pct_year']})")
    print(f"{base_year} gas self-suf: {snap['gas_self_suff_pct']:.1f}%  "
          f"gap {snap['gas_gap_bcf']:.1f} BCF  "
          f"(read {snap['gas_self_suff_pct_year']})")
    print(f"{base_year} T&D loss    : {snap['td_loss_pct']:.1f}%  "
          f"(read {snap['td_loss_pct_year']})")
    print(f"{base_year} import dep  : {snap['fossil_import_dep_pct']:.1f}%  "
          f"(read {snap['fossil_import_dep_pct_year']})")

    sc = score_bottlenecks(df, base_year)
    assert not sc.empty, "empty scorecard"
    print("\nBottleneck scorecard (ranked):")
    for _, r in sc.iterrows():
        print(f"  [{r['family']:<9s}] {r['severity']:5.0f}  {r['name']:<24s} "
              f"{r['reading']:<24s} {r['obs_year']}")

    fam = aggregate_by_family(sc)
    print("\nMean severity by family:",
          {k: (round(v) if v == v else None) for k, v in fam.items()})

    factor_elec = display_factor("electricity", "GWh")
    factor_gas = display_factor("gas", "BCF")

    figs = [
        visual1_severity_scorecard(sc),
        visual2_capacity_factor_trend(df),
        visual3_capability_gap(df, factor_elec, "GWh"),
        visual4_gas_supply_gap(df, factor_gas, "BCF"),
    ]
    for i, f in enumerate(figs, 1):
        n = len(f.data)
        assert n > 0, f"visual{i} has no traces"
        print(f"visual{i}           : {n} traces OK")

    # sanity: severities bounded 0-100 where finite
    fin = sc["severity"].dropna()
    assert ((fin >= 0) & (fin <= 100)).all(), "severity out of band"
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
