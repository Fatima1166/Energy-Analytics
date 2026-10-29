"""
core/bottleneck_metrics.py -- analytical engine for Q3 (Bottlenecks in Achieving
Planned Targets).

Design rules that fix the previous dashboard's problems
-------------------------------------------------------
1. ONE reference year.  Every KPI is evaluated for the same year so
   year-on-year comparisons and gap rankings are consistent.  Previously K1 was
   read from 2019, K2/K3 from 2024 and K4 from 2018, all in the same card row.

2. HONEST data provenance.  Each annual point is tagged:
       Actual        -- a reported value from the database
       Missing       -- the source row is absent, so the year shows blank
       Projected     -- modelled forward beyond the last reported year
   A gap is never silently filled with 0 and never carried over from another
   year: a value only ever appears under the year that produced it.

3. 2035 horizon.  Every series runs 2002 -> 2035 so the charts answer the
   question for the planned-target horizon, and the actual/projected boundary
   is drawn explicitly.

4. Direction-aware targets.  Being *below* a "lower is better" target is
   success, not a 30pp failure.

All values stay in database base units (TOE, GWh, BCF, MW); unit conversion is
the caller's job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from core.targets import (
    KPI_SPEC,
    achievement_pct,
    on_track,
    severity,
    signed_gap,
)

# ── Provenance tags ─────────────────────────────────────────────────────────
ACTUAL = "Actual"
ESTIMATED = "Estimated"
PROJECTED = "Projected"
MISSING = "Missing"          # Power BI style blank — source row absent

PROVENANCE_COLORS = {
    ACTUAL: "#10B981",
    ESTIMATED: "#F59E0B",
    PROJECTED: "#00A6FB",
    MISSING: "#64748B",
}

HISTORY_START = 2002
LAST_REPORTED_IMPORT_YEAR = 2022      # fact_primary_energy_supply import rows stop here (LNG rows FY2022-23 included in the current dump)
HISTORY_END = 2024                    # last year with real generation/supply data
DEFAULT_PROJECT_END = 2035


def _num(value) -> float:
    """None / NaN / '' safe float."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if out != out else out


def _safe_div(a: float, b: float, default: float = 0.0) -> float:
    return (a / b) if b else default


# ══════════════════════════════════════════════════════════════════════════
#  1. Historical annual series
# ══════════════════════════════════════════════════════════════════════════

