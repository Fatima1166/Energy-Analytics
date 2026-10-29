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
    PILLARS, apply_weights, build_indicator_frame,
    build_verdict, latest_pillar_scores, project_pathways,
    select_optimal_package, snapshot_row, strategy_value_density,
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

    # -- the two rules that keep the headline number trustworthy --
    # 1. a year that reported nothing must not be read as a year of zero imports
    if "import_dep_pct" in ind.columns and "sc_security_imp_dep" in ind.columns:
        blind = ind[ind["import_dep_pct"].isna()]
        leaked = int(pd.to_numeric(blind["sc_security_imp_dep"],
                                   errors="coerce").notna().sum())
        check("unreported imports score nothing", leaked == 0 and not blind.empty,
              f"{len(blind)} year-rows without import figures ({blind['calendar_year'].min()}"
              f"-{blind['calendar_year'].max()}), {leaked} scored anyway")
    # 2. the index is only read once every pillar has appeared at least once; a
    #    pillar carrying its last value forward is allowed, a pillar that never
    #    existed is not (that is what used to lift the index as coverage decayed)
    scored = ind_w[ind_w["score_weighted"].notna()]
    ready = max(int(ind_w.loc[ind_w[f"score_{p}"].notna(), "calendar_year"].min())
                for p in PILLARS)
    early = scored[scored["calendar_year"] < ready]
    check("composite waits for all four pillars",
          bool(len(scored)) and early.empty,
          f"all four pillars known from {ready}; scored years "
          f"{scored['calendar_year'].min()}-{scored['calendar_year'].max()}, "
          f"{len(early)} scored too early")

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
    # Only the projected years (2025+) must be a well-formed finite score.  The
    # reported part of the pathway is deliberately blank for any year that did
    # not report all four pillars, so requiring those to be finite would demand
    # the very carry-forward the no-bridge rule removes.
    proj_rows = paths[~paths["is_actual"]]
    for col in ("composite_bau", "composite_announced", "composite_optimal"):
        s = pd.to_numeric(proj_rows[col], errors="coerce")
        check(f"{col} projection 0-100 & finite",
              bool(s.notna().all()) and bool(((s >= 0) & (s <= 100)).all()),
              f"at {horizon}: {hor[col]:.1f}")

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
    # The K1 card and the pathway chart must tell the same story about the same
    # year.  The card wears the latest year that had a full weighted score (the
    # no-bridge rule leaves the evaluation year blank when a pillar is missing),
    # so the chart point to compare against is that same year, not eval_year.
    snap = snapshot_row(ind_w, eval_year)
    snap_year = int(snap["calendar_year"])
    chart_rows = paths[paths["calendar_year"] == snap_year]
    if chart_rows.empty:
        start = float("nan")
    else:
        start = float(chart_rows.iloc[0]["composite_bau"])
    check("card equals the chart at the card's own year",
          np.isfinite(start) and abs(start - verdict["index_now"]) < 0.005,
          f"card {verdict['index_now']:.2f} ({snap_year}) vs chart {start:.2f}")
    pillars_now = latest_pillar_scores(ind_w, eval_year)
    check("all four pillars have a current score",
          all(np.isfinite(v) for v in pillars_now.values()),
          "  ".join(f"{p}={v:.0f}" for p, v in pillars_now.items()))

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
