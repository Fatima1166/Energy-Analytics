# Q5 — Forecasted Energy Supply (1999–2035)

**Question:** *What is forecasted energy supply?*

Provides a comprehensive, empirical, and policy-grounded outlook for Pakistan's energy supply from the reported historical era (1999–2024) to the 2035 planning horizon under **Low**, **Base**, and **High** scenarios.

Engine: [`core/supply_forecast.py`](../../core/supply_forecast.py).  
Reproduce every figure without opening a browser:
```powershell
.venv\Scripts\python.exe scripts\verify_supply_forecast.py
```

---

## 1. How the question is answered

| Objective | Where it is answered |
|---|---|
| **1. Historical supply trends (1999–2024)** | **E1** KPI strip, **E2** V1 History trajectory (Primary TOE & Power GWh) |
| **2. Supply forecast to 2035 under Low / Base / High** | **E3** V2 Scenario fan (Primary TOE & Generation GWh) |
| **3. Fuel & technology supply mix evolution** | **E4** V3 Technology mix vs ARE 30% and 60% Clean Energy targets |
| **4. Installed generation capacity expansion (MW)** | **E5** V4 Capacity outlook across Hydro, Solar, Wind, Nuclear & Thermal |
| **5. Supply adequacy & reserve margin vs demand** | **E6** V5 Supply vs demand (GWh) & system reserve margin % corridor |
| **6. Energy security: indigenous vs imported supply** | **E7** V6 Indigenous energy vs import dependency trajectory |
| **7. Forecast reliability: hold-out backtesting** | **E8** V7 Hold-out (2021–2024) MAPE %, RMSE, Bias %, R² & model winner |

---

## 2. The eight dashboard elements

| # | Element | What it shows |
|---|---|---|
| **E1** | **KPI strip (5 cards)** | 2024 reported vs 2035 horizon levels for Primary Supply, Power Generation, Clean Share %, Required Capacity (MW), and Reserve Margin Adequacy |
| **E2** | **V1 Historical trajectory (1999–2024)** | Dual panel: Primary Energy Supply by fuel source (TOE) and Power Generation by technology (GWh) |
| **E3** | **V2 Scenario fans (2025–2035)** | Low / Base / High paths for Total Primary Supply and Power Generation, envelope shaded with boundary demarcation |
| **E4** | **V3 Fuel & technology mix** | Technology dispatch shares (Hydro, Solar, Wind, Nuclear, Coal, Gas) and Clean Energy share % vs 60% Clean Target and 30% ARE Target |
| **E5** | **V4 Installed capacity (MW/GW)** | Technology-wise generation capacity required to reliably deliver dispatch, accounting for technology capacity factors |
| **E6** | **V5 Supply adequacy & reserve margin** | Generation supply vs forecasted demand (GWh) with system reserve margin % evaluated against the safe 15%–25% planning corridor |
| **E7** | **V6 Energy security & imports** | Indigenous domestic energy production vs imported fuel exposure (TOE) and import dependency % trajectory |
| **E8** | **V7 Forecast reliability** | Hold-out backtest (training ≤ 2020, hold-out 2021–2024) comparing Driver vs Trend models with MAPE, RMSE, Bias and R² |

---

## 3. Baseline numbers (Calibration 2012–2024, Horizon 2035, Base GDP 4.0% ± 1.5pp)

### A. Energy Supply Aggregates

| Metric | 2024 Reported | 2035 Low | 2035 Base | 2035 High | Base Growth |
|---|---|---|---|---|---|
| **Total Primary Supply (MTOE)** | 75.73 | 86.29 | **93.25** | 100.72 | +1.91%/yr |
| **Power Generation Supply (GWh)** | 154,480 | 276,171 | **385,837** | 533,758 | +8.68%/yr |
| **Clean Generation (GWh)** | 86,140 | 125,109 | **161,512** | 207,727 | +6.90%/yr |
| **Clean Energy Share %** | 55.76% | 45.30% | **41.86%** | 38.92% | Tracking benchmark |
| **Variable RE (Solar + Wind) %** | 16.18% | 16.83% | **17.78%** | 19.06% | ARE 30% policy |
| **Required Installed Capacity (GW)** | 43.8 GW | 52.4 GW | **69.8 GW** | 94.6 GW | Capacity additions |

