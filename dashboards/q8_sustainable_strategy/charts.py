"""
dashboards/q8_sustainable_strategy/charts.py -- visuals for Question 8
("What optimal strategy may be opted to make energy development sustainable?").

Four figures, one job each:
V1  Where we stand      -- four pillars, latest score against ten years earlier
V2  What each option buys per dollar, funded and deferred in one ranking
V3  The measures behind each pillar -- one heat-map, latest reported year
V4  What the recommended package adds to each pillar
V5  How much the next bn of spend actually buys -- budget-to-score curve

Presentation-only ("dumb"): core/sustainability_engine.py pre-computes every
value; these functions only draw.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .config import PILLAR_COLOURS

# ═══════════════════════════ shared dark theme ═══════════════════════════════

_AXIS = "#2A2F3A"
_TICK = "#8B95A7"
_TEXT = "#C8D0DA"
_PAPER = "#1A1D24"
_PLOT = "#14171E"
_FUNDED = "#10B981"
_DEFERRED = "#475569"


def _dark_theme(fig, height: int = 400, y_title: Optional[str] = None,
                x_title: Optional[str] = None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        margin=dict(l=62, r=46, t=45, b=72),
        height=height,
        hovermode="closest",
        hoverlabel=dict(bgcolor="#232830", font_size=11,
                        font_family="Inter, sans-serif"),
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                  color=_TEXT),
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                    font=dict(size=10.5, color=_TEXT)),
    )
    fig.update_xaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=x_title, font=dict(size=11.5, color=_TEXT)) if x_title else None,
                     tickfont=dict(size=11, color=_TICK))
    fig.update_yaxes(gridcolor=_AXIS, zerolinecolor=_AXIS,
                     title=dict(text=y_title, font=dict(size=11.5, color=_TEXT)) if y_title else None,
                     tickfont=dict(size=11, color=_TICK))
    return fig


def _empty(fig, msg="Nothing to show", **kw):
    fig.add_annotation(text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
                       showarrow=False, font=dict(color=_TEXT, size=13))
    return _dark_theme(fig, **kw)


# ═══════════════ V1 -- where we stand (grouped bars, latest vs 10 yrs back) ══

def visual1_pillar_scorecard(scorecard: pd.DataFrame) -> go.Figure:
    """Four pillars, two bars each: the latest score and the score ten years
    earlier.  Each pillar carries the year it was last reported and how many
    measures stand behind it, because those differ a lot."""
    fig = go.Figure()
    if scorecard is None or scorecard.empty:
        return _empty(fig, "No pillar history to compare", height=400,
                      y_title="Score (out of 100)", x_title="Pillar")
    labels = [f"{row['pillar']}<br>{row['year']} · {row['n_measures']} measure"
              f"{'s' if row['n_measures'] != 1 else ''}"
              for _, row in scorecard.iterrows()]
    fig.add_trace(go.Bar(
        x=labels, y=scorecard["then"], name=scorecard["then_label"].iat[0],
        marker=dict(color="rgba(148,163,184,0.45)", line=dict(width=0)),
        customdata=scorecard["then_year"],
        hovertemplate="%{x}<br>Ten years earlier (%{customdata}): %{y:.1f}"
                      "<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=labels, y=scorecard["now"], name=scorecard["now_label"].iat[0],
        marker=dict(color=[PILLAR_COLOURS.get(p, "#00A6FB")
                           for p in scorecard["pillar_key"]], line=dict(width=0)),
        text=[f"{v:.0f}" for v in scorecard["now"]], textposition="outside",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace", color="#E2E8F0"),
        customdata=scorecard["delta"],
        hovertemplate="%{x}<br>Now: %{y:.1f}<br>Change: %{customdata:+.1f}"
                      "<extra></extra>",
    ))
    fig.update_layout(barmode="group")
    _dark_theme(fig, height=400, y_title="Score (out of 100)", x_title="Pillar")
    fig.update_yaxes(range=[0, 108])
    fig.update_xaxes(tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═══════════════ V2 -- what each option buys per dollar (h-bars) ════════════

def visual2_value_ranking(ranked: pd.DataFrame, chosen_ids: set,
                          unit_cost: str = "USD bn",
                          factor_cost: float = 1e-9) -> go.Figure:
    """Every option ranked by what it adds per unit of money a year, split into
    the ones the budget pays for and the ones it does not.

    The ranking yardstick stays "per $bn" -- one measure costs $0.2bn to $3bn, so
    any smaller unit turns the bars into decimals.  The cost inside the hover is
    still shown in whatever unit the slicer asks for (`per_unit` is one USD bn
    expressed in that unit).
    """
    fig = go.Figure()
    if ranked is None or ranked.empty:
        return _empty(fig, "No options to rank", height=460,
                      x_title="Score points added per $bn a year",
                      y_title="Option")
    per_unit = max(1e9 * float(factor_cost), 1e-12)
    order = list(ranked["short"][::-1])
    for name, colour, keep in (("Pays for", _FUNDED, True), ("Defers", _DEFERRED, False)):
        mask = ranked["id"].isin(chosen_ids) if keep else ~ranked["id"].isin(chosen_ids)
        d = ranked[mask]
        if d.empty:
            continue
        fig.add_trace(go.Bar(
            y=d["short"], x=d["density"], orientation="h", name=name,
            marker=dict(color=colour, line=dict(width=0)),
            text=[f"{v:.1f}" for v in d["density"]],
            textposition="outside",
            textfont=dict(size=10, family="JetBrains Mono, monospace", color="#E2E8F0"),
            customdata=np.stack([d["cost_bn_per_year"] * per_unit,
                                 d["weighted_impact"],
                                 d["feasibility"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>Value: %{x:.1f} points per $bn a year<br>"
                          "Cost: %{customdata[0]:,.2f} " + unit_cost + " a year<br>"
                          "Adds: %{customdata[1]:.1f} points<br>"
                          "Can be delivered: %{customdata[2]}% of the way"
                          "<extra></extra>",
        ))
    _dark_theme(fig, height=460,
                x_title="Score points added per $bn a year (best value on top)",
                y_title=None)
    fig.update_yaxes(categoryorder="array", categoryarray=order,
                     tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═══════════════ V3 -- the measures behind each pillar (heat-map) ═══════════

_MEASURE_WORDS = {
    "imp_dep": "Bought from abroad kept low",
    "gas_ss": "Gas made at home",
    "diversity": "Spread across sources",
    "grid_eff": "Losses kept off the wires",
    "lng_price": "Cheap gas bought by ship",
    "re_share": "Clean share of what is made",
    "pc_elec": "Power per person",
    "coverage": "Demand met at home",
}


def visual3_measure_heatmap(ind_w: pd.DataFrame, pillars_now: dict,
                            seen: dict) -> go.Figure:
    """One cell per measure: the score it got in the pillar's latest reported
    year.  A pillar is the average of its own cells, so the low cells are what
    hold it down.  A measure with no score is left blank, not painted zero."""
    fig = go.Figure()
    # one shared column list: each pillar's measures, in pillar order
    all_cols = []
    for p in pillars_now:
        all_cols += sorted(c for c in ind_w.columns if c.startswith(f"sc_{p}_"))
    rows, custom, row_labels = [], [], []
    for p, score in pillars_now.items():
        if score is None or not np.isfinite(score):
            continue
        yr = int(seen.get(p, 0))
        hit = ind_w[ind_w["calendar_year"] == yr]
        if hit.empty:
            continue
        row = hit.iloc[0]
        vals, yrs = [], []
        for c in all_cols:
            # np.nan keeps the whole z matrix numeric; a None in the row would
            # turn it into an object array the Heatmap rejects.
            keep = c.startswith(f"sc_{p}_") and pd.notna(row[c])
            vals.append(float(row[c]) if keep else np.nan)
            yrs.append(yr if keep else None)
        if all(np.isnan(v) for v in vals):
            continue
        rows.append(vals)
        custom.append(yrs)
        row_labels.append(f"{p.title()} · {score:.0f}")
    if not rows:
        return _empty(fig, "No measure scores to show", height=420,
                      y_title="Pillar (score out of 100)",
                      x_title="Measure inside the pillar")
    x_labels = [_MEASURE_WORDS.get(c.split("_", 2)[2], c) for c in all_cols]
    fig.add_trace(go.Heatmap(
        z=rows, x=x_labels, y=row_labels,
        customdata=custom,
        colorscale=[[0.0, "#EF4444"], [0.5, "#F59E0B"], [1.0, "#10B981"]],
        zmin=0, zmax=100,
        # np.nan cells render blank on their own -- this Plotly build has
        # neither nan_color nor a cell line property (same 5.24 limit as the
        # polar/gauge gaps), so the dark x/y gaps do the separating instead.
        xgap=2, ygap=3,
        text=[[f"{v:.0f}" if np.isfinite(v) else "" for v in r] for r in rows],
        texttemplate="%{text}",
        textfont=dict(size=10.5, family="JetBrains Mono, monospace",
                      color="#0F172A"),
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f} / 100 in "
                      "%{customdata}<extra></extra>",
        showscale=False,
    ))
    # The four pillar groups read from the column order and the hover; a
    # numeric separator line would not anchor on a categorical axis.
    _dark_theme(fig, height=420, y_title="Pillar (its score out of 100)",
                x_title="Measure inside the pillar (its score, same year)")
    fig.update_layout(margin=dict(l=56, r=24, t=45, b=110))
    fig.update_xaxes(tickfont=dict(size=9, color="#CBD5E1"))
    fig.update_yaxes(tickfont=dict(size=10, color="#CBD5E1"))
    return fig


# ═══════════════ V4 -- what the package adds to each pillar ═════════════════

def visual4_pillar_gain(gain: pd.DataFrame, horizon: int) -> go.Figure:
    """Points the recommended package adds over doing nothing, pillar by pillar."""
    fig = go.Figure()
    if gain is None or gain.empty:
        return _empty(fig, "No pillar gain computed", height=420,
                      y_title="Points added (out of 100)", x_title="Pillar")
    fig.add_trace(go.Bar(
        x=gain["pillar"], y=gain["gain"],
        marker=dict(color=[PILLAR_COLOURS.get(p, "#00A6FB")
                           for p in gain["pillar_key"]]),
        text=[f"{v:+.1f}" for v in gain["gain"]], textposition="outside",
        textfont=dict(size=11, family="JetBrains Mono, monospace", color="#E2E8F0"),
        # a plain list keeps the two numbers numeric next to the text note;
        # np.stack would cast the whole row to strings
        customdata=[[float(b), float(o), str(n)] for b, o, n in
                    zip(gain["bau"], gain["optimal"], gain["capped"])],
        hovertemplate="<b>%{x}</b><br>Adds: %{y:+.1f} points<br>"
                      "%{customdata[0]:.1f} without it -> %{customdata[1]:.1f} with it"
                      "<br>%{customdata[2]}<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=0, line=dict(color="rgba(255,255,255,0.35)", width=1.2))
    _dark_theme(fig, height=420, y_title=f"Points added by {horizon} (out of 100)",
                x_title="Pillar")
    fig.update_layout(margin=dict(l=56, r=24, t=45, b=52))
    fig.update_xaxes(tickfont=dict(size=9.5, color="#CBD5E1"))
    return fig


# ═════════════════════ V5 -- budget vs score (diminishing returns) ═════════

def visual5_budget_curve(curve: pd.DataFrame,
                         current_budget: float) -> go.Figure:
    """Composite score at the horizon, drawn against the yearly budget that
    bought it.  The curve is steep while the money is still buying real
    strategies and flattens once the good ones are all funded — the shape
    tells the reader where the next bn stops helping."""
    fig = go.Figure()
    if curve is None or curve.empty or curve["composite_at_horizon"].isna().all():
        return _empty(fig, "No budgets produce a projection", height=380,
                      y_title="Composite score at horizon (0-100)",
                      x_title="Yearly budget (USD bn)")
    c = curve.dropna(subset=["composite_at_horizon"]).sort_values("budget_bn")
    if c.empty:
        return _empty(fig, "No budgets produce a projection", height=380,
                      y_title="Composite score at horizon (0-100)",
                      x_title="Yearly budget (USD bn)")

    fig.add_trace(go.Scatter(
        x=c["budget_bn"].tolist(), y=c["composite_at_horizon"].tolist(),
        mode="lines+markers",
        line=dict(color="#14B8A6", width=2.6, shape="spline", smoothing=0.4),
        marker=dict(size=8, color="#0F172A",
                    line=dict(color="#14B8A6", width=2)),
        customdata=c["n_chosen"].tolist(),
        name="Horizon score",
        hovertemplate=("Budget $%{x:.1f} bn<br>"
                       "Score: <b>%{y:.1f}</b> / 100<br>"
                       "Strategies funded: %{customdata}<extra></extra>"),
    ))

    try:
        cb = float(current_budget)
    except (TypeError, ValueError):
        cb = None
    if cb is not None:
        sub = c.iloc[(c["budget_bn"] - cb).abs().argsort()[:1]]
        if not sub.empty:
            fig.add_trace(go.Scatter(
                x=[float(sub["budget_bn"].iloc[0])],
                y=[float(sub["composite_at_horizon"].iloc[0])],
                mode="markers", name="your budget",
                marker=dict(size=18, color="rgba(0,0,0,0)",
                            line=dict(color="#F59E0B", width=2.2)),
                hoverinfo="skip",
            ))

    _dark_theme(fig, height=380,
                y_title="Composite score at horizon (0-100)",
                x_title="Yearly budget (USD bn)")
    fig.update_layout(legend=dict(orientation="h", y=-0.28, x=0.5,
                                   xanchor="center",
                                   font=dict(size=10, color="#C8CDD6")))
    return fig
