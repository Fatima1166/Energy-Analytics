"""
core/data_entry.py -- Full CRUD backend for dynamic data entry in the energy dashboard.

Provides:
- Add new year data (sequential validation)
- Edit existing year data
- Delete first year or latest year only (no mid-year deletion)
- Restore deleted year data
- Insert into ALL database tables (energy overview, renewable energy, economic, electric,
  gas, supply, TD losses, province consumption, sector consumption, LNG, etc.)

Tables covered:
  dim_year, fact_energy_overview, fact_renewable_energy, fact_economic_indicators,
  fact_elec_generation, fact_co2_emissions, fact_td_losses,
  fact_primary_energy_supply, fact_final_energy_consumption,
  fact_elec_sector_consumption, fact_elec_province_consumption,
  fact_gas_sector_consumption, fact_gas_province_consumption,
  fact_lng_imports, fact_natural_gas, fact_renewable_capacity,
  fact_consm_conn
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
import streamlit as st
import json
import os
from config.database import get_connection


# ════════════════════════════════════════════════════════════════════════════════
# YEAR HELPERS
# ════════════════════════════════════════════════════════════════════════════════

def get_latest_year() -> int:
    """Get the latest calendar year in dim_year."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT MAX(calendar_year) as max_year FROM dim_year")
        result = cur.fetchone()
        return int(result['max_year']) if result and result['max_year'] else 2024
    finally:
        cur.close()


def get_first_year() -> int:
    """Get the first calendar year in dim_year."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT MIN(calendar_year) as min_year FROM dim_year")
        result = cur.fetchone()
        return int(result['min_year']) if result and result['min_year'] else 1999
    finally:
        cur.close()


def get_all_years() -> List[int]:
    """Get all available calendar years sorted."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT calendar_year FROM dim_year ORDER BY calendar_year")
        rows = cur.fetchall()
        return [int(r['calendar_year']) for r in rows]
    finally:
        cur.close()


def get_next_year() -> int:
    """Get the next year that can be added (latest + 1)."""
    return get_latest_year() + 1


def year_exists(year: int) -> bool:
    """Check if a year already exists in dim_year."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT year_id FROM dim_year WHERE calendar_year = %s", (year,))
        return cur.fetchone() is not None
    finally:
        cur.close()


def get_year_id(year: int) -> Optional[int]:
    """Get year_id for a given calendar_year."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT year_id FROM dim_year WHERE calendar_year = %s", (year,))
        result = cur.fetchone()
        return int(result['year_id']) if result else None
    finally:
        cur.close()


