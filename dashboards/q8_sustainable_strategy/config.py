"""
dashboards/q8_sustainable_strategy/config.py -- constants and the strategy
library for Question 8 ("What optimal strategy may be opted to make energy
development sustainable?").

All analytics live in core/sustainability_engine.py; this file only declares
tunables and the catalogue of candidate strategies the optimiser picks from.

Every label here is written the way someone would say it out loud: the short
name goes on the charts, the full name goes in the funded-measures table.
"""

DASHBOARD_TITLE = "Sustainable Energy Strategy -- Optimal Development Pathway"
DEFAULT_HORIZON = 2035
HORIZON_RANGE = (2026, 2035)      # the plan is never read past 2035
DEFAULT_EVAL_YEAR = 2024          # the last year the record reports
DEFAULT_BUDGET_BN = 8.0           # USD bn per year the package may commit
BUDGET_RANGE = (1.0, 20.0)

# Default pillar weighting (percent, renormalised in the page)
DEFAULT_WEIGHTS = {"security": 30.0, "economy": 25.0,
                   "environment": 25.0, "access": 20.0}

PILLAR_WORDS = {
    "security":    "Supply security",
    "economy":     "Affordability",
    "environment": "Clean power",
    "access":      "Access",
}

# What counts most -- one pick instead of four weight sliders.  The four
# numbers are the weights on Supply security / Affordability / Clean power /
# Access; they are listed in the module README, not printed on the sidebar.
PRIORITY_PRESETS = {
    "Balanced (planner's default)":       (30.0, 25.0, 25.0, 20.0),
    "Clean power counts most":            (20.0, 20.0, 45.0, 15.0),
    "Supply security counts most":        (45.0, 25.0, 15.0, 15.0),
    "Affordability counts most":          (20.0, 45.0, 15.0, 20.0),
    "Access counts most":                 (20.0, 20.0, 15.0, 45.0),
}
PRESET_ORDER = list(PRIORITY_PRESETS)


def preset_weights(preset: str) -> dict:
    """The four pillar weights for one preset name, as fractions of 1."""
    sec, eco, env, acc = PRIORITY_PRESETS.get(preset, PRIORITY_PRESETS[PRESET_ORDER[0]])
    total = (sec + eco + env + acc) or 1.0
    return {"security": sec / total, "economy": eco / total,
            "environment": env / total, "access": acc / total}


