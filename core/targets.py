"""
core/targets.py -- benchmark targets for the bottleneck analysis.

The authoritative source is the database table ``dim_target``.  A small
POLICY_OVERRIDES map lets an official policy value win over the data-derived
"historical best" value that ``dim_target`` stores for most metrics.

Every metric carries a ``direction``:
    "lower"  -> being BELOW the target is good   (losses, import dependence)
    "higher" -> being ABOVE the target is good   (RE share, gas self-sufficiency)

``gap`` is always reported as **favourable-positive**:
    gap > 0  -> the target is met (surplus / head-room)
    gap < 0  -> the target is missed by |gap|
so a single rule works for both directions and the KPI cards can never show a
"green" badge for a missed target.
"""

from __future__ import annotations

import pandas as pd

# ── Policy targets that should beat the data-derived value in dim_target ──────
# ARE Policy 2019 sets a 30% renewable share target for 2030.
POLICY_OVERRIDES = {
    "re_share_pct": {
        "target": 30.0,
        "label": "Renewable Share %",
        "direction": "higher",
        "unit": "%",
        "source": "ARE Policy 2019 (official)",
        "notes": "30% renewable share target",
    },
}

# ── Which metric feeds which KPI, plus its dashboard metadata ────────────────
KPI_SPEC = [
    {
        "key": "losses_pct",
        "target_metric": "losses_pct",
        "code": "K1",
        "title": "Energy Losses % of Supply",
        "short": "Losses",
        "color": "#EF4444",
        "icon": "fa-droplet-slash",
        "direction": "lower",
        "formula": "total_losses_toe / total_primary_supply_toe x 100",
        "area": "Transmission, distribution & transformation losses",
    },
    {
        "key": "import_dependence",
        "target_metric": "import_pct",
        "code": "K2",
        "title": "Import Dependence %",
        "short": "Import Dep.",
        "color": "#F59E0B",
        "icon": "fa-ship",
        "direction": "lower",
        "formula": "(LNG Imports + Imported Electricity) / total primary supply x 100",
        "area": "Exposure to imported fuel & electricity",
    },
    {
        "key": "renewable_share",
        "target_metric": "re_share_pct",
        "code": "K3",
        "title": "Renewable Share %",
        "short": "Renewable Share",
        "color": "#10B981",
        "icon": "fa-leaf",
        "direction": "higher",
        "formula": "(solar+wind+hydro+other) / total generation x 100",
        "area": "Clean-generation build-out",
    },
    {
        "key": "gas_self_sufficiency",
        "target_metric": "gas_self_suff_pct",
        "code": "K4",
        "title": "Gas Self-Sufficiency %",
        "short": "Gas Self-Suff.",
        "color": "#00A6FB",
        "icon": "fa-fire-flame-curved",
        "direction": "higher",
        "formula": "production_bcf / consumption_bcf x 100",
        "area": "Domestic gas adequacy",
    },
]

# Used when the database is unreachable so the dashboard still renders.
FALLBACK_TARGETS = {
    "losses_pct":          {"target": 28.23,  "label": "Energy Losses % of Supply",
                            "direction": "lower",  "unit": "%",
                            "source": "Historical best (2019-20)", "notes": "fallback"},
    "td_losses_pct":       {"target": 1.66,   "label": "T&D Losses %",
                            "direction": "lower",  "unit": "%",
                            "source": "Historical best (2018-19)", "notes": "fallback"},
    "import_pct":          {"target": 10.77,  "label": "Import Dependence %",
                            "direction": "lower",  "unit": "%",
                            "source": "Historical best (2018)", "notes": "fallback"},
    "gas_self_suff_pct":   {"target": 122.37, "label": "Gas Self-Sufficiency %",
                            "direction": "higher", "unit": "%",
                            "source": "Historical best (2013-14)", "notes": "fallback"},
    "re_share_pct":        {"target": 30.0,   "label": "Renewable Share %",
                            "direction": "higher", "unit": "%",
                            "source": "ARE Policy 2019 (official)", "notes": "fallback"},
    "capacity_util_pct":   {"target": 57.83,  "label": "Power Capacity Utilisation %",
                            "direction": "higher", "unit": "%",
                            "source": "Historical best (2006-07)", "notes": "fallback"},
}

Q_TARGETS = """
SELECT metric, metric_label, target_value, best_year, direction, unit, source, notes
FROM dim_target
ORDER BY metric
"""

_DIRECTION_WORDS = {
    "lower_better": "lower",
    "higher_better": "higher",
    "lower": "lower",
    "higher": "higher",
}