def _get_next_id(table: str, id_column: str) -> int:
    """Get the next available ID for a table."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT MAX({id_column}) as max_id FROM {table}")
        result = cur.fetchone()
        return int(result['max_id']) + 1 if result and result['max_id'] else 1
    finally:
        cur.close()


def _fiscal_year_label(year: int) -> str:
    """dim_year.fiscal_year format: 1999 -> '1999-2000', 2000 -> '2000-01', 2025 -> '2025-26'."""
    nxt = year + 1
    return f"{year}-{nxt}" if year % 100 == 99 else f"{year}-{str(nxt)[-2:]}"


def _row_exists(cur, table: str, where: str, params: tuple) -> bool:
    cur.execute(f"SELECT 1 FROM {table} WHERE {where} LIMIT 1", params)
    return cur.fetchone() is not None


def _upsert_year_row(cur, table: str, id_col: str, year_id: int,
                     values: dict, insert_extra: dict | None = None,
                     insert_if_empty: bool = False) -> None:
    """Update the single year_id row of a one-row-per-year fact table,
    or insert it when the year has no row yet (a plain UPDATE silently
    affects 0 rows in that case)."""
    if _row_exists(cur, table, 'year_id = %s', (year_id,)):
        set_sql = ", ".join(f"{col} = %s" for col in values)
        cur.execute(f"UPDATE {table} SET {set_sql} WHERE year_id = %s",
                    (*values.values(), year_id))
        return
    has_data = any(v is not None and v != 0 and v != '' for v in values.values())
    if insert_if_empty or has_data:
        extra = dict(insert_extra or {})
        cols = ['year_id', *values.keys(), *extra.keys()]
        cur.execute(
            f"INSERT INTO {table} ({id_col}, {', '.join(cols)}) "
            f"VALUES ({', '.join(['%s'] * (len(cols) + 1))})",
            (_get_next_id(table, id_col), year_id, *values.values(), *extra.values()))


def _upsert_breakdown(cur, table: str, id_col: str, key_col: str,
                      val_col: str, year_id: int, key_id: int, value) -> None:
    """Insert or update one (year_id, key_id) row of a breakdown table."""
    if _row_exists(cur, table, f"year_id = %s AND {key_col} = %s", (year_id, key_id)):
        cur.execute(
            f"UPDATE {table} SET {val_col} = %s WHERE year_id = %s AND {key_col} = %s",
            (value, year_id, key_id))
    else:
        cur.execute(
            f"INSERT INTO {table} ({id_col}, year_id, {key_col}, {val_col}) "
            f"VALUES (%s, %s, %s, %s)",
            (_get_next_id(table, id_col), year_id, key_id, value))


# ════════════════════════════════════════════════════════════════════════════════
# FETCH EXISTING YEAR DATA (for Edit form pre-fill)
# ════════════════════════════════════════════════════════════════════════════════

def fetch_year_data(year: int) -> dict:
    """
    Fetch all data for a given year from all fact tables.
    Returns a dict with all fields, empty values where no data exists.
    """
    year_id = get_year_id(year)
    if year_id is None:
        return {}

    data: dict = {"calendar_year": year, "year_id": year_id}
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # fact_energy_overview
        cur.execute(
            "SELECT * FROM fact_energy_overview WHERE year_id = %s LIMIT 1", (year_id,))
        row = cur.fetchone()
        if row:
            data["total_primary_supply_toe"] = row.get("total_primary_supply_toe")
            data["total_final_consumption_toe"] = row.get("total_final_consumption_toe")
            data["transformation_losses_toe"] = row.get("transformation_losses_toe")
            data["td_losses_toe"] = row.get("td_losses_toe")
            data["total_losses_toe"] = row.get("total_losses_toe")
            data["energy_used_in_transformation"] = row.get("energy_used_in_transformation")
            data["energy_sector_own_use"] = row.get("energy_sector_own_use")
            data["savings_toe"] = row.get("savings_toe")
            data["savings_pct"] = row.get("savings_pct")
            data["sustainability_class"] = row.get("sustainability_class")

        # fact_renewable_energy
        cur.execute(
            "SELECT * FROM fact_renewable_energy WHERE year_id = %s LIMIT 1", (year_id,))
        row = cur.fetchone()
        if row:
            data["capacity_mw"] = row.get("capacity_mw")
            data["gen_solar_gwh"] = row.get("gen_solar_gwh")
            data["gen_wind_gwh"] = row.get("gen_wind_gwh")
            data["gen_hydro_gwh"] = row.get("gen_hydro_gwh")
            data["gen_other_renewables_gwh"] = row.get("gen_other_renewables_gwh")
            data["gen_coal_gwh"] = row.get("gen_coal_gwh")
            data["gen_gas_gwh"] = row.get("gen_gas_gwh")
            data["gen_nuclear_gwh"] = row.get("gen_nuclear_gwh")
            data["demand_gwh"] = row.get("demand_gwh")
            data["primary_energy_gwh"] = row.get("primary_energy_gwh")

        # fact_economic_indicators
        cur.execute(
            "SELECT * FROM fact_economic_indicators WHERE year_id = %s LIMIT 1", (year_id,))
        row = cur.fetchone()
        if row:
            data["gdp_current_usd"] = row.get("gdp_current_usd")
            data["gdp_growth_pct"] = row.get("gdp_growth_pct")
            data["population"] = row.get("population")
            data["co2_emissions_tonnes"] = row.get("co2_emissions_tonnes")

        # fact_elec_generation
        cur.execute(
            "SELECT * FROM fact_elec_generation WHERE year_id = %s LIMIT 1", (year_id,))
        row = cur.fetchone()
        if row:
            data["installed_capacity_mw"] = row.get("installed_capacity_mw")
            data["generation_gwh"] = row.get("generation_gwh")
            data["imports_gwh"] = row.get("imports_gwh")
            data["consumption_gwh"] = row.get("consumption_gwh")

        # fact_co2_emissions (uses calendar_year directly)
        cur.execute(
            "SELECT co2_emissions_t FROM fact_co2_emissions WHERE calendar_year = %s LIMIT 1",
            (year,))
        row = cur.fetchone()
        if row:
            data["co2_emissions_tonnes"] = row.get("co2_emissions_t")

        # fact_td_losses
        cur.execute(
            "SELECT td_losses_gwh FROM fact_td_losses WHERE year_id = %s LIMIT 1", (year_id,))
        row = cur.fetchone()
        if row:
            data["td_losses_gwh"] = row.get("td_losses_gwh")

        # fact_natural_gas (uses year_id)
        cur.execute(
            "SELECT production_bcf, consumption_bcf, gap_bcf, gap_with_lng_bcf "
            "FROM fact_natural_gas WHERE year_id = %s LIMIT 1",
            (year_id,))
        row = cur.fetchone()
        if row:
            data["gas_production_bcf"] = row.get("production_bcf")
            data["gas_consumption_bcf"] = row.get("consumption_bcf")
            data["gas_gap_bcf"] = row.get("gap_bcf")
            data["gas_gap_with_lng_bcf"] = row.get("gap_with_lng_bcf")

        # fact_lng_imports
        cur.execute(
            "SELECT imports_bcf, imports_value_musd FROM fact_lng_imports "
            "WHERE year_id = %s LIMIT 1",
            (year_id,))
        row = cur.fetchone()
        if row:
            data["lng_imports_bcf"] = row.get("imports_bcf")
            data["lng_value_musd"] = row.get("imports_value_musd")

        # fact_primary_energy_supply (by source)
        cur.execute(
            "SELECT source_id, supply_toe FROM fact_primary_energy_supply "
            "WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"supply_source_{int(r['source_id'])}"] = r.get("supply_toe")

        # fact_final_energy_consumption (by source)
        cur.execute(
            "SELECT source_id, consumption_toe FROM fact_final_energy_consumption "
            "WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"cons_source_{int(r['source_id'])}"] = r.get("consumption_toe")

        # fact_elec_sector_consumption (by sector)
        cur.execute(
            "SELECT sector_id, consumption_gwh FROM fact_elec_sector_consumption "
            "WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"sector_cons_{int(r['sector_id'])}"] = r.get("consumption_gwh")

        # fact_elec_province_consumption (by province)
        cur.execute(
            "SELECT province_id, consumption_gwh FROM fact_elec_province_consumption "
            "WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"province_cons_{int(r['province_id'])}"] = r.get("consumption_gwh")

        # fact_gas_sector_consumption (reported split -- kept for restore)
        cur.execute(
            "SELECT sector_id, consumption_bcf FROM fact_gas_sector_consumption "
            "WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"gas_sector_cons_{int(r['sector_id'])}"] = r.get("consumption_bcf")

        # fact_gas_province_consumption (reported split -- kept for restore)
        cur.execute(
            "SELECT province_id, consumption_bcf, share_pct "
            "FROM fact_gas_province_consumption WHERE year_id = %s",
            (year_id,))
        for r in cur.fetchall():
            data[f"gas_prov_cons_{int(r['province_id'])}"] = r.get("consumption_bcf")
            data[f"gas_prov_share_{int(r['province_id'])}"] = r.get("share_pct")

        # fact_renewable_capacity (reported split -- kept for restore)
        cur.execute(
            "SELECT renewable_source, installed_capacity_mw, source_name "
            "FROM fact_renewable_capacity WHERE year_id = %s",
            (year_id,))
        rows = cur.fetchall()
        if rows:
            data["re_capacity_rows"] = [
                (r.get("renewable_source"), r.get("installed_capacity_mw"), r.get("source_name"))
                for r in rows
            ]

    finally:
        cur.close()

    return data


# ════════════════════════════════════════════════════════════════════════════════
# INSERT NEW YEAR DATA
# ════════════════════════════════════════════════════════════════════════════════

def validate_year_data(year: int, data: dict) -> list[str]:
    """Validate data before insertion. Returns list of error messages."""
    errors = []

    expected_year = get_next_year()
    if year != expected_year:
        errors.append(f"Can only add year {expected_year}. Year {year} is not allowed.")

    if year_exists(year):
        errors.append(f"Year {year} already exists in the database.")

    numeric_fields = [
        'total_primary_supply_toe', 'total_final_consumption_toe',
        'generation_gwh', 'installed_capacity_mw', 'capacity_mw',
        'gdp_current_usd', 'population', 'co2_emissions_tonnes',
        'transformation_losses_toe', 'td_losses_toe', 'total_losses_toe'
    ]

    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                val = float(data[field])
                if val < 0:
                    errors.append(f"{field} cannot be negative.")
            except (ValueError, TypeError):
                errors.append(f"{field} must be a valid number.")

    supply = data.get('total_primary_supply_toe')
    consumption = data.get('total_final_consumption_toe')
    if supply is not None and consumption is not None:
        try:
            if float(supply) < float(consumption):
                errors.append("Primary supply should be >= final consumption.")
        except (ValueError, TypeError):
            pass

    gen_gwh = data.get('generation_gwh')
    if gen_gwh is not None:
        try:
            gen_val = float(gen_gwh)
            if gen_val < 1000:
                errors.append("Generation seems too low. Please verify (in GWh).")
            if gen_val > 500000:
                errors.append("Generation seems too high. Please verify (in GWh).")
        except (ValueError, TypeError):
            pass

    return errors


def insert_year_data(year: int, data: dict) -> tuple[bool, str]:
    """
    Insert a complete year's data into ALL relevant tables.
    Returns (success: bool, message: str).
    """
    errors = validate_year_data(year, data)
    if errors:
        return False, "Validation failed:\n" + "\n".join(f"• {e}" for e in errors)

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # 1. dim_year
        year_id = _get_next_id('dim_year', 'year_id')
        fiscal_year = _fiscal_year_label(year)
        cur.execute(
            "INSERT INTO dim_year (year_id, fiscal_year, calendar_year) VALUES (%s, %s, %s)",
            (year_id, fiscal_year, year))

        # 2. fact_energy_overview
        if any(k in data for k in ('total_primary_supply_toe', 'total_final_consumption_toe',
                                   'transformation_losses_toe', 'td_losses_toe',
                                   'total_losses_toe', 'energy_used_in_transformation',
                                   'energy_sector_own_use', 'savings_toe', 'savings_pct',
                                   'sustainability_class')):
            overview_id = _get_next_id('fact_energy_overview', 'overview_id')
            supply = data.get('total_primary_supply_toe', 0)
            consumption = data.get('total_final_consumption_toe', 0)
            gap = float(supply) - float(consumption) if supply and consumption else 0
            savings_pct = (float(data.get('savings_toe') or 0) / float(supply) * 100.0
                           if supply else 0)
            cur.execute(
                """INSERT INTO fact_energy_overview
                   (overview_id, year_id, total_primary_supply_toe, total_final_consumption_toe,
                    supply_consumption_gap_toe, transformation_losses_toe, td_losses_toe,
                    total_losses_toe, energy_used_in_transformation, energy_sector_own_use,
                    savings_toe, savings_pct, sustainability_class)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (overview_id, year_id, supply, consumption, gap,
                 data.get('transformation_losses_toe', 0),
                 data.get('td_losses_toe', 0),
                 data.get('total_losses_toe', 0),
                 data.get('energy_used_in_transformation', 0),
                 data.get('energy_sector_own_use', 0),
                 data.get('savings_toe', 0),
                 savings_pct,
                 data.get('sustainability_class', 'Unsustainable')))

        # 3. fact_renewable_energy
        renewable_id = _get_next_id('fact_renewable_energy', 'renewable_energy_id')
        cur.execute(
            """INSERT INTO fact_renewable_energy
               (renewable_energy_id, year_id, calendar_year, capacity_mw,
                gen_solar_gwh, gen_wind_gwh, gen_hydro_gwh, gen_other_renewables_gwh,
                gen_coal_gwh, gen_gas_gwh, gen_nuclear_gwh, demand_gwh, primary_energy_gwh)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (renewable_id, year_id, year,
             data.get('capacity_mw', 0),
             data.get('gen_solar_gwh', 0),
             data.get('gen_wind_gwh', 0),
             data.get('gen_hydro_gwh', 0),
             data.get('gen_other_renewables_gwh', 0),
             data.get('gen_coal_gwh', 0),
             data.get('gen_gas_gwh', 0),
             data.get('gen_nuclear_gwh', 0),
             data.get('demand_gwh') or None,
             data.get('primary_energy_gwh') or None))

        # 4. fact_economic_indicators
        econ_id = _get_next_id('fact_economic_indicators', 'economic_id')
        cur.execute(
            """INSERT INTO fact_economic_indicators
               (economic_id, year_id, calendar_year, gdp_current_usd,
                gdp_growth_pct, population, co2_emissions_tonnes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (econ_id, year_id, year,
             data.get('gdp_current_usd', 0),
             data.get('gdp_growth_pct', 0),
             data.get('population', 0),
             data.get('co2_emissions_tonnes', 0)))

        # 5. fact_co2_emissions (calendar_year direct)
        cur.execute(
            """INSERT INTO fact_co2_emissions
               (co2_id, country_id, calendar_year, co2_emissions_t)
               VALUES (%s, %s, %s, %s)""",
            (_get_next_id('fact_co2_emissions', 'co2_id'), 175, year,
             data.get('co2_emissions_tonnes', 0)))

        # 6. fact_elec_generation
        gen_id = _get_next_id('fact_elec_generation', 'generation_id')
        cur.execute(
            """INSERT INTO fact_elec_generation
               (generation_id, year_id, installed_capacity_mw, generation_gwh,
                imports_gwh, consumption_gwh)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (gen_id, year_id,
             data.get('installed_capacity_mw', 0),
             data.get('generation_gwh', 0),
             data.get('imports_gwh', 0),
             data.get('consumption_gwh', 0)))

        # 7. fact_td_losses
        cur.execute(
            """INSERT INTO fact_td_losses
               (td_loss_id, year_id, td_losses_gwh)
               VALUES (%s, %s, %s)""",
            (_get_next_id('fact_td_losses', 'td_loss_id'), year_id,
             data.get('td_losses_gwh', 0)))

        # 8. fact_primary_energy_supply (by source)
        for source_id in range(1, 11):
            val = data.get(f'supply_source_{source_id}')
            if val is not None and val > 0:
                cur.execute(
                    """INSERT INTO fact_primary_energy_supply
                       (supply_id, year_id, source_id, supply_toe, imports_toe, imports_pct, unit)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (_get_next_id('fact_primary_energy_supply', 'supply_id'), year_id,
                     source_id, val, 0, 0, 'TOE'))

        # 9. fact_final_energy_consumption (by source)
        for source_id in range(1, 11):
            val = data.get(f'cons_source_{source_id}')
            if val is not None and val > 0:
                cur.execute(
                    """INSERT INTO fact_final_energy_consumption
                       (consumption_id, year_id, source_id, consumption_toe)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_final_energy_consumption', 'consumption_id'),
                     year_id, source_id, val))

        # 10. fact_elec_sector_consumption
        for sector_id in range(1, 18):
            val = data.get(f'sector_cons_{sector_id}')
            if val is not None and val > 0:
                cur.execute(
                    """INSERT INTO fact_elec_sector_consumption
                       (elec_sector_id, year_id, sector_id, consumption_gwh)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_elec_sector_consumption', 'elec_sector_id'),
                     year_id, sector_id, val))

        # 11. fact_elec_province_consumption
        for province_id in range(1, 9):
            val = data.get(f'province_cons_{province_id}')
            if val is not None and val > 0:
                cur.execute(
                    """INSERT INTO fact_elec_province_consumption
                       (prov_cons_id, year_id, province_id, consumption_gwh)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_elec_province_consumption', 'prov_cons_id'),
                     year_id, province_id, val))

        # 12. fact_gas_sector_consumption
        gas_sec_val = data.get('gas_consumption_bcf', 0)
        if gas_sec_val and gas_sec_val > 0:
            for sector_id in range(1, 18):
                cur.execute(
                    """INSERT INTO fact_gas_sector_consumption
                       (gas_sector_id, year_id, sector_id, consumption_bcf)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_gas_sector_consumption', 'gas_sector_id'),
                     year_id, sector_id, gas_sec_val / 17))

        # 13. fact_gas_province_consumption
        gas_prov_val = data.get('gas_consumption_bcf', 0)
        if gas_prov_val and gas_prov_val > 0:
            for province_id in range(1, 9):
                cur.execute(
                    """INSERT INTO fact_gas_province_consumption
                       (gas_prov_id, year_id, province_id, consumption_bcf, share_pct)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (_get_next_id('fact_gas_province_consumption', 'gas_prov_id'),
                     year_id, province_id, gas_prov_val / 8, 12.5))

        # 14. fact_lng_imports
        lng_val = data.get('lng_imports_bcf', 0)
        lng_value = data.get('lng_value_musd')  # Use actual value if provided, else NULL
        if lng_val and lng_val > 0:
            cur.execute(
                """INSERT INTO fact_lng_imports
                   (lng_import_id, year_id, imports_bcf, imports_value_musd)
                   VALUES (%s, %s, %s, %s)""",
                (_get_next_id('fact_lng_imports', 'lng_import_id'),
                 year_id, lng_val, lng_value))

        # 15. fact_natural_gas
        gas_prod = data.get('gas_production_bcf', 0)
        gas_cons = data.get('gas_consumption_bcf', 0)
        if gas_prod or gas_cons:
            gap = gas_prod - gas_cons  # DB convention: positive = surplus, negative = deficit
            cur.execute(
                """INSERT INTO fact_natural_gas
                   (gas_id, year_id, production_bcf, consumption_bcf, gap_bcf,
                    gap_with_lng_bcf)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (_get_next_id('fact_natural_gas', 'gas_id'), year_id,
                 gas_prod, gas_cons, gap, max(0, gap)))

        # 16. fact_renewable_capacity (Hydel, Wind, Solar, Bagasse)
        re_capacity_total = data.get('capacity_mw', 0)
        if re_capacity_total and re_capacity_total > 0:
            for source_name in ('Hydel', 'Wind', 'Solar', 'Bagasse'):
                cur.execute(
                    """INSERT INTO fact_renewable_capacity
                       (renewable_capacity_id, year_id, renewable_source,
                        installed_capacity_mw, source_name)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (_get_next_id('fact_renewable_capacity', 'renewable_capacity_id'),
                     year_id, source_name, re_capacity_total / 4,
                     'User Entry'))

        # 17. fact_consm_conn (consumer connections)
        for utility_id in range(1, 3):
            for province_id in range(1, 9):
                for sector_id in range(1, 18):
                    cur.execute(
                        """INSERT INTO fact_consm_conn
                           (connection_id, year_id, utility_id, province_id,
                            sector_id, consumers_added)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (_get_next_id('fact_consm_conn', 'connection_id'),
                         year_id, utility_id, province_id, sector_id, 0))

        # Commit
        if hasattr(conn, 'raw'):
            conn.raw.commit()
        else:
            conn.commit()

        _clear_all_caches()
        return True, f"Successfully added data for year {year}!"

    except Exception as e:
        try:
            if hasattr(conn, 'raw'):
                conn.raw.rollback()
            else:
                conn.rollback()
        except Exception:
            pass
        return False, f"Database error: {str(e)}"
    finally:
        cur.close()


