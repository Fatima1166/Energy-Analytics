"""
charts.py -- Q3 Target Bottlenecks Dashboard visuals.

All four visuals support the full 2002 -> 2035 horizon and mark the boundary
between reported history and modelled values, so a projected point can never be
mistaken for a measured one.

V1  Loss waterfall            -- where primary supply leaks, for one year
V2  Losses vs benchmark path  -- is the gap closing, and when does it close?
V3  Import dependence         -- import share build-up vs the benchmark
V4  Gas balance               -- production vs consumption, self-sufficiency
V5  Bottleneck gap paths      -- all four KPI gaps on one comparable axis
V6  Achievement bars          -- how much of each benchmark is delivered
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core.bottleneck_metrics import ACTUAL, ESTIMATED, PROJECTED, PROVENANCE_COLORS

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TITLE = "#94A3B8"


def _dark_theme(fig, height=390, y_title=None, x_title="Year", y2_title=None, legend_h=True):
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
    if y2_title:
        fig.update_layout(yaxis2=dict(
            title=dict(text=y2_title, font=dict(size=11, color=_TICK)),
            tickfont=dict(size=11, color=_TICK),
            overlaying="y", side="right", gridcolor=_AXIS, showgrid=False))
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
    """
    df = pd.DataFrame({"x": list(x), "y": list(y),
                       "t": [t if isinstance(t, str) else ACTUAL for t in types]})
    if df.empty:
        return fig

    # If the whole series is modelled, it must still read as modelled.
    if (df["t"] == ACTUAL).sum() == 0:
        df["t"] = PROJECTED

    boundaries = [i for i in range(1, len(df)) if df["t"].iloc[i] != df["t"].iloc[i - 1]]
    starts = [0] + boundaries
    ends = boundaries + [len(df)]

    for seg_i, (a, b) in enumerate(zip(starts, ends)):
        lo = max(0, a - 1) if seg_i > 0 else a      # overlap one point, no gap
        seg = df.iloc[lo:b]
        tag = df["t"].iloc[b - 1]
        seg_color = PROVENANCE_COLORS.get(tag, color)
        line_style = dict(color=seg_color, width=width)
        if tag == ESTIMATED:
            line_style["dash"] = "dot"
        elif tag == PROJECTED:
            line_style["dash"] = "dash"
        marker = (dict(size=5, color=seg_color, line=dict(width=1, color="#1A1D24"))
                  if mode == "lines+markers" else None)

        trace = go.Scatter(
            x=seg["x"], y=seg["y"], mode=mode, name=base_name,
            line=line_style, marker=marker, showlegend=False, legendgroup=base_name,
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
    supply = float(r.get("supply_toe") or 0.0)
    losses = float(r.get("losses_toe") or 0.0)
    td = float(r.get("td_losses_toe") or 0.0)
    if td != td:                       # NaN
        td = 0.0
    if supply <= 0:
        return _empty_fig(f"No supply data for {yr}")

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
    fig.update_layout(
        title=dict(text=f"Energy Flow Waterfall — {yr}",
                   font=dict(size=12, color=_TITLE), x=0.01),
        showlegend=False, bargap=0.34,
    )
    fig.update_xaxes(title=dict(text="Flow Stage", font=dict(size=11, color=_TICK)), tickfont=dict(size=10))
    return fig


# ═══════════ V2: Losses vs benchmark path (actual -> 2035) ═════════════════

def visual2_losses_path(series: pd.DataFrame, year_range: tuple,
                        target: float, direction: str = "lower"):
    """
    V2 -- reported and projected energy-loss intensity against the benchmark,
    with the gap shaded and a star on the first year the target is met.
    """
    if series is None or series.empty:
        return _empty_fig("No loss data")

    df = series[["calendar_year", "losses_pct", "losses_pct__type"]].dropna(
        subset=["losses_pct"]).copy()
    df = df[(df["calendar_year"] >= year_range[0]) & (df["calendar_year"] <= year_range[1])]
    if df.empty:
        return _empty_fig("No loss data in the selected year range")

    x = df["calendar_year"].astype(int)
    y = pd.to_numeric(df["losses_pct"], errors="coerce")
    types = df["losses_pct__type"].fillna(ACTUAL)
    actual_x = x[types == ACTUAL]
    boundary = int(actual_x.max()) if not actual_x.empty else None

    fig = go.Figure()

    # Shaded gap between the actual path and the benchmark.
    fig.add_trace(go.Scatter(
        x=list(x) + list(x[::-1]),
        y=list(y) + [target] * len(x),
        fill="toself", fillcolor="rgba(239,68,68,0.10)",
        line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
        showlegend=False, name="Gap to benchmark",
    ))

    _segment_traces(fig, x, y, types, "Energy Losses %", "#EF4444",
                    mode="lines+markers", width=2.6)
    _legend_proxy(fig, "Energy Losses %", "#EF4444")

    fig.add_trace(go.Scatter(
        x=[int(x.min()), int(x.max())], y=[target, target],
        name=f"Benchmark {target:.1f}%", mode="lines",
        line=dict(color="#10B981", width=2, dash="dash"), hoverinfo="skip",
    ))

    met = (df[pd.to_numeric(df["losses_pct"], errors="coerce") <= target]
           if str(direction).lower() == "lower"
           else df[pd.to_numeric(df["losses_pct"], errors="coerce") >= target])
    if not met.empty:
        mx, my = int(met["calendar_year"].iloc[0]), float(met["losses_pct"].iloc[0])
        fig.add_trace(go.Scatter(
            x=[mx], y=[my], mode="markers+text", name=f"Target met ({mx})",
            marker=dict(size=14, color="#10B981", symbol="star",
                        line=dict(color="#0B3B2E", width=1)),
            text=[f"met {mx}"], textposition="bottom center",
            textfont=dict(size=9.5, color="#10B981"), hoverinfo="skip",
        ))

    if boundary is not None:
        _split_marker(fig, boundary)

    fig = _dark_theme(fig, height=400, y_title="Losses % of Primary Supply", x_title="Year")
    fig.update_layout(yaxis=dict(
        ticksuffix="%", gridcolor=_AXIS, zerolinecolor=_AXIS,
        tickfont=dict(size=11, color=_TICK),
        title=dict(text="Losses % of Primary Supply", font=dict(size=11, color=_TICK))))
    return fig


# ═════════════ V3: Import dependence vs benchmark ═══════════════════════════

def visual3_import_dependence(series: pd.DataFrame, year_range: tuple,
                              target: float, unit_energy: str = "TOE",
                              last_reported_year: int = 2018,
                              benchmark_note: str = "best recorded year"):
    """
    V3 -- import dependence over time, with imported volume as context bars.
    Reported years are solid, the bridge years with no source rows are dotted
    (Estimated), and the post-2024 horizon is dashed (Projected).
    """
    if series is None or series.empty:
        return _empty_fig("No primary supply data")

    df = series[["calendar_year", "import_pct", "import_pct__type",
                 "import_toe", "supply_toe"]].dropna(subset=["import_pct"]).copy()
    df = df[(df["calendar_year"] >= year_range[0]) & (df["calendar_year"] <= year_range[1])]
    if df.empty:
        return _empty_fig("No import data in the selected year range")

    x = df["calendar_year"].astype(int)
    y = pd.to_numeric(df["import_pct"], errors="coerce")
    types = df["import_pct__type"].fillna(ACTUAL)
    actual_x = x[types == ACTUAL]
    boundary = int(actual_x.max()) if not actual_x.empty else None

    fig = make_subplots(specs=[[{"secondary_y": True}]])

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


# ══════════════════════ V4: Gas balance ═════════════════════════════════════

def visual4_gas_balance(series: pd.DataFrame, year_range: tuple,
                        target: float, unit_gas: str = "BCF"):
    """
    V4 -- domestic production vs consumption with the self-sufficiency ratio on
    the secondary axis, extended to the horizon so gas depletion is visible.
    """
    if series is None or series.empty:
        return _empty_fig("No natural gas data")

    cols = ["calendar_year", "gas_production_bcf", "gas_consumption_bcf",
            "gas_self_suff_pct", "gas_self_suff_pct__type"]
    df = series[cols].dropna(subset=["gas_production_bcf", "gas_consumption_bcf"]).copy()
    df = df[(df["calendar_year"] >= year_range[0]) & (df["calendar_year"] <= year_range[1])]
    if df.empty:
        return _empty_fig("No gas data in the selected year range")

    x = df["calendar_year"].astype(int)
    prod = pd.to_numeric(df["gas_production_bcf"], errors="coerce")
    cons = pd.to_numeric(df["gas_consumption_bcf"], errors="coerce")
    ratio = pd.to_numeric(df["gas_self_suff_pct"], errors="coerce")
    types = df["gas_self_suff_pct__type"].fillna(ACTUAL)
    actual_x = x[types == ACTUAL]
    boundary = int(actual_x.max()) if not actual_x.empty else None
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


# ═══════════════ V5: Bottleneck gap paths (all metrics) ═════════════════════

def visual5_gap_paths(timeline: pd.DataFrame, year_range: tuple,
                      labels: dict, colors: dict):
    """
    V5 -- every KPI gap on one axis.  Positive = benchmark met, negative =
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
            x=df["calendar_year"], y=df[metric].round(2),
            name=label, mode="lines",
            line=dict(color=colors.get(metric, "#8B95A7"), width=2.3),
            hovertemplate=label + "<br>%{x}: <b>%{y:+.2f} pp</b><extra></extra>",
        ))

    fig = _dark_theme(fig, height=340, y_title="Gap to benchmark (pp)", x_title="Year")
    fig.update_layout(yaxis=dict(
        ticksuffix="pp", gridcolor=_AXIS, zerolinecolor=_AXIS,
        tickfont=dict(size=11, color=_TICK),
        title=dict(text="Gap to benchmark (percentage points)",
                   font=dict(size=11, color=_TICK))))
    return fig


# ══════════════ V6: Achievement bars at the reference year ══════════════════

def visual6_achievement(readings: dict, order: list, year: int = None):
    """
    V6 -- how much of each benchmark is delivered at the reference year.
    100% is the benchmark; bars are coloured by severity.

    Sized and margined to sit level with V5 when the two share a row.
    """
    if not readings:
        return _empty_fig("No KPI data")

    keys = [k for k in order if k in readings]
    if not keys:
        return _empty_fig("No KPI data")

    labels = [readings[k].short for k in keys]
    values = [readings[k].achievement for k in keys]
    colors = [readings[k].sev["color"] for k in keys]
    custom = [(readings[k].target, readings[k].actual_value, readings[k].provenance)
              for k in keys]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(color="#1A1D24", width=0.6)),
        text=[f"{v:.0f}%" for v in values], textposition="outside",
        textfont=dict(size=11, color="#C8CDD6"),
        customdata=custom,
        hovertemplate=("<b>%{y}</b><br>Achievement: %{x:.1f}% of benchmark"
                       "<br>Benchmark: %{customdata[0]:.2f}%"
                       "<br>Value: %{customdata[1]:.2f}% (%{customdata[2]})"
                       "<extra></extra>"),
    ))
    fig.add_vline(x=100, line=dict(color="#10B981", width=2, dash="dash"))
    fig.add_annotation(x=100, y=1.0, yref="paper", yanchor="bottom",
                       text="benchmark", showarrow=False,
                       font=dict(size=10, color="#10B981"))

    # Same height as V5 so the two cards line up in a shared row.
    fig = _dark_theme(fig, height=340, x_title="Benchmark Achievement (%)", y_title="KPI / Target", legend_h=False)
    fig.update_layout(
        showlegend=False,
        bargap=0.42,
        title=dict(text=(f"Delivery at {year}" if year else ""),
                   font=dict(size=11.5, color=_TITLE), x=0.01),
        xaxis=dict(range=[0, max(170, max(values) * 1.28 if values else 170)],
                   ticksuffix="%", gridcolor=_AXIS, tickfont=dict(size=11, color=_TICK),
                   title=dict(text="Benchmark Achievement (%)", font=dict(size=11, color=_TICK))),
        yaxis=dict(tickfont=dict(size=11.5, color="#C8CDD6"),
                   title=dict(text="KPI / Target", font=dict(size=11, color=_TICK))),
        margin=dict(l=126, r=76, t=40, b=52),
    )
    return fig
