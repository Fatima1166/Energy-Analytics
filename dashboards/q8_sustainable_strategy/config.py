"""
dashboards/q8_sustainable_strategy/config.py -- constants and the strategy
library for Question 8 ("What optimal strategy may be opted to make energy
development sustainable?").

All analytics live in core/sustainability_engine.py; this file only declares
tunables and the catalogue of candidate strategies the knapsack optimiser
picks from.
"""

DASHBOARD_TITLE = "Sustainable Energy Strategy -- Optimal Development Pathway"
DEFAULT_HORIZON = 2035
DEFAULT_EVAL_YEAR = 2024
DEFAULT_BUDGET_BN = 8.0          # USD bn per year the package may commit
BUDGET_RANGE = (1.0, 20.0)

# Default pillar weighting (percent, renormalised in the page)
DEFAULT_WEIGHTS = {"security": 30.0, "economy": 25.0,
                   "environment": 25.0, "access": 20.0}

# ══════════════════════ strategy library ══════════════════════════════════
# pillar_impacts are score points (0-100 scale) a fully-implemented strategy
# adds to each pillar at the horizon; cost_bn_per_year is annual spend in
# constant USD billions; feasibility is the analyst's delivery-confidence 0-100.
STRATEGY_LIBRARY = [
    {
        "id": "solar_wind", "name": "Utility Solar & Wind Scale-Up",
        "short": "Solar + Wind Scale-Up", "category": "Environment",
        "pillar_impacts": {"environment": 22.0, "security": 8.0,
                           "economy": 3.0, "access": 4.0},
        "cost_bn_per_year": 3.0, "feasibility": 75, "lead_years": 3,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "hydro", "name": "Large & Run-of-River Hydro Expansion",
        "short": "Hydro Expansion", "category": "Environment",
        "pillar_impacts": {"environment": 15.0, "security": 7.0,
                           "economy": 5.0, "access": 3.0},
        "cost_bn_per_year": 2.2, "feasibility": 60, "lead_years": 5,
        "phase": "Medium-term (2029-32)",
    },
    {
        "id": "grid_loss", "name": "T&D Loss Reduction & Grid Modernisation",
        "short": "Grid Loss Reduction", "category": "Economy",
        "pillar_impacts": {"economy": 18.0, "access": 8.0,
                           "environment": 5.0, "security": 3.0},
        "cost_bn_per_year": 1.2, "feasibility": 70, "lead_years": 2,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "dsm_eff", "name": "Demand-Side Efficiency & Appliance Standards",
        "short": "Demand-Side Efficiency", "category": "Economy",
        "pillar_impacts": {"economy": 10.0, "environment": 9.0,
                           "security": 5.0, "access": 3.0},
        "cost_bn_per_year": 0.6, "feasibility": 65, "lead_years": 2,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "lng_portfolio", "name": "Contracted LNG Portfolio Diversification",
        "short": "LNG Portfolio Diversification", "category": "Security",
        "pillar_impacts": {"security": 12.0, "economy": 6.0,
                           "environment": 0.0, "access": 2.0},
        "cost_bn_per_year": 1.8, "feasibility": 80, "lead_years": 1,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "indigenous_gas", "name": "Indigenous Gas Upstream (Thar, Reko Diq)",
        "short": "Indigenous Gas Upstream", "category": "Security",
        "pillar_impacts": {"security": 18.0, "economy": 8.0,
                           "environment": -3.0, "access": 4.0},
        "cost_bn_per_year": 2.5, "feasibility": 55, "lead_years": 5,
        "phase": "Medium-term (2029-32)",
    },
    {
        "id": "distributed_solar", "name": "Distributed & Net-Metering Solar",
        "short": "Distributed Solar", "category": "Access",
        "pillar_impacts": {"access": 14.0, "environment": 10.0,
                           "economy": 3.0, "security": 2.0},
        "cost_bn_per_year": 0.9, "feasibility": 70, "lead_years": 2,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "coal_exit", "name": "Retire / Repower Unfit Coal Fleet",
        "short": "Coal Fleet Exit", "category": "Environment",
        "pillar_impacts": {"environment": 12.0, "economy": 4.0,
                           "security": -2.0, "access": 0.0},
        "cost_bn_per_year": 0.7, "feasibility": 45, "lead_years": 4,
        "phase": "Medium-term (2029-32)",
    },
    {
        "id": "nuclear", "name": "Nuclear Baseload (Chashma-5 & SMRs)",
        "short": "Nuclear Baseload", "category": "Security",
        "pillar_impacts": {"environment": 12.0, "security": 9.0,
                           "economy": 2.0, "access": 2.0},
        "cost_bn_per_year": 2.8, "feasibility": 40, "lead_years": 7,
        "phase": "Long-term (2033+)",
    },
    {
        "id": "tariff_reform", "name": "Cost-Recovery Tariff & Circular-Debt Reform",
        "short": "Tariff Reform", "category": "Economy",
        "pillar_impacts": {"economy": 15.0, "access": 5.0,
                           "security": 3.0, "environment": 2.0},
        "cost_bn_per_year": 0.2, "feasibility": 50, "lead_years": 2,
        "phase": "Short-term (2025-28)",
    },
    {
        "id": "storage", "name": "Storage: Pumped Hydro & Grid Batteries",
        "short": "Storage Build-Out", "category": "Security",
        "pillar_impacts": {"security": 10.0, "environment": 8.0,
                           "economy": 5.0, "access": 3.0},
        "cost_bn_per_year": 1.9, "feasibility": 50, "lead_years": 5,
        "phase": "Long-term (2033+)",
    },
    {
        "id": "rural_access", "name": "Rural Grid Extension & Off-Grid Last Mile",
        "short": "Rural Last-Mile Access", "category": "Access",
        "pillar_impacts": {"access": 20.0, "economy": 4.0,
                           "environment": 3.0, "security": 1.0},
        "cost_bn_per_year": 1.1, "feasibility": 60, "lead_years": 3,
        "phase": "Medium-term (2029-32)",
    },
    {
        "id": "regional_trade", "name": "CASA-1000 & Regional Power Trading",
        "short": "Regional Power Trading", "category": "Security",
        "pillar_impacts": {"security": 10.0, "economy": 6.0,
                           "environment": 6.0, "access": 5.0},
        "cost_bn_per_year": 1.4, "feasibility": 45, "lead_years": 5,
        "phase": "Long-term (2033+)",
    },
]

