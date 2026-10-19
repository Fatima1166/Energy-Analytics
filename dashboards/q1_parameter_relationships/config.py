# Configuration for the Parameter Relationships & What-If dashboard (question 1).

DASHBOARD_TITLE = "Energy Parameter Relationships & What-If Forecasts (1999-2035)"
DEFAULT_HORIZON = 2035
DEFAULT_PERIOD = (2002, 2024)
DEFAULT_ROLL_WINDOW = 7

# The five analytical elements of Question 1:
ELEMENTS = [
    {
        "id": "E1",
        "title": "Relationship web (correlation heat-map)",
        "objective": 1,
        "what": "Pairwise Pearson correlation across every tracked energy, "
                "economic and emissions parameter over the chosen period",
    },
    {
        "id": "E2",
        "title": "Pair explorer (scatter + OLS trend)",
        "objective": 1,
        "what": "Any two parameters plotted against each other with the fitted "
                "line, r, R² and slope for the selected period",
    },
    {
        "id": "E3",
        "title": "Relationship stability (rolling line)",
        "objective": 2,
        "what": "The selected pair's correlation recomputed on a sliding year "
                "window to show whether the link is stable or drifting",
    },
    {
        "id": "E4",
        "title": "What-if projection (history + baseline + what-if)",
        "objective": 3,
        "what": "One parameter's reported history extended to the horizon under "
                "the historical trajectory and the slider-driven what-if case",
    },
    {
        "id": "E5",
        "title": "Cross-parameter verdict (delta + elasticity bars)",
        "objective": 3,
        "what": "What-if vs baseline change for every parameter plus the fitted "
                "GDP / population elasticities that drive it, with a ledger table",
    },
]

# Palette -- blue/cyan-led to separate Q1 from the emerald allocation deck and
# the amber cost deck.
GREEN = "#10B981"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
SLATE = "#94A3B8"
