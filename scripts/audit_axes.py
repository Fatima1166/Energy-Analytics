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
    Q_LNG,
    Q_NATURAL_GAS,
    Q_PRIMARY_SUPPLY,
    Q_RENEWABLE_ENERGY,
    Q_TD_LOSSES,
)
from core.demand_forecast import build_dashboard_data
from core.supply_forecast import build_supply_dashboard_data
from core.cost_forecast import HORIZON, build_cost_dashboard_data
from core.sustainability_engine import (
    apply_weights, budget_score_curve, build_indicator_frame, build_verdict,
    latest_pillar_scores,
    pillar_last_seen, project_pathways,
    select_optimal_package, snapshot_row, strategy_value_density,
)
from dashboards.q4_forecast_demand import charts as q4_charts
from dashboards.q5_forecast_supply import charts as q5_charts
from dashboards.q6_supply_chain_optimization import charts as q6_charts
from dashboards.q6_supply_chain_optimization.config import STRATEGIES
from dashboards.q6_supply_chain_optimization.page import (
    _compute_scores,
    _grid_frame,
    _supply_frame,
)
from dashboards.q7_forecast_cost import charts as q7_charts
from dashboards.q7_forecast_cost.config import CASE_WORDS, TECHS_SHOWN
from dashboards.q8_sustainable_strategy import charts as q8_charts
from dashboards.q8_sustainable_strategy import page as q8_page
from dashboards.q8_sustainable_strategy.config import (
    PRESET_ORDER, STRATEGY_LIBRARY, preset_weights,
)

fuel_df = run_query(Q_FINAL_ENERGY_BY_SOURCE)
re_df = run_query(Q_RENEWABLE_ENERGY)
econ_df = run_query(Q_ECONOMIC)
primary_df = run_query(Q_PRIMARY_SUPPLY)
gen_df = run_query(Q_ELEC_GEN)
gas_df = run_query(Q_NATURAL_GAS)
td_df = run_query(Q_TD_LOSSES)
lng_df = run_query(Q_LNG)
sector_df = run_query(Q_ELEC_SECTOR_CONSUMPTION)
province_df = run_query(Q_ELEC_PROVINCE_CONSUMPTION)

d4 = build_dashboard_data(fuel_df, re_df, econ_df, primary_df, gen_df, gas_df, sector_df, province_df)
d5 = build_supply_dashboard_data(primary_df, re_df, econ_df, gen_df)

q4_figs = {
    'Q4 V1 (Demand so far)': q4_charts.visual1_history_trends(d4['history'], ['total_final', 'electricity_final', 'gas_final', 'elec_grid'], (1999, 2024)),
    'Q4 V2 (Scenario Paths)': q4_charts.visual2_scenario_fans(d4['bands'], d4['history'], ['total_final', 'electricity_final', 'gas_final', 'elec_grid'], ['Low', 'Base', 'High']),
    'Q4 V3 (What Moves Demand)': q4_charts.visual3_drivers(d4['history'], d4['models'].get('electricity_final', {}), 'electricity_final', (1999, 2024)),
    'Q4 V4 (Sector Mix)': q4_charts.visual4_sector_mix(d4['sectors'], 2035),
    'Q4 V5 (Trust In The Forecast)': q4_charts.visual5_reliability(d4['backtest']['metrics'], 2020, 2024),
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
    'Q5 V1 (Supply So Far)': q5_charts.visual1_history_trajectory(d5['history']),
    'Q5 V2 (Three Supply Paths)': q5_charts.visual2_scenario_fans(d5['history'], d5['forecast']),
    'Q5 V3 (Technology Mix)': q5_charts.visual3_technology_mix(d5['tech_mix']),
    'Q5 V4 (Supply Against Demand)': q5_charts.visual4_supply_vs_demand(d5['adequacy']),
    'Q5 V5 (Home Made Versus Imported)': q5_charts.visual5_domestic_vs_imports(d5['security']),
    'Q5 V6 (Trust In The Forecast)': q5_charts.visual6_reliability(d5['backtest']['table'], 2020, 2024),
}

print('\n=== AUDIT OF Q5 CHARTS ===')
for name, fig in q5_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')


preset = STRATEGIES['All four parts equally']
q6_grid = _grid_frame(gen_df, td_df)
q6_scores = _compute_scores(q6_grid, _supply_frame(primary_df), re_df, gas_df,
                            (2002, 2024), preset['weights'], preset['loss_target'])
q6_figs = {
    'Q6 V1 (Score Over Time)': q6_charts.visual1_score_over_time(q6_scores),
    'Q6 V2 (Grid Losses)': q6_charts.visual2_grid_losses(q6_grid, 'GWh', 1.0, preset['loss_target']),
    'Q6 V3 (Clean Plant Use)': q6_charts.visual3_renewable_plant_use(re_df, 'GWh', 1.0, 'MW', 1.0),
    'Q6 V4 (Gas Chain)': q6_charts.visual4_gas_chain(gas_df, lng_df, 'BCF', 1.0),
    'Q6 V5 (Now And Target Mix)': q6_charts.visual5_best_mix(preset['re_target'],
                                                             100 - preset['re_target'],
                                                             'GWh', 1.0,
                                                             re_df.iloc[-1].to_dict()),
}

print('\n=== AUDIT OF Q6 CHARTS ===')
for name, fig in q6_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')