# ════════════════════════════════════════════════════════════════════════════════
# UPDATE EXISTING YEAR DATA (Edit)
# ════════════════════════════════════════════════════════════════════════════════

def update_year_data(year: int, data: dict) -> tuple[bool, str]:
    """Update all fact table rows for a given year. Creates rows if they don't exist."""
    year_id = get_year_id(year)
    if year_id is None:
        return False, f"Year {year} does not exist in the database."

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # fact_energy_overview (upsert — many years have no row)
        eo_cols = ('total_primary_supply_toe', 'total_final_consumption_toe',
                   'transformation_losses_toe', 'td_losses_toe', 'total_losses_toe',
                   'energy_used_in_transformation', 'energy_sector_own_use',
                   'savings_toe', 'sustainability_class')
        if any(k in data for k in eo_cols):
            supply = data.get('total_primary_supply_toe', 0)
            consumption = data.get('total_final_consumption_toe', 0)
            gap = float(supply) - float(consumption) if supply and consumption else 0
            savings_pct = (float(data.get('savings_toe') or 0) / float(supply) * 100.0
                           if supply else 0)
            vals = {
                'total_primary_supply_toe': supply,
                'total_final_consumption_toe': consumption,
                'supply_consumption_gap_toe': gap,
                'transformation_losses_toe': data.get('transformation_losses_toe', 0),
                'td_losses_toe': data.get('td_losses_toe', 0),
                'total_losses_toe': data.get('total_losses_toe', 0),
                'energy_used_in_transformation': data.get('energy_used_in_transformation', 0),
                'energy_sector_own_use': data.get('energy_sector_own_use', 0),
                'savings_toe': data.get('savings_toe', 0),
                'savings_pct': savings_pct,
                'sustainability_class': data.get('sustainability_class', 'Unsustainable'),
            }
            _upsert_year_row(cur, 'fact_energy_overview', 'overview_id', year_id, vals)

        # fact_renewable_energy (upsert)
        re_vals = {
            'capacity_mw': data.get('capacity_mw', 0),
            'gen_solar_gwh': data.get('gen_solar_gwh', 0),
            'gen_wind_gwh': data.get('gen_wind_gwh', 0),
            'gen_hydro_gwh': data.get('gen_hydro_gwh', 0),
            'gen_other_renewables_gwh': data.get('gen_other_renewables_gwh', 0),
            'gen_coal_gwh': data.get('gen_coal_gwh', 0),
            'gen_gas_gwh': data.get('gen_gas_gwh', 0),
            'gen_nuclear_gwh': data.get('gen_nuclear_gwh', 0),
            'demand_gwh': data.get('demand_gwh') or None,
            'primary_energy_gwh': data.get('primary_energy_gwh') or None,
        }
        _upsert_year_row(cur, 'fact_renewable_energy', 'renewable_energy_id', year_id, re_vals)

        # fact_economic_indicators (upsert)
        econ_vals = {
            'gdp_current_usd': data.get('gdp_current_usd', 0),
            'gdp_growth_pct': data.get('gdp_growth_pct', 0),
            'population': data.get('population', 0),
            'co2_emissions_tonnes': data.get('co2_emissions_tonnes', 0),
        }
        _upsert_year_row(cur, 'fact_economic_indicators', 'economic_id', year_id, econ_vals)

        # fact_co2_emissions (insert/update by calendar_year directly)
        co2_val = data.get('co2_emissions_tonnes', 0)
        if _row_exists(cur, 'fact_co2_emissions', 'calendar_year = %s', (year,)):
            cur.execute(
                "UPDATE fact_co2_emissions SET co2_emissions_t=%s WHERE calendar_year=%s",
                (co2_val, year))
        else:
            cur.execute(
                "INSERT INTO fact_co2_emissions (co2_id, country_id, calendar_year, co2_emissions_t) VALUES (%s, %s, %s, %s)",
                (_get_next_id('fact_co2_emissions', 'co2_id'), 175, year, co2_val))

        # fact_elec_generation (upsert)
        elec_vals = {
            'installed_capacity_mw': data.get('installed_capacity_mw', 0),
            'generation_gwh': data.get('generation_gwh', 0),
            'imports_gwh': data.get('imports_gwh', 0),
            'consumption_gwh': data.get('consumption_gwh', 0),
        }
        _upsert_year_row(cur, 'fact_elec_generation', 'generation_id', year_id, elec_vals)

        # fact_td_losses (upsert)
        td_vals = {'td_losses_gwh': data.get('td_losses_gwh', 0)}
        _upsert_year_row(cur, 'fact_td_losses', 'td_loss_id', year_id, td_vals)

        # fact_natural_gas (upsert)
        gas_prod = data.get('gas_production_bcf')
        gas_cons = data.get('gas_consumption_bcf')
        if gas_prod is not None or gas_cons is not None:
            gap = float(gas_prod or 0) - float(gas_cons or 0)
            lng_gap = max(0, gap)
            gas_vals = {
                'production_bcf': gas_prod or 0,
                'consumption_bcf': gas_cons or 0,
                'gap_bcf': gap,
                'gap_with_lng_bcf': lng_gap,
            }
            _upsert_year_row(cur, 'fact_natural_gas', 'gas_id', year_id, gas_vals)

        # fact_lng_imports (upsert)
        lng_val = data.get('lng_imports_bcf')
        lng_value = data.get('lng_value_musd')
        if lng_val is not None and lng_val > 0:
            lng_vals = {'imports_bcf': lng_val, 'imports_value_musd': lng_value}
            _upsert_year_row(cur, 'fact_lng_imports', 'lng_import_id', year_id, lng_vals)

        # Breakdown tables: by-source supply
        for source_id in range(1, 11):
            val = data.get(f'supply_source_{source_id}')
            if val is not None:
                _upsert_breakdown(cur, 'fact_primary_energy_supply', 'supply_id',
                                 'source_id', 'supply_toe', year_id, source_id, val)

        # Breakdown tables: by-source consumption
        for source_id in range(1, 11):
            val = data.get(f'cons_source_{source_id}')
            if val is not None:
                _upsert_breakdown(cur, 'fact_final_energy_consumption', 'consumption_id',
                                 'source_id', 'consumption_toe', year_id, source_id, val)

        # Breakdown tables: by-sector electricity
        for sector_id in range(1, 18):
            val = data.get(f'sector_cons_{sector_id}')
            if val is not None:
                _upsert_breakdown(cur, 'fact_elec_sector_consumption', 'elec_sector_id',
                                 'sector_id', 'consumption_gwh', year_id, sector_id, val)

        # Breakdown tables: by-province electricity
        for province_id in range(1, 9):
            val = data.get(f'province_cons_{province_id}')
            if val is not None:
                _upsert_breakdown(cur, 'fact_elec_province_consumption', 'prov_cons_id',
                                 'province_id', 'consumption_gwh', year_id, province_id, val)

        if hasattr(conn, 'raw'):
            conn.raw.commit()
        else:
            conn.commit()

        _clear_all_caches()
        return True, f"Successfully updated data for year {year}!"

    except Exception as e:
        try:
            if hasattr(conn, 'raw'):
                conn.raw.rollback()
            else:
                conn.rollback()
        except Exception:
            pass
        return False, f"Database error: {str(e)}"
    finally:
        cur.close()


