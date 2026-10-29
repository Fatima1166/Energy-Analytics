"""
dashboards/q10_resource_allocation/config.py -- tunables and plain-word labels
for Question 10 ("What is optimal resource allocation for sustainable
development?").

All the maths lives in core/resource_allocation.py.  This file only holds the
reader-facing choices (what the plan may favour, how far ahead it looks, how
fast demand grows), the words every one of those means, and the palette.

The engine keeps its own defaults for the two knobs that are no longer on
screen (share concentration and fuel price drift), so a run with no sidebar
state still lands on the same plan as the Balanced preset below.
"""

DASHBOARD_TITLE = "Optimal Resource Allocation for Sustainable Development (2024-2035)"

# ── Reader choices ───────────────────────────────────────────────────────────
HORIZON_RANGE = (2026, 2035)     # the plan is never read past 2035
GROWTH_RANGE = (2.0, 8.0)        # % a year on the reported generation base
DEFAULT_GROWTH_PCT = 4.5

# One pick instead of three weight sliders.  The three numbers are the weights
# on cheapest power / lowest CO₂ / least imported fuel; they are normalised in
# the engine, so only their ratio matters.  Listed here, not printed on screen.
PRIORITY_PRESETS = {
    "Balanced (planner's default)":     (35.0, 40.0, 25.0),
    "Cheapest power":                   (70.0, 15.0, 15.0),
    "Lowest CO₂":                        (15.0, 60.0, 25.0),
    "Least fuel bought abroad":         (20.0, 20.0, 60.0),
}
PRESET_ORDER = list(PRIORITY_PRESETS)


def preset_weights(preset: str) -> tuple:
    """The (cost, carbon, security) weights behind one preset name."""
    return PRIORITY_PRESETS.get(preset, PRIORITY_PRESETS[PRESET_ORDER[0]])


# ── Plain words ──────────────────────────────────────────────────────────────
# "Other RE" is the only source name a reader has to decode; it is two words
# wide, so the bar charts get a line break instead of a squeezed label.
TECH_WORDS = {"Other RE": "Other renewables"}
TECH_TICKS = {"Other RE": "Other\nrenewables"}


def tech_word(tech: str) -> str:
    """The full plain name of one technology."""
    return TECH_WORDS.get(tech, tech)


def tech_tick(tech: str) -> str:
    """The axis-label form of one technology name."""
    return TECH_TICKS.get(tech, tech)


# What the plan is called on screen.  The old mix is named with the year it
# actually came from, so a label never claims a year the number is not from.
PLAN_WORD = "The plan"


def bau_word(year: int) -> str:
    return f"The {int(year)} mix"


# ── Palette ──────────────────────────────────────────────────────────────────
# Emerald/teal leads this page so it reads apart from the amber cost deck.
GREEN = "#10B981"
TEAL = "#14B8A6"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
SLATE = "#94A3B8"
