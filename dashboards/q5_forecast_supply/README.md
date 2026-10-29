# Q5 — Forecasted Energy Supply

**Question:** *What is forecasted energy supply?*

The page answers it in plain steps: what supply has really been, the three paths
it can take to 2035, what the electricity is made of, whether it keeps up with
demand, how much of it is bought from abroad, and how far the guess can be
trusted.

Engine: [`core/supply_forecast.py`](../../core/supply_forecast.py).
Reproduce every figure without opening a browser:
```powershell
.venv\Scripts\python.exe scripts\verify_supply_forecast.py
```

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "forecasted" | Three paths — slow, planned and fast supply growth — drawn from the last measured year to the horizon |
| "energy supply" | Total primary energy and electricity generated, each in real units |
| "how much, how soon" | KPI cards for supply today, supply at the horizon, and whether it covers demand |
| "is it enough" | Visual 4 puts the supply line next to the demand line it has to meet |
| "can we believe it" | Visual 6 tests both models on four years they were not shown |

How much **demand** there will be is [Q4](../q4_forecast_demand/README.md)'s
answer. This page does not refit it: it carries the last measured demand forward
at a flat 4.8% a year, only as the line supply is measured against.

---

## 2. The three KPI cards

| Code | Card | What it says |
|---|---|---|
| **K1** | Total primary energy supply | The last measured level, the level at the horizon under the chosen scenario, and the % change |
| **K2** | Electricity generation | The same three numbers for generated electricity, plus the yearly growth rate |
| **K3** | Does supply cover demand | How far supply sits above or below demand at the horizon, in %, with the supply and demand levels and the comfortable 15%–25% band |

**Default view** (fitted 2012–2024, horizon 2035, planned GDP growth = the median
of the last ten reported years, Low/High = ±1.5pp around it):

| Series | 2024 measured | 2035 Low | 2035 Base | 2035 High | Base growth |
|---|---|---|---|---|---|
| Total primary supply (MTOE) | 75.73 | 86.29 | **93.25** | 100.72 | +1.91%/yr |
| Electricity generated (GWh) | 154,480 | 276,171 | **385,837** | 533,758 | +8.68%/yr |
| Clean generation (GWh) | 86,140 | 125,109 | **161,512** | 207,727 | +6.90%/yr |
| Clean share of generation (%) | 55.76 | 45.30 | **41.86** | 38.92 | against the 60% goal |

---

## 3. Layout

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **Supply so far** | Primary energy by source and electricity by source, stacked, for the measured years |
| V2 | **Three ways supply can go** | Measured history, then the slow / planned / fast paths to the horizon, dashed, with the band between slow and fast shaded |
| V3 | **What the electricity is made of** | Each generating source stacked, with the clean share on the right axis next to the 60% clean goal and the 30% renewables goal |
| V4 | **Does supply cover demand** | Generated electricity against the demand it must meet; the shaded part is spare supply |
| V5 | **Where the supply comes from** | Energy made at home against energy bought from abroad, with the imported share on the right axis |
| V6 | **How far to trust the forecast** | The average error per series and model on the four years the model had not seen |

Things that were cut, and why: the installed-capacity chart and its card (MW is a
build-plan figure, not a supply, and the question asks what supply will be), the
separate reserve-margin chart (its one number is the whole of card K3 and the
shape of V4), the predicted-versus-actual path and the model metrics table (V6's
bars carry the same message in one look), and a clean-share card (V3 already shows
the share and its two goals).

### 3.2 Sidebar

Deliberately minimal — two controls, plus the shared Unit Selection.

| Control | Range | Effect |
|---|---|---|
| **Scenarios to show** | Low / Base / High | Which paths are drawn, and which scenario the cards read |
| **Forecast up to** | 2026 – 2035 | The last year the model looks ahead to |
| **Unit Selection** | Energy (TOE/KTOE/MTOE), Electricity (GWh/TWh/MWh) | Re-renders every axis, hover and card |

There are no fitting knobs. The model always uses the driver method, the 2012
calibration start and the data-driven GDP default, because leaving them open lets
the same question be answered several different ways.

---

## 4. Method

### 4.1 Two ways to project one series

For each series (total primary supply, electricity generated, clean generated) the
engine fits, over 2012–2024:

* **driver model** — `ln(supply) = a + ε · ln(real GDP)`, with ε kept in 0.1…2.5;
* **trend model** — `ln(supply) = a + b · years since 2012`, with b kept in −2…+12%/yr.

Real GDP is chained from the reported `gdp_growth_pct`, so the exchange rate cannot
creep into the answer. The page draws the driver model; the trend model stays fitted
because V6 compares the two.

### 4.2 The three scenarios

`g = ε × GDP growth`, clamped to 0.5…12% a year.

