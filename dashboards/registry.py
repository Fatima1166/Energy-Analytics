import importlib

# `units` lists the unit families a dashboard actually renders.  The sidebar
# unit selector shows exactly these, in this order, so a dashboard is never
# offered a unit it does not use.
DASHBOARDS = [
    {
        "key": "home",
        "label": "Energy Overview",
        "title": "Pakistan Energy Outlook — Overview",
        "subtitle": "National Energy Snapshot, Fuel Mix & Emissions at a Glance",
        "icon": "overview",
        "module": "dashboards.home_energy_overview.page",
        # Landing page respects the global slicer for its headline stats
        "units": ["energy", "electricity", "emission"],
    },
    {
        "key": "q1",
        "label": "Parameter Relationships",
        "title": "What have been the relationships among different parameters of energy over a given period of time? What are the predicted values of these parameters based on the what-if analysis?",
        "subtitle": "Question 1 Analysis  •  Correlation Web, Top Pairs, Pair Explorer, Rolling Stability & What-if Forecast (1999–2035)",
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
        "subtitle": "Question 2  •  Five clean-energy plans compared: power mix, CO₂ kept out of the air, and gas imports saved (2000–2035)",
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
        "subtitle": "Question 4  •  Where demand has been, the three paths it can take to 2035, and how far to trust the guess",
        "icon": "demand",
        "module": "dashboards.q4_forecast_demand.page",
        # Final energy demand (TOE) and grid / sector demand (GWh)
        "units": ["energy", "electricity"],
    },
    {
        "key": "q5",
        "label": "Forecasted Supply",
        "title": "What is forecasted energy supply?",
        "subtitle": "Question 5  •  Where supply has been, the three paths it can take to 2035, and whether it keeps up with demand",
        "icon": "supply",
        "module": "dashboards.q5_forecast_supply.page",
        # Total primary supply (TOE) and electricity generated (GWh)
        "units": ["energy", "electricity"],
    },
    {
        "key": "q6",
        "label": "Supply Chain Optimization",
        "title": "What is the optimal utilization of fuel and renewable energy supply chains?",
        "subtitle": "Question 6  •  How well the fuel and clean-energy chains are used, scored four ways, year by year",
        "icon": "supply",
        "module": "dashboards.q6_supply_chain_optimization.page",
        # Electricity generated and lost (GWh), clean plant built (MW), gas (BCF)
        "units": ["electricity", "power", "gas"],
    },
    {
        "key": "q7",
        "label": "Forecasted Producer Cost",
        "title": "What is the forecasted cost of energy power producers?",
        "subtitle": "Question 7  •  What producers were paid, what the bill points to by 2035, and which assumption moves it",
        "icon": "cost",
        "module": "dashboards.q7_forecast_cost.page",
        # Producer purchase cost (constant USD)
        "units": ["cost"],
    },
    {
        "key": "q8",
        "label": "Sustainable Strategy",
        "title": "What optimal strategy may be opted to make energy development sustainable?",
        "subtitle": "Question 8 Analysis  •  What the Four Pillars Score Today, "
                    "Which Measures Are Worth the Money, and Where They Lead by 2035",
        "icon": "sustainability",
        "module": "dashboards.q8_sustainable_strategy.page",
        # Index scores are unitless; the plan's yearly costs are constant USD
        "units": ["cost"],
    },
    {
        "key": "q9",
        "label": "Operational Bottlenecks",
        "title": "What are the operational bottlenecks in fossil and renewable energy supplies?",
        "subtitle": "Question 9  •  Which choke points limit fossil and renewable "
                   "supply, how badly each one binds, and for how long (2002–2024)",
        "icon": "warning",
        "module": "dashboards.q9_operational_bottlenecks.page",
        # Generation (GWh), capacity (MW), gas balance (BCF)
        "units": ["electricity", "power", "gas"],
    },
    {
        "key": "q10",
        "label": "Optimal Resource Allocation",
        "title": "What is optimal resource allocation for sustainable development?",
        "subtitle": "Question 10  •  How the 2035 power need is split across "
                    "resources for less cost, less CO₂ and less bought fuel "
                    "(latest reported mix → 2035)",
        "icon": "sustainability",
        "module": "dashboards.q10_resource_allocation.page",
        # Allocation (GWh), purchase cost (USD), CO₂ (t)
        "units": ["electricity", "cost", "emission"],
    },
]


def load_dashboard_module(module_path: str):
    """Import and return the dashboard module itself."""
    return importlib.import_module(module_path)


def load_dashboard(module_path: str):
    """Dynamically import module and return its render() function."""
    return getattr(load_dashboard_module(module_path), "render")