### B. Technology Generation Mix to 2035 (Base Scenario, GWh)

| Technology | 2024 Reported | 2035 Base Outlook | Technology Role |
|---|---|---|---|
| **Hydro** | 38,270 | **57,681** | Major baseload expansion (Dasu, Mohmand, Diamer-Bhasha) |
| **Solar** | 19,830 | **56,577** | Accelerated utility & distributed solar under ARE policy |
| **Wind** | 5,160 | **12,031** | Jhimpir & coastal wind corridor development |
| **Nuclear** | 22,880 | **35,223** | Reliable non-fossil baseload (K-2, K-3, C-5) |
| **Coal** | 24,360 | **112,163** | Prioritizing indigenous Thar coal over imported coal |
| **Natural Gas / RLNG** | 43,980 | **112,163** | Dispatchable balancing & peaking thermal capacity |
| **Total Generation** | **154,480** | **385,837** | +8.68% CAGR |

### C. Supply Adequacy & Reserve Margin (2035)

| Scenario | Generation Supply (GWh) | Projected Demand (GWh) | Reserve Margin % | System Adequacy Classification |
|---|---|---|---|---|
| **Low** | 276,171 | 293,834 | **−6.01%** | **Deficit Risk / Load Shedding Threat** |
| **Base** | 385,837 | 293,834 | **+31.31%** | **Capacity Trap / Payment Burden Risk** |
| **High** | 533,758 | 293,834 | **+81.65%** | **Severe Overcapacity Trap** |

> **Key Finding:** In the Low supply scenario, delayed capital expenditures create a supply deficit by 2035. Conversely, in the Base and High scenarios, if demand growth slows, excess installed capacity can trigger unsustainable capacity payments. Maintaining reserve margins within the **15%–25% corridor** is essential.

### D. Energy Security & Import Vulnerability (2035)

| Scenario | 2035 Primary Supply (MTOE) | Indigenous Supply (MTOE) | Imported Energy (MTOE) | Import Share % |
|---|---|---|---|---|
| **Reported (2024)** | 75.73 | 54.15 | 21.58 | **28.5%** |
| **Low Scenario** | 86.29 | 59.54 | 26.75 | **31.0%** |
| **Base Scenario** | 93.25 | 72.73 | 20.51 | **22.0%** |
| **High Scenario** | 100.72 | 84.60 | 16.11 | **16.0%** |

### E. Model Hold-Out Backtesting (2021–2024)

| Series | Model | Hold-Out MAPE % | Hold-Out RMSE | Bias % | Calibration R² | Model Winner |
|---|---|---|---|---|---|---|
| **Primary Energy Supply** | Driver | **12.65%** | 1.13e+07 | +9.0% | 0.889 | ◀ Lower Error |
| Primary Energy Supply | Trend | 13.45% | 1.20e+07 | +10.0% | 0.814 | |
| **Electricity Generation** | Driver | **7.83%** | 14,152 | +7.8% | 0.968 | ◀ Lower Error |
| Electricity Generation | Trend | 11.39% | 20,109 | +11.4% | 0.966 | |
| **Clean Generation** | Trend | **24.00%** | 19,783 | −24.0% | 0.820 | ◀ Lower Error |
| Clean Generation | Driver | 25.37% | 20,947 | −25.4% | 0.702 | |

---

## 4. Unit Support

Supports real-time unit conversion via the platform unit slicer:
- **Energy:** `TOE`, `MTOE`, `KTOE`
- **Electricity:** `GWh`, `TWh`, `MWh`
- **Power:** `MW`, `GW`, `kW`
