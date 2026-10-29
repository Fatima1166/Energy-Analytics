# Q10 — Optimal Resource Allocation for Sustainable Development

**Question:** *What is optimal resource allocation for sustainable development?*

The page works out how the horizon year's power need can be split across the
seven resources that Pakistan can actually use, what that split costs, what it
emits, and how much fuel it has to buy from abroad — all measured against the
2024 mix doing the same job.

```
the plan = the power that has to be supplied, given to the best-scoring
           resources first, up to what each one can physically produce
```

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "optimal" | Each resource is scored on three things at once — buying cost, CO₂, and how much of its fuel comes from abroad — and the need is handed to the highest scorers first |
| "resource allocation" | The split is shown resource by resource, in a chart and in a table, with the change against the 2024 mix |
| "for sustainable development" | The plan is scored on six plain things against the 2024 mix: cheaper power, lower CO₂, fuel from home, source spread, clean share, demand served |
| "compared to what" | Against the 2024 mix kept going on the same power need, and against the cleanest and cheapest plans that could be drawn up |

The real limit on the answer is that each resource can only produce so much.
Hydro, solar, wind, nuclear and other renewables are already pinned at those
limits in the default view, which is the finding, not a modelling error.

---

## 2. The three KPI cards

| Code | Card | What it says |
|---|---|---|
| **K1** | Power that has to be supplied | The horizon-year need, what was actually made in 2024, the growth rate used, and how much is left unserved |
| **K2** | What the plan costs a year | The plan's yearly buying cost, the same figure for the 2024 mix, the change, and CO₂ for both |
| **K3** | How clean, and how sure of fuel | Clean share of the plan, the same share on the 2024 mix, fuel bought from abroad, and how many resources are sitting on their limit |

A fourth column slot is left open so each card keeps a four-up width; the cards
are sized by their own content rather than by a fixed height.

**Default view** (What the plan should favour = Balanced, growth 4.5% a year,
plan up to 2035):

| Card | Reading | Behind it |
|---|---|---|
| K1 | **284,713** GWh a year | 175,440 GWh made in 2024, so the plan must cover 1.6× that; 0 GWh left unserved |
| K2 | **13.64** USD bn | The same energy on the 2024 mix would cost 19.24 bn, so −29.1%; CO₂ 24.2 Mt against 76.6 Mt |
| K3 | **68.2** % clean | 41.0% on the 2024 mix; fuel bought abroad 13.6% (was 34.7%); 5 of 7 resources at their limit |

Moving the sidebar controls (all six rows are from the live record):

| Setting | Need (GWh) | Cost (USD bn) | CO₂ (Mt) | Clean % | Unserved | At limit |
|---|---|---|---|---|---|---|
| Balanced (35 / 40 / 25) | 284,713 | 13.64 | 24.2 | 68.2 | 0 | 5 of 7 |
| Cheapest power (70 / 15 / 15) | 284,713 | 12.60 | 39.9 | 68.2 | 0 | 5 of 7 |
| Lowest CO₂ (15 / 60 / 25) | 284,713 | 13.71 | 23.1 | 68.2 | 0 | 5 of 7 |
| Least fuel bought abroad (20 / 20 / 60) | 284,713 | 13.70 | 23.2 | 68.2 | 0 | 5 of 7 |
| Growth 2.0% a year | 218,138 | 8.38 | 8.1 | 81.1 | 0 | 3 of 7 |
| Growth 8.0% a year | 409,063 | 26.95 | 77.5 | 47.4 | 0 | 5 of 7 |
| Plan up to 2026 | 191,585 | 7.73 | 7.1 | 82.3 | 0 | 3 of 7 |

The point those rows make: **the four picks all land on the same 68.2% clean
share.** What the plan is told to favour changes what it costs and emits, not
how much of it is clean, because the clean resources are already pressed
against their ceilings. A small demand (2026, or 2% growth) is the only case
where the plan reaches 81–82% clean without hitting those limits. At 8% growth
the clean share falls to 47.4%, below the 60% mark K3 carries, because the
limits force coal and gas back in.

---

## 3. Layout

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **How the power is split** | Each resource with the 2024 mix behind the plan, and the most it could ever make in the hover |
| V2 | **What the priorities buy** | The same plan run from cheapest-first to cleanest-first, with cost and CO₂ on two lines and a dotted mark at the reader's pick |
| V3 | **What moves, source by source** | Plan minus the 2024 mix for each resource; green grows a source, red pulls one back |
| V4 | **Is the plan more sustainable?** | The six plain things, scored 0–100 for the 2024 mix and for the plan |
| V5 | **The cost-CO₂ trade-off shape** | Every plan the sweep can build, one dot per priority, plotted cost against CO₂; the knee shows where going cleaner stops costing much more |
| — | **The plan, resource by resource** | Table: plan, 2024 mix, change, most possible, cost, CO₂, and whether the resource is at its limit |

