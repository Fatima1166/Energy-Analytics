# Q7 — Forecasted Cost of Energy Power Producers

Answers **Question 7**: *"What is the forecasted cost of energy power producers?"*
over the reported era (1999–2024) with a modelled outlook to 2035.

## Idea

Electricity is bought from power producers (IPPs / GENCOs) through per-technology
purchase contracts, so the producer cost bill decomposes as:

```
cost_year = Σ  generation(technology, year) × unit purchase cost(technology, year)   [US$]
```

Renewable unit costs follow a learning curve (declining US$/MWh); coal and gas
tariffs escalate with an analyst-controlled fuel-price pass-through. Total
generation is identical across the three deployment cases — only the mix, and
hence the bill, differs.

## Architecture

| Layer | File | Role |
|---|---|---|
| Engine | `core/cost_forecast.py` | Pure analytics: cost history, scenario pricing, avoidance, sensitivity, backtest |
| Config | `config.py` | Defaults, palette, analytical element register |
| Charts | `charts.py` | Dumb, presentation-only Plotly figures (values pre-computed) |
| Page | `page.py` | Sidebar filters, KPI strip, visual composition |

Registered in `dashboards/registry.py` under key `q7` with the `cost` unit
domain (`USD bn / USD mn / USD`, see `core/units.py`).

## Visuals (fixed order convention)

1. **V1** Historical producer cost bill — stacked cost by technology + blended
   buying price and fuel-cost share.
2. **V2** Fuel price exposure, sensitivity & forecast reliability — full width,
   with the cost-model hold-out table directly below.
3. **V3** Cumulative cost avoided (bars + cumulative line) beside the blended
   price learning curves.
4. **V4** Implied purchase-tariff heat-map — technology × year US$/MWh matrix.
5. **V5 + V6** (final row, side by side) Forecasted producer cost by deployment
   case — Minimum RE / Reference / RE 50% fan — next to the **cost-bridge
   waterfall** walking the bill from the reported 2024 level to the horizon.

## Sidebar controls

- Deployment scenarios (Minimum RE / Reference / RE 50%)
- Forecast horizon (2026–2035)
- Fuel price escalation %/yr and sensitivity band ±pp
- Advanced: calibration start, Base GDP growth

## Verification

```
.venv\Scripts\python.exe scripts\verify_q7_cost.py
```

Runs the engine against MySQL and prints the KPI figures, scenario bill at the
horizon, avoidance total and backtest metrics.
