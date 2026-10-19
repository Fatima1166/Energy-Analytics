# Q6 — Optimal Fuel & Renewable Energy Supply Chain Utilization

**Question:** *What is the optimal utilization of fuel and renewable energy supply chains?*

An interactive supply chain optimization dashboard analyzing transmission efficiency, fuel import dependency, renewable utilization, natural gas self-sufficiency, and simulated optimal power generation portfolios (1999–2024).

---

## 1. How the Question is Answered

| Analysis Objective | Implementation |
|---|---|
| **Objective 1: Multi-Dimensional Scorecard** | Spider/radar chart comparing 5 supply chain dimensions against perfect benchmark (100) + historical T&D losses and grid efficiency trajectory |
| **Objective 2: Import & Utilisation Balance** | Domestic vs imported primary supply with import dependency % trajectory + RE installed capacity (MW) vs actual generation (GWh) utilisation rate |
| **Objective 3: Gas Balance & LNG Economics** | Natural gas production, consumption and LNG top-up with domestic self-sufficiency % + LNG import volume vs cost and unit cost efficiency (MUSD/unit) |
| **Objective 4: Composite Optimization Score** | Historical weighted composite optimization index (0–100) tracked over time under user-selected strategy weights |
| **Objective 5: Optimal Mix Simulator** | What-if simulation comparing the evaluated year's actual reported generation mix with user-defined target portfolio (% RE vs % Conventional) |

---

## 2. Interactive Sidebar Controls

The sidebar enables thorough scenario analysis with real-time reactivity across all KPIs, visual charts, and recommendations:

1. **Optimization Strategy**:
   - `Balanced Optimization`: 40% RE / 60% Conventional, balanced weighting.
   - `Accelerated Clean Transition`: 60% RE / 40% Conventional, clean transition priority.
   - `Aggressive Net-Zero Ambition`: 75% RE / 25% Conventional, high decarbonization priority.
   - `Energy Security & Import Reduction`: 50% RE / 50% Conventional, import & gas security priority.
   - `Grid Efficiency & Loss Minimization`: 45% RE / 55% Conventional, T&D loss reduction priority.
   - `Custom Policy Mix`: Fully custom parameter selection.
2. **Analysis Period**:
   - Dual-ended range slider (1999–2024). All KPI cards and scorecards evaluate the final year selected.
3. **Supply & Fuel Streams Multiselect**:
   - Filter which energy streams (`Natural Gas`, `LNG Imports`, `Coal`, `Oil & Petroleum`, `Nuclear`, `Hydro`, `Renewables`, `Imported Power`) are included in the primary supply and import dependency calculations.
4. **Target RE Generation Share (%)**:
   - Adjust target renewable generation share (20%–85%). The complementary conventional share is dynamically calculated (`100 - RE%`).
5. **Target T&D Loss Benchmark (%)**:
   - Dynamic benchmark slider (8%–22%, default 15.0%). Updates grid efficiency scoring and reference lines.
6. **Optimization Objective Priority (Weights)**:
   - Dynamic weighting presets: `Balanced`, `Energy Security`, `Grid & Transmission Efficiency`, `Renewable & Clean Transition`.
7. **Global Unit Slicers**:
   - Full support for Energy (`TOE`, `MTOE`, `KTOE`), Electricity (`GWh`, `TWh`, `MWh`), Power (`MW`, `GW`, `kW`), and Gas (`BCF`, `TCF`, `MMSCF`).

---

## 3. The 5 KPI Dimensions

| Code | KPI Card | Formula / Dimension | Benchmark Target |
|---|---|---|---|
| **SC1** | Composite Supply Chain Score | Weighted combination of 5 normalized dimensions (0–100) | ≥75 / 100 (Optimal) |
| **SC2** | Grid Transmission Efficiency | `(1 - td_losses / generation) × 100` | Target Loss Benchmark (≤15%) |
| **SC3** | Fuel Import Dependency | `imports / (domestic + imports) × 100` across selected streams | ≤30% safe threshold |
| **SC4** | Renewable Utilisation Rate | RE actual generation / theoretical max potential at capacity | ≥75 score |
| **SC5** | Gas Self-Sufficiency | `domestic production / consumption × 100` | ≥70% self-sufficiency |

---

## 4. Visualizations Overview

- **Visual 1**: Multi-dimensional radar scorecard for evaluated year.
- **Visual 2**: T&D losses vs generation and grid transmission efficiency vs benchmark.
- **Visual 3**: Domestic primary supply vs imports stacked volume and dependency %.
- **Visual 4**: Renewable capacity (MW) vs actual generation (GWh) with capacity factor utilization.
- **Visual 5**: Domestic natural gas production vs consumption gap and LNG imports with self-sufficiency %.
- **Visual 6**: LNG import volume vs cost (MUSD) and cost-per-unit efficiency trend.
- **Visual 7**: Composite supply chain optimization score trend (1999–2024) with dimension breakdown.
- **Visual 8**: Real historical generation mix vs optimal target simulation mix.
