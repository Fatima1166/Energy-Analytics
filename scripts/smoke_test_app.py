"""
scripts/smoke_test_app.py -- headless smoke test of every dashboard.

Runs the Streamlit app with ``streamlit.testing.v1.AppTest`` and switches the
sidebar radio through all registered dashboards, failing loudly on any
exception.  This is the check that catches import errors, bad Plotly calls and
missing session state without opening a browser.

Usage (from the project root):

    .venv\\Scripts\\python.exe scripts\\smoke_test_app.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Streamlit writes session temp files under %TEMP%; point that inside the
# project so the run works under a confined sandbox and cleans up after itself.
_TMP = ROOT / ".tmp"
_TMP.mkdir(exist_ok=True)
os.environ["TMP"] = os.environ["TEMP"] = str(_TMP)
tempfile.tempdir = str(_TMP)

# The page prints arrows and check marks; a cp1252 console would raise on them.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):   # pragma: no cover - non-TextIO stream
        pass

from streamlit.testing.v1 import AppTest          # noqa: E402

from dashboards.registry import DASHBOARDS        # noqa: E402


def describe(at: AppTest) -> str:
    bits = []
    for kind in ("error", "warning", "exception"):
        for element in getattr(at, kind, []):
            value = getattr(element, "value", element)
            bits.append(f"{kind}: {value}")
    return " | ".join(bits)


def main() -> int:
    failures = 0
    for dashboard in DASHBOARDS:
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=300)
        at.run()
        if at.exception:
            print(f"[FAIL] {dashboard['label']}: app did not start -> {describe(at)}")
            failures += 1
            continue

        if len(at.sidebar.selectbox) > 0:
            nav = at.sidebar.selectbox[0]
        else:
            nav = at.sidebar.radio[0]
        nav.set_value(dashboard["label"]).run()

        if at.exception:
            print(f"[FAIL] {dashboard['label']}: {describe(at)}")
            failures += 1
            continue

        errors = describe(at)
        status = "OK  " if not errors else "WARN"
        print(f"[{status}] {dashboard['label']:22s} "
              f"markdown={len(at.markdown):3d} sliders={len(at.sidebar.slider):2d} "
              f"selectboxes={len(at.sidebar.selectbox):2d} dataframe={len(at.dataframe)}")
        if errors:
            print(f"        {errors}")

        if dashboard["key"] in ("q4", "q5"):
            print(f"\n--- KPI cards ({dashboard['label']}) ---")
            for block in at.markdown[:5]:
                text = " ".join(str(block.value).split())
                print("   ", text[:150])
            print("\n--- reliability table ---")
            for frame in at.dataframe:
                print(frame.value.to_string(index=False))
            print()

    print("\nAll dashboards rendered with no exception." if not failures
          else f"\n{failures} dashboard(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    # Skip interpreter-exit cleanup: the last Streamlit temp directory cannot be
    # removed under a confined Windows sandbox (os.chmod denied), and that
    # PermissionError would otherwise overwrite this script's exit code.
    os._exit(exit_code)
