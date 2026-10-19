# Q10 — Optimal Resource Allocation for Sustainable Development

Answers **Question 10**: *"What is optimal resource allocation for sustainable
development?"* with a transparent, solver-free constrained optimiser planning
to 2035 (horizon adjustable to 2040).

## Idea

Given the horizon-year generation requirement, split it across the seven
production technologies to maximise a three-pillar sustainability utility

```
utility(tech) = w_cost·(1−costₙ) + w_carbon·(1−CO₂ₙ) + w_security·(1−importₙ)
```

subject to real **resource ceilings** (domestic gas field → GWh, hydro/wind/
solar build-out headroom, coal import logistics). Shares are drawn
proportional to `utility^pressure`, then a **water-filling loop** clamps each
technology to its ceiling and re-spreads the remainder — anything left
unserved is reported honestly as a shortfall. Everything is benchmarked
against BAU: the reported 2024 mix frozen forward onto the same requirement.

## Architecture

| Layer | File | Role |
|---|---|---|
| Engine | `core/resource_allocation.py` | Profiles, utility, water-filling, Pareto sweep, sector split, radar scores |
| Config | `config.py` | Defaults, weights, emerald/teal palette |
| Charts | `charts.py` | Dumb polar/Sankey/gauge figures, values pre-computed |
| Page | `page.py` | Weight sliders, KPI strip, visual composition, ledger |

Registered as key `q10` with unit domains `electricity, cost, emission, gas`.
CO₂ intensities fall back to IPCC lifecycle constants unless
`dim_emission_factor` matches Coal/Gas vocabulary.

## Visuals (deliberately different chart types from the rest of the deck)

1. **Row 1** — Cost–carbon **Pareto frontier** (θ sweep, optimal star + BAU
   diamond) beside the **Nightingale rose** (BAU ring vs optimal wedges).
2. **Row 2** — Six-axis **sustainability radar** beside the per-technology
   **reallocation dumbbell** (emerald scale-ups, red claw-backs).
3. **Row 3** — Two **deliverability gauges**: demand coverage inside ceilings
   and domestic-gas self-sufficiency of the allocated gas run.
4. **Row 4** — Source→sector **Sankey** of the optimised allocation.
5. **Row 5** — Allocation ledger table (optimal vs BAU, ceilings, clamped
   flags, cost, CO₂, required GW).

## Sidebar controls

- Planning horizon (2026–2040), demand growth %/yr
- Sustainability weights: Least cost / Low carbon / Fuel security (normalised)
- Optimisation pressure (share-concentration exponent)
- Advanced: fuel price escalation %/yr

## Verification

```
.venv\Scripts\python.exe scripts\verify_q10_allocation.py
```

Runs the optimiser against MySQL and prints the allocation, BAU-vs-optimal
KPIs, Pareto endpoints, gas feasibility and sanity checks.
