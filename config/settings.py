import os

# ---------- App-level settings ----------
APP_TITLE = "Pakistan National Energy Analytics Platform"
APP_SUBTITLE = "Enterprise Decision-Grade Modeling, Scenario Projections & Optimization (1999–2035)"
APP_ICON = "⚡"

# Which login guards this dashboard:
#   "react"     -> the React portal on http://localhost:5173 is the login (default)
#   "streamlit" -> the built-in Streamlit login gate protects port 8501 directly
LOGIN_MODE = os.getenv("LOGIN_MODE", "react").strip().lower()

# ---------- Color palette ----------
COLORS = {
    "primary":    "#2E8B57",
    "green":      "#2ECC71",
    "blue":       "#00A6FB",
    "orange":     "#F4A300",
    "purple":     "#9B59B6",
    "red":        "#E74C3C",
    "teal":       "#1ABC9C",
    "gray":       "#4A4A4A",
    "bg_dark":    "#0E1117",
    "bg_card":    "#1A1D24",
    "border":     "#2A2F3A",
    "text":       "#FFFFFF",
    "text_muted": "#8B95A7",
}

# ---------- Emission factors (tCO2/MWh) based on dim_emission_factor / IPCC ----------
EMISSION_FACTORS = {
    "coal": 0.9,
    "gas":  0.4,
    "oil":  0.7,
    "hydro": 0.0,
    "nuclear": 0.0,
    "renewables": 0.0,
}

# ---------- Economic parameters ----------
# Marginal LNG import fuel savings per TWh of Gas generation avoided (~$75M USD / TWh)
LNG_SAVING_PER_GAS_TWH_MUSD = 75.0

# ---------- Scenario growth assumptions (% per year for solar & wind) ----------
SCENARIOS = {
    "Baseline": {
        "label": "Baseline",
        "solar": 2.0,
        "wind": 2.0,
        "hydro": 1.0,
        "other": 1.0,
        "desc": "Status-quo / historical policy continuation (2% annual RE growth)",
        "color": "#8B95A7",
    },
    "Moderate": {
        "label": "Moderate",
        "solar": 8.0,
        "wind": 8.0,
        "hydro": 2.0,
        "other": 3.0,
        "desc": "Balanced growth across clean sources (8% solar & wind)",
        "color": "#00A6FB",
    },
    "Accelerated": {
        "label": "Accelerated",
        "solar": 15.0,
        "wind": 15.0,
        "hydro": 3.0,
        "other": 5.0,
        "desc": "Aggressive clean transition targeting high decarbonisation (15% growth)",
        "color": "#2ECC71",
    },
    "Solar-led": {
        "label": "Solar-led",
        "solar": 25.0,
        "wind": 5.0,
        "hydro": 1.5,
        "other": 2.0,
        "desc": "Priority deployment of utility-scale & distributed solar (25% solar growth)",
        "color": "#F4A300",
    },
    "Wind-led": {
        "label": "Wind-led",
        "solar": 5.0,
        "wind": 25.0,
        "hydro": 1.5,
        "other": 2.0,
        "desc": "Major exploitation of southern & coastal wind corridors (25% wind growth)",
        "color": "#9B59B6",
    },
}