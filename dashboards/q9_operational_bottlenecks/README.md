# Q9 — Operational Bottlenecks

**Question:** *What are the operational bottlenecks in fossil and renewable energy supplies?*

A diagnostic page. An *operational bottleneck* is anything that stops installed
plant from becoming delivered energy. The page measures how much of the plant
that exists actually gets made, ranks every choke point as a **0–100 severity**,
and groups them into three families — **fossil supply**, **renewable supply** and
**grid delivery**. Three cards and four charts; nothing else.

Check the engine headless: `.venv\Scripts\python.exe scripts\verify_q9_bottlenecks.py`

---

## 1. Algorithms & formulas (base units)

| Formula | Rule |
|---|---|
| **Nameplate energy** | `GWh_available = installed_MW × 8.76` (8760 hours ÷ 1000) |
| **Capacity factor %** | `generation_GWh / nameplate_GWh × 100` |
| **Gas self-sufficiency %** | `production_BCF / consumption_BCF × 100` |
| **Fossil import dependence %** | `Σ imports / Σ supply × 100` over oil, gas, LNG, LPG, coal |
| **T&D loss rate %** | `td_losses_GWh / generation_GWh × 100` |
| **Severity, higher-is-better** | `clamp((worst − value) / (worst − best) × 100)` |
| **Severity, lower-is-better** | `clamp((value − best) / (worst − best) × 100)` |

Each bottleneck is normalised on **its own reference band** (worst → best), never
a shared assumption. A missing denominator yields NaN, never a silent 0. The
whole scorecard is judged at one base year so the ranking is internally consistent.

### The eight bottlenecks and their bands

| Family | Bottleneck | Metric | Band (worst → best) |
|---|---|---|---|
| Fossil supply | Fossil plant sits idle | coal/gas/nuclear capacity factor | 15% → 80% |
| Fossil supply | Not enough home gas | gas self-sufficiency | 20% → 100% |
| Fossil supply | Fuel bought from abroad | fossil import dependence | 90% → 10% |
| Renewable supply | Clean plant under-used | blended renewable capacity factor | 8% → 55% |
| Renewable supply | Solar is day-only | solar capacity factor | 6% → 30% |
| Renewable supply | Wind comes and goes | wind capacity factor | 10% → 45% |
| Renewable supply | Hydro needs water | hydro capacity factor | 15% → 55% |
| Grid delivery | Power lost in delivery | T&D loss rate | 25% → 8% |

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Whole-system utilisation** | system load factor `total generation / (total MW × 8.76) × 100` | undelivered energy = capability − actual generation |
| **K2 — Fossil side** | fossil plant capacity factor | home gas self-sufficiency · fuel bought from abroad, each from its own newest year |
| **K3 — Renewable side** | blended renewable capacity factor | renewable output · the weakest single source |

Every stream reports through a different last year (utilisation, gas and imports
stop in 2018, T&D losses in 2019, capacity & generation in 2023), so **each card
prints the year its own number came from** — no figure pretends to be one 2024
snapshot. The sidebar slider means *"no later than this year"*; each measure then
uses its newest reading at or before it.

What the live record says (read to 2024): the binding constraints are
**utilisation, not shortage** — fossil plant at ~40.8% CF (severity 60) and T&D
losses at 17.9% (severity 58) lead; home gas (98.8% met) and imported fuel
(12.1%) are not binding on this record.

---

## 3. Visuals

Two rows: **V1 | V2**, then **V3 | V4**.

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | Which choke point hurts most | All eight bottlenecks ranked as horizontal severity bars, 0–100, coloured by family — the direct answer to the question. Hover prints each reading's own year. |
| **V2** | How long plant has sat idle | Capacity factor year by year for fossil, hydro, wind, solar and blended renewables. |
| **V3** | The power that never came out | Nameplate capability (`MW × 8.76`) against actual generation, per year; the gap is undelivered energy. |
| **V4** | The gas shortfall | Gas used against gas made at home; the shaded gap has to be bought. |

Sidebar: one **Year to judge** slider (2008–2024) plus the shared unit slicers
(electricity GWh, power MW, gas BCF). Percentages and severities are ratios, so
unit changes never move them.

---

## 4. Data

| Query | Table | Used for |
|---|---|---|
| `Q_ELEC_GEN` | `fact_elec_generation` | installed MW, generation GWh |
| `Q_RENEWABLE_ENERGY` | `fact_renewable_energy` | generation by fuel |
| `Q_RENEWABLE_CAPACITY` | `fact_renewable_capacity` | renewable MW by source |
| `Q_TD_LOSSES` | `fact_td_losses` | T&D losses GWh |
| `Q_NATURAL_GAS` | `fact_natural_gas` | gas production / consumption BCF |
| `Q_PRIMARY_SUPPLY` | `fact_primary_energy_supply` | fossil supply & imports TOE |

Base units MW · GWh · TOE · BCF; display conversion at render time via `core.units`.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/operational_bottlenecks.py`](../../core/operational_bottlenecks.py) | all analytics — pure pandas/numpy, zero Streamlit |
| Charts | `charts.py` | four Plotly visuals (render frames, compute nothing) |
| Page | `page.py` | slider, three cards, two chart rows (thin shell) |
| Config | `config.py` | families, labels, band benchmark, palette |
| Verify | [`scripts/verify_q9_bottlenecks.py`](../../scripts/verify_q9_bottlenecks.py) | headless end-to-end engine test |

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
