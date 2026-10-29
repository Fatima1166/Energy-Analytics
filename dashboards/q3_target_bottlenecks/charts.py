"""
charts.py -- Q3 Target Bottlenecks Dashboard visuals.

All four visuals support the full 2002 -> 2035 horizon and mark the boundary
between reported history and modelled values, so a projected point can never be
mistaken for a measured one.

V1  Loss waterfall       -- where primary supply leaks, for one year
V2  Import dependence    -- import share build-up with imported volume
V3  Gas balance          -- production vs consumption, self-sufficiency
V4  Bottleneck gaps      -- all four KPI gaps on one comparable axis
V5  Better or worse      -- slope: first reported year to last reported year

Each target's own benchmark, gap and rank already sit on its KPI card, and V4
carries the "are we getting closer" answer for all four -- so no chart here
redraws one metric against its target line.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.bottleneck_metrics import (ACTUAL, ESTIMATED, PROJECTED, MISSING,
                                      PROVENANCE_COLORS)

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"


def _dark_theme(fig, height=390, y_title=None, x_title="Year", legend_h=True):
    """Consistent premium dark theme used by every Q3 figure."""
    legend_cfg = (
        dict(orientation="h", y=-0.24, x=0.5, xanchor="center",
             font=dict(size=10.5, color="#C8CDD6"))
        if legend_h
        else dict(orientation="v", x=1.02, y=0.5, font=dict(size=10.5, color="#C8CDD6"))
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#1A1D24",
        plot_bgcolor="#14171E",
        margin=dict(l=54, r=40, t=34, b=66),
        height=height,
        legend=legend_cfg,
        hovermode="x",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        xaxis=dict(gridcolor=_AXIS, zerolinecolor=_AXIS,
                   title=dict(text=x_title, font=dict(size=11, color=_TICK)) if x_title else None,
                   tickfont=dict(size=11, color=_TICK)),
        yaxis=dict(gridcolor=_AXIS, zerolinecolor=_AXIS,
                   title=dict(text=y_title, font=dict(size=11, color=_TICK)) if y_title else None,
                   tickfont=dict(size=11, color=_TICK)),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color="#C8CDD6"),
    )
    return fig


def _empty_fig(msg="No data available for this selection"):
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=13, color=_TICK))
    return _dark_theme(fig)


def _split_marker(fig, boundary_year):
    """Vertical dashed line + label at the history/modelled boundary."""
    if boundary_year is None:
        return fig
    fig.add_vline(x=boundary_year + 0.5, line=dict(color="#64748B", width=1.4, dash="dash"))
    fig.add_annotation(
        x=boundary_year + 0.5, y=1.0, yref="paper", yanchor="bottom",
        text="Reported ◀ | ▶ Modelled",
        showarrow=False, font=dict(size=9.5, color="#94A3B8"),
        bgcolor="rgba(20,23,30,0.85)", borderpad=3, xanchor="center",
    )
    return fig


def _segment_traces(fig, x, y, types, base_name, color, width=2.5,
                    mode="lines", row=None, col=None, secondary_y=False):
    """
    Draw one series split into Actual / Estimated / Projected segments so the
    line styling itself communicates provenance.

    Power BI style blank -- rows whose ``types`` is ``MISSING``/``None`` **or**
    whose ``y`` is NaN are left as line breaks (``connectgaps=False``) so the
    gap year is visibly empty on the chart, never silently bridged.
    """
    y_num = pd.to_numeric(pd.Series(list(y)), errors="coerce")
    df = pd.DataFrame({
        "x": list(x),
        "y": list(y_num),
        "t": [t if isinstance(t, str) and t != MISSING else None for t in types],
    })
    if df.empty:
        return fig

    # If the whole series is modelled, it must still read as modelled.
    if (df["t"] == ACTUAL).sum() == 0 and (df["t"] == ESTIMATED).sum() == 0:
        if (df["t"] == PROJECTED).any():
            df["t"] = df["t"].apply(lambda t: t if t is not None else PROJECTED)

    # Break at tag changes AND at missing-y so a gap year visibly stops the
    # line rather than being bridged.
    def _key(i):
        return (df["t"].iloc[i], not pd.isna(df["y"].iloc[i]))
    boundaries = [i for i in range(1, len(df)) if _key(i) != _key(i - 1)]
    starts = [0] + boundaries
    ends = boundaries + [len(df)]

    for seg_i, (a, b) in enumerate(zip(starts, ends)):
        seg = df.iloc[a:b]
        # Skip runs made entirely of gap years -- nothing to draw.
        if seg["y"].isna().all():
            continue
        tag = df["t"].iloc[b - 1] or PROJECTED
        seg_color = PROVENANCE_COLORS.get(tag, color)
        line_style = dict(color=seg_color, width=width)
        if tag == ESTIMATED:
            line_style["dash"] = "dot"
        elif tag == PROJECTED:
            line_style["dash"] = "dash"
        marker = (dict(size=5, color=seg_color, line=dict(width=1, color="#1A1D24"))
                  if "markers" in mode else None)

        # Overlap the previous segment by one point only when that point is
        # present (so tags connect visually across a tag change but NOT
        # across a Power BI gap).
        prev_present = (seg_i > 0 and a > 0 and not pd.isna(df["y"].iloc[a - 1]))
        if prev_present:
            seg = pd.concat([df.iloc[a - 1:a], seg], ignore_index=True)

        trace = go.Scatter(
            x=seg["x"], y=seg["y"], mode=mode, name=base_name,
            line=line_style, marker=marker, showlegend=False,
            legendgroup=base_name, connectgaps=False,
            hovertemplate=f"{base_name}<br>%{{x}}: <b>%{{y:,.2f}}</b><extra></extra>",
        )
        if row is not None:
            fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
        else:
            fig.add_trace(trace)
    return fig


def _legend_proxy(fig, name, color, mode="lines+markers", dash=None, width=2.5,
                  row=None, col=None, secondary_y=False):
    """One visible legend entry standing in for the hidden segment traces."""
    line = dict(color=color, width=width)
    if dash:
        line["dash"] = dash
    trace = go.Scatter(
        x=[None], y=[None], mode=mode, name=name, line=line,
        marker=dict(size=5, color=color) if "markers" in mode else None,
        showlegend=True, hoverinfo="skip",
    )
    if row is not None:
        fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    else:
        fig.add_trace(trace)
    return fig


# ══════════════════════ V1: Energy loss waterfall ═══════════════════════════

def visual1_loss_waterfall(series: pd.DataFrame, year: int, unit: str = "TOE"):
    """
    V1 -- how primary supply splits into transformation losses, T&D losses and
    final consumption, for one year.

    For modelled years the split is derived: transformation losses keep their
    last reported share of total losses, T&D keeps its own share, and final
    consumption closes the balance.  The title states which it is.
    """
    if series is None or series.empty:
        return _empty_fig("No energy balance data")

    row = series[series["calendar_year"] == year]
    if row.empty:
        row = series.dropna(subset=["losses_pct"]).tail(1)
    if row.empty:
        return _empty_fig("No energy balance data")

    r = row.iloc[0]
    yr = int(r["calendar_year"])
    supply_v = r.get("supply_toe")
    losses_v = r.get("losses_toe")
    td_v = r.get("td_losses_toe")

    # Power BI style blank -- if the selected year has no losses or supply
    # row, show the empty figure instead of a misleading waterfall of zeros.
    if supply_v is None or pd.isna(supply_v) or float(supply_v) <= 0:
        return _empty_fig(f"No supply data for {yr}")
    if losses_v is None or pd.isna(losses_v):
        return _empty_fig(f"No losses data for {yr}")

    supply = float(supply_v)
    losses = float(losses_v)
    td = 0.0 if (td_v is None or pd.isna(td_v)) else float(td_v)

    # Transformation share of total losses from the last reported breakdown.
    trans_ratio = 0.88
    hist = series[(series["losses_toe"].notna()) & (series["td_losses_toe"].notna())]
    if not hist.empty:
        h = hist.iloc[-1]
        hl, htd = float(h.get("losses_toe") or 0.0), float(h.get("td_losses_toe") or 0.0)
        if hl > 0:
            trans_ratio = max(0.0, min(1.0, (hl - htd) / hl))

    trans = (losses - td) if td > 0 else losses * trans_ratio
    trans = max(0.0, min(losses, trans))
    other = max(0.0, losses - trans - td)
    consumption = max(0.0, supply - losses)

    bars = [
        ("Primary Supply", supply, "#00A6FB", "Supply"),
        ("Transformation\nLosses", trans, "#F59E0B", "Loss"),
        ("T&D Losses", td, "#EF4444", "Loss"),
        ("Other Losses", other, "#A855F7", "Loss"),
        ("Final Consumption", consumption, "#10B981", "Delivered"),
    ]

    x_labels, bases, heights, texts, colors = [], [], [], [], []
    running = supply
    for i, (lab, val, colr, kind) in enumerate(bars):
        if i == 0:
            bases.append(0.0)
            heights.append(val)
            running = val
        elif i == len(bars) - 1:
            bases.append(0.0)
            heights.append(val)
        else:
            running -= val
            bases.append(max(0.0, running))
            heights.append(val)
        x_labels.append(lab)
        texts.append(f"{val:,.0f}")
        colors.append(colr)

    fig = go.Figure(go.Bar(
        x=x_labels, y=heights, base=bases,
        marker=dict(color=colors, line=dict(color="#1A1D24", width=0.8)),
        text=texts, textposition="outside",
        textfont=dict(size=10, color="#C8CDD6"),
        customdata=[[b[1], b[3]] for b in bars],
        hovertemplate=("<b>%{x}</b><br>" + unit + ": %{customdata[0]:,.0f}"
                       "<br>%{customdata[1]}<extra></extra>"),
    ))

    fig = _dark_theme(fig, height=400, y_title=f"Energy Flow ({unit})", x_title="Flow Stage")
    fig.update_layout(showlegend=False, bargap=0.34)
    fig.update_xaxes(title=dict(text="Flow Stage", font=dict(size=11, color=_TICK)), tickfont=dict(size=10))
    return fig


# ═════════════ V2: Import dependence ════════════════════════════════════════

def visual2_import_dependence(series: pd.DataFrame, year_range: tuple,
                              unit_energy: str = "TOE"):
    """
    V2 -- import dependence over time, with imported volume as context bars.
    Reported years are solid and the post-HISTORY_END horizon is dashed
    (Projected).  Years whose source table has no import row are rendered
    as blank: no bar, line break (Power BI style).  The benchmark comparison
    lives on the KPI card and in V4, so this chart only shows the build-up.
    """
    if series is None or series.empty:
        return _empty_fig("No primary supply data")

    df = series[["calendar_year", "import_pct", "import_pct__type",
                 "import_toe", "supply_toe"]].copy()
    df = df[(df["calendar_year"] >= year_range[0]) & (df["calendar_year"] <= year_range[1])]
    if df.empty or df["import_pct"].notna().sum() == 0:
        return _empty_fig("No import data in the selected year range")

    x = df["calendar_year"].astype(int)
    y = pd.to_numeric(df["import_pct"], errors="coerce")
    types = df["import_pct__type"]
    actual_x = x[(types == ACTUAL) & y.notna()]
    boundary = int(actual_x.max()) if not actual_x.empty else None

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Missing import_toe is left as NaN -- Plotly renders no bar for that
    # year, which is the Power BI blank behaviour the user wants.
    fig.add_trace(go.Bar(
        x=x, y=pd.to_numeric(df["import_toe"], errors="coerce"),
        name=f"Imported energy ({unit_energy})",
        marker_color="rgba(239,68,68,0.32)",
        marker_line=dict(color="#1A1D24", width=0.4),
        hovertemplate=("Imported: <b>%{y:,.0f} " + unit_energy + "</b><extra></extra>"),
    ), row=1, col=1, secondary_y=True)

    _segment_traces(fig, x, y, types, "Import Dependence %", "#F59E0B",
                    mode="lines+markers", width=2.8, row=1, col=1)
    _legend_proxy(fig, "Import Dependence %", "#F59E0B", row=1, col=1)
    if boundary is not None:
        _split_marker(fig, boundary)

    fig = _dark_theme(fig, height=400, y_title="Import share (%)", x_title="Year")
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_layout(
        yaxis=dict(ticksuffix="%", gridcolor=_AXIS, zerolinecolor=_AXIS,
                   tickfont=dict(size=11, color=_TICK), rangemode="tozero",
                   title=dict(text="Import share (%)", font=dict(size=11, color=_TICK))),
        yaxis2=dict(title=dict(text=f"Imported energy ({unit_energy})",
                                font=dict(size=10.5, color="#8B95A7")),
                    tickfont=dict(size=10, color="#8B95A7"), showgrid=False),
        bargap=0.55,
    )
    return fig


# ══════════════════════ V3: Gas balance ═════════════════════════════════════

def visual3_gas_balance(series: pd.DataFrame, year_range: tuple,
                        target: float, unit_gas: str = "BCF"):
    """
    V3 -- domestic production vs consumption with the self-sufficiency ratio on
    the secondary axis, extended to the horizon so gas depletion is visible.
    Years with no source row are shown blank (no bar, line break) rather than
    bridged -- Power BI style missing-year handling.
    """
    if series is None or series.empty:
        return _empty_fig("No natural gas data")

    cols = ["calendar_year", "gas_production_bcf", "gas_consumption_bcf",
            "gas_self_suff_pct", "gas_self_suff_pct__type"]
    df = series[cols].copy()
    df = df[(df["calendar_year"] >= year_range[0]) & (df["calendar_year"] <= year_range[1])]
    if df.empty or df["gas_production_bcf"].notna().sum() == 0:
        return _empty_fig("No gas data in the selected year range")

    x = df["calendar_year"].astype(int)
    prod = pd.to_numeric(df["gas_production_bcf"], errors="coerce")
    cons = pd.to_numeric(df["gas_consumption_bcf"], errors="coerce")
    ratio = pd.to_numeric(df["gas_self_suff_pct"], errors="coerce")
    types = df["gas_self_suff_pct__type"]
    actual_x = x[(types == ACTUAL) & ratio.notna()]
    boundary = int(actual_x.max()) if not actual_x.empty else None
    # Deficit only where BOTH prod and cons are reported -- NaN propagates so
    # gap years produce no shaded area.
    deficit = (prod - cons).clip(upper=0)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=x, y=prod, name="Domestic Production",
        marker_color="#10B981", marker_line=dict(color="#1A1D24", width=0.5),
        hovertemplate="Production: <b>%{y:,.1f} " + unit_gas + "</b><extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        x=x, y=cons, name="Consumption",
        marker_color="rgba(245,158,11,0.55)",
        marker_line=dict(color="#1A1D24", width=0.5),
        hovertemplate="Consumption: <b>%{y:,.1f} " + unit_gas + "</b><extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x, y=deficit, name="Supply deficit",
        mode="lines", line=dict(color="#EF4444", width=1.6, dash="dot"),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.22)",
        connectgaps=False,
        hovertemplate="Deficit: <b>%{y:,.1f} " + unit_gas + "</b><extra></extra>",
    ), secondary_y=False)

    _segment_traces(fig, x, ratio, types, "Self-Sufficiency %", "#A855F7",
                    mode="lines+markers", width=2.2, secondary_y=True)
    _legend_proxy(fig, "Self-Sufficiency %", "#A855F7", secondary_y=True)

    fig.add_trace(go.Scatter(
        x=[int(x.min()), int(x.max())], y=[target, target],
        name=f"Benchmark {target:.0f}%", mode="lines",
        line=dict(color="#FFFFFF", width=1.6, dash="dash"), hoverinfo="skip",
    ), secondary_y=True)

    if boundary is not None:
        _split_marker(fig, boundary)

    top = 140.0
    if ratio.notna().any():
        top = max(140.0, float(ratio.max()) * 1.2)
    fig = _dark_theme(fig, height=400, y_title=f"Gas Volume ({unit_gas})", x_title="Year", legend_h=True)
    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_layout(
        barmode="group", bargap=0.22, bargroupgap=0.08,
        yaxis=dict(title=dict(text=f"Natural Gas ({unit_gas})", font=dict(size=11, color=_TICK)),
                   gridcolor=_AXIS, zerolinecolor=_AXIS,
                   tickfont=dict(size=11, color=_TICK)),
        yaxis2=dict(title=dict(text="Self-Sufficiency (%)",
                               font=dict(size=11, color="#A855F7")),
                    ticksuffix="%", tickfont=dict(size=10.5, color="#A855F7"),
                    range=[0, top], showgrid=False),
    )
    return fig


# ═══════════════ V4: Bottleneck gap paths (all metrics) ═════════════════════

def visual4_gap_paths(timeline: pd.DataFrame, year_range: tuple,
                      labels: dict, colors: dict):
    """
    V4 -- every KPI gap on one axis.  Positive = benchmark met, negative =
    missed, which makes the direction of each bottleneck directly comparable.
    """
    if timeline is None or timeline.empty:
        return _empty_fig("No gap data")

    df = timeline[(timeline["calendar_year"] >= year_range[0]) &
                  (timeline["calendar_year"] <= year_range[1])]
    if df.empty:
        return _empty_fig("No gap data in the selected year range")

    fig = go.Figure()
    fig.add_hline(y=0, line=dict(color="#64748B", width=1.4))

    for metric, label in labels.items():
        if metric not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["calendar_year"], y=pd.to_numeric(df[metric], errors="coerce").round(2),
            name=label, mode="lines",
            line=dict(color=colors.get(metric, "#8B95A7"), width=2.3),
            connectgaps=False,
            hovertemplate=label + "<br>%{x}: <b>%{y:+.2f} points</b><extra></extra>",
        ))

    gap_axis = "Gap to benchmark (percentage points)"
    fig = _dark_theme(fig, height=340, y_title=gap_axis, x_title="Year")
    fig.update_layout(yaxis=dict(
        ticksuffix="pp", gridcolor=_AXIS, zerolinecolor=_AXIS,
        tickfont=dict(size=11, color=_TICK),
        title=dict(text=gap_axis,
                   font=dict(size=11, color=_TICK))))
    return fig


# ═══════════════════════════════ V5 -- better or worse (slope) ═════════════

_METRIC_WORDS = {
    "losses_pct": ("Energy Losses %", "#EF4444", "lower"),
    "import_pct": ("Import Dependence %", "#F59E0B", "lower"),
    "re_share_pct": ("Renewable Share %", "#10B981", "higher"),
    "gas_self_suff_pct": ("Gas Self-Sufficiency %", "#00A6FB", "higher"),
}


def visual5_bottleneck_slope(series: pd.DataFrame, year_range: tuple) -> go.Figure:
    """One line per bottleneck metric: its value in the first reported year of
    the range and its value in the last reported year.  A line that moves
    towards the improvement side (losses/imports down, renewables/gas up) is
    painted green; a line that moves the wrong way is red.  This is the "is
    the bottleneck easing or tightening?" answer that V1..V4 do not give."""
    fig = go.Figure()
    if series is None or series.empty:
        return _dark_theme(fig, height=380, y_title="Metric (%)",
                           x_title="First reported → Last reported")

    lo_yr, hi_yr = int(year_range[0]), int(year_range[1])
    actual = series[(series["calendar_year"] >= lo_yr) &
                    (series["calendar_year"] <= hi_yr)]

    any_drawn = False
    for metric, (label, colour, direction) in _METRIC_WORDS.items():
        type_col = f"{metric}__type"
        if metric not in actual.columns:
            continue
        if type_col in actual.columns:
            pool = actual[actual[type_col] == ACTUAL]
        else:
            pool = actual[actual[metric].notna()]
        if pool.empty:
            continue
        pool = pool.sort_values("calendar_year")
        first_row = pool.iloc[0]
        last_row = pool.iloc[-1]
        x0 = str(int(first_row["calendar_year"]))
        x1 = str(int(last_row["calendar_year"]))
        v0 = float(first_row[metric])
        v1 = float(last_row[metric])
        moved_good = (v1 < v0) if direction == "lower" else (v1 > v0)
        line_colour = "#10B981" if moved_good else "#EF4444"
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[v0, v1], mode="lines+markers+text",
            name=label,
            line=dict(color=line_colour, width=2.4),
            marker=dict(size=9, color=[line_colour, line_colour]),
            text=[f"{v0:.1f}%", f"{v1:.1f}%"],
            textposition=["middle right", "middle left"],
            textfont=dict(size=9.5, color=_TICK),
            customdata=[v1 - v0],
            hovertemplate=('<b>' + label + '</b><br>'
                           f'{x0} \u2192 {x1}<br>'
                           'First: <b>' + f'{v0:.2f}' + '%</b><br>'
                           'Last: <b>' + f'{v1:.2f}' + '%</b><br>'
                           'Change: ' + f'{(v1-v0):+.2f}' + ' pp'
                           '<extra></extra>'),
        ))
        # a light grey label on the left axis so the reader can see what the
        # line means even without hovering
        any_drawn = True

    if not any_drawn:
        fig.add_annotation(text="No reported years in this range",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color=_TICK, size=12))

    _dark_theme(fig, height=380,
                y_title="Metric value (% of the base)",
                x_title="First reported year → Last reported year",
                legend_h=False)
    fig.update_layout(
        legend=dict(orientation="h", y=-0.30, x=0.5, xanchor="center",
                    font=dict(size=9.5, color="#C8CDD6")),
        margin=dict(l=54, r=40, t=34, b=88),
    )
    return fig

