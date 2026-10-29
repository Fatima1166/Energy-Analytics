# Q8 — Sustainable Energy Strategy

**Question:** *What optimal strategy may be opted to make energy development
sustainable?*

The page scores where Pakistan's energy system stands on four pillars, works out
which measures buy the most progress for a year's money, and shows where that
package leads by the year asked for.

```
the plan = the measures, best value first, until the yearly money runs out
```

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "optimal" | Every option is scored on what it adds per $bn a year, discounted by how sure the delivery is, then paid for best-value-first until the budget is gone |
| "strategy" | Thirteen named measures, each with a yearly cost, a delivery confidence, a lead time and a pillar-by-pillar effect |
| "make energy development sustainable" | Four pillars — Supply security, Affordability, Clean power, Access — scored 0-100 out of the reported record |
| "compared to what" | Against the same score if nothing changes, and against the last reported year |

What the pillars are made of is measured on Q3's and Q6's data; what the money
side of a cleaner mix costs is [Q7](../q7_forecast_cost/README.md)'s page. This
page only answers the strategy question.

---

## 2. The three KPI cards

| Code | Card | What it says |
|---|---|---|
| **K1** | Where things stand | The weighted score for the last reported year, the lowest and highest pillar behind it, and how many of the four pillars that year actually reported |
| **K2** | What the plan reaches | The score at the horizon under the recommended package, the same score if nothing changes, the gap between them, and how many measures get paid for |
| **K3** | What the plan costs a year | The money the funded measures take, what was asked for, what was left over, and how many measures were put off |

**Default view** (Balanced priorities, 8 USD bn a year, outlook to 2035):

| Card | Reading | Behind it |
|---|---|---|
| K1 | **71.9** for 2018 | The latest year all four pillars reported; each pillar row carries its own year (security 83 · economy 92 · environment 65 · access 46) |
| K2 | **94.1** for 2035 | 82.0 if nothing changes, so the plan is worth +12.1 points; 8 of 13 measures funded |
| K3 | **7.90** USD bn a year | 0.10 left over, 5 measures put off |

The composite waits for all four pillars, so 2019–2024 — years that cannot
form one from complete components — print nothing on the paths, and the card
sits on 2018, the latest year that really scored. Its label moves with the
number; the number never moves to the label.

The eight measures the money pays for, in the order it is spent (USD bn a year):
Charge the real cost 0.2, Use power more efficiently 0.6, Solar on rooftops 0.9,
Cut grid losses 1.2, Reach villages off the grid 1.1, Buy gas on longer deals 1.8,
Trade power with neighbours 1.4, Close or convert coal plants 0.7.

What is put off is every large build: Big solar and wind farms, More hydropower,
Store power for later, Pump more of our own gas, Add nuclear power. At 8 bn a year
the cheap reforms are simply denser than the plant that would replace them — and
because the envelope is filled in order, the seventh-best option (Big solar and
wind farms) is refused while the eighth and ninth are bought.

Pillar gain of the package by 2035, against doing nothing: Access **+35.7**,
Affordability **+22.9**, Clean power **+18.1**, Supply security **+0.0** — its
score is already pinned at 100, so it has no room to show a gain.

Moving the two sidebar controls:

| Setting | K1 | K2 | Funded |
|---|---|---|---|
| Balanced (30/25/25/20) | 70.7 | 94.1 | 8 of 13 |
| Clean power counts most | 68.4 | 95.5 | 7 of 13 |
| Supply security counts most | 76.9 | 95.6 | 8 of 13 |
| Affordability counts most | 66.3 | 94.1 | 8 of 13 |
| Access counts most | 62.6 | 86.8 | 8 of 13 |
| Budget 1.0 / 3.5 / 8.0 / 20.0 bn | 70.7 | 82.8 / 90.8 / 94.1 / 95.8 | 2 / 4 / 8 / 12 |
| Horizon 2026 / 2030 / 2035 | 70.7 | 72.3 / 94.3 / 94.1 | 8 of 13 |

Those readings came off the live record through the engine, and
`scripts/verify_q8_strategy.py` re-checks the rules behind them.

---

## 3. Layout

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **Where each pillar stands** | Each pillar's latest score against ten years earlier, with the year it came from and how many measures back it |
| V2 | **What each option buys per dollar** | All thirteen options ranked by score points added per $bn a year; green is paid for, grey is put off |
| V3 | **The measures behind each pillar** | One heat-map: every measure's score (out of 100) in its pillar's latest reported year — the low cells show what holds the pillar down |
| V4 | **What the plan changes** | Points each pillar gains by the horizon because of the package |
| V5 | **Where the money stops helping** | Budget-to-score curve: for every yearly budget from 1 to 20 bn, the composite score the plan reaches at the horizon; the shape shows the diminishing returns |
| — | **The measures this budget pays for** | The funded list only: what it works on, when it starts, what it costs, how sure the delivery is, what it adds |

