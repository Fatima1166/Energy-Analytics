# Configuration for the Forecasted Power Producer Cost dashboard (question 7).

DASHBOARD_TITLE = "Forecasted Cost of Energy Power Producers (1999-2035)"
DEFAULT_HORIZON = 2035
DEFAULT_CALIB_START = 2012
DEFAULT_BASE_GDP_GROWTH = 4.0
DEFAULT_FUEL_INFL = 3.0
DEFAULT_SPREAD_PP = 2.0

# The six analytical elements of Question 7:
ELEMENTS = [
    {
        "id": "E1",
        "title": "Producer cost snapshot (KPI strip)",
        "objective": 1,
        "what": "Reported 2024 purchase-cost bill, horizon-year projected cost, blended "
                "US$/MWh and cumulative cost avoidance of the RE 50% pathway",
    },
    {
        "id": "E2",
        "title": "V1 Historical cost bill purchased from power producers",
        "objective": 1,
        "what": "Per-technology generation priced at implied purchase tariffs "
                "(US$/MWh), 1999-2024, plus blended average buying price",
    },
    {
        "id": "E3",
        "title": "V2 Fuel price exposure, sensitivity & backtest",
        "objective": 2,
        "what": "Reference-cost band under low/base/high fuel escalation + hold-out "
                "validation of the cost model (2021-2024)",
    },
    {
        "id": "E4",
        "title": "V3 Cost avoidance & unit-cost learning curves",
        "objective": 3,
        "what": "Annual and cumulative producer-cost avoided by RE 50% vs Minimum RE, "
                "and blended purchase price trajectories per deployment case",
    },
    {
        "id": "E5",
        "title": "V4 Who gets paid what (cost mix by technology)",
        "objective": 4,
        "what": "Stacked cost bill by technology for the selected deployment case and "
                "2024 vs horizon-year bar comparison",
    },
    {
        "id": "E6",
        "title": "V5 Forecasted producer cost by deployment case",
        "objective": 5,
        "what": "Total purchase-cost fan Minimum RE / Reference / RE 50% to the horizon, "
                "anchored on the reported 2024 bill",
    },
]

# Curated palette matched to the platform design system
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
SLATE = "#94A3B8"

ACCENT = AMBER  # cost dashboards anchor on amber/gold
