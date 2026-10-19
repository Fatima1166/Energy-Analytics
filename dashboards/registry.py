import importlib

# `units` lists the unit families a dashboard actually renders.  The sidebar
# unit selector shows exactly these, in this order, so a dashboard is never
# offered a unit it does not use.
DASHBOARDS = [
    {
        "key": "home",
        "label": "Energy Overview",
        "title": "Pakistan Energy Outlook -- Overview",
        "subtitle": "Home  •  National Energy Snapshot, Fuel Mix & Emissions at a Glance",
        "icon": "overview",
        "module": "dashboards.home_energy_overview.page",
        # Landing page respects the global slicer for its headline stats
        "units": ["energy", "electricity", "emission"],
    },
    {
        "key": "q1",
        "label": "Parameter Relationships",
        "title": "What have been the relationships among different parameters of energy over a given period of time? What are the predicted values of these parameters based on the what-if analysis?",
        "subtitle": "Question 1 Analysis  •  Correlation Web, Rolling Stability, Driver Elasticities & What-If Forecasts (1999–2035)",
        "icon": "data",
        "module": "dashboards.q1_parameter_relationships.page",
        # Supply / consumption (TOE), electricity flows (GWh), capacity (MW),
        # gas balance (BCF), CO2 (t)
        "units": ["energy", "electricity", "power", "gas", "emission"],
    },
    {
        "key": "q2",
        "label": "Renewable Scenarios",
        "title": "What are the potential outcomes of installing renewable energy sources in different energy scenarios?",
        "subtitle": "Question 2 Analysis  •  Comparative Scenario Simulation: Generation Mix, CO₂ Avoidance & LNG Savings (1999–2035)",
        "icon": "renewables",
        "module": "dashboards.q2_renewable_scenarios.page",
        # Generation mix (GWh), capacity (MW), CO₂ (t)
        "units": ["electricity", "power", "emission"],
    },
    {
        "key": "q3",
        "label": "Target Bottlenecks",
        "title": "What are the bottlenecks in achieving planned targets?",
        "subtitle": "Question 3 Analysis  •  Losses, Import Dependence, Renewable Share & Gas Self-Sufficiency vs Benchmarks (2002–2035)",
        "icon": "warning",
        "module": "dashboards.q3_target_bottlenecks.page",
        # Primary energy / losses (TOE) and the gas balance (BCF)
        "units": ["energy", "gas"],
    },
    {
        "key": "q4",
        "label": "Forecasted Demand",
        "title": "What is forecasted energy demand?",
        "subtitle": "Question 4 Analysis  •  Reported Demand (1999–2024), GDP & Population Drivers, Low/Base/High Scenarios to 2035",
        "icon": "demand",
        "module": "dashboards.q4_forecast_demand.page",
        # Final energy demand (TOE), grid / sector / province demand (GWh)
        "units": ["energy", "electricity"],
    },
    {
        "key": "q5",
        "label": "Forecasted Supply",
        "title": "What is forecasted energy supply?",
        "subtitle": "Question 5 Analysis  •  Primary Supply & Generation Outlook, Fuel Mix Scenarios to 2035, Capacity Expansion & Adequacy",
        "icon": "supply",
        "module": "dashboards.q5_forecast_supply.page",
        # Primary supply (TOE), generation (GWh), capacity (MW)
        "units": ["energy", "electricity", "power"],
    },
    {
        "key": "q6",
        "label": "Supply Chain Optimization",
        "title": "What is the optimal utilization of fuel and renewable energy supply chains?",
        "subtitle": "Question 6 Analysis  •  Supply Chain Efficiency Scorecard, T&D Losses, Import Dependency, RE Utilisation & Gas Self-Sufficiency (1999–2024)",
        "icon": "supply",
        "module": "dashboards.q6_supply_chain_optimization.page",
        # Primary supply (TOE), generation (GWh), capacity (MW), gas (BCF)
        "units": ["energy", "electricity", "power", "gas"],
    },
    {
        "key": "q7",
        "label": "Forecasted Producer Cost",
        "title": "What is the forecasted cost of energy power producers?",
        "subtitle": "Question 7 Analysis  •  Purchase-Cost Bill by Technology, Deployment-Case Scenarios, Fuel-Price Sensitivity & Cost Avoidance (1999–2035)",
        "icon": "cost",
        "module": "dashboards.q7_forecast_cost.page",
        # Producer purchase cost (constant USD)
        "units": ["cost"],
    },
    {
        "key": "q8",
        "label": "Sustainable Strategy",
        "title": "What optimal strategy may be opted to make energy development sustainable?",
        "subtitle": "Question 8 Analysis  •  Four-Pillar Sustainability Index, Knapsack Strategy Package & BAU / Announced / Optimal Pathways to 2035",
        "icon": "sustainability",
        "module": "dashboards.q8_sustainable_strategy.page",
        # Index scores are unitless; the ledger budgets are constant USD
        "units": ["cost"],
    },
    {
        "key": "q9",
        "label": "Operational Bottlenecks",
        "title": "What are the operational bottlenecks in fossil and renewable energy supplies?",
        "subtitle": "Question 9 Analysis  •  Capacity-Factor, Gas-Supply, Import-Dependence & T&D Loss Bottleneck Scorecard (2002–2024)",
        "icon": "warning",
        "module": "dashboards.q9_operational_bottlenecks.page",
        # Generation (GWh), capacity (MW), gas balance (BCF)
        "units": ["electricity", "power", "gas"],
    },
    {
        "key": "q10",
        "label": "Optimal Resource Allocation",
        "title": "What is optimal resource allocation for sustainable development?",
        "subtitle": "Question 10 Analysis  •  Constrained Water-Filling Optimiser: Least-Cost · Low-Carbon · Secure Generation Allocation with Sector Flows (2024–2035)",
        "icon": "sustainability",
        "module": "dashboards.q10_resource_allocation.page",
        # Allocation (GWh), purchase cost (USD), CO₂ (t), domestic gas (BCF)
        "units": ["electricity", "cost", "emission", "gas"],
    },
]


def load_dashboard_module(module_path: str):
    """Import and return the dashboard module itself."""
    return importlib.import_module(module_path)


def load_dashboard(module_path: str):
    """Dynamically import module and return its render() function."""
    return getattr(load_dashboard_module(module_path), "render")
