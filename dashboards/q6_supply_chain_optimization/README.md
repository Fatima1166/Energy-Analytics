# Q6 — Supply Chain Optimization

**Question:** *What is the optimal utilization of fuel and renewable energy supply chains?*

The page answers it by scoring four things that supply chains actually lose or
waste, year by year: the electricity that never reaches anyone, how much of the
clean plant is used, how little has to be bought from abroad, and how much gas
demand is met at home. One score adds the four up under the strategy you pick.

Nothing here is a forecast. Every number is a reported year judged against a
stated bar.

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "utilization" | Four scored parts, each 0–100 where 100 means the bar is met, plus one overall score |
| "fuel and renewable supply chains" | The grid chain, the clean-plant chain, the bought-from-abroad chain and the gas chain |
| "optimal" | Five strategies that change which part is counted hardest, and a target-mix panel showing what the year would look like if the clean and fuel targets were met |
| "compared to what" | Every part is read against a written bar (15% loss, 75% plant use, 30% imports, 70% gas at home) |

Where the supply comes from is [Q5](../q5_forecast_supply/README.md)'s page and
what imported gas costs is [Q7](../q7_forecast_cost/README.md)'s. The import and
gas numbers stay here as scored parts of the chain, but neither gets a chart of
its own on those pages' territory.

---

## 2. The three KPI cards

| Code | Card | What it says |
|---|---|---|
| **K1** | How well the chains are used | The overall score, which part the chosen strategy counts hardest, and how many of the four parts the score could actually be built from |
| **K2** | Electricity that reached people | The share that arrived, the loss behind it, the aim, and how much of the aim was reached |
| **K3** | Clean plant made vs what it could make | The share of its year-round potential the clean plant actually made, with the energy and plant size behind it |

Each card prints the year its own number came from. The record stops reporting
grid losses, gas and imports in different years, so a card would otherwise carry
a 2024 title over a 2019 number.

**Default view** (strategy *All four parts equally*, window 2002–2024, loss aim
15%, clean target 40% / fuel 60%):

| Card | Reading | Behind it |
|---|---|---|
| K1 | **54.9 / 100** for 2024, from **1 of 4** parts | only the clean-plant part is reported for 2024 |
| K2 | **82.1%** arrived, 2019 | 134,241 GWh made, 24,000 GWh lost = 17.9% against a 15% aim → **Over the aim**, aim reached 97% |
| K3 | **41.2%** for 2024 | 63,260 GWh made from 17,525 MW of plant (potential 153,522 GWh) → aim reached 55% |

Score for the same strategy, year by year: 91.6 (2015) → 84.8 (2018) → 72.4
(2019) → 48.4 (2020) → 54.9 (2024). The fall after 2018 is largely the record
thinning out, not the chains collapsing — see §4.4.

---

## 3. Layout

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **The score, year by year** | The overall score as a thick line and its four parts as thin lines, with the 75 and 50 marks |
| V2 | **Electricity lost on the wires** | Electricity made and electricity lost, with the share that arrived against the aim |
| V3 | **Clean plant built, and what it made** | Plant built (MW), what it made (GWh) and the share of what it could make |
| V4 | **The gas chain** | Gas made at home, gas used, gas bought by ship, and the share met at home against the 70% bar |
| V5 | **What is made now and the target mix** | The year's mix by source, and the same year with the clean and fuel targets met |

The charts go in three rows: **V1 | V4** across the top, then **V2 | V3**, then V5
full width. V1 keeps its legend as a column to the right of the plot instead of a
row under it, because five names do not fit in one row at half width; the strategy
those scores were judged under is on the section badge, so the legend says only
"Overall score". That later years lean on fewer parts — the record thins out after
2018 — is §4.4's subject rather than a caption's.

Things that were cut, and why:

* **The radar scorecard** — it re-drew the same four scores V1 already draws, and
  a five-axis polygon is harder to read than five numbers.
* **The import-dependency chart** — that is Q5's subject; the number still counts
  inside the score.
* **The LNG cost chart** — cost is Q7's subject.
* **A fifth scored part, "fuel waste"** — it was computed from the same
  transmission-loss column as the grid part, so it said the same thing twice and
  pulled the score in one direction twice over. Four parts remain.
* **The "Key Optimization Insights" text panel** — three cards of prose that
  restated the KPI values, and any wording that outlives the numbers it was
  written about is noise.
* **Cards SC3 (import dependency) and SC5 (gas self-sufficiency)** — each was one
  number that V4's line and the score parts already carry.

### 3.2 Sidebar

Two controls, plus the shared Unit Selection.

| Control | Range | Effect |
|---|---|---|
| **Which part counts most** | five strategies | Sets the weights of the four parts, the loss aim and the clean/fuel target |
| **Years to judge** | 1999 – 2024 | Which years are scored; the cards read the last year in the window that has a record |
| **Unit Selection** | Electricity (GWh/TWh/MWh), Power (MW/GW/kW), Gas (BCF/TCF/MMSCF) | Re-renders every axis, hover and card |

