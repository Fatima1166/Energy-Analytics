# Q7 — Forecasted Producer Cost

**Question:** *What is the forecasted cost of energy power producers?*

The page prices the electricity bought from power producers: what the reported
years cost, what the outlook says the bill will be, which source the extra money
goes to, and which assumption moves the answer most. One rule runs through every
year on the page:

```
bill for the year = Σ (electricity bought from each source × that source's purchase price)
```

Check the engine against live MySQL any time:
```
.venv\Scripts\python.exe scripts\verify_q7_cost.py
```

---

## 1. Algorithms & formulas

| Step | Formula / rule |
|---|---|
| **The bill** | `bill = Σ GWh × 1000 × price(source, year)` in constant US$. Only electricity volumes are reported — there are no invoices in the warehouse — so the money side comes from stated price anchors. |
| **Price anchors (2024, US$/MWh)** | Hydro **32** · Solar **38** · Wind **42** · Nuclear **60** · Coal **55** · Gas **75**. Anchored on 2024, run backwards for history and forwards for the outlook. |
| **Yearly price drift** | Solar −4.0%, wind −2.5% (clean plant that learns), hydro +1.5%, nuclear +2.0% (upkeep). Coal and gas have no drift of their own: they move with the fuel escalation (3%/yr), gas at ×1.15 (3.45%/yr) and coal at ×1.00 (3.0%/yr) because the gas contract is the more exposed one. No price falls below **15 US$/MWh**. |
| **Three build-out cases** | All three buy the same electricity on one shared growth path — only the **mix** differs, so the gap between paths is the cost of the mix and nothing else. Each glides from 2024 shares to its 2035 target in equal steps. |
| **Fuel-price band** | The planned build-out is re-priced at 1%, 3% and 5% fuel escalation — a spread of about 6.5 US$ bn at 2035. |
| **Backtest** | Fit the bill on years ≤ 2020, predict 2021–2024, compare with what those years actually cost. GDP-linked growth missed by 6.7% on average, past-trend by 11.7% — both over-predicted. |

### The three cases at 2035

| Case | Clean share | Solar+wind within clean | Coal part of thermal |
|---|---|---|---|
| Little clean power (Minimum RE) | 42% | 25% | 58% |
| The planned build-out (Reference) | 46% | 45% | 50% |
| Half clean power (RE 50%) | 50% | 62% | 45% |

The clean remainder after solar and wind goes to hydro; nothing is charged to
"Other RE" (the record never reported it).

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — What buying electricity cost** | the bill for the last reported year | average price per unit · electricity bought · fuel share of the bill |
| **K2 — The bill it points to** | the bill at the horizon year | which build-out case · yearly growth % · gap over the reported bill |
| **K3 — What one unit costs** | US$/MWh at the horizon year | the price it grew from · clean share of the mix behind it |

Default view (outlook to 2035): K1 = 8.21 US$ bn for 2024 (154,480 GWh at an
average 53.1 US$/MWh, 56.5% of the bill is fuel) · K2 = 24.01 US$ bn, planned
build-out, growing 10.3%/yr · K3 = 62.2 US$/MWh with clean sources at 46%.

---

## 3. Visuals

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | What producers were paid | Yearly bill stacked by source, then the average price paid and the fuel share of the bill. |
| **V2** | The bill from here on | Reported bill solid, then one dashed path per build-out case, with the band between the dearest and cheapest case shaded. |
| **V3** | Where the extra money goes | Waterfall walk from the reported bill to the planned one, one step per source, biggest addition first. |
| **V4** | What one unit costs | Price per unit: reported history, then one path per case. |
| **V5** | How sure is this bill? | Left: the bill re-priced at 1/3/5% fuel escalation. Right: backtest error of the two growth models on years they had not been shown. |

Sidebar: **Build-out cases to show** and **Forecast up to** (2026–2035), plus the
shared unit selector. Model settings (3% fuel escalation, tested ±2 pp, fit to
2024) are stated, not adjustable — so one question always gets one answer.

---

## 4. Data

| Table | Used for | Units |
|---|---|---|
| `fact_renewable_energy` | electricity by source (the priced volumes) | GWh |
| `fact_economic_indicators` | GDP & population behind the growth path | USD / persons |

Priced history starts at 2000 (1999 reports no source at all); wind starts 2009,
solar 2010; `gen_other_renewables_gwh` is never reported, so it is priced at
nothing rather than invented. Missing years break the line, never show zero.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/cost_forecast.py`](../../core/cost_forecast.py) | price anchors, cases, bills, band, backtest (shared with Q10) |
| Charts | `charts.py` | the five Plotly visuals |
| Page | `page.py` | sidebar, KPI cards, layout |
| Config | `config.py` | case names in plain words, sources drawn, palette |
| Verify | [`scripts/verify_q7_cost.py`](../../scripts/verify_q7_cost.py) | engine audit against MySQL |

Known limits: the money side is assumed from anchors, not invoiced; the build-out
case moves the bill only ~1.8 US$ bn while the fuel assumption moves it 6.5 bn
(read V5 before V2); both growth models over-predict, so the outlook is a
high-side estimate; producer purchase cost only — losses, taxes and consumer
tariffs are Q6's territory.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
