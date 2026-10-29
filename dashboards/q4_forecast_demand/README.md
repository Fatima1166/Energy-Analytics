# Q4 — Forecasted Energy Demand

**Question:** *What is forecasted energy demand?*

The page answers it in plain steps: what demand has really done, what pushes it
up, where it goes to 2035 under three scenarios, who uses the electricity, and
how far the guess can be trusted.

Engine: [`core/demand_forecast.py`](../../core/demand_forecast.py).
Reproduce every figure without opening a browser:
`python scripts/verify_demand_forecast.py`.

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "forecasted" | Three paths — slow, planned, fast growth — drawn from the last measured year to the horizon |
| "energy demand" | Total energy, electricity and gas, each in real units and as growth from the first year |
| "how much, how soon" | KPI cards for demand today, demand at the horizon, and the yearly growth rate |
| "can we believe it" | Visual 5 tests the models on four years they were not shown |

What supply will do — the supply gap and import dependency — is
[Q5](../q5_forecast_supply/README.md)'s answer, so it is not repeated here.

---

## 2. The three KPI cards

| Code | KPI | What it says |
|---|---|---|
| **K1** | Total energy demand | The last measured level, the level at the horizon under the chosen scenario, and the % change |
| **K2** | Electricity demand | The same three numbers for grid electricity, plus the yearly growth rate |
| **K3** | How fast demand grows | The forecast growth rate a year, next to the rate the data actually shows |

**Default view** (calibration 2012–2024, horizon 2035, planned GDP growth = the
median of the last ten reported years, Low/High = ±1.5pp around it):

| Series | 2024 measured | 2035 Low | 2035 Base | 2035 High | Base growth |
|---|---|---|---|---|---|
| Total final energy (MTOE) | 76.56 | 80.34 | **95.22** | 112.57 | +2.01%/yr |
| Electricity, final energy (MTOE) | 15.09 | 23.43 | **28.82** | 35.30 | +6.06%/yr |
| Gas, final energy (MTOE) | 31.86 | 28.21 | **25.88** | 23.74 | −1.86%/yr |
| Grid electricity demand (GWh) | 175,440 | 241,191 | **300,586** | 372,992 | +5.02%/yr |

---

## 3. Layout

The three cards go into a four-slot row, so each keeps the width a four-up strip
would give it and the last slot stays empty. Card height is `auto`, not the
225 px that the shared `.kpi-balance` sheet in `core/styles.py` pins — a
page-scoped `.kpi-balance.q4-kpi` override lifts it, because a fixed height plus
`margin-top: auto` on the detail block left a dead band across the middle of
every card. The row stays level because all three cards carry three detail rows
and the title block reserves two lines.

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **Demand so far** | Total energy, electricity and gas since 2000, as real amounts and as growth from the first year |
| V2 | **Three ways demand can go** | Measured history, then the slow / planned / fast paths to the horizon, dashed and lightly shaded |
| V3 | **What moves demand** | Demand next to the economy and the population on one growth scale, and demand per head against income per head with the fitted line |
| V4 | **Who uses the electricity** | Each sector's use in the last measured year against its use at the horizon |
| V5 | **How far to trust the forecast** | The average error per series and model on the four years the model had not seen |

