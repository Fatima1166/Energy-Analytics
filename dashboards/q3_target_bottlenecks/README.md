# Q3 — Target Bottlenecks

**Question:** *What are the bottlenecks in achieving planned targets?*

This dashboard measures four national energy indicators against their targets,
scores how badly each one is missed, and runs every series to 2035 so you can
see which gap closes and which one widens.

---

## 1. Algorithms & formulas

| Technique | Formula / rule |
|---|---|
| **Direction-aware gap** | `gap = target − actual` for lower-is-better metrics, `gap = actual − target` for higher-is-better ones. **Positive gap always means the benchmark is met** — one rule works for all four cards, so a missed target can never show a green badge. |
| **Achievement %** | lower-is-better: `target / actual × 100` · higher-is-better: `actual / target × 100`, clamped to 0–200% so one wild year cannot flatten the scale. |
| **Severity bands** | gap ≥ +10 → "Exceeding" · ≥ 0 → "On track" · ≥ −5 → "Slightly behind" · ≥ −15 → "Off track" · ≥ −30 → "Critical" · below that → "Severe bottleneck". |
| **Bottleneck ranking** | `score = missed_pp × 0.6 + (relative shortfall × 100) × 0.4`. Combining the raw percentage-point miss with the miss *relative to the target size* means a small target missed badly is not hidden by a big target missed slightly. The two worst get a `#1 / #2 bottleneck` chip. |
| **Trend projection** | Past the last reported year each metric follows its own rule (see §4). Reported years are solid line, projected years dashed, unreported years print nothing. |

---

## 2. KPI cards

All four are judged on **one reference year** — the last year of the sidebar
range — so they stay comparable. Each card shows the benchmark, the gap in
percentage points, the year-over-year move, and its severity band.

| Card | Formula | Benchmark | Better when |
|---|---|---|---|
| **K1 — Energy Losses % of Supply** | `total_losses_toe / total_primary_supply_toe × 100` | 28.23% | lower |
| **K2 — Import Dependence %** | `(LNG Imports + Imported Electricity) / total primary supply × 100` | 0.00% | lower |
| **K3 — Renewable Share %** | `(solar + wind + hydro + other) / total generation × 100` | 30.00% (ARE Policy 2019) | higher |
| **K4 — Gas Self-Sufficiency %** | `production_bcf / consumption_bcf × 100` | 122.37% | higher |

Benchmarks come from the `dim_target` table. Three of the four are *historical
bests* — the best level Pakistan actually recorded — so missing them means
"worse than our own best year", not a policy failure. The 30% renewable target
is the one official policy number.

---

## 3. Visuals

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Where the Energy Is Lost (waterfall) | Primary supply → transformation losses → T&D losses → other → final consumption, for the range's final year. Checked to balance exactly: supply = losses + consumption. |
| **V2** | Energy We Import | Import share over time as a line, imported volume as context bars. Years with no import row stay blank. |
| **V3** | Gas Made vs Gas Used | Bars for production and consumption, the deficit shaded, self-sufficiency % on a second axis against its benchmark line. |
| **V4** | Distance to Each Target | All four KPI gaps as bars on one axis; above the middle line = benchmark met. |

The "better or worse" slope chart was removed from the page; V4 already
carries the direction answer for all four metrics.

Sidebar is deliberately minimal: one **Years to show** range (2002–2035) that
sets the judging year and zooms every chart, plus the shared unit selectors.

---

## 4. Projection rules (2025 → 2035)

- **Primary supply** — geometric trend of the last five reported years, clamped
  to −5% … +8%/yr.
- **Energy losses %** — five-year average level with the observed slope halved
  and frozen after six years (the ratio has been flat since 2016).
- **Import dependence** — the 2014–2018 import-share slope extended at 65%
  strength, capped at 60%.
- **Renewable share** — damped least-squares slope of recent years; generation
  grows at its five-year CAGR.
- **Gas** — production declines and consumption grows at recent rates (floors
  −2% / +2% per year), which is what widens the self-sufficiency gap.
- **Waterfall split** — the last reported loss breakdown is held constant; final
  consumption closes the balance.

These are trend extrapolations, not forecasts — they show what happens if
nothing changes.

---

## 5. Data

| Table | Used for |
|---|---|
| `fact_energy_overview` | supply, consumption, transformation & T&D losses (TOE), reported 2005–2019 |
| `fact_primary_energy_supply` | supply and imports by source (TOE), reported 2002–2024 |
| `fact_renewable_energy` | generation by source (GWh) |
| `fact_natural_gas` | production & consumption (BCF), reported 1999–2018 |
| `dim_target` | benchmark, direction and source of each target |

Known limits: import rows stop at 2018 (K2 prints "no reading" after that until
the projection takes over, tagged *Projected*); losses stop at 2019; K2's 0%
benchmark is the historical minimum and is arithmetically unreachable.

---

## 6. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/bottleneck_metrics.py`](../../core/bottleneck_metrics.py) | series build, projection, gaps, ranking |
| Benchmarks | [`core/targets.py`](../../core/targets.py) | `dim_target` load, policy overrides, severity bands |
| Charts | `charts.py` | the four Plotly visuals |
| Page | `page.py` | sidebar, KPI cards, layout |

Base units TOE · GWh · BCF · MW — percentages are unit-free.
See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
