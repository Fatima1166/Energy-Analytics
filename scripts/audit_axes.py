import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
import pandas as pd
from config.database import run_query
from core.queries import (
    Q_ECONOMIC,
    Q_ELEC_GEN,
    Q_ELEC_PROVINCE_CONSUMPTION,
    Q_ELEC_SECTOR_CONSUMPTION,
    Q_FINAL_ENERGY_BY_SOURCE,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
)
from core.demand_forecast import build_dashboard_data
from core.supply_forecast import build_supply_dashboard_data
from dashboards.q4_forecast_demand import charts as q4_charts
from dashboards.q5_forecast_supply import charts as q5_charts

fuel_df = run_query(Q_FINAL_ENERGY_BY_SOURCE)
re_df = run_query(Q_RENEWABLE_ENERGY)
econ_df = run_query(Q_ECONOMIC)
primary_df = run_query(Q_PRIMARY_SUPPLY)
gen_df = run_query(Q_ELEC_GEN)
gas_df = run_query(Q_NATURAL_GAS)
sector_df = run_query(Q_ELEC_SECTOR_CONSUMPTION)
province_df = run_query(Q_ELEC_PROVINCE_CONSUMPTION)

d4 = build_dashboard_data(fuel_df, re_df, econ_df, primary_df, gen_df, gas_df, sector_df, province_df)
d5 = build_supply_dashboard_data(primary_df, re_df, econ_df)

q4_figs = {
    'Q4 V1 (History)': q4_charts.visual1_history_trends(d4['history'], ['total_final', 'electricity_final', 'gas_final', 'elec_grid'], (1999, 2024)),
    'Q4 V2 (Scenario Fans)': q4_charts.visual2_scenario_fans(d4['bands'], d4['history'], ['total_final', 'electricity_final', 'gas_final', 'elec_grid'], ['Low', 'Base', 'High']),
    'Q4 V3 (Drivers)': q4_charts.visual3_drivers(d4['history'], d4['models'].get('electricity_final', {}), 'electricity_final', (1999, 2024)),
    'Q4 V4 (Decomposition)': q4_charts.visual4_decomposition(d4['decomposition']['electricity_final'], 'Electricity'),
    'Q4 V5 (Sector Mix)': q4_charts.visual5_sector_mix(d4['sectors'], 2035),
    'Q4 V5 (Province Mix)': q4_charts.visual5_province_mix(d4['provinces'], 2035),
    'Q4 V6 (Supply-Demand Gap)': q4_charts.visual6_gap(d4['gap'].get('total')),
    'Q4 V6 (Imports)': q4_charts.visual6_imports(d4['imports'], 2035),
    'Q4 V7 (Backtest MAPE)': q4_charts.visual7_backtest_mape(d4['backtest']['metrics'], 2020, 2024),
    'Q4 V7 (Backtest Path)': q4_charts.visual7_backtest_path(d4['backtest']['predictions'], 'electricity_final', 'GWh', 1.0, 'Electricity'),
}

print('=== AUDIT OF Q4 CHARTS ===')
for name, fig in q4_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')

q5_figs = {
    'Q5 V1 (History Trajectory)': q5_charts.visual1_history_trajectory(d5['history']),
    'Q5 V2 (Scenario Fans)': q5_charts.visual2_scenario_fans(d5['history'], d5['forecast']),
    'Q5 V3 (Technology Mix)': q5_charts.visual3_technology_mix(d5['tech_mix']),
    'Q5 V4 (Capacity Expansion)': q5_charts.visual4_capacity_expansion(d5['capacity']),
    'Q5 V5 (Supply vs Demand)': q5_charts.visual5_supply_vs_demand(d5['adequacy']),
    'Q5 V5 (Reserve Margin)': q5_charts.visual5_reserve_margin(d5['adequacy']),
    'Q5 V5 (Supply Adequacy Combined)': q5_charts.visual5_supply_adequacy(d5['adequacy']),
    'Q5 V6 (Energy Security)': q5_charts.visual6_indigenous_vs_imports(d5['security']),
    'Q5 V7 (Reliability Backtest)': q5_charts.visual7_reliability_backtest(d5['backtest']),
}

print('\n=== AUDIT OF Q5 CHARTS ===')
for name, fig in q5_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')

