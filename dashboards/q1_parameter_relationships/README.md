# Q1 — Energy Parameter Relationships & What-If Forecasts

Answers Question 1: *"What have been the relationships among different
parameters of energy over a given period of time? What are the predicted
values of these parameters based on the what-if analysis?"*

## Architecture

| Layer | File | Role |
|-------|------|------|
| Engine | `core/parameter_relationships.py` | Parameter frame build, Pearson correlations, OLS pair fits, rolling stability, elasticity-driven what-if model |
| Charts | `dashboards/q1_parameter_relationships/charts.py` | Eight dumb Plotly visuals (no analytics) |
| Page | `dashboards/q1_parameter_relationships/page.py` | Sidebar controls, KPI strip, chart rows, what-if ledger |
| Verify | `scripts/verify_q1_relationships.py` | Standalone MySQL audit of the engine |

## Visuals

- **V1** Correlation heat-map — parameter × parameter Pearson r (green co-move / red inverse) — full-width row
- **V2** Pair explorer — scatter of the selected pair + OLS trend line with r / R² / slope note
- **V3** Rolling correlation line — is the selected link stable across sliding year windows?
- **V4** What-if projection — reported-history bars continued by baseline (historic CAGR) and what-if lines
- **V5** What-if impact — diverging bars of % change vs baseline for every parameter at the horizon
- **V6** Driver elasticities — grouped β_GDP / β_Pop bars per parameter (full-width row), plus a full ledger table
- **V7** Top relationship ranking — lollipop of the twelve strongest |r| links (engine `pair_samples`)
- **V8** Correlation distribution — histogram of every computable pairwise r, co-moving vs inverse

Row order: V1 (full width) → V7 | V8 → V2 | V3 → V4 | V5 → V6 (full width) → ledger.

## What-if model (solver-free)

Each parameter grows by `autonomy + β_GDP·gdp_growth + β_POP·pop_growth`, with
an optional efficiency/decoupling drag applied to the what-if case only.
Elasticities β come from log-log regressions on reported history (fallback
0.8 / 1.0 when a fit is impossible); the autonomy term is back-solved so the
baseline path reproduces the parameter's own historic CAGR exactly. Sliders:
GDP growth, population growth, efficiency drag, horizon year.

## Data sources

`Q_ECONOMIC`, `Q_RENEWABLE_ENERGY`, `Q_ELEC_GEN`, `Q_TD_LOSSES`,
`Q_NATURAL_GAS`, `Q_LNG`, `Q_ENERGY_OVERVIEW` — merged on `calendar_year`
into 19 tracked parameters (levels + derived ratios such as renewable share,
electricity intensity, per-capita demand and gas self-sufficiency).
