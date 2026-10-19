"""
scripts/verify_q8_strategy.py -- standalone audit of the Q8 sustainability
engine against the live MySQL warehouse (no Streamlit rendering).

Run:  .venv\\Scripts\\python.exe scripts\\verify_q8_strategy.py
Exits non-zero if any structural invariant fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from config.database import run_query
from core.queries import (
    Q_ECONOMIC, Q_ELEC_GEN, Q_LNG, Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY, Q_RENEWABLE_ENERGY, Q_TD_LOSSES,
)
from core.sustainability_engine import (
    PILLARS, PILLAR_LABELS, apply_weights, build_indicator_frame,
    build_verdict, latest_pillar_scores, project_pathways,
    select_optimal_package, strategy_value_density,
)
from dashboards.q8_sustainable_strategy.config import STRATEGY_LIBRARY

FAILS: list[str] = []
WARNS: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    ind = build_indicator_frame(
        re_df=run_query(Q_RENEWABLE_ENERGY),
        gen_df=run_query(Q_ELEC_GEN),
        td_df=run_query(Q_TD_LOSSES),
        ps_df=run_query(Q_PRIMARY_SUPPLY),
        gas_df=run_query(Q_NATURAL_GAS),
        lng_df=run_query(Q_LNG),
        econ_df=run_query(Q_ECONOMIC),
    )
    check("indicator frame built", ind is not None and not ind.empty,
          f"{len(ind)} year-rows" if ind is not None else "None")
    if ind.empty:
        print("Nothing to verify.")
        return 1

    print(ind[["calendar_year"] + [f"score_{p}" for p in PILLARS]
              + ["score_composite"]].to_string(index=False))

    # scores must live inside 0-100 wherever present
    for p in PILLARS:
        s = pd.to_numeric(ind[f"score_{p}"], errors="coerce").dropna()
        check(f"score_{p} within 0-100",
              bool(((s >= 0) & (s <= 100)).all()) and len(s) > 0,
              f"n={len(s)}, range [{s.min():.1f}, {s.max():.1f}]")

    weights = {"security": 0.3, "economy": 0.25,
               "environment": 0.25, "access": 0.2}
    ind_w = apply_weights(ind, weights)
    comp = pd.to_numeric(ind_w["score_weighted"], errors="coerce").dropna()
    check("weighted composite present", len(comp) > 0,
          f"n={len(comp)}, latest={comp.iloc[-1]:.1f}")

    # ---- optimiser ----
    ranked = strategy_value_density(STRATEGY_LIBRARY, weights)
    check("ranking densest-first",
          bool((ranked["density"].diff().dropna() <= 1e-9).all()),
          f"top={ranked.iloc[0]['name']!r} density={ranked.iloc[0]['density']:.2f}")

    budget = 8.0
    pkg = select_optimal_package(STRATEGY_LIBRARY, weights, budget)
    check("package within budget", pkg["committed_bn"] <= budget + 1e-9,
          f"committed {pkg['committed_bn']:.1f} of {budget:.1f}, "
          f"{len(pkg['chosen'])} strategies chosen")
    check("package non-empty", len(pkg["chosen"]) > 0,
          ", ".join(c["short"] for c in pkg["chosen"][:4]) + " ...")

    # ---- pathways ----
    eval_year, horizon = 2024, 2035
    paths = project_pathways(ind_w, weights, pkg, eval_year, horizon,
                             STRATEGY_LIBRARY)
    check("pathways cover to horizon",
          not paths.empty and int(paths["calendar_year"].max()) >= horizon)
    hor = paths[paths["calendar_year"] == horizon].iloc[0]
    for col in ("composite_bau", "composite_announced", "composite_optimal"):
        s = pd.to_numeric(paths[col], errors="coerce")
        check(f"{col} 0-100 & finite",
              bool(s.notna().all()) and bool(((s >= 0) & (s <= 100)).all()),
              f"at {horizon}: {s.iloc[-1]:.1f}")

    check("optimal >= announced >= bau at horizon",
          hor["composite_optimal"] >= hor["composite_announced"] >= hor["composite_bau"] - 1e-9,
          f"{hor['composite_bau']:.1f} <= {hor['composite_announced']:.1f} <= {hor['composite_optimal']:.1f}")
    flag_ok = bool((paths[paths["is_actual"]]["calendar_year"] <= eval_year).all()
                   and (paths[~paths["is_actual"]]["calendar_year"] > eval_year).all())
    check("history/projection split at eval year", flag_ok,
          f"actual rows end {paths[paths['is_actual']]['calendar_year'].max()}")

    verdict = build_verdict(ind_w, weights, pkg, paths, eval_year, horizon)
    check("verdict synthesized", bool(verdict),
          f"index {verdict.get('index_now', float('nan')):.1f} -> "
          f"{verdict.get('index_optimal', float('nan')):.1f} "
          f"(BAU {verdict.get('index_bau', float('nan')):.1f}), "
          f"gain {verdict.get('gap_vs_bau', float('nan')):+.1f} pts")
    pillars_now = latest_pillar_scores(ind_w, eval_year)
    check("all four pillars have a current score",
          all(np.isfinite(v) for v in pillars_now.values()),
          "  ".join(f"{PILLAR_LABELS[p].split()[0]}={v:.0f}"
                    for p, v in pillars_now.items()))

    print()
    if WARNS:
        print("WARNINGS:", *WARNS, sep="\n  - ")
    if FAILS:
        print(f"{len(FAILS)} CHECK(S) FAILED")
        return 1
    print("All structural checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
