# Q10 — Optimal Resource Allocation

**Question:** *What is optimal resource allocation for sustainable development?*

The page splits the horizon year's power need across the seven resources
Pakistan can actually use — hydro, solar, wind, other renewables, nuclear, coal,
gas — so that a three-pillar sustainability score is maximised within each
resource's physical ceiling. Every number is shown against the **2024 mix doing
the same job**.

```
the plan = the power that has to be supplied, given to the best-scoring
           resources first, up to what each one can physically produce
```

No solver, no optimiser library: a transparent, reproducible water-filling rule.
Check it headless: `.venv\Scripts\python.exe scripts\verify_q10_allocation.py`

---

## 1. Algorithms & formulas (base units GWh · US$ · t · BCF)

| Step | Formula / rule |
|---|---|
| **Demand** | `need = base-year generation × (1 + growth)^years` — base 2024 (175,440 GWh), growth from the sidebar (default 4.5%/yr). Unreported years print no reading, never a carried or zero-filled value. |
| **Profiles** | Per resource: buying cost US$/MWh from the Q7 anchors (`core/cost_forecast.unit_cost`), cradle-to-grave CO₂ t/MWh (IPCC AR5 medians: coal 0.90, gas 0.44, solar 0.041, other RE 0.030, hydro 0.024, nuclear 0.012, wind 0.011 — replaced by `dim_emission_factor` when names match), import dependence of the fuel chain (nuclear 0.35, coal 0.97, gas 0.50, clean 0), capacity factor. |
| **Utility score** | Cost, CO₂ and import dependence are min-max stretched to 0–1 across the seven resources, then `utility = w_cost·(1 − costₙ) + w_carbon·(1 − CO₂ₙ) + w_security·(1 − importₙ)` with the pick's weights normalised to sum to 1. |
| **Water-filling split** | `share ∝ utility^3.0` (pressure 3.0 concentrates the need on the best scorers). Any resource pushed over its ceiling is clamped to it and the remainder is re-spread over the still-free pool, repeatedly. What still cannot be served is reported honestly as "Left unserved". |
| **Ceilings** | Each resource may stretch a documented multiple of its best reported year: Hydro 1.30×, Solar 6.00×, Wind 4.00×, Other RE 2.50×, Nuclear 2.20×, Coal 1.80×. Gas has one hard physical cap: `max(domestic BCF × 150 GWh/BCF, best year × 1.25)`. |
| **BAU comparison** | The same need allocated in the proportions the record shows for 2024 — every figure on the page has a "same energy, old mix" partner. |
| **Priority sweep** | Cost and carbon weights traded from all-cost to all-carbon in 21 steps — the source of V2 and the Pareto shape in V5. |
| **The six scores** | `Cheaper power = 1 − (US$/MWh ÷ 80)` · `Lower CO₂ = 1 − (t/MWh ÷ 0.90)` · `Fuel from home = 100 − import share` · `Source spread = (1 − HHI) × 100` · `Clean share = clean% ÷ 60% benchmark` · `Demand served = coverage%`. Fixed references keep both mixes on one scale. |

### Picks (weights: cost / carbon / security)

Balanced **35/40/25** (default) · Cheapest power 70/15/15 · Lowest CO₂ 15/60/25 ·
Least fuel bought abroad 20/20/60.

---

## 2. KPI cards

| Card | Big number | Detail rows |
|---|---|---|
| **K1 — Power that has to be supplied** | horizon-year need in GWh | what 2024 actually made · the growth rate used · how much is left unserved |
| **K2 — What the plan costs a year** | plan's yearly buying cost, US$ | same energy on the 2024 mix · % change · CO₂ for both |
| **K3 — How clean, how sure of fuel** | clean share of the plan % | the 2024 mix's clean share · fuel bought from abroad · how many resources sit at their ceiling |

Default view (Balanced, 4.5%/yr, 2035): K1 = 284,713 GWh (1.6× 2024's 175,440,
0 unserved) · K2 = 13.64 US$ bn vs 19.24 on the old mix (−29.1%), CO₂ 24.2 Mt vs
76.6 Mt · K3 = 68.2% clean vs 41.0%, imports 13.6% vs 34.7%, 5 of 7 at limit.

Key finding: **all four picks land on the same 68.2% clean share** — the
ceilings, not the preference, set the clean level. The pick only moves cost and
CO₂.

---

## 3. Visuals

Two rows of two — **V1 | V2**, **V3 | V4** — then V5 wide and the plan table.

| # | Chart | How it is drawn |
|---|---|---|
| **V1** | How the power is split | Bars per resource: the plan in front, the 2024 mix behind it; the ceiling is in the hover. |
| **V2** | What the priorities buy | The sweep run from cheapest-first to cleanest-first with cost and CO₂ as two lines; a dotted mark shows the reader's pick. |
| **V3** | What moves, source by source | Plan − 2024 mix per resource; green grows a source, red pulls one back. |
| **V4** | Is the plan more sustainable? | The six scores, 0–100, one bar pair each: the 2024 mix vs the plan. |
| **V5** | The cost–CO₂ trade-off shape | Every plan the sweep can build, one dot per priority, cost against CO₂ — the knee shows where going cleaner stops costing more. |
| **—** | The plan, resource by resource | Table: plan, 2024 mix, change, most possible, cost, CO₂, at-limit flag. |

Sidebar: **What the plan should favour** (four named picks), **How fast demand
grows** (slider), **Plan up to** (stops at 2035 — further just extends an
exponential past what the record supports). No weight sliders, no solver knobs:
pressure stays 3.0 and fuel drift mirrors Q7's 3%/yr.

---

## 4. Data

| Query | Table | Used for |
|---|---|---|
| `Q_RENEWABLE_ENERGY` | `fact_renewable_energy` | 2024 generation by resource, build-out ceilings |
| `Q_NATURAL_GAS` | `fact_natural_gas` | domestic gas production → the gas ceiling |
| `Q_EMISSION_FACTORS` | `dim_emission_factor` | CO₂ intensity overrides |

Cost anchors are shared with [Q7](../q7_forecast_cost/README.md); the four
pillars a strategy is worth are [Q8](../q8_sustainable_strategy/README.md)'s page.

---

## 5. Files

| Layer | File | Role |
|---|---|---|
| Engine | [`core/resource_allocation.py`](../../core/resource_allocation.py) | profiles, utility, water-filling, sweep, six-way score |
| Charts | `charts.py` | the five Plotly visuals (values pre-computed by the engine) |
| Page | `page.py` | three controls, three cards, chart rows, the table |
| Config | `config.py` | the four picks, slider ranges, plain words, palette |
| Verify | [`scripts/verify_q10_allocation.py`](../../scripts/verify_q10_allocation.py) | engine against MySQL with sanity checks |

Honest limits: this is a planning shape, not a dispatch schedule (no storage,
grid geography or ramping); 5 of 7 resources sit pinned at their ceiling in the
default view; source spread *drops* (79.3 → 73.8) as concentrating the need is
what makes the plan cheaper and cleaner; CO₂ prints in tonnes by deck default
and follows the Emission slicer.

See [UNIT_GUIDE.md](../../UNIT_GUIDE.md).