def build_annual_series(overview_df: pd.DataFrame,
                        primary_df: pd.DataFrame,
                        re_df: pd.DataFrame,
                        gas_df: pd.DataFrame,
                        project_end: int = DEFAULT_PROJECT_END) -> pd.DataFrame:
    """
    Combine the four source tables into one tidy annual frame, 2002 -> project_end.

    Columns
    -------
    calendar_year, supply_toe, import_toe, import_pct, losses_toe, losses_pct,
    td_losses_toe, re_gen_gwh, total_gen_gwh, re_share_pct,
    gas_production_bcf, gas_consumption_bcf, gas_self_suff_pct,
    sources  (list of provenance tags that contributed to the row)
    """
    years = list(range(HISTORY_START, project_end + 1))
    frame = pd.DataFrame({"calendar_year": years})

    # ── primary supply + import dependence ────────────────────────────────
    # Imported energy = "LNG Imports" + "Imported Electricity" (the only two
    # genuinely imported sources in dim_energy_source).  We use the
    # `imports_toe` column as the authoritative measure and fall back to
    # `supply_toe` where that column is NULL, which is why the earlier
    # "source_name contains import|lng" test was used -- but it is applied to a
    # wider set of names so LNG cannot be missed.
    IMPORT_SOURCE_NAMES = {"lng imports", "imported electricity", "imports", "lng"}

    if primary_df is not None and not primary_df.empty:
        p = primary_df.copy()
        p["calendar_year"] = pd.to_numeric(p["calendar_year"], errors="coerce")
        p = p.dropna(subset=["calendar_year"])
        p["calendar_year"] = p["calendar_year"].astype(int)
        # No fillna: a NULL cell is a year the source did not report, and a zero
        # here would read back as "imported nothing that year".
        p["supply_toe"] = pd.to_numeric(p.get("supply_toe"), errors="coerce")
        p["imports_toe"] = pd.to_numeric(p.get("imports_toe"), errors="coerce")

        name = p.get("source_name", pd.Series("", index=p.index)).astype(str).str.strip().str.lower()
        p["_is_import"] = name.isin(IMPORT_SOURCE_NAMES)

        # Imported volume: prefer the explicit imports column, else the supply
        # column of that same import row.  Rows that are not an import source
        # carry no evidence either way, so they stay blank rather than 0 -- the
        # sum of a year with no import row must be blank, not "0 toe imported".
        p["_import_val"] = p["imports_toe"].where(p["imports_toe"] > 0, p["supply_toe"])
        p.loc[~p["_is_import"], "_import_val"] = float("nan")

        agg = p.groupby("calendar_year").agg(
            supply_toe=("supply_toe", lambda s: s.sum(min_count=1)),
            import_toe=("_import_val", lambda s: s.sum(min_count=1)),
        ).reset_index()
        agg["import_pct"] = [
            _safe_div(i, s, float("nan")) * 100.0
            for i, s in zip(agg["import_toe"], agg["supply_toe"])
        ]
        frame = frame.merge(agg, on="calendar_year", how="left")

    for col in ("supply_toe", "import_toe", "import_pct"):
        if col not in frame.columns:
            frame[col] = float("nan")

    # ── losses ────────────────────────────────────────────────────────────
    if overview_df is not None and not overview_df.empty:
        o = overview_df.copy()
        o["calendar_year"] = pd.to_numeric(o["calendar_year"], errors="coerce")
        o = o.dropna(subset=["calendar_year"])
        o["calendar_year"] = o["calendar_year"].astype(int)
        for src, dst in (("total_primary_supply_toe", "_ov_supply"),
                         ("total_losses_toe", "losses_toe"),
                         ("td_losses_toe", "td_losses_toe")):
            o[dst] = pd.to_numeric(o.get(src), errors="coerce")
        o["losses_pct"] = [
            _safe_div(l, s, float("nan")) * 100.0
            for l, s in zip(o["losses_toe"], o["_ov_supply"])
        ]
        frame = frame.merge(
            o[["calendar_year", "losses_toe", "td_losses_toe", "losses_pct"]],
            on="calendar_year", how="left",
        )

    for col in ("losses_toe", "td_losses_toe", "losses_pct"):
        if col not in frame.columns:
            frame[col] = float("nan")

    # ── generation mix / renewable share ──────────────────────────────────
    if re_df is not None and not re_df.empty:
        r = re_df.copy()
        r["calendar_year"] = pd.to_numeric(r["calendar_year"], errors="coerce")
        r = r.dropna(subset=["calendar_year"])
        r["calendar_year"] = r["calendar_year"].astype(int)
        gen_cols = ["gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
                    "gen_other_renewables_gwh", "gen_coal_gwh", "gen_gas_gwh",
                    "gen_nuclear_gwh"]
        re_names = {"gen_solar_gwh", "gen_wind_gwh", "gen_hydro_gwh",
                    "gen_other_renewables_gwh"}
        # A fuel column the record never filled is an absent source, not a zero:
        # dropped before summing.  A year that leaves a reported fuel blank has no
        # total either (1999 reports no coal, gas or nuclear row).
        for c in gen_cols:
            r[c] = pd.to_numeric(r.get(c), errors="coerce")
        gen_cols = [c for c in gen_cols if r[c].notna().any()]
        # picked by name, never by position: dropping an absent fuel must not
        # slide coal up into the renewable slice
        re_part = [c for c in gen_cols if c in re_names]
        r["re_gen_gwh"] = (r[re_part].sum(axis=1, min_count=len(re_part))
                           if re_part else float("nan"))
        r["total_gen_gwh"] = r[gen_cols].sum(axis=1, min_count=len(gen_cols))
        r["re_share_pct"] = [
            _safe_div(a, b, float("nan")) * 100.0
            for a, b in zip(r["re_gen_gwh"], r["total_gen_gwh"])
        ]
        frame = frame.merge(
            r[["calendar_year", "re_gen_gwh", "total_gen_gwh", "re_share_pct"]],
            on="calendar_year", how="left",
        )

    for col in ("re_gen_gwh", "total_gen_gwh", "re_share_pct"):
        if col not in frame.columns:
            frame[col] = float("nan")

    # ── gas balance ───────────────────────────────────────────────────────
    if gas_df is not None and not gas_df.empty:
        g = gas_df.copy()
        g["calendar_year"] = pd.to_numeric(g["calendar_year"], errors="coerce")
        g = g.dropna(subset=["calendar_year"])
        g["calendar_year"] = g["calendar_year"].astype(int)
        g["gas_production_bcf"] = pd.to_numeric(g.get("production_bcf"), errors="coerce")
        g["gas_consumption_bcf"] = pd.to_numeric(g.get("consumption_bcf"), errors="coerce")
        g["gas_self_suff_pct"] = [
            _safe_div(p, c, float("nan")) * 100.0
            for p, c in zip(g["gas_production_bcf"], g["gas_consumption_bcf"])
        ]
        frame = frame.merge(
            g[["calendar_year", "gas_production_bcf", "gas_consumption_bcf",
               "gas_self_suff_pct"]],
            on="calendar_year", how="left",
        )

    for col in ("gas_production_bcf", "gas_consumption_bcf", "gas_self_suff_pct"):
        if col not in frame.columns:
            frame[col] = float("nan")

    return frame.sort_values("calendar_year").reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════
