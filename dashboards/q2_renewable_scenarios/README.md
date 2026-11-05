# Q2 — Renewable Energy Scenarios & Policy Impact

Answers Question 2: *"What renewable-energy scenarios could Pakistan follow, and
what would each one mean for the power mix, emissions and gas imports?"*

The page grows five "what-if" paths from the last reported year and shows where
each one ends up. Everything to the left of the horizon is real data; everything
to the right is a scenario projection, clearly drawn as dashed lines.

---

## 1. Algorithms & formulas

| Technique | Formula / rule |
|---|---|
| **Compound growth** | Each renewable source grows year on year: `value(year n) = base × (1 + g/100)ⁿ`, where `base` is the last reported year and `g` is the scenario's growth rate for that source. |
| **Scenario what-if** | Five fixed growth-rate sets (table below) — the only input that changes between paths. |
| **Demand ceiling** | Total demand grows at a steady `demand_growth` (default **2.5%/yr**); nuclear grows **1.5%/yr**. Renewables + nuclear take what they take; whatever is left is fossil. |
| **Fossil split** | The leftover residual demand is split in the country's standing ratio: `coal = 35.6%` and `gas = 64.4%` of remaining fossil power. |
| **Counterfactual baseline** | "Avoided" numbers compare the scenario against a status-quo world where renewables keep growing at only 2%/yr (hydro 1%/yr). `avoided_fossil = baseline_fossil − scenario_fossil`. |
| **CO₂ accounting** | `co2_t = fossil_GWh × 1000 × factor`, with t CO₂/MWh: coal **0.9**, gas **0.4**, oil **0.7**. |
| **Gas-import savings** | Every GWh of gas power the scenario removes saves imported LNG: `savings = gas_avoided_TWh × $75 M` (≈ $75 million per TWh). |
| **Capacity mapping** | Renewable MW is grown with the same compound rule from the last reported capacity, scaled to the energy projection. |

### The five scenarios (%/yr growth)

| Scenario | Solar | Wind | Hydro | Other RE |
|---|---|---|---|---|
| Baseline | 2 | 2 | 1 | 1 |
| Moderate | 8 | 8 | 2 | 3 |
| **Accelerated** (default) | 15 | 15 | 3 | 5 |
| Solar-led | 25 | 5 | 1.5 | 2 |
| Wind-led | 5 | 25 | 1.5 | 2 |

---

## 2. KPI cards (scenario outcomes at the horizon year)

All four cards read the **selected scenario's** projected final year — they move
when you change the Scenario or Year Range in the sidebar.

| Card | Value | How it is computed |
|---|---|---|
| **Renewable Share** | `renewable_GWh / total_GWh × 100` in the horizon year | shown with the % change vs the last reported year |
| **Renewable Power Built (MW)** | solar + wind + hydro + other RE capacity in the horizon year | delta vs the last reported capacity, e.g. "+121% more than 2025" |
| **CO₂ Avoided** | `Σ (baseline fossil − scenario fossil) × emission factor` over all projected years — a running total, with the horizon year's own figure underneath | cumulative tonnes kept out of the air |
| **Gas Import Savings** | `Σ gas_replaced_TWh × $75 M` over the projected years | cumulative USD not spent on LNG |

If the chosen year range ends before the horizon, the cards that need a future
year say so instead of showing a zero.

---

## 3. Visuals

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Renewable Share Over Time | Solid line = recorded history of `renewable / total × 100`; dashed lines = all five scenario paths; the selected scenario is highlighted. |
| **V2** | Where the Power Comes From | Stacked area by source (solar, wind, hydro, nuclear, gas, coal) for every year under the selected scenario. |
| **V3** | Outcomes (two modes) | **Yearly tab:** one line per year showing fossil power replaced, CO₂ avoided, and savings. **Comparison tab:** the five scenarios side by side at the horizon year — renewable share, fossil replaced, CO₂ avoided. |
| **V4** | Renewable Power Plants Built | Stacked MW capacity by renewable source over the years — the build-out the scenario needs. |

---

## 4. Data

| Query | Table | Used for |
|---|---|---|
| `Q_RENEWABLE_ENERGY` | `fact_renewable_energy` | solar/wind/hydro/other generation base |
| `Q_ELEC_GEN` | `fact_elec_generation` | total generation base |
| `Q_RENEWABLE_CAPACITY` | `fact_renewable_capacity` | MW capacity base |
| `Q_ECONOMIC` | `fact_economic_indicators` | demand context |

Projection base = the latest year that actually reported values. Missing years
are never carried forward as zeros.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/projections.py`](../../core/projections.py) | compound growth, scenario paths, avoided CO₂ & savings |
| Settings | [`config/settings.py`](../../config/settings.py) | SCENARIOS rates, emission factors, LNG $/TWh |
| Charts | `charts.py` | the four Plotly visuals |
| Page | `page.py` | sidebar controls, KPI cards, layout |

Base units GWh · MW · t CO₂ · USD — see [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
