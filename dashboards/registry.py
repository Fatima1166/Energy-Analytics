import importlib

# `units` lists the unit families a dashboard actually renders.  The sidebar
# unit selector shows exactly these, in this order, so a dashboard is never
# offered a unit it does not use.
DASHBOARDS = [
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
]


def load_dashboard_module(module_path: str):
    """Import and return the dashboard module itself."""
    return importlib.import_module(module_path)


def load_dashboard(module_path: str):
    """Dynamically import module and return its render() function."""
    return getattr(load_dashboard_module(module_path), "render")
