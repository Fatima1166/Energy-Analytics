# Configuration for the Optimal Resource Allocation dashboard (question 10).

DASHBOARD_TITLE = "Optimal Resource Allocation for Sustainable Development (2024-2035)"
DEFAULT_HORIZON = 2035
DEFAULT_DEMAND_GROWTH = 4.5
DEFAULT_PRESSURE = 3.0
DEFAULT_W_COST = 35.0
DEFAULT_W_CARBON = 40.0
DEFAULT_W_SECURITY = 25.0
DEFAULT_FUEL_INFL = 3.0

# The five analytical elements of Question 10:
ELEMENTS = [
    {
        "id": "E1",
        "title": "Allocation footprint (grouped bars + trade-off lines)",
        "objective": 1,
        "what": "BAU-vs-optimal generation per technology as grouped bars, and the "
                "cost-carbon weight sweep as a dual-axis line chart",
    },
    {
        "id": "E2",
        "title": "Reallocation & scorecard (diverging bars + butterfly bars)",
        "objective": 2,
        "what": "Per-technology optimal-minus-BAU shift as diverging bars and the "
                "six-dimension BAU-vs-optimal scorecard as butterfly bars",
    },
    {
        "id": "E3",
        "title": "Allocation concentration (cumulative-share Pareto)",
        "objective": 3,
        "what": "Resources ranked by optimal generation with the running cumulative "
                "share -- how few technologies carry the plan (80/20 reading)",
    },
    {
        "id": "E4",
        "title": "Source-to-sector supply mix",
        "objective": 4,
        "what": "Stacked bars of optimised generation per end-use sector, split by "
                "resource group",
    },
    {
        "id": "E5",
        "title": "Allocation ledger",
        "objective": 5,
        "what": "Technology table of optimal vs BAU GWh, ceilings, clamped flags, "
                "cost, CO2 and required capacity",
    },
]

# Palette -- this deck leans on emerald/teal to visually separate it from the
# amber-led cost deck and blue/green forecast decks
GREEN = "#10B981"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
SLATE = "#94A3B8"

GROUP_COLORS = {
    "Hydro": "#0284C7",
    "Solar & Wind": "#10B981",
    "Nuclear": "#A78BFA",
    "Coal": "#6B7280",
    "Gas": "#F97316",
}
SECTOR_COLOR = "#38BDF8"
