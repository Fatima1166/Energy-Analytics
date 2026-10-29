# Configuration for the Forecasted Producer Cost dashboard (Question 7).
#
# Question 7 asks what electricity bought from power producers will cost, so this
# file holds only what that answer needs: the build-out cases said in plain words,
# the technologies the page actually draws, and the palette.  The cost maths lives
# in core/cost_forecast.py.

from core.cost_forecast import COST_TECHS

# The three build-out cases the engine prices.  Total generation is the same in
# every case -- only the mix differs -- so these say which mix is being bought.
CASE_WORDS = {
    "Minimum RE": "Little clean power",
    "Reference": "The planned build-out",
    "RE 50%": "Half clean power",
}

DEFAULT_CASE = "Reference"

# Technologies shown.  "Other RE" is left out on purpose: the reported record
# holds no generation for it in any year (fact_renewable_energy
# .gen_other_renewables_gwh is empty), so drawing it only adds a legend entry and
# a bar that are always zero.
TECHS_SHOWN = [t for t in COST_TECHS if t != "Other RE"]

# Palette matched to the platform design system
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
SLATE = "#94A3B8"
LIGHT = "#CBD5E1"
TEXT = "#E2E8F0"
