"""
core/wisrule_engine.py -- light runtime interface to the trained WisRule model.

The dashboard never mines rules. It loads the pre-trained JSON saved by
`wisrule/wisrule_model_training.py` and uses three operations:

    1. build_scenario_items(gdp_pct, pop_pct, eff_pct)
        -> translates the What-if sidebar sliders into High/Low/Stable labels
           the same way the training script did.

    2. fire_rules(items) -> DataFrame
        -> returns the shortlisted rules whose "if" part matches the scenario,
           sorted by WisVal.

    3. ensemble_predict(items) -> DataFrame
        -> weighted vote across ALL fired positive rules, one row per parameter.

Everything is @st.cache_data wrapped (except the scenario build, which depends
on live slider values) so the JSON is only parsed once per session.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.parameter_relationships import build_parameter_frame
from core.queries import (
    Q_CO2, Q_ECONOMIC, Q_ELEC_GEN, Q_ENERGY_OVERVIEW,
    Q_LNG, Q_NATURAL_GAS, Q_RENEWABLE_ENERGY, Q_TD_LOSSES,
)

# --- where the trained model lives ----------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = _PROJECT_ROOT / "wisrule" / "model" / "wisrule_q1_model.json"

# --- label maps -------------------------------------------------------------
# Same map the training script uses, kept here so dashboard and trainer agree.
_LABEL_OF = {
    "gdp": "GDP", "population": "Population", "demand": "Demand",
    "generation": "Generation", "consumption": "Consumption",
    "capacity": "Capacity", "elec_imports": "Elec Imports",
    "td_losses": "T&D Losses", "gas_production": "Gas Production",
    "gas_consumption": "Gas Consumption", "lng_imports": "LNG Imports",
    "co2": "CO2", "primary_supply": "Primary Supply",
    "final_consumption": "Final Consumption",
}
_PARAM_OF = {v: k for k, v in _LABEL_OF.items()}

# Parameters the ensemble predicts (mirrors training ENSEMBLE_PREDICT_KEYS).
_ENSEMBLE_LABELS = ["Demand", "Generation", "Consumption", "CO2",
                    "Primary Supply", "Final Consumption",
                    "Gas Production", "Gas Consumption"]
# The training CV used min_weight 3.0 against the raw mined pool of hundreds
# of rules. The dashboard fires only the 23-rule shortlist, so a smaller
# floor is needed for the ensemble to commit. 1.5 means "at least one strong
# rule (conf × lift ≥ 1.5) backs this call".
_ENSEMBLE_MIN_WEIGHT = 1.5
_ENSEMBLE_LIFT_CAP = 5.0


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_wisrule_model() -> dict:
    """Read the trained JSON once per session. Returns {} if file missing."""
    if not MODEL_PATH.exists():
        return {}
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Reference growth rates (from energy.db, cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_reference_growth_rates() -> dict:
    """Median GDP growth % and Population growth % from recorded history.

    Uses the same source query as the parameter-relationships engine so the
    reference numbers stay aligned across the dashboard.
    """
    frame = build_parameter_frame(
        econ_df=run_query(Q_ECONOMIC),
        re_df=run_query(Q_RENEWABLE_ENERGY),
        gen_df=run_query(Q_ELEC_GEN),
        td_df=run_query(Q_TD_LOSSES),
        gas_df=run_query(Q_NATURAL_GAS),
        lng_df=run_query(Q_LNG),
        overview_df=run_query(Q_ENERGY_OVERVIEW),
        co2_df=run_query(Q_CO2),
    )
    if frame is None or frame.empty:
        return {"gdp_ref": 0.0, "pop_ref": 0.0}

    f = frame.copy()
    # Prefer the reported real GDP growth column (already a %).
    if "gdp_growth" in f.columns:
        g = pd.to_numeric(f["gdp_growth"], errors="coerce").dropna()
        gdp_ref = float(g.median()) if len(g) else 0.0
    else:
        gdp_ref = 0.0

    def _median_growth(col: str) -> float:
        if col not in f.columns:
            return 0.0
        s = pd.to_numeric(f[col], errors="coerce")
        s = s[(s > 0) & np.isfinite(s)]
        if len(s) < 2:
            return 0.0
        pct = (s.pct_change() * 100).replace([np.inf, -np.inf], np.nan).dropna()
        return float(pct.median()) if len(pct) else 0.0

    if gdp_ref == 0.0:
        gdp_ref = _median_growth("gdp")
    pop_ref = _median_growth("population")
    return {"gdp_ref": round(gdp_ref, 2), "pop_ref": round(pop_ref, 2)}


# ---------------------------------------------------------------------------
# Scenario builder
# ---------------------------------------------------------------------------
def _label(reference: float, given: float) -> str:
    """Turn a (reference, given) growth pair into High/Low/Stable."""
    if abs(given - reference) <= 0.5:
        return "Stable"
    return "High" if given > reference else "Low"


def build_scenario_items(gdp_growth_pct: float, pop_growth_pct: float,
                         efficiency_pct: float) -> List[str]:
    """Translate sidebar what-if values into High/Low/Stable item labels.

    Same rule the training script uses:
      * GDP and Population compared against their recorded median growth.
      * Energy parameters follow the GDP reading (model learned that link).
      * Efficiency >= 1% drags energy parameters down one step to "Low".
    """
    refs = get_reference_growth_rates()
    gdp_ref = refs["gdp_ref"]
    pop_ref = refs["pop_ref"]

    gdp_state = _label(gdp_ref, gdp_growth_pct)
    pop_state = _label(pop_ref, pop_growth_pct)

    items = [f"GDP={gdp_state}", f"Population={pop_state}"]
    drag = efficiency_pct >= 1.0
    energy_state = "Low" if drag else gdp_state
    # Everything that historically tracks economic activity gets the same
    # reading. Extending beyond the training script's 7 items so the ensemble
    # has more fired voters on the shortlisted 23 rules (the mined pool is
    # not available at display time, so a richer scenario helps).
    for key in ("Demand", "Consumption", "Primary Supply",
                "Final Consumption", "Generation",
                "CO2", "Gas Production", "Gas Consumption",
                "Capacity", "LNG Imports", "Elec Imports", "T&D Losses"):
        items.append(f"{key}={energy_state}")
    return items


# ---------------------------------------------------------------------------
# Rule firing
# ---------------------------------------------------------------------------
def fire_rules(items: Iterable[str], model: dict = None,
               top_n: int = 20) -> pd.DataFrame:
    """Return the rules whose antecedent matches the given items.

    Includes BOTH positive and negative rules. Each row carries:
      rule_id, rule_text, type, antecedent, consequent, confidence, lift,
      wisval_norm, cv_firings, cv_confidence, cv_verdict, currently_holds.
    """
    model = model if model is not None else load_wisrule_model()
    rules = model.get("rules", []) if model else []
    if not rules:
        return pd.DataFrame()

    items = frozenset(items)
    fired = []
    for r in rules:
        ante = frozenset(r["antecedent"])
        if not ante <= items:
            continue
        cons = frozenset(r["consequent"])
        present = cons <= items
        holds = present if r["rule_type"] == "Positive" else not present
        fired.append({
            "rule_id": r["rule_id"],
            "rule": r["rule_text"],
            "type": r["rule_type"],
            "antecedent": r["antecedent"],
            "consequent": r["consequent"],
            "confidence": r["confidence"],
            "lift": r["lift"],
            "support": r["support"],
            "wisval_norm": r["wisval_norm"],
            "cv_firings": r.get("cv_firings"),
            "cv_confidence": r.get("cv_confidence"),
            "cv_verdict": r.get("cv_verdict"),
            "currently_holds": "yes" if holds else "no",
        })
    if not fired:
        return pd.DataFrame()
    df = pd.DataFrame(fired)
    df = df.sort_values("wisval_norm", ascending=False).head(top_n)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Ensemble weighted vote
# ---------------------------------------------------------------------------
def ensemble_predict(items: Iterable[str], model: dict = None) -> pd.DataFrame:
    """Aggregate vote across all fired POSITIVE rules, per parameter.

    Each fired positive rule votes for its consequent state with weight
    ``confidence * min(lift, 5)``. For every parameter the ensemble tracks,
    we take argmax of the summed weights across states {High, Stable, Low}.
    If the top total is under ENSEMBLE_MIN_WEIGHT, no prediction is made
    for that parameter (returned row has state = None).

    Returns: DataFrame[parameter, predicted_state, weight, runner_up,
                        runner_up_weight, n_voters].
    """
    model = model if model is not None else load_wisrule_model()
    rules = model.get("rules", []) if model else []
    if not rules:
        return pd.DataFrame()

    items = frozenset(items)
    tally = {}  # {parameter_label: {state: weight}}

    for r in rules:
        if r["rule_type"] != "Positive":
            continue
        ante = frozenset(r["antecedent"])
        if not ante <= items:
            continue
        cons = list(r["consequent"])
        if not cons:
            continue
        # consequent is a single item like "Demand=High"
        cons_item = cons[0]
        if "=" not in cons_item:
            continue
        param_label, state = cons_item.split("=", 1)
        if param_label not in _ENSEMBLE_LABELS:
            continue
        weight = float(r["confidence"]) * min(float(r["lift"]), _ENSEMBLE_LIFT_CAP)
        bucket = tally.setdefault(param_label, {"High": 0.0, "Stable": 0.0, "Low": 0.0})
        bucket[state] = bucket.get(state, 0.0) + weight

    if not tally:
        return pd.DataFrame()

    rows = []
    for label in _ENSEMBLE_LABELS:
        bucket = tally.get(label)
        if bucket is None:
            continue
        s = pd.Series(bucket).sort_values(ascending=False)
        top_state, top_w = s.index[0], float(s.iloc[0])
        runner_state, runner_w = s.index[1], float(s.iloc[1])
        committed = top_w >= _ENSEMBLE_MIN_WEIGHT
        rows.append({
            "parameter": _PARAM_OF.get(label, label.lower()),
            "label": label,
            "predicted_state": top_state if committed else None,
            "weight": round(top_w, 3),
            "runner_up": runner_state if runner_w > 0 else None,
            "runner_up_weight": round(runner_w, 3),
            "n_voters": sum(1 for v in s.values if v > 0),
            "committed": bool(committed),
            "votes_by_state": {k: round(v, 3) for k, v in s.items() if v > 0},
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Model metrics summary (for KPI card)
# ---------------------------------------------------------------------------
def model_summary() -> dict:
    """Return the metrics dict + n_positive / n_negative for dashboard use."""
    model = load_wisrule_model()
    if not model:
        return {}
    m = dict(model.get("metrics", {}))
    m["trained_at"] = model.get("trained_at", "")
    m["n_rules_total"] = len(model.get("rules", []))
    return m


# ---------------------------------------------------------------------------
# Numeric forecast from state-conditional growth rates
# ---------------------------------------------------------------------------
def forecast_values(ens_df: pd.DataFrame,
                    horizon_year: int = 2035,
                    model: dict = None) -> pd.DataFrame:
    """Turn the ensemble's state prediction into a year-by-year numeric forecast.

    For each parameter the ensemble committed to a state, apply the median
    year-over-year growth rate recorded for that state historically. Repeat
    from the anchor (last measured year) up to ``horizon_year``. Also compute
    a low-band (25th pct growth) and high-band (75th pct growth) so the
    dashboard can draw a confidence interval.

    Parameters
    ----------
    ens_df : DataFrame
        Output of :func:`ensemble_predict`. Only rows with ``committed=True``
        produce a forecast; uncommitted rows are included with empty values.
    horizon_year : int
        Terminal year of the projection (defaults to 2035).
    model : dict, optional
        Loaded model JSON. Uses cached loader if omitted.

    Returns
    -------
    DataFrame with columns:
        parameter, label, state, anchor_year, anchor_value,
        growth_median_pct, growth_lo_pct, growth_hi_pct,
        years (list), median (list), low (list), high (list),
        horizon_value, horizon_low, horizon_high
    """
    model = model if model is not None else load_wisrule_model()
    if not model or ens_df is None or ens_df.empty:
        return pd.DataFrame()
    gr = model.get("growth_rates") or {}
    la = model.get("last_actuals") or {}
    if not gr or not la:
        return pd.DataFrame()

    rows = []
    for _, r in ens_df.iterrows():
        pkey = r["parameter"]
        state = r.get("predicted_state")
        anchor = la.get(pkey)
        growth = (gr.get(pkey) or {}).get(state) if state else None
        if not anchor or not growth:
            rows.append({
                "parameter": pkey, "label": r["label"],
                "state": state or "—", "has_forecast": False,
                "anchor_year": anchor["year"] if anchor else None,
                "anchor_value": anchor["value"] if anchor else None,
                "growth_median_pct": None,
                "growth_lo_pct": None, "growth_hi_pct": None,
                "years": [], "median": [], "low": [], "high": [],
                "horizon_value": None, "horizon_low": None,
                "horizon_high": None,
            })
            continue

        start_year = int(anchor["year"])
        v0 = float(anchor["value"])
        m_pct = float(growth["median_pct"]) / 100.0
        lo_pct = float(growth["lo_pct"]) / 100.0
        hi_pct = float(growth["hi_pct"]) / 100.0
        years, med, low, high = [], [], [], []
        vm = vl = vh = v0
        for y in range(start_year + 1, horizon_year + 1):
            vm *= (1 + m_pct)
            vl *= (1 + lo_pct)
            vh *= (1 + hi_pct)
            years.append(y)
            med.append(round(vm, 3))
            low.append(round(vl, 3))
            high.append(round(vh, 3))
        rows.append({
            "parameter": pkey, "label": r["label"],
            "state": state, "has_forecast": True,
            "anchor_year": start_year, "anchor_value": round(v0, 3),
            "growth_median_pct": float(growth["median_pct"]),
            "growth_lo_pct": float(growth["lo_pct"]),
            "growth_hi_pct": float(growth["hi_pct"]),
            "years": years, "median": med, "low": low, "high": high,
            "horizon_value": med[-1] if med else None,
            "horizon_low": low[-1] if low else None,
            "horizon_high": high[-1] if high else None,
        })
    return pd.DataFrame(rows)


def growth_rate_table(model: dict = None) -> pd.DataFrame:
    """Helper for the UI: return the growth-rate matrix as a tidy DataFrame."""
    model = model if model is not None else load_wisrule_model()
    gr = (model or {}).get("growth_rates") or {}
    rows = []
    for pkey, states in gr.items():
        for state, m in states.items():
            rows.append({
                "parameter": pkey, "state": state,
                "median_pct": m["median_pct"],
                "lo_pct": m["lo_pct"], "hi_pct": m["hi_pct"],
                "n_years": m["n_years"],
            })
    return pd.DataFrame(rows)
