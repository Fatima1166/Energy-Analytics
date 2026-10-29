"""
Energy Parameter Relationships dashboard (Question 1).

Presentation layer only -- pairwise correlations and the rolling-stability
line are computed in core/parameter_relationships.py.

Kept intentionally minimal: this dashboard answers the two halves of
Question 1 -- how are the tracked energy / economic / emissions parameters
related (the correlation visuals), and what are their predicted values under
a what-if (the V9 forecast section, driven by the sidebar's What-if
Assumptions).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.components import conclusion_card, section_title
from core.icons import icon
from core.parameter_relationships import (
    DEFAULT_EFFICIENCY,
    DEFAULT_GDP_GROWTH,
    DEFAULT_POP_GROWTH,
    PARAMETERS,
    HISTORY_END,
    build_relationship_data,
    forecast_path,
    pairwise_fit,
    rolling_correlation,
)
from core.queries import (
    Q_CO2,
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_ENERGY_OVERVIEW,
    Q_LNG,
    Q_NATURAL_GAS,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.unit_slicer import get_units
from core.units import display_factor

from .charts import (
    visual1_corr_heatmap,
    visual2_pair_scatter,
    visual3_rolling_corr,
    visual7_top_pairs,
    visual8_corr_distribution,
    visual9_forecast_path,
)
from .config import DEFAULT_PERIOD, DEFAULT_ROLL_WINDOW

FILTERS_KEY = "q1_filters"
_CHART_CONFIG = {"displayModeBar": False}
MIN_SPAN = 8                       # shortest period the sidebar allows (engine needs 6 joint years)
YEAR_MIN, YEAR_MAX = 1999, HISTORY_END

# Compact KPI skin -- slim header strip so cards never tower over the charts.
# The 148px box still clears the 23px headline value used on Q4-Q8 by ~15px.
_COMPACT_CSS = """
<style>
.kpi-balance.kpi-compact {
    height: 148px !important;
    min-height: 148px !important;
    max-height: 148px !important;
    justify-content: flex-start !important;
    padding: 10px 12px 10px !important;
    overflow: hidden !important;
}
.kpi-balance.kpi-compact .kpi-balance-details {
    margin-top: auto !important;
    padding-top: 4px !important;
}
</style>
"""

_LABELS = {k: m["label"] for k, m in PARAMETERS.items()}


def _unit_for(family: str, stored: str) -> tuple:
    """(unit label, display factor) for a parameter's family."""
    if family in ("none", "economic"):
        return stored, 1.0
    units = get_units()
    unit = units.get(family, "")
    return (unit or stored), display_factor(family, unit) if unit else 1.0


# --- Sidebar controls ---

def _enforce_min_span() -> None:
    """Push the picked range back to MIN_SPAN years, before the app reruns.

    The engine needs MIN_PAIR_OBS (6) joint years before it will compute a
    correlation, so the range is clamped here -- in a callback the new value
    is corrected before the slider is re-read, keeping the handles and the
    charts in sync.
    """
    lo, hi = st.session_state["q1_period"]
    lo, hi = int(lo), int(hi)
    if hi - lo + 1 < MIN_SPAN:
        hi = min(lo + MIN_SPAN - 1, YEAR_MAX)
        lo = max(hi - MIN_SPAN + 1, YEAR_MIN)
        st.session_state["q1_period"] = (lo, hi)


