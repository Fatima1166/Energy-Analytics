# Q3 — Target Bottlenecks

**Question:** *What are the bottlenecks in achieving planned targets?*

A benchmark-tracking dashboard. It measures four national energy indicators
against their targets, ranks how badly each is missed, and projects them all to
2035 so it is clear which gap closes and which one widens.

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "bottlenecks" | Four KPIs scored against benchmarks and ranked worst-first |
| "achieving planned targets" | Gap to benchmark in percentage points, plus % of benchmark delivered |
| "planned" horizon | Every series runs 2002 → 2035, with reported vs modelled years marked |

---

## 2. The four KPIs

All four are judged on a **single reference year** — the final year of the
sidebar Year Range — so they stay comparable. Each card carries the benchmark,
the direction-aware gap, the year-over-year move, and how much of the benchmark
is delivered.

| Code | KPI | Working | Benchmark | Better when |
|---|---|---|---|---|
| **K1** | Energy Losses % of Supply | `total_losses_toe / total_primary_supply_toe × 100` | 28.23% | lower |
| **K2** | Import Dependence % | `(LNG Imports + Imported Electricity) / total primary supply × 100` | 0.00% | lower |
| **K3** | Renewable Share % | `(solar+wind+hydro+other) / total generation × 100` | 30.00% | higher |
| **K4** | Gas Self-Sufficiency % | `production_bcf / consumption_bcf × 100` | 122.37% | higher |

**Benchmarks** come from the `dim_target` table, with the official ARE Policy
2019 renewable target (30%) layered on top by [`core/targets.py`](../../core/targets.py).
Three of the four are *data-derived floors* — the best level Pakistan has
actually recorded — so a missed benchmark means "worse than our own best year",
not a policy failure.

**Direction-aware gaps.** `gap = target − actual` for lower-is-better metrics and
`gap = actual − target` for higher-is-better ones, so **positive always means the
benchmark is met**. This matters: under the old fixed logic, imports at 20%
against a 30% target were flagged as a 10pp failure when they were actually
comfortably inside the target.

**Default view (range 2002–2035, judged on 2035):**

| KPI | Value | Gap | % of benchmark | Verdict |
|---|---|---|---|---|
| K1 Losses | 27.16% | +1.1pp | 104% | On track |
| K2 Import Dependence | 38.26% | −38.3pp | 0% | Severe |
| K3 Renewable Share | 50.05% | +20.0pp | 167% | Exceeding |
| K4 Gas Self-Sufficiency | 47.80% | −74.6pp | 39% | #1 bottleneck |

(Gaps are shown to one decimal place, as on the cards.)

**Ranking** combines the percentage-point shortfall with the shortfall relative
to the benchmark (`missed × 0.6 + relative shortfall × 100 × 0.4`), so a small
target missed badly is not hidden by a large target missed slightly.

---

## 3. Layout

### 3.1 Visuals

| # | Chart | Working |
|---|---|---|
| V1 | **Energy loss waterfall** | Primary supply → transformation losses → T&D losses → other → final consumption, for the range's final year; balances exactly |
| V2 | **Losses vs benchmark** | Actual path against the benchmark line, gap shaded, star on the first year the target is met |
| V3 | **Import dependence** | Import share over time with imported volume as context bars |
| V4 | **Gas production vs consumption** | Bars for production and consumption, deficit shaded, self-sufficiency on a second axis |
| V5 | **Benchmark gaps** | All four gaps on one axis; above zero = benchmark met |
| V6 | **Achievement vs benchmark** | % of each benchmark delivered, bars coloured by severity |

### 3.2 Sidebar

Deliberately minimal — one control.

| Control | Range | Effect |
|---|---|---|
| **Year Range** | 2002 – 2035 | Zooms every chart, sets the year the KPI cards and the waterfall are judged on |
| **Unit Selection** | Energy (TOE/KTOE/MTOE), Gas (BCF/TCF/MMSCF) | Re-renders the waterfall, import bars and gas chart |

### 3.3 Footer

A three-line footnote describing the live view: the range and benchmark year, the
method and which KPI is currently most urgent, the sources, and an amber note
naming exactly which series are modelled rather than measured.

---

## 4. Data

| Table | Used for |
|---|---|
| `fact_energy_overview` | Primary supply, final consumption, transformation & T&D losses (TOE) — reported 2005–2019 |
| `fact_primary_energy_supply` | Supply and imports by source (TOE) — reported 2002–2024 |
| `fact_renewable_energy` | Generation mix by source (GWh) — reported 1999–2024 |
| `fact_natural_gas` | Production and consumption (BCF) — reported 1999–2018 |
| `dim_energy_source` | Source names, used to identify the import rows |
| `dim_target` | Benchmarks, direction and source of each |
| `dim_year` | Fiscal year ↔ calendar year |

**Joins:** `fact_renewable_energy.calendar_year → dim_year.calendar_year`; the
other fact tables on `dim_year.year_id`.

**Base units:** TOE · GWh · BCF · MW. Percentages are unit-free.

---

## 5. Method & assumptions

### Data provenance

Every annual value is tagged, and the tags drive the line styles:

| Tag | Meaning | Drawn as |
|---|---|---|
| **Actual** | Reported in the database | solid |
| **Estimated** | Bridged where the source table has a gap | dotted |
| **Projected** | Modelled beyond the last reported year | dashed |

Reported coverage differs per metric — losses stop at 2019, gas at 2018,
generation at 2024 — so each series is extended from its own last reported year.

### Projection rules

- **Primary supply** — geometric trend of the last five reported years (clamped
  to −5% … +8%).
- **Energy losses %** — five-year average level with the observed slope damped by
  half and frozen after six years, because the loss ratio has been broadly flat
  since 2016.
- **Import dependence** — the 2014–2018 import-share slope (the years that
  actually report import rows) extended at 65% strength, capped at 60%.
- **Renewable share** — damped least-squares slope of recent years; generation
  grows at its five-year CAGR.
- **Gas** — production declines and consumption grows at their recent rates,
  with floors of −2%/yr and +2%/yr, which is what widens the self-sufficiency gap.
- **Waterfall split** — the last reported breakdown of losses into
  transformation, T&D and other is held constant, and final consumption closes
  the balance.

### Validation built into the code

- The waterfall is checked to balance in every year (supply = losses +
  consumption, exactly).
- The KPI reference year is clamped into the data range, so no card can silently
  read zero.
- Import matching uses the exact source names `LNG Imports` and
  `Imported Electricity` and prefers the `imports_toe` column over `supply_toe`.

---

## 6. Known limitations

- **Import data stops at 2018.** `fact_primary_energy_supply` has no import rows
  for 2019 onwards, so K2 and its chart are trend-bridged from 2018. These are
  estimates and are labelled as such; load real import rows and the KPI will pick
  them up automatically.
- **K2's benchmark is 0%** (the historical minimum), which makes it arithmetically
  impossible to satisfy. It is the data-derived floor, not a policy goal.
- **Losses beyond 2019** are modelled because `fact_energy_overview` ends there,
  even though supply is still reported for 2020–2024.
- The 2035 numbers are trend extrapolations, not forecasts — they show what
  happens if nothing changes.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, KPI cards, layout, footer |
| `charts.py` | The six Plotly figures |
| `config.py` | View constants only — benchmarks deliberately live in the database |
| `README.md` | This document |

Related: [`core/bottleneck_metrics.py`](../../core/bottleneck_metrics.py) (projection
and gap engine), [`core/targets.py`](../../core/targets.py) (benchmarks),
[`core/components.py`](../../core/components.py) (cards, footer).
