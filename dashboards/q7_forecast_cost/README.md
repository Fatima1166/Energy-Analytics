# Q7 — Forecasted Producer Cost

**Question:** *What is the forecasted cost of energy power producers?*

The page prices the electricity that is bought from power producers: what the
reported years cost, what the outlook says the bill will be, which source the
extra money goes to, and which assumption could move that answer most.

Everything is worked out the same way, for every year on the page:

```
bill for the year = Σ  electricity bought from each source × the purchase price of that source
```

---

## 1. How the question is answered

| Part of the question | What the dashboard does |
|---|---|
| "cost" | A bill in constant US$, built source by source, and a price for one unit that strips the growth in electricity out of it |
| "energy power producers" | Six sources are priced: hydro, solar, wind, nuclear, coal and gas |
| "forecasted" | One path per build-out case from 2025 to the year asked for, a fuel-price band around it, and a check of how far the model was off on years it had not been shown |
| "compared to what" | Against the bill for the years already reported, and against the price per unit in that year |

Where the electricity comes from is [Q5](../q5_forecast_supply/README.md)'s page,
how well the chains are used is [Q6](../q6_supply_chain_optimization/README.md)'s,
and what a strategy would be worth is [Q8](../q8_sustainable_strategy/README.md)'s.
This page only answers the money question.

---

## 2. The three KPI cards

| Code | Card | What it says |
|---|---|---|
| **K1** | What buying electricity cost | The bill for the last reported year, the average price paid for a unit, how much electricity was bought, and the fuel part of the bill |
| **K2** | The bill it points to | The bill at the year asked for, which build-out case it belongs to, how fast it grows a year, and how much bigger it is than the reported bill |
| **K3** | What one unit costs | The price of one unit at the same year, the price it is changing from, and the clean share of the mix behind it |

**Default view** (all three cases shown, outlook to 2035, USD bn):

| Card | Reading | Behind it |
|---|---|---|
| K1 | **8.21** for 2024 | 154,480 GWh bought at an average 53.1 US$ per unit; 56.5% of the bill is fuel |
| K2 | **24.01** for 2035, planned build-out | grows 10.3% a year, 15.80 more than 2024 |
| K3 | **62.2** US$ per unit for 2035 | up 9.1 from 2024, with clean sources at 46% of the mix |

The bill by source in 2024, and what each one adds by 2035 under the planned
build-out (US$ bn):

| Source | 2024 | 2035 | Change |
|---|---|---|---|
| Gas | 3.30 | 8.24 | +4.95 |
| Coal | 1.34 | 5.76 | +4.42 |
| Nuclear | 1.37 | 4.26 | +2.89 |
| Hydro | 1.22 | 3.68 | +2.45 |
| Solar | 0.75 | 1.54 | +0.78 |
| Wind | 0.22 | 0.52 | +0.31 |

The three build-out cases at 2035: Little clean power **24.88** (64.5 US$ per
unit, 42% clean), planned build-out **24.01** (62.2, 46%), half clean power
**23.05** (59.7, 50%).

---

## 3. Layout

### 3.1 Visuals

| # | Chart | What it shows |
|---|---|---|
| V1 | **What producers were paid** | The yearly bill stacked by source, then the average price paid and the fuel part of the bill |
| V2 | **The bill from here on** | The reported bill, then one path per build-out case, with the band between the dearest and cheapest case |
| V3 | **Where the extra money goes** | A step-by-step walk from the reported bill to the planned one, one step per source, biggest addition first |
| V4 | **What one unit costs** | The price of a unit, reported then one path per case |
| V5 | **How sure is this bill?** | The bill re-priced with fuel costs rising slower and faster, beside how far each growth model was off on years it had not been shown |

Each visual carries one short caption line (under ~120 characters) that only says
where to look. Method detail, disclosures and the price anchors live here in the
README, not on the page.

Things that were cut, and why:

* **Multi-sentence captions under every chart** — five of them ran to 45-55 words
  each and repeated what the legend and axes already said. They are now one short
  line apiece, and the readings that were dropped from them are in section 4.
* **The "Cumulative Cost Avoided" card and chart** — what a cleaner pathway
  *saves* is Question 8's strategy answer. Question 7 asks what producers cost.
* **The purchase-tariff heat-map** — it redrew the prices that were put *into*
  the model. An assumption restated is not an answer, and V1's price line already
  carries the prices that were actually paid out.
