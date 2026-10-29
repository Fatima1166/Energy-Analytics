# Configuration for the Operational Bottlenecks dashboard (Q9)
#
# All analytics live in core/operational_bottlenecks.py.  This file only holds
# the visual palette and the family / series labels -- data, not logic.

DASHBOARD_TITLE = "Operational Bottlenecks in Fossil & Renewable Energy Supplies"
HISTORY_START = 2002
HISTORY_END = 2024
DEFAULT_BASE_YEAR = 2024
BASE_YEAR_MIN = 2008
BASE_YEAR_MAX = 2024

# ── Bottleneck families ──────────────────────────────────────────────────────
# The scorecard splits every choke point into one of three operational families.
FAMILIES = {
    "fossil":    "Fossil supply",
    "renewable": "Renewable supply",
    "delivery":  "Grid delivery",
}

FAMILY_COLORS = {
    "fossil":    "#F97316",   # orange
    "renewable": "#10B981",   # green
    "delivery":  "#00A6FB",   # blue
}

# ── Lines drawn in the utilisation chart ─────────────────────────────────────
# (scorecard column suffix, label shown in the legend, colour).  Labels stay
# short: the chart shares a row with another chart, so the legend has to fit.
CF_SERIES = [
    ("fossil_cf_pct",  "Fossil",           "#F97316"),
    ("hydel_cf_pct",   "Hydro",            "#00A6FB"),
    ("wind_cf_pct",    "Wind",             "#14B8A6"),
    ("solar_cf_pct",   "Solar",            "#F59E0B"),
    ("re_cf_pct",      "All renewables",   "#10B981"),
]

# ── Reference benchmark (drawn as a guide line; informational) ───────────────
BENCHMARK_FOSSIL_CF_PCT = 60.0   # what healthy fossil plant utilisation looks like

# ── Palette ──────────────────────────────────────────────────────────────────
GREEN  = "#10B981"
BLUE    = "#00A6FB"
AMBER   = "#F59E0B"
RED     = "#EF4444"
TEAL    = "#14B8A6"
ORANGE  = "#F97316"
SLATE   = "#64748B"