Each visual has one short caption line (84–93 characters) that only says where
to look. The method and the warnings are in this file, not on the page.

The four charts sit in two rows of two — V1 | V2, then V3 | V4 — and V5 spans
most of the row below them (its dots need the width to separate the priorities)
with a small empty slot at the right; the plan table then spans the page.
V3 and V4 are horizontal bars, so their left margin is set from the longest
label (104 px for 16-character resource names, 96 px for the six axis names) to
keep the labels inside the half-width column. V1's long resource names are
broken onto two lines instead of being rotated.

Things that were cut, and why:

* **The source→sector chart** — the allocation model uses one national mix, so
  the same resource shares were being reprinted in every sector. All eight
  sectors gave Coal 0.8 / Gas 13.4 / Hydro 17.5 / Nuclear 17.7 / Solar & Wind
  50.7, a spread of 0.0 points. A chart that cannot show a choice was not
  answering an allocation question, and the sector column of the engine went
  with it.
* **The coverage gauge and the gas self-sufficiency gauge** — demand served is
  100.0% and unserved is 0 GWh in every setting tested (2026–2035, growth 2–8%,
  all four picks). Both numbers now sit as rows on K1 and V4 instead of two
  dials that never move.
* **The concentration Pareto chart and the rose chart** — the rose repeats V1's
  values as wedge angles, and the concentration chart is V1's bars sorted
  differently. V2 keeps the priority sweep, which is the one thing on the page
  that shows a trade-off rather than a result.
* **Two KPI cards** — the unserved-power card and the gas card became rows on
  K1 and K3, for the reason above: their headline never changed.
* **Four weight sliders** — a reader moving three weights to any values is a
  modelling decision, not a question. One pick, "What the plan should favour",
  with four named settings, is the same control with the shape of the answer
  kept honest (Q8 uses the same form).
