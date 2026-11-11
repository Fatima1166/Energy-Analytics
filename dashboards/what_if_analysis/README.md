# What-If Analysis & WisRule Prediction Dashboard

---

## 1. Overview & Objective

This dashboard answers the research question:
> **"What are the predicted values of these parameters based on the what-if analysis?"**

It integrates the trained Machine Learning models (Gradient Boosting Regressors, Random Forest Demand Classifier, Gradient Boosting Security Classifier) with the **1,546 cognitive association rules** mined by the **WisRule algorithm** (*Khan & Shaheen, 2022, Journal of Information Science*).

---

## 2. Core Capabilities

### Dynamic Scenario Builder (Beyond Static Presets)
Users can define scenarios **dynamically** rather than choosing from static presets:
- **Scenario Meta**: Name, description, horizon year (2024–2035).
- **Four WisRule Multi-Dimensional Axes**:
  1. **Time Dimension ($TI$)**: Historical intervals (`TI1_2000-05` to `TI5_2020-25`) and seasonal slices (e.g. December / winter peak).
  2. **Location Dimension ($LI$)**: Geographic / demand strata (`LI_High` Industrial, `LI_Medium` Commercial, `LI_Low` Residential).
  3. **Utility Dimension ($U$)**: Domain utility priorities (Electricity Waste/Losses, Renewable Share, Gas Self-Sufficiency, Import Dependence, CO₂ Intensity, Capacity Utilization).
  4. **Context Dimension ($C$)**: Operational shocks and policies (High Waste Surge, ARE 2030 Policy Target, Winter Gas Curtailment, Economic Expansion/Slowdown).
- **Interactive Parameter Sliders**:
  - Electricity Waste / T&D Loss rate (5.0% to 35.0%)
  - GDP Growth Rate (-2.0% to +8.0%)
  - Installed Capacity (30,000 to 70,000 MW)
  - Generation by source: Solar, Wind, Hydro, Gas, Coal, Nuclear (GWh)
  - Sector Focus: Industrial, Commercial, Domestic, Bulk Supply

---

## 3. Predicted Parameters (What-If Outputs)

| Parameter | Unit | Model / Method | Accuracy / Performance |
|-----------|------|----------------|------------------------|
| **Total Generation** | GWh | Gradient Boosting Regressor + Mix Calibration | $R^2 = 93.4\%$ (Accuracy $95.96\%$) |
| **Delivered Power** | GWh | Generation $\times (1 - \text{Waste Rate})$ | Direct physical conservation |
| **Electricity Waste / Losses** | GWh | Generation $\times \text{Waste Rate}$ | Quantified volume lost |
| **Renewable Share** | % | Regressor + Clean Physics Generation | $R^2 = 76.9\%$ (Accuracy $93.33\%$) |
| **CO₂ Emissions** | Mt | Gradient Boosting Regressor + Carbon Accounting | $R^2 = 76.2\%$ (Accuracy $94.34\%$) |
| **Energy Security Status** | Class | Gradient Boosting Classifier | $100\%$ Test Accuracy (`Secure`, `Moderate`, `Stressed`) |
| **Sector Demand Regime** | Tier | Stratified Random Forest Classifier | $95.12\%$ Test Accuracy (`Tier1_Low`, `Tier2_Med`, `Tier3_High`) |

---

## 4. WisRule Cognitive Rules Tables & Multi-Dimensional Filtering

Currently presents all **1,546 mined rules** in interactive tables with multi-dimensional filtering:
- **Polarity**: Positive Wise Rules (WFISp, $\text{WisVal} = 1.0$) vs Negative Wise Rules (WFISn, $\text{iWisVal} = 2.0$).
- **Time Filter**: `TI1`, `TI2`, `TI3`, `TI4`, `TI5`.
- **Location Filter**: `LI_High` (Industrial), `LI_Medium` (Commercial), `LI_Low` (Residential).
- **Utility Focus**: Waste/Efficiency, Renewables, Gas, CO₂, Capacity, Coal, Nuclear.
- **Minimum Utility**: Slider from $0.60$ to $1.00$.
- **Context Filter**: ARE Policy, Pre-ARE, GDP Growth, Industrial Demand.
- **Search**: Free-text search across Rule IDs, Antecedents, and Consequents.
- **Export**: One-click CSV export of filtered rules.

---

## 5. Mathematical Formulations (Khan & Shaheen, 2022)

- **CPIR (Conditional-Probability Increment Ratio, Eq 2)**:
  $$\text{CPIR}(A \to B) = \frac{\text{Supp}(A \cup B) - \text{Supp}(A)\cdot\text{Supp}(B)}{\text{Supp}(A)\cdot(1 - \text{Supp}(B))}$$

- **UPII (Utility of Potentially Interesting Itemsets, Eq 15)**:
  $$\text{UPII}(A \to B) = \frac{u(AB)\cdot\text{Supp}(AB) - [u(A)\cdot\text{Supp}(A)][u(B)\cdot\text{Supp}(B)]}{u(A)\cdot\text{Supp}(A)\cdot(1 - \text{Supp}(B))}$$

- **WisVal Invariant (Positive Rules, Eq 17)**:
  $$\text{WisVal} = 1.0 \iff \text{All 4 gates cleared simultaneously}$$

- **iWisVal Invariant (Negative Rules, Eq 19)**:
  $$\text{iWisVal} = 2.0 \iff A \implies \neg B$$

