# Home — Energy Overview (Landing Dashboard)

The front page of the platform. It shows a few headline national numbers, four
simple trend charts, and tiles that open any of the ten question dashboards.
It is the **first** entry in `dashboards/registry.py`, so it is the default view.

This page does no forecasting. Every number is a value the database actually
reported.

---

## 1. Algorithms & techniques

| Technique | What it does |
|---|---|
| **Latest-reported-value pick** | For each metric, take the newest year that has a real reading. Missing years are never filled, carried over, or read as zero. |
| **10-year delta** | Compare that latest value with the value from about ten years earlier, to show the direction of travel. |
| **Fuel-mix share** | For the latest year that reports source detail, split supply by source and turn it into percentages. |
| **Renewable share** | Renewables ÷ total generation, for the latest year that reports both. |
| **Carbon intensity** | CO₂ ÷ generation, but only when the two numbers are from the **same year**. |

All maths runs in database base units (TOE, GWh, tonnes). The sidebar unit
slicer only changes how a number is displayed.

---

## 2. KPI cards (National Energy Snapshot)

Four cards. Each one shows its **own latest year**, the value, a 10-year change,
and one short context note.

| Card | Value | Change formula | Context note |
|---|---|---|---|
| **[TPES] Primary Supply** | latest `total_primary_supply_toe` | `(now / 10y_ago − 1) × 100` | the two biggest sources in the latest mix, with their share |
| **[TFC] Final Consumption** | latest `total_final_consumption_toe` | same 10-year delta | `Losses% = (supply − use) / supply × 100` |
| **[GRID] Power Generation** | latest `generation_gwh` | same 10-year delta | `Clean% = renewable share of generation` |
| **[CO2] Annual Emissions** | latest `co2_emissions_t` | 10-year delta (up = bad, red) | `tCO₂ per GWh = co2 / generation` (same-year only) |

Rules that keep the cards honest:
- A card prints **"no reading"** when its metric has never reported — it does not
  borrow another metric's year or show a zero.
- The 10-year delta returns **"--"** when there is no value from ten years back.
- Carbon intensity only appears when emissions and generation share a year;
  otherwise the card says "no same-year emissions/power pair".

---

## 3. Visuals (25-Year Energy Trends)

Four charts, shown in tabs. Each is a plain history line — no model, no
projection.

| # | Chart | How it is drawn |
|---|---|---|
| **H1** | Supply vs Use | Two filled area lines: `total_primary_supply_toe` and `total_final_consumption_toe`. The gap between them is conversion, refining and grid losses. |
| **H2** | Fuel Mix (donut) | Latest-year supply by source, as `share_pct = source_toe / total × 100`. Slice colours are matched by source name. |
| **H3** | Emissions (bars) | One bar per reported year for `co2_emissions_t`; the latest year is highlighted in amber. |
| **H4** | Power Output (line) | Annual `generation_gwh` as a single filled line. |

Every chart breaks its line where a year was never reported, instead of drawing
a made-up zero.

---

## 4. Question hub & takeaways

- **Explore the 10 Dashboards** — tiles grouped into four topics (Supply &
  Demand, Clean Energy, Grid & Infrastructure, Cost & Dispatch). Each tile links
  with `?nav=<key>`; `app.py` reads it and switches the sidebar selector.
- **Key Takeaways** — four fixed summary cards written in plain English.

---

## 5. Data

| Query | Table | Used for |
|---|---|---|
| `Q_ENERGY_OVERVIEW` | `fact_energy_overview` | primary supply, final consumption |
| `Q_ELEC_GEN` | `fact_elec_generation` | power generation (GWh) |
| `Q_RENEWABLE_ENERGY` | `fact_renewable_energy` | generation by source → renewable share |
| `Q_PRIMARY_SUPPLY` | `fact_primary_energy_supply` | supply by source → fuel mix |
| `Q_ECONOMIC` | `fact_economic_indicators` | CO₂ fallback |
| `Q_CO2` | `fact_co2_emissions` | authoritative CO₂ series |

---

## 6. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/energy_overview.py`](../../core/energy_overview.py) | snapshot, histories, fuel mix, renewable share |
| Charts | `charts.py` | the four dumb visuals |
| Page | `page.py` | hero, KPI cards, chart tabs, tiles, takeaways |
| Config | `config.py` | hero copy and the fuel colour palette |

Base units TOE · GWh · t — see [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
