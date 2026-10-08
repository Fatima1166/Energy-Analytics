# Configuration for the Forecasted Energy Supply dashboard (question 5).

DASHBOARD_TITLE = "Forecasted Energy Supply (1999-2035)"
DEFAULT_HORIZON = 2035
DEFAULT_CALIB_START = 2012
DEFAULT_BASE_GDP_GROWTH = 4.0
DEFAULT_SPREAD = 1.5
DEFAULT_CLEAN_TARGET = 60.0

# The eight analytical elements of Question 5:
ELEMENTS = [
    {
        "id": "E1",
        "title": "Supply snapshot (KPI strip)",
        "objective": 1,
        "what": "Reported 2024 primary supply & generation, 2035 horizon projections, clean share, capacity & reserve margin",
    },
    {
        "id": "E2",
        "title": "V1 Historical supply trajectory 1999-2024",
        "objective": 1,
        "what": "Primary energy supply (TOE) by fuel and electricity generation (GWh) by technology over the reported era",
    },
    {
        "id": "E3",
        "title": "V2 Supply scenario fan 2025-2035",
        "objective": 2,
        "what": "Low / Base / High trajectories with shaded envelope for Primary Supply and Total Generation",
    },
    {
        "id": "E4",
        "title": "V3 Fuel & technology supply mix evolution",
        "objective": 3,
        "what": "Generation shares by source to 2035, tracking against ARE 30% and 60% Clean Energy policy benchmarks",
    },
    {
        "id": "E5",
        "title": "V4 Installed generation capacity outlook (MW)",
        "objective": 4,
        "what": "Required installed capacity expansion across Hydro, Solar, Wind, Nuclear and Thermal assets to 2035",
    },
    {
        "id": "E6",
        "title": "V5 Supply adequacy & reserve margin",
        "objective": 5,
        "what": "Generation supply vs demand (GWh), reserve margin % corridor, deficit risks vs capacity trap burden",
    },
    {
        "id": "E7",
        "title": "V6 Energy security & import vulnerability",
        "objective": 5,
        "what": "Domestic indigenous energy vs imported fuel dependency (TOE) trajectory to 2035",
    },
    {
        "id": "E8",
        "title": "V7 Supply forecast reliability & backtest",
        "objective": 6,
        "what": "Hold-out validation (2021-2024) comparing Macro-Driver vs Trend models: MAPE %, RMSE, Bias and R²",
    },
]

# Curated palette matched to the platform design system
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#06B6D4"

SERIES_COLORS = {
    "tpes_toe": BLUE,
    "gen_total_gwh": GREEN,
    "gen_clean_gwh": TEAL,
    "capacity_mw": PURPLE,
}
