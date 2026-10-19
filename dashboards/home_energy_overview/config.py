"""
dashboards/home_energy_overview/config.py -- palette and copy for the landing
Energy Overview page.  Analytics live in core/energy_overview.py.
"""

HERO_KICKER = "NATIONAL ENERGY ANALYTICS PLATFORM"
HERO_TITLE = "Pakistan Energy Outlook"
HERO_TAGLINE = ("Ten decision-grade analyses over one live warehouse -- "
                "supply, demand, forecasts, costs, bottlenecks and the "
                "optimal path to a sustainable energy future.")

GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
SLATE = "#94A3B8"

# Fuel-mix donut colours (matched by substring, fallback cycling)
FUEL_COLOURS = [
    ("natural gas", "#00A6FB"),
    ("oil", "#F59E0B"),
    ("coal", "#94A3B8"),
    ("hydro", "#22D3EE"),
    ("renew", "#10B981"),
    ("solar", "#FBBF24"),
    ("wind", "#34D399"),
    ("nuclear", "#A78BFA"),
    ("biomass", "#84CC16"),
    ("import", "#EF4444"),
]
FALLBACK_RING = ["#00A6FB", "#F59E0B", "#10B981", "#A78BFA", "#22D3EE",
                 "#FBBF24", "#94A3B8", "#EF4444", "#84CC16", "#14B8A6"]