Each visual carries one short caption line (under ~120 characters) that only says
where to look. Method and disclosures live here in the README.

The four charts sit in two rows of two — V1 | V2, then V3 | V4 — and the funded
list spans the page below them. V3 is a heat-map with no legend: the pillar
groups of columns are separated by thin gaps and each row carries its own
pillar score, so the cells read on their own at half width.

Things that were cut, and why:

* **Three of the seven visuals** — the index trajectory (its line is V3's history
  bars), the cost-impact bubble map (the same two numbers as V2's bars, and its
  "filled vs hollow" said nothing V2's colours do not), and the component
  diagnostics (nine sub-scores that only restate the four pillar bars plus the
  measure counts now printed on V1's axis).
* **The fourth KPI card, "Avoided BAU Drift"** — its number is the gap between two
  lines on V3 and sits on K2 as "+17.4 points"; the card also carried two index
  values that repeat K1 and K2.
* **Four pillar-weight sliders** — they let a reader move 30/25/25/20 to any four
  numbers, which is a modelling choice rather than a question. One pick, "What
  counts most", sets them; the five presets and the four numbers behind each are
  listed in §3.2.
* **The evaluation-year slider** — the record stops in 2024, and every earlier
  year scores fewer pillars, so the choice only moved the baseline onto thinner
  evidence. The year is fixed and the page says what it rests on.
* **The thirteen-row budget ledger** — the deferred rows are already in V2 in grey,
  with the same cost, delivery and effect figures.
* **The "Objective 1 … Objective 3" badges** — a numbering scheme that appears
  nowhere else; the year span and the count say more in fewer words.
* **`ELEMENTS` and `COMPONENT_LABELS` in config** — they existed to feed the
  diagnostics chart.

### 3.2 Sidebar

Three controls, nothing else — no caption text under them. The shared Unit
Selection sits below.

| Control | Range | Effect |
|---|---|---|
| **What counts most** | Five presets | The pillar weights behind the score, the ranking and every projection |
| **Money a year for new measures** | 1.0 – 20.0 USD bn | How far down the value ranking the plan gets, so which measures are funded and what the score reaches |
| **Plan up to** | 2026 – 2035 | The year K2, K3, V2, V3 and V4 are read at |
| **Unit Selection** | Cost (USD bn / USD mn / USD) | K3, V2's hover cost and the cost column of the funded list |

What each preset sets, as weights on Supply security / Affordability / Clean
power / Access (`PRIORITY_PRESETS` in `config.py`):

| Preset | Weights |
|---|---|
| Balanced (planner's default) | 30 / 25 / 25 / 20 |
| Clean power counts most | 20 / 20 / 45 / 15 |
| Supply security counts most | 45 / 25 / 15 / 15 |
| Affordability counts most | 20 / 45 / 15 / 20 |
| Access counts most | 20 / 20 / 15 / 45 |

Two disclosures the sidebar no longer spells out, because the page carries them
elsewhere: the index is **out of 100, not a percentage** — K1 and K2 print their
value as `/ 100` and three of the four axis titles say so — and the base year is
**built from the pillars that reported**, which K1 states as "Reported in 2024: 2
of 4 pillars" while V1 prints each pillar's own year.

---

## 4. Method

### 4.1 The four pillars

Each pillar is the mean of its measured components, scored 0-100. Where a
benchmark is agreed it is used directly; otherwise the component is calibrated on
Pakistan's own 10th-90th percentile (`_auto_calibrate`), which means the best year
in the record always scores 100.

| Pillar | Components | Years each was reported |
|---|---|---|
| Supply security | import dependence, gas self-sufficiency, generation diversity | 2002–2018, 1999–2018, 1999–2024 |
| Affordability | grid (T&D) efficiency, LNG unit price | 2002–2019, 2014–2018 |
| Clean power | renewable share of electricity | 2000–2024 |
| Access | electricity per person, demand coverage | 2002–2023, 2002–2023 |

So each pillar's own span is narrower than its label suggests: Supply security
26 years, Affordability 18 (2002–2019), Clean power 25 (2000–2024), Access 22
(2002–2023).

CO₂ intensity is deliberately **not** a component. The warehouse holds national CO₂
(every fuel, every sector) against electricity generation only, so the ratio lands
between 1,200 and 2,200 kg/MWh against a power-sector benchmark of 350 — every year
scored nought on a scope error and pulled Clean power down by a third.

The weighted score needs all four pillars. Each pillar carries its own last
reported value forward, so 2024 is scored from Supply security 2024, Affordability
2019, Clean power 2024 and Access 2023 — and V1 prints those years, because they
are not all the same year. Scoring starts in 2002, the first year all four have
appeared.

### 4.2 What an option is worth

```
weighted impact = Σ pillar weight × the points that measure adds to that pillar
value density    = weighted impact / cost a year × delivery confidence
```

`select_optimal_package()` walks that ranking top-down and buys any measure that
still fits the yearly envelope (a greedy knapsack). Effects are discounted by the
same delivery confidence when they are applied to the pillars.

### 4.3 The three paths

Each pillar drifts on its own last eight reported years, with the slope clamped to
−1.0 … +1.5 points a year so a short run cannot tilt the outlook.

* **If nothing changes** — the drift alone.
* **Only what is already promised** — the funded measures that are at least 60%
  deliverable, at half effect.
* **The recommended package** — every funded measure at full effect, ramped in over
  three years after each measure's lead time.

All three share the same reported history, so the gap between the lines is the
plan and nothing else.

---

## 5. Data

| Query | Used for |
|---|---|
| `Q_RENEWABLE_ENERGY` | Electricity by source, renewable share |
| `Q_ELEC_GEN` | Generation total, diversity of the mix |
| `Q_TD_LOSSES` | Grid efficiency |
| `Q_PRIMARY_SUPPLY` | Domestic supply and imports (import dependence) |
| `Q_NATURAL_GAS` | Gas self-sufficiency |
| `Q_LNG` | LNG unit price |
| `Q_ECONOMIC` | CO₂, population, GDP (per-head and coverage figures) |

Merged on `calendar_year`, 1999–2024. Money is constant USD; the Cost unit slicer
only changes how it is displayed.

---

## 6. Known limitations

* **The score is not a percentage.** It mixes absolute benchmarks with self-calibrated
  percentiles, so 70.7 means "well into the range Pakistan has itself recorded",
  not "71% sustainable". Out of 100, and worth comparing only to itself.
* **2024 rests on two of the four pillars.** Affordability carries 2019 forward and
  Access carries 2023; the record reports no T&D loss figure for the last five
  years, no LNG price since 2018, and nothing at all for import dependence after
  2018. K1 states the count rather than hiding it.
* **Supply security scores 100 on one measure.** With imports and gas unreported,
  only generation diversity is left, and it is self-calibrated — so the best year
  wins outright. That is why V4 shows a gain of +0.0 there, and the hover says the
  pillar is already at the top of its scale.
* **Clean power is one measure too** — the renewable share of electricity, with no
  carbon figure in it (§4.1). A mix that shifts from gas to imported coal moves the
  pillar not at all.
* **The cost, delivery confidence and pillar effects of each measure are stated,
  not measured.** Thirteen sets of three numbers drive the whole ranking; the
  library is the place to argue with, and the order changes if they change.
* **The paths are drifts plus ramps**, not a model of the system. Nothing in them
  reacts to prices, weather, debt or a project slipping.
* **A longer horizon can read lower.** The package peaks at 94.3 in 2030 and settles
  to 94.1 by 2035, because the pillars stop at 100 while the doing-nothing line
  keeps rising. Past about 2030 the scale, not the plan, is what runs out — so the
  control tops out at 2035.
* **One warehouse figure is wrong but harmless.** `lng_usd_per_mmbtu` is out by a
  factor of about 1,000, and covers only 2014–2018. It feeds a self-calibrated
  component, so the order of years survives and the score does not move — but the
  figure must never be quoted as a price.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, the three cards, layout, the funded list |
| `charts.py` | The four Plotly figures |
| `config.py` | The thirteen measures, the five presets, pillar and path names in plain words, the palette |
| `README.md` | This document |

The maths lives in [`core/sustainability_engine.py`](../../core/sustainability_engine.py).

Check it:

```
.venv\Scripts\python.exe scripts\verify_q8_strategy.py   # engine against MySQL, with sanity checks
.venv\Scripts\python.exe scripts\audit_axes.py           # prints every Q8 axis title
.venv\Scripts\python.exe scripts\smoke_test_app.py       # headless render of all dashboards
```
