# Q8 — Sustainable Energy Strategy

**Question:** *What optimal strategy may be opted to make energy development
sustainable?*

The page scores where the energy system stands on four pillars, works out which
measures buy the most progress per year's money, and shows where that package
leads by the horizon year:

```
the plan = the measures, best value first, until the yearly budget runs out
```

Check the rules any time: `.venv\Scripts\python.exe scripts\verify_q8_strategy.py`

---

## 1. Algorithms & formulas

### The four pillars (each 0–100)

Each pillar is the mean of its measured components. Where an agreed benchmark
exists it is used directly; otherwise the component is auto-calibrated on
Pakistan's own **10th–90th percentile**, so the best year in the record always
scores 100. The score is out of 100, **not a percentage of sustainability**.

| Pillar | Components (years reported) |
|---|---|
| Supply security | import dependence (2002–18), gas self-sufficiency (1999–18), generation diversity (1999–24) |
| Affordability | grid T&D efficiency (2002–19), LNG unit price (2014–18) |
| Clean power | renewable share of electricity (2000–24) |
| Access | electricity per person, demand coverage (2002–23) |

CO₂ intensity is deliberately **not** a component: the warehouse holds national
CO₂ (all fuels, all sectors) against electricity-only generation, a scope
mismatch that would score 0 every year. The weighted score needs all four
pillars; each pillar carries its own last reported value forward, and every
card and axis prints which year each number really came from.

### What a measure is worth (the ranking)

```
weighted impact = Σ (pillar weight × points the measure adds to that pillar)
value density   = weighted impact / cost per year × delivery confidence
```

`select_optimal_package()` walks that ranking top-down and buys any measure that
still fits the yearly envelope — a **greedy knapsack**. Effects are discounted by
the same delivery confidence when applied to the pillars.

### The three paths

Every pillar drifts on its own last eight reported years, slope clamped to
**−1.0 … +1.5 points/yr**:

- **If nothing changes** — the drift alone.
- **Only what is already promised** — funded measures ≥ 60% deliverable, at half effect.
- **The recommended package** — every funded measure at full effect, ramped in over
  three years after each measure's lead time.

All three share the same reported history, so the gap between the lines is the
plan and nothing else.

### Presets (pillar weights: security / affordability / clean / access)

Balanced 30/25/25/20 · Clean most 20/20/45/15 · Security most 45/25/15/15 ·
Affordability most 20/45/15/20 · Access most 20/20/15/45.

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Where things stand** | weighted pillar score, `/100`, for the latest year the four pillars could form | lowest & highest pillar behind it · how many of the 4 pillars that year actually reported |
| **K2 — What the plan reaches** | score at the horizon under the recommended package | the same score if nothing changes · the gap between them · how many of the 13 measures get funded |
| **K3 — What the plan costs a year** | money the funded measures take, US$ bn/yr | what was asked for · what was left over · how many measures were put off |

Default view (Balanced, 8 US$ bn/yr, horizon 2035): K1 = 71.9 · K2 = 94.1 vs
82.0 unchanged (+12.1), 8 of 13 funded · K3 = 7.90 of 8.0 bn, 0.10 left, 5 put off.
At this budget the cheap reforms out-rank the big builds: grid-loss fixes,
efficiency, rooftop solar and tariff reform get funded while solar/wind farms,
hydro, storage, gas drilling and nuclear are deferred.

---

## 3. Visuals

Two rows of two, then the funded list full width: **V1 | V2**, **V3 | V4**, V5 + list.

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Where each pillar stands | Each pillar's latest score against ten years earlier, labelled with its own year and how many measures back it. |
| **V2** | What each option buys per dollar | All 13 measures ranked by value density (points added per $bn/yr); green = funded, grey = deferred. |
| **V3** | The measures behind each pillar | Heat-map: every measure's 0–100 score in its pillar's latest reported year — low cells show what holds a pillar down. No legend needed; pillar groups are separated by gaps. |
| **V4** | What the plan changes | Points each pillar gains by the horizon because of the package (Supply security shows +0.0 — already pinned at 100). |
| **V5** | Where the money stops helping | Budget-to-score curve: for every yearly budget from 1 to 20 bn, the horizon score the plan reaches — the flattening shows diminishing returns. |
| **—** | The measures this budget pays for | Funded list only: what it works on, start time, cost, delivery confidence, points added. |

Sidebar: **What counts most** (five presets), **Money a year** (1–20 US$ bn),
**Plan up to** (2026–2035), plus the shared unit slicer. No free weight sliders —
one question should not get five answers.

---

## 4. Data

`Q_RENEWABLE_ENERGY`, `Q_ELEC_GEN`, `Q_TD_LOSSES`, `Q_PRIMARY_SUPPLY`,
`Q_NATURAL_GAS`, `Q_LNG`, `Q_ECONOMIC` — merged on `calendar_year`, 1999–2024.
Constant USD; the Cost unit slicer only changes display.

Cautions: 2024 rests on 2 of 4 fresh pillars (Affordability carries 2019, Access
2023); `lng_usd_per_mmbtu` is out by ~1000× but feeds a self-calibrated
component, so scores survive while the raw figure must never be quoted.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/sustainability_engine.py`](../../core/sustainability_engine.py) | pillar scoring, value ranking, knapsack, paths |
| Charts | `charts.py` | the Plotly visuals |
| Page | `page.py` | sidebar, cards, layout, funded list |
| Config | `config.py` | the 13 measures, 5 presets, plain-word names, palette |
| Verify | [`scripts/verify_q8_strategy.py`](../../scripts/verify_q8_strategy.py) | engine audit with sanity checks |

The paths are drifts plus ramps — nothing reacts to prices, weather or a
project slipping. The measure costs, confidences and effects are stated, not
measured; the config library is the place to argue with.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