def sidebar() -> None:
    """Called by app.py before the global unit slicer.

    One control only -- the analysis period, as a two-handle range slider.
    Everything else is automatic: the pair to inspect is the strongest link in
    the matrix, and the rolling window adapts to the chosen span.
    """
    st.sidebar.markdown('<div class="dsh-side-title">Analysis Period</div>',
                        unsafe_allow_html=True)

    period = st.sidebar.slider(
        "Analysis period",
        min_value=YEAR_MIN,
        max_value=YEAR_MAX,
        value=(max(YEAR_MIN, DEFAULT_PERIOD[0]), min(YEAR_MAX, DEFAULT_PERIOD[1])),
        step=1,
        format="%d",
        key="q1_period",
        label_visibility="collapsed",
        on_change=_enforce_min_span,
    )
    st.session_state[FILTERS_KEY] = {
        "period": (int(period[0]), int(period[1])),
    }
    st.sidebar.caption(f"Minimum {MIN_SPAN} years -- both charts need joint data.")
    st.sidebar.divider()

    # --- What-if assumptions (Question 1's second half) ---
    # The engine grows each forecastable parameter by
    #   autonomy + β_gdp·GDP growth + β_pop·population growth − efficiency,
    # with autonomy back-solved from history, so the defaults leave the
    # baseline untouched and every delta here is purely the assumption's doing.
    st.sidebar.markdown('<div class="dsh-side-title">What-if Assumptions</div>',
                        unsafe_allow_html=True)
    wi_gdp = st.sidebar.slider("GDP growth", 0.0, 8.0, DEFAULT_GDP_GROWTH, 0.1,
                               format="%.1f%%", key="q1_wi_gdp",
                               help="Yearly GDP growth the what-if assumes.")
    wi_pop = st.sidebar.slider("Population growth", 0.0, 4.0, DEFAULT_POP_GROWTH,
                               0.1, format="%.1f%%", key="q1_wi_pop",
                               help="Yearly population growth the what-if assumes.")
    wi_eff = st.sidebar.slider("Efficiency gains", 0.0, 3.0, DEFAULT_EFFICIENCY,
                               0.1, format="%.1f%%", key="q1_wi_eff",
                               help="Yearly decoupling drag subtracted from every "
                                    "parameter's growth.")
    st.session_state[FILTERS_KEY]["whatif"] = {
        "gdp_growth_pct": float(wi_gdp),
        "pop_growth_pct": float(wi_pop),
        "efficiency_pct": float(wi_eff),
    }
    st.sidebar.caption("Predictions run to 2035 · defaults keep the historical trend.")
    st.sidebar.divider()


# --- KPI Card UI ---

def _kpi_card(code: str, title: str, value: str, unit: str, rows: list,
              accent: str = "#00A6FB", icon_name: str = "data",
              badge: str = "", badge_colour: str = "#00A6FB",
              value_size: int = 23) -> str:
    """Compact dark glassmorphism KPI card."""
    detail = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:8px;'
        f'font-size:9px;color:#94A3B8;padding:1px 0;">'
        f'<span>{label}</span><span style="color:{colour};font-weight:700;">{text}</span>'
        f'</div>'
        for label, text, colour in rows
    )
    badge_html = (f'<span style="background:{badge_colour}22;color:{badge_colour};'
                  f'font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;'
                  f'border:1px solid {badge_colour}55;white-space:nowrap;">{badge}</span>'
                  if badge else "")
    return f"""
<div class="kpi-balance kpi-compact" style="border: 1px solid {accent}44;">
  <div style="position:absolute;top:0;left:0;right:0;height:2.5px;
              background:linear-gradient(90deg,{accent}00,{accent},{accent}00);"></div>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;">
    <div style="display:flex;align-items:center;gap:6px;">
      <div style="width:22px;height:22px;background:{accent}22;border:1px solid {accent}44;
                  border-radius:6px;display:flex;align-items:center;justify-content:center;
                  color:{accent};font-size:10px;">{icon(icon_name)}</div>
      <div style="color:#94A3B8;font-size:8.5px;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.6px;">{code}</div>
    </div>
    {badge_html}
  </div>
  <div style="color:#E2E8F0;font-size:10px;font-weight:600;line-height:1.25;
              margin-bottom:2px;">{title}</div>
  <div style="display:flex;align-items:baseline;gap:6px;">
    <span style="color:{accent};font-size:{value_size}px;font-weight:800;line-height:1;
                 font-family:'JetBrains Mono','Courier New',monospace;">{value}</span>
    <span style="color:#64748B;font-size:9px;font-weight:600;">{unit}</span>
  </div>
  <div class="kpi-balance-details">{detail}</div>
</div>
"""


