# Q9 — Operational Bottlenecks in Fossil & Renewable Energy Supplies

**Question:** *What are the operational bottlenecks in fossil and renewable energy supplies?*

A diagnostic page that measures how much of the plant that exists actually gets
made, ranks every choke point as a **0–100 severity**, and splits them into three
families — **fossil supply**, **renewable supply** and **grid delivery**.
Three cards and four charts in two rows; nothing else.

---

## 1. Architecture — engine / presentation split

Q9 follows the Q8 pattern: **zero analytics inside `page.py`**. All maths live in
a pure pandas/numpy engine.

```
core/operational_bottlenecks.py        ← ALL analytics (pure pandas/numpy)
   build_bottleneck_frame()            per-year utilisation / supply-gap / loss metrics
   score_bottlenecks()                 ranked 0-100 severity scorecard at a base year
   latest_obs()                        newest year each measure has data for
   aggregate_by_family()               mean severity per family (kept for the verifier)
   snapshot_metrics()                  headline values, each from its own year
          ▲
dashboards/q9_operational_bottlenecks/ ← presentation only
   config.py   families, chart series labels, benchmark, palette (data, not logic)
   charts.py   four Plotly visuals (render engine frames, compute nothing)
   page.py     one sidebar slider + three cards + two chart rows (thin shell)
scripts/verify_q9_bottlenecks.py       headless end-to-end test of the engine
```

## 2. What counts as an "operational bottleneck"

A bottleneck is any constraint that stops **what plant could make** from becoming
**energy that is actually made**. Each is put on a severity (higher = more
binding) using its own reference band, never one shared 0–100 assumption:

| Family | Bottleneck | Underlying metric | Band (worst → best) |
|---|---|---|---|
| **Fossil supply** | Fossil plant sits idle | coal/gas/nuclear capacity factor | 15% → 80% |
| **Fossil supply** | Not enough home gas | gas made at home ÷ gas used | 20% → 100% |
| **Fossil supply** | Fuel bought from abroad | imported ÷ total fossil supply (TOE) | 90% → 10% |
| **Renewable supply** | Clean plant under-used | blended renewable capacity factor | 8% → 55% |
| **Renewable supply** | Solar is day-only | solar capacity factor | 6% → 30% |
| **Renewable supply** | Wind comes and goes | wind capacity factor | 10% → 45% |
| **Renewable supply** | Hydro needs water | hydro capacity factor | 15% → 55% |
| **Grid delivery** | Power lost in delivery | T&D losses ÷ generation | 25% → 8% |

## 3. Layout

### 3.1 Visuals

| # | Chart | What it decides |
|---|---|---|
| V1 | **Which choke point hurts most** | Every bottleneck ranked 0–100 — the direct answer to the question |
| V2 | **How long plant has sat idle** | Fossil, hydro, wind, solar and blended renewable utilisation, year by year |
| V3 | **The power that never came out** | What all the plant could make in a year against what it made |
| V4 | **The gas shortfall** | Gas used against gas made at home; the shaded gap has to be bought |

K1 (whole-system utilisation), K2 (fossil plant, home gas, bought fuel) and
K3 (renewable plant, its output, its weakest source) sit above the charts in
three of four card slots, so each card keeps a four-up row's width. V1 and V2
share the first row and V3 and V4 the second, with captions of similar length so
the chart tops line up. Because the row is half width, V1's plain-language names
were shortened to fit a 142px left margin and the shared chart skin now uses
tighter side margins and a 9.5pt legend.

Things that were cut, and why:

* **Four of the eight visuals** — the T&D loss line and the renewable
  capacity-versus-output panel (both already live on Q6 Supply Chain
  Optimization, which owns grid losses and clean-plant conversion), the family
  severity average (the mean of bars V1 already ranks), and the source bubble
  map (the same capacity-factor facts as V2, in a harder language).
* **The answer hero and the three findings cards** — prose restatements of the
  tallest bar in V1.
* **Two of the five KPI cards** — gas self-sufficiency became a row on the
  fossil card and T&D losses left the page with their chart; they are still
  scored in V1.
* **The family and severity filters** — the scorecard is already ranked, so a
  threshold only hides rows the order makes obvious, and the family picker
  affected two of the eight visuals and none of the cards.

### 3.2 What the live record says (read up to 2024)

| Bottleneck | Severity | Reading |
|---|---|---|
| Fossil plant sits idle | 60 | 40.8 % capacity factor (2018) |
| Power lost in delivery | 58 | 17.9 % of generation (2019) |
| Hydro needs water | 58 | 32.0 % capacity factor (2018) |
| Clean plant under-used | 54 | 29.8 % capacity factor (2018) |
| Wind comes and goes | 46 | 29.0 % capacity factor (2018) |
| Solar is day-only | 38 | 20.8 % capacity factor (2018) |
| Fuel bought from abroad | 3 | 12.1 % of fossil supply (2018) |
| Not enough home gas | 1 | 98.8 % met at home (2018) |

So the binding constraints are **utilisation, not shortage of fuel**: fossil
plant and clean plant both run far below their size, and about 18% of everything
generated never reaches a consumer. Home gas and imported fuel are *not* binding
on this record — an earlier version of this page claimed the gas shortfall was
the tightest bottleneck, and the numbers do not support that.

## 4. Reading the years honestly

Every stream is reported through a different last year: utilisation, gas and
import figures stop in **2018**, T&D losses in **2019**, installed capacity and
generation in **2023**. "Year to judge" therefore means *nothing later than this
year*; each measure then uses the newest year it has. V1 prints the year of every
reading in its hover, and every card prints the year of its own headline number,
so no figure on this page pretends to be a single 2024 snapshot.

## 5. Sidebar controls

1. **Year to judge** — 2008 to 2024, the year the scorecard is read as at.
2. **Global unit slicers** — electricity (GWh), power (MW), gas (BCF). V3 follows
   electricity, V4 follows gas, and the MW / GWh rows on the cards follow power
   and electricity. The percentages and the severity scores are ratios, so they
   never move.

## 6. Key formulas (base units)

- Nameplate energy (GWh) = installed MW × **8.76**  (8760 h / 1000)
- Capacity factor % = generation ÷ nameplate energy × 100
- Gas self-sufficiency % = production ÷ consumption × 100
- Fossil import dependence % = Σ imports ÷ Σ supply over oil/gas/LNG/LPG/coal
- T&D loss rate % = T&D losses ÷ generation × 100
- Severity (higher-is-better metric) = clamp((worst − value) / (worst − best) × 100)
- Severity (lower-is-better metric) = clamp((value − best) / (worst − best) × 100)
