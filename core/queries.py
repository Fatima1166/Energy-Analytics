# ---------- SQL queries for the energy dashboard ----------
# All queries return raw base units: TOE, GWh, MW, BCF, t, USD.
# The sidebar's unit selection is applied afterwards by core.units.

# Fact renewable energy (Solar, Wind, Hydro, Coal, Gas, Nuclear, Demand, Capacity)
# Joined on calendar_year with dim_year as per specification
Q_RENEWABLE_ENERGY = """
SELECT re.year_id, y.fiscal_year, re.calendar_year,
       re.capacity_mw,
       re.gen_solar_gwh, re.gen_wind_gwh, re.gen_hydro_gwh,
       re.gen_other_renewables_gwh,
       re.gen_coal_gwh, re.gen_gas_gwh, re.gen_nuclear_gwh,
       re.demand_gwh, re.primary_energy_gwh
FROM fact_renewable_energy re
JOIN dim_year y ON re.calendar_year = y.calendar_year
ORDER BY re.calendar_year;
"""

# Economic and CO2 indicators (CO2 stored in tonnes)
Q_ECONOMIC = """
SELECT e.year_id, y.calendar_year, e.gdp_current_usd,
       e.gdp_growth_pct, e.population, e.co2_emissions_tonnes
FROM fact_economic_indicators e
JOIN dim_year y ON e.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# T&D Losses (GWh)
Q_TD_LOSSES = """
SELECT t.year_id, y.calendar_year, t.td_losses_gwh
FROM fact_td_losses t
JOIN dim_year y ON t.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# LNG Imports (volume in BCF, value in Million USD)
Q_LNG = """
SELECT l.year_id, y.calendar_year, l.imports_bcf, l.imports_value_musd
FROM fact_lng_imports l
JOIN dim_year y ON l.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# Electricity Generation & Installed Capacity (GWh / MW)
Q_ELEC_GEN = """
SELECT g.year_id, y.calendar_year, g.installed_capacity_mw,
       g.generation_gwh, g.imports_gwh, g.consumption_gwh
FROM fact_elec_generation g
JOIN dim_year y ON g.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# Renewable Installed Capacity by Source (Hydel, Wind, Solar, Bagasse) -- MW
Q_RENEWABLE_CAPACITY = """
SELECT rc.year_id, y.calendar_year, rc.renewable_source,
       rc.installed_capacity_mw
FROM fact_renewable_capacity rc
JOIN dim_year y ON rc.year_id = y.year_id
ORDER BY y.calendar_year, rc.renewable_source;
"""

# Emission Factors from DB dim_emission_factor (tCO2/MWh -- a ratio, not converted)
Q_EMISSION_FACTORS = """
SELECT factor_id, source_id, fuel_type, emission_factor_tco2_mwh, reference
FROM dim_emission_factor;
"""

# Energy overview -- TOE domain (primary supply / final consumption / losses)
Q_ENERGY_OVERVIEW = """
SELECT eo.year_id, y.calendar_year,
       eo.total_primary_supply_toe, eo.total_final_consumption_toe,
       eo.supply_consumption_gap_toe, eo.transformation_losses_toe,
       eo.td_losses_toe, eo.total_losses_toe,
       eo.savings_toe, eo.savings_pct, eo.sustainability_class
FROM fact_energy_overview eo
JOIN dim_year y ON eo.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# Natural gas balance -- BCF domain
Q_NATURAL_GAS = """
SELECT g.year_id, y.calendar_year, g.production_bcf, g.consumption_bcf,
       g.gap_bcf, g.gap_with_lng_bcf
FROM fact_natural_gas g
JOIN dim_year y ON g.year_id = y.year_id
ORDER BY y.calendar_year;
"""

# Combo Chart: Capacity vs Generation vs T&D Losses
Q_COMBO_ELEC_TD = """
SELECT y.calendar_year,
       g.installed_capacity_mw,
       g.generation_gwh,
       t.td_losses_gwh
