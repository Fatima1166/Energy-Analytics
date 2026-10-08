# Q4 — Forecasted Energy Demand (1999–2035)

**Question:** *What is forecasted energy demand?*

Answers it in three moves: what demand has actually done, what drives it, and
what it becomes to 2035 under Low, Base and High scenarios — with the forecast
backtested so the numbers can be defended.

Engine: [`core/demand_forecast.py`](../../core/demand_forecast.py).
Reproduce every figure without opening a browser:
`python scripts/verify_demand_forecast.py`.

---

## 1. How the question is answered

| Objective | Where it is answered |
|---|---|
| 1. Historical demand trends 1999–2024 (electricity, gas, total final energy) | **E1** KPI strip, **E2** V1 history |
| 2. Forecast 2025–2035 under Low / Base / High | **E3** V2 scenario fan |
| 3. Link demand to GDP, population and GDP growth | **E4** V3 drivers, **E5** V4 decomposition |
| 4. Demand by sector and province to 2035 | **E6** V5 sector and province mix |
| 5. Demand vs supply: gaps and import dependency to 2035 | **E7** V6 supply gap, import dependency |
| 6. Forecast reliability: MAPE, RMSE, R² | **E8** V7 reliability |

Eight elements — the maximum the brief allows — in the order above.

---

## 2. The eight elements

| # | Element | What it shows |
|---|---|---|
| **E1** | KPI strip (5 cards) | Demand in 2024 and at the horizon, forecast growth rate, income elasticity, 2035 supply gap |
| **E2** | V1 History 1999–2024 | Total final energy, electricity and gas, absolute and indexed to the first year |
| **E3** | V2 Scenario fan 2025–2035 | Low / Base / High paths for the three final-energy series, envelope shaded |
| **E4** | V3 Demand drivers | Demand vs real GDP, real GDP per head and population, plus the per-capita elasticity fit |
| **E5** | V4 Driver decomposition | Each year's growth split into income-per-head, population and intensity residual |
| **E6** | V5 Sector and province mix | Electricity demand by end-use sector (reported vs 2035) and province share paths |
| **E7** | V6 Supply–demand gap | Primary supply vs demand with the gap, and gas / electricity import dependency |
| **E8** | V7 Forecast reliability | Hold-out MAPE per model, predicted vs reported, and the metric table |

### KPI cards (E1)

| Code | KPI | Working |
|---|---|---|
| **K1** | Total final energy demand | Reported 2024 level, horizon level under the chosen scenario, % change |
| **K2** | Grid electricity demand | Reported GWh, horizon GWh, implied growth rate |
| **K3** | Demand growth | Forecast CAGR against the reported CAGR over the calibration window |
| **K4** | Income elasticity | ε from `ln(demand/head) ~ ln(real GDP/head)`, with the fit R² |
| **K5** | Supply–demand gap | Horizon gap as a share of primary supply, the projected supply CAGR and the CAGR needed to close it |

---

## 3. Default view (calibration 2012–2024, horizon 2035, Base GDP 4.0%/yr ± 1.5pp)

**Demand**

| Series | 2024 reported | 2035 Low | 2035 Base | 2035 High | Base growth |
|---|---|---|---|---|---|
| Total final energy (MTOE) | 76.56 | 80.34 | **95.22** | 112.57 | +2.01%/yr |
| Electricity, final energy (MTOE) | 15.09 | 23.43 | **28.82** | 35.30 | +6.06%/yr |
| Gas, final energy (MTOE) | 31.86 | 28.21 | **25.88** | 23.74 | −1.86%/yr |
| Grid electricity demand (GWh) | 175,440 | 241,191 | **300,586** | 372,992 | +5.02%/yr |

**Drivers** (fitted 2012–2024, income elasticity from the per-capita log-log fit)

| Series | ε (income) | R² per-capita | R² vs total GDP | Post-2019 residual |
|---|---|---|---|---|
| Total final energy | 1.04 | 0.924 | 0.948 | −4.18 pp/yr |
| Electricity, final energy | 1.32 | 0.981 | 0.988 | +2.59 pp/yr |
| Gas, final energy | −0.6 (clamped) | 0.952 | 0.974 | −4.87 pp/yr |
| Grid electricity demand | 1.39 | 0.880 | 0.948 | +0.16 pp/yr |