# Component column -> human label, for the diagnostics bar chart
COMPONENT_LABELS = {
    "sc_security_imp_dep":  "Import Dependence",
    "sc_security_gas_ss":   "Gas Self-Sufficiency",
    "sc_security_diversity": "Generation Diversity (1-HHI)",
    "sc_economy_grid_eff":  "Grid Efficiency (T&D)",
    "sc_economy_lng_price": "LNG Price Pressure",
    "sc_environment_re_share": "Renewable Generation Share",
    "sc_environment_co2_int":  "CO2 Intensity of Electricity",
    "sc_access_pc_elec":    "Per-Capita Electricity",
    "sc_access_coverage":   "Demand Coverage",
}

# Analytical elements of Question 8 (documentation aid)
ELEMENTS = [
    {"id": "E1", "title": "Pillar scorecard", "objective": 1,
     "what": "Latest vs 10-years-ago score for the four sustainability pillars"},
    {"id": "E2", "title": "Index trajectory", "objective": 1,
     "what": "Pillar scores and the weighted composite across the record"},
    {"id": "E3", "title": "Strategy value density", "objective": 2,
     "what": "Feasibility-discounted weighted impact per $bn/yr, ranked"},
    {"id": "E4", "title": "Cost-impact bubble map", "objective": 2,
     "what": "Each strategy: cost vs impact, sized by feasibility, in/out of package"},
    {"id": "E5", "title": "Pathway projection", "objective": 3,
     "what": "Composite index history continued under BAU / announced / optimal"},
    {"id": "E6", "title": "Pillar gain vs BAU", "objective": 3,
     "what": "Score points the optimal package adds per pillar at the horizon"},
    {"id": "E7", "title": "Component diagnostics", "objective": 1,
     "what": "All nine underlying 0-100 component scores, latest observation"},
]

# ══════════════════════ palette ══════════════════════
GREEN = "#10B981"
BLUE = "#00A6FB"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A78BFA"
TEAL = "#14B8A6"
CYAN = "#22D3EE"
SLATE = "#94A3B8"

PILLAR_COLOURS = {
    "security": BLUE, "economy": AMBER,
    "environment": GREEN, "access": PURPLE,
}
ACCENT = TEAL
