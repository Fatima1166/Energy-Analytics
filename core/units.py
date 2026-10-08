"""
core/units.py -- unit registry and conversion engine.

Data is stored in one base unit per domain (TOE, GWh, MW, BCF, t, USD).
The sidebar picks a display unit; values convert at render time as
value_display = value_base * display_factor(domain, unit).
"""

from __future__ import annotations

import math
from typing import Dict, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# 1. Domains and their sidebar options
# ---------------------------------------------------------------------------
DOMAIN_ORDER = ["energy", "electricity", "power", "gas", "emission", "economic"]

DOMAINS: Dict[str, dict] = {
    "energy": {
        "label": "Energy",
        "base": "TOE",
        "units": ["TOE", "MTOE", "KTOE"],
        "default": "TOE",
        "fixed": False,
        "note": "Primary energy supply, final consumption, losses, savings",
    },
    "electricity": {
        "label": "Electricity",
        "base": "GWh",
        "units": ["GWh", "TWh", "MWh"],
        "default": "GWh",
        "fixed": False,
        "note": "Generation, demand, imports, consumption, T&D losses",
    },
    "power": {
        "label": "Power",
        "base": "MW",
        "units": ["MW", "GW", "kW"],
        "default": "MW",
        "fixed": False,
        "note": "Installed / renewable capacity",
    },
    "gas": {
        "label": "Gas",
        "base": "BCF",
        "units": ["BCF", "TCF", "MMSCF"],
        "default": "BCF",
        "fixed": False,
        "note": "Gas production, consumption, reserves, LNG volume",
    },
    "emission": {
        "label": "Emission",
        "base": "t",
        "units": ["t", "Mt", "kt"],
        "default": "t",
        "fixed": False,
        "note": "CO2 emissions (mass of CO2)",
    },
    "economic": {
        "label": "Economic",
        "base": "USD",
        "units": ["USD", "%", "Persons"],
        "default": "USD",
        "fixed": True,
        "note": "Currency / ratio / head-count -- fixed, not converted",
    },
}

# ---------------------------------------------------------------------------
# 2. Factors:  value_in_base = value * _TO_BASE[unit]
# ---------------------------------------------------------------------------
_TO_BASE: Dict[str, float] = {
    # energy (base TOE)
    "TOE": 1.0, "KTOE": 1e3, "MTOE": 1e6,
    # electricity (base GWh)
    "GWh": 1.0, "TWh": 1e3, "MWh": 1e-3,
    # power (base MW)
    "MW": 1.0, "GW": 1e3, "kW": 1e-3,
    # gas (base BCF) -- MMSCF and MMCF are the same thing
    "BCF": 1.0, "TCF": 1e3, "MMSCF": 1e-3,
    # emission (base t)
    "t": 1.0, "kt": 1e3, "Mt": 1e6,
    # economic (fixed)
    "USD": 1.0, "%": 1.0, "Persons": 1.0,
}

_ALIASES: Dict[str, str] = {
    "MMCF": "MMSCF", "MMSCFD": "MMSCF", "MSCF": "MMSCF",
    "TONNE": "t", "TONNES": "t", "TON": "t", "TCO2": "t", "TCO₂": "t",
    "MILLION USD": "USD", "MUSD": "USD", "M USD": "USD",
    "PEOPLE": "Persons", "PERSON": "Persons",
    "TWH": "TWh", "GWH": "GWh", "MWH": "MWh",
    "KWH": "MWh", "KILOWATT HOUR": "MWh",
}

# case-insensitive lookup tables
_CASE_INDEX: Dict[str, str] = {k.upper(): k for k in _TO_BASE}
_ALIAS_INDEX: Dict[str, str] = {k.upper(): v for k, v in _ALIASES.items()}


def normalise(unit: Optional[str]) -> str:
    """Canonical spelling of a unit: 'TWH' -> 'TWh', 'MMCF' -> 'MMSCF', 'tonnes' -> 't'."""
    if unit is None:
        return ""
    raw = str(unit).strip()
    if raw in _TO_BASE:
        return raw
    key = raw.upper()
    if key in _CASE_INDEX:
        return _CASE_INDEX[key]
    if key in _ALIAS_INDEX:
        return _ALIAS_INDEX[key]
    for cfg in DOMAINS.values():
        for u in cfg["units"]:
            if u.upper() == key:
                return u
    return raw


def base_of(domain: str) -> str:
    """Canonical base (storage) unit of a domain."""
    return DOMAINS[domain]["base"]


def domain_of(unit: str) -> Optional[str]:
    """Which domain does a unit belong to (best effort)?"""
    u = normalise(unit)
    for dom, cfg in DOMAINS.items():
        if u in cfg["units"]:
            return dom
    for dom, cfg in DOMAINS.items():
        if u.upper() == cfg["base"].upper():
            return dom
    return None


# ---------------------------------------------------------------------------
# 3. Conversion helpers
# ---------------------------------------------------------------------------
def display_factor(domain: str, unit: str) -> float:
    """value_unit = value_base * display_factor(domain, unit)."""
    u = normalise(unit)
    if u not in _TO_BASE:
        return 1.0
    if DOMAINS.get(domain, {}).get("fixed"):
        return 1.0
    return 1.0 / _TO_BASE[u]


def factor(from_unit: str, to_unit: str) -> float:
    """Generic multiplier: value_to = value_from * factor(from_unit, to_unit)."""
    a, b = normalise(from_unit), normalise(to_unit)
    if a not in _TO_BASE or b not in _TO_BASE:
        return 1.0
    return _TO_BASE[a] / _TO_BASE[b]