#  2. Trend helpers
# ══════════════════════════════════════════════════════════════════════════

def _cagr(first: float, last: float, periods: int) -> float:
    """Compound annual growth rate in %, from `first` to `last` over `periods`."""
    if periods <= 0 or first is None or last is None:
        return 0.0
    if first <= 0 or last <= 0:
        return 0.0
    return ((last / first) ** (1.0 / periods) - 1.0) * 100.0


def _recent_window(series: pd.Series, n: int = 5) -> pd.Series:
    """Last `n` non-NaN observations of a series."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    return s.tail(n)


# ══════════════════════════════════════════════════════════════════════════
#  3. Forward fill + projection to the horizon
# ══════════════════════════════════════════════════════════════════════════

def extend_to_horizon(frame: pd.DataFrame,
                      project_end: int = DEFAULT_PROJECT_END,
                      gas_to_2035: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Fill every metric from its last reported year through `project_end` and tag
    each row's provenance.

    Rules
    -----
    * primary supply      : geometric trend of the last 5 reported years
    * import dependence   : ratio trend fitted on the years that actually
                            report imports (2014-2018), then held to a
                            documented ceiling; 2019-2024 is left blank because
                            the source rows are absent, 2025+ is ``Projected``.
    * losses %            : 5-year average level with the observed trend damped
    * renewable share     : driven by the generation-mix projection
    * gas                 : production decline and consumption growth extended
                            separately so the widening deficit is visible

    Adds the column ``sources`` = the provenance tags present in that row, and
    per-metric provenance columns ``<metric>__type``.
    """
    df = frame.copy().sort_values("calendar_year").reset_index(drop=True)

    metric_cols = [
        "supply_toe", "import_toe", "import_pct", "losses_toe", "losses_pct",
        "td_losses_toe", "re_gen_gwh", "total_gen_gwh", "re_share_pct",
        "gas_production_bcf", "gas_consumption_bcf", "gas_self_suff_pct",
    ]

    # Base provenance: whatever the database actually reported.
    for c in metric_cols:
        df[f"{c}__type"] = [
            ACTUAL if pd.notna(v) else None for v in df[c]
        ]

    # ── primary supply: geometric trend ──────────────────────────────────
    sup = _recent_window(df["supply_toe"], 5)
    if len(sup) >= 2:
        g_supply = _cagr(sup.iloc[0], sup.iloc[-1], len(sup) - 1)
    else:
        g_supply = 2.0
    g_supply = max(-5.0, min(8.0, g_supply))

    last_sup_idx = df["supply_toe"].last_valid_index()
    if last_sup_idx is not None:
        base_sup = df.at[last_sup_idx, "supply_toe"]
        last_sup_year = int(df.at[last_sup_idx, "calendar_year"])
        # Power BI style: gap years inside history stay blank; only years
        # beyond HISTORY_END are modelled forward as Projected.
        for i in range(last_sup_idx + 1, len(df)):
            yr = int(df.at[i, "calendar_year"])
            if yr <= HISTORY_END:
                continue
            n = yr - last_sup_year
            df.at[i, "supply_toe"] = round(base_sup * (1 + g_supply / 100.0) ** n, 2)
            df.at[i, "supply_toe__type"] = PROJECTED

    # ── import dependence ────────────────────────────────────────────────
    known_import = df[df["import_pct"].notna() & (df["import_toe"] > 0)]
    if not known_import.empty:
        w = known_import.tail(5)
        # Trend of the import SHARE (percentage points per year).
        pp_slope = 0.0
        if len(w) >= 2:
            pp_slope = (w["import_pct"].iloc[-1] - w["import_pct"].iloc[0]) / (len(w) - 1)
        # Damp the historical slope: import growth cannot continue linearly for
        # a decade, and LNG contract ceilings exist.
        pp_slope = max(0.0, pp_slope) * 0.65
        last_imp_year = int(w["calendar_year"].iloc[-1])
        base_imp_pct = float(w["import_pct"].iloc[-1])

        # Power BI style blank: years after last reported up through
        # HISTORY_END have no source rows -- drop them to NaN, do NOT bridge.
        _blank = (df["calendar_year"] > last_imp_year) & (df["calendar_year"] <= HISTORY_END)
        df.loc[_blank, "import_pct"] = float("nan")
        df.loc[_blank, "import_toe"] = float("nan")
        df.loc[_blank, "import_pct__type"] = None
        df.loc[_blank, "import_toe__type"] = None

        # HISTORY_END+1 .. project_end -> Projected (trend continues the last
        # reported slope, but the historical gap remains visible on the chart).
        for i, yr in enumerate(df["calendar_year"]):
            yr = int(yr)
            if yr <= HISTORY_END:
                continue
            n = yr - last_imp_year
            val = min(base_imp_pct + pp_slope * n, 60.0)
            df.at[i, "import_pct"] = round(val, 2)
            sup_val = _num(df.at[i, "supply_toe"])
            if sup_val:
                df.at[i, "import_toe"] = round(sup_val * val / 100.0, 2)
            df.at[i, "import_toe__type"] = PROJECTED
            df.at[i, "import_pct__type"] = PROJECTED
        df.attrs["import_model"] = {
            "slope_pp_per_year": round(pp_slope, 3),
            "base_year": last_imp_year,
            "base_pct": round(base_imp_pct, 2),
            "last_reported_year": last_imp_year,
        }

    # ── losses ───────────────────────────────────────────────────────────
    los = _recent_window(df["losses_pct"], 5)
    last_los_idx = df["losses_pct"].last_valid_index()
    if last_los_idx is not None and not los.empty:
        base_los = float(los.mean())
        if len(los) >= 2:
            slope = (los.iloc[-1] - los.iloc[0]) / (len(los) - 1)
        else:
            slope = 0.0
        slope = max(-1.5, min(1.5, slope))
        last_los_year = int(df.at[last_los_idx, "calendar_year"])
        # Blank any interior-history gap; only Project beyond HISTORY_END.
        _blank = (df["calendar_year"] > last_los_year) & (df["calendar_year"] <= HISTORY_END)
        df.loc[_blank, "losses_pct"] = float("nan")
        df.loc[_blank, "losses_toe"] = float("nan")
        df.loc[_blank, "td_losses_toe"] = float("nan")
        df.loc[_blank, "losses_pct__type"] = None
        df.loc[_blank, "losses_toe__type"] = None
        for i in range(last_los_idx + 1, len(df)):
            yr = int(df.at[i, "calendar_year"])
            if yr <= HISTORY_END:
                continue
            n = yr - last_los_year
            # Damped improvement: half the observed slope, frozen after 2030.
            eff = min(n, 6)
            val = base_los + slope * eff * 0.5
            df.at[i, "losses_pct"] = round(max(0.0, val), 2)
            sup_val = _num(df.at[i, "supply_toe"])
            df.at[i, "losses_toe"] = round(sup_val * val / 100.0, 2)
            if pd.isna(df.at[i, "td_losses_toe"]):
                td_hist = _recent_window(df["td_losses_toe"], 5)
                td_share = _safe_div(_num(td_hist.mean()), _num(_recent_window(df["losses_toe"], 5).mean()))
                df.at[i, "td_losses_toe"] = round(_num(df.at[i, "losses_toe"]) * td_share, 2)
            df.at[i, "losses_pct__type"] = PROJECTED
            df.at[i, "losses_toe__type"] = PROJECTED

    # ── generation mix / renewable share ─────────────────────────────────
    re_last = df["re_share_pct"].last_valid_index()
    re_hist = df["re_share_pct"].dropna()
    if re_last is not None and len(re_hist) >= 4:
        w = re_hist.tail(6)
        # Least-squares slope on the recent RE-share path, damped 50%.
        xs = list(range(len(w)))
        ys = [float(v) for v in w.values]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        denom = sum((x - mx) ** 2 for x in xs)
        slope = (sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom) if denom else 0.0
        slope = max(0.0, slope) * 0.5
        base_share = float(w.iloc[-1])

        gen_hist = _recent_window(df["total_gen_gwh"], 5)
        g_gen = _cagr(gen_hist.iloc[0], gen_hist.iloc[-1], len(gen_hist) - 1) if len(gen_hist) >= 2 else 2.5
        g_gen = max(0.0, min(8.0, g_gen))

        last_gen_idx = df["total_gen_gwh"].last_valid_index()
        base_gen = _num(df.at[last_gen_idx, "total_gen_gwh"]) if last_gen_idx is not None else 0.0
        last_re_year = int(df.at[re_last, "calendar_year"])
        # Blank interior-history gaps.
        _blank = (df["calendar_year"] > last_re_year) & (df["calendar_year"] <= HISTORY_END)
        for c in ("re_share_pct", "re_gen_gwh", "total_gen_gwh"):
            df.loc[_blank, c] = float("nan")
            df.loc[_blank, f"{c}__type"] = None
        for i in range(re_last + 1, len(df)):
            yr = int(df.at[i, "calendar_year"])
            if yr <= HISTORY_END:
                continue
            n = yr - last_re_year
            val = min(base_share + slope * n, 95.0)
            df.at[i, "re_share_pct"] = round(val, 2)
            gen_val = base_gen * (1 + g_gen / 100.0) ** n
            df.at[i, "total_gen_gwh"] = round(gen_val, 2)
            df.at[i, "re_gen_gwh"] = round(gen_val * val / 100.0, 2)
            df.at[i, "re_share_pct__type"] = PROJECTED
            df.at[i, "re_gen_gwh__type"] = PROJECTED
            df.at[i, "total_gen_gwh__type"] = PROJECTED

    # ── gas ──────────────────────────────────────────────────────────────
    gas_last = df["gas_self_suff_pct"].last_valid_index()
    prod_hist = df["gas_production_bcf"].dropna()
    cons_hist = df["gas_consumption_bcf"].dropna()
    if gas_last is not None and len(prod_hist) >= 2 and len(cons_hist) >= 2:
        pw = prod_hist.tail(6)
        cw = cons_hist.tail(6)
        g_prod = _cagr(pw.iloc[0], pw.iloc[-1], len(pw) - 1)
        g_cons = _cagr(cw.iloc[0], cw.iloc[-1], len(cw) - 1)
        # Domestic fields deplete (-2%/yr floor); demand keeps growing a little.
        g_prod = max(-6.0, min(1.0, g_prod))
        g_cons = max(0.0, min(6.0, g_cons))
        if abs(g_prod) < 0.2:
            g_prod = -2.0
        if g_cons < 0.5:
            g_cons = 2.0

        base_prod = float(pw.iloc[-1])
        base_cons = float(cw.iloc[-1])
        last_gas_year = int(df.at[gas_last, "calendar_year"])
        # Blank interior-history gaps.
        _blank = (df["calendar_year"] > last_gas_year) & (df["calendar_year"] <= HISTORY_END)
        for c in ("gas_production_bcf", "gas_consumption_bcf", "gas_self_suff_pct"):
            df.loc[_blank, c] = float("nan")
            df.loc[_blank, f"{c}__type"] = None
        for i in range(gas_last + 1, len(df)):
            yr = int(df.at[i, "calendar_year"])
            if yr <= HISTORY_END:
                continue
            n = yr - last_gas_year
            prod = base_prod * (1 + g_prod / 100.0) ** n
            cons = base_cons * (1 + g_cons / 100.0) ** n
            df.at[i, "gas_production_bcf"] = round(prod, 2)
            df.at[i, "gas_consumption_bcf"] = round(cons, 2)
            df.at[i, "gas_self_suff_pct"] = round(_safe_div(prod, cons) * 100.0, 2)
            for c in ("gas_production_bcf", "gas_consumption_bcf", "gas_self_suff_pct"):
                df.at[i, f"{c}__type"] = PROJECTED

    # ── aggregate provenance tag per row ─────────────────────────────────
    def _row_sources(row) -> list:
        tags = []
        for c in metric_cols:
            t = row.get(f"{c}__type")
            if isinstance(t, str) and t not in tags:
                tags.append(t)
        order = [ACTUAL, ESTIMATED, PROJECTED]
        return [t for t in order if t in tags]

    df["sources"] = df.apply(_row_sources, axis=1)
    return df


