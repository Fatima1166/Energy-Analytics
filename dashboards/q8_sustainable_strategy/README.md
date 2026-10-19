# Q8 — Sustainable Energy Strategy

Answers Question 8: *"What optimal strategy may be opted to make energy
development sustainable?"*

## Architecture

| Layer | File | Role |
|-------|------|------|
| Engine | `core/sustainability_engine.py` | Four-pillar indicator frame, scoring, greedy-knapsack package, pathway projection, verdict |
| Config | `dashboards/q8_sustainable_strategy/config.py` | Strategy library (13 candidates), pillar defaults, palette |
| Charts | `dashboards/q8_sustainable_strategy/charts.py` | Seven dumb Plotly visuals (no analytics) |
| Page | `dashboards/q8_sustainable_strategy/page.py` | Sidebar weights/budget/horizon, KPI strip, chart rows, budget ledger |
| Verify | `scripts/verify_q8_strategy.py` | Standalone MySQL audit of the engine |

## Model — the extended trilemma

Four pillars, each scored 0-100 from measured components (absolute
benchmarks where agreed, else 10th-90th percentile auto-calibration):

- **Security** — import dependence, gas self-sufficiency, generation diversity
- **Economy** — grid (T&D) efficiency, LNG unit-price pressure
- **Environment** — renewable generation share, CO₂ intensity of electricity
- **Access** — per-capita electricity, demand coverage

## Visuals

- **V1** Pillar scorecard — grouped bars: latest vs decade-earlier per pillar
- **V2** Index trajectory — multi-line: four pillars + bold weighted composite
- **V3** Strategy value density — horizontal ranking bars (pts/$bn, feasibility colour)
- **V4** Cost-impact bubble map — scatter, bubble = feasibility, filled = funded
- **V5** Pathway projection — history bars + BAU / Announced / Optimal lines
- **V6** Pillar gain vs BAU — diverging bars at the horizon
- **V7** Component diagnostics — horizontal bars of the nine underlying scores

Row order: V1 | V2 → V3 | V4 → V5 | V6 → V7 (full width) → budget ledger.

## Optimiser

Strategies carry weighted pillar impact (analyst pillar weights), annual
cost ($bn/yr) and delivery feasibility. `select_optimal_package()` ranks by
feasibility-discounted impact-per-dollar and greedily fills the budget
(knapsack). Pathways project each pillar's fitted trend to the horizon and
layer strategy uplift on top: BAU = none, Announced = feasible subset at half
effect, Optimal = full package after each strategy's lead-time ramp.

## Data sources

`Q_RENEWABLE_ENERGY`, `Q_ELEC_GEN`, `Q_TD_LOSSES`, `Q_PRIMARY_SUPPLY`,
`Q_NATURAL_GAS`, `Q_LNG`, `Q_ECONOMIC` — merged on `calendar_year` (1999-2024).
