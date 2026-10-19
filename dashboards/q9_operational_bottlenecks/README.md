# Q9 — Operational Bottlenecks in Fossil & Renewable Energy Supplies

**Question:** *What are the operational bottlenecks in fossil and renewable energy supplies?*

A diagnostic dashboard that measures how much of Pakistan's installed energy
capability actually becomes **delivered** energy, ranks every constraint as a
**0–100 severity bottleneck (2002–2024)**, and splits them into three families —
**fossil supply**, **renewable supply** and **grid delivery**.

---

## 1. Architecture — engine / presentation split

Q9 follows the Q8 pattern: **zero analytics inside `page.py`**. All maths live in
a pure pandas/numpy engine.

```
core/operational_bottlenecks.py        ← ALL analytics (pure pandas/numpy)
   build_bottleneck_frame()            per-year utilisation / supply-gap / loss metrics
   score_bottlenecks()                 ranked 0-100 severity scorecard at a base year
   aggregate_by_family()               mean severity per fossil/renewable/delivery family
   snapshot_metrics()                  headline KPI values at the base year
          ▲
dashboards/q9_operational_bottlenecks/ ← presentation only
   config.py   families, CF series, benchmarks, palette (data, not logic)
   charts.py   six Plotly visuals (renders engine frames, computes nothing)
   page.py     sidebar + KPI deck + answer hero + insight cards (thin shell)
scripts/verify_q9_bottlenecks.py       headless end-to-end test of the engine
```

## 2. What counts as an "operational bottleneck"

A bottleneck is any constraint that stops **nameplate capability** from becoming
**delivered energy**. Each is normalised to a severity (higher = more binding) on
its own reference band:

| Family | Bottleneck | Underlying metric |
|---|---|---|
| **Fossil supply** | Thermal fleet under-utilisation | coal/gas/nuclear capacity factor |
| **Fossil supply** | Domestic gas supply shortfall | gas production ÷ consumption |
| **Fossil supply** | Fossil import dependence | imported ÷ total fossil supply (TOE) |
| **Renewable supply** | Renewable capacity not converting | blended RE capacity factor |
| **Renewable supply** | Solar intermittency / wind variability / hydro seasonality | per-source capacity factor |
| **Grid delivery** | T&D delivery losses | T&D losses ÷ generation |

## 3. How the question is answered

| Step | Visual | What it decides |
|---|---|---|
| **1 · Diagnose** | Answer hero + V1 severity scorecard + V2 capacity-factor trends | Which bottleneck is the tightest, and how utilisation has moved |
| **2 · Quantify** | V3 capability-vs-delivered gap + V4 gas supply gap | The physical energy trapped by under-use and fuel shortfalls |
| **3 · Trace** | V5 T&D loss drain + V6 RE capability-vs-output | Delivery losses and the renewable conversion gap |
| **4 · Synthesise** | KPI deck + insight cards | Headline constraints for fossil, renewable and delivery |

The **answer** the dashboard recommends: the tallest severity bar in V1 — in this
system typically the **domestic gas supply shortfall** and **thermal
under-utilisation** on the fossil side, and **renewable capability not converting
(interittency/integration)** on the renewable side.

## 4. Sidebar controls

1. **Analysis Year** — snapshot year the scorecard is evaluated at (2008–2024).
2. **Bottleneck Families** — include/exclude fossil, renewable and delivery.
3. **Flag bottlenecks at severity ≥** — threshold slider to cut through to the
   most binding constraints.
4. **Global unit slicers** — electricity (GWh), power (MW), gas (BCF).

## 5. Visualizations

- **V1** — ranked horizontal severity scorecard (0–100, family-coloured, "binding ≥45" guide).
- **V2** — capacity-factor trajectories for thermal, hydro, wind, solar and blended RE.
- **V3** — nameplate capability (bars) vs delivered generation (area) — the shortfall.
- **V4** — gas production vs consumption with the LNG-met shortfall shaded.
- **V5** — T&D loss rate against the 15% benchmark.
- **V6** — dual-axis renewable installed MW vs realised RE generation.

## 6. Key formulas (base units)

- Nameplate energy (GWh) = installed MW × **8.76**  (8760 h / 1000)
- Capacity factor % = generation ÷ nameplate energy × 100
- Gas self-sufficiency % = production ÷ consumption × 100
- Fossil import dependence % = Σ imports ÷ Σ supply over oil/gas/LNG/LPG/coal
- T&D loss rate % = T&D losses ÷ generation × 100
- Severity (higher-is-better metric) = clamp((worst − value) / (worst − best) × 100)