# ══════════════════════════════════════════════════════════════════════════
#  4. KPI evaluation at one reference year
# ══════════════════════════════════════════════════════════════════════════

METRIC_TYPES = {
    "losses_pct": "losses_pct__type",
    "import_pct": "import_pct__type",
    "re_share_pct": "re_share_pct__type",
    "gas_self_suff_pct": "gas_self_suff_pct__type",
}


@dataclass
class MetricReading:
    key: str
    code: str
    title: str
    short: str
    color: str
    icon: str
    direction: str
    formula: str
    area: str
    actual_value: float
    target: float
    target_source: str
    target_label: str
    gap: float                  # favourable-positive
    achievement: float          # % of target achieved
    yoy: float                  # percentage-point change vs previous year
    reference_year: int
    provenance: str
    on_track: bool
    sev: dict = field(default_factory=dict)
    history: pd.DataFrame = field(default_factory=pd.DataFrame)


def _reading_for(year: int, key: str, spec: dict, series: pd.DataFrame,
                 targets: dict) -> Optional[MetricReading]:
    """One KPI reading for `key` at `year`."""
    col = {"losses_pct": "losses_pct",
           "import_dependence": "import_pct",
           "renewable_share": "re_share_pct",
           "gas_self_sufficiency": "gas_self_suff_pct"}[key]
    metric = spec["target_metric"]
    tinfo = targets.get(metric, {})
    target = _num(tinfo.get("target"))
    direction = tinfo.get("direction") or spec["direction"]

    rows = series[series["calendar_year"] == year]
    if rows.empty:
        return None
    raw = rows.iloc[0].get(col)

    # Power BI style blank: year exists in the frame but the metric has no
    # source row -- return a reading whose value is NaN so the KPI card can
    # render an empty cell instead of a misleading 0.
    if raw is None or pd.isna(raw):
        return MetricReading(
            key=key,
            code=spec["code"],
            title=spec["title"],
            short=spec["short"],
            color=spec["color"],
            icon=spec["icon"],
            direction=direction,
            formula=spec["formula"],
            area=spec["area"],
            actual_value=float("nan"),
            target=target,
            target_source=tinfo.get("source", "n/a"),
            target_label=tinfo.get("label", spec["title"]),
            gap=float("nan"),
            achievement=float("nan"),
            yoy=float("nan"),
            reference_year=int(year),
            provenance=MISSING,
            on_track=False,
            sev={"key": "missing", "label": "No data",
                 "color": "#64748B", "bg": "rgba(100,116,139,0.14)",
                 "score": 0.0},
            history=series[["calendar_year", col, f"{col}__type"]].rename(
                columns={col: "value", f"{col}__type": "provenance"}),
        )

    actual = float(raw)
    prov = rows.iloc[0].get(f"{col}__type") or ACTUAL

    prev = series[series["calendar_year"] == year - 1]
    yoy = (actual - _num(prev.iloc[0][col])) if not prev.empty else 0.0

    gap = signed_gap(actual, target, direction)
    return MetricReading(
        key=key,
        code=spec["code"],
        title=spec["title"],
        short=spec["short"],
        color=spec["color"],
        icon=spec["icon"],
        direction=direction,
        formula=spec["formula"],
        area=spec["area"],
        actual_value=actual,
        target=target,
        target_source=tinfo.get("source", "n/a"),
        target_label=tinfo.get("label", spec["title"]),
        gap=gap,
        achievement=achievement_pct(actual, target, direction),
        yoy=yoy,
        reference_year=int(year),
        provenance=str(prov),
        on_track=on_track(actual, target, direction),
        sev=severity(gap),
        history=series[["calendar_year", col, f"{col}__type"]].rename(
            columns={col: "value", f"{col}__type": "provenance"}),
    )


