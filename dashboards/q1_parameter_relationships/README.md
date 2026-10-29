# Q1 — Energy Parameter Relationships

Answers the first half of Question 1: *"What have been the relationships among
different parameters of energy over a given period of time?"*

The second half of the research question (what-if predicted values) is served by
the dedicated forecast dashboards Q4 (demand), Q5 (supply) and Q7 (cost), so this
page stays focused on one signal only: how the parameters move together.

## Architecture

| Layer | File | Role |
|-------|------|------|
| Engine | `core/parameter_relationships.py` | Parameter frame build, Pearson correlations, OLS pair fits, rolling stability |
| Charts | `dashboards/q1_parameter_relationships/charts.py` | Five dumb Plotly visuals (no analytics) |
| Page | `dashboards/q1_parameter_relationships/page.py` | Sidebar period control, KPI strip, chart rows |
| Verify | `scripts/verify_q1_relationships.py` | Standalone MySQL audit of the engine |

## Visuals

- **V1** Correlation heat-map — parameter × parameter Pearson r (green co-move / red inverse) — full-width row
- **V7** Top relationship ranking — lollipop of the twelve strongest \|r\| links
- **V8** Correlation distribution — histogram of every computable pairwise r, co-moving vs inverse
- **V2** Pair explorer — scatter of the headline pair + OLS trend line with r / R² / slope note
- **V3** Rolling correlation line — is that link stable across sliding year windows inside the period?

Row order: KPI strip (K1 | K2 | K3) → V1 (full width) → V7 | V8 → V2 | V3.

## KPI strip

- **K1** how many parameters have joint data, how many links that implies, and how many are strong (\|r\| ≥ 0.7)
- **K2** the strongest link in the matrix
- **K3** the weakest link in the matrix

Derived ratios (`DERIVED_KEYS` in the engine — renewable share, electricity
intensity, per-capita demand, gas self-sufficiency) stay in the heat-map,
ranking and distribution, but are never chosen as the K2 headline or the
Pair Explorer pair: each is computed from parameters already on the page, so a
link involving one is partly self-referential and plots as a near-straight line.

## Period handling

The period is set in the sidebar, as one two-handle range slider above the
shared unit selectors. The engine needs six joint years before it will compute
a correlation, so a narrower pick is pushed back to a minimum eight-year span
(`MIN_SPAN`) by an `on_change` callback before the app reruns — the handles
always show what was actually analysed, and no selectable period can come back
blank. The Pair Explorer and rolling line follow the automatically chosen
headline pair, and the rolling window adapts to the span (half the period,
clamped to 4–7 years) so the stability line always has enough points to read.

## Data sources

`Q_ECONOMIC`, `Q_RENEWABLE_ENERGY`, `Q_ELEC_GEN`, `Q_TD_LOSSES`,
`Q_NATURAL_GAS`, `Q_LNG`, `Q_ENERGY_OVERVIEW` — merged on `calendar_year`
into 19 tracked parameters (levels + derived ratios such as renewable share,
electricity intensity, per-capita demand and gas self-sufficiency).