What used to be here and is gone: the streams multiselect, the separate target-RE
slider, the separate loss-benchmark slider, the priority-weight picker and the
"Advanced Policy Controls" expander. Those four sliders and pickers let one
question be answered several different ways at once; now each strategy carries
its own targets and weights in one choice.

---

## 4. Method

### 4.1 The four parts

Each part is 0–100 and each is capped at 100, so a part cannot score well by
being far past its bar.

| Part | Formula | Bar |
|---|---|---|
| Electricity that arrives | `arrived% / (100 − loss aim) × 100` | loss aim from the strategy (15% by default) |
| Clean plant used well | `used% / 75 × 100` | 75% of a year-round potential |
| Less bought from abroad | `(30 − import share%) / 30 × 100 + 50` | 30% of supply imported |
| Gas made at home | `met% / 70 × 100` | 70% of gas demand met at home |

`used%` is generation divided by what the same plant could make running every
hour of the year (`capacity_mw × 8,760 / 1,000`). Real sun, wind and water give
25–35%, so 75% is a stretch bar, not a physical one.

### 4.2 The overall score

The weighted average of the parts under the chosen strategy. Weights:

| Strategy | Grid | Clean plant | Imports | Gas |
|---|---|---|---|---|
| All four parts equally | .25 | .25 | .25 | .25 |
| More clean energy | .25 | .40 | .20 | .15 |
| Much more clean energy | .20 | .50 | .20 | .10 |
| Buy less from abroad | .15 | .15 | .40 | .30 |
| Fix grid losses first | .50 | .15 | .20 | .15 |

Bands: 75 and above is **Working well**, 50–75 is **Room to improve**, under 50
is **Needs work**.

### 4.3 The target mix (V5)

Nuclear keeps the share it already has, and the clean/fuel target splits
everything else in proportion. For 2024 the mix is gas 28.5%, hydro 24.8%, coal
15.8%, nuclear 14.8%, solar 12.8%, wind 3.3% over 154,480 GWh. Under the default
40% clean / 60% fuel target the panel draws 34.1% clean, 51.1% fuel and 14.8%
nuclear — 40% and 60% of the non-nuclear part, which is what the target can mean
when one source is held fixed.

### 4.4 A missing report is blank, not zero

The record stops filling columns in different years:

| Column | Last year with a real report |
|---|---|
| `fact_td_losses.td_losses_gwh` | 2019 |
| `fact_primary_energy_supply.imports_toe` | 2018 |
| `fact_natural_gas.production_bcf` / `consumption_bcf` | 2018 |
| `fact_lng_imports.imports_bcf` | 2018 |
| `fact_elec_generation.generation_gwh` | 2023 |
| `fact_renewable_energy` (capacity and generation by source) | 2024 |

So a year with no report scores nothing for that part rather than a perfect 100
(nothing bought) or a hard zero (nothing made). The overall score is then the
weighted average of the parts that were reported, and K1 prints how many that
was — which is why 2024's 54.9 rests on 1 part and 2018's 84.8 rests on 4.

---

## 5. Data

| Table | Used for | Units |
|---|---|---|
| `fact_elec_generation` | Electricity made (GWh) | GWh |
| `fact_td_losses` | Electricity lost on the wires (GWh) | GWh |
| `fact_renewable_energy` | Clean plant (MW), generation by source (GWh) | MW / GWh |
| `fact_primary_energy_supply` + `dim_energy_source` | Supply at home and bought abroad (TOE) | TOE |
| `fact_natural_gas` | Gas made and used (BCF) | BCF |
| `fact_lng_imports` | Gas bought by ship (BCF) | BCF |

Base units GWh · MW · BCF · TOE, converted for display by
[`core/units.py`](../../core/units.py). `gen_other_renewables_gwh` is empty in
every row, so "clean" here is hydro + solar + wind.

---

## 6. Known limitations

* **Two of the four parts sit at their ceiling in this record.** Imports run
  0–9.7% of supply and gas met 99–122% of demand, so both parts score 100 in
  every year they can be computed. The score's shape is carried by clean-plant
  use (39–72) and grid losses (86.5–100). V1 shows this plainly rather than hiding
  the flat lines.
* **The score thins out, it does not collapse.** After 2019 only the clean-plant
  part is reported, so the overall score drops to that part alone. K1's "Scored
  from 1 of 4 parts" is there to stop that drop being read as a real decline.
* **Plant potential is a capacity-times-hours ceiling**, not a site-by-site wind
  and sun resource. It is the same standard for every year, so years compare, but
  the level is generous.
* **The target mix is a reshuffle of one reported year**, not a build plan. It
  moves shares, and says nothing about cost, timing or grid stability.
* **Loss figures are the reported transmission and distribution total**; the
  warehouse holds no split between the two, so the page cannot say where the
  electricity goes missing.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, the four-part score, KPI cards, layout |
| `charts.py` | The five Plotly figures |
| `config.py` | The bars, the strategies and their weights, the palette |
| `README.md` | This document |

Related: [`core/queries.py`](../../core/queries.py) (SQL),
[`scripts/audit_axes.py`](../../scripts/audit_axes.py) (prints every Q6 axis
title), [`scripts/smoke_test_app.py`](../../scripts/smoke_test_app.py) (headless
render check of all dashboards).
