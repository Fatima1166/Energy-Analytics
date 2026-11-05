# Q5 — Forecasted Energy Supply

**Question:** *What is forecasted energy supply?*

The engine fits how supply has moved with the real economy, then runs that
relationship forward to 2035 under three growth paths. Solid lines are reported
data; dashed lines are the model. Demand here is only a reference line —
forecasting demand is [Q4](../q4_forecast_demand/README.md)'s job.

Reproduce every number without a browser:
```powershell
.venv\Scripts\python.exe scripts\verify_supply_forecast.py
```

---

## 1. Algorithms & formulas

| Step | Formula / rule |
|---|---|
| **Real GDP rebuild** | Current-USD GDP moves with the exchange rate, so real GDP is chained from the reported growth series: `index_t = index_(t−1) × (1 + g_t)` (base 100 in 2000). |
| **Driver model** | Fitted per series over 2012–2024: `ln(supply) = a + ε · ln(real GDP)`, elasticity ε clamped to **0.1…2.5**. This is the model the page draws. |
| **Trend model** | `ln(supply) = a + b · years since 2012`, b clamped to −2…+12%/yr. Kept fitted because V6 compares the two models. |
| **Three scenarios** | Annual supply growth `g = ε × GDP growth`, clamped to **0.5…12%/yr**. Planned GDP growth = median of the last ten reported years; Low = −1.5 pp, High = +1.5 pp. The path compounds from the last measured year to the horizon. |
| **Demand reference** | Measured demand up to 2024, then carried at a flat **4.8%/yr** — a benchmark, not a forecast. |
| **Adequacy margin** | `margin % = (supply − demand) / demand × 100`. Bands: < 10% = not enough supply · 10–25% = comfortable · > 25% = more built than needed. |
| **Technology mix** | Each source follows its reported build trend (hydro/solar expanding, nuclear baseload, coal/gas the dispatchable balance), then all parts are rescaled so they add exactly to the scenario total. `clean share = (hydro + nuclear + solar + wind + other) / total × 100`. |
| **Import share** | Measured directly (`imports_toe / supply_toe × 100`) to 2024; after that a stated straight line from 28.5% to the scenario's horizon assumption (Low 31%, Base 22%, High 16%) — no price/policy series exists to fit. |
| **Backtest** | Refit each model on years ≤ 2020 only, predict the unseen 2021–2024, report the average error per series. |

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Total primary energy supply** | last measured level (card names the year it really came from) | `By <horizon>` under the chosen scenario · `% change = (horizon / now − 1) × 100` · scenario name |
| **K2 — Electricity generation** | last measured generation | same horizon value + % change · badge shows the yearly growth pace |
| **K3 — Does supply cover demand** | `margin %` at the horizon, `(supply − demand) / demand × 100` | supply level · demand level · the comfortable 15–25% band · status word |

A series that never reported shows "--", never a fake zero.

---

## 3. Visuals

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Supply so far | Primary energy by source and electricity by source, stacked, measured years only. |
| **V2** | Three ways supply can go | Measured history, then Low / Base / High paths dashed to the horizon, with the band between slow and fast shaded. |
| **V3** | What the electricity is made of | Generation stacked by source; clean share on the right axis against the 60% clean and 30% renewable goals. |
| **V4** | Does supply cover demand | Generation vs the demand line it must meet; the shaded gap is spare supply. |
| **V5** | Where the supply comes from | Domestic vs imported supply as areas, imported share % on the right axis. |
| **V6** | How far to trust the forecast | Bars of average backtest error per series for both models — the driver model wins on supply and generation; both struggle on clean generation because solar/wind arrived faster than any pre-2020 relationship predicted. |

Sidebar: **Scenarios to show** (Low/Base/High) and **Forecast up to** (2026–2035),
plus the shared unit selectors. There are no fitting knobs — the method is fixed
so the question always gets one answer.

---

## 4. Data

| Table | Used for | Reported |
|---|---|---|
| `fact_primary_energy_supply` + `dim_energy_source` | supply by source, total, imports (TOE) | 1999–2024 |
| `fact_renewable_energy` | generation by technology (GWh) | 2000–2024 |
| `fact_elec_generation` | total generation cross-check (GWh) | 2000–2024 |
| `fact_economic_indicators` | GDP growth, population | 2000–2024 |

Base units TOE · GWh · USD. Reported years draw solid, projected years dashed;
unreported years print nothing.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/supply_forecast.py`](../../core/supply_forecast.py) | fits, scenarios, mix, adequacy, imports, backtest |
| Charts | `charts.py` | the six Plotly visuals |
| Page | `page.py` | sidebar, KPI cards, layout |
| Verify | [`scripts/verify_supply_forecast.py`](../../scripts/verify_supply_forecast.py) | prints every figure from live MySQL |

Known limits: supply grows from one fitted relationship (no plant-level build
schedule exists in the warehouse); the demand line is a 4.8%/yr reference, not a
forecast; the post-2024 import share is a stated path.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
