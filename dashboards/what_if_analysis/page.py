"""
dashboards/what_if_analysis/page.py -- Dynamic What-If Scenario & Rules Table Dashboard.

Features:
- Dynamic scenario controls located in the sidebar (Time, Location, Utility, Context).
- Main view dedicated completely to the matching WisRule cognitive rules table.
- No unit selection in sidebar.
"""

from __future__ import annotations

import io
import pandas as pd
import streamlit as st

from core.components import section_title
from core.whatif_engine import filter_wisrule_rules, load_wisrule_rules

TIME_OPTIONS = [
    "All",
    "TI5_2020-25 (2020-2025)",
    "TI4_2015-20 (2015-2020)",
    "TI3_2010-15 (2010-2015)",
    "TI2_2005-10 (2005-2010)",
    "TI1_2000-05 (2000-2005)",
]

LOCATION_OPTIONS = [
    "Industrial Area (LI_High)",
    "Commercial Area (LI_Medium)",
    "Residential / Rural (LI_Low)",
    "All",
]

UTILITY_OPTIONS = [
    "Waste / Losses / Efficiency",
    "Renewable Share",
    "Gas Self-Sufficiency",
    "Import Dependence",
    "CO2 Intensity",
    "Capacity Utilization",
    "All",
]

CONTEXT_OPTIONS = [
    "All",
    "ARE_Policy",
    "Pre_ARE",
    "GDP_Growth",
    "Demand",
    "Capacity",
]


def sidebar() -> None:
    """Dynamic scenario controls placed cleanly in the sidebar."""
    st.sidebar.markdown(
        '<div class="dsh-side-title"><i class="fa-solid fa-sliders"></i> Scenario Slicer</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Adjust scenario dimensions to filter WisRule cognitive association rules.")

    st.sidebar.selectbox(
        "Time Dimension",
        TIME_OPTIONS,
        index=1,
        key="whatif_time",
        help="Select time interval (TI1 to TI5).",
    )

    st.sidebar.selectbox(
        "Location Dimension",
        LOCATION_OPTIONS,
        index=0,
        key="whatif_loc",
        help="Select location demand stratum (e.g. Industrial / LI_High).",
    )

    st.sidebar.selectbox(
        "Utility Dimension",
        UTILITY_OPTIONS,
        index=0,
        key="whatif_util",
        help="Select utility dimension (e.g. Electricity Waste / Losses).",
    )

    st.sidebar.selectbox(
        "Context Dimension",
        CONTEXT_OPTIONS,
        index=0,
        key="whatif_ctx",
        help="Select contextual condition or shock.",
    )

    st.sidebar.divider()


def render() -> None:
    """Render simple, focused What-If Rules table driven by sidebar scenario slicer."""
    st.markdown(
        section_title("Dynamic What-If Scenario & Rules Table", "table", "WisRule Mining"),
        unsafe_allow_html=True,
    )

    # Read active scenario selected in sidebar
    scen_time = st.session_state.get("whatif_time", "TI5_2020-25 (2020-2025)")
    scen_loc = st.session_state.get("whatif_loc", "Industrial Area (LI_High)")
    scen_util = st.session_state.get("whatif_util", "Waste / Losses / Efficiency")
    scen_ctx = st.session_state.get("whatif_ctx", "All")

    # Load rules and apply filters
    all_rules_df = load_wisrule_rules()

    filtered_df = filter_wisrule_rules(
        df=all_rules_df,
        time_filter=scen_time,
        location_filter=scen_loc,
        utility_focus=scen_util,
        context_filter=scen_ctx,
    )

    # Active Scenario Status Banner
    st.markdown(
        f"""
        <div style="background-color: #1A1F2C; border: 1px solid #2B3346; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 13px; color: #E0E6ED;">
                <b style="color: #4A90E2;">Active Scenario:</b>
                Time: <span style="color:#FFF;">{scen_time.split('(')[0].strip()}</span> |
                Location: <span style="color:#FFF;">{scen_loc.split('(')[0].strip()}</span> |
                Utility: <span style="color:#FFF;">{scen_util.split('/')[0].strip()}</span> |
                Context: <span style="color:#FFF;">{scen_ctx}</span>
            </div>
            <div style="font-size: 13px; color: #00E676; font-weight: 600;">
                {len(filtered_df):,} Rules Matched
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not filtered_df.empty:
        cols_to_show = [
            "Rule_ID", "Type", "Rule", "Support", "Confidence",
            "Utility", "WisVal", "Time_Intervals", "Locations"
        ]
        available = [c for c in cols_to_show if c in filtered_df.columns]
        df_display = filtered_df[available].copy()

        st.dataframe(
            df_display,
            use_container_width=True,
            height=540,
            column_config={
                "Rule_ID": st.column_config.TextColumn("Rule ID", width="small"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Rule": st.column_config.TextColumn("Rule Expression (Antecedent => Consequent)", width="large"),
                "Support": st.column_config.NumberColumn("Support (ms)", format="%.3f"),
                "Confidence": st.column_config.NumberColumn("Confidence (mc)", format="%.3f"),
                "Utility": st.column_config.NumberColumn("Utility (mu)", format="%.3f"),
                "WisVal": st.column_config.NumberColumn("WisVal", format="%.2f"),
                "Time_Intervals": st.column_config.TextColumn("Time Intervals", width="medium"),
                "Locations": st.column_config.TextColumn("Locations", width="medium"),
            },
        )

        csv_buf = io.StringIO()
        filtered_df.to_csv(csv_buf, index=False)
        st.download_button(
            label=f"Download Filtered Rules as CSV ({len(filtered_df):,} rules)",
            data=csv_buf.getvalue(),
            file_name="wisrule_scenario_rules.csv",
            mime="text/csv",
        )
    else:
        st.warning("No rules match this specific scenario combination. Try selecting 'All' for one of the dimensions in the sidebar.")