FROM fact_elec_generation g
JOIN dim_year y ON g.year_id = y.year_id
LEFT JOIN fact_td_losses t ON g.year_id = t.year_id
ORDER BY y.calendar_year;
"""

# Dual-Axis Line: CO2 (t) vs RE Share %
Q_CO2_VS_RE = """
SELECT re.calendar_year,
       re.gen_solar_gwh, re.gen_wind_gwh, re.gen_hydro_gwh,
       re.gen_other_renewables_gwh,
       re.gen_coal_gwh, re.gen_gas_gwh, re.gen_nuclear_gwh,
       e.co2_emissions_tonnes
FROM fact_renewable_energy re
JOIN fact_economic_indicators e ON re.calendar_year = e.calendar_year
ORDER BY re.calendar_year;
"""

# Optional overview / primary / sector tables (TOE)
Q_PRIMARY_SUPPLY = """
SELECT p.year_id, y.calendar_year, s.source_name, p.supply_toe, p.imports_toe
FROM fact_primary_energy_supply p
JOIN dim_year y ON p.year_id = y.year_id
JOIN dim_energy_source s ON p.source_id = s.source_id
ORDER BY y.calendar_year;
"""

Q_SECTOR_DEMAND = """
SELECT f.year_id, y.calendar_year, s.source_name, f.consumption_toe
FROM fact_final_energy_consumption f
JOIN dim_year y ON f.year_id = y.year_id
JOIN dim_energy_source s ON f.source_id = s.source_id
ORDER BY y.calendar_year;
"""

# ── Question 4 (forecasted energy demand) ───────────────────────────────────
# Final energy demand by fuel/source -- the base for total, electricity and gas
# demand history (TOE).  Reported 2002-2024.
Q_FINAL_ENERGY_BY_SOURCE = """
SELECT y.calendar_year, s.source_name, f.consumption_toe
FROM fact_final_energy_consumption f
JOIN dim_year y ON f.year_id = y.year_id
JOIN dim_energy_source s ON f.source_id = s.source_id
ORDER BY y.calendar_year, s.source_name;
"""

# Electricity consumption by end-use sector (GWh) -- reported 2002-2024.
Q_ELEC_SECTOR_CONSUMPTION = """
SELECT y.calendar_year, d.sector_name, x.consumption_gwh
FROM fact_elec_sector_consumption x
JOIN dim_year y ON x.year_id = y.year_id
JOIN dim_sector d ON x.sector_id = d.sector_id
ORDER BY y.calendar_year, d.sector_name;
"""

# Electricity consumption by province / region (GWh) -- reported 2002-2024.
Q_ELEC_PROVINCE_CONSUMPTION = """
SELECT y.calendar_year, d.province_name, x.consumption_gwh
FROM fact_elec_province_consumption x
JOIN dim_year y ON x.year_id = y.year_id
JOIN dim_province d ON x.province_id = d.province_id
ORDER BY y.calendar_year, d.province_name;
"""

# Gas consumption by end-use sector (BCF) -- reported 2013-2018 only.
Q_GAS_SECTOR_CONSUMPTION = """
SELECT y.calendar_year, d.sector_name, x.consumption_bcf
FROM fact_gas_sector_consumption x
JOIN dim_year y ON x.year_id = y.year_id
JOIN dim_sector d ON x.sector_id = d.sector_id
ORDER BY y.calendar_year, d.sector_name;
"""

# Unit dimension kept in MySQL (source of truth for base -> display mappings)
Q_UNIT_METADATA = """
SELECT domain, table_name, column_name, base_unit, display_unit,
       conversion_factor, is_default
FROM dim_unit_metadata
ORDER BY domain, table_name, column_name, conversion_factor;
"""

Q_UNIT_DIM = """
SELECT unit_code, domain, unit_name, to_base, is_base, is_fixed, sort_order
FROM dim_unit
ORDER BY domain, sort_order;
"""