def compute_readings(series: pd.DataFrame,
                     targets: dict,
                     year_range: tuple,
                     reference_year: Optional[int] = None) -> dict:
    """
    Evaluate all four KPIs at a single reference year.

    `reference_year` defaults to the **end of the selected year range**, so the
    KPI cards follow the sidebar range: choose 2015-2030 and every card reports
    2030.  If the range end has no data at all we fall back to the latest year
    that does.
    """
    yr0, yr1 = int(year_range[0]), int(year_range[1])
    window = series[(series["calendar_year"] >= yr0) &
                    (series["calendar_year"] <= yr1)]

    if reference_year is None:
        if not window.empty:
            reference_year = yr1
        else:
            reference_year = int(series["calendar_year"].max())

    # Keep the requested year inside the data we actually have.
    available = series.dropna(subset=["losses_pct", "import_pct", "re_share_pct",
                                      "gas_self_suff_pct"], how="all")
    if not available.empty:
        reference_year = max(int(available["calendar_year"].min()),
                             min(int(available["calendar_year"].max()),
                                 int(reference_year)))

    readings = {}
    for spec in KPI_SPEC:
        r = _reading_for(reference_year, spec["key"], spec, series, targets)
        if r is not None:
            readings[spec["key"]] = r
    return readings


def rank_bottlenecks(readings: dict) -> list:
    """
    Rank by how badly the target is missed, using BOTH the percentage-point gap
    and the proportion of the target achieved.

    Only missed targets (gap < 0) can be bottlenecks; if everything is on
    track we fall back to the smallest surplus so the panel still shows an
    ordering.
    """
    scored = []
    for key, r in readings.items():
        if r.actual_value is None or pd.isna(r.actual_value) or pd.isna(r.gap):
            # Power BI style blank -- not ranked as a bottleneck.
            continue
        missed = max(0.0, -r.gap)
        # Relative shortfall: 1.0 means "nothing delivered at all".
        relative = 0.0
        if r.target:
            relative = missed / abs(r.target)
        scored.append({
            "key": key,
            "short": r.short,
            "title": r.title,
            "color": r.color,
            "gap": r.gap,
            "missed_pp": missed,
            "relative_shortfall": relative,
            "achievement": r.achievement,
            "score": missed * 0.6 + relative * 100.0 * 0.4,
            "on_track": r.on_track,
            "provenance": r.provenance,
            "sev": r.sev,
        })
    scored.sort(key=lambda d: d["score"], reverse=True)
    for i, d in enumerate(scored, start=1):
        d["rank"] = i
    return scored


