# Configuration for the Operational Bottlenecks dashboard (Q9)
#
# All analytics live in core/operational_bottlenecks.py.  This file only holds
# the visual palette, family metadata and the reference benchmarks the sidebar
# exposes -- data, not logic.

DASHBOARD_TITLE = "Operational Bottlenecks in Fossil & Renewable Energy Supplies"
HISTORY_START = 2002
HISTORY_END = 2024
DEFAULT_BASE_YEAR = 2024
BASE_YEAR_MIN = 2008
BASE_YEAR_MAX = 2024

# ── Bottleneck families ──────────────────────────────────────────────────────
# The scorecard splits every choke point into one of three operational families.
FAMILIES = {
    "fossil":    "Fossil Supply",
    "renewable": "Renewable Supply",
    "delivery":  "Grid Delivery",
}

FAMILY_COLORS = {
    "fossil":    "#F97316",   # orange
    "renewable": "#10B981",   # green
    "delivery":  "#00A6FB",   # blue
}

FAMILY_ICONS = {
    "fossil":    "primary_energy",
    "renewable": "renewables",
    "delivery":  "supply",
}

# ── Generation sources shown in the utilisation chart ────────────────────────
# (scorecard column suffix, friendly label, colour)
CF_SERIES = [
    ("fossil_cf_pct",  "Thermal (Coal/Gas/Nuclear)", "#F97316"),
    ("hydel_cf_pct",   "Hydro",                      "#00A6FB"),
    ("wind_cf_pct",    "Wind",                       "#14B8A6"),
    ("solar_cf_pct",   "Solar",                      "#F59E0B"),
    ("re_cf_pct",      "All Renewables",             "#10B981"),
]

# ── Reference benchmarks (drawn as guide lines; informational) ───────────────
BENCHMARK_TD_LOSS_PCT = 15.0     # standard acceptable T&D loss ceiling
BENCHMARK_FOSSIL_CF_PCT = 60.0   # "target" thermal utilisation
BENCHMARK_RE_CF_PCT = 30.0       # typical blended RE capacity factor

# ── Palette ──────────────────────────────────────────────────────────────────
GREEN  = "#10B981"
BLUE    = "#00A6FB"
AMBER   = "#F59E0B"
RED     = "#EF4444"
PURPLE  = "#A78BFA"
TEAL    = "#14B8A6"
CYAN    = "#06B6D4"
ORANGE  = "#F97316"
ROSE    = "#F43F5E"
SLATE   = "#64748B"
