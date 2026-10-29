"""scripts/verify_missing_year_blanks.py -- the "no bridge" gate.

Two independent checks that together enforce the Missing-Years rule the deck is
built on:

  A. Static fill gate.  No engine or chart may carry a value forward, interpolate
     a gap or zero-fill a reading with `.fillna(0...)`, `.ffill()`, `.bfill()` or
     `.interpolate(`.  A handful of sites are on a reviewed allow-list because
     they are *not* display fills: model drivers that only assume a rate for the
     projection window (>= 2025), text-label merges, and guards that turn a
     non-positive cell into NaN.  Anything new on the floor that is not on that
     list fails the gate, so a bridge cannot be re-introduced quietly.

  B. Projection boundary.  Every row an engine marks as modelled rather than
     actually reported must fall strictly after HISTORY_END (2024).  A projected
     figure never occupies a year inside the reported window.

Usage (from the project root, with MySQL up):

    .venv\\Scripts\\python.exe scripts\\verify_missing_year_blanks.py
"""

from __future__ import annotations

import os
import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

# HISTORY_END is the last calendar year the record can actually report.
from core.resource_allocation import HISTORY_END  # noqa: E402

# ── A. Static fill gate ──────────────────────────────────────────────────────
BRIDGE = re.compile(r"\.fillna\(|\.ffill\(|\.bfill\(|\.interpolate\(|\.pad\(")

# (relative file, a substring that identifies the reviewed line, why it is safe)
ALLOW: list[tuple[str, str, str]] = [
    ("core/supply_forecast.py", ".fillna(DEFAULT_BASE_GDP_GROWTH)",
     "GDP index chain driver: the default rate only covers projection years "
     "(>=2025) and the single pre-window anchor; it never fills a displayed "
     "supply reading, which stays NaN per history row."),
    ("core/demand_forecast.py", ".fillna(growth)",
     "Derives a missing growth rate from the reported GDP level series, i.e. a "
     "model driver, not a display value; if levels are absent it yields NaN."),
    ("core/demand_forecast.py", '.fillna(d["gas_import_dep_pct_rep"])',
     "Falls back to the SAME year's reported import-dependence when the balance "
     "derivation is empty; it never borrows another year's number."),
    ("core/demand_forecast.py", '.fillna(d["provenance_rep"])',
     "Fills a text provenance LABEL for the same row, not a number."),
    ("core/demand_forecast.py", '.fillna(merged["provenance_y"])',
     "Picks one provenance label over the other after a merge; labels only."),
    ("core/operational_bottlenecks.py", "imp.where(imp.fillna(0) > 0, np.nan)",
     "Guard that maps a non-positive or missing import to NaN -- it produces a "
     "blank, the opposite of a zero-fill."),
    ("core/sustainability_engine.py", "earlier `.ffill()`",
     "Prose in a docstring explaining why the carry was removed; not a call."),
]

SCAN_DIRS = ["core", "dashboards"]


def _allowed(rel_path: str, line: str) -> bool:
    for afile, marker, _reason in ALLOW:
        if rel_path == afile and marker in line:
            return True
    return False


def check_fill_gate() -> int:
    offenders = 0
    print("=" * 70)
    print("A.  STATIC FILL GATE  (no ffill / interpolate / zero-fill leaks)")
    print("=" * 70)
    for base in SCAN_DIRS:
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                if not BRIDGE.search(line):
                    continue
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue  # comment mentioning the pattern
                if _allowed(rel, stripped):
                    print(f"  [allow] {rel}:{lineno}")
                    continue
                print(f"  [FAIL ] {rel}:{lineno}  {stripped[:70]}")
                offenders += 1
    if offenders:
        print(f"\n  {offenders} un-reviewed bridging call(s). Rule 3 blocked.")
    else:
        print("\n  No un-reviewed bridging calls. Rule 3 holds.")
    return offenders


# ── B. Projection boundary ───────────────────────────────────────────────────
def check_projection_boundary() -> int:
    import mysql.connector
    import pandas as pd
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from core import queries
    from core.projections import project_renewable

    conn_kwargs = dict(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "energy_database_new"),
        port=int(os.getenv("DB_PORT", 3306)),
    )
    warnings.filterwarnings("ignore")
    conn = mysql.connector.connect(**conn_kwargs)
    try:
        re_df = pd.read_sql(queries.Q_RENEWABLE_ENERGY, conn)
    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("B.  PROJECTION BOUNDARY  (modelled rows live strictly after 2024)")
    print("=" * 70)

    offenders = 0
    for scenario in ("Conservative", "Base", "Accelerated"):
        proj = project_renewable(re_df, scenario=scenario, end_year=2035)
        # "Projected" rows are the model's own; "Missing" rows are in-window
        # history years that simply had no reading, which is the blank case we
        # WANT -- only a genuine projection may not occupy a year <= 2024.
        modelled = proj[proj["data_type"] == "Projected"]
        if modelled.empty:
            print(f"  [{scenario:12s}] no projected rows")
            continue
        min_year = int(modelled["calendar_year"].min())
        bad = modelled[modelled["calendar_year"] <= HISTORY_END]
        ok = min_year > HISTORY_END and bad.empty
        offenders += len(bad)
        flag = "OK  " if ok else "FAIL"
        print(f"  [{flag}] {scenario:12s}: modelled rows from {min_year} "
              f"(must be > {HISTORY_END}); in-window rows = {len(bad)}")
    return offenders


def main() -> int:
    failures = check_fill_gate() + check_projection_boundary()
    print("\n" + "=" * 70)
    if failures:
        print(f"GATE FAILED: {failures} violation(s).")
        return 1
    print("GATE PASSED: missing years stay blank, nothing bridges into them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