* **The cost-model hold-out table** — the same two numbers as the bars in V5.
* **The fourth KPI card** — it held the avoided-cost figure and the fuel-exposure
  range, and both are on the page properly now (K2's case line and V5).
* **The "Objective 1 … Objective 5" badges** — they labelled sections with a
  numbering scheme that appears nowhere else. Year ranges and case names say more
  in fewer words.
* **A priced slice for "Other RE"** — the record holds no generation for it in any
  year (`gen_other_renewables_gwh` is empty everywhere), so the engine no longer
  invents one and the page no longer draws a legend entry that is always zero.

### 3.2 Sidebar

Two controls, plus the shared Unit Selection.

| Control | Range | Effect |
|---|---|---|
| **Build-out cases to show** | Little clean power / The planned build-out / Half clean power | Which paths V2 and V4 draw, which case K2 and K3 read, and which case V3 walks |
| **Forecast up to** | 2026 – 2035 | The year the outlook is read at |
| **Unit Selection** | Cost (USD bn / USD mn / USD) | Re-renders every axis, hover and card |

What used to be here and is gone: fuel price escalation %/yr, the sensitivity
band ±pp, and an "Advanced Model Settings" expander holding the calibration start
and base GDP growth. Those four are settings of the model rather than choices in
the question, so the page states the model's own values instead of letting them
be moved: fuel costs rise 3% a year, tested at 1% and 5%, and the growth fit runs
on the reported years up to 2024.

---

## 4. Method

### 4.1 The bill

`bill = Σ electricity(1,000 MWh blocks) × price(source, year)` in constant US$.
Only the electricity is reported. The warehouse holds no producer invoices, so
the money side is built from a stated price per source, anchored on 2024 and run
backwards for earlier years and forwards for the outlook. The 2024 average of
53.1 US$ per unit is therefore the reported mix against those anchors, not a
figure read from accounts.

### 4.2 The price of each source

| Source | 2024 anchor (US$/MWh) | Yearly drift |
|---|---|---|
| Hydro | 32.0 | +1.5% |
| Solar | 38.0 | −4.0% |
| Wind | 42.0 | −2.5% |
| Nuclear | 60.0 | +2.0% |
| Coal | 55.0 | fuel escalation × 1.00 |
| Gas | 75.0 | fuel escalation × 1.15 |

Clean plant that learns gets a fixed yearly drift (solar and wind fall, firm
clean plant drifts with upkeep). Coal and gas have no drift of their own: their
purchase price moves with the fuel-cost escalation, gas a little more than coal
because its contract is the more exposed one. No price falls below 15 US$/MWh.
At the stated 3% fuel escalation, coal's purchase price grows 3.0% a year and
gas's 3.45%, while solar gives way 4% a year — which is why the mix matters more
every year the outlook runs.

### 4.3 The three build-out cases

All three buy the **same amount of electricity** on one shared growth path. Only
the mix differs, so the gap between the paths is the cost of the mix and nothing
else. Each case glides from 2024's shares to its own target in equal steps:

| Case | Clean share at 2035 | Solar+wind within clean | Nuclear shift | Coal part of thermal |
|---|---|---|---|---|
| Little clean power (Minimum RE) | 42% (2024 + 1 pp) | 25% | none | 58% |
| The planned build-out (Reference) | 46% (2024 + 5 pp) | 45% | none | 50% |
| Half clean power (RE 50%) | 50% (fixed target) | 62% | −2 pp | 45% |

The clean remainder after solar and wind goes to hydro, and nothing is charged to
"Other RE". Because the three land within a few points of each other on the clean
share, the paths end close together — see §6.

### 4.4 The fuel band (V5, left)

The planned build-out is priced three times with fuel escalation at 1%, 3% and 5%
a year. At 2035 that gives **21.08 / 24.01 / 27.62** US$ bn — a spread of 6.5 bn
around the middle path.

### 4.5 How far the model misses (V5, right)

The bill is fitted on years up to 2020 only, then asked to predict 2021–2024, and
compared with what those years actually cost. Two growth stories are tried: one
tied to GDP growth, one carried on from past growth. Average error:
**6.7%** (GDP-linked) and **11.7%** (past-trend). Both were too high, by the same
amounts, so the outlook on this page is likelier to over-state the bill than to
under-state it.

---

## 5. Data

| Table | Used for | Units |
|---|---|---|
| `fact_renewable_energy` | Electricity made by each source per year, and the total bill is built from those same sources | GWh |
| `fact_economic_indicators` | GDP and population path behind the growth in electricity | USD / persons |

Two reads, both of which the engine needs: the sources that are priced, and the
economy that grows them. Base unit for money is USD, converted for display by
[`core/units.py`](../../core/units.py).

What the record actually holds, source by source:

| Column | Years with something in it |
|---|---|
| `gen_hydro_gwh`, `gen_coal_gwh`, `gen_gas_gwh`, `gen_nuclear_gwh` | 2000–2024 |
| `gen_wind_gwh` | 2009–2024 |
| `gen_solar_gwh` | 2010–2024 |
| `gen_other_renewables_gwh` | never reported |

1999 reports no source at all, so the engine's priced history starts at 2000 and
no year is filled in with an estimate. A source with no reading for a year simply
scores nothing there — the charts break the line and the cards name the year the
value actually came from.

---

## 6. Known limitations

* **The money side is assumed, not invoiced.** Only the electricity is reported;
  the price per source is a stated anchor (§4.1). Changing the anchors moves every
  number on the page together, and moves nothing *between* the years.
* **The choice of build-out case barely moves the bill** — 23.05 to 24.88 US$ bn at
  2035, 1.8 bn apart — **while the fuel assumption moves it 6.5 bn.** V5 should be
  read before V2, or the case lines will look like more of an answer than they are.
* **Both growth models over-predicted** the four years they were tested on, so the
  forecast side of the page is a high-side estimate rather than a central one.
* **Constant dollars throughout.** No general price inflation is applied to the
  bill; the only price drift is per source (§4.2). A fuel-spike year, a contract
  renegotiation or a capacity payment change is not modelled.
* **Producer purchase cost only.** Grid losses, distribution, taxes and consumer
  tariffs are outside this question — the loss part of the chain is Q6's.
* **Clean shares are targets, not plans.** A case says what share of electricity
  should come from clean sources by the horizon year; it does not say which
  plants get built, when, or what they cost to connect.

---

## 7. Files

| File | Purpose |
|---|---|
| `page.py` | Sidebar, the three cards, layout, the walk in V3 |
| `charts.py` | The five Plotly figures |
| `config.py` | Case names in plain words, the sources drawn, the palette |
| `README.md` | This document |

The maths lives in [`core/cost_forecast.py`](../../core/cost_forecast.py) (shared
with Q10's allocation model, which is why the engine still carries an "Other RE"
entry it never prices).

Check it:

```
.venv\Scripts\python.exe scripts\verify_q7_cost.py   # engine against MySQL, with sanity checks
.venv\Scripts\python.exe scripts\audit_axes.py       # prints every Q7 axis title
.venv\Scripts\python.exe scripts\smoke_test_app.py   # headless render of all dashboards
```