# ══════════════════════════════════════════════════════════════════════════
#  5. Bottleneck timeline (gap per year, all metrics)
# ══════════════════════════════════════════════════════════════════════════

def gap_timeline(series: pd.DataFrame, targets: dict) -> pd.DataFrame:
    """Year x metric table of favourable-positive gaps (pp), 2002 -> horizon."""
    out = pd.DataFrame({"calendar_year": series["calendar_year"]})
    mapping = {"losses_pct": "losses_pct", "import_pct": "import_pct",
               "re_share_pct": "re_share_pct", "gas_self_suff_pct": "gas_self_suff_pct"}
    for metric, col in mapping.items():
        tinfo = targets.get(metric, {})
        target = _num(tinfo.get("target"))
        direction = tinfo.get("direction", "lower")
        vals = pd.to_numeric(series[col], errors="coerce")
        gaps = []
        for v in vals:
            if pd.isna(v):
                gaps.append(float("nan"))
            elif direction == "lower":
                gaps.append(target - float(v))
            else:
                gaps.append(float(v) - target)
        out[metric] = gaps
    return out


def horizon_summary(series: pd.DataFrame, targets: dict,
                    project_end: int = DEFAULT_PROJECT_END) -> pd.DataFrame:
    """
    Per-metric status at the horizon plus the first year the target is met, so
    the dashboard can say *when* (if ever) each target lands.
    """
    tl = gap_timeline(series, targets)
    rows = []
    label_map = {
        "losses_pct": "Energy Losses %",
        "import_pct": "Import Dependence %",
        "re_share_pct": "Renewable Share %",
        "gas_self_suff_pct": "Gas Self-Sufficiency %",
    }
    spec_by_metric = {s["target_metric"]: s for s in KPI_SPEC}
    for metric, label in label_map.items():
        spec = spec_by_metric.get(metric, {})
        g = tl[["calendar_year", metric]].dropna()
        if g.empty:
            continue
        met = g[g[metric] >= 0]
        end_row = g[g["calendar_year"] <= project_end].tail(1)
        rows.append({
            "metric": metric,
            "label": label,
            "color": spec.get("color", "#8B95A7"),
            "gap_at_horizon": float(end_row[metric].iloc[0]) if not end_row.empty else 0.0,
            "first_year_met": int(met["calendar_year"].min()) if not met.empty else None,
            "meets_by_horizon": bool(not met.empty and int(met["calendar_year"].min()) <= project_end),
        })
    return pd.DataFrame(rows)