d7 = build_cost_dashboard_data(re_df=re_df, econ_df=econ_df, gen_df=gen_df,
                               lng_df=lng_df)
h7 = d7['history'].iloc[-1]
f7 = d7['forecast']
ref_h = f7[(f7.scenario == 'Reference') & (f7.calendar_year == HORIZON)].iloc[0]
q7_steps = sorted(
    [(tech, float(ref_h[f'cost_{tech.lower().replace(" ", "")}_usd'])
      - float(h7[f'cost_{tech.lower().replace(" ", "")}_usd']))
     for tech in TECHS_SHOWN], key=lambda s: -s[1])
q7_figs = {
    'Q7 V1 (What Producers Were Paid)': q7_charts.visual1_cost_so_far(d7['history']),
    'Q7 V2 (The Bill From Here On)': q7_charts.visual2_forecast_bill(
        d7['history'], f7, ['Minimum RE', 'Reference', 'RE 50%'], CASE_WORDS),
    'Q7 V3 (Where The Extra Money Goes)': q7_charts.visual3_where_money_goes(
        [f'{int(h7.calendar_year)} paid'] + [t for t, _ in q7_steps]
        + [f'{HORIZON} plan'],
        ['absolute'] + ['relative'] * len(q7_steps) + ['total'],
        [float(h7.cost_total_usd)] + [d for _, d in q7_steps]
        + [float(ref_h.cost_total_usd)]),
    'Q7 V4 (What One Unit Costs)': q7_charts.visual4_unit_price(
        d7['history'], f7, ['Minimum RE', 'Reference', 'RE 50%'], CASE_WORDS),
    'Q7 V5 (Fuel Band And Model Error)': q7_charts.visual5_fuel_and_trust(
        d7['sensitivity'], d7['backtest'],
        ['Fuel up 1% a year', 'Fuel up 3% a year (used here)', 'Fuel up 5% a year']),
}

print('\n=== AUDIT OF Q7 CHARTS ===')
for name, fig in q7_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')


BASE_YEAR, HORIZON8 = 2024, 2035
ind8 = build_indicator_frame(re_df=re_df, gen_df=gen_df, td_df=td_df,
                             ps_df=primary_df, gas_df=gas_df, lng_df=lng_df,
                             econ_df=econ_df)
W8 = preset_weights(PRESET_ORDER[0])
ind8_w = apply_weights(ind8, W8)
ranked8 = strategy_value_density(STRATEGY_LIBRARY, W8)
pkg8 = select_optimal_package(STRATEGY_LIBRARY, W8, 8.0)
paths8 = project_pathways(ind8_w, W8, pkg8, BASE_YEAR, HORIZON8, STRATEGY_LIBRARY)
verdict8 = build_verdict(ind8_w, W8, pkg8, paths8, BASE_YEAR, HORIZON8)

# the K1 card and the first plotted point on V3 have to be the same number.
# The card wears the latest year with a full weighted score (the no-bridge rule
# leaves the evaluation year blank when a pillar is unreported), so the chart
# point it must agree with is that same year, not the blank evaluation year.
_card_year = int(snapshot_row(ind8_w, BASE_YEAR)['calendar_year'])
first_path = float(paths8[paths8.calendar_year == _card_year].iloc[0]['composite_bau'])
assert abs(first_path - verdict8['index_now']) < 0.005, (
    f"card {verdict8['index_now']:.2f} != chart {first_path:.2f} at {_card_year}")

q8_figs = {
    'Q8 V1 (Where Each Pillar Stands)': q8_charts.visual1_pillar_scorecard(
        q8_page._build_scorecard(ind8_w, BASE_YEAR)),
    'Q8 V2 (What Each Option Buys Per Dollar)': q8_charts.visual2_value_ranking(
        ranked8, {c['id'] for c in pkg8['chosen']}),
    'Q8 V3 (Measures Behind Each Pillar)': q8_charts.visual3_measure_heatmap(
        ind8_w, latest_pillar_scores(ind8_w, BASE_YEAR),
        pillar_last_seen(ind8_w, BASE_YEAR)),
    'Q8 V4 (What The Plan Changes)': q8_charts.visual4_pillar_gain(
        q8_page._build_gain(paths8, verdict8, HORIZON8), HORIZON8),
    'Q8 V5 (Where The Money Stops Helping)': q8_charts.visual5_budget_curve(
        budget_score_curve(ind8_w, W8, STRATEGY_LIBRARY, BASE_YEAR, HORIZON8,
                           [1.0, 4.0, 8.0, 12.0, 16.0, 20.0]), 8.0),
}

print('\n=== AUDIT OF Q8 CHARTS ===')
print(f"  index {verdict8['index_now']:.1f} -> "
      f"{verdict8['index_optimal']:.1f} (BAU {verdict8['index_bau']:.1f}), "
      f"{len(pkg8['chosen'])} funded of {len(STRATEGY_LIBRARY)}, "
      f"{pkg8['committed_bn']:.1f} of 8.0 $bn -- card and chart agree")
for name, fig in q8_figs.items():
    print(f'\n{name}:')
    for k in sorted(fig.layout):
        if k.startswith('xaxis') or k.startswith('yaxis'):
            ax = getattr(fig.layout, k)
            title = getattr(ax.title, 'text', None) if hasattr(ax, 'title') else None
            print(f'  {k}: title = \"{title}\"')

