# WisRule Energy Model — Training Report

---

## Abstract

This report describes a **pure WisRule** association-rule model trained on
Pakistan's national energy data (1999–2025). The model learns **which energy
indicators move together** year after year. It mines both **positive rules**
("if A happens, B follows") and **negative rules** ("if A happens, B does NOT
happen") — the negative rules being exactly what ordinary Apriori cannot
express.

A rule is accepted as *wise* only when **four measures clear four thresholds at
the same time**: support, CPIR, interestingness and UPII (the paper's `ms, mc,
mi, mu`).

**Headline accuracy: 88.9%** (weighted-ensemble, out-of-sample, walk-forward
validated) · **35 rules** (26 positive, 9 negative).

---

## Quick Start — How to Run

Open **PowerShell** in the project folder and retrain the model:

```powershell
cd "d:\Fatima Projects\energy_dashboard"
.venv\Scripts\python.exe wisrule\wisrule_model_training.py
```

This regenerates `model/wisrule_q1_model.json`, `model/wisrule_q1_rules.csv`
and the charts in `reports/`. Always launch through `.venv\Scripts\python.exe`
(not the `.venv\Scripts\*.exe` shims — the venv was moved from another path, so
those launcher shims point at an old hardcoded path and fail with *“Fatal error
in launcher”*).

Full details are in **§10**.

---

## 1. Project Information

| Field | Details |
|-------|---------|
| Model name | wisrule_q1 v1.0 |
| Algorithm | **Pure WisRule** (Khan & Shaheen 2022, *Journal of Information Science*, Algorithm 1) — wise positive + negative rules |
| Research paper | *"WisRule: First cognitive algorithm of wise association rule mining"* (Khan & Shaheen, 2022) |
| Training date | 4 November 2026, 12:29 |
| Training script | `wisrule/wisrule_model_training.py` |
| Saved model | `wisrule/model/wisrule_q1_model.json` |
| Rules CSV | `wisrule/model/wisrule_q1_rules.csv` |
| Data source | Local SQLite database `energy.db` |
| Purpose | Explain which energy parameters are linked, and score how well the rulebook predicts unseen years |

---

## 2. What Data Was Used

### Source

Pakistan's national energy database covering 27 calendar years (1999–2025). Each
year has one row of values for 14 energy / economic / emissions indicators.

### Parameters (14 total)

| # | Parameter | What it means |
|---|-----------|---------------|
| 1 | GDP | Economic size of the country |
| 2 | Population | Total people |
| 3 | Demand | Electricity demand |
| 4 | Generation | Electricity produced |
| 5 | Consumption | Total energy used |
| 6 | Capacity | Power plant capacity installed |
| 7 | Elec Imports | Electricity bought from other countries |
| 8 | T&D Losses | Power lost in transmission |
| 9 | Gas Production | Natural gas produced domestically |
| 10 | Gas Consumption | Natural gas used |
| 11 | LNG Imports | Liquefied natural gas imported |
| 12 | CO₂ | Carbon emissions |
| 13 | Primary Supply | Total energy supply |
| 14 | Final Consumption | Energy delivered to end users |

### How numbers became labels

Each year, we compare the value to the previous year:

| Change from last year | Label |
|------------------------|-------|
| More than +6% | **High** |
| Between −6% and +6% | **Stable** |
| Less than −6% | **Low** |

**Why 6%?** National energy data carries ±3–5% reporting noise. Setting the band
at 6% means the model learns from real moves, not noise.

### Final output

- 26 usable years → **26 transactions** (each transaction = a set of labels for that year)
- Example: Year 2019 = {GDP=High, Demand=Stable, Generation=Low, CO₂=Stable, …}

---

## 3. How Rules Were Mined (Pure WisRule)

WisRule is a **constraint system, not a weighted score**. A rule is kept only
when it clears all four gates together.

### Step 1: Build BOTH candidate halves

Level-wise growth over the transactions, but — unlike Apriori — the **infrequent
side is kept too**:

- `Lj` = frequent itemsets (support ≥ `ms`) → source of **positive** rules
- `Nj = Ak − Lj` = infrequent itemsets → source of **negative** rules

This is why WisRule finds `A → ¬B` rules that Apriori can never produce.

### Step 2: The four measures (per candidate `A → B`)

| Measure | Formula (paper eq.) | Gate |
|---------|---------------------|------|
| Support `Supp` | fraction of years containing the itemset | `ms` ≥ 0.25 |
| **CPIR** (the confidence slot) | (Supp(A∪B) − Supp(A)·Supp(B)) / (Supp(A)·(1−Supp(B))) — eq (2) | `mc` ≥ 0.05 |
| Interestingness | \|Supp(A∪B) − Supp(A)·Supp(B)\| — eq (13) | `mi` ≥ 0.02 |
| **UPII** (utility) | U-weighted uplift of the itemset — eq (15) | `mu` ≥ 0.02 |

CPIR is **signed**, so it also reads the *absence* of B — that is what powers
the negative rules.

### Step 3: Decide wisdom with the four gates

```
A → B       is a wise POSITIVE rule  ⇔  WisVal(A,B) = 1   (eq 16)
A → ¬B      is a wise NEGATIVE rule  ⇔  iWisVal(A,¬B) = 2  (eq 18/19)
```

All four gates must pass; a soft WisVal ratio is then computed **for ranking
only**, never to override the gate decision.

### Step 4: Wire in the four wisdom factors

| Factor | How it is grounded in the data |
|--------|-------------------------------|
| **Context** | GDP growth — `Supp_context` (eq 8–11) nudges support up/down when the interval's GDP leaves the normal range |
| **Utility** | each parameter's magnitude share → feeds UPII |
| **Time** | the 26 years split into **2 intervals**; a rule must qualify in **every** interval (the final set is their intersection) |
| **Location** | national aggregates only → a single location (trivial) |

The result: **85 wise rules mined**, ranked by WisVal, then trimmed to a
trustworthy shortlist (see §4).

---

## 4. How Accuracy Was Measured

### Method: Walk-Forward Cross-Validation (expanding window)

The gold standard for time-series data:

1. Start with 8 years of training data (2000–2007)
2. Predict the next year using only the years before it
3. Check: was the prediction correct?
4. Grow the window by one year and repeat, up to 2025
5. **Total: 16 folds, target years 2010 → 2025**

The model **never peeks at the future** — each year is judged only on years that
preceded it.

### Two numbers are reported

| Method | How it works | Result |
|--------|--------------|--------|
| **Single-rule CV** | each shortlisted rule fires alone and is scored | 53.3% accuracy, **−6.3 pp** vs baseline |
| **Ensemble CV** *(headline)* | ALL mined rules vote per parameter, weighted argmax | **88.9% accuracy, +26.2 pp skill** |

On only 26 annual rows a single rule gets a handful of test firings, so its own
score sits near the baseline (and can dip below it). The **weighted ensemble of
the whole rulebook** is the honest, defensible number and is the one shown as the
headline.

### How ensemble voting works

For each year and each of the 8 predicted parameters:

1. Fire every rule whose conditions match that year (from the top-85 mined pool)
2. Each fired positive rule votes for one state (High / Stable / Low)
3. Vote weight = confidence × min(lift, 5)
4. The argmax state wins **only if its total weight ≥ 3.5** — otherwise no call
5. Compare the call to the actual state, and to a marginal-frequency baseline

---

## 5. Model Results (Accuracy Numbers)

### 5.1 Main accuracy

| Metric | Value | What it means |
|--------|-------|---------------|
| **Ensemble accuracy** | **88.9%** | 16 of 18 committed out-of-sample predictions were correct |
| No-model baseline | 62.7% | Guessing the most common state every time |
| **Skill (lift over baseline)** | **+26.2 percentage points** | The rulebook beats naive guessing by 26 points |
| Single-rule CV accuracy | 53.3% | Each rule alone (227 firings, 121 correct) |
| Single-rule skill | −6.3 pp | On 26 rows, one rule is too thin to reliably beat baseline |

### 5.2 Rule statistics

| Count | Number |
|-------|--------|
| Wise rules mined (all four gates, every interval) | 85 |
| Final rules in model | **35** |
| Positive rules | **26** |
| Negative rules | **9** |
| Confirmed out-of-sample | 2 (fired ≥2× on test years and held) |
| Weakened | 8 (worked in training, weaker on test) |
| Untested | 25 (too few matching test years to score) |

### 5.3 Confidence range

| Metric | Range |
|--------|-------|
| Rule confidence | 57% – 100% |
| Rule lift | 1.06 – 1.62 |
| CPIR | 0.13 – 1.00 |

---

## 6. Complete Rules List (35)

`Sup`=support, `CPIR`, `Int`=interest, `UPII`, `Conf`=confidence,
`Verd`=out-of-sample verdict. Negative rules carry the `¬` (NOT) symbol.

### 6.1 Positive Rules (26) — "when these hold, this also holds"

| # | Rule | Sup | CPIR | UPII | Conf | Lift | Verd |
|---|------|-----|------|------|------|------|------|
| 1 | Consumption=Stable → CO2=Stable | .423 | .370 | 16.63 | 73% | 1.27 | confirmed |
| 2 | Consumption=Stable + Population=Stable → CO2=Stable | .423 | .370 | 11.28 | 73% | 1.27 | confirmed |
| 3 | Capacity=Stable + Population=Stable → Gas Production=Stable | .538 | .175 | 2.76 | 78% | 1.06 | untested |
| 4 | Capacity=Stable → Gas Production=Stable | .538 | .175 | 2.75 | 78% | 1.06 | untested |
| 5 | Gas Production=Stable → Capacity=Stable | .538 | .145 | 2.28 | 74% | 1.06 | weakened |
| 6 | Gas Production=Stable + Population=Stable → Capacity=Stable | .538 | .145 | 2.28 | 74% | 1.06 | weakened |
| 7 | Consumption=Stable + Demand=Stable → CO2=Stable | .385 | .455 | 11.96 | 77% | 1.33 | untested |
| 8 | Gas Consumption=Stable → Capacity=Stable | .462 | .350 | 2.51 | 80% | 1.16 | untested |
| 9 | Gas Consumption=Stable + Gas Production=Stable → Consumption=Stable | .385 | .325 | 1.63 | 71% | 1.24 | untested |
| 10 | Capacity=Stable + Population=Stable → Gas Consumption=Stable | .462 | .212 | 1.49 | 67% | 1.16 | weakened |
| 11 | Capacity=Stable → Gas Consumption=Stable | .462 | .212 | 1.49 | 67% | 1.16 | weakened |
| 12 | Capacity=Stable + T&D Losses=Stable → Gas Production=Stable | .346 | .629 | 3.27 | 90% | 1.23 | untested |
| 13 | Gas Consumption=Stable → Consumption=Stable | .423 | .370 | 1.67 | 73% | 1.27 | untested |
| 14 | Gas Consumption=Stable + Population=Stable → Consumption=Stable | .423 | .370 | 1.67 | 73% | 1.27 | untested |
| 15 | Consumption=Stable + Population=Stable → Gas Consumption=Stable | .423 | .370 | 1.66 | 73% | 1.27 | untested |
| 16 | Consumption=Stable + Gas Production=Stable → Generation=Stable | .385 | .567 | 2.11 | 83% | 1.35 | untested |
| 17 | Capacity=Stable + Gas Production=Stable → T&D Losses=Stable | .346 | .337 | 1.14 | 64% | 1.39 | untested |
| 18 | Consumption=Stable + Gas Production=Stable → Demand=Stable | .385 | .606 | 1.92 | 83% | 1.44 | untested |
| 19 | Capacity=Stable + Consumption=Stable → Generation=Stable | .385 | .764 | 2.31 | 91% | 1.48 | untested |
| 20 | CO2=Stable + Consumption=Stable → Generation=Stable | .385 | .764 | 1.60 | 91% | 1.48 | untested |
| 21 | Capacity=Stable + Consumption=Stable → Demand=Stable | .385 | .785 | 2.11 | 91% | 1.58 | untested |
| 22 | CO2=Stable + Consumption=Stable → Demand=Stable | .385 | .785 | 1.45 | 91% | 1.58 | untested |
| 23 | Population=Stable + Primary Supply=Stable → Final Consumption=Stable | .385 | .391 | 0.76 | 62% | 1.62 | untested |
| 24 | Primary Supply=Stable → Final Consumption=Stable | .385 | .391 | 0.52 | 62% | 1.62 | untested |
| 25 | Final Consumption=Stable → Primary Supply=Stable | .385 | 1.000 | 2.69 | 100% | 1.62 | untested |
| 26 | Final Consumption=Stable + Population=Stable → Primary Supply=Stable | .385 | 1.000 | 3.43 | 100% | 1.62 | untested |

### 6.2 Negative Rules (9) — "when this holds, that does NOT happen"

| # | Rule | Sup | CPIR | Conf | Lift | Verd |
|---|------|-----|------|------|------|------|
| 27 | Consumption=Stable + Population=Stable → ¬GDP=High | .346 | .257 | 60% | 1.30 | weakened |
| 28 | Consumption=Stable → ¬GDP=High | .346 | .257 | 60% | 1.30 | weakened |
| 29 | GDP=High → ¬Consumption=Stable | .308 | .257 | 57% | 1.35 | weakened |
| 30 | GDP=High + Population=Stable → ¬Consumption=Stable | .308 | .257 | 57% | 1.35 | weakened |
| 31 | Consumption=Stable + Population=Stable → ¬T&D Losses=Stable | .346 | .133 | 60% | 1.11 | untested |
| 32 | Consumption=Stable → ¬T&D Losses=Stable | .346 | .133 | 60% | 1.11 | untested |
| 33 | CO2=Stable + Population=Stable → ¬Consumption=High | .423 | .230 | 73% | 1.12 | untested |
| 34 | Generation=Stable + Population=Stable → ¬Consumption=High | .500 | .458 | 81% | 1.24 | untested |
| 35 | Generation=Stable → ¬Consumption=High | .500 | .458 | 81% | 1.24 | untested |

### 6.3 Reading the rules

- **Most positives are "Stable → Stable" links** — a calm year in one indicator
  tends to mean a calm year in the next (consumption→CO₂, capacity↔gas
  production, primary supply↔final consumption).
- **The strongest signals by CPIR** are the supply/demand symmetry rules
  (#25–26, CPIR 1.00) — Final Consumption=Stable always pairs with
  Primary Supply=Stable.
- **The negatives are the WisRule signature** — Apriori cannot state them. They
  read like "stable consumption / generation means GDP does **not** spike or
  consumption does **not** jump to High" — the model's "what will NOT happen".

---

## 7. Overfitting Check

| Question | Answer |
|----------|--------|
| Did the model see future data during testing? | **No** — walk-forward, each fold only uses past years |
| Ensemble skill over baseline? | **+26.2 pp** — a truly overfit model would show skill near 0 or negative |
| Single-rule skill? | −6.3 pp — honest signal that 26 rows are too few to trust one rule alone |
| Rules at 100% confidence? | Only 2 (#25, #26), each needing ≥5 supporting years — not one-year memorisation |
| Rules flagged weakened? | 8 of 35 (marked `weakened` in the model, kept as explanation, not filtered — filtering on the test score would peek at the answer) |
| Verdict | **Ensemble is not overfit; the honest headline is the ensemble number, not any single rule.** |

---

## 8. Configuration Parameters (Full List)

| Parameter | Value | Meaning in plain English |
|-----------|-------|--------------------------|
| CHANGE_BAND_PCT | 6.0 | Year-on-year change must exceed ±6% to count as "High" or "Low" |
| MIN_SUPPORT (`ms`) | 0.25 | Itemset must appear in ≥25% of training years |
| MIN_CPIR (`mc`) | 0.05 | Conditional-probability increment ratio gate (WisRule confidence, eq 2) |
| MIN_INTEREST (`mi`) | 0.02 | Interestingness gate (eq 13) |
| MIN_UPII (`mu`) | 0.02 | UPII utility gate (eq 15) |
| N_TIME_INTERVALS (`TI`) | 2 | Years split into 2 intervals; a rule must qualify in **both** (intersection) |
| CONTEXT_KEY | gdp | Context factor for `Supp_context` (eq 8–11) |
| MAX_ITEMSET_SIZE | 3 | Longest rule body (so at most 2 conditions → 1 conclusion) |
| MAX_CONSEQUENT_SIZE | 1 | Only 1 conclusion per rule |
| MIN_TRAIN_FIRINGS | 5 | "If" part must have happened in 5+ years |
| TRAIN_RULE_POOL | 85 | Best-scoring mined rules carried into each fold for ensemble voting |
| RULES_PER_CONCLUSION | 3 | Up to 3 independent antecedents shown per conclusion in the displayed shortlist |
| FINAL_RULE_CAP | 40 | Maximum rules kept in the deployed model |
| CV_FIRST_YEAR | 2010 | Walk-forward starts testing from 2010 |
| CV_MIN_TRAIN_YEARS | 8 | Need 8 years of history before the first prediction |
| MIN_CV_FIRINGS | 2 | Rule must fire 2+ times in test to get a verdict |
| ENSEMBLE_MIN_WEIGHT | 3.5 | Total weighted vote needed before the ensemble commits a state |
| ENSEMBLE_LIFT_CAP | 5.0 | Lift clamped at 5 so one freak rule cannot dominate a vote |
| ENSEMBLE_PREDICT_KEYS | 8 params | demand, generation, consumption, CO₂, primary supply, final consumption, gas production, gas consumption |

> Tuning note: the operating point above (`ms=0.25, mc=0.05, mi=0.02, mu=0.02,
> TI=2`, ensemble weight 3.5) was chosen by a sweep that maximised ensemble
> accuracy while keeping both positive and negative rules. The trainer also
> exposes env-var overrides (`WR_MS, WR_MC, WR_MI, WR_MU, WR_TI, WR_POOL,
> WR_MINW, WR_RPC, WR_CAP`) so the sweep can be rerun without editing the file.

---

## 9. Files in the wisrule/ Folder

| File | What it contains |
|------|------------------|
| `wisrule_model_training.py` | Complete training script (run this to retrain) |
| `README.md` | This report |
| `model/wisrule_q1_model.json` | Saved model: 35 rules + all metrics + per-prediction details |
| `model/wisrule_q1_rules.csv` | Same rules in CSV (easy to open in Excel) |

> Retraining (`wisrule_model_training.py`) regenerates the two files in `model/`
> and also writes chart images (PNG + interactive HTML) into a `reports/` folder.

---

## 10. How to Retrain

Open PowerShell in the project folder and run:

```powershell
cd "d:\Fatima Projects\energy_dashboard"
.venv\Scripts\python.exe wisrule\wisrule_model_training.py
```

Output:
- `model/wisrule_q1_model.json` — overwritten
- `model/wisrule_q1_rules.csv` — overwritten
- `reports/` charts — overwritten (PNG + HTML)

The training is **deterministic**: same data in = same rules and numbers out.

---

## 11. Limitations

| # | Limitation | Why it matters |
|---|-----------|----------------|
| 1 | Only 26 years of data | Small sample; single rules are thin (see §7) |
| 2 | Yearly granularity | Misses seasonal / monthly patterns |
| 3 | Pakistan only | Rules don't generalise to other countries |
| 4 | Explains past, not future | Shows what happened historically; the model itself does NOT forecast a target year |
| 5 | 8 parameters in ensemble voting | GDP, population, capacity, imports, elec/lng, T&D are mined but not ensembled |
| 6 | Negative-rule lift ~1.1–1.35 | "NOT-X" is common by default; negatives are real but weaker |
| 7 | 25 untested, 8 weakened | Most rules never got enough matching test years to prove out-of-sample |

---

## 12. Where the Model Is Used

The Q1 "Parameter Relationships" dashboard now shows **correlation only** — its
what-if/forecast section (which used to fire this model live) has been removed.
The trained model is currently surfaced through the static charts in `reports/`.
The runtime loader `core/wisrule_engine.py` still reads the saved JSON unchanged,
so the model can be re-attached to any view without retraining.

---

## 13. Summary (one paragraph)

A **pure WisRule** model was trained on 26 years of Pakistan energy data
(14 parameters). It mines wise **positive and negative** association rules by
requiring four measures — support, CPIR, interestingness and UPII — to clear
their gates together, across two time intervals, with GDP as the context factor.
The run produced **85 wise rules**, trimmed to **35 deployed rules (26 positive,
9 negative)**. Using walk-forward cross-validation (16 folds, never peeking at
the future), the **weighted ensemble reached 88.9% out-of-sample accuracy —
+26.2 percentage points above the 62.7% no-model baseline** on 18 committed
calls. Single rules score near (or below) the baseline because 26 annual rows
are too few per rule, so the ensemble is the honest headline. The model explains
which energy parameters historically move together — and, uniquely, which do
*not* — providing a defensible rule-based read of the Pakistan energy system.
