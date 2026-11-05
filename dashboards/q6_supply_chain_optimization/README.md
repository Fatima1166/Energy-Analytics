# Q6 — Supply Chain Optimization

**Question:** *What is the optimal utilization of fuel and renewable energy supply chains?*

The page scores four things supply chains actually lose or waste, year by year,
and adds them into one overall score under the strategy you pick. Nothing here
is a forecast — every number is a reported year judged against a stated bar.

---

## 1. Algorithms & formulas

### The four scored parts (each 0–100, capped at 100)

| Part | Formula | Bar |
|---|---|---|
| Electricity that arrives | `arrived% / (100 − loss aim) × 100` | loss aim from the strategy (default 15%) |
| Clean plant used well | `used% / 75 × 100` | 75% of year-round potential |
| Less bought from abroad | `(30 − import share%) / 30 × 100 + 50` | ≤ 30% of supply imported |
| Gas made at home | `met% / 70 × 100` | 70% of gas demand met domestically |

`used%` (capacity factor) = `generation_GWh / (capacity_MW × 8760 / 1000)` —
what the plant made versus what it could make running every hour. Real sun and
wind give 25–35%, so 75% is a stretch bar, not a physical one.

### The overall score

Weighted average of the parts under the chosen strategy:

| Strategy | Grid | Clean plant | Imports | Gas |
|---|---|---|---|---|
| All four parts equally | .25 | .25 | .25 | .25 |
| More clean energy | .25 | .40 | .20 | .15 |
| Much more clean energy | .20 | .50 | .20 | .10 |
| Buy less from abroad | .15 | .15 | .40 | .30 |
| Fix grid losses first | .50 | .15 | .20 | .15 |

Bands: **≥ 75** = working well · **50–75** = room to improve · **< 50** = needs work.

### Missing reports are blank, not zero

Each data column stops reporting in its own year (T&D losses 2019, imports and
gas 2018, generation 2023, renewables 2024). A year with no report scores
**nothing** for that part — neither a fake 100 nor a hard 0 — and the overall
score averages only the reported parts. K1 prints how many parts it used, so a
falling score can be recognised as the record thinning out, not a collapse.

### Target mix (V5)

Nuclear keeps its reported share; the clean/fuel target splits everything else
in proportion (default 40% clean / 60% fuel of the non-nuclear part).

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Chain utilization score** | overall score `/100` for the latest year with a record | which part the strategy counts hardest · how many of the 4 parts the score was built from |
| **K2 — Electricity that reached people** | `arrived% = (generated − losses) / generated × 100` | energy generated · energy lost · the loss aim and % of aim reached |
| **K3 — Clean plant made vs could make** | capacity factor `used%` | generation (GWh) and plant size (MW) behind it · potential · % of aim reached |

Each card prints the year its own number came from, never another metric's year.

---

## 3. Visuals

Row order: **V1 | V4** on top, then **V2 | V3**, then V5 full width.

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | The score, year by year | Thick line = overall score; thin lines = its four parts; reference marks at 75 and 50. Legend sits beside the plot. |
| **V2** | Electricity lost on the wires | Bars for electricity made and lost, with the arrived-% line against the loss aim. |
| **V3** | Clean plant built and what it made | Capacity (MW) and generation (GWh), plus the share of year-round potential achieved. |
| **V4** | The gas chain | Gas made at home, gas used, gas bought by ship, and the share met domestically against the 70% bar. |
| **V5** | Now vs target mix | The latest year's mix by source, side by side with the same year reshuffled to meet the clean/fuel targets. |

Sidebar: **Which part counts most** (the five strategies) and **Years to judge**
(1999–2024), plus the shared unit selectors. No free sliders — each strategy
carries its own targets so one question gets one answer.

---

## 4. Data

| Table | Used for | Units |
|---|---|---|
| `fact_elec_generation` | electricity made | GWh |
| `fact_td_losses` | electricity lost on the wires | GWh |
| `fact_renewable_energy` | clean plant capacity & generation | MW / GWh |
| `fact_primary_energy_supply` + `dim_energy_source` | supply at home vs bought abroad | TOE |
| `fact_natural_gas` | gas made and used | BCF |
| `fact_lng_imports` | gas bought by ship | BCF |

Base units GWh · MW · BCF · TOE. `gen_other_renewables_gwh` is empty in every
row, so "clean" here means hydro + solar + wind.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Charts | `charts.py` | the five Plotly visuals |
| Page | `page.py` | sidebar, four-part score, KPI cards, layout |
| Config | `config.py` | bars, strategies & weights, palette |
| SQL | [`core/queries.py`](../../core/queries.py) | the warehouse queries |

Known limits: imports (0–9.7%) and gas-at-home (99–122%) sit at their ceiling in
every computable year, so the score's shape comes from clean-plant use and grid
losses; the target mix is a reshuffle of one year, not a build plan; the warehouse
holds no split between transmission and distribution losses.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