Planned GDP growth is the median of the last ten reported years (from
`fact_economic_indicators`), Low is that minus 1.5pp and High is it plus 1.5pp. The
path is then compounded from the last measured year to the horizon.

### 4.3 What the electricity is made of

Each source follows the planned build-out in the reported record — hydro and solar
expanding, nuclear as clean baseload, coal and gas as the dispatchable balance — and
is rescaled so the parts always add up to the scenario's total generation. The clean
share is the sum of hydro, nuclear, solar, wind and other renewables over that total,
read against the 60% clean goal and the 30% renewables goal.

### 4.4 Does supply cover demand

`margin % = (supply − demand) / demand × 100`, with demand at its measured value up
to 2024 and carried on at 4.8% a year after it. The bands are the ones planning
practice uses: under 10% is **not enough supply**, 10–25% is a **comfortable
margin**, above 25% is **more built than needed**.

| Scenario | 2035 supply (GWh) | 2035 demand (GWh) | Margin | Read as |
|---|---|---|---|---|
| Low | 276,171 | 293,834 | **−6.0%** | Not enough supply |
| Base | 385,837 | 293,834 | **+31.3%** | More built than needed |
| High | 533,758 | 293,834 | **+81.7%** | More built than needed |

The point the page makes is not that one scenario is right, but that supply growth
here runs ahead of demand growth: the risk in this data is spare capacity, not
shortage.

### 4.5 Where the supply comes from

Imports are measured directly (`imports_toe` in the primary supply table) and shown
against total supply. After 2024 the imported share moves in a straight line from the
measured 28.5% (2024) to the share each scenario assumes for the horizon — 31% slow,
22% planned, 16% fast — because the warehouse holds no fuel-price or policy series to
fit one. It is a stated path, and the chart says so by sitting on the dashed side of
the boundary.

### 4.6 Testing the forecast

Each model is fitted only on years up to 2020 and then asked to predict 2021–2024,
which it has not seen. V6 shows the average error of each attempt.

| Series | Trend model | Driver model | Easier to beat |
|---|---|---|---|
| Total primary supply | 13.45% | **12.65%** | Driver |
| Electricity generated | 11.39% | **7.83%** | Driver |
| Clean generation | **24.00%** | 25.37% | Trend |

The income-linked model wins on total supply and on generation, and both models are
far off on clean generation — the years 2021–2024 are exactly when solar and wind
started arriving faster than any relationship in the earlier data would predict. V6
names both models instead of hiding the worse one.

---

## 5. Data

| Table | Used for | Reported |
|---|---|---|
| `fact_primary_energy_supply` + `dim_energy_source` | Supply by source, total, imports (TOE) | 1999–2024 |
| `fact_renewable_energy` | Generation by technology and grid demand (GWh) | 2000–2024 |
| `fact_elec_generation` | Total generation and installed capacity cross-check (GWh, MW) | 2000–2024 |
| `fact_economic_indicators` | GDP growth, population | 2000–2024 |
| `dim_year` | Fiscal year ↔ calendar year | 1999–2024 |

Base units: TOE · GWh · USD — converted for display by
[`core/units.py`](../../core/units.py).

Every point is tagged, and the tag drives the line style: what was reported is
solid, what the model expects is dashed, and the vertical line in each chart marks
where one stops and the other starts. A year inside the window the record never
reported prints nothing — it is not filled with 0 or carried from a neighbouring
year — and each card names the year its value actually came from (or *no reading*).
Projection starts at 2025.

---

## 6. Known limitations

* **Supply is projected from one relationship.** Growth follows real GDP through a
  fitted elasticity; no plant-level build schedule, fuel price or weather series is
  in the warehouse, so the paths cannot be built on those.
* **The demand line is a benchmark, not this page's forecast.** It is Q4's subject;
  here it is a flat 4.8% a year after 2024, so the margin in K3 and V4 should be read
  as "supply against a reference demand path".
* **The imported share after 2024 is an assumed trajectory** (4.5 above), not a
  fitted result.
* **The test window is four years.** Average error is read from it; the fit quality
  R² comes from the fitting window, where it means something.
* Installed capacity (MW) is deliberately off the page. A build plan is not a supply,
  and mixing the two on one chart makes a planned megawatt look like delivered energy.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, KPI cards, layout |
| `charts.py` | The six Plotly figures |
| `README.md` | This document |

Related: [`core/supply_forecast.py`](../../core/supply_forecast.py) (fits,
scenarios, technology mix, adequacy, imports, backtest),
[`core/queries.py`](../../core/queries.py) (SQL),
[`scripts/verify_supply_forecast.py`](../../scripts/verify_supply_forecast.py)
(prints the numbers from live MySQL),
[`scripts/smoke_test_app.py`](../../scripts/smoke_test_app.py) (headless render
check of all dashboards).
