# Q2 — Renewable Scenarios

**Question:** *What are the potential outcomes of installing renewable energy sources in different energy scenarios?*

An interactive what-if simulator. It reads reported history from MySQL, extends it
to 2035 under five policy scenarios, and reports the environmental and economic
outcome of each. Everything on the page reacts live to the three sidebar slicers.

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "potential outcomes" | Five scenarios projected to 2035, plus a live custom growth-rate slider |
| "installing renewable energy" | Solar / wind / hydro / other generation compounded from the 2024 base |
| "different energy scenarios" | Side-by-side comparison chart and a "best scenario" badge |

The result is a 360° view: **environmental** (CO₂ avoided), **economic** (LNG
import savings) and **technical** (generation mix, capacity, T&D losses).

---

## 2. Layout

### 2.1 KPI cards — scenario outcomes

These are **not** historical values. Each card reports the selected scenario at
the **final year of the sidebar Year Range**, compared with the last reported
year (2024). Change Scenario, Growth Rate or Year Range and the cards move.

| KPI | Working | Default (Accelerated, 2035) |
|---|---|---|
| **RE Share %** | `re_gwh / total_gen_gwh × 100` | 73.5% |
| **RE Capacity** | sum of projected `installed_capacity_mw` across sources | 36,135 MW |
| **CO₂ Emissions** | `coal_gwh × EF_coal + gas_gwh × EF_gas` (t), auto-scaled to t / kt / Mt | 19,654 MtCO₂ |
| **LNG Savings** | cumulative `lng_savings_musd` over 2025 → range end | $21,607 M |
| **CO₂ Intensity** | `co2_t / total_gen_gwh` → kgCO₂ per MWh | 85 kgCO₂/MWh |

Each card also shows the % change against 2024, coloured by whether the movement
is an improvement. If the range ends before 2024 the card reports the scenario's
pre-baseline state and says so instead of showing a backwards delta.

**Scenario spread at 2035** (the whole point of the dashboard):

| Scenario | RE Share | Capacity | CO₂ | LNG Savings | Intensity |
|---|---|---|---|---|---|
| Baseline | 32.0% | 14,626 MW | 74,835 Mt | $0 | 325 |
| Moderate | 46.0% | 20,997 MW | 56,291 Mt | $8,066 M | 245 |
| Accelerated | 73.5% | 36,135 MW | 19,654 Mt | $21,607 M | 85 |
| Solar-led | 92.6% | 90,888 MW | 0 Mt | $37,685 M | 0 |
| Wind-led | 38.1% | 17,309 MW | 66,712 Mt | $3,687 M | 290 |

### 2.2 Scenario impact summary

Four compact metrics under the cards: horizon RE share, cumulative fossil
generation avoided, cumulative CO₂ avoided, and cumulative LNG savings, plus a
**"Best 2035 Strategy"** badge naming the scenario with the highest avoided CO₂.

### 2.3 Slicers (sidebar)

| Slicer | Range | Effect |
|---|---|---|
| **Scenario** | Baseline / Moderate / Accelerated / Solar-led / Wind-led | Rebuilds every chart and KPI card |
| **Growth Rate %** | 0 – 30 | Overrides the scenario's solar & wind growth rate |
| **Year Range** | 2000 – 2035 | Zooms the charts; sets the year the KPI cards are judged on |
| **Unit Selection** | Electricity, Power, Emission | Re-renders charts and cards in the chosen unit |

### 2.4 Visuals

| # | Chart | Working |
|---|---|---|
| V1 | **RE Share % line** (actual + projected) | All five scenarios; history solid, projection dashed |
| V2 | **Generation mix** stacked column | Solar / wind / hydro / other / coal / gas / nuclear per year |
| V3 | **Outcomes** — toggle *Year by year* or *Scenario comparison* | Yearly avoided CO₂ & displaced fossil, or all five scenarios at the horizon |
| V4 | **CO₂ vs RE Share** dual-axis line | Reported CO₂ joined with RE share, extended to the horizon |
| V5 | **Renewable capacity by source** stacked area | Hydel / wind / solar / bagasse |
| V6 | **Capacity vs generation vs T&D losses** combo | Bars = capacity & generation, line = T&D losses |

### 2.5 Footer

A three-line footnote that always describes the live view: the current scenario,
growth rate and range; the method and headline result; the sources; and a short
amber note when the displayed years are projected rather than measured.

---

## 3. Data

| Table | Used for |
|---|---|
| `fact_renewable_energy` | Solar / wind / hydro / other / coal / gas / nuclear generation (GWh), capacity (MW), demand |
| `fact_economic_indicators` | CO₂ emissions (tonnes) |
| `fact_renewable_capacity` | Installed capacity by source (2006–2018) |
| `fact_elec_generation` | Installed capacity, generation, consumption |
| `fact_td_losses` | T&D losses (GWh) |
| `fact_lng_imports` | LNG volume (BCF) and value (M USD) |
| `dim_year` | Fiscal year ↔ calendar year |
| `dim_emission_factor` | Emission factors (tCO₂/MWh) |

**Key joins:** `fact_renewable_energy.calendar_year → dim_year.calendar_year`;
other fact tables on `dim_year.year_id`.

**Base units:** TOE · GWh · MW · BCF · t · USD. The Unit Selection slicer
converts at render time — see [UNIT_GUIDE.md](../../UNIT_GUIDE.md).

---

## 4. Method & assumptions

**Actual vs projected.** Reported data runs to **2024**. Everything after that is
modelled, and the chart boundary is drawn explicitly (solid = reported, dashed =
projected).

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

- Capacity for 2019 onwards is not in `fact_renewable_capacity`; the projection
  scales renewable capacity with renewable generation.
- When the Year Range ends before 2024, the cards show the scenario's
  pre-baseline state — a comparison figure, not a forecast.
- A 30% custom growth rate compounded to 2035 gives very large capacity
  (~164 GW); that is the arithmetic of the assumption, not a feasibility claim.

---

## 6. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar slicers, KPI computation, layout |
| `charts.py` | The six Plotly figures |
| `config.py` | `KPI_CONFIG` (card metadata) and `SCENARIOS_META` |
| `README.md` | This document |

Related: [`core/projections.py`](../../core/projections.py) (scenario engine),
[`core/units.py`](../../core/units.py) (conversion),
[`core/components.py`](../../core/components.py) (cards, footer).
