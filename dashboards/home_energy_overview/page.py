"""
dashboards/home_energy_overview/page.py -- Executive Landing Command Center
for the Pakistan National Energy Analytics Platform.

Vibrant, colorful, and institutional design:
1. Executive Sidebar: Data coverage, live unit slicers.
2. Headline KPI Strip: Equal-height cards on the shared header skin, with animated accent edges.
3. Strategic Visualizations: Energy balance, fuel mix, emissions, and generation.
4. Question Hub: The 10 dashboards shown side by side in one row per topic.
5. Key Takeaways: Short policy summary cards.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from config.database import run_query
from core.energy_overview import (
    co2_history,
    fuel_mix_latest,
    generation_history,
    headline_snapshot,
    record_counts,
    supply_demand_history,
)
from core.queries import (
    Q_CO2,
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_ENERGY_OVERVIEW,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
)
from core.unit_slicer import get_units, render_sidebar_unit_slicer
from core.units import display_factor
from dashboards.registry import DASHBOARDS

from .charts import (
    visual1_supply_demand,
    visual2_fuel_donut,
    visual3_co2_bars,
    visual4_generation_trajectory,
)

_CHART_CONFIG = {"displayModeBar": False}

# ══════════════════════════════════════════════════════════════════════════════
# QUESTION METADATA ARCHITECTURE & COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════
QUESTION_METADATA = {
    "q1": {
        "pillar": "Supply & Demand",
        "pillar_id": "p1",
        "pillar_color": "#00A6FB",
        "glow_color": "rgba(0, 166, 251, 0.22)",
        "border_color": "rgba(0, 166, 251, 0.4)",
        "chip_bg": "rgba(0, 166, 251, 0.12)",
        "chip_text": "#7DD3FC",
        "btn_from": "#00A6FB",
        "btn_to": "#0284C7",
        "tag": "Econometric Modeling",
        "code_display": "Q-01",
        "short_title": "Which Indicators Move Together",
        "strategic_question": "See which energy and economic figures rise or fall together, and how steady those links stay over time.",
        "methods": ["Correlation Map", "Strongest Links", "Rolling Stability"],
    },
    "q2": {
        "pillar": "Clean Energy",
        "pillar_id": "p2",
        "pillar_color": "#10B981",
        "glow_color": "rgba(16, 185, 129, 0.22)",
        "border_color": "rgba(16, 185, 129, 0.4)",
        "chip_bg": "rgba(16, 185, 129, 0.12)",
        "chip_text": "#6EE7B7",
        "btn_from": "#10B981",
        "btn_to": "#059669",
        "tag": "Scenario Simulation",
        "code_display": "Q-02",
        "short_title": "Adding More Solar and Wind",
        "strategic_question": "Compare what happens if we build more solar and wind: cleaner power and less spent on imported gas.",
        "methods": ["Scenario Compare", "CO₂ Saved", "Import Bills Saved"],
    },
    "q3": {
        "pillar": "Grid & Infrastructure",
        "pillar_id": "p3",
        "pillar_color": "#F59E0B",
        "glow_color": "rgba(245, 158, 11, 0.22)",
        "border_color": "rgba(245, 158, 11, 0.4)",
        "chip_bg": "rgba(245, 158, 11, 0.12)",
        "chip_text": "#FCD34D",
        "btn_from": "#F59E0B",
        "btn_to": "#D97706",
        "tag": "Diagnostic Audit",
        "code_display": "Q-03",
        "short_title": "National Targets vs Reality",
        "strategic_question": "Check national energy targets against what is really happening, and see where the system falls short.",
        "methods": ["Loss Scorecard", "Import Share", "Target Gap"],
    },
    "q4": {
        "pillar": "Supply & Demand",
        "pillar_id": "p1",
        "pillar_color": "#00A6FB",
        "glow_color": "rgba(0, 166, 251, 0.22)",
        "border_color": "rgba(0, 166, 251, 0.4)",
        "chip_bg": "rgba(0, 166, 251, 0.12)",
        "chip_text": "#7DD3FC",
        "btn_from": "#00A6FB",
        "btn_to": "#0284C7",
        "tag": "Long-Term Forecasting",
        "code_display": "Q-04",
        "short_title": "Future Energy Demand",
        "strategic_question": "How much energy the country will need up to 2035, based on economic growth and population.",
        "methods": ["GDP Drivers", "Sector Split", "Low / Base / High"],
    },
    "q5": {
        "pillar": "Supply & Demand",
        "pillar_id": "p1",
        "pillar_color": "#00A6FB",
        "glow_color": "rgba(0, 166, 251, 0.22)",
        "border_color": "rgba(0, 166, 251, 0.4)",
        "chip_bg": "rgba(0, 166, 251, 0.12)",
        "chip_text": "#7DD3FC",
        "btn_from": "#00A6FB",
        "btn_to": "#0284C7",
        "tag": "Supply Adequacy",
        "code_display": "Q-05",
        "short_title": "Future Energy Supply",
        "strategic_question": "Whether supply and power capacity can keep up with demand up to 2035.",
        "methods": ["Fuel Trajectory", "Generation Mix", "Spare Capacity"],
    },
    "q6": {
        "pillar": "Grid & Infrastructure",
        "pillar_id": "p3",
        "pillar_color": "#F59E0B",
        "glow_color": "rgba(245, 158, 11, 0.22)",
        "border_color": "rgba(245, 158, 11, 0.4)",
        "chip_bg": "rgba(245, 158, 11, 0.12)",
        "chip_text": "#FCD34D",
        "btn_from": "#F59E0B",
        "btn_to": "#D97706",
        "tag": "Supply Chain Efficiency",
        "code_display": "Q-06",
        "short_title": "Fuel and Supply Chain Efficiency",
        "strategic_question": "Where fuel is wasted, how fast local gas is running out, and how much clean power we throw away.",
        "methods": ["Efficiency Scorecard", "Gas Depletion", "Wasted Output"],
    },
    "q7": {
        "pillar": "Cost & Dispatch",
        "pillar_id": "p4",
        "pillar_color": "#A78BFA",
        "glow_color": "rgba(167, 139, 250, 0.22)",
        "border_color": "rgba(167, 139, 250, 0.4)",
        "chip_bg": "rgba(167, 139, 250, 0.12)",
        "chip_text": "#DDD6FE",
        "btn_from": "#A78BFA",
        "btn_to": "#7C3AED",
        "tag": "Financial Economics",
        "code_display": "Q-07",
        "short_title": "Cost of Power Generation",
        "strategic_question": "What it costs to buy power from each technology, and how fuel price swings change consumer bills.",
        "methods": ["Cost by Technology", "Fuel Price Shocks", "Tariff Impact"],
    },
    "q8": {
        "pillar": "Clean Energy",
        "pillar_id": "p2",
        "pillar_color": "#10B981",
        "glow_color": "rgba(16, 185, 129, 0.22)",
        "border_color": "rgba(16, 185, 129, 0.4)",
        "chip_bg": "rgba(16, 185, 129, 0.12)",
        "chip_text": "#6EE7B7",
        "btn_from": "#10B981",
        "btn_to": "#059669",
        "tag": "Strategic Optimization",
        "code_display": "Q-08",
        "short_title": "Sustainable Energy Strategy",
        "strategic_question": "The best mix of policies to grow cleanly, compared with carrying on as usual to 2035.",
        "methods": ["4-Part Index", "Policy Package", "Trade-offs"],
    },
    "q9": {
        "pillar": "Grid & Infrastructure",
        "pillar_id": "p3",
        "pillar_color": "#F59E0B",
        "glow_color": "rgba(245, 158, 11, 0.22)",
        "border_color": "rgba(245, 158, 11, 0.4)",
        "chip_bg": "rgba(245, 158, 11, 0.12)",
        "chip_text": "#FCD34D",
        "btn_from": "#F59E0B",
        "btn_to": "#D97706",
        "tag": "Operational Diagnostics",
        "code_display": "Q-09",
        "short_title": "Day-to-Day Operating Problems",
        "strategic_question": "Power plants running below capacity, seasonal gas shortages, and contract rules that waste fuel.",
        "methods": ["Plant Utilization", "Gas Shortfall", "Take-or-Pay Cost"],
    },
    "q10": {
        "pillar": "Cost & Dispatch",
        "pillar_id": "p4",
        "pillar_color": "#A78BFA",
        "glow_color": "rgba(167, 139, 250, 0.22)",
        "border_color": "rgba(167, 139, 250, 0.4)",
        "chip_bg": "rgba(167, 139, 250, 0.12)",
        "chip_text": "#DDD6FE",
        "btn_from": "#A78BFA",
        "btn_to": "#7C3AED",
        "tag": "Constrained Optimization",
        "code_display": "Q-10",
        "short_title": "Cheapest Way to Run Power Plants",
        "strategic_question": "Work out the lowest-cost, low-carbon way to run power plants while respecting limits for each sector.",
        "methods": ["Least-Cost Solver", "Dispatch Order", "Carbon Limits"],
    },
}

PILLARS = [
    {
        "id": "p1",
        "short_name": "Supply & Demand",
        "title": "Supply & Demand",
        "color": "#00A6FB",
        "keys": ["q1", "q4", "q5"],
    },
    {
        "id": "p2",
        "short_name": "Clean Energy",
        "title": "Clean Energy",
        "color": "#10B981",
        "keys": ["q2", "q8"],
    },
    {
        "id": "p3",
        "short_name": "Grid & Infrastructure",
        "title": "Grid & Infrastructure",
        "color": "#F59E0B",
        "keys": ["q3", "q6", "q9"],
    },
    {
        "id": "p4",
        "short_name": "Cost & Dispatch",
        "title": "Cost & Dispatch",
        "color": "#A78BFA",
        "keys": ["q7", "q10"],
    },
]

# ══════════════════════════════════════════════════════════════════════════════
# VIBRANT & BALANCED CSS ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
_HOME_CSS = """
<style>
/* ---------------- Equal Column Stretch ---------------- */
[data-testid="column"],
[data-testid="stColumn"],
.stColumn {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 0 !important;
    height: 100% !important;
}