def _direction_from_db(direction: str, metric: str) -> str:
    """Map dim_target.direction onto our 'lower'/'higher' vocabulary."""
    key = str(direction or "").strip().lower()
    if key in _DIRECTION_WORDS:
        return _DIRECTION_WORDS[key]
    # Sensible default for the known bottleneck metrics.
    return "higher" if metric in ("gas_self_suff_pct", "re_share_pct",
                                 "capacity_util_pct") else "lower"


def fallback_targets() -> dict:
    """A private copy of the built-in benchmarks."""
    return {k: dict(v) for k, v in FALLBACK_TARGETS.items()}


def load_targets() -> dict:
    """
    Return ``{metric: {target, label, direction, unit, source, notes, best_year}}``.

    Reads ``dim_target`` and overlays ``POLICY_OVERRIDES``.  Falls back to the
    built-in table if the query fails, so the dashboard never dies on a missing
    benchmark row.
    """
    targets = fallback_targets()

    try:
        from config.database import run_query

        df = run_query(Q_TARGETS)
    except Exception:
        return targets

    if df is None or df.empty:
        return targets

    for _, row in df.iterrows():
        metric = str(row.get("metric") or "").strip()
        if not metric:
            continue
        try:
            value = float(row.get("target_value"))
        except (TypeError, ValueError):
            continue
        if value != value:          # NaN
            continue

        targets[metric] = {
            "target": value,
            "label": str(row.get("metric_label") or metric),
            "direction": _direction_from_db(row.get("direction"), metric),
            "unit": str(row.get("unit") or "%"),
            "source": str(row.get("source") or "dim_target"),
            "notes": str(row.get("notes") or ""),
            "best_year": str(row.get("best_year") or ""),
        }

    # Official policy values win over the data-derived ones.
    for metric, override in POLICY_OVERRIDES.items():
        merged = dict(targets.get(metric, {}))
        merged.update(override)
        targets[metric] = merged

    return targets


def target_for(targets: dict, metric: str) -> dict:
    """One benchmark record, never None."""
    if targets and metric in targets:
        return targets[metric]
    return fallback_targets().get(
        metric, {"target": 0.0, "label": metric, "direction": "lower",
                 "unit": "%", "source": "n/a", "notes": ""})


def signed_gap(actual: float, target: float, direction: str) -> float:
    """
    Favourable-positive gap in the metric's own unit.

    lower-better  : target - actual   (actual below target -> positive)
    higher-better : actual - target   (actual above target -> positive)
    """
    if actual is None or target is None:
        return 0.0
    if str(direction).lower() == "lower":
        return float(target) - float(actual)
    return float(actual) - float(target)


def achievement_pct(actual: float, target: float, direction: str) -> float:
    """
    How much of the target is achieved, as a percentage (100% == on target).

    For lower-better metrics a smaller actual is better, so achievement is
    ``target / actual``.  For higher-better it is ``actual / target``.
    Clamped to 0..200 so a single wild year cannot flatten the whole scale.
    """
    try:
        a, t = float(actual), float(target)
    except (TypeError, ValueError):
        return 0.0
    if t == 0:
        return 100.0 if a == 0 else 0.0
    if str(direction).lower() == "lower":
        pct = (t / a * 100.0) if a > 0 else 200.0
    else:
        pct = a / t * 100.0
    return max(0.0, min(200.0, pct))


def on_track(actual: float, target: float, direction: str) -> bool:
    """True when the metric has met its benchmark."""
    return signed_gap(actual, target, direction) >= 0.0


def severity(gap_pp: float, unit: str = "%") -> dict:
    """
    Classify a favourable-positive gap into a severity band.

    Only *missed* targets (negative gap) can be severe; a met target is
    'achieved' or better.
    """
    g = float(gap_pp or 0.0)
    if g >= 10:
        return {"key": "exceeding", "label": "Exceeding target", "color": "#10B981",
                "bg": "rgba(16,185,129,0.12)", "score": 0.0}
    if g >= 0:
        return {"key": "ontrack", "label": "On track", "color": "#34D399",
                "bg": "rgba(52,211,153,0.12)", "score": 1.0}
    if g >= -5:
        return {"key": "watch", "label": "Slightly behind", "color": "#FBBF24",
                "bg": "rgba(251,191,36,0.12)", "score": 2.0}
    if g >= -15:
        return {"key": "offtrack", "label": "Off track", "color": "#F59E0B",
                "bg": "rgba(245,158,11,0.12)", "score": 3.0}
    if g >= -30:
        return {"key": "critical", "label": "Critical", "color": "#EF4444",
                "bg": "rgba(239,68,68,0.12)", "score": 4.0}
    return {"key": "severe", "label": "Severe bottleneck", "color": "#DC2626",
            "bg": "rgba(220,38,38,0.14)", "score": 5.0}
