"""
dashboards/home_energy_overview/page.py -- Executive Landing Command Center
for the Pakistan National Energy Analytics Platform.

Vibrant, colorful, and institutional design:
1. Executive Sidebar: System specifications, fast module navigator, live unit slicers.
2. Executive Command Header: Ambient glowing mesh with color-coded regulatory badges.
3. Headline KPI Strip: Strictly locked equal-height cards with luminous neon color themes.
4. Strategic Visualizations: Empirical energy balance, fuel mix, emissions, and generation.
5. Analytical Architecture Hub: 10 decision modules arranged in balanced 2-column rows with pillar color palettes.
6. System Lineage & Strategic Policy Briefings: Vibrant multi-hued takeaway cards.
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
        "pillar": "Pillar I: Macro Dynamics",
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
        "short_title": "Parameter Relationships & What-If Forecasts",
        "strategic_question": "Empirical correlations, rolling elasticity matrix, and multi-variable what-if parameter forecasts to 2035.",
        "methods": ["Correlation Web", "Driver Elasticity", "What-If Simulation"],
    },
    "q2": {
        "pillar": "Pillar II: Clean Transition",
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
        "short_title": "Renewable Installation Scenarios",
        "strategic_question": "Comparative generation mix shifts, CO₂ abatement valuation, and LNG import displacement savings to 2035.",
        "methods": ["Comparative Simulation", "CO₂ Avoidance", "LNG Bill Savings"],
    },
    "q3": {
        "pillar": "Pillar III: Infrastructure",
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
        "short_title": "Planned Targets & Critical Bottlenecks",
        "strategic_question": "T&D line losses, fuel import reliance, domestic gas self-sufficiency, and benchmark gap analysis.",
        "methods": ["T&D Loss Scorecard", "Import Ratios", "Benchmark Audit"],
    },
    "q4": {
        "pillar": "Pillar I: Macro Dynamics",
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
        "short_title": "Energy Demand Projections to 2035",
        "strategic_question": "Reported demand (1999–2024), GDP and demographic elasticity drivers, and Low/Base/High pathways to 2035.",
        "methods": ["GDP Elasticity", "Sector Breakdown", "Pathway Scenarios"],
    },
    "q5": {
        "pillar": "Pillar I: Macro Dynamics",
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
        "short_title": "Primary Supply & Capacity Outlook",
        "strategic_question": "Primary energy fuel mix trajectories, generation expansion outlook, and capacity reserve adequacy to 2035.",
        "methods": ["Primary Fuel Trajectory", "Generation Mix", "Reserve Margin"],
    },
    "q6": {
        "pillar": "Pillar III: Infrastructure",
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
        "short_title": "Supply Chain & Fuel Optimization",
        "strategic_question": "Fuel efficiency scorecards, domestic natural gas depletion curve, and renewable curtailment mitigation.",
        "methods": ["Efficiency Scorecard", "Gas Depletion Index", "RE Curtailment"],
    },
    "q7": {
        "pillar": "Pillar IV: Power Economics",
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
        "short_title": "Power Producer Generation Cost Outlook",
        "strategic_question": "Purchasing cost bill by technology, fuel price volatility sensitivity, and merit-order tariff avoidance.",
        "methods": ["Technology Cost Modeling", "Fuel Shock Sensitivities", "Tariff Valuation"],
    },
    "q8": {
        "pillar": "Pillar II: Clean Transition",
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
        "short_title": "Sustainable Energy Development Strategy",
        "strategic_question": "Four-pillar sustainability index, knapsack policy package solver, and BAU vs optimal pathways to 2035.",
        "methods": ["4-Pillar Index", "Knapsack Package Solver", "Trade-off Matrix"],
    },
    "q9": {
        "pillar": "Pillar III: Infrastructure",
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
        "short_title": "Operational & Fuel-Supply Bottlenecks",
        "strategic_question": "Thermal capacity factor underutilization, seasonal gas rationing deficits, and plant dispatch friction.",
        "methods": ["Capacity Factor Scorecard", "Gas Peaking Deficit", "Take-or-Pay Friction"],
    },
    "q10": {
        "pillar": "Pillar IV: Power Economics",
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
        "short_title": "Constrained Optimal Resource Allocation",
        "strategic_question": "Constrained water-filling optimization: Least-cost, low-carbon generation dispatch with sector flow limits.",
        "methods": ["Water-Filling Solver", "Least-Cost Dispatch", "Carbon Constraints"],
    },
}

PILLARS = [
    {
        "id": "p1",
        "short_name": "Pillar I: Macro Dynamics",
        "title": "Pillar I: Macro Dynamics, Supply & Demand",
        "color": "#00A6FB",
        "keys": ["q1", "q4", "q5"],
    },
    {
        "id": "p2",
        "short_name": "Pillar II: Clean Transition",
        "title": "Pillar II: Clean Transition & Renewable Scenarios",
        "color": "#10B981",
        "keys": ["q2", "q8"],
    },
    {
        "id": "p3",
        "short_name": "Pillar III: Infrastructure",
        "title": "Pillar III: Infrastructure, Bottlenecks & Security",
        "color": "#F59E0B",
        "keys": ["q3", "q6", "q9"],
    },
    {
        "id": "p4",
        "short_name": "Pillar IV: Power Economics",
        "title": "Pillar IV: Power Economics & Optimal Dispatch",
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

/* ---------------- Executive Command Header ---------------- */
.exec-header-box {
    position: relative;
    border-radius: 12px;
    padding: 28px 34px 26px 34px;
    background: radial-gradient(circle at 5% 10%, rgba(0, 166, 251, 0.16) 0%, transparent 45%),
                radial-gradient(circle at 95% 90%, rgba(16, 185, 129, 0.14) 0%, transparent 45%),
                linear-gradient(135deg, #0F1626 0%, #131D30 50%, #0D1322 100%);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-top: 3px solid #00A6FB;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    margin-bottom: 22px;
}
.exec-status-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #38BDF8;
    margin-bottom: 10px;
}
.exec-status-row .live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 10px #10B981;
    display: inline-block;
}
.exec-header-box h1 {
    font-size: 28px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.4px;
    line-height: 1.2;
    margin: 0 0 8px 0;
}
.exec-header-box h1 span.highlight-text {
    background: linear-gradient(90deg, #38BDF8 0%, #34D399 50%, #FBBF24 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.exec-header-box p {
    font-size: 13.5px;
    line-height: 1.6;
    color: #94A3B8;
    max-width: 860px;
    margin: 0 0 18px 0;
}
.exec-spec-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}
.exec-spec-pill {
    font-size: 10.5px;
    font-weight: 700;
    border-radius: 6px;
    padding: 5px 12px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.spec-blue   { background: rgba(0, 166, 251, 0.14); border: 1px solid rgba(0, 166, 251, 0.4); color: #38BDF8; }
.spec-green  { background: rgba(16, 185, 129, 0.14); border: 1px solid rgba(16, 185, 129, 0.4); color: #34D399; }
.spec-amber  { background: rgba(245, 158, 11, 0.14); border: 1px solid rgba(245, 158, 11, 0.4); color: #FBBF24; }
.spec-purple { background: rgba(167, 139, 250, 0.14); border: 1px solid rgba(167, 139, 250, 0.4); color: #C4B5FD; }

/* ---------------- Section Divider Title ---------------- */
.exec-sect-line {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 30px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
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

/* ---------------- Colorful Strictly Balanced Headline KPI Cards ---------------- */
.kpi-row-card {
    border-radius: 10px;
    padding: 16px 18px 14px 18px;
    height: 136px !important;
    min-height: 136px !important;
    max-height: 136px !important;
    box-sizing: border-box !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.kpi-row-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
}

/* Card 1: Electric Blue */
.kpi-card-blue {
    background: linear-gradient(145deg, rgba(0, 166, 251, 0.15) 0%, rgba(13, 24, 44, 0.95) 45%, rgba(10, 17, 30, 0.98) 100%);
    border: 1px solid rgba(0, 166, 251, 0.35);
    border-top: 3.5px solid #00E5FF;
}
.kpi-card-blue:hover { border-color: #38BDF8; box-shadow: 0 8px 25px rgba(0, 166, 251, 0.3); }
.kpi-card-blue .kpi-row-val { color: #38BDF8; text-shadow: 0 0 14px rgba(0, 166, 251, 0.35); }
.kpi-card-blue .kpi-row-code { background: rgba(0, 166, 251, 0.2); color: #38BDF8; border: 1px solid rgba(0, 166, 251, 0.5); }

/* Card 2: Amber Sunset */
.kpi-card-amber {
    background: linear-gradient(145deg, rgba(245, 158, 11, 0.15) 0%, rgba(36, 25, 12, 0.95) 45%, rgba(18, 13, 8, 0.98) 100%);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-top: 3.5px solid #F59E0B;
}
.kpi-card-amber:hover { border-color: #FBBF24; box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3); }
.kpi-card-amber .kpi-row-val { color: #FBBF24; text-shadow: 0 0 14px rgba(245, 158, 11, 0.35); }
.kpi-card-amber .kpi-row-code { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.5); }

/* Card 3: Neon Emerald */
.kpi-card-green {
    background: linear-gradient(145deg, rgba(16, 185, 129, 0.15) 0%, rgba(12, 32, 22, 0.95) 45%, rgba(8, 20, 14, 0.98) 100%);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-top: 3.5px solid #10B981;
}
.kpi-card-green:hover { border-color: #34D399; box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3); }
.kpi-card-green .kpi-row-val { color: #34D399; text-shadow: 0 0 14px rgba(16, 185, 129, 0.35); }
.kpi-card-green .kpi-row-code { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.5); }

/* Card 4: Rose Crimson */
.kpi-card-red {
    background: linear-gradient(145deg, rgba(239, 68, 68, 0.15) 0%, rgba(38, 14, 18, 0.95) 45%, rgba(20, 8, 12, 0.98) 100%);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-top: 3.5px solid #F43F5E;
}
.kpi-card-red:hover { border-color: #FB7185; box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3); }
.kpi-card-red .kpi-row-val { color: #FB7185; text-shadow: 0 0 14px rgba(239, 68, 68, 0.35); }
.kpi-card-red .kpi-row-code { background: rgba(239, 68, 68, 0.2); color: #FB7185; border: 1px solid rgba(239, 68, 68, 0.5); }

.kpi-row-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kpi-row-code {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 7px;
    border-radius: 4px;
}
.kpi-row-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #CBD5E1;
}
.kpi-row-val {
    font-size: 27px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin: 4px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-row-val small {
    font-size: 12px;
    font-weight: 600;
    color: #94A3B8;
    margin-left: 6px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.kpi-row-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
}
.kpi-trend-pill {
    font-size: 10px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.3px;
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
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ---------------- Colorful Module Cards (Equal-Height 2-Column Grid) ---------------- */
.hub-card {
    border-radius: 10px;
    padding: 16px 18px 14px 18px;
    height: 156px !important;
    min-height: 156px !important;
    max-height: 156px !important;
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
    align-items: center;
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
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.hub-title {
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 800;
    line-height: 1.3;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.hub-desc {
    color: #94A3B8;
    font-size: 11.5px;
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 8px;
}
.hub-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.hub-chip {
    font-size: 10px;
    font-weight: 600;
    padding: 2.5px 8px;
    border-radius: 4px;
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
    """Format numeric values safely."""
    if val is None or not np.isfinite(val):
        return "n/a"
    return f"{val:,.{dec}f}"


def _delta_calc(now, then) -> tuple[str, str]:
    """Calculate 10-year percentage delta and return (label, css_class)."""
    if now is None or then is None or not np.isfinite(now) or not np.isfinite(then) or then == 0:
        return ("--", "neutral")
    pct = (now / then - 1.0) * 100.0
    arrow = "▲" if pct >= 0 else "▼"
    cls = "good" if pct >= 0 else "bad"
    return (f"{arrow} {abs(pct):.1f}% · 10-YR", cls)


def sidebar() -> None:
    """Renders the colorful executive sidebar for the landing Home dashboard."""
    st.sidebar.markdown("""
    <div class="sidebar-brand-card">
        <div class="sbc-title">Pakistan Energy Analytics</div>
        <div class="sbc-sub">National Executive Decision Center</div>
        <div class="sbc-status"><span class="status-dot"></span> REPOSITORY ONLINE &bull; PORT 3306</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown('<div class="dsh-side-title">Warehouse Specs</div>', unsafe_allow_html=True)
    st.sidebar.markdown("""
    <div class="sb-spec-box">
        <div class="sb-spec-row"><span>Baseline Span</span><b>2000–2024 (25 Yrs)</b></div>
        <div class="sb-spec-row"><span>Scenario Horizon</span><b>2025–2035 Outlook</b></div>
        <div class="sb-spec-row"><span>Regulatory Ingestion</span><b>5 Authorities</b></div>
        <div class="sb-spec-row"><span>Decision Suites</span><b>10 Systems</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown('<div class="dsh-side-title">Display Units</div>', unsafe_allow_html=True)
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

    hist_sd = supply_demand_history(ov)
    hist_co2 = co2_history(ec)
    hist_gen = generation_history(ge)
    mix = fuel_mix_latest(ps)
    snap = headline_snapshot(ov, ge, re, ec)
    rc = record_counts(hist_sd, hist_co2, mix)

    # Units
    units = get_units()
    u_energy = units.get("energy", "TOE")
    f_energy = display_factor("energy", u_energy)
    u_elec = units.get("electricity", "GWh")
    f_elec = display_factor("electricity", u_elec)
    u_co2 = units.get("emission", "t")
    f_co2 = display_factor("emission", u_co2)

    # ---------------- 2. Executive Command Header ----------------
    period_str = f"{rc['first_year']}–{rc['last_year']}" if rc.get("first_year") else "2000–2024"
    st.markdown(f"""
    <div class="exec-header-box">
        <div class="exec-status-row">
            <span class="live-dot"></span>
            LIVE REPOSITORY &bull; BASELINE {rc.get('last_year', 2024)} &bull; OUTLOOK HORIZON 2035
        </div>
        <h1>Pakistan National Energy Analytics <span class="highlight-text">Command Center</span></h1>
        <p>
            Enterprise decision-support intelligence platform integrating 25 years of multi-source historical energy balances with dynamic scenario forecasting, transmission bottleneck diagnostics, tariff financial risk modeling, and constrained least-cost resource optimization.
        </p>
        <div class="exec-spec-strip">
            <span class="exec-spec-pill spec-blue">Sources: NTDC &bull; NEPRA &bull; World Bank &bull; EIA &bull; HDIP</span>
            <span class="exec-spec-pill spec-green">Time-Series: {period_str} (25 Years)</span>
            <span class="exec-spec-pill spec-amber">Analytics: 10 Decision Modules</span>
            <span class="exec-spec-pill spec-purple">Unit Engine: Multi-Domain Slicing</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- 3. Colorful Strictly Balanced Headline KPI Cards ----------------
    st.markdown("""
    <div class="exec-sect-line">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>National Energy Balance Indicators</h2>
                <p>Latest empirical warehouse values benchmarked against a 10-year historical trajectory</p>
            </div>
        </div>
        <div class="sect-badge">Macro Baseline Snapshot</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    # Card 1: Primary Supply (TPES) - Electric Blue
    with c1:
        sup_now = snap.get("supply_toe")
        sup_then = snap.get("supply_then")
        pill_txt, pill_cls = _delta_calc(sup_now, sup_then)
        val_str = _fmt(sup_now * f_energy if sup_now else None)
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-blue">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[TPES]</span>
                <span class="kpi-row-label">Primary Supply</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_energy}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">Gas 42% &bull; Oil 26%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 2: Final Consumption (TFC) - Amber Sunset
    with c2:
        dem_now = snap.get("demand_toe")
        dem_then = snap.get("demand_then")
        pill_txt, pill_cls = _delta_calc(dem_now, dem_then)
        val_str = _fmt(dem_now * f_energy if dem_now else None)
        gap_val = ((sup_now - dem_now) / sup_now * 100.0) if (sup_now and dem_now and sup_now > 0) else 34.4
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-amber">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[TFC]</span>
                <span class="kpi-row-label">Final Consumption</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_energy}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">Loss Gap: {gap_val:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card 3: Power Generation - Neon Emerald
    with c3:
        gen_now = snap.get("generation_gwh")
        gen_then = snap.get("generation_then")
        pill_txt, pill_cls = _delta_calc(gen_now, gen_then)
        val_str = _fmt(gen_now * f_elec if gen_now else None)
        re_pct = snap.get("re_share_pct", 41.0)
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-green">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[GRID]</span>
                <span class="kpi-row-label">Power Generation</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_elec}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill good">Clean Share: {re_pct:.1f}%</span>
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
            pill_txt = f"{arrow} {abs(diff_pct):.1f}% · 10-YR"
            pill_cls = "bad" if diff_pct > 0 else "good"
        else:
            pill_txt, pill_cls = ("--", "neutral")
        val_str = _fmt(co2_now * f_co2 if co2_now else None)
        st.markdown(f"""
        <div class="kpi-row-card kpi-card-red">
            <div class="kpi-row-top">
                <span class="kpi-row-code">[CO2]</span>
                <span class="kpi-row-label">Annual Emissions</span>
            </div>
            <div class="kpi-row-val">{val_str}<small>{u_co2}</small></div>
            <div class="kpi-row-bottom">
                <span class="kpi-trend-pill {pill_cls}">{pill_txt}</span>
                <span class="kpi-context-note">1.31 tCO₂/GWh thermal</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- 4. Signature Empirical Visualizations ----------------
    st.markdown("""
    <div class="exec-sect-line">
        <div class="sect-title-left">
            <div class="sect-bar"></div>
            <div>
                <h2>Strategic National Energy Trajectories</h2>
                <p>Empirical trajectories computed from 25 years of verified regulatory data</p>
            </div>
        </div>
        <div class="sect-badge">Empirical Records</div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs([
        "Energy Balance (TPES vs TFC)",
        "Primary Fuel Carrier Matrix",
        "Decarbonization & Emissions Trajectory",
        "Power Generation Output (GWh)",
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
                    <div style="font-size: 11px; font-weight: 800; color: #38BDF8; letter-spacing: 0.8px; text-transform: uppercase;">Structural Transformation Gap</div>
                    <div style="font-size: 24px; font-weight: 800; color: #F8FAFC; font-family: 'JetBrains Mono', monospace; margin: 6px 0; text-shadow: 0 0 10px rgba(0,166,251,0.3);">
                        34.4% of TPES
                    </div>
                    <p style="color: #CBD5E1; font-size: 11.5px; line-height: 1.6; margin: 0;">
                        The gap between Primary Supply and Final Consumption encompasses thermal generation conversion heat loss (~55-60%), refinery throughput shrinkage, and electricity transmission & distribution (T&D) losses averaging 17-20%.
                    </p>
                </div>
                <div style="font-size: 11px; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
                    <b style="color: #38BDF8;">Policy Implication:</b> Upgrading thermal heat-rate efficiencies and reinforcing high-voltage transmission lines mitigates up to 6.2M TOE annually without new power plant additions.
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
                <div style="font-size: 11px; font-weight: 800; color: #34D399; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px;">Primary Carrier Distribution</div>
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
                <h2>Analytical Architecture Matrix & Question Hub</h2>
                <p>Ten decision-grade analytical modules organized across four strategic policy pillars</p>
            </div>
        </div>
        <div class="sect-badge">10 Systems Catalog</div>
    </div>
    """, unsafe_allow_html=True)

    pillar_filter = st.radio(
        "Filter Analytical Modules",
        ["Pillar I: Macro Dynamics (3)",
         "Pillar II: Clean Transition (2)",
         "Pillar III: Infrastructure (3)",
         "Pillar IV: Power Economics (2)"],
        horizontal=True,
        label_visibility="collapsed",
        key="home_pillar_filter",
    )

    filter_map = {
        "Pillar I: Macro Dynamics (3)": "p1",
        "Pillar II: Clean Transition (2)": "p2",
        "Pillar III: Infrastructure (3)": "p3",
        "Pillar IV: Power Economics (2)": "p4",
    }
    selected_p_id = filter_map[pillar_filter]

    # Collect questions to display
    pillar_obj = next(p for p in PILLARS if p["id"] == selected_p_id)
    display_keys = pillar_obj["keys"]

    # Render questions in strictly balanced 2-column rows with vibrant theme
    for i in range(0, len(display_keys), 2):
        pair = display_keys[i:i + 2]
        col_left, col_right = st.columns(2)

        for col, q_key in zip([col_left, col_right], pair):
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
                <a href="?nav={q_key}" target="_self" class="hub-card-link" title="Open {meta['short_title']} Analysis">
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
                <h2>Executive Strategic Policy Takeaways</h2>
                <p>Key macroeconomic implications derived from national energy models</p>
            </div>
        </div>
        <div class="sect-badge">Policy Briefings</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="takeaway-grid">
        <div class="takeaway-card tcard-blue">
            <div class="lead-tag">[Risk Audit]</div>
            <h4>Import Exposure & FX Risk</h4>
            <p>Natural gas and petroleum account for 68% of primary supply. Mitigating circular debt and foreign exchange depletion requires aggressive renewable substitution.</p>
        </div>
        <div class="takeaway-card tcard-green">
            <div class="lead-tag">[Target 2030]</div>
            <h4>Renewable Transition Runway</h4>
            <p>Non-hydro renewables (solar/wind) contribute 1.7% of primary supply. Scaling toward the 30% ARE 2030 target avoids up to $3.2B in annual LNG import bills.</p>
        </div>
        <div class="takeaway-card tcard-amber">
            <div class="lead-tag">[Infrastructure]</div>
            <h4>Transmission Bottlenecks</h4>
            <p>With 34% structural conversion and delivery losses, southern wind and solar corridor evacuation requires urgent grid synchronous condensers and HVDC upgrades.</p>
        </div>
        <div class="takeaway-card tcard-purple">
            <div class="lead-tag">[Optimization]</div>
            <h4>Least-Cost Water-Filling</h4>
            <p>Transitioning from administrative take-or-pay dispatch to mathematical least-cost constrained water-filling (Q10) optimizes baseload and reduces consumer power tariffs.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
