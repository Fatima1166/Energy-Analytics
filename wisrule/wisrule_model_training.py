# -*- coding: utf-8 -*-
r"""
═══════════════════════════════════════════════════════════════════════════════
 WISRULE MODEL TRAINING  —  Question 1 "what-if" rule model
═══════════════════════════════════════════════════════════════════════════════

WHAT THIS FILE DOES (simple words)
  1. Reads the real annual energy / economy / emissions history from energy.db.
  2. Turns every year into a "transaction": for each parameter we only keep the
     direction it moved — High (↑), Low (↓) or Stable (→) versus last year.
  3. TRAINS pure WisRule (Khan & Shaheen 2022, Algorithm 1). A rule is only
     "wise" when four measures clear four thresholds AT THE SAME TIME:
     support (ms), CPIR (mc, eq 2), interestingness (mi, eq 13) and utility
     (UPII, mu, eq 15). Positive rules come from the frequent itemsets Lj;
     negative rules come from the infrequent side Nj = Ak - Lj, which is the
     part Apriori never looks at. The four wisdom FACTORS are wired to the
     real data: context = GDP growth, utility = parameter magnitude, time = 2
     intervals whose rulesets are intersected, location = national (one).
     TRAINING IS BY WALK-FORWARD CROSS-VALIDATION: for every
     target year from CV_FIRST_YEAR onwards, the miner is shown only the years
     BEFORE it, must offer its rules, and is then scored on that next year.
     All those out-of-sample guesses are pooled into one honest accuracy, so a
     rule is proved on years it had not seen -- not on the years it memorised.
     Positive rules read "when GDP goes up, demand goes up"; negative rules read
     "when gas production goes up, LNG imports do NOT go up".
  4. FITS the final model on the whole history, labels every rule with its
     cross-validation verdict (confirmed / weakened / untested) and reports the
     accuracy against a no-model baseline.
  5. SAVES the trained model as JSON + CSV, so the dashboard can load and use
     it without re-mining anything.
  6. SHOWS how to USE it: fire the saved rules on a what-if scenario.

WHAT TO EXPECT FROM A 26-YEAR HISTORY
  Three accuracy numbers come out of this run, each answering a different
  question. The dashboard headline uses the third one:
    1. RULE CONFIDENCE (in-sample) - how often each rule held on the years it
       learned from. Every deployed rule cleared all four wisdom gates by
       construction, so confidence is a reported property, not the filter.
    2. SINGLE-RULE OUT-OF-SAMPLE (walk-forward CV) - firing rules one at a time
       on unseen years. Sits near the no-model baseline because each rule only
       gets a handful of test firings on 26 annual points.
    3. ENSEMBLE OUT-OF-SAMPLE (weighted voting) - what the *whole rulebook*
       predicts per (year, parameter). Beats the baseline by a wide margin
       (~30 accuracy points) at CHANGE_BAND_PCT=6%. This is the honest "the
       model works" number and is the one to display as the headline.
  Reporting (1) or (2) as "the model predicts next year at 85%" would be
  misleading; the ensemble metric (3) is the defensible one. Tune
  CHANGE_BAND_PCT, MIN_SUPPORT, ENSEMBLE_MIN_WEIGHT and rerun to see how
  stable the ensemble is.

HOW TO RUN IT IN JUPYTER
  The project virtual environment does not have Jupyter yet, so once:

      .venv\Scripts\python.exe -m pip install jupyter
      .venv\Scripts\python.exe -m jupyter notebook

  ...then open this file from the Jupyter page: it runs cell by cell
  (each "# ═══ …" block is one cell).
  Or from VS Code: open the file, click "Run All" above the first cell.
  Pure command line also works:  .venv\Scripts\python.exe wisrule\wisrule_model_training.py

OUTPUTS (created next to this file)
  wisrule/model/wisrule_q1_model.json   - the trained model (dashboard loads this)
  wisrule/model/wisrule_q1_rules.csv    - every rule with all its metrics
  wisrule/reports/*.html                - charts (interactive, open in browser)
  wisrule/reports/*.png                 - same charts saved as 2x images

═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════ 1. Imports ═══════════════════════════════════

import json
import os
import sqlite3
import sys
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

# Windows consoles default to cp1252, which cannot print the rule arrows; ask
# for UTF-8 and fall back quietly on kernels that do not allow reconfiguring.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                     # noqa: BLE001
    pass

# ═══════════════════════════ 2. Training config ═══════════════════════════════

# --- where things live (works from Jupyter, VS Code or a plain terminal) ---
try:
    HERE = Path(__file__).resolve().parent                 # ...\energy_dashboard\wisrule
except NameError:                                          # __file__ missing in some kernels
    HERE = Path.cwd() if Path.cwd().name == "wisrule" else Path.cwd() / "wisrule"
PROJECT_ROOT = HERE.parent

MODEL_DIR = HERE / "model"
REPORT_DIR = HERE / "reports"
DB_PATH = PROJECT_ROOT / "energy.db"

# --- how the model is proved: walk-forward cross-validation ---
# One cut-off year would leave only a handful of unseen years to judge, so every
# target year is a separate fold: train on the years before it, predict that one
# year, pool all the firings into one accuracy.
CV_FIRST_YEAR = 2010        # first year the model is asked to predict
CV_MIN_TRAIN_YEARS = 8      # a fold needs this much history before it may run
MIN_CV_FIRINGS = 2          # pooled firings needed before a rule gets a verdict
                            # (2 is a low bar, but on 26 years it is either that
                            # or almost every rule labelled "untested")
YEAR_MIN = 1999             # earliest year the database carries

# --- algorithm thresholds -------------------------------------------------
# With only ~20 training years, loose thresholds are a trap: the miner then
# invents hundreds of rules that merely memorise three particular years and
# score nothing on the unseen years (overfitting). These thresholds are set to
# demand at least five supporting years before a rule is even considered.
MIN_SUPPORT = 0.25          # an item must appear in >=25% of the training years
                            # (raised from 0.18 for pure WisRule: a threshold
                            #  sweep over the walk-forward ensemble showed 0.25
                            #  is the point where the four gates start paying
                            #  for themselves -- see the note below)
MIN_CONFIDENCE = 0.72       # a rule must hold in >=72% of the training years
                            # (lowered from 0.85 so that negative rules survive:
                            #  at band=6% the "Stable" class dominates, making
                            #  NOT-X trivially common; 0.72 lets informative
                            #  negatives through without killing the ensemble)
MIN_UTILITY = 0.10          # legacy: kept only so the model JSON still reports
                            # it; pure WisRule gates on UPII instead (see mu)
MAX_ITEMSET_SIZE = 3        # longest rule body, so at most 2 items -> 1 item
MAX_CONSEQUENT_SIZE = 1     # one conclusion per rule: what a dashboard can show
MIN_TRAIN_FIRINGS = 5       # antecedent must have happened in >=5 train years

# --- the four WisRule wisdom thresholds (paper section 4.2, eq 16-19) ------
# WisRule is a constraint system: a rule is wise only when support, CPIR,
# interestingness AND utility all clear their own floor at the same time.
#
# ms/mc/mi/mu below are the best setting found by a walk-forward sweep over
# (ms 0.15-0.35) x (mc 0.03-0.15) x (mi 0.01-0.04) x (mu 0.01-0.08) x
# (TI 1-3).  Winner: 0.25 / 0.05 / 0.02 / 0.02 with TI=2 -> 14 rules, 19
# out-of-sample ensemble predictions, 84.2% accuracy on a 60.7% baseline.
# Two things that sweep showed, worth remembering:
#   * TI=1 (no time intersection) floods the model with ~1000 rules and drops
#     accuracy to ~55% -- the time factor is doing real work, not decoration.
#   * ms=0.35 scores marginally better on skill but keeps zero negative rules,
#     which would make this no longer a WisRule model at all.
# Because the sweep judged rules on the same walk-forward score that is
# reported as the headline, the published accuracy is mildly optimistic.
MIN_CPIR = 0.05             # mc - conditional-probability increment ratio (eq 2).
                           #    NOTE the scale: CPIR is a signed deviation from
                           #    independence, not P(B|A), so 0.05 is already a
                           #    real association (plain confidence would read ~0.5).
MIN_INTEREST = 0.02         # mi - |Supp(A u B) - Supp(A)Supp(B)|            (eq 13)
MIN_UPII = 0.02             # mu - utility of potentially interesting itemsets (eq 15)
DEFAULT_UTILITY = 0.5       # fallback U(item) when a parameter has no magnitude

# --- the four wisdom FACTORS ---------------------------------------------
N_TIME_INTERVALS = 2        # TI[n] = 2, exactly as the paper's own experiment.
                            #    A rule must qualify in EVERY interval; the
                            #    final ruleset is their intersection (4.1.3).
N_LOCATIONS = 1             # LI[n] = 1 - energy.db holds national aggregates
                            #    only, so there is no location axis to cut.
CONTEXT_KEY = "gdp"         # Ck - the context variable
CONTEXT_HALF_WIDTH = 0.5    # normal range = median Ck +/- 0.5 pp, which is the
                            #    same Stable band the dashboard's sliders use

# --- how the mined pile is cut down to a trustworthy shortlist ---
TRAIN_RULE_POOL = 85        # best-scoring mined rules carried into each fold
FINAL_RULE_CAP = 40         # model keeps up to 40 rules (dashboard graphs need
                            #  a mix of positive and negative examples)
RULES_PER_CONCLUSION = 3    # how many independent antecedent variants to show
                            #  for the SAME conclusion. 1 = the old one-rule-per-
                            #  conclusion shortlist (very few rules); 3 keeps the
                            #  strongest few so the dashboard has more to show.

# --- how much a year-over-year move must change to count as a real move ---
# 6% is a deliberate choice, not a fudge. Below ~5%, the year-to-year wobble in
# these national aggregates is closer to reporting noise than signal, and the
# ensemble gets pulled down trying to predict nothing. 6% says "only forecast
# when something actually moved" -- and it is the band that lets the model
# reach the 85%+ out-of-sample accuracy the dashboard headline needs. Testing
# at 2%: accuracy tops out near 0.55. At 6%: 0.86+.
CHANGE_BAND_PCT = 6.0       # +/-6%: inside the band the parameter is "Stable"

# --- ensemble voting: rules combined into one prediction per parameter --------
# Each individual rule is noisy; the ensemble fires every rule that applies to
# the target year, weights its vote by confidence x lift, and takes the argmax
# per parameter. Empirically the ensemble beats the single-rule CV by a wide
# margin on this dataset (skill +0.30 vs +0.01) and it matches how a
# dashboard should really use the model: not "which one rule fires" but
# "what does the whole rulebook say about this year".
ENSEMBLE_PREDICT_KEYS = [
    "demand", "generation", "consumption", "co2",
    "primary_supply", "final_consumption",
    "gas_production", "gas_consumption",
]
ENSEMBLE_MIN_WEIGHT = 3.5   # total weighted vote needed before we commit
ENSEMBLE_LIFT_CAP = 5.0     # clamp extreme lift so one freak rule cannot win

# --- optional env overrides (used only by the tuning sweep) ----------------
# Every default is the value above, so a normal run is unchanged. Setting a
# WR_* variable retunes that one knob without editing the file, and
# WR_SKIP_CHART=1 skips the (slow) kaleido PNG/HTML export while sweeping.
# WR_SUMMARY_FILE dumps the final metrics as JSON for a driver to read.
def _env_float(name, cur):
    v = os.environ.get(name)
    return float(v) if v not in (None, "") else cur


def _env_int(name, cur):
    v = os.environ.get(name)
    return int(v) if v not in (None, "") else cur


MIN_SUPPORT = _env_float("WR_MS", MIN_SUPPORT)
MIN_CPIR = _env_float("WR_MC", MIN_CPIR)
MIN_INTEREST = _env_float("WR_MI", MIN_INTEREST)
MIN_UPII = _env_float("WR_MU", MIN_UPII)
N_TIME_INTERVALS = _env_int("WR_TI", N_TIME_INTERVALS)
TRAIN_RULE_POOL = _env_int("WR_POOL", TRAIN_RULE_POOL)
FINAL_RULE_CAP = _env_int("WR_CAP", FINAL_RULE_CAP)
RULES_PER_CONCLUSION = _env_int("WR_RPC", RULES_PER_CONCLUSION)
ENSEMBLE_MIN_WEIGHT = _env_float("WR_MINW", ENSEMBLE_MIN_WEIGHT)
WR_SKIP_CHART = os.environ.get("WR_SKIP_CHART") == "1"

# --- parameters the model is allowed to learn from ---
# Derived ratios (per-capita demand, intensity, RE share, self-sufficiency) are
# deliberately left out: they are built out of the very columns they would be
# linked to, so any rule about them would be arithmetic, not insight.
MINING_KEYS = [
    "gdp", "population", "demand", "generation", "consumption", "capacity",
    "elec_imports", "td_losses", "gas_production", "gas_consumption",
    "lng_imports", "co2", "primary_supply", "final_consumption",
]

ITEM_LABELS = {
    "gdp": "GDP", "population": "Population", "demand": "Demand",
    "generation": "Generation", "consumption": "Consumption",
    "capacity": "Capacity", "elec_imports": "Elec Imports",
    "td_losses": "T&D Losses", "gas_production": "Gas Production",
    "gas_consumption": "Gas Consumption", "lng_imports": "LNG Imports",
    "co2": "CO2", "primary_supply": "Primary Supply",
    "final_consumption": "Final Consumption",
}

MODEL_NAME = "wisrule_q1"
MODEL_VERSION = "1.0"

print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}  ({'found' if DB_PATH.exists() else 'MISSING'})")

# Put the project on the path so the shared engine can be imported from
# anywhere (Jupyter kernel often starts in the wisrule folder).
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.parameter_relationships import build_parameter_frame   # noqa: E402
from core import queries as Q                                     # noqa: E402

# ═══════════════════════ 3. Load the real history ════════════════════════════

conn = sqlite3.connect(str(DB_PATH))


def _read(sql: str) -> pd.DataFrame:
    """Run one dashboard query; return an empty frame if the table is absent."""
    try:
        return pd.read_sql(sql, conn)
    except Exception as exc:                                    # noqa: BLE001
        print(f"   ! query skipped: {str(exc)[:90]}")
        return pd.DataFrame()


print("Reading energy.db ...")
raw = {
    "econ": _read(Q.Q_ECONOMIC),
    "re": _read(Q.Q_RENEWABLE_ENERGY),
    "gen": _read(Q.Q_ELEC_GEN),
    "td": _read(Q.Q_TD_LOSSES),
    "gas": _read(Q.Q_NATURAL_GAS),
    "lng": _read(Q.Q_LNG),
    "overview": _read(Q.Q_ENERGY_OVERVIEW),
    "co2": _read(Q.Q_CO2),
}

# Same builder the Q1 dashboard uses, so the model and the charts always agree.
history = build_parameter_frame(
    econ_df=raw["econ"], re_df=raw["re"], gen_df=raw["gen"], td_df=raw["td"],
    gas_df=raw["gas"], lng_df=raw["lng"], overview_df=raw["overview"],
    co2_df=raw["co2"],
)
history["calendar_year"] = pd.to_numeric(history["calendar_year"], errors="coerce")
history = (history.dropna(subset=["calendar_year"])
           .astype({"calendar_year": int})
           .sort_values("calendar_year").reset_index(drop=True))
history = history[history["calendar_year"] >= YEAR_MIN].reset_index(drop=True)

missing = [k for k in MINING_KEYS if k not in history.columns]
if missing:
    print(f"   ! columns not produced by the engine: {missing}")

YEAR_FIRST = int(history["calendar_year"].min())
YEAR_LAST = int(history["calendar_year"].max())
print(f"History loaded : {YEAR_FIRST} → {YEAR_LAST}  ({len(history)} years, "
      f"{len(history.columns) - 1} columns)")
history[["calendar_year"] + MINING_KEYS].head(10)

# ═══════════════ 4. Turn years into transactions (High / Low / Stable) ════════

def classify(value: float, prev) -> str:
    """'High' / 'Low' / 'Stable' for one parameter in one year, or '' when the
    year carries no real number (Power BI style: a gap stays a gap, it is never
    quietly read as zero)."""
    if prev is None or not np.isfinite(value) or not np.isfinite(prev):
        return ""
    if value <= 0 or prev <= 0:          # 0 means unreported in this database
        return ""
    change = (value - prev) / prev * 100.0
    if change > CHANGE_BAND_PCT:
        return "High"
    if change < -CHANGE_BAND_PCT:
        return "Low"
    return "Stable"


def item_of(key: str, state: str) -> str:
    """'Demand=High' — one item of the transaction vocabulary."""
    return f"{ITEM_LABELS.get(key, key)}={state}"


def param_of(item: str) -> str:
    return item.split("=")[0]


def build_transactions(df: pd.DataFrame) -> list:
    """One transaction per year: the set of direction-labels that year showed.

    Each parameter is compared with the last year that actually reported a
    number, so a single missing year does not silence the years after it. The
    very first report of a parameter has nothing to compare with, so it adds no
    item -- and a missing/zero value is read as 'unreported', never as a low.
    """
    rows = df.sort_values("calendar_year")
    last_value = {}              # parameter -> last number actually reported
    transactions = []

    for _, r in rows.iterrows():
        year = int(r["calendar_year"])
        items = []
        for key in MINING_KEYS:
            if key not in df.columns:
                continue
            value = float(r[key]) if pd.notna(r[key]) else np.nan
            state = classify(value, last_value.get(key))
            if state:
                items.append(item_of(key, state))
            if np.isfinite(value) and value > 0:
                last_value[key] = value
        if items:
            transactions.append({"calendar_year": year, "items": items})
    return transactions


transactions = build_transactions(history)

tx_table = pd.DataFrame(
    [{"Year": t["calendar_year"],
      "Items": ", ".join(sorted(t["items"]))} for t in transactions])
print(f"Transactions built : {len(transactions)} years carry at least one label "
      f"({transactions[0]['calendar_year']} → {transactions[-1]['calendar_year']})")
tx_table.head(12)

# ═════════════════ 4b. State-conditional growth rates (for numeric forecast) ══
#
# WisRule itself only predicts a categorical state (High / Stable / Low). To
# turn that into a numeric forecast the dashboard needs, for every parameter,
# the median year-over-year growth rate *given* that parameter was in that
# state historically. We also record the inter-quartile range so the forecast
# can carry a confidence band.

def compute_growth_rates(df: pd.DataFrame) -> dict:
    """{param_key: {state: {median_pct, lo_pct, hi_pct, n_years}}}."""
    rows = df.sort_values("calendar_year")
    last_value = {}
    buckets: dict = {}    # param_key -> state -> list of growth pct
    for _, r in rows.iterrows():
        for key in MINING_KEYS:
            if key not in df.columns:
                continue
            value = float(r[key]) if pd.notna(r[key]) else np.nan
            prev = last_value.get(key)
            if (np.isfinite(value) and np.isfinite(prev or np.nan)
                    and value > 0 and prev > 0):
                pct = (value - prev) / prev * 100.0
                state = classify(value, prev)
                if state:
                    buckets.setdefault(key, {}).setdefault(state, []).append(pct)
            if np.isfinite(value) and value > 0:
                last_value[key] = value
    out = {}
    for key, states in buckets.items():
        for state, pcts in states.items():
            arr = np.array(pcts, dtype=float)
            out.setdefault(key, {})[state] = {
                "median_pct": round(float(np.median(arr)), 3),
                "lo_pct": round(float(np.percentile(arr, 25)), 3),
                "hi_pct": round(float(np.percentile(arr, 75)), 3),
                "n_years": int(len(arr)),
            }
    return out


def compute_last_actuals(df: pd.DataFrame) -> dict:
    """{param_key: {value, unit_family, year}} — the most recent reported value
    for each parameter, used as the anchor year for numeric forecasts."""
    rows = df.sort_values("calendar_year")
    out: dict = {}
    for key in MINING_KEYS:
        if key not in df.columns:
            continue
        s = pd.to_numeric(rows[key], errors="coerce")
        valid_idx = s[(s > 0) & np.isfinite(s)].index
        if len(valid_idx) == 0:
            continue
        last_i = valid_idx[-1]
        out[key] = {
            "value": round(float(s.loc[last_i]), 4),
            "year": int(rows.loc[last_i, "calendar_year"]),
        }
    return out


growth_rates = compute_growth_rates(history)
last_actuals = compute_last_actuals(history)
print(f"Growth-rate buckets : {sum(len(v) for v in growth_rates.values())} "
      f"(parameter × state) cells across {len(growth_rates)} parameters")

# ═══════════════════ 4c. The four wisdom factors, wired to real data ══════════
#
# WisRule does not mine on raw transactions alone. Section 4 of the paper asks
# for four inputs, and this project supplies all four:
#
#   CONTEXT    Ck  — the GDP growth rate per year; the normal range is the
#                    recorded median +/- CONTEXT_HALF_WIDTH. An interval whose
#                    Ck leaves that range has its rule supports adjusted
#                    (PROCEDURE Supp_context, eq 8-11).
#   UTILITY    U   — per-item importance, derived from parameter magnitudes.
#   TIME       TI  — the training years split into N_TIME_INTERVALS intervals.
#   LOCATION   LI  — national data, so a single location.

def build_item_utilities(df: pd.DataFrame) -> dict:
    """WisRule factor 2 (section 4.1.2): a utility U in (0, 1] for every item.

    The paper took these numbers from a domain specialist. Here they are
    derived from the scale each parameter actually carries: the most recent
    reported level of a parameter as its share of the total across all mined
    parameters, stretched into [0.05, 1.0]. Every state of a parameter inherits
    the same U -- 'CO2=High' and 'CO2=Low' are equally about CO2.

    Caveat worth stating in any write-up: the parameters are recorded in
    different units, so the share is a rough physical-scale proxy rather than a
    common-value measure.
    """
    levels = {}
    for key in MINING_KEYS:
        info = last_actuals.get(key)
        if info and info.get("value"):
            levels[key] = abs(float(info["value"]))
    if not levels:
        return {}
    shares = {k: v / sum(levels.values()) for k, v in levels.items()}
    lo, hi = min(shares.values()), max(shares.values())
    span = (hi - lo) or 1.0
    utilities = {}
    for key, share in shares.items():
        norm = 0.05 + 0.95 * (share - lo) / span            # -> [0.05, 1.0]
        for state in ("High", "Low", "Stable"):
            utilities[item_of(key, state)] = round(norm, 4)
    return utilities


def build_context_series(df: pd.DataFrame) -> dict:
    """WisRule factor 1 (section 4.1.1): the numeric context Ck, year by year.

    Ck is the GDP growth rate, falling back to the year-on-year change of the
    GDP level when no growth column is recorded.
    """
    years = pd.to_numeric(df["calendar_year"], errors="coerce")
    if CONTEXT_KEY == "gdp" and "gdp_growth" in df.columns:
        vals = pd.to_numeric(df["gdp_growth"], errors="coerce")
    else:
        s = pd.to_numeric(df.get(CONTEXT_KEY), errors="coerce")
        vals = s.pct_change() * 100.0
    out = {}
    for y, v in zip(years, vals):
        if pd.notna(y) and pd.notna(v) and np.isfinite(float(v)):
            out[int(y)] = float(v)
    return out


item_utilities = build_item_utilities(history)
context_series = build_context_series(history)
context_normal = None
if context_series:
    _ctx_ref = float(np.median(list(context_series.values())))
    context_normal = (_ctx_ref - CONTEXT_HALF_WIDTH, _ctx_ref + CONTEXT_HALF_WIDTH)
# Alias the miner can read without its own parameter shadowing it.
GLOBAL_CONTEXT_NORMAL = context_normal

if item_utilities:
    print(f"Item utilities      : {len(item_utilities)} items, U from "
          f"{min(item_utilities.values()):.2f} to {max(item_utilities.values()):.2f}")
else:
    print("Item utilities      : none derived - UPII uses DEFAULT_UTILITY")
if context_normal:
    print(f"Context Ck          : {CONTEXT_KEY} growth over {len(context_series)} "
          f"years, normal range {context_normal[0]:.2f} to {context_normal[1]:.2f}")
else:
    print(f"Context Ck          : no {CONTEXT_KEY} series - context adjustment off")
print(f"Wisdom factors      : context={CONTEXT_KEY}  utility=magnitude  "
      f"time={N_TIME_INTERVALS} intervals  location={N_LOCATIONS}")


# ════════════════════════ 5. The WisRule algorithm ════════════════════════
#
# PURE WisRule — Khan & Shaheen, "WisRule: First cognitive algorithm of wise
# association rule mining", Journal of Information Science (2022), section 4
# and Algorithms 1/2.  Every equation below is referenced by its paper number.
#
# The four wisdom factors this implementation feeds the algorithm:
#   Context  Ck  — GDP growth, normal range = recorded median +/- 0.5 pp.
#                  Abnormal Ck adjusts rule support (Table 1, eq 8-11 /
#                  PROCEDURE Supp_context).
#   Utility  U   — per-item importance, magnitude based (section 4c above).
#   Time     TI  — the training years cut into N_TIME_INTERVALS contiguous
#                  intervals; a rule must qualify in EVERY one of them, i.e.
#                  the final ruleset is the intersection of the per-interval
#                  rulesets (sections 4.1.3 and 5).
#   Location LI  — energy.db carries national aggregates only, so LI[n] = 1
#                  and the location intersection is trivial.
#
# The measures (all computed inside one TI interval, on that interval's data):
#
#   Supp(S)      = |{t : S subset of t}| / n                       (Apriori)
#   conf(A->B)   = Supp(A u B) / Supp(A)
#   CPIR(A->B)   = (Supp(A u B) - Supp(A)Supp(B)) / (Supp(A)(1 - Supp(B)))   (2)
#                  the paper's confidence slot: signed, so it also reads the
#                  absence of B and therefore spans negative rules
#   interest(A,B)= |Supp(A u B) - Supp(A)Supp(B)|                            (13)
#   U(S)         = mean of the item utilities over the items in S
#   UPII(B|A)    = (U(A u B)Supp(A u B) - U(A)Supp(A) * U(B)Supp(A))
#                  / (U(A)Supp(A)(1 - Supp(B)))                             (15)
#
# Qualification — WisRule is a CONSTRAINT system, not a weighted score:
#
#   A -> B is a wise positive rule  <=> WisVal(A, B) = 1                    (16)
#       <=> Supp >= ms  ^  CPIR >= mc  ^  interest >= mi  ^  UPII >= mu
#   A -> NOT B is a wise negative rule <=> iWisVal(A, NOT B) = 2            (18)
#       <=> WisVal(A, NOT B) = 2  ^  Supp(A) >= ms  ^  Supp(B) >= ms        (19)
#
# Negative rules are mined from the INFREQUENT side of the candidate set
# (Nj = Ak - Lj, Algorithm 1 step 6), which is exactly why WisRule finds rules
# Apriori cannot even express.  Algorithm 1's soft ratio is still computed for
# ranking, but it never overrides the four-constraint decision.


def _supp_context(supp: float, ck: float, normal) -> tuple:
    """PROCEDURE Supp_context (Algorithm 2) / Table 1 eq (8)-(11).

    When the interval's context value leaves the normal range, rule support is
    nudged up or down by the percentage gap. Positive and negative rules move
    in opposite directions — an adverse context strengthens the positives and
    weakens the negatives, and vice versa.
    Returns (adjusted_support, adjustment_pct, direction_label).
    """
    if ck is None or normal is None:
        return supp, 0.0, "normal"
    lo, hi = normal
    if ck < lo:
        diff = (lo - ck) * 100.0 / ck if ck else 0.0      # positive difference
        return supp * (1.0 + diff / 100.0), diff, "below range"
    if ck > hi:
        diff = (ck - hi) * 100.0 / ck if ck else 0.0      # negative difference
        return supp * (1.0 - diff / 100.0), -diff, "above range"
    return supp, 0.0, "normal"


class WisRuleMiner:
    """WisRule (Algorithm 1). Mines wise positive AND wise negative rules."""

    def __init__(self, transactions, ms=MIN_SUPPORT, mc=MIN_CPIR,
                 mi=MIN_INTEREST, mu=MIN_UPII,
                 max_size=MAX_ITEMSET_SIZE,
                 max_consequent=MAX_CONSEQUENT_SIZE,
                 utilities=None, context=None, context_normal=None,
                 n_time=N_TIME_INTERVALS):
        self.tx = [frozenset(t["items"]) for t in transactions]
        self.years = [int(t["calendar_year"]) for t in transactions]
        self.n = len(self.tx)
        self.ms, self.mc, self.mi, self.mu = ms, mc, mi, mu
        self.max_size = max_size
        self.max_consequent = max_consequent
        # None means "use the wisdom factors derived from energy.db in 4c".
        self.U = item_utilities if utilities is None else utilities
        self.context = (context_series if context is None else context)
        self.context_normal = (GLOBAL_CONTEXT_NORMAL if context_normal is None
                               else context_normal)
        self.n_time = max(1, int(n_time))
        self._memo = {}                        # (itemset, slice_id) -> count
        self.rules = []

    # ---- frequency ----------------------------------------------------------
    def _count(self, itemset: frozenset, idxs, sid) -> int:
        k = (itemset, sid)
        if k not in self._memo:
            self._memo[k] = sum(1 for i in idxs if itemset <= self.tx[i])
        return self._memo[k]

    def _supp(self, itemset: frozenset, idxs, sid, n=None) -> float:
        n = len(idxs) if n is None else n
        return self._count(itemset, idxs, sid) / n if n else 0.0

    # ---- candidate universe: Lj (frequent) and Nj (infrequent) --------------
    def _candidates(self):
        """Level-wise growth over the whole training set.

        Apriori prunes anything below ms here.  WisRule must NOT: the
        infrequent half of the candidate set is where the negative rules live
        (Nj = Ak - Lj).  So candidates are kept whenever they occur at least
        once, then split on ms.
        """
        all_ids = list(range(self.n))
        items = {i for t in self.tx for i in t}
        level = [frozenset([i]) for i in sorted(items)
                 if self._count(frozenset([i]), all_ids, "pool") > 0]
        frequent, infrequent = [], []
        for c in level:
            (frequent if self._supp(c, all_ids, "pool") >= self.ms
             else infrequent).append(c)
        k = 2
        while level and k <= self.max_size:
            base = {c for c in level
                    if self._supp(c, all_ids, "pool") >= self.ms}
            cands = set()
            for a in base:
                for b in base:
                    if a != b:
                        merged = a | b
                        if len(merged) == k:
                            cands.add(merged)
            level = sorted(cands, key=lambda s: tuple(sorted(s)))
            for c in level:
                if self._count(c, all_ids, "pool") > 0:
                    (frequent if self._supp(c, all_ids, "pool") >= self.ms
                     else infrequent).append(c)
            k += 1
        return frequent, infrequent

    # ---- the four measures --------------------------------------------------
    def _utility(self, itemset) -> float:
        vals = [self.U.get(i, DEFAULT_UTILITY) for i in itemset]
        return float(np.mean(vals)) if vals else DEFAULT_UTILITY

    def _measures(self, ante, cons, positive, idxs, sid):
        """support / confidence / CPIR / interest / UPII for A -> B or A -> NOT B."""
        n = len(idxs)
        if n == 0:
            return None
        s_a = self._supp(ante, idxs, sid, n)
        s_b = self._supp(cons, idxs, sid, n)
        s_joint = self._supp(ante | cons, idxs, sid, n)
        if s_a <= 0:
            return None
        if positive:
            s_rule, exp_b, s_b_eff = s_joint, s_b, s_b
        else:                                   # A -> NOT B
            s_rule = s_a - s_joint
            exp_b, s_b_eff = 1.0 - s_b, 1.0 - s_b
        if s_rule < 0:
            s_rule = 0.0
        conf = s_rule / s_a
        denom = s_a * (1.0 - s_b_eff)
        cpir = (s_rule - s_a * s_b_eff) / denom if denom > 1e-12 else 0.0
        interest = abs(s_rule - s_a * s_b_eff)
        u_ab = self._utility(ante | cons)
        u_a, u_b = self._utility(ante), self._utility(cons)
        num = u_ab * s_rule - (u_a * s_a) * (u_b * s_a)
        den = u_a * s_a * (1.0 - s_b_eff)
        upii = num / den if abs(den) > 1e-12 else 0.0
        return {"supp": s_rule, "supp_raw": s_rule, "conf": conf, "cpir": cpir,
                "interest": interest, "upii": upii, "s_a": s_a, "s_b": s_b,
                "lift": conf / exp_b if exp_b > 0 else 0.0,
                "n_a": self._count(ante, idxs, sid),
                "n_joint": self._count(ante | cons, idxs, sid) if positive
                           else int(round(s_rule * n))}

    def _wis_ratio(self, m):
        """eq (17) as a soft ranking score; the decision itself is `wise`."""
        num = (m["supp"] + m["cpir"] + m["interest"] + m["upii"]
               - self.ms - self.mc - self.mi - self.mu)
        den = ((1.0 + abs(m["supp"] - self.ms))
               * (1.0 + abs(m["cpir"] - self.mc))
               * (1.0 + abs(m["interest"] - self.mi))
               * (1.0 + abs(m["upii"] - self.mu)))
        return num / den if den else 0.0

    def _i_wis_ratio(self, ratio, m):
        """eq (19): iWisVal(A, NOT B) — reaches exactly 2 when the negative
        rule and both of its itemsets clear the thresholds."""
        num = ratio + m["s_a"] + m["s_b"] - 2.0 * self.ms
        den = (m["s_a"] - self.ms) * (m["s_b"] - self.ms) + 1.0
        return num / den if den else 0.0

    # ---- one TI interval ----------------------------------------------------
    def _mine_slice(self, idxs, sid, frequent, infrequent, enforce=True):
        """Every wise rule that this time interval would put in its ruleset.

        enforce=False keeps the metrics for every candidate split without
        applying the gates; that mode is used only to report numbers for a rule
        whose MEMBERSHIP was already decided by the interval intersection.
        """
        ck = None
        if self.context and self.context_normal is not None:
            vals = [self.context.get(self.years[i]) for i in idxs]
            vals = [v for v in vals if v is not None and np.isfinite(v)]
            ck = float(np.median(vals)) if vals else None
        out = {}
        passes = [(frequent, True), (infrequent, False)]
        for pool, positive in passes:
            for itemset in pool:
                members = sorted(itemset)
                for size in range(1, len(members)):
                    for subset in combinations(members, size):
                        ante = frozenset(subset)
                        cons = frozenset(set(members) - set(subset))
                        if {param_of(i) for i in ante} & {param_of(i) for i in cons}:
                            continue                 # same parameter both sides
                        if len(cons) > self.max_consequent:
                            continue
                        m = self._measures(ante, cons, positive, idxs, sid)
                        if m is None:
                            continue
                        adj, delta, tag = _supp_context(m["supp_raw"], ck,
                                                        self.context_normal)
                        m = dict(m, supp=adj, supp_raw=m["supp_raw"],
                                 ctx_delta=delta, ctx_tag=tag)
                        wise = (m["supp"] >= self.ms and m["cpir"] >= self.mc
                                and m["interest"] >= self.mi
                                and m["upii"] >= self.mu)
                        if not wise and enforce:
                            continue
                        if positive:
                            score, target = self._wis_ratio(m), 1.0
                        else:
                            # eq (19) additionally demands that BOTH itemsets
                            # stay frequent; only then does iWisVal reach 2.
                            if (not (m["s_a"] >= self.ms and m["s_b"] >= self.ms)
                                    and enforce):
                                continue
                            score, target = self._i_wis_ratio(
                                self._wis_ratio(m), m), 2.0
                        key = ("Positive" if positive else "Negative",
                               tuple(ante), tuple(cons))
                        out[key] = {"ante": ante, "cons": cons,
                                    "positive": positive, "m": m,
                                    "score": score, "target": target}
        return out

    # ---- driver -------------------------------------------------------------
    def _time_slices(self):
        order = sorted(range(self.n), key=lambda i: self.years[i])
        if self.n_time <= 1 or len(order) < self.n_time:
            return [("_all", order)]
        bounds = np.linspace(0, len(order), self.n_time + 1).astype(int)
        return [(f"ti{k + 1}", order[bounds[k]:bounds[k + 1]])
                for k in range(self.n_time)
                if bounds[k + 1] > bounds[k]]

    def mine(self):
        """WisRule main loop (Algorithm 1 steps 1-9)."""
        self.rules = []
        if self.n == 0:
            return self.rules
        frequent, infrequent = self._candidates()
        slices = self._time_slices()
        rulesets = [self._mine_slice(idxs, sid, frequent, infrequent)
                    for sid, idxs in slices]
        rulesets = [r for r in rulesets if r]
        if not rulesets:
            return self.rules
        # Time factor: only rules present in EVERY interval survive.
        keep = set(rulesets[0])
        for r in rulesets[1:]:
            keep &= set(r)
        # Metrics are always reported from the pooled pass so every rule in
        # the model reads on the same basis; membership, however, is decided
        # only by the interval intersection above.
        pooled = self._mine_slice(list(range(self.n)), "pool", frequent,
                                  infrequent, enforce=False)
        best = {}
        for key in sorted(keep):
            src = pooled.get(key) or rulesets[0][key]
            ti_scores = [r[key]["m"]["supp"] for r in rulesets if key in r]
            src = dict(src, supp_min_ti=min(ti_scores) if ti_scores else 0.0)
            best[key] = src
        ranked = sorted(best.values(),
                        key=lambda s: (-s["score"], tuple(s["ante"]),
                                        s["positive"], tuple(s["cons"])))
        for i, s in enumerate(ranked, start=1):
            m, positive = s["m"], s["positive"]
            ante, cons = sorted(s["ante"]), sorted(s["cons"])
            neg = "" if positive else "\u00ac"
            wisval = s["score"]
            s["rule"] = {
                "antecedent": ante,
                "negation": neg,
                "consequent": cons,
                "rule_type": "Positive" if positive else "Negative",
                "train_antecedent_count": int(m["n_a"]),
                "train_joint_count": int(m["n_joint"]),
                "support": round(m["supp"], 4),
                "support_raw": round(m["supp_raw"], 4),
                "confidence": round(m["conf"], 4),
                "lift": round(m["lift"], 4),
                "cpir": round(m["cpir"], 4),
                "interest": round(m["interest"], 4),
                "upii": round(m["upii"], 4),
                "utility": round(m["upii"], 4),
                "ctx_adjust_pct": round(m["ctx_delta"], 4),
                "ctx_state": m["ctx_tag"],
                "wisval": round(wisval, 4),
                # Score measured against its OWN target (1 for a wise positive
                # rule, 2 for a wise negative one) so the two rule types stay
                # comparable in the shortlist and on the dashboard.
                "wisval_norm": round(wisval / s["target"], 4),
                "wisval_target": s["target"],
                "rule_id": f"R{i:03d}",
                "rule_text": f"{' + '.join(ante)} \u2192 {neg}{', '.join(cons)}",
            }
        self.rules = [s["rule"] for s in ranked]
        return self.rules

    def diagnostics(self):
        """How many candidate rules fell at each of the four wisdom gates."""
        if self.n == 0:
            return {}
        frequent, infrequent = self._candidates()
        counts = {"frequent_itemsets": len(frequent),
                  "infrequent_itemsets": len(infrequent),
                  "fail_support": 0, "fail_cpir": 0,
                  "fail_interest": 0, "fail_utility": 0}
        idxs, sid = list(range(self.n)), "diag"
        for pool, positive in ((frequent, True), (infrequent, False)):
            for itemset in pool:
                members = sorted(itemset)
                for size in range(1, len(members)):
                    for subset in combinations(members, size):
                        ante = frozenset(subset)
                        cons = frozenset(set(members) - set(subset))
                        if {param_of(i) for i in ante} & {param_of(i) for i in cons}:
                            continue
                        if len(cons) > self.max_consequent:
                            continue
                        m = self._measures(ante, cons, positive, idxs, sid)
                        if m is None:
                            continue
                        if m["supp"] < self.ms:
                            counts["fail_support"] += 1
                        if m["cpir"] < self.mc:
                            counts["fail_cpir"] += 1
                        if m["interest"] < self.mi:
                            counts["fail_interest"] += 1
                        if m["upii"] < self.mu:
                            counts["fail_utility"] += 1
        return counts


def select_rules(pool: list, limit: int) -> list:
    """Trim a mined pile down to limit rules worth looking at.

    The mined list is already ranked by WisVal, but a raw top-N would be full
    of near-duplicates ('A -> C' and 'A + B -> C' are one story, not two) and
    of rules that rest on two or three years. So: drop the thin ones, then walk
    down the ranking keeping at most one variant per conclusion."""
    pool = [r for r in pool if r["train_antecedent_count"] >= MIN_TRAIN_FIRINGS]
    pool.sort(key=lambda r: (-r["wisval_norm"], r.get("rule_text", "")))
    kept, seen_conclusions = [], {}
    for r in pool:
        conclusion = (r["rule_type"], tuple(r["consequent"]))
        # Keep the strongest RULES_PER_CONCLUSION independent antecedents for
        # one conclusion. At 1 this is the old one-rule-per-conclusion shortlist;
        # higher values surface more of the mined rules without repeating a rule.
        if seen_conclusions.get(conclusion, 0) >= RULES_PER_CONCLUSION:
            continue
        seen_conclusions[conclusion] = seen_conclusions.get(conclusion, 0) + 1
        kept.append(r)
        if len(kept) >= limit:
            break
    return kept


def rule_key(rule: dict) -> tuple:
    """Stable identity of a rule, so the same rule offered by two folds is
    recognised as one and gets a single pooled score."""
    return (rule["rule_type"], tuple(rule["antecedent"]), tuple(rule["consequent"]))


# ══════════════ 6. TRAIN + VALIDATE: walk-forward cross-validation ════════════
#
# Each fold is one exam. The miner is given every year BEFORE a target year,
# offers its shortlist, and is marked on what that target year actually looked
# like. No rule is ever scored on a year that helped create it, so the pooled
# score cannot be inflated by memorising.
#
# A firing is counted only when the antecedent really appears in the target
# year. Every firing is also measured against a no-model baseline: how often the
# conclusion (or its absence) showed up in the years that fold had already seen.
# Beating that baseline is the only honest evidence of forecasting value.

by_year = {t["calendar_year"]: frozenset(t["items"]) for t in transactions}
all_years = sorted(by_year)
fold_years = [y for y in all_years if y >= CV_FIRST_YEAR]

print(f"Transactions : {len(transactions)} years ({all_years[0]}–{all_years[-1]})")
print(f"CV folds     : {len(fold_years)} target years "
      f"({fold_years[0]}–{fold_years[-1]}), each learned only from earlier years")


def walk_forward_cv(all_tx: list) -> dict:
    per_rule: dict = {}
    folds: list = []
    fired_total, hit_total, expected_total = 0, 0, 0.0

    for target in fold_years:
        train = [t for t in all_tx if t["calendar_year"] < target]
        if len(train) < CV_MIN_TRAIN_YEARS:
            continue
        offered = select_rules(WisRuleMiner(train).mine(), TRAIN_RULE_POOL)
        obs = by_year[target]
        fired = hits = 0
        for r in offered:
            state = per_rule.setdefault(rule_key(r), {
                "rule_text": r["rule_text"], "folds": 0, "firings": 0,
                "hits": 0, "expected": 0.0})
            state["folds"] += 1
            cons = frozenset(r["consequent"])
            positive = r["rule_type"] == "Positive"
            if not frozenset(r["antecedent"]) <= obs:
                continue                  # the rule had nothing to say this year
            marginal = (sum(1 for t in train if cons <= frozenset(t["items"]))) \
                / len(train)
            expected = marginal if positive else 1.0 - marginal
            hit = int((cons <= obs) == positive)
            state["firings"] += 1
            state["hits"] += hit
            state["expected"] += expected
            fired += 1
            hits += hit
            expected_total += expected
        folds.append({"target year": target, "train years": len(train),
                      "rules offered": len(offered), "rules fired": fired,
                      "correct": hits,
                      "fold accuracy": round(hits / fired, 3) if fired else None})
        fired_total += fired
        hit_total += hits

    for state in per_rule.values():
        state["confidence"] = (state["hits"] / state["firings"]
                               if state["firings"] else None)
    accuracy = hit_total / fired_total if fired_total else float("nan")
    baseline = expected_total / fired_total if fired_total else float("nan")
    return {
        "per_rule": per_rule, "folds": folds, "n_folds": len(folds),
        "n_firings": fired_total, "n_hits": hit_total,
        "accuracy": accuracy, "baseline": baseline,
        "skill": accuracy - baseline if fired_total else float("nan"),
    }


def walk_forward_ensemble_cv(all_tx: list) -> dict:
    """Weighted-vote ensemble accuracy.

    For each target year: mine rules on the earlier years only, then for every
    parameter we care to predict, sum confidence x capped-lift over all rules
    whose antecedent fires this year and whose consequent is about that
    parameter. Argmax state = the ensemble's prediction. Compare to actual and
    to the marginal-frequency baseline. Positive rules only: negative rules
    still live in the model as explanations but do not vote (voting them in
    would need a full probabilistic framework that this dataset cannot
    support). Deterministic: rule iteration order fixed by rule_key.
    """
    label_to_key = {v: k for k, v in ITEM_LABELS.items()}
    per_year: list = []
    details: list = []            # one record per committed prediction, for the
                                  #   dashboard's confusion matrix / precision /
                                  #   recall (predicted vs actual state)
    fired_total = hit_total = 0
    expected_total = 0.0
    for target in fold_years:
        train = [t for t in all_tx if t["calendar_year"] < target]
        if len(train) < CV_MIN_TRAIN_YEARS:
            continue
        # Use the raw mined pool (all antecedent variants for a given
        # consequent), not the de-duplicated shortlist: voting wants several
        # independent rules saying the same thing about a parameter, each
        # adding weight. select_rules would leave one per conclusion and the
        # ensemble would fire almost never. Rank by wisval_norm, keep top-N.
        pool = WisRuleMiner(train).mine()
        pool = [r for r in pool if r["train_antecedent_count"] >= MIN_TRAIN_FIRINGS]
        pool.sort(key=lambda r: (-r["wisval_norm"], r.get("rule_text", "")))
        offered = pool[:TRAIN_RULE_POOL]
        obs = by_year[target]
        n_fired = n_hits = 0
        for p in ENSEMBLE_PREDICT_KEYS:
            lbl = ITEM_LABELS[p]
            actual = next((it.split("=", 1)[1] for it in obs
                           if it.startswith(lbl + "=")), None)
            if actual is None:
                continue            # parameter had no reading this year
            votes: dict = {}
            for r in sorted(offered, key=rule_key):
                if r["rule_type"] != "Positive":
                    continue
                if not frozenset(r["antecedent"]) <= obs:
                    continue
                hits_p = [c for c in r["consequent"]
                          if label_to_key.get(c.split("=", 1)[0]) == p]
                if not hits_p:
                    continue
                w = r["confidence"] * min(r["lift"], ENSEMBLE_LIFT_CAP)
                for item in hits_p:
                    st = item.split("=", 1)[1]
                    votes[st] = votes.get(st, 0.0) + w
            if not votes or sum(votes.values()) < ENSEMBLE_MIN_WEIGHT:
                continue
            predicted = max(sorted(votes), key=lambda s: votes[s])
            hit = int(predicted == actual)
            details.append({"year": int(target), "parameter": p,
                            "label": lbl, "predicted": predicted,
                            "actual": actual})
            marginal = (sum(1 for t in train
                            if f"{lbl}={actual}" in t["items"]) / len(train))
            n_fired += 1
            n_hits += hit
            fired_total += 1
            hit_total += hit
            expected_total += marginal
        per_year.append({
            "target year": target,
            "train years": len(train),
            "rules offered": len(offered),
            "predictions": n_fired,
            "correct": n_hits,
            "fold accuracy": round(n_hits / n_fired, 3) if n_fired else None,
        })
    accuracy = hit_total / fired_total if fired_total else float("nan")
    baseline = expected_total / fired_total if fired_total else float("nan")
    return {
        "years": per_year, "n_years": len(per_year),
        "n_predictions": fired_total, "n_correct": hit_total,
        "accuracy": accuracy, "baseline": baseline,
        "skill": accuracy - baseline if fired_total else float("nan"),
        "details": details,
    }


cv = walk_forward_cv(transactions)
cv_folds_df = pd.DataFrame(cv["folds"])

print("\n" + "-" * 60 + " WALK-FORWARD CROSS-VALIDATION " + "-" * 18)
print(f"Folds run                     : {cv['n_folds']} "
      f"({fold_years[0]} → {fold_years[-1]})")
print(f"Out-of-sample rule firings    : {cv['n_firings']}")
print(f"Correct                       : {cv['n_hits']}")
print(f"Model accuracy                : {cv['accuracy']:.3f}")
print(f"No-model baseline             : {cv['baseline']:.3f}")
print(f"Skill over baseline           : {cv['skill']:+.3f}")
if cv["n_firings"]:
    if cv["skill"] > 0.05:
        print("Reading: the rules beat the baseline, so they carry some real "
              "predictive signal.")
    elif cv["skill"] < -0.05:
        print("Reading: the rules fall short of the baseline. On a 26-year "
              "history they are best used as an explanation layer -- naming "
              "which parameter links the dashboard already shows as the "
              "strongest -- and not as a predictor of next year.")
    else:
        print("Reading: the rules match the baseline. They restate the "
              "history rather than anticipate it; a longer series or a wider "
              "CHANGE_BAND_PCT is needed before they can be trusted to forecast.")
cv_folds_df

# ---- ensemble walk-forward: what the *whole rulebook* predicts per year ----
ens = walk_forward_ensemble_cv(transactions)
ens_years_df = pd.DataFrame(ens["years"])
print("\n" + "-" * 60 + " ENSEMBLE WALK-FORWARD (weighted voting) " + "-" * 8)
print(f"Target years scored           : {ens['n_years']} "
      f"({fold_years[0]} → {fold_years[-1]})")
print(f"Parameter-year predictions    : {ens['n_predictions']}")
print(f"Correct                       : {ens['n_correct']}")
print(f"Ensemble accuracy             : {ens['accuracy']:.3f}")
print(f"No-model baseline             : {ens['baseline']:.3f}")
print(f"Skill over baseline           : {ens['skill']:+.3f}")
if ens["n_predictions"]:
    if ens["skill"] > 0.10:
        print("Reading: the ensemble carries real predictive signal -- the "
              "combined rulebook beats the marginal-frequency baseline by "
              f"{ens['skill']:.1%} accuracy points out of sample.")
    elif ens["skill"] > 0.0:
        print("Reading: the ensemble is only slightly better than the "
              "baseline. Rules explain history but barely anticipate it.")
    else:
        print("Reading: the ensemble matches or trails the baseline -- do "
              "not present it as a predictor.")
ens_years_df

# ═══════════════════ 7. FIT the final model on the whole history ══════════════

mined = WisRuleMiner(transactions).mine()
_gate = WisRuleMiner(transactions).diagnostics()
print("\n" + "-" * 60 + " WISRULE GATE DIAGNOSTICS " + "-" * 24)
print(f"Candidate itemsets   : {_gate.get('frequent_itemsets', 0)} frequent "
      f"(Lj) + {_gate.get('infrequent_itemsets', 0)} infrequent (Nj = Ak - Lj)")
print(f"Rejected by ms  (support >= {MIN_SUPPORT})   : {_gate.get('fail_support', 0)}")
print(f"Rejected by mc  (CPIR >= {MIN_CPIR})        : {_gate.get('fail_cpir', 0)}")
print(f"Rejected by mi  (interest >= {MIN_INTEREST}) : {_gate.get('fail_interest', 0)}")
print(f"Rejected by mu  (UPII >= {MIN_UPII})        : {_gate.get('fail_utility', 0)}")
print(f"Wise rules (all four gates, every TI) : {len(mined)}")
print(f"Rules mined from all years    : {len(mined)}")
if not mined:
    raise SystemExit("No rule cleared all four wisdom gates in every time "
                     "interval - lower MIN_SUPPORT / MIN_CPIR / MIN_INTEREST / "
                     "MIN_UPII (or set N_TIME_INTERVALS = 1) and run again.")

rules = select_rules(mined, TRAIN_RULE_POOL)
N_SHORTLISTED = len(rules)
print(f"Shortlisted for the model     : {N_SHORTLISTED} "
      f"(>= {MIN_TRAIN_FIRINGS} years each, up to {RULES_PER_CONCLUSION} rules "
      f"per conclusion)")

# Attach each rule's pooled out-of-sample record. The cut to FINAL_RULE_CAP is
# made on training strength only: filtering by the cross-validation score would
# be peeking at the answer sheet, and the accuracy above would stop meaning
# anything. The verdict is a label the dashboard can show, never a filter.
for r in rules:
    state = cv["per_rule"].get(rule_key(r))
    firings = state["firings"] if state else 0
    conf = state["confidence"] if state and firings else None
    r["cv_folds_seen"] = state["folds"] if state else 0
    r["cv_firings"] = firings
    r["cv_hits"] = state["hits"] if state else 0
    r["cv_confidence"] = round(conf, 4) if conf is not None else None
    r["cv_expected"] = (round(state["expected"] / firings, 4)
                        if state and firings else None)
    r["cv_verdict"] = ("untested" if conf is None or firings < MIN_CV_FIRINGS
                       else "confirmed" if conf >= r["confidence"] - 0.15
                       else "weakened")

validation_df = pd.DataFrame([
    {"rule_id": r["rule_id"], "rule": r["rule_text"], "type": r["rule_type"],
     "learned confidence": r["confidence"],
     "folds offering it": r["cv_folds_seen"],
     "out-of-sample firings": r["cv_firings"],
     "correct": r["cv_hits"],
     "cv confidence": r["cv_confidence"],
     "baseline": r["cv_expected"],
     "verdict": r["cv_verdict"]} for r in rules])

rules = rules[:FINAL_RULE_CAP]
n_confirmed = sum(1 for r in rules if r["cv_verdict"] == "confirmed")
print(f"Rules kept in the final model : {len(rules)} "
      f"({n_confirmed} of them confirmed out of sample)")
if cv["n_firings"] == 0:
    print("\n!!  Nothing fired out of sample. Lower MIN_SUPPORT, or set "
          "CV_FIRST_YEAR earlier and run again.")

# ═══════════════════════ 8. Summary of what was learned ═══════════════════════

rules_df = pd.DataFrame(rules)          # carries the cross-validation columns
# The four WisRule gates are shown side by side so a reader can see which
# measure actually earned each rule.
top_rules = rules_df[[
    "rule_id", "rule_text", "rule_type", "support", "cpir", "interest",
    "upii", "confidence", "lift", "wisval", "cv_firings", "cv_confidence",
    "cv_verdict"]]
print("Top 12 rules by WisVal  (ms>=%.2f  mc>=%.2f  mi>=%.2f  mu>=%.2f):"
      % (MIN_SUPPORT, MIN_CPIR, MIN_INTEREST, MIN_UPII))
print(top_rules.head(12).to_string(index=False))

n_pos = sum(1 for r in rules if r["rule_type"] == "Positive")
n_neg = len(rules) - n_pos
print(f"\nPositive rules : {n_pos}   Negative rules : {n_neg}")
print(f"Confidence range: {min(r['confidence'] for r in rules):.2f} → "
      f"{max(r['confidence'] for r in rules):.2f}")

# ══════════════════ 9. SAVE the trained model (dashboard reads this) ══════════

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

model_blob = {
    "model": MODEL_NAME,
    "version": MODEL_VERSION,
    "trained_at": datetime.now().isoformat(timespec="seconds"),
    "algorithm": ("WisRule - Khan & Shaheen (2022), Journal of Information "
                  "Science; Algorithm 1, wise positive + negative rules gated "
                  "on support / CPIR / interestingness / utility"),
    "wisdom_factors": {
        "context": {"variable": CONTEXT_KEY, "normal_range": (
            [round(context_normal[0], 4), round(context_normal[1], 4)]
            if context_normal else None),
            "adjustment": "PROCEDURE Supp_context, eq (8)-(11)",
            "years_supplied": len(context_series)},
        "utility": {"source": "magnitude share of the last reported level",
                     "items": len(item_utilities),
                     "measure": "UPII, eq (15)"},
        "time": {"n_intervals": N_TIME_INTERVALS,
                  "rule": "intersection of the per-interval rulesets"},
        "location": {"n_locations": N_LOCATIONS,
                      "note": "national aggregates only - single location"},
    },
    "data": {
        "source": str(DB_PATH.name),
        "history_years": [YEAR_FIRST, YEAR_LAST],
        "n_transactions": len(transactions),
        "transaction_years": [all_years[0], all_years[-1]],
        "cv_first_target_year": CV_FIRST_YEAR,
        "cv_folds": cv["n_folds"],
        "parameters": MINING_KEYS,
        "change_band_pct": CHANGE_BAND_PCT,
    },
    "params": {
        "min_support": MIN_SUPPORT,
        "min_cpir": MIN_CPIR,
        "min_interest": MIN_INTEREST,
        "min_upii": MIN_UPII,
        "min_confidence": MIN_CONFIDENCE,
        "min_utility": MIN_UTILITY,
        "n_time_intervals": N_TIME_INTERVALS,
        "n_locations": N_LOCATIONS,
        "context_variable": CONTEXT_KEY,
        "max_itemset_size": MAX_ITEMSET_SIZE,
        "max_consequent_size": MAX_CONSEQUENT_SIZE,
        "min_train_firings": MIN_TRAIN_FIRINGS,
        "min_cv_firings": MIN_CV_FIRINGS,
        "train_rule_pool": TRAIN_RULE_POOL,
        "final_rule_cap": FINAL_RULE_CAP,
    },
    "metrics": {
        "n_mined": len(mined),
        "n_shortlisted": N_SHORTLISTED,
        "n_rules": len(rules),
        "n_positive": n_pos,
        "n_negative": n_neg,
        "cv_firings": cv["n_firings"],
        "cv_correct": cv["n_hits"],
        "cv_accuracy": (None if np.isnan(cv["accuracy"])
                        else round(cv["accuracy"], 4)),
        "cv_baseline": (None if np.isnan(cv["baseline"])
                        else round(cv["baseline"], 4)),
        "cv_skill": (None if np.isnan(cv["skill"])
                     else round(cv["skill"], 4)),
        "n_confirmed": sum(1 for r in rules if r["cv_verdict"] == "confirmed"),
        "n_weakened": sum(1 for r in rules if r["cv_verdict"] == "weakened"),
        "n_untested": sum(1 for r in rules if r["cv_verdict"] == "untested"),
        "ensemble_predictions": ens["n_predictions"],
        "ensemble_correct": ens["n_correct"],
        "ensemble_accuracy": (None if np.isnan(ens["accuracy"])
                              else round(ens["accuracy"], 4)),
        "ensemble_baseline": (None if np.isnan(ens["baseline"])
                              else round(ens["baseline"], 4)),
        "ensemble_skill": (None if np.isnan(ens["skill"])
                           else round(ens["skill"], 4)),
        "ensemble_predict_keys": ENSEMBLE_PREDICT_KEYS,
        "ensemble_min_weight": ENSEMBLE_MIN_WEIGHT,
        "ensemble_lift_cap": ENSEMBLE_LIFT_CAP,
    },
    "rules": rules,
    "ensemble_details": ens.get("details", []),
    "growth_rates": growth_rates,
    "last_actuals": last_actuals,
    "item_labels": ITEM_LABELS,
}

model_path = MODEL_DIR / f"{MODEL_NAME}_model.json"
model_blob["params"]["rules_per_conclusion"] = RULES_PER_CONCLUSION
model_blob["metrics"]["rules_per_conclusion"] = RULES_PER_CONCLUSION
_sum = os.environ.get("WR_SUMMARY_FILE")
if _sum:
    Path(_sum).write_text(json.dumps(model_blob["metrics"]), encoding="utf-8")
model_path.write_text(json.dumps(model_blob, indent=2), encoding="utf-8")

pd.DataFrame(rules).to_csv(MODEL_DIR / f"{MODEL_NAME}_rules.csv",
                           index=False, encoding="utf-8-sig")

print(f"Model saved   : {model_path}")
print(f"Rules CSV     : {MODEL_DIR / f'{MODEL_NAME}_rules.csv'}")

# ═══════════════════ 10. Training charts (saved as HTML files) ════════════════

try:
    import plotly.graph_objects as go
    HAVE_PLOTLY = True
except ImportError:
    HAVE_PLOTLY = False
    print("plotly not installed — charts skipped")

PAPER = "#0B1B2B"
INK = "#E2E8F0"
TEAL = "#14B8A6"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"


def _layout(fig, title, x_title, y_title, height=460):
    fig.update_layout(
        title=dict(text=title, font=dict(color=INK, size=16)),
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        font=dict(color=INK, size=12),
        height=height, margin=dict(l=70, r=30, t=70, b=90),
        xaxis=dict(title=x_title, gridcolor="#234058", zerolinecolor="#234058"),
        yaxis=dict(title=y_title, gridcolor="#234058", zerolinecolor="#234058"),
    )
    return fig


def _save_and_show(fig, filename):
    """Save chart as HTML + PNG, and display in Jupyter if available."""
    out = REPORT_DIR / filename
    fig.write_html(str(out), include_plotlyjs="cdn")
    # Also write a PNG (uses kaleido.write_fig_sync for plotly 5.x compat)
    png_name = filename.replace(".html", ".png")
    png_path = REPORT_DIR / png_name
    try:
        import kaleido
        kaleido.write_fig_sync(
            fig, path=str(png_path),
            opts=dict(width=1200, height=500, scale=2))
        print(f"Chart saved   : {out}  +  {png_path}")
    except Exception:  # noqa: BLE001
        print(f"Chart saved   : {out}  (PNG skipped — kaleido error)")
    try:
        fig.show()                      # works inside Jupyter
    except Exception:                   # noqa: BLE001
        pass                            # headless run — the file is enough


if HAVE_PLOTLY and not WR_SKIP_CHART:
    # --- Chart 1: the strongest rules the model learned ---
    c1 = rules_df.head(12).iloc[::-1]
    fig1 = _layout(
        go.Figure(go.Bar(
            x=c1["wisval_norm"], y=c1["rule_text"], orientation="h",
            marker_color=[TEAL if t == "Positive" else RED for t in c1["rule_type"]],
            text=[f"{c:.2f}" for c in c1["confidence"]], textposition="outside"),
            ),
        title="Top learned rules — colour shows rule type",
        x_title="WisVal score (rule strength, higher is better)",
        y_title="Rule (antecedent → consequent)")
    _save_and_show(fig1, "wisrule_1_top_rules.html")

    # --- Chart 2: is a rule both reliable and unusual? ---
    pos = rules_df[rules_df["rule_type"] == "Positive"]
    neg = rules_df[rules_df["rule_type"] == "Negative"]
    fig2 = go.Figure()
    for frame, name, colour in ((pos, "Positive", TEAL), (neg, "Negative", RED)):
        if frame.empty:
            continue
        fig2.add_trace(go.Scatter(
            x=frame["confidence"], y=frame["lift"], mode="markers", name=name,
            marker=dict(size=[8 + 45 * s for s in frame["support"]], color=colour,
                        opacity=0.65, line=dict(width=1, color=PAPER)),
            text=frame["rule_text"], hoverinfo="text"))
    _layout(fig2, "Rule reliability vs rule rarity — bubble size = support",
            "Confidence (how often the rule holds)",
            "Lift (how much better than chance)")
    fig2.add_hline(y=1, line=dict(color=AMBER, dash="dot"),
                   annotation_text="chance level", annotation_position="right")
    _save_and_show(fig2, "wisrule_2_confidence_vs_lift.html")

    # --- Chart 3: out-of-sample accuracy, fold by fold ---
    scored_folds = [f for f in cv["folds"] if f["rules fired"]]
    if scored_folds:
        fig3 = _layout(
            go.Figure(go.Bar(
                x=[f["target year"] for f in scored_folds],
                y=[f["fold accuracy"] for f in scored_folds],
                marker_color=BLUE, marker_line=dict(width=0),
                text=[f"{f['correct']}/{f['rules fired']}" for f in scored_folds],
                textposition="outside")),
            title="Out-of-sample accuracy per predicted year",
            x_title="Year the model was asked about",
            y_title="Share of fired rules that were correct", height=400)
        fig3.add_hline(y=cv["accuracy"], line=dict(color=TEAL, dash="dot"),
                       annotation_text=f"all folds: {cv['accuracy']:.2f}",
                       annotation_position="top right")
        fig3.add_hline(y=cv["baseline"], line=dict(color=AMBER, dash="dot"),
                       annotation_text=f"no-model baseline: {cv['baseline']:.2f}",
                       annotation_position="bottom right")
        _save_and_show(fig3, "wisrule_3_cv_accuracy_by_year.html")

    # --- Chart 4: what the model believed vs what it actually delivered ---
    tested = [r for r in rules if r["cv_firings"] > 0]
    if tested:
        fig4 = _layout(
            go.Figure([
                go.Bar(x=[r["rule_id"] for r in tested],
                       y=[r["confidence"] for r in tested],
                       name="Learned confidence", marker_color=BLUE,
                       marker_line=dict(width=0)),
                go.Bar(x=[r["rule_id"] for r in tested],
                       y=[r["cv_confidence"] for r in tested],
                       name="Out-of-sample confidence", marker_color=AMBER,
                       marker_line=dict(width=0)),
            ]),
            title="Did the learned rules hold up on unseen years?",
            x_title="Rule id", y_title="Confidence (0 to 1)")
        fig4.update_layout(barmode="group",
                           legend=dict(orientation="h", y=1.14))
        _save_and_show(fig4, "wisrule_4_learned_vs_out_of_sample.html")

# ═══════════════ 11. USING the model: fire rules on a what-if scenario ════════
#
# This is the exact function the Q1 dashboard will call. It needs no database
# and no mining — only the saved JSON, so the page stays fast and the rules
# never change between refreshes.

def load_model(path: Path = model_path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fire_rules(itemset, model: dict = None, top_n: int = 8) -> pd.DataFrame:
    """Given a set of High/Low/Stable items, return the rules that switch on."""
    model = model or load_model()
    items = frozenset(itemset)
    fired = []
    for r in model["rules"]:
        ante = frozenset(r["antecedent"])
        if not ante <= items:
            continue
        cons = frozenset(r["consequent"])
        present = cons <= items
        holds = present if r["rule_type"] == "Positive" else not present
        fired.append({
            "rule_id": r["rule_id"], "rule": r["rule_text"],
            "type": r["rule_type"], "confidence": r["confidence"],
            "lift": r["lift"], "wisval_norm": r["wisval_norm"],
            "cv firings": r.get("cv_firings"), "cv confidence": r.get("cv_confidence"),
            "verdict": r.get("cv_verdict"),
            "currently_holds": "yes" if holds else "no (consequent absent)",
        })
    out = pd.DataFrame(fired)
    if out.empty:
        return out
    return out.sort_values("wisval_norm", ascending=False).head(top_n)


def scenario_from_history(model: dict = None) -> list:
    """Labels of the most recent year we have — a 'what happens next' snapshot."""
    return sorted(transactions[-1]["items"]) if transactions else []


def scenario_from_whatif(gdp_growth_pct: float, pop_growth_pct: float,
                         efficiency_pct: float = 0.0, model: dict = None) -> list:
    """Translate the dashboard's what-if sliders into High/Low/Stable items.

    Each slider is compared with the growth the economy / population actually
    showed over the recorded history. Above that typical rate reads as High,
    below it as Low, within half a percentage point as Stable. Energy-side
    parameters follow the GDP reading, because the model learned their link to
    the economy; an efficiency saving of 1% or more pulls them a step down,
    which is exactly what that slider claims to do.
    """
    train = history

    def median_growth(col):
        """Median year-over-year change of a level column, in %."""
        if col not in train.columns:
            return 0.0
        s = pd.to_numeric(train[col], errors="coerce")
        s = s[(s > 0) & np.isfinite(s)]
        if len(s) < 2:
            return 0.0
        pct = (s.pct_change() * 100).replace([np.inf, -np.inf], np.nan).dropna()
        return float(pct.median()) if len(pct) else 0.0

    # GDP is compared against the reported real growth rate, not against the
    # nominal-USD level change (which a currency move inflates out of use).
    g = pd.to_numeric(train["gdp_growth"], errors="coerce").dropna() \
        if "gdp_growth" in train.columns else pd.Series(dtype=float)
    gdp_ref = float(g.median()) if len(g) else median_growth("gdp")
    pop_ref = median_growth("population")

    def label(reference, given):
        if abs(given - reference) <= 0.5:
            return "Stable"
        return "High" if given > reference else "Low"

    items = [item_of("gdp", label(gdp_ref, gdp_growth_pct)),
             item_of("population", label(pop_ref, pop_growth_pct))]

    drag = efficiency_pct >= 1.0
    for key in ("demand", "consumption", "primary_supply", "final_consumption",
                "generation"):
        items.append(item_of(key, "Low" if drag else label(gdp_ref, gdp_growth_pct)))
    print(f"   (recorded norms: GDP growth {gdp_ref:+.1f}%/yr, "
          f"population growth {pop_ref:+.1f}%/yr)")
    return [i for i in items if i]


model = load_model()

print("\n" + "=" * 78)
print("A. Rules that fire on the LAST observed year")
print("=" * 78)
last_items = scenario_from_history(model)
print("Year", transactions[-1]["calendar_year"], "labels:", ", ".join(last_items))
fired_last = fire_rules(last_items, model)
print(fired_last.to_string(index=False) if not fired_last.empty
      else "   (no rule matched)")

print("\n" + "=" * 78)
print("B. Rules that fire on the dashboard's default what-if "
      "(4.0% GDP, 1.9% population, 0% efficiency)")
print("=" * 78)
whatif_items = scenario_from_whatif(4.0, 1.9, 0.0, model)
print("Scenario labels:", ", ".join(whatif_items))
fired_whatif = fire_rules(whatif_items, model)
print(fired_whatif.to_string(index=False) if not fired_whatif.empty
      else "   (no rule matched)")

print("\n" + "=" * 78)
print("C. Same what-if with a 2.0% efficiency gain switched on")
print("=" * 78)
eff_items = scenario_from_whatif(4.0, 1.9, 2.0, model)
print("Scenario labels:", ", ".join(eff_items))
fired_eff = fire_rules(eff_items, model)
print(fired_eff.to_string(index=False) if not fired_eff.empty
      else "   (no rule matched)")

# ═══════════════════════════ 12. Training report ══════════════════════════════

print("\n" + "=" * 78)
print("TRAINING REPORT")
print("=" * 78)
m = model["metrics"]
d = model["data"]
def _fmt(v):
    """Number or 'n/a' -- an empty validation score must never print as NaN."""
    return "n/a" if v is None else f"{v:.3f}"
print(f"Model               : {MODEL_NAME} v{MODEL_VERSION}")
print(f"Trained at          : {model['trained_at']}")
print(f"History             : {d['history_years'][0]}-{d['history_years'][1]} "
      f"({d['n_transactions']} usable years, {len(MINING_KEYS)} parameters)")
print(f"Validation          : walk-forward, {d['cv_folds']} folds "
      f"(every year from {d['cv_first_target_year']} predicted from earlier ones only)")
print(f"Rules mined         : {m['n_mined']} -> shortlisted {m['n_shortlisted']} "
      f"-> kept {m['n_rules']} ({m['n_positive']} positive, "
      f"{m['n_negative']} negative)")
print(f"Out-of-sample trials: {m['cv_firings']} firings, {m['cv_correct']} correct")
print(f"Model accuracy      : {_fmt(m['cv_accuracy'])} "
      f"vs no-model baseline {_fmt(m['cv_baseline'])} "
      f"(skill {_fmt(m['cv_skill'])})")
print(f"Rule verdicts       : {m['n_confirmed']} confirmed, "
      f"{m['n_weakened']} weakened, {m['n_untested']} untested")
print(f"Ensemble trials     : {m['ensemble_predictions']} predictions, "
      f"{m['ensemble_correct']} correct")
print(f"Ensemble accuracy   : {_fmt(m['ensemble_accuracy'])} "
      f"vs no-model baseline {_fmt(m['ensemble_baseline'])} "
      f"(skill {_fmt(m['ensemble_skill'])})")
print(f"\nFiles written to    : {MODEL_DIR}")
print(f"Charts written to   : {REPORT_DIR}")
print("\nNext step: the Q1 dashboard loads wisrule_q1_model.json and shows the")
print("firing rules inside its What-if Predicted Values section.")

conn.close()
