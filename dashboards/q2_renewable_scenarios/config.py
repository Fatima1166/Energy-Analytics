# Configuration for Question 2: Renewable Energy Scenarios Dashboard

DASHBOARD_TITLE = "Renewable Energy Scenarios & Policy Impact Analysis"
DEFAULT_YEAR_RANGE = (1999, 2035)
DEFAULT_SCENARIO = "Accelerated"

# The 5 Top-Row KPI Cards (section 3.1).
#
# These are SCENARIO OUTCOMES, evaluated at the horizon year for the selected
# scenario -- not historical values.  Each card compares the scenario's
# `target_year` value against the last reported year (2024) so the direction of
# travel is visible.  Titles are filled in at render time with the actual years.
KPI_CONFIG = [
    {
        "key": "re_share",
        "title": "RE Share %",
        "unit": "of Total Generation",
        "icon": "re_share",
        "color": "green",
        "reason": "Renewable penetration the scenario reaches at the horizon.",
    },
    {
        "key": "re_capacity",
        "title": "RE Capacity",
        "unit": "MW Installed",
        "icon": "primary_energy",
        "color": "blue",
        "reason": "Installed renewable base the scenario builds to.",
    },
    {
        "key": "co2_emissions",
        "title": "CO₂ Emissions",
        "unit": "MtCO₂",
        "icon": "co2",
        "color": "red",
        "reason": "Emissions remaining at the horizon under this scenario.",
    },
    {
        "key": "lng_savings",
        "title": "LNG Savings",
        "unit": "M USD cumulative",
        "icon": "imports",
        "color": "orange",
        "reason": "Import bill avoided by displacing gas generation.",
    },
    {
        "key": "co2_intensity",
        "title": "CO₂ Intensity",
        "unit": "kgCO₂/MWh",
        "icon": "generation",
        "color": "purple",
        "reason": "Carbon intensity of the grid at the horizon.",
    },
]

# Scenario metadata
SCENARIOS_META = {
    "Baseline": {
        "badge": "Status Quo",
        "growth_solar": 2.0,
        "growth_wind": 2.0,
        "summary": "Business-as-usual with 2% annual solar & wind growth.",
    },
    "Moderate": {
        "badge": "Target 2030",
        "growth_solar": 8.0,
        "growth_wind": 8.0,
        "summary": "Balanced 8% clean energy deployment across provinces.",
    },
    "Accelerated": {
        "badge": "Recommended",
        "growth_solar": 15.0,
        "growth_wind": 15.0,
        "summary": "Aggressive decarbonisation with 15% annual renewable addition.",
    },
    "Solar-led": {
        "badge": "PV Focus",
        "growth_solar": 25.0,
        "growth_wind": 5.0,
        "summary": "High solar penetration (25% p.a.) targeting rooftop & solar parks.",
    },
    "Wind-led": {
        "badge": "Corridor Focus",
        "growth_solar": 5.0,
        "growth_wind": 25.0,
        "summary": "Rapid wind buildout (25% p.a.) in Sindh & Balochistan corridors.",
    },
}