# ══════════════════════ strategy library ══════════════════════════════════
# pillar_impacts are score points (0-100 scale) a fully-implemented strategy
# adds to each pillar at the horizon; cost_bn_per_year is annual spend in
# constant USD billions; feasibility is the analyst's delivery-confidence 0-100.
STRATEGY_LIBRARY = [
    {
        "id": "solar_wind", "name": "Utility-scale solar and wind farms",
        "short": "Big solar and wind farms", "category": "environment",
        "pillar_impacts": {"environment": 22.0, "security": 8.0,
                           "economy": 3.0, "access": 4.0},
        "cost_bn_per_year": 3.0, "feasibility": 75, "lead_years": 3,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "hydro", "name": "Large and run-of-river hydropower",
        "short": "More hydropower", "category": "environment",
        "pillar_impacts": {"environment": 15.0, "security": 7.0,
                           "economy": 5.0, "access": 3.0},
        "cost_bn_per_year": 2.2, "feasibility": 60, "lead_years": 5,
        "phase": "Starts next (2029-32)",
    },
    {
        "id": "grid_loss", "name": "Cut losses on the grid and rebuild it",
        "short": "Cut grid losses", "category": "economy",
        "pillar_impacts": {"economy": 18.0, "access": 8.0,
                           "environment": 5.0, "security": 3.0},
        "cost_bn_per_year": 1.2, "feasibility": 70, "lead_years": 2,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "dsm_eff", "name": "Efficiency standards for appliances and industry",
        "short": "Use power more efficiently", "category": "economy",
        "pillar_impacts": {"economy": 10.0, "environment": 9.0,
                           "security": 5.0, "access": 3.0},
        "cost_bn_per_year": 0.6, "feasibility": 65, "lead_years": 2,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "lng_portfolio", "name": "Long-term LNG contracts from several sellers",
        "short": "Buy gas on longer deals", "category": "security",
        "pillar_impacts": {"security": 12.0, "economy": 6.0,
                           "environment": 0.0, "access": 2.0},
        "cost_bn_per_year": 1.8, "feasibility": 80, "lead_years": 1,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "indigenous_gas", "name": "Develop our own gas (Thar, Reko Diq)",
        "short": "Pump more of our own gas", "category": "security",
        "pillar_impacts": {"security": 18.0, "economy": 8.0,
                           "environment": -3.0, "access": 4.0},
        "cost_bn_per_year": 2.5, "feasibility": 55, "lead_years": 5,
        "phase": "Starts next (2029-32)",
    },
    {
        "id": "distributed_solar", "name": "Rooftop and net-metering solar",
        "short": "Solar on rooftops", "category": "access",
        "pillar_impacts": {"access": 14.0, "environment": 10.0,
                           "economy": 3.0, "security": 2.0},
        "cost_bn_per_year": 0.9, "feasibility": 70, "lead_years": 2,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "coal_exit", "name": "Retire or convert coal plants that cannot work",
        "short": "Close or convert coal plants", "category": "environment",
        "pillar_impacts": {"environment": 12.0, "economy": 4.0,
                           "security": -2.0, "access": 0.0},
        "cost_bn_per_year": 0.7, "feasibility": 45, "lead_years": 4,
        "phase": "Starts next (2029-32)",
    },
    {
        "id": "nuclear", "name": "Nuclear baseload (Chashma-5 and small reactors)",
        "short": "Add nuclear power", "category": "security",
        "pillar_impacts": {"environment": 12.0, "security": 9.0,
                           "economy": 2.0, "access": 2.0},
        "cost_bn_per_year": 2.8, "feasibility": 40, "lead_years": 7,
        "phase": "Starts later (2033+)",
    },
    {
        "id": "tariff_reform", "name": "Charge what power really costs and clear the debt",
        "short": "Charge the real cost", "category": "economy",
        "pillar_impacts": {"economy": 15.0, "access": 5.0,
                           "security": 3.0, "environment": 2.0},
        "cost_bn_per_year": 0.2, "feasibility": 50, "lead_years": 2,
        "phase": "Starts now (by 2028)",
    },
    {
        "id": "storage", "name": "Storage: pumped hydro and grid batteries",
        "short": "Store power for later", "category": "security",
        "pillar_impacts": {"security": 10.0, "environment": 8.0,
                           "economy": 5.0, "access": 3.0},
        "cost_bn_per_year": 1.9, "feasibility": 50, "lead_years": 5,
        "phase": "Starts later (2033+)",
    },
    {
        "id": "rural_access", "name": "Extend the grid and reach the last villages",
        "short": "Reach villages off the grid", "category": "access",
        "pillar_impacts": {"access": 20.0, "economy": 4.0,
                           "environment": 3.0, "security": 1.0},
        "cost_bn_per_year": 1.1, "feasibility": 60, "lead_years": 3,
        "phase": "Starts next (2029-32)",
    },
    {
        "id": "regional_trade", "name": "CASA-1000 and trading power with neighbours",
        "short": "Trade power with neighbours", "category": "security",
        "pillar_impacts": {"security": 10.0, "economy": 6.0,
                           "environment": 6.0, "access": 5.0},
        "cost_bn_per_year": 1.4, "feasibility": 45, "lead_years": 5,
        "phase": "Starts later (2033+)",
    },
]

# ══════════════════════ palette ══════════════════════
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
SLATE = "#94A3B8"

PILLAR_COLOURS = {
    "security": BLUE, "economy": AMBER,
    "environment": GREEN, "access": PURPLE,
}
ACCENT = TEAL

# The three futures the pathway chart draws, in plain words.
PATHWAY_WORDS = {
    "bau": "If nothing changes",
    "announced": "Only what is already promised",
    "optimal": "The recommended package",
}
PATHWAY_COLOURS = {"bau": RED, "announced": AMBER, "optimal": GREEN}