Things that were cut, and why: a growth-breakdown chart (it repeated V3), a
province-share chart (a second "who uses it" chart, and the question asks for
demand, not geography), the supply-gap and import charts (Q5's job), a
predicted-vs-actual path plus a metrics table (the bars in V5 already carry the
same message), and two KPI cards for income elasticity and the supply gap.

### 3.2 Sidebar

Deliberately minimal — two controls, plus the shared Unit Selection.

| Control | Range | Effect |
|---|---|---|
| **Scenarios to show** | Low / Base / High | Which paths are drawn, and which scenario the cards read |
| **Forecast up to** | 2026 – 2035 | The last year the model looks ahead to |
| **Unit Selection** | Energy (TOE/KTOE/MTOE), Electricity (GWh/TWh/MWh) | Re-renders every axis, hover and card |

There are no fitting knobs. The model always uses the driver method, the 2012
calibration start and the data-driven GDP default, because leaving them open
lets the same question be answered several different ways.

---

## 4. Method

### 4.1 The fit is done on income per head, in real terms

Current-USD GDP moves with the exchange rate — the rupee's slide is big enough
that USD GDP *fell* 9.9% in 2019 while the economy really grew 2.5%. Using it
flips the sign of the result. Instead:

* real GDP is chained from `gdp_growth_pct` (`index_t = index_(t-1) × (1 + g_t)`);
* the fit is `ln(demand / population) = b0 + ε · ln(income per head) + b2 · D`,
  where `D` is the 2019 basis dummy;
* population then enters the projection with coefficient 1 (people consume):
  `g_demand = g_population + ε · (g_GDP − g_population) + residual`.

A two-factor fit of `ln(demand)` on `ln(GDP)` *and* `ln(population)` was tried
first and rejected: over a 13-year sample the two inputs move together and the
income effect came out at zero or negative for every series.

Fitted elasticities and fit quality (2012–2024):

| Series | ε (income per head) | R² per head | R² vs total GDP | After 2019 |
|---|---|---|---|---|
| Total final energy | 1.04 | 0.924 | 0.948 | −4.18 pp/yr |
| Electricity, final energy | 1.32 | 0.981 | 0.988 | +2.59 pp/yr |
| Gas, final energy | −0.6 (clamped) | 0.952 | 0.974 | −4.87 pp/yr |
| Grid electricity demand | 1.39 | 0.880 | 0.948 | +0.16 pp/yr |

Population growth over the window: **+1.58%/yr**.

### 4.2 The 2019 change in reporting basis

`fact_final_energy_consumption` jumps 53% between 2018 and 2019 (55.0 → 84.1
MTOE) and then falls every year to 2024. That is a change in what is covered,
not a change in demand. It is found automatically (`detect_break`: largest log
jump ≥ 20% and ≥ 2.5× the typical year) and handled three ways:

* a **level dummy** in every fit, so the trend slope is not contaminated;
* the **leftover drift** is measured only in years *after* the jump, so the jump
  cannot pass itself off as growth;
* the jump year is dropped from the fitted points, and the break is marked on V1.

### 4.3 Scenarios

`g = g_population + ε · (g_GDP − g_population) + residual × decay`

* Planned GDP growth is the median of the last ten reported years; Low is that
  minus 1.5pp and High is it plus 1.5pp.
* The leftover drift fades **linearly to zero by the horizon**, so the
  post-2019 contraction is not compounded for eleven years.
* Growth is clamped to −8%…+14%/yr and ε to −0.6…+2.5. The negative floor is
  deliberate: gas demand genuinely moves against income in this data.

### 4.4 Sector shares

Sector shares move at the fitted log rate, **clamped to ±3% a year**, and are
renormalised to add to 100%; the sector total follows the electricity scenario
growth anchored on that table's own last measured year. Parts therefore always
add up to the whole, and small categories cannot explode.

**Sectors, 2035 Base** (GWh)

| Sector | 2024 | 2035 |
|---|---|---|
| Domestic | 74,000 | 135,476 |
| Industrial | 36,500 | 53,386 |
| Agriculture | 13,800 | 22,758 |
| Commercial | 11,800 | 20,873 |
| Bulk Supply | 7,800 | 13,864 |
| **Total** | **145,013** | **248,454** |

### 4.5 Testing the forecast

Each model is fitted on years up to 2020 and then asked to predict 2021–2024,
which it has not seen. The bar chart shows the average error of each attempt.

| Series | Average error, Trend | Average error, Driver | Easier to beat |
|---|---|---|---|
| Total final energy | 23.30% | **16.07%** | Driver |
| Electricity, final energy | **4.75%** | 18.92% | Trend |
| Gas, final energy | **11.80%** | 15.09% | Trend |
| Grid electricity demand | 4.77% | **3.72%** | Driver |

The income model wins where money really moves demand (total demand, grid
demand) and loses where the 2022–24 gas shortage dominates (gas, electricity
final energy). V5 names both models instead of hiding the worse one.

---

## 5. Data

| Table | Used for | Reported |
|---|---|---|
| `fact_final_energy_consumption` + `dim_energy_source` | Total, electricity and gas demand (TOE) | 2002–2024 |
| `fact_renewable_energy` | Grid electricity demand (GWh) | 2000–2024 |
| `fact_economic_indicators` | GDP growth, income per head, population | 2000–2024 |
| `fact_elec_sector_consumption` + `dim_sector` | Sector use (GWh) | 2002–2024 |
| `dim_year` | Fiscal year ↔ calendar year | 1999–2024 |

Base units: TOE · GWh · USD · persons — converted for display by
[`core/units.py`](../../core/units.py).

Every point is tagged, and the tag drives the line style: **measured** is solid,
a year the source never reported prints **nothing** (it is not filled in or
bridged), **forecast** is dashed from 2025.

---

## 6. Known limitations

* **The 2019 basis change limits how far the levels can be trusted.** Pre-2019
  and post-2019 final energy are not on the same basis, so the year-on-year
  levels across the break are indicative; the growth rates are the robust part.
* **The test window is four years.** Average error and typical gap are read from
  it; R² comes from the fit window, where it means something.
* **Only three paths are shown.** There is no price, policy or weather series in
  the warehouse, so no scenario can be built on those.
* Projections are honest extensions of fitted relationships, not a bottom-up
  demand model.
* The model is shown on the driver method only; the trend alternative is still
  fitted and still appears in V5, but it is not drawn on the paths.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, KPI cards, layout |
| `charts.py` | The five Plotly figures |
| `README.md` | This document |

Related: [`core/demand_forecast.py`](../../core/demand_forecast.py) (models,
scenarios, sector split, backtest),
[`core/queries.py`](../../core/queries.py) (SQL),
[`scripts/verify_demand_forecast.py`](../../scripts/verify_demand_forecast.py)
(prints every number above from live MySQL),
[`scripts/smoke_test_app.py`](../../scripts/smoke_test_app.py) (headless render
check of all dashboards).