# --- Main Dashboard Render ---

def render() -> None:
    """Renders the Parameter Relationships dashboard.

    Focus: how are the tracked parameters related?  Everything on this page
    is a different view of the same correlation signal -- the matrix, the
    top pairs, the distribution, the pair explorer, and the rolling check.
    """
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)

    flt = st.session_state.get(FILTERS_KEY, {})
    period = flt.get("period", DEFAULT_PERIOD)
    whatif = flt.get("whatif", {})
    span = int(period[1]) - int(period[0]) + 1
    # Keep the rolling window inside the selected period: half the span,
    # clamped to 4..default so the stability line always has enough points.
    roll_window = int(np.clip(span // 2, 4, DEFAULT_ROLL_WINDOW))

    data = build_relationship_data(
        econ_df=run_query(Q_ECONOMIC),
        re_df=run_query(Q_RENEWABLE_ENERGY),
        gen_df=run_query(Q_ELEC_GEN),
        td_df=run_query(Q_TD_LOSSES),
        gas_df=run_query(Q_NATURAL_GAS),
        lng_df=run_query(Q_LNG),
        overview_df=run_query(Q_ENERGY_OVERVIEW),
        co2_df=run_query(Q_CO2),
        period=period,
        roll_window=roll_window,
        **whatif,
    )

    corr = data["corr"]
    strongest = data["strongest"]
    y0, y1 = data["period"]

    # The pair explorer & rolling charts follow the strongest link automatically
    # -- no manual pair selection anywhere on the page. Only the two per-pair
    # views are recomputed; the matrix and frame are reused as-is.
    if strongest:
        pair_x, pair_y = strongest[0], strongest[1]
    else:
        pair_x, pair_y = "gdp", "demand"
    fit = pairwise_fit(data["frame"], pair_x, pair_y, y0, y1)
    roll = rolling_correlation(data["frame"], pair_x, pair_y, roll_window, y0, y1)
    data["fit"] = fit
    data["rolling"] = roll

    # ---- KPI strip: two headline correlation stats ----
    n_params = int(corr.notna().any(axis=1).sum()) if corr is not None else 0
    strong_links = 0
    if corr is not None and not corr.empty:
        tri = corr.where(~np.eye(len(corr), dtype=bool))
        strong_links = int((tri.abs() >= 0.7).sum().sum() // 2)

    # Cards take three of the four slices, so each card is about a quarter
    # of the page width and the strip still ends with a small breathing gap.
    kpi_cols = st.columns([1, 1, 1, 0.4])

    with kpi_cols[0]:
        st.markdown(
            _kpi_card(
                code="K1",
                title=f"Parameters Analysed ({period[0]}–{period[1]})",
                value=f"{n_params}",
                unit="parameters",
                rows=[
                    ("Pairwise links", f"{n_params * (n_params - 1) // 2}", "#CBD5E1"),
                    ("Strong |r|≥0.7", f"{strong_links}", "#14B8A6"),
                    ("Rolling window", f"{roll_window} yr", "#94A3B8"),
                ],
                accent="#00A6FB",
                icon_name="data",
            ),
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        if strongest:
            a, b, r = strongest
            st.markdown(
                _kpi_card(
                    code="K2",
                    title="Strongest Relationship",
                    value=f"{r:+.2f}",
                    unit="Pearson r",
                    rows=[
                        ("Driver", _LABELS[a], "#CBD5E1"),
                        ("Response", _LABELS[b], "#CBD5E1"),
                        ("Nature", "co-moving" if r > 0 else "inverse",
                         "#10B981" if r > 0 else "#EF4444"),
                    ],
                    accent="#14B8A6",
                    icon_name="route",
                    badge="max |r|",
                    badge_colour="#14B8A6",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _kpi_card(code="K2", title="Strongest Relationship",
                          value="–", unit="",
                          rows=[("Data", "not enough overlap", "#94A3B8")],
                          accent="#14B8A6", icon_name="route"),
                unsafe_allow_html=True,
            )

    with kpi_cols[2]:
        pairs_df = data["pairs"]
        if pairs_df is not None and not pairs_df.empty:
            w = pairs_df.iloc[-1]          # weakest link (pairs sorted by |r|)
            wr = float(w["r"])
            st.markdown(
                _kpi_card(
                    code="K3",
                    title="Weakest Relationship",
                    value=f"{wr:+.2f}",
                    unit="Pearson r",
                    rows=[
                        ("Parameter", _LABELS[w["param_a"]], "#CBD5E1"),
                        ("Parameter", _LABELS[w["param_b"]], "#CBD5E1"),
                        ("Links tested", f"{len(pairs_df)}", "#94A3B8"),
                    ],
                    accent="#F59E0B",
                    icon_name="insights",
                    badge="min |r|",
                    badge_colour="#F59E0B",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                _kpi_card(code="K3", title="Weakest Relationship",
                          value="–", unit="",
                          rows=[("Data", "not enough overlap", "#94A3B8")],
                          accent="#F59E0B", icon_name="insights"),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ---- Row 1: correlation heat-map (full width) ----
    with st.columns(1)[0]:
        st.markdown(section_title("The Relationship Web — Correlation Matrix",
                                  "data", "Objective 1"), unsafe_allow_html=True)
        st.caption("Green cells grow together, red cells move apart, blank cells have no data.")
        fig1 = visual1_corr_heatmap(corr, [_LABELS[k] for k in corr.index])
        st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 2: reading the web (ranking + distribution) ----
    w1, w2 = st.columns(2)

    with w1:
        st.markdown(section_title("Top Relationship Ranking",
                                  "insights", "Objective 1"), unsafe_allow_html=True)
        st.caption("The 12 strongest links, ranked. Green = move together, red = move apart.")
        fig7 = visual7_top_pairs(data["pairs"], _LABELS, n=12)
        st.plotly_chart(fig7, use_container_width=True, config=_CHART_CONFIG)

    with w2:
        st.markdown(section_title("Correlation Distribution",
                                  "overview", "Objective 1"), unsafe_allow_html=True)
        st.caption("Tall bars at the ends = system closely linked; tall bars in the middle = mostly unrelated.")
        fig8 = visual8_corr_distribution(data["pairs"])
        st.plotly_chart(fig8, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 3: pair explorer + rolling stability ----
    p1, p2 = st.columns(2)

    with p1:
        xu, xf = _unit_for(PARAMETERS[pair_x]["family"], PARAMETERS[pair_x]["unit"])
        yu, yf = _unit_for(PARAMETERS[pair_y]["family"], PARAMETERS[pair_y]["unit"])
        st.markdown(section_title(f"Pair Explorer — {_LABELS[pair_x]} vs {_LABELS[pair_y]}",
                                  "route", "Objective 1"), unsafe_allow_html=True)
        st.caption("Each dot is one year. The dashed line shows the trend — tighter dots mean a stronger link.")
        fig2 = visual2_pair_scatter(fit, _LABELS[pair_x], _LABELS[pair_y],
                                    xu, yu, xf, yf)
        st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    with p2:
        st.markdown(section_title("Is the Link Stable? — Rolling Correlation",
                                  "scenario", "Objective 2"), unsafe_allow_html=True)
        st.caption("A steady line near the top or bottom = reliable link; a line crossing the middle = changing link.")
        fig3 = visual3_rolling_corr(roll,
                                    f"{_LABELS[pair_x]} × {_LABELS[pair_y]}",
                                    roll_window)
        st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    # ---- Row 4: what-if predicted values (Question 1's second half) ----
    fc = data["forecasts"]
    if fc is not None and not fc.empty:
        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # Table gets its own full-width row so every parameter sits on a
        # single horizontal row instead of stacking down a narrow column.
        st.markdown(section_title("What-if Predicted Values",
                                  "scenario", "Objective 3"),
                    unsafe_allow_html=True)
        st.caption("Each parameter grown by its own trend plus the sidebar's "
                   "GDP / population / efficiency assumptions. A 0% what-if "
                   "difference means the assumption left the trend untouched.")

        def _mag(v: float) -> str:
            """Compact magnitude ladder so one decimal always reads clean."""
            a = abs(v)
            for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
                if a >= div:
                    return f"{v / div:,.1f}{suf}"
            return f"{v:,.1f}"

        rows = []
        for r in fc.to_dict("records"):
            fu, ff = _unit_for(r["family"], r["unit"])
            rows.append({
                "Parameter": r["label"],
                "Last measured": f"{_mag(r['last_value'] * ff)} {fu} · {int(r['last_year'])}",
                "Trend to 2035": f"{_mag(r['baseline_value'] * ff)} {fu}",
                "What-if 2035": f"{_mag(r['whatif_value'] * ff)} {fu}",
                "What-if Δ": f"{r['delta_pct']:+.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # ---- Prediction path (full width under the table) ----
        pick_key = st.selectbox(
            "Parameter to project",
            fc["key"].tolist(),
            index=fc["key"].tolist().index(data["target_key"])
            if data["target_key"] in set(fc["key"]) else 0,
            format_func=lambda k: PARAMETERS[k]["label"],
            key="q1_fc_target")
        row = fc[fc["key"] == pick_key].iloc[0]
        path_df = forecast_path(data["frame"], pick_key, row,
                                int(data["horizon"]))
        pu, pf = _unit_for(PARAMETERS[pick_key]["family"],
                           PARAMETERS[pick_key]["unit"])
        st.markdown(section_title(
            f"Prediction Path — {PARAMETERS[pick_key]['label']}",
            "data", "Objective 3"), unsafe_allow_html=True)
        st.caption("Blue is what was recorded; the dotted lines continue each "
                   "scenario from the last measured year to 2035.")
        fig9 = visual9_forecast_path(
            path_df.assign(value=path_df["value"] * pf),
            PARAMETERS[pick_key]["label"], pu, int(data["horizon"]))
        st.plotly_chart(fig9, use_container_width=True, config=_CHART_CONFIG)

    # ---- Bottom line ----
    if strongest:
        _a, _b, _r = strongest
        _how = ("when one goes up, the other goes up too" if _r > 0
                else "when one goes up, the other goes down")
        line1 = (f"The tightest link is {_LABELS[_a]} with {_LABELS[_b]} "
                 f"({_r:+.2f}) — {_how}.")
    else:
        line1 = "No two parameters share enough years together for a firm link."
    n_links = len(pairs_df) if pairs_df is not None else 0
    line2 = (f"{strong_links} of {n_links} links tested move tight together "
             f"(0.7 or more); the rest run mostly on their own.")
    if fc is not None and not fc.empty:
        wi = data["inputs"]
        _big = fc.loc[fc["delta_pct"].abs().idxmax()]
        line3 = (f"Under the what-if ({wi['gdp_growth_pct']:.1f}% GDP, "
                 f"{wi['pop_growth_pct']:.1f}% population, "
                 f"{wi['efficiency_pct']:.1f}% efficiency), "
                 f"{_big['label']} moves the most by 2035 "
                 f"({_big['delta_pct']:+.1f}% against its own trend).")
    else:
        line3 = "No parameter has enough history for a what-if projection yet."
    st.markdown(conclusion_card([line1, line2, line3]), unsafe_allow_html=True)