Population growth over the window: **+1.58%/yr**.

**Sector and province, 2035 Base** (GWh)

| Sector | 2024 | 2035 | | Province | 2024 | 2035 | Share |
|---|---|---|---|---|---|---|---|
| Domestic | 74,000 | 135,476 | | Punjab | 90,000 | 152,489 | 60.6% |
| Industrial | 36,500 | 53,386 | | Sindh | 30,400 | 49,241 | 19.6% |
| Agriculture | 13,800 | 22,758 | | KPK | 15,600 | 27,428 | 10.9% |
| Commercial | 11,800 | 20,873 | | Balochistan | 7,600 | 14,672 | 5.8% |
| Bulk Supply | 7,800 | 13,864 | | AJK | 3,300 | 7,858 | 3.1% |
| **Total** | **145,013** | **248,454** | | **Total** | **146,900** | **251,688** | 100% |

**Supply and imports, 2035**

| Metric | 2024 | 2035 | Note |
|---|---|---|---|
| Primary supply (MTOE) | 75.7 | 90.7 | trend-projected at +1.65%/yr |
| Final demand, Base (MTOE) | 76.6 | 95.2 | scenario fan |
| Gap | ≈0 | −4.5 MTOE (−4.98% of supply) | demand outgrows supply |
| Supply CAGR needed to close it | — | **+2.1%/yr** | against +1.65%/yr projected |
| Gas import dependency | 1.2% (2018) | **41.0%** | production flat, consumption rising |
| Electricity import share | 0.31% | 0.20% | reported only to 2023 |

**Backtest** (fit ≤ 2020, hold-out 2021–2024)

| Series | Hold-out MAPE Trend | Hold-out MAPE Driver | Calibration R² Trend | Calibration R² Driver | Lower error |
|---|---|---|---|---|---|
| Total final energy | 23.30% | **16.07%** | 0.985 | 0.994 | Driver |
| Electricity, final energy | **4.75%** | 18.92% | 0.996 | 0.979 | Trend |
| Gas, final energy | **11.80%** | 15.09% | 0.988 | 0.984 | Trend |
| Grid electricity demand | 4.77% | **3.72%** | 0.972 | 0.921 | Driver |

The driver model wins where income genuinely moves demand (total demand, grid
demand) and loses where the 2022–24 gas squeeze dominates (gas, electricity
final energy). The reliability panel states which is which rather than hiding it.

---

## 4. Method

### 4.1 Elasticities are estimated on real GDP, in per-capita space

Current-USD GDP moves with the exchange rate — the rupee's slide is big enough
that USD GDP *fell* 9.9% in 2019 while real GDP grew 2.5%. Using it produces
sign-flipped elasticities. Instead:

* real GDP is chained from `gdp_growth_pct` (`index_t = index_(t-1) × (1 + g_t)`);
* the model is fitted as
  `ln(demand / population) = b0 + ε · ln(real GDP per head) + b2 · D`, where `D`
  is the 2019 basis dummy;
* population then enters the projection with coefficient 1 (people consume):
  `g_demand = g_population + ε · (g_GDP − g_population) + residual`.

A two-factor fit of `ln(demand)` on `ln(GDP)` *and* `ln(population)` was tried
first and rejected: over a 13-year sample the two regressors are collinear and
the income elasticity came out at zero or negative for every series.

### 4.2 The 2019 reporting-basis change

`fact_final_energy_consumption` jumps 53% between 2018 and 2019 (55.0 → 84.1
MTOE) and then falls every year to 2024. That is a coverage change, not demand.
It is detected automatically (`detect_break`: largest log jump ≥ 20% and ≥ 2.5×
the typical year) and handled three ways:

* a **level dummy** in every fitted model, so the trend slope is not contaminated;
* the **residual drift** is measured only in years *after* the break, so the jump
  cannot masquerade as growth;
* the jump year is dropped from the decomposition chart, and the break is marked
  on V1.

### 4.3 Scenarios

`g = g_population + ε · (g_GDP − g_population) + residual × decay`

* Base GDP growth is a sidebar slider (default = median of the last ten reported
  years, 4.0% here); Low = Base − spread, High = Base + spread (default ±1.5pp).