* **The solver knobs** — "Reallocation pressure" and "Fuel price drift" were in
  the sidebar and one of them sat inside an "Advanced Model Settings" expander.
  Both are fixed at their documented engine values (pressure 3.0, fuel drift
  3.0% a year, mirroring Q7's anchor) and are explained in §4.

### 3.2 Sidebar

Three controls, no caption text under them, no expander:

```
Resource Allocation
  What the plan should favour   [ Balanced (planner's default) ▾ ]
  How fast demand grows (% a year) [ ────●──── ] 4.5
  Plan up to                    [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Electricity  [ GWh ▾ ]
  Cost         [ USD bn ▾ ]
  Emission     [ t ▾ ]
```

`Plan up to` stops at 2035 on purpose — the question is asked for the 2035
need, and reading past it would only extend an exponential growth assumption
further than the record supports.

---

## 4. Method (base units: GWh, US$, t, BCF, MW)

**Demand.** `need = reported generation of the base year × (1 + growth)^years`,
with the base year 2024 (175,440 GWh) and growth from the sidebar. The base year
is the last year the record reported in full; an unreported year would print no
reading rather than a carried-over or zero-filled value — the engine tags each
history year `Actual` or `Missing` and the cards name the year their number
came from.

**Profiles.** Per resource: buying cost in US$/MWh from the Q7 anchors
(`core/cost_forecast.unit_cost`), cradle-to-grave CO₂ in t/MWh (IPCC AR5
medians, replaced by `dim_emission_factor` when it has a matching name), how
much of the fuel chain is bought abroad, and the capacity factor.

**Score.** Each resource's cost, CO₂ and import dependence are stretched to
0–1 across the seven resources (min-max), then

```
utility = w_cost·(1 − costₙ) + w_carbon·(1 − CO₂ₙ) + w_security·(1 − importₙ)
```

with the weights from the pick, normalised to sum to 1.

**Split.** `share ∝ utility^3.0`. Pressure above 1 concentrates the need on the
best scorers; 3.0 is the value the whole page is calibrated at. A water-filling
loop then clamps any resource over its ceiling and re-spreads what is left over
the resources still free. Whatever still cannot be served is reported as
"Left unserved" rather than hidden.

**Ceilings.** Each resource may stretch to a documented multiple of its best
reported year: Solar 6.00×, Wind 4.00×, Coal 1.80× (Thar ramp plus import
logistics), Nuclear 2.20×, Other renewables 2.50×, Hydro 1.30× (Indus flow plus
the pipeline already committed). Gas is the one hard physical cap —
`max(domestic production BCF × 150 GWh/BCF, best reported year × 1.25)`. The
page deliberately shows no capacity column: every number on it is an amount of
power, a cost or a tonne, so no `Power` dropdown is offered either.

**The 2024 mix comparison.** The same need is allocated in the proportions the
record actually shows for 2024, so every figure on the page has a "same energy,
old mix" partner.

**The priorities sweep.** The cost weight and the carbon weight are traded from
all-cost to all-carbon in 21 steps; V2 draws the two resulting lines.

**The six scores.** `Cheaper power` = 1 − (US$/MWh ÷ 80); `Lower CO₂` =
1 − (t/MWh ÷ 0.90); `Fuel from home` = 100 − import share; `Source spread` =
(1 − HHI) × 100; `Clean share` = clean % ÷ 60% benchmark; `Demand served` =
coverage %. Fixed references keep the 2024 mix and the plan on one scale.

---

## 5. Data

| Query | Table | Used for |
|---|---|---|
| `Q_RENEWABLE_ENERGY` | `fact_renewable_energy` | 2024 generation by resource, build-out ceilings |
| `Q_NATURAL_GAS` | `fact_natural_gas` | Domestic gas production → the gas ceiling |
| `Q_EMISSION_FACTORS` | `dim_emission_factor` | CO₂ intensity overrides |

Cost anchors are shared with [Q7](../q7_forecast_cost/README.md). The four
pillars a strategy is worth are [Q8](../q8_sustainable_strategy/README.md)'s
page; this page only answers how to split the power need.

---

## 6. What the live record cannot support

* **Clean share is set by the ceilings, not by the pick.** All four priority
  settings land on 68.2%, and V4's `Clean share` axis reaches 100 for each of
  them because 68.2% is already over the 60% benchmark. The page must not be
  read as "choose Lowest CO₂ and the mix turns cleaner".
* **Source spread goes down.** 79.3 → 73.8 in the default view (and as low as
  68.1 when the need is small). Concentrating the need on the best-scoring
  resources is what makes the plan cheaper and cleaner, and it also makes the
  mix less spread out. V4 prints both numbers rather than only the wins.
* **5 of 7 resources are pinned at their limit** in the default view, so the
  plan's shape is mostly a statement about the ceilings. `Other renewables`
  tops out at 2 GWh and is worth a row in the table, not a colour in a chart.
* **The unserved-power warning never fires on this record.** `page.py` still
  prints it if a future setting makes the ceilings bind, but it is not a live
  reading.
* **The engine is not a solver.** Utility-weighted water-filling is a
  transparent approximation of least-cost-plus-constraint dispatch. It ignores
  dispatch order, storage, grid geography and ramping, so the split is a
  planning shape, not a schedule.
* **CO₂ shows in tonnes** because the Emission domain defaults to `t`, the same
  as the rest of the deck. The plan's 24.2 Mt therefore reads as 24,209,729 t on
  K2 and as long tonnage figures in the table; a reader who prefers megatonnes
  picks `Mt` and every CO₂ figure on the page follows. The sweep line on V2 uses
  short ticks ("24M") so the tonnage still fits a half-width chart.

---

## 7. Files

| Layer | File | Role |
|---|---|---|
| Engine | `core/resource_allocation.py` | Profiles, utility, water-filling, priorities sweep, six-way score |
| Config | `dashboards/q10_resource_allocation/config.py` | The four picks, slider ranges, plain words, palette |
| Charts | `dashboards/q10_resource_allocation/charts.py` | Four figures, values pre-computed by the engine |
| Page | `dashboards/q10_resource_allocation/page.py` | Three controls, three cards, two chart rows, the table |
| Verify | `scripts/verify_q10_allocation.py` | Engine against MySQL, with sanity checks |

Registered as key `q10` with unit domains `electricity, cost, emission`. Only
physical amounts follow those dropdowns — axis titles, table headers, card
values and hover text. The percentages, the 0–100 scores and the ratio of the
need to the 2024 need are ratios of two figures in the same unit and stay put.
`gas` was dropped from the declaration when the gas card went: nothing on the
page prints BCF any more, so a Gas dropdown would have been a control with
nothing to control.

Check it:

```
.venv\Scripts\python.exe scripts\verify_q10_allocation.py
.venv\Scripts\python.exe scripts\smoke_test_app.py
```