def convert(value, from_unit: str, to_unit: str) -> float:
    """Convert a single (already numeric) value between any two known units."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    return v * factor(from_unit, to_unit)


def _scale(value, unit: str, to_display: bool) -> float:
    """Shared numeric core: display = base / to_base[unit]; base = display * to_base[unit]."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    f = _TO_BASE.get(unit, 1.0)
    return v / f if to_display else v * f


def from_base(value, unit: str) -> float:
    """Base unit -> display unit (e.g. 179800380 t -> 179.8 Mt)."""
    return _scale(value, normalise(unit), True)


def base_to(value, unit: str) -> float:
    """Inverse of from_base (display unit -> domain base unit)."""
    return _scale(value, normalise(unit), False)


def to_base(value, unit: str) -> float:
    """Alias of base_to, kept for readability in query code."""
    return base_to(value, unit)


def from_base_series(series, unit: str):
    """Vectorised ``from_base`` for a pandas Series / column."""
    f = _TO_BASE.get(normalise(unit), 1.0)
    return pd.to_numeric(series, errors="coerce") * (1.0 / f)


def to_base_series(series, unit: str):
    """Vectorised ``base_to`` for a pandas Series / column."""
    f = _TO_BASE.get(normalise(unit), 1.0)
    return pd.to_numeric(series, errors="coerce") * f


def convert_series(series, from_unit: str, to_unit: str):
    return pd.to_numeric(series, errors="coerce") * factor(from_unit, to_unit)


def unit_for(units: Optional[dict], domain: str) -> str:
    """Read the selected display unit for a domain out of the prefs dict."""
    if units:
        chosen = units.get(domain)
        if chosen:
            return normalise(chosen)
    return DOMAINS[domain]["default"]


# ---------------------------------------------------------------------------
# 4. Formatting
# ---------------------------------------------------------------------------
def fmt(value, decimals: Optional[int] = None) -> str:
    """Human friendly number formatting that survives unit changes."""
    if value is None:
        return "--"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(f) or math.isinf(f):
        return "--"
    if decimals is not None:
        return f"{f:,.{decimals}f}"
    a = abs(f)
    if a == 0:
        return "0"
    if a >= 1e9 or a < 1e-4:
        return f"{f:.3e}"
    if a >= 1000:
        return f"{f:,.0f}"
    if a >= 100:
        return f"{f:,.1f}"
    if a >= 1:
        return f"{f:,.2f}"
    return f"{f:,.4f}"


def fmt_unit(value, unit: str, decimals: Optional[int] = None) -> str:
    """`123.4 Mt` style string."""
    return f"{fmt(value, decimals)} {normalise(unit)}".strip()


# ---------------------------------------------------------------------------
# 5. Formula documentation
# ---------------------------------------------------------------------------
def _g(x: float) -> str:
    return f"{x:g}"


def formula(domain: str, unit: str) -> str:
    """Human readable formula for one display unit, e.g. 'Mt = t x 1e-06'."""
    u = normalise(unit)
    cfg = DOMAINS[domain]
    if cfg.get("fixed"):
        return f"{u} (fixed -- no conversion)"
    f = display_factor(domain, u)
    if f == 1.0:
        return f"{u} = {cfg['base']} (stored unit)"
    return f"{u} = {cfg['base']} x {_g(f)}"


def conversion_rows(domain: str):
    """[(unit, display_factor, formula), ...] for one domain."""
    cfg = DOMAINS[domain]
    return [(u, display_factor(domain, u), formula(domain, u)) for u in cfg["units"]]


def all_formulas(units: Optional[dict] = None) -> Dict[str, str]:
    """{domain_label: active formula} for the current selection."""
    out = {}
    for dom in DOMAIN_ORDER:
        out[DOMAINS[dom]["label"]] = formula(dom, unit_for(units, dom))
    return out


# ---------------------------------------------------------------------------
# 6. Database metadata bridge
# ---------------------------------------------------------------------------
_Q_UNIT_METADATA = """
SELECT domain, table_name, column_name, base_unit, display_unit,
       conversion_factor, is_default
FROM dim_unit_metadata
ORDER BY domain, table_name, column_name, conversion_factor;
"""


def db_metadata() -> pd.DataFrame:
    """Read `dim_unit_metadata`; returns an empty frame if MySQL is unavailable."""
    try:
        from config.database import run_query

        df = run_query(_Q_UNIT_METADATA)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def metadata_mismatches(meta: pd.DataFrame) -> pd.DataFrame:
    """Rows of `dim_unit_metadata` whose factor disagrees with this module."""
    if meta is None or meta.empty:
        return pd.DataFrame()
    rows = []
    for _, r in meta.iterrows():
        dom = str(r.get("domain", "")).strip().lower()
        shown = str(r.get("display_unit", "")).strip()
        declared = float(r.get("conversion_factor") or 0)
        if dom not in DOMAINS:
            continue
        expected = display_factor(dom, shown)
        if abs(declared - expected) > max(1e-12, abs(expected) * 1e-6):
            rows.append({
                "domain": dom,
                "table_name": r.get("table_name"),
                "column_name": r.get("column_name"),
                "display_unit": shown,
                "db_factor": declared,
                "app_factor": expected,
            })
    return pd.DataFrame(rows)


def defaults() -> Dict[str, str]:
    """Default display unit per domain == the unit the data is STORED in."""
    return {dom: DOMAINS[dom]["default"] for dom in DOMAIN_ORDER}