* The residual drift fades **linearly to zero by the horizon**, so the post-2019
  contraction is not compounded for eleven years.
* Growth is clamped to −8%…+14%/yr and ε to −0.6…+2.5. The negative floor is
  deliberate: gas demand genuinely moves against income in this data.
* The **Forecast basis** control switches between the driver model and the
  log-linear trend (shifted by half the GDP surprise), so the two can be compared.

### 4.4 Sector and province allocation

Group shares are trended at the fitted log rate, **clamped to ±3% per year** and
renormalised to sum to 100%; the group total follows the electricity scenario
growth anchored on that table's own last reported year. Parts therefore always
add up to the whole, and small categories cannot explode.

---

## 5. Sidebar

| Control | Range | Effect |
|---|---|---|
| **Scenarios** | Low / Base / High | Which paths are drawn and which enclose the KPI cards |
| **Forecast basis** | Driver / Trend | Elasticity-driven or pure-trend projection |
| **Calibration start** | 2005 – 2020 | Fit window for elasticities, residuals and the trend |
| **Forecast horizon** | 2026 – 2035 | Last modelled year; the residual drift decays to zero here |
| **Base GDP growth %** | 1.0 – 8.0 | Base scenario real GDP growth |
| **Scenario spread ±pp** | 0.0 – 3.0 | Distance from Base to Low and High |
| **Unit Selection** | Energy (TOE/KTOE/MTOE), Electricity (GWh/TWh/MWh) | Re-renders every axis, hover and KPI |

---

## 6. Data

| Table | Used for | Reported |
|---|---|---|
| `fact_final_energy_consumption` + `dim_energy_source` | Total, electricity and gas final demand (TOE) | 2002–2024 |
| `fact_renewable_energy` | Grid electricity demand (GWh) | 2000–2024 |
| `fact_economic_indicators` | GDP, GDP growth, population | 2000–2024 |
| `fact_elec_sector_consumption` + `dim_sector` | Sector demand (GWh) | 2002–2024 |
| `fact_elec_province_consumption` + `dim_province` | Province demand (GWh) | 2002–2024 |
| `fact_primary_energy_supply` | Primary supply for the gap (TOE) | 2002–2024 |
| `fact_elec_generation` | Electricity imports and generation (GWh) | 2002–2023 |
| `fact_natural_gas` | Gas production and consumption (BCF) | 1999–2018 |
| `dim_year` | Fiscal year ↔ calendar year | 1999–2024 |

Base units: TOE · GWh · BCF · USD · persons — converted for display by
[`core/units.py`](../../core/units.py).

---

## 7. Known limitations

* **The 2019 basis change caps how far the levels can be trusted.** The
  pre-2019 and post-2019 final-energy series are not on the same basis, so V6's
  level gap between primary supply and final demand is *indicative*; the growth
  rates and the gap direction are the robust part. The footer says so on screen.
* **`fact_lng_imports.imports_bcf` is unusable** — 3.7 BCF is recorded against
  USD 3.4bn of imports, so the volume column contradicts its own value column.
  Gas import dependency is therefore built from the production/consumption
  balance instead.
* **Oil and coal import shares are not recorded** in the warehouse, so national
  import dependency cannot be measured end-to-end; only gas and electricity are
  shown.
* **Gas-by-sector data stops at 2018** and gas-by-province exists for 2018 only,
  so the sector and province mixes use electricity, which is reported to 2024.
* **The hold-out window is four years.** MAPE and RMSE are read from it; R² is
  reported from the calibration fit, where it is meaningful.
* Projections are transparent extrapolations of fitted relationships, not a
  bottom-up demand model; no price, policy or weather elasticity is available in
  the data.

---

## 8. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, eight elements, KPI cards, reliability table, footer |
| `charts.py` | The seven Plotly figures |
| `config.py` | Element/objective map and the colour vocabulary |
| `README.md` | This document |

Related: [`core/demand_forecast.py`](../../core/demand_forecast.py) (models,
scenarios, composition, gap, backtest),
[`core/queries.py`](../../core/queries.py) (SQL),
[`scripts/verify_demand_forecast.py`](../../scripts/verify_demand_forecast.py)
(prints every number above from live MySQL),
[`scripts/smoke_test_app.py`](../../scripts/smoke_test_app.py) (headless render
check of all three dashboards).
