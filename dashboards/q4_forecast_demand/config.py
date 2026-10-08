# Configuration for the Forecasted Energy Demand dashboard (question 4).

DASHBOARD_TITLE = "Forecasted Energy Demand (1999-2035)"
DEFAULT_HORIZON = 2035
DEFAULT_CALIB_START = 2012
DEFAULT_BASE_GDP_GROWTH = 4.0
DEFAULT_SPREAD = 1.5

# The eight elements this dashboard is allowed to show, and the objective each
# one answers.  Kept here so the README, the footer and the page cannot drift
# apart.
ELEMENTS = [
    {"id": "E1", "title": "Demand snapshot", "objective": 1,
     "what": "Reported demand now, the horizon value under each scenario, and the forecast growth rate"},
    {"id": "E2", "title": "V1 History 1999-2024", "objective": 1,
     "what": "Electricity, gas and total final energy, absolute and indexed"},
    {"id": "E3", "title": "V2 Scenario fan 2025-2035", "objective": 2,
     "what": "Low / Base / High paths for total, electricity and gas demand"},
    {"id": "E4", "title": "V3 Demand drivers", "objective": 3,
     "what": "Demand against real GDP, GDP growth and population, with the fitted income elasticity"},
    {"id": "E5", "title": "V4 Driver decomposition", "objective": 3,
     "what": "Each year's demand growth split into income per head, population and intensity"},
    {"id": "E6", "title": "V5 Sector and province mix", "objective": 4,
     "what": "Electricity demand by end-use sector and by province, reported and to 2035"},
    {"id": "E7", "title": "V6 Supply-demand gap", "objective": 5,
     "what": "Primary supply against demand, the gap, and gas / electricity import dependency"},
    {"id": "E8", "title": "V7 Forecast reliability", "objective": 6,
     "what": "Hold-out MAPE and RMSE per model, and how the last four years would have been predicted"},
]

# Short colour vocabulary, matched to the rest of the app.
GREEN = "#10B981"
BLUE = "#00A6FB"
ORANGE = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
PINK = "#F472B6"

SERIES_COLORS = {
    "total_final": BLUE,
    "electricity_final": GREEN,
    "gas_final": ORANGE,
    "elec_grid": PURPLE,
}
