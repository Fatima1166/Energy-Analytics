# Q4 — Energy Demand Forecast

**Question:** *What will Pakistan's energy demand look like in the coming years?*

The engine fits how demand has responded to the economy in the past, then walks
that relationship forward under three GDP paths. Everything before 2025 is
reported data; everything after is a modelled path, drawn dashed.

---

## 1. Algorithms & formulas

| Step | Formula / rule |
|---|---|
| **Real GDP rebuild** | Current-USD GDP moves with the exchange rate (the rupee slide made USD GDP *fall* 9.9% in 2019 while the real economy grew). So real GDP is chained from growth: `index_t = index_(t−1) × (1 + g_t)`. |
| **Income elasticity fit** | Log-log OLS per series: `ln(demand / population) = b0 + ε · ln(income per head) + b2 · D`, where `D` is the 2019 basis dummy. ε is the income elasticity — how many % demand moves when income per head moves 1%. |
| **Projection** | Population enters with coefficient 1 (people consume): `g_demand = g_pop + ε · (g_GDP − g_pop) + residual drag`. |
| **2019 break detection** | The final-energy table jumps 53% between 2018 and 2019 — a reporting-basis change, not demand. Found automatically (largest log jump ≥ 20% and ≥ 2.5× the typical year), handled with a level dummy plus measuring drift only after the jump. |
| **Residual decay** | The leftover post-2019 drift fades **linearly to zero** by the horizon, so a one-off contraction is not compounded for eleven years. |
| **Clamps** | Growth clamped to −8%…+14%/yr; ε clamped to −0.6…+2.5 (gas genuinely moves against income here, so the negative floor is deliberate). |
| **Three scenarios** | Low / Base / High GDP growth, spread **±1.5 pp** around the recent actual GDP growth. Each series is projected under all three. |
| **Sector shares** | Residential / industrial / commercial / agriculture shares drift at their fitted log rate, clamped to ±3%/yr, then renormalised to sum to 100%. |
| **Backtest** | Refit using only years ≤ 2020, predict 2021–2024, and score against what was actually reported — this is what "how far to trust the forecast" is built from. |

Fitted elasticities (2012–2024): total final energy ε ≈ 1.04, electricity
ε ≈ 1.32, grid demand ε ≈ 1.39, gas ε = −0.6 (clamped). Population growth over
the window ≈ +1.58%/yr.

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Total energy demand** | latest-year total final demand (model anchored on reported data) | `By <horizon>` value · `Change = (horizon / now − 1) × 100` % · which scenario is shown |
| **K2 — Electricity demand** | latest-year grid electricity demand | same horizon value + % change · badge shows its own yearly growth rate |
| **K3 — How fast demand grows** | forecast CAGR, `% a year` | observed CAGR seen in history · the calibration years fitted on · years ahead |

All three follow the scenario checkboxes and horizon slider in the sidebar.

---

## 3. Visuals

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Demand so far | Reported history of total demand and electricity demand as solid lines; unreported years leave a gap, never a zero. |
| **V2** | Three ways demand can go | The modelled path under Low / Base / High GDP scenarios, drawn dashed forward from the last reported year. |
| **V3** | Who uses the electricity | Sector consumption split (residential, industrial, commercial, agriculture) over the years, projected with the clamped share drift. |
| **V4** | How far to trust the forecast | Backtest bars: predicted vs actual for 2021–2024 from a model blind to those years — the closer the bars, the more trust the forward paths get. |

The income-per-head vs demand-per-head fit that drives the model is computed
inside the engine but no longer plotted — it was removed as too complex for
the page. The projection formulas above describe what that fit does.

---

## 4. Data

| Query | Table | Used for |
|---|---|---|
| `Q_FINAL_ENERGY_BY_SOURCE` | `fact_final_energy_consumption` | total final demand history |
| `Q_ECONOMIC` | `fact_economic_indicators` | GDP growth, population, income per head |
| `Q_RENEWABLE_ENERGY` / `Q_ELEC_GEN` | generation facts | electricity demand context |
| `Q_ELEC_SECTOR_CONSUMPTION` | `fact_elec_sector_consumption` | sector shares (V3) |

Base units TOE · GWh · USD; display conversion via the sidebar unit slicer.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/demand_forecast.py`](../../core/demand_forecast.py) | elasticity fits, break detection, scenarios, backtest |
| Charts | `charts.py` | the four Plotly visuals |
| Page | `page.py` | sidebar (scenarios, horizon), KPI cards, layout |
| Verify | [`scripts/verify_demand_forecast.py`](../../scripts/verify_demand_forecast.py) | standalone MySQL audit of the engine |

Known limit: pre- and post-2019 final-energy levels are not on the same basis,
so levels across the break are indicative — the growth rates are the robust part.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