# ════════════════════════════════════════════════════════════════════════════════
# DELETE / RESTORE YEAR DATA (First or Latest year only)
# ════════════════════════════════════════════════════════════════════════════════

def delete_year_data(year: int, mode: str = "latest") -> tuple[bool, str]:
    """
    Delete all data for a year. Only allows first year or latest year.
    mode: 'latest' or 'first'
    Returns (success, message).
    """
    year_id = get_year_id(year)
    if year_id is None:
        return False, f"Year {year} does not exist."

    all_years = get_all_years()
    if len(all_years) <= 1:
        return False, "Cannot delete the only year in the database."

    if mode == "latest" and year != all_years[-1]:
        return False, "Can only delete the latest year."
    if mode == "first" and year != all_years[0]:
        return False, "Can only delete the first year."

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Save backup before deletion (for restore)
        backup = fetch_year_data(year)

        # Delete from all tables in dependency order
        tables_by_year_id = [
            'fact_energy_overview', 'fact_renewable_energy', 'fact_economic_indicators',
            'fact_elec_generation', 'fact_td_losses',
            'fact_primary_energy_supply', 'fact_final_energy_consumption',
            'fact_elec_sector_consumption', 'fact_elec_province_consumption',
            'fact_gas_sector_consumption', 'fact_gas_province_consumption',
            'fact_lng_imports', 'fact_natural_gas', 'fact_renewable_capacity',
            'fact_consm_conn'
        ]

        for table in tables_by_year_id:
            cur.execute(f"DELETE FROM {table} WHERE year_id = %s", (year_id,))

        # fact_co2_emissions uses calendar_year directly
        cur.execute("DELETE FROM fact_co2_emissions WHERE calendar_year = %s", (year,))

        # Delete dim_year last
        cur.execute("DELETE FROM dim_year WHERE year_id = %s", (year_id,))

        if hasattr(conn, 'raw'):
            conn.raw.commit()
        else:
            conn.commit()

        _clear_all_caches()

        # Store backup in permanent file for restore (survives page refresh)
        _save_backup_to_file(year, backup)

        return True, f"Successfully deleted year {year}. You can restore it anytime."

    except Exception as e:
        try:
            if hasattr(conn, 'raw'):
                conn.raw.rollback()
            else:
                conn.rollback()
        except Exception:
            pass
        return False, f"Database error: {str(e)}"
    finally:
        cur.close()


