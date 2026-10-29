# Q2 — Renewable Scenarios

**Question:** *What are the potential outcomes of installing renewable energy sources in different energy scenarios?*

It reads reported history from MySQL, extends it to 2035 under five policy
scenarios, and reports the outcome of each. Everything on the page reacts live
to the two sidebar slicers.

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "potential outcomes" | RE share, capacity built, CO₂ avoided and import savings at the horizon year |
| "installing renewable energy" | Solar / wind / hydro / other generation compounded from the last reported year (2025) |
| "different energy scenarios" | All five projected together, and shown side by side in one chart |

Each scenario keeps the growth rates it was defined with -- there is no manual
override -- so the five stay a like-for-like comparison rather than one tweaked
contender.

---

## 2. Layout

### 2.1 KPI cards — scenario outcomes

These are **not** historical values. Each card reports the selected scenario at
the **final year of the sidebar Year Range**. Change Scenario or Year Range and
the cards move.

| KPI | Working | Default (Accelerated, 2035) |
|---|---|---|
| **Renewable Share** | `re_gwh / total_gen_gwh × 100` | 73.5% of all power |
| **Renewable Power Built** | sum of projected `installed_capacity_mw` across sources | 36,135 MW |
| **CO₂ Avoided** | cumulative `co2_avoided_t` after the last reported year, auto-scaled t → kt → Mt | 258.6 million tonnes of CO₂ |
| **Gas Import Savings** | cumulative `lng_savings_musd` after the last reported year | $21,607 million USD |

Every card label is written in plain words, not unit symbols: mass units read
"million tonnes of CO₂" rather than "MtCO₂", and money reads "million USD"
rather than "$21,607M".

The first two cards also show the change against 2024 ("32.6 percentage points
more than 2024", "120.4% more than 2024"), coloured by whether the movement is
an improvement. The two savings cards give the running total with that year's
own figure underneath ("2035 alone: …"). If the range stops at a recorded year
there is nothing forecast to total, so those two cards show
"-- needs a later end year" instead of a zero.

**Scenario spread at 2035** (the whole point of the dashboard), read from
`compare_all_scenarios`:

| Scenario | RE Share | CO₂ at 2035 | CO₂ avoided (cum.) | LNG saved (cum.) |
|---|---|---|---|---|
| Baseline | 32.0% | 74.8 Mt | 0 | $0 |
| Moderate | 46.0% | 56.3 Mt | 96.5 Mt | $8,066 M |
| Accelerated | 73.5% | 19.7 Mt | 258.6 Mt | $21,607 M |
| Solar-led | 91.3% | 0 | 409.3 Mt | $34,200 M |
| Wind-led | 60.4% | 37.1 Mt | 158.3 Mt | $13,230 M |

### 2.2 Slicers (sidebar)

| Slicer | Range | Effect |
|---|---|---|
| **Pick a scenario** | Baseline / Moderate / Accelerated / Solar-led / Wind-led | Rebuilds every chart and KPI card |
| **Years to show** | 2000 – 2035 | Zooms the charts; sets the year the KPI cards are judged on |
| **Unit Selection** | Electricity, Power, Emission | Re-renders charts and cards in the chosen unit |

### 2.3 Visuals

| # | Chart | Working |
|---|---|---|
| V1 | **Renewable Share Over Time** (actual + forecast) | All five at once; history solid, projection dashed |
| V2 | **Where the Power Comes From** stacked column | Solar / wind / hydro / nuclear / gas / coal per year, active scenario |
| V3 | **Results** — toggle *One year at a time* or *All five scenarios* | Yearly displaced fossil and avoided CO₂, or all five scenarios at the horizon |
| V4 | **Renewable Power Plants Built** stacked area | Hydropower / wind / solar / bagasse |

---

## 3. Data

| Table | Used for |
|---|---|
| `fact_renewable_energy` | Solar / wind / hydro / other / coal / gas / nuclear generation (GWh), capacity (MW), demand |
| `fact_renewable_capacity` | Installed capacity by source (2006–2018) |
| `dim_emission_factor` | Emission factors (tCO₂/MWh) |
| `dim_year` | Fiscal year ↔ calendar year |

**Key joins:** `fact_renewable_energy.calendar_year → dim_year.calendar_year`;
other fact tables on `dim_year.year_id`.

**Base units:** TOE · GWh · MW · BCF · t · USD. The Unit Selection slicer
converts at render time — see [UNIT_GUIDE.md](../../UNIT_GUIDE.md).

---

## 4. Method & assumptions

**Actual vs projected.** Reported data runs to **2025** for generation (the
FY2025-26 row from Economic Survey 2025-26 / Ember); everything after the last
reported year is modelled, and the chart boundary is drawn explicitly (solid =
reported, dashed = projected).

**Growth.** Generation compounds from the last reported year:
`value(year) = base × (1 + growth/100)^n`. Scenario presets:

| Scenario | Solar | Wind | Hydro | Other |
|---|---|---|---|---|
| Baseline | 2.0% | 2.0% | 1.0% | 1.0% |
| Moderate | 8.0% | 8.0% | 2.0% | 3.0% |
| Accelerated | 15.0% | 15.0% | 3.0% | 5.0% |
| Solar-led | 25.0% | 5.0% | 1.5% | 2.0% |
| Wind-led | 5.0% | 25.0% | 1.5% | 2.0% |

Demand grows at 2.5%/yr and nuclear at 1.5%/yr. Fossil generation fills whatever
demand remains after renewables and nuclear, split 35.6% coal / 64.4% gas.

**Emission factors** (tCO₂/MWh) come from `dim_emission_factor`, with
`config/settings.py` as the fallback: **coal 0.9, gas 0.4, oil 0.7**, hydro /
nuclear / renewables 0. CO₂ avoided compares each scenario against a status-quo
baseline in which renewables keep growing at only 2%/yr.

**LNG savings** value avoided gas generation at ~$75 M per TWh.

---

## 5. Known limitations

- A year inside the reported window (up to 2025) that the record never reported
  prints nothing — no zero, no carry from another year. The scenario paths are
  model output from the first unreported year onwards.
- Reported capacity now reaches FY2025-26 in `fact_renewable_capacity`; the
  projection still scales renewable capacity with renewable generation.
- When the Year Range ends before 2024 the page stays on recorded history: the
  two savings cards show "-- needs a later end year" rather than a zero.
- Compounding a 25%/yr growth rate to 2035 gives very large capacity (Wind-led
  reaches ~70 GW); that is the arithmetic of the assumption, not a feasibility
  claim.

---

## 6. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar slicers, KPI computation, layout |
| `charts.py` | The four visuals (V3 is built two ways) |
| `config.py` | `KPI_CONFIG` (card metadata) and `DEFAULT_SCENARIO` |
| `README.md` | This document |

Related: [`core/projections.py`](../../core/projections.py) (scenario engine),
[`core/units.py`](../../core/units.py) (conversion),
[`core/components.py`](../../core/components.py) (cards, footer).
