# Configuration for the Supply Chain dashboard (Question 6).
#
# Question 6 asks how well the fuel and renewable supply chains are being used,
# so this file holds only what that answer needs: the standards each part is
# judged against, the four parts that make up the overall score, and the
# strategies that decide which part matters most.

# --- Standards (a part scoring 100 has met its standard) --------------------
BENCHMARK_IMPORT_DEPENDENCY_MAX = 30.0  # % of supply bought from abroad
BENCHMARK_RE_UTILISATION_MIN = 75.0     # % of clean plant you would expect it to make
BENCHMARK_GAS_SELFSUFFICIENCY = 70.0    # % of gas demand met at home

# Where the overall score stops being good and starts being poor.
SCORE_GOOD = 75.0
SCORE_FAIR = 50.0

# --- The four parts of the overall score ------------------------------------
# Each is a 0-100 score computed in page.py:
#   grid_efficiency        -- electricity that arrives vs electricity generated
#   re_utilisation         -- what clean plant makes vs what it could make
#   import_independence    -- how little of the supply is bought from abroad
#   gas_self_sufficiency   -- how much gas demand is met at home
#
# A fifth part used to sit here ("fuel waste"), but it was worked out from the
# same grid-loss numbers as grid_efficiency, so it said the same thing twice and
# pulled the score in one direction twice over. It is gone.

# --- Strategies ---------------------------------------------------------------
# One entry per choice in the sidebar. Each sets a clean-energy target, a grid
# loss target, and how much weight each of the four parts carries.
STRATEGIES = {
    "All four parts equally": {
        "re_target": 40,
        "loss_target": 15.0,
        "weights": {
            "grid_efficiency": 0.25,
            "re_utilisation": 0.25,
            "import_independence": 0.25,
            "gas_self_sufficiency": 0.25,
        },
        "desc": "No favourite: grid losses, clean plant use, imports and gas all count the same.",
    },
    "More clean energy": {
        "re_target": 60,
        "loss_target": 13.0,
        "weights": {
            "grid_efficiency": 0.25,
            "re_utilisation": 0.40,
            "import_independence": 0.20,
            "gas_self_sufficiency": 0.15,
        },
        "desc": "Solar, wind and hydro count for the most, on a modernised low-loss grid.",
    },
    "Much more clean energy": {
        "re_target": 75,
        "loss_target": 11.0,
        "weights": {
            "grid_efficiency": 0.20,
            "re_utilisation": 0.50,
            "import_independence": 0.20,
            "gas_self_sufficiency": 0.10,
        },
        "desc": "A deep shift to clean power, keeping as little fuel burning as possible.",
    },
    "Buy less from abroad": {
        "re_target": 50,
        "loss_target": 14.0,
        "weights": {
            "grid_efficiency": 0.15,
            "re_utilisation": 0.15,
            "import_independence": 0.40,
            "gas_self_sufficiency": 0.30,
        },
        "desc": "Home gas, home hydro and home renewables, so less is bought from other countries.",
    },
    "Fix grid losses first": {
        "re_target": 45,
        "loss_target": 10.0,
        "weights": {
            "grid_efficiency": 0.50,
            "re_utilisation": 0.15,
            "import_independence": 0.20,
            "gas_self_sufficiency": 0.15,
        },
        "desc": "Wires and transformers first: cut the electricity that never reaches anyone.",
    },
}

DEFAULT_STRATEGY = "All four parts equally"

# --- Palette ------------------------------------------------------------------
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#06B6D4"
ORANGE = "#F97316"
ROSE = "#F43F5E"
