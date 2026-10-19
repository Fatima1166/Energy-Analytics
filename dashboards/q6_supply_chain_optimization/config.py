# Configuration for the Supply Chain Optimization dashboard (Q6)

DASHBOARD_TITLE = "Optimal Fuel & Renewable Energy Supply Chain Utilization"
HISTORY_START = 1999
HISTORY_END = 2024
DEFAULT_HORIZON = 2035

# ── Fuel supply chain efficiency benchmarks ──────────────────────────────────
# Based on IEA / Pakistan Energy Yearbook guidelines
BENCHMARK_TRANSMISSION_EFFICIENCY = 85.0   # % target T&D efficiency (15% loss)
BENCHMARK_IMPORT_DEPENDENCY_MAX   = 30.0   # % max acceptable import share
BENCHMARK_RE_UTILISATION_MIN      = 75.0   # % min capacity utilisation (RE)
BENCHMARK_FUEL_WASTE_MAX           = 15.0   # % max allowable supply chain loss
BENCHMARK_GAS_SELFSUFFICIENCY      = 70.0   # % domestic gas vs total gas demand

# Renewable utilisation factors (capacity factor proxies, %)
CF_SOLAR   = 18.0
CF_WIND    = 30.0
CF_HYDRO   = 45.0
CF_NUCLEAR = 85.0
CF_THERMAL = 60.0

# Base supply chain efficiency score weights (summing to 1.0)
SCE_WEIGHTS = {
    "transmission_efficiency": 0.25,
    "re_utilisation":          0.25,
    "import_dependency":       0.20,
    "fuel_waste_reduction":    0.20,
    "gas_self_sufficiency":    0.10,
}

# ── Optimization Strategies ──────────────────────────────────────────────────
STRATEGY_PRESETS = {
    "Balanced Optimization": {
        "re_target": 40,
        "fuel_target": 60,
        "priority": "Balanced (Equal Emphasis)",
        "loss_target": 15.0,
        "desc": "Balanced portfolio targeting 40% renewable energy and 15% transmission losses.",
    },
    "Accelerated Clean Transition": {
        "re_target": 60,
        "fuel_target": 40,
        "priority": "Renewable & Clean Transition",
        "loss_target": 13.0,
        "desc": "Aggressive scaling of solar, wind and hydro to 60% with modernised low-loss grid.",
    },
    "Aggressive Net-Zero Ambition": {
        "re_target": 75,
        "fuel_target": 25,
        "priority": "Renewable & Clean Transition",
        "loss_target": 11.0,
        "desc": "Deep decarbonization with 75% clean energy, minimizing thermal generation.",
    },
    "Energy Security & Import Reduction": {
        "re_target": 50,
        "fuel_target": 50,
        "priority": "Energy Security (Import & Gas Focus)",
        "loss_target": 14.0,
        "desc": "Maximized reliance on indigenous gas, hydro, and domestic renewables to curb LNG imports.",
    },
    "Grid Efficiency & Loss Minimization": {
        "re_target": 45,
        "fuel_target": 55,
        "priority": "Grid & Transmission Efficiency",
        "loss_target": 10.0,
        "desc": "Infrastructure overhaul focusing on cutting T&D losses to international standards (10%).",
    },
    "Custom Policy Mix": {
        "re_target": 40,
        "fuel_target": 60,
        "priority": "Balanced (Equal Emphasis)",
        "loss_target": 15.0,
        "desc": "User-defined custom supply chain targets and weighting parameters.",
    },
}

# ── Priority Weights Presets ──────────────────────────────────────────────────
PRIORITY_WEIGHTS = {
    "Balanced (Equal Emphasis)": {
        "transmission_efficiency": 0.25,
        "re_utilisation":          0.20,
        "import_dependency":       0.20,
        "fuel_waste_reduction":    0.20,
        "gas_self_sufficiency":    0.15,
    },
    "Energy Security (Import & Gas Focus)": {
        "transmission_efficiency": 0.15,
        "re_utilisation":          0.10,
        "import_dependency":       0.35,
        "fuel_waste_reduction":    0.10,
        "gas_self_sufficiency":    0.30,
    },
    "Grid & Transmission Efficiency": {
        "transmission_efficiency": 0.35,
        "re_utilisation":          0.10,
        "import_dependency":       0.15,
        "fuel_waste_reduction":    0.30,
        "gas_self_sufficiency":    0.10,
    },
    "Renewable & Clean Transition": {
        "transmission_efficiency": 0.20,
        "re_utilisation":          0.40,
        "import_dependency":       0.15,
        "fuel_waste_reduction":    0.15,
        "gas_self_sufficiency":    0.10,
    },
}

# ── Fuel Stream Mapping to Database source_name ──────────────────────────────
FUEL_STREAM_MAP = {
    "Natural Gas": ["Gas"],
    "LNG Imports": ["LNG Imports"],
    "Coal": ["Coal"],
    "Oil & Petroleum": ["Oil", "LPG"],
    "Nuclear": ["Nuclear Electricity"],
    "Hydro": ["Hydro Electricity"],
    "Renewables": ["Renewable Electricity"],
    "Imported Power": ["Imported Electricity"],
}

# ── Palette ─────────────────────────────────────────────────────────────────
GREEN   = "#10B981"
BLUE    = "#00A6FB"
AMBER   = "#F59E0B"
RED     = "#EF4444"
PURPLE  = "#A78BFA"
TEAL    = "#14B8A6"
CYAN    = "#06B6D4"
ORANGE  = "#F97316"
ROSE    = "#F43F5E"
LIME    = "#84CC16"