def build_dashboard_data(overview_df, primary_df, re_df, gas_df,
                         targets: dict,
                         year_range: tuple,
                         project_end: int = DEFAULT_PROJECT_END,
                         reference_year: Optional[int] = None) -> dict:
    """
    One call that returns everything the Q3 page renders.

    Returns
    -------
    dict with keys: series, readings, ranking, timeline, horizon, reference_year,
    project_end, history_end, import_note.
    """
    raw = build_annual_series(overview_df, primary_df, re_df, gas_df, project_end)
    series = extend_to_horizon(raw, project_end)

    readings = compute_readings(series, targets, year_range, reference_year)
    ranking = rank_bottlenecks(readings)
    timeline = gap_timeline(series, targets)
    horizon = horizon_summary(series, targets, project_end)

    # Provenance note for the import KPI, which has a real data gap.
    imp_rows = series[series["import_pct"].notna()]
    last_reported_imp = None
    if not imp_rows.empty:
        real = imp_rows[imp_rows["import_pct__type"] == ACTUAL]
        if not real.empty:
            last_reported_imp = int(real["calendar_year"].max())

    actual_end = None
    act = series[series["losses_pct__type"] == ACTUAL]
    if not act.empty:
        actual_end = int(act["calendar_year"].max())

    return {
        "series": series,
        "readings": readings,
        "ranking": ranking,
        "timeline": timeline,
        "horizon": horizon,
        "reference_year": next(iter(readings.values())).reference_year if readings else year_range[1],
        "project_end": project_end,
        "last_reported_import_year": last_reported_imp if last_reported_imp else LAST_REPORTED_IMPORT_YEAR,
        "last_actual_losses_year": actual_end,
    }
