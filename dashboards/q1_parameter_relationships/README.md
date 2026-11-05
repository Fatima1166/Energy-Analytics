# Q1 — Energy Parameter Relationships

Answers the first half of Question 1: *"What have been the relationships among
different parameters of energy over a given period of time?"*

This page only measures **how the parameters move together** in history. The
what-if forecast half of the question is served by Q4 (demand), Q5 (supply) and
Q7 (cost), so nothing here predicts the future.

---

## 1. Algorithms & formulas

| Technique | Formula / rule |
|---|---|
| **Pearson correlation** | For each parameter pair: `r = cov(A, B) / (σA · σB)` — computed with `np.corrcoef` on the years where **both** parameters have a real value. `r = +1` moves together, `r = −1` moves opposite. |
| **Pair minimum** | A pair needs at least **6 shared years** (`MIN_PAIR_OBS`) and some variation in both columns, otherwise its cell stays blank (NaN) — never a fake r. |
| **OLS pair fit** | Straight-line fit `y = a + b·x` over the period using `np.polyfit(x, y, 1)`. Reported with `r`, `R² = r × r`, slope `b` and the point count `n`. |
| **Rolling correlation** | The same Pearson r, recomputed over a sliding window of years, to show whether a link is stable or keeps flipping. |
| **Strongest / weakest pair** | Scan the matrix (diagonal excluded) for the largest and smallest `|r|` cells. |

Parameters come from 7 warehouse queries merged on `calendar_year` into one
frame of 19 tracked columns (levels like GDP, demand, generation, plus derived
ratios like renewable share and per-capita demand).

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Parameters Analysed** | count of parameters that have any correlation computed in the period | pairwise links = `n·(n−1)/2` · strong links with `|r| ≥ 0.7` · rolling window in years |
| **K2 — Strongest Relationship** | the maximum `r` in the matrix (`+0.91` style) | driver name · response name · nature: "co-moving" if r > 0, "inverse" if r < 0 |
| **K3 — Weakest Relationship** | the minimum `|r|` among all tested pairs | the two parameter names · how many links were tested |

K2 prints "not enough overlap" when the period is too short to compute any pair.

**Derived-ratio guard:** ratios such as renewable share or per-capita demand are
built from parameters already on the page, so a link involving one is partly
self-referential. They stay in the heat-map, ranking and histogram, but are
**never** picked as the K2 headline or the Pair Explorer pair
(`DERIVED_KEYS` exclusion in the engine).

---

## 3. Visuals

Row order: KPI strip (K1 | K2 | K3) → V1 full width → V7 | V8 → V2 | V3.

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Correlation heat-map | Parameter × parameter grid of Pearson r. Green = co-moving, red = inverse, blank = not enough shared years. |
| **V7** | Top relationship ranking | Horizontal lollipop of the twelve strongest `|r|` links, longest = strongest. |
| **V8** | Correlation distribution | Histogram of every computable pairwise r, split into co-moving (positive) vs inverse (negative). |
| **V2** | Pair explorer | Scatter of the headline pair with the OLS line `y = a + b·x` drawn over it; the note shows r, R² and slope. |
| **V3** | Rolling correlation | One line: Pearson r of the headline pair recomputed over each sliding year window. Flat = stable link, wavy = fragile link. |

V2 and V3 always follow the automatically chosen strongest pair — there is no
manual pair picker anywhere on the page.

---

## 4. Period handling

- The period is one two-handle range slider in the sidebar.
- The engine needs 6 joint years for any correlation, so a narrower pick is
  pushed back to a minimum **8-year span** (`MIN_SPAN`) by an `on_change`
  callback — the handles always show what was actually analysed.
- The rolling window adapts to the span: `window = clip(span // 2, 4, 7)` years,
  so the stability line always has enough points.

---

## 5. Data

`Q_ECONOMIC`, `Q_RENEWABLE_ENERGY`, `Q_ELEC_GEN`, `Q_TD_LOSSES`,
`Q_NATURAL_GAS`, `Q_LNG`, `Q_ENERGY_OVERVIEW`, `Q_CO2` — merged on
`calendar_year`.

---

## 6. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/parameter_relationships.py`](../../core/parameter_relationships.py) | parameter frame, Pearson matrix, OLS fits, rolling stability |
| Charts | `charts.py` | five dumb Plotly visuals (no analytics) |
| Page | `page.py` | period control, KPI strip, chart rows |
| Verify | [`scripts/verify_q1_relationships.py`](../../scripts/verify_q1_relationships.py) | standalone MySQL audit of the engine |

Base units TOE · GWh · MW · USD — see [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