/* ---------------- Section Divider Title ---------------- */
.exec-sect-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 18px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
/* The first block sits directly under the shared header card -- keep it tight. */
.exec-sect-line.sect-first { margin-top: 2px; }
.exec-sect-line .sect-title-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.exec-sect-line .sect-bar {
    width: 4.5px;
    height: 20px;
    border-radius: 2px;
    background: linear-gradient(180deg, #00A6FB 0%, #10B981 100%);
}
.exec-sect-line h2 {
    font-size: 17px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.2px;
    margin: 0;
}
.exec-sect-line p {
    font-size: 12px;
    color: #8B95A7;
    margin: 0 0 0 8px;
    font-weight: 500;
}
.exec-sect-line .sect-badge {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #38BDF8;
    background: rgba(0, 166, 251, 0.1);
    border: 1px solid rgba(0, 166, 251, 0.3);
    padding: 4px 10px;
    border-radius: 6px;
}

/* ---------------- Headline KPI Cards (same skin as the header card) ---------------- */
.kpi-row-card {
    position: relative;
    overflow: hidden;
    border-radius: 12px;
    padding: 14px 18px 15px 18px;
    height: 128px !important;
    min-height: 128px !important;
    max-height: 128px !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(14, 17, 23, 0.98) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
/* Animated accent strip, mirroring the header card's bottom edge. */
.kpi-row-card::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2.5px;
    background: linear-gradient(90deg, var(--acc-a), var(--acc-b), var(--acc-a));
    background-size: 300% 100%;
    animation: gradientShift 6s ease infinite;
}
.kpi-row-card:hover {
    transform: translateY(-2px);
    border-color: var(--acc-a);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
}

.kpi-card-blue  { --acc-a: #00A6FB; --acc-b: #2ECC71; }
.kpi-card-amber { --acc-a: #F4A300; --acc-b: #FB7185; }
.kpi-card-green { --acc-a: #2ECC71; --acc-b: #00A6FB; }
.kpi-card-red   { --acc-a: #F43F5E; --acc-b: #F4A300; }

.kpi-card-blue  .kpi-row-val { color: #38BDF8; }
.kpi-card-amber .kpi-row-val { color: #FBBF24; }
.kpi-card-green .kpi-row-val { color: #34D399; }
.kpi-card-red   .kpi-row-val { color: #FB7185; }

.kpi-card-blue  .kpi-row-code { background: rgba(0, 166, 251, 0.14);  color: #38BDF8; border: 1px solid rgba(0, 166, 251, 0.35); }
.kpi-card-amber .kpi-row-code { background: rgba(245, 158, 11, 0.14); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.35); }
.kpi-card-green .kpi-row-code { background: rgba(16, 185, 129, 0.14); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.35); }
.kpi-card-red   .kpi-row-code { background: rgba(239, 68, 68, 0.14);  color: #FB7185; border: 1px solid rgba(239, 68, 68, 0.35); }

.kpi-row-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}
.kpi-row-code {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 7px;
    border-radius: 4px;
    flex-shrink: 0;
}
.kpi-row-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #CBD5E1;
    flex: 1;
    min-width: 0;
    text-align: right;
    line-height: 1.25;
}
.kpi-row-val {
    font-size: 24px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 2px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-row-val small {
    font-size: 11px;
    font-weight: 600;
    color: #94A3B8;
    margin-left: 5px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.kpi-row-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    font-size: 10.5px;
}
.kpi-trend-pill {
    font-size: 9px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 1px 6px;
    border-radius: 4px;
    letter-spacing: 0.2px;
    white-space: nowrap;
    flex-shrink: 0;
}
.kpi-trend-pill.good {
    color: #34D399;
    background: rgba(16, 185, 129, 0.16);
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.kpi-trend-pill.bad {
    color: #F87171;
    background: rgba(239, 68, 68, 0.16);
    border: 1px solid rgba(239, 68, 68, 0.35);
}
.kpi-trend-pill.neutral {
    color: #94A3B8;
    background: rgba(148, 163, 184, 0.12);
    border: 1px solid rgba(148, 163, 184, 0.25);
}
.kpi-context-note {
    color: #CBD5E1;
    font-size: 10.5px;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ---------------- Colorful Module Cards (One Balanced Row Per Pillar) ---------------- */
.hub-card {
    border-radius: 10px;
    padding: 14px 16px 14px 16px;
    height: 212px !important;
    min-height: 212px !important;
    max-height: 212px !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    margin-bottom: 16px;
    position: relative;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.hub-card:hover {
    transform: translateY(-2px);
}
.hub-arrow {
    position: absolute;
    bottom: 12px;
    right: 14px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    z-index: 5;
}
.hub-card:hover .hub-arrow {
    transform: scale(1.12) translateX(3px);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
}
.hub-card-link {
    text-decoration: none !important;
    color: inherit !important;
    display: block !important;
}
.hub-card-link:hover {
    text-decoration: none !important;
    color: inherit !important;
}
.hub-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 6px;
}
.hub-code {
    font-size: 10.5px;
    font-weight: 800;
    padding: 2.5px 8px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
}
.hub-pillar-tag {
    font-size: 9.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    line-height: 1.3;
    text-align: right;
    flex-shrink: 0;
}
.hub-title {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 4px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.hub-desc {
    color: #94A3B8;
    font-size: 11.5px;
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 8px;
}
.hub-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    padding-right: 34px;
}
.hub-chip {
    font-size: 9.5px;
    font-weight: 600;
    padding: 2.5px 7px;
    border-radius: 4px;
    white-space: nowrap;
}

/* ---------------- Colorful Action Buttons ---------------- */
div.stButton > button {
    border-radius: 8px !important;
    padding: 8px 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    margin-bottom: 16px !important;
    transition: all 0.25s ease !important;
}

/* ---------------- Sidebar Styling ---------------- */
.sidebar-brand-card {
    background: linear-gradient(145deg, rgba(0, 166, 251, 0.12) 0%, rgba(16, 185, 129, 0.12) 50%, #0E131C 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-top: 3px solid #10B981;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.sbc-title {
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.sbc-sub {
    color: #94A3B8;
    font-size: 11px;
    margin-top: 3px;
}
.sbc-status {
    color: #34D399;
    font-size: 10.5px;
    font-weight: 700;
    margin-top: 8px;
    letter-spacing: 0.5px;
}
.sbc-status .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    display: inline-block;
    margin-right: 5px;
}
.sb-spec-box {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
}
.sb-spec-row {
    display: flex;
    justify-content: space-between;
    font-size: 11.5px;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.sb-spec-row:last-child {
    border-bottom: none;
}
.sb-spec-row span {
    color: #94A3B8;
}
.sb-spec-row b {
    color: #38BDF8;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}

/* ---------------- Tabs ---------------- */
[data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255, 255, 255, 0.02);
    padding: 5px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 14px;
}
[data-baseweb="tab"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    color: #94A3B8 !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease !important;
}
[data-baseweb="tab"]:hover {
    color: #F8FAFC !important;
    background: rgba(255, 255, 255, 0.05) !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: linear-gradient(135deg, rgba(0, 166, 251, 0.2) 0%, rgba(16, 185, 129, 0.16) 100%) !important;
    border: 1px solid #38BDF8 !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(0, 166, 251, 0.25) !important;
}

/* ---------------- Colorful Takeaway Grid ---------------- */
.takeaway-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 10px;
}
.takeaway-card {
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s ease;
}
.takeaway-card:hover {
    transform: translateY(-2px);
}
.takeaway-card .lead-tag {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
}
.takeaway-card h4 {
    color: #F1F5F9;
    font-size: 13px;
    font-weight: 800;
    margin: 0 0 6px 0;
}
.takeaway-card p {
    color: #CBD5E1;
    font-size: 11.5px;
    line-height: 1.55;
    margin: 0;
}

/* 4 Takeaway Card Color Themes */
.tcard-blue {
    background: linear-gradient(145deg, rgba(0, 166, 251, 0.14) 0%, rgba(13, 22, 36, 0.95) 55%, rgba(10, 16, 26, 0.98) 100%);
    border: 1px solid rgba(0, 166, 251, 0.35);
    border-top: 3px solid #00A6FB;
}
.tcard-blue .lead-tag { color: #38BDF8; }

.tcard-green {
    background: linear-gradient(145deg, rgba(16, 185, 129, 0.14) 0%, rgba(12, 28, 22, 0.95) 55%, rgba(8, 18, 14, 0.98) 100%);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-top: 3px solid #10B981;
}
.tcard-green .lead-tag { color: #34D399; }

.tcard-amber {
    background: linear-gradient(145deg, rgba(245, 158, 11, 0.14) 0%, rgba(32, 24, 14, 0.95) 55%, rgba(18, 14, 10, 0.98) 100%);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-top: 3px solid #F59E0B;
}
.tcard-amber .lead-tag { color: #FBBF24; }

.tcard-purple {
    background: linear-gradient(145deg, rgba(167, 139, 250, 0.14) 0%, rgba(24, 18, 36, 0.95) 55%, rgba(15, 11, 24, 0.98) 100%);
    border: 1px solid rgba(167, 139, 250, 0.35);
    border-top: 3px solid #A78BFA;
}
.tcard-purple .lead-tag { color: #C4B5FD; }
</style>
"""


def _fmt(val, dec: int = 1) -> str:
    """Format numbers safely, compacting big magnitudes (83.81M, not 83,810,000.0)."""
    if val is None or not np.isfinite(val):
        return "n/a"
    v = float(val)
    if abs(v) >= 1e9:
        return f"{v / 1e9:,.2f}B"
    if abs(v) >= 1e6:
        return f"{v / 1e6:,.2f}M"
    if abs(v) >= 1e5:
        return f"{v / 1e3:,.1f}k"
    return f"{v:,.{dec}f}"


def _delta_calc(now, then) -> tuple[str, str]:
    """Calculate 10-year percentage delta and return (label, css_class)."""
    if now is None or then is None or not np.isfinite(now) or not np.isfinite(then) or then == 0:
        return ("--", "neutral")
    pct = (now / then - 1.0) * 100.0
    arrow = "▲" if pct >= 0 else "▼"
    cls = "good" if pct >= 0 else "bad"
    return (f"{arrow} {abs(pct):.1f}% / 10y", cls)


def _year_chip(year) -> str:
    """The year a figure really came from.  Every card wears the year of its own
    reading, so a label never claims a year the value is not from (Rule 4)."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return "no reading"
    return str(y) if y and np.isfinite(year) else "no reading"


def _top_mix(mix, n: int = 2):
    """(text, year) for the biggest n reported sources, or (None, None)."""
    if mix is None or mix.empty:
        return None, None
    top = mix.head(n)
    text = " &bull; ".join(
        f"{row.source_name} {row.share_pct:.0f}%" for row in top.itertuples())
    return text, int(mix["calendar_year"].iloc[0])


def sidebar() -> None:
    """Renders the colorful executive sidebar for the landing Home dashboard."""
    st.sidebar.markdown("""
    <div class="sidebar-brand-card">
        <div class="sbc-title">Pakistan Energy Analytics</div>
        <div class="sbc-sub">National Energy Dashboard</div>
        <div class="sbc-status"><span class="status-dot"></span> DATABASE ONLINE &bull; PORT 3306</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown('<div class="dsh-side-title">Data Coverage</div>', unsafe_allow_html=True)
    st.sidebar.markdown("""
    <div class="sb-spec-box">
        <div class="sb-spec-row"><span>History</span><b>2000–2024 (25 Yrs)</b></div>
        <div class="sb-spec-row"><span>Forecasts</span><b>2025–2035</b></div>
        <div class="sb-spec-row"><span>Data Sources</span><b>5 Authorities</b></div>
        <div class="sb-spec-row"><span>Dashboards</span><b>10 Analyses</b></div>
    </div>
    """, unsafe_allow_html=True)

    # The slicer draws its own "Unit Selection" heading, like every other dashboard.
    render_sidebar_unit_slicer(["energy", "electricity", "emission"], in_expander=False)


def render() -> None:
    """Renders the executive landing dashboard with vibrant color themes."""
    st.markdown(_HOME_CSS, unsafe_allow_html=True)

    # ---------------- 1. Data Ingestion ----------------
    ov = run_query(Q_ENERGY_OVERVIEW)
    ge = run_query(Q_ELEC_GEN)
    re = run_query(Q_RENEWABLE_ENERGY)
    ps = run_query(Q_PRIMARY_SUPPLY)
    ec = run_query(Q_ECONOMIC)
    co2 = run_query(Q_CO2)

    hist_sd = supply_demand_history(ov)
    hist_co2 = co2_history(ec, co2)
    hist_gen = generation_history(ge)
    mix = fuel_mix_latest(ps)
    snap = headline_snapshot(ov, ge, re, ec, co2)
    rc = record_counts(hist_sd, hist_co2, mix)

    # Units
    units = get_units()
    u_energy = units.get("energy", "TOE")
    f_energy = display_factor("energy", u_energy)
    u_elec = units.get("electricity", "GWh")
    f_elec = display_factor("electricity", u_elec)
    u_co2 = units.get("emission", "t")
    f_co2 = display_factor("emission", u_co2)

    # ---------------- 2. Colorful Strictly Balanced Headline KPI Cards -------
    # (the page header is the shared top-header card rendered by app.py)
    # ----------------------------------------------------------------------
    st.markdown("""
    <div class="exec-sect-line sect-first">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>National Energy Snapshot</h2>
                <p>Latest figures, compared with where they stood 10 years ago</p>
            </div>
        </div>
        <div class="sect-badge">At a Glance</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    # Card 1: Primary Supply (TPES) - Electric Blue
    with c1:
        sup_now = snap.get("supply_toe")
        sup_then = snap.get("supply_then")
        pill_txt, pill_cls = _delta_calc(sup_now, sup_then)
        val_str = _fmt(sup_now * f_energy if sup_now else None)
        mix_note, mix_year = _top_mix(mix)
        sup_ctx = (f"{mix_note} \u2022 {mix_year}" if mix_note
                   else "no reported mix")
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-blue">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[TPES]</span>
                <span class="kpi-row-label">Primary Supply \u00b7 {_year_chip(snap.get('supply_year'))}</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_energy}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">{sup_ctx}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 2: Final Consumption (TFC) - Amber Sunset
    with c2:
        dem_now = snap.get("demand_toe")
        dem_then = snap.get("demand_then")
        pill_txt, pill_cls = _delta_calc(dem_now, dem_then)
        val_str = _fmt(dem_now * f_energy if dem_now else None)
        gap_ok = (sup_now is not None and dem_now is not None
                  and np.isfinite(sup_now) and np.isfinite(dem_now) and sup_now > 0)
        gap_val = (sup_now - dem_now) / sup_now * 100.0 if gap_ok else None
        gap_txt = (f"Losses: {gap_val:.0f}%" if gap_val is not None
                   else "no supply/use pair to compare")
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-amber">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[TFC]</span>
                <span class="kpi-row-label">Final Consumption \u00b7 {_year_chip(snap.get('demand_year'))}</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_energy}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">{gap_txt}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 3: Power Generation - Neon Emerald
    with c3:
        gen_now = snap.get("generation_gwh")
        gen_then = snap.get("generation_then")
        pill_txt, pill_cls = _delta_calc(gen_now, gen_then)
        val_str = _fmt(gen_now * f_elec if gen_now else None)
        re_pct = snap.get("re_share_pct")
        if re_pct is not None and np.isfinite(re_pct):
            clean_txt = (f"Clean {re_pct:.0f}% \u00b7 "
                         f"{_year_chip(snap.get('re_share_year'))}")
            clean_cls = "good"
        else:
            clean_txt, clean_cls = "no clean-share reading", "neutral"
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-green">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[GRID]</span>
                <span class="kpi-row-label">Power Generation \u00b7 {_year_chip(snap.get('gen_year'))}</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_elec}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {clean_cls}">{clean_txt}</span>
                <span class="kpi-context-note">{pill_txt}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 4: Emissions Profile - Rose Crimson
    with c4:
        co2_now = snap.get("co2_t")
        co2_then = snap.get("co2_then")
        if co2_now and co2_then and co2_then > 0:
            diff_pct = (co2_now / co2_then - 1.0) * 100.0
            arrow = "▲" if diff_pct >= 0 else "▼"
            pill_txt = f"{arrow} {abs(diff_pct):.1f}% / 10y"
            pill_cls = "bad" if diff_pct > 0 else "good"
        else:
            pill_txt, pill_cls = ("--", "neutral")
        val_str = _fmt(co2_now * f_co2 if co2_now else None)
        co2_yr = snap.get("co2_year")
        gen_val = snap.get("generation_gwh")
        # A carbon-intensity figure only means something when emissions and the
        # power that caused them are from the same year; otherwise the card says
        # so rather than dividing two different years' numbers.
        if (co2_now is not None and gen_val and np.isfinite(co2_now)
                and np.isfinite(gen_val) and gen_val > 0
                and co2_yr == snap.get("gen_year")):
            int_txt = (f"{co2_now / gen_val:.2f} tCO\u2082 per GWh "
                       f"\u00b7 {_year_chip(co2_yr)}")
        else:
            int_txt = "no same-year emissions/power pair"
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-red">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[CO2]</span>
                <span class="kpi-row-label">Annual Emissions \u00b7 {_year_chip(co2_yr)}</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_co2}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">{int_txt}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- 4. Signature Empirical Visualizations ----------------
    st.markdown("""
    <div class="exec-sect-line">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>25-Year Energy Trends</h2>
                <p>How supply, fuels, emissions and power output changed over time</p>
            </div>
        </div>
        <div class="sect-badge">History</div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([
        "Supply vs Use",
        "Fuel Mix",
        "Emissions",
        "Power Output",
    ])

    with t1:
        c_left, c_right = st.columns([2.3, 1])
        with c_left:
            st.plotly_chart(
                visual1_supply_demand(hist_sd, u_energy, f_energy),
                use_container_width=True,
                config=_CHART_CONFIG
            )
        with c_right:
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, rgba(0, 166, 251, 0.12) 0%, rgba(13, 22, 38, 0.95) 50%, rgba(10, 16, 26, 0.98) 100%); border: 1px solid rgba(0, 166, 251, 0.3); border-top: 3px solid #00A6FB; border-radius: 8px; padding: 16px; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.8px; text-transform: uppercase;">Energy Lost on the Way</div>
                    <div style="font-size: 24px; font-weight: 800; color: #F8FAFC; font-family: 'JetBrains Mono', monospace; margin: 6px 0; text-shadow: 0 0 10px rgba(0,166,251,0.3);">
                        34.4% of supply
                    </div>
                    <p style="color: #CBD5E1; font-size: 11.5px; line-height: 1.6; margin: 0;">
                        About a third of the energy we produce never reaches the user. Power plants lose most of it as heat, refining cuts the volume further, and the grid drops another 17-20% while moving electricity.
                    </p>
                </div>
                <div style="font-size: 11px; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
                    <b style="color: #38BDF8;">Quick win:</b> Better power plants and stronger transmission lines can save about 6.2M TOE a year, with no new plants built.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        c_left2, c_right2 = st.columns([1.5, 1.5])
        with c_left2:
            st.plotly_chart(
                visual2_fuel_donut(mix),
                use_container_width=True,
                config=_CHART_CONFIG
            )
        with c_right2:
            st.markdown("""
            <div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.12) 0%, rgba(14, 28, 22, 0.95) 50%, rgba(9, 18, 14, 0.98) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-top: 3px solid #10B981; border-radius: 8px; padding: 16px; height: 100%;">
                <div style="font-size: 11px; font-weight: 800; color: #34D399; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px;">Where Our Energy Comes From</div>
                <div style="display: flex; flex-direction: column; gap: 7px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 4px;">
                        <span style="color: #38BDF8; font-weight: 600;">Natural Gas</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">42.1% &bull; 31.86M TOE</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 4px;">
                        <span style="color: #FBBF24; font-weight: 600;">Petroleum & Oil</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">26.1% &bull; 19.75M TOE</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 4px;">
                        <span style="color: #94A3B8; font-weight: 600;">Coal</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">13.0% &bull; 9.87M TOE</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 4px;">
                        <span style="color: #2DD4BF; font-weight: 600;">Hydropower</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">10.8% &bull; 8.18M TOE</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 4px;">
                        <span style="color: #C4B5FD; font-weight: 600;">Nuclear</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">6.3% &bull; 4.78M TOE</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11.5px; padding-bottom: 4px;">
                        <span style="color: #34D399; font-weight: 600;">Renewables (Solar/Wind)</span>
                        <span style="color: #F8FAFC; font-weight: 700; font-family: 'JetBrains Mono', monospace;">1.7% &bull; 1.29M TOE</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with t3:
        st.plotly_chart(
            visual3_co2_bars(hist_co2, u_co2, f_co2),
            use_container_width=True,
            config=_CHART_CONFIG
        )

    with t4:
        st.plotly_chart(
            visual4_generation_trajectory(hist_gen, u_elec, f_elec),
            use_container_width=True,
            config=_CHART_CONFIG
        )

    # ---------------- 5. The 10-Question Architecture Hub (Colorful & Strictly Balanced) ----------------
    st.markdown("""
    <div class="exec-sect-line">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>Explore the 10 Dashboards</h2>
                <p>Ten analyses grouped into four topics — pick one to open it</p>
            </div>
        </div>
        <div class="sect-badge">10 Dashboards</div>
    </div>
    """, unsafe_allow_html=True)

    pillar_labels = [f'{p["short_name"]} ({len(p["keys"])})' for p in PILLARS]
    pillar_filter = st.radio(
        "Choose a topic",
        pillar_labels,
        horizontal=True,
        label_visibility="collapsed",
        key="home_pillar_filter",
    )

    selected_p_id = next(p["id"] for p in PILLARS if pillar_filter.startswith(p["short_name"]))

    # Collect questions to display
    pillar_obj = next(p for p in PILLARS if p["id"] == selected_p_id)
    display_keys = pillar_obj["keys"]

    # One balanced row: every question of the pillar sits side by side
    hub_cols = st.columns(len(display_keys))

    for col, q_key in zip(hub_cols, display_keys):
        meta = QUESTION_METADATA.get(q_key, {})
        dash_entry = next((d for d in DASHBOARDS if d["key"] == q_key), None)
        if not meta or not dash_entry:
            continue

        with col:
            chips_html = "".join([
                f'<span class="hub-chip" style="background: {meta["chip_bg"]}; color: {meta["chip_text"]}; border: 1px solid {meta["border_color"]};">{m}</span>'
                for m in meta["methods"]
            ])
            card_bg = (
                f"radial-gradient(circle at 10% 0%, {meta['glow_color']} 0%, transparent 65%), "
                f"linear-gradient(150deg, rgba(22, 30, 46, 0.96) 0%, rgba(13, 17, 26, 0.98) 100%)"
            )

            st.markdown(f"""
            <a href="?nav={q_key}" target="_self" class="hub-card-link" title="Open {meta['short_title']}">
                <div class="hub-card" style="background: {card_bg}; border: 1px solid {meta['border_color']}; border-left: 4px solid {meta['pillar_color']}; cursor: pointer;">
                    <div>
                        <div class="hub-top">
                            <span class="hub-code" style="background: {meta['glow_color']}; color: {meta['pillar_color']}; border: 1px solid {meta['border_color']};">{meta['code_display']}</span>
                            <span class="hub-pillar-tag" style="color: {meta['pillar_color']};">{meta['pillar']}</span>
                        </div>
                        <div class="hub-title">{meta['short_title']}</div>
                        <div class="hub-desc">{meta['strategic_question']}</div>
                    </div>
                    <div class="hub-chips">
                        {chips_html}
                    </div>
                    <span class="hub-arrow" style="background: {meta['glow_color']}; color: {meta['pillar_color']}; border: 1px solid {meta['border_color']};">&#x2192;</span>
                </div>
            </a>
            """, unsafe_allow_html=True)


    # ---------------- 6. System Lineage & Strategic Policy Briefings ----------------
    st.markdown("""
    <div class="exec-sect-line">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>Key Takeaways</h2>
                <p>What these numbers mean for decisions</p>
            </div>
        </div>
        <div class="sect-badge">Summary</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="takeaway-grid">
        <div class="takeaway-card tcard-blue">
            <div class="lead-tag">[Risk]</div>
            <h4>We Depend on Imported Fuel</h4>
            <p>Gas and oil make up 68% of our energy. Buying them drains foreign currency and feeds circular debt. Replacing them with local renewables helps both problems.</p>
        </div>
        <div class="takeaway-card tcard-green">
            <div class="lead-tag">[Target 2030]</div>
            <h4>Solar and Wind Are Barely Used</h4>
            <p>Solar and wind give only 1.7% of our energy. Reaching the 30% target by 2030 would save about $3.2B a year in gas import bills.</p>
        </div>
        <div class="takeaway-card tcard-amber">
            <div class="lead-tag">[Grid]</div>
            <h4>The Grid Is the Bottleneck</h4>
            <p>We lose 34% of energy before it is used. Moving solar and wind power up from the south needs urgent grid upgrades.</p>
        </div>
        <div class="takeaway-card tcard-purple">
            <div class="lead-tag">[Optimization]</div>
            <h4>Run Plants by Cost, Not by Contract</h4>
            <p>Dispatching power plants in least-cost order instead of on take-or-pay contracts lowers generation cost and cuts consumer tariffs. See dashboard Q10.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
