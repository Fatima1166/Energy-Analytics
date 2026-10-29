# Configuration for Question 2: Renewable Energy Scenarios Dashboard

DASHBOARD_TITLE = "Renewable Energy Scenarios & Policy Impact Analysis"
DEFAULT_SCENARIO = "Accelerated"   # the scenario the sidebar opens on

# The 4 Top-Row KPI Cards.
#
# These are SCENARIO OUTCOMES, evaluated at the horizon year for the selected
# scenario -- not historical values.  The first two compare that year with the
# last reported year (2024) so the direction of travel shows; the two saving
# cards give a running total with that year's own figure underneath.  Titles
# and years are filled in at render time, and `unit` is only a fallback label --
# the page passes the real unit so it follows the unit slicer.
KPI_CONFIG = [
    {
        "key": "re_share",
        "title": "Renewable Share",
        "unit": "of all power",
        "icon": "re_share",
        "color": "green",
        "reason": "How much of our power comes from renewables at the final year.",
    },
    {
        "key": "re_capacity",
        "title": "Renewable Power Built",
        "unit": "MW",
        "icon": "primary_energy",
        "color": "blue",
        "reason": "Clean plant capacity the scenario has to build.",
    },
    {
        "key": "co2_avoided",
        "title": "CO₂ Avoided",
        "unit": "million tonnes of CO₂",
        "icon": "co2",
        "color": "red",
        "reason": "Emissions the scenario keeps out of the air over the years shown.",
    },
    {
        "key": "lng_savings",
        "title": "Gas Import Savings",
        "unit": "million USD",
        "icon": "imports",
        "color": "orange",
        "reason": "Money not spent importing gas, because renewables made that power.",
    },
]

# The five scenarios themselves -- rates, labels, colours and descriptions --
# live in config.settings.SCENARIOS, which is what the projections read.  They
# are not repeated here so the two can never drift apart.