def restore_year_data(year: int) -> tuple[bool, str]:
    """Restore a previously deleted year's data from permanent file backup."""
    backup = _load_backup_from_file(year)
    if not backup:
        return False, f"No backup found for year {year}. Cannot restore."

    if year_exists(year):
        return False, f"Year {year} already exists in the database."

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        year_id = _get_next_id('dim_year', 'year_id')
        fiscal_year = _fiscal_year_label(year)
        cur.execute(
            "INSERT INTO dim_year (year_id, fiscal_year, calendar_year) VALUES (%s, %s, %s)",
            (year_id, fiscal_year, year))

        # Restore fact_energy_overview
        if backup.get('total_primary_supply_toe') is not None:
            supply = backup.get('total_primary_supply_toe', 0)
            consumption = backup.get('total_final_consumption_toe', 0)
            gap = float(supply) - float(consumption) if supply and consumption else 0
            savings_pct = (float(backup.get('savings_toe') or 0) / float(supply) * 100.0
                           if supply else backup.get('savings_pct') or 0)
            cur.execute(
                """INSERT INTO fact_energy_overview
                   (overview_id, year_id, total_primary_supply_toe, total_final_consumption_toe,
                    supply_consumption_gap_toe, transformation_losses_toe, td_losses_toe,
                    total_losses_toe, energy_used_in_transformation, energy_sector_own_use,
                    savings_toe, savings_pct, sustainability_class)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (_get_next_id('fact_energy_overview', 'overview_id'), year_id,
                 supply, consumption, gap,
                 backup.get('transformation_losses_toe', 0),
                 backup.get('td_losses_toe', 0),
                 backup.get('total_losses_toe', 0),
                 backup.get('energy_used_in_transformation', 0),
                 backup.get('energy_sector_own_use', 0),
                 backup.get('savings_toe', 0),
                 savings_pct,
                 backup.get('sustainability_class', 'Unsustainable')))

        # Restore fact_renewable_energy
        cur.execute(
            """INSERT INTO fact_renewable_energy
               (renewable_energy_id, year_id, calendar_year, capacity_mw,
                gen_solar_gwh, gen_wind_gwh, gen_hydro_gwh, gen_other_renewables_gwh,
                gen_coal_gwh, gen_gas_gwh, gen_nuclear_gwh, demand_gwh, primary_energy_gwh)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (_get_next_id('fact_renewable_energy', 'renewable_energy_id'), year_id, year,
             backup.get('capacity_mw', 0), backup.get('gen_solar_gwh', 0),
             backup.get('gen_wind_gwh', 0), backup.get('gen_hydro_gwh', 0),
             backup.get('gen_other_renewables_gwh', 0), backup.get('gen_coal_gwh', 0),
             backup.get('gen_gas_gwh', 0), backup.get('gen_nuclear_gwh', 0),
             backup.get('demand_gwh') or None, backup.get('primary_energy_gwh') or None))

        # Restore fact_economic_indicators
        cur.execute(
            """INSERT INTO fact_economic_indicators
               (economic_id, year_id, calendar_year, gdp_current_usd,
                gdp_growth_pct, population, co2_emissions_tonnes)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (_get_next_id('fact_economic_indicators', 'economic_id'), year_id, year,
             backup.get('gdp_current_usd', 0), backup.get('gdp_growth_pct', 0),
             backup.get('population', 0), backup.get('co2_emissions_tonnes', 0)))

        # Restore fact_co2_emissions
        cur.execute(
            """INSERT INTO fact_co2_emissions
               (co2_id, country_id, calendar_year, co2_emissions_t)
               VALUES (%s, %s, %s, %s)""",
            (_get_next_id('fact_co2_emissions', 'co2_id'), 175, year,
             backup.get('co2_emissions_tonnes', 0)))

        # Restore fact_elec_generation
        cur.execute(
            """INSERT INTO fact_elec_generation
               (generation_id, year_id, installed_capacity_mw, generation_gwh,
                imports_gwh, consumption_gwh)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (_get_next_id('fact_elec_generation', 'generation_id'), year_id,
             backup.get('installed_capacity_mw', 0), backup.get('generation_gwh', 0),
             backup.get('imports_gwh', 0), backup.get('consumption_gwh', 0)))

        # Restore fact_td_losses
        cur.execute(
            """INSERT INTO fact_td_losses
               (td_loss_id, year_id, td_losses_gwh)
               VALUES (%s, %s, %s)""",
            (_get_next_id('fact_td_losses', 'td_loss_id'), year_id,
             backup.get('td_losses_gwh', 0)))

        # Restore fact_natural_gas
        gas_prod = backup.get('gas_production_bcf', 0)
        gas_cons = backup.get('gas_consumption_bcf', 0)
        if gas_prod or gas_cons:
            gap = float(gas_prod or 0) - float(gas_cons or 0)  # DB convention
            # Preserve original gap_with_lng if backed up, else max(0, gap)
            gap_with_lng = backup.get('gas_gap_with_lng_bcf')
            if gap_with_lng is None:
                gap_with_lng = max(0, gap)
            cur.execute(
                """INSERT INTO fact_natural_gas
                   (gas_id, year_id, production_bcf, consumption_bcf, gap_bcf,
                    gap_with_lng_bcf)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (_get_next_id('fact_natural_gas', 'gas_id'), year_id,
                 gas_prod or 0, gas_cons or 0, gap, gap_with_lng))

        # Restore fact_lng_imports
        lng_val = backup.get('lng_imports_bcf')
        if lng_val:
            cur.execute(
                """INSERT INTO fact_lng_imports
                   (lng_import_id, year_id, imports_bcf, imports_value_musd)
                   VALUES (%s, %s, %s, %s)""",
                (_get_next_id('fact_lng_imports', 'lng_import_id'), year_id,
                 lng_val, backup.get('lng_value_musd')))

        # Restore fact_primary_energy_supply (by source)
        for source_id in range(1, 11):
            val = backup.get(f'supply_source_{source_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_primary_energy_supply
                       (supply_id, year_id, source_id, supply_toe, imports_toe, imports_pct, unit)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (_get_next_id('fact_primary_energy_supply', 'supply_id'), year_id,
                     source_id, val, 0, 0, 'TOE'))

        # Restore fact_final_energy_consumption (by source)
        for source_id in range(1, 11):
            val = backup.get(f'cons_source_{source_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_final_energy_consumption
                       (consumption_id, year_id, source_id, consumption_toe)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_final_energy_consumption', 'consumption_id'),
                     year_id, source_id, val))

        # Restore fact_elec_sector_consumption (by sector)
        for sector_id in range(1, 18):
            val = backup.get(f'sector_cons_{sector_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_elec_sector_consumption
                       (elec_sector_id, year_id, sector_id, consumption_gwh)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_elec_sector_consumption', 'elec_sector_id'),
                     year_id, sector_id, val))

        # Restore fact_elec_province_consumption (by province)
        for province_id in range(1, 9):
            val = backup.get(f'province_cons_{province_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_elec_province_consumption
                       (prov_cons_id, year_id, province_id, consumption_gwh)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_elec_province_consumption', 'prov_cons_id'),
                     year_id, province_id, val))

        # Restore fact_gas_sector_consumption (reported split)
        for sector_id in range(1, 18):
            val = backup.get(f'gas_sector_cons_{sector_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_gas_sector_consumption
                       (gas_sector_id, year_id, sector_id, consumption_bcf)
                       VALUES (%s, %s, %s, %s)""",
                    (_get_next_id('fact_gas_sector_consumption', 'gas_sector_id'),
                     year_id, sector_id, val))

        # Restore fact_gas_province_consumption (reported split)
        for province_id in range(1, 9):
            val = backup.get(f'gas_prov_cons_{province_id}')
            if val is not None:
                cur.execute(
                    """INSERT INTO fact_gas_province_consumption
                       (gas_prov_id, year_id, province_id, consumption_bcf, share_pct)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (_get_next_id('fact_gas_province_consumption', 'gas_prov_id'),
                     year_id, province_id, val,
                     backup.get(f'gas_prov_share_{province_id}')))

        # Restore fact_renewable_capacity (reported split)
        for r in backup.get('re_capacity_rows', []) or []:
            source_name, cap_mw, src = r
            cur.execute(
                """INSERT INTO fact_renewable_capacity
                   (renewable_capacity_id, year_id, renewable_source,
                    installed_capacity_mw, source_name)
                   VALUES (%s, %s, %s, %s, %s)""",
                (_get_next_id('fact_renewable_capacity', 'renewable_capacity_id'),
                 year_id, source_name, cap_mw, src))

        if hasattr(conn, 'raw'):
            conn.raw.commit()
        else:
            conn.commit()

        _clear_all_caches()
        # Delete backup file after successful restore
        _delete_backup_file(year)

        return True, f"Successfully restored year {year}!"

    except Exception as e:
        try:
            if hasattr(conn, 'raw'):
                conn.raw.rollback()
            else:
                conn.rollback()
        except Exception:
            pass
        return False, f"Database error: {str(e)}"
    finally:
        cur.close()


def _clear_all_caches():
    """Clear all Streamlit caches to force data refresh."""
    try:
        st.cache_data.clear()
        st.cache_resource.clear()
    except Exception:
        pass


def _get_backup_dir() -> str:
    """Get the directory for storing permanent deletion backups."""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def _get_backup_file(year: int) -> str:
    """Get the backup file path for a given year."""
    return os.path.join(_get_backup_dir(), f"deleted_backup_{year}.json")


def _save_backup_to_file(year: int, backup: dict) -> None:
    """Save deleted year backup to a permanent JSON file."""
    backup_file = _get_backup_file(year)
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, default=str)


def _load_backup_from_file(year: int) -> dict | None:
    """Load deleted year backup from permanent JSON file."""
    backup_file = _get_backup_file(year)
    if os.path.exists(backup_file):
        with open(backup_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _delete_backup_file(year: int) -> None:
    """Delete the backup file after successful restore."""
    backup_file = _get_backup_file(year)
    if os.path.exists(backup_file):
        os.remove(backup_file)


def get_current_data_summary() -> dict:
    """Get a summary of current data for display in the form."""
    latest_year = get_latest_year()
    first_year = get_first_year()
    next_year = get_next_year()
    all_years = get_all_years()

    return {
        'latest_year': latest_year,
        'first_year': first_year,
        'next_year': next_year,
        'all_years': all_years,
        'message': f"Data from {first_year} to {latest_year}. You can add {next_year}.",
        'can_delete_latest': len(all_years) > 1,
        'can_delete_first': len(all_years) > 1,
    }
