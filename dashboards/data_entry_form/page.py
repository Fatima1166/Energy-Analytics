"""
dashboards/data_entry_form/page.py -- Professional Data Entry & Management Form.

Features:
- Add new year data (sequential validation only)
- Edit any existing year's data
- Delete first or latest year only (no mid-year deletion)
- Restore deleted year data
- All database tables covered
- Professional dark theme, minimal icons
"""

from __future__ import annotations

import io
import os

import pandas as pd
import streamlit as st

from core.data_entry import (
    get_current_data_summary,
    get_next_year,
    get_all_years,
    fetch_year_data,
    insert_year_data,
    update_year_data,
    delete_year_data,
    restore_year_data,
    get_first_year,
    get_latest_year,
)


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.de-panel {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95));
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}
.de-title {
    color: #E2E8F0;
    font-size: 22px;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: -0.3px;
}
.de-subtitle {
    color: #94A3B8;
    font-size: 13px;
    margin: 0 0 18px 0;
    line-height: 1.5;
}
.de-section {
    background: rgba(15, 23, 42, 0.45);
    border: 1px solid rgba(71, 85, 105, 0.2);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 14px;
}
.de-section-title {
    color: #38BDF8;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(56, 189, 248, 0.15);
}
.de-info {
    background: rgba(14, 165, 233, 0.1);
    border: 1px solid rgba(14, 165, 233, 0.25);
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 16px;
    font-size: 12px;
    color: #94A3B8;
    line-height: 1.6;
}
.stNumberInput > div > input {
    background: rgba(15, 23, 42, 0.6) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(71, 85, 105, 0.3) !important;
    border-radius: 6px !important;
}
</style>
"""

# ── Dimension helpers ─────────────────────────────────────────────────────────

def _fetch_dim(table: str, id_col: str, name_col: str) -> list[tuple]:
    from config.database import get_connection
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {name_col}")
        return [(r[id_col], r[name_col]) for r in cur.fetchall()]
    finally:
        cur.close()

def _get_sources(): return _fetch_dim('dim_energy_source', 'source_id', 'source_name')
def _get_provinces(): return _fetch_dim('dim_province', 'province_id', 'province_name')
def _get_sectors(): return _fetch_dim('dim_sector', 'sector_id', 'sector_name')

# ── Sidebar ───────────────────────────────────────────────────────────────────

def _parse_csv_for_year(df: pd.DataFrame) -> dict:
    """Parse uploaded CSV and extract data for a single year.
    
    Expects CSV with columns like:
    - year (required) or fiscal_year
    - Field names matching database column names OR common aliases
    
    Returns dict mapping field names to values.
    """
    if df.empty:
        return {}
    
    # Normalize column names (lowercase, strip spaces)
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Find year column
    year_col = None
    for col in ['year', 'calendar_year', 'fiscal_year', 'yr']:
        if col in df.columns:
            year_col = col
            break
    
    if not year_col:
        return {}
    
    # Take first row as data source
    row = df.iloc[0]
    result = {}
    
    # String fields (keep as-is)
    string_fields = {'sustainability_class'}
    
    # Define field mappings (csv_name -> db_key)
    field_map = {
        # Energy Overview (TOE)
        'total_primary_supply_toe': 'total_primary_supply_toe',
        'primary_supply_toe': 'total_primary_supply_toe',
        'total_final_consumption_toe': 'total_final_consumption_toe',
        'final_consumption_toe': 'total_final_consumption_toe',
        'transformation_losses_toe': 'transformation_losses_toe',
        'td_losses_toe': 'td_losses_toe',
        'total_losses_toe': 'total_losses_toe',
        'energy_used_in_transformation': 'energy_used_in_transformation',
        'energy_sector_own_use': 'energy_sector_own_use',
        'savings_toe': 'savings_toe',
        
        # Electricity Generation (GWh/MW)
        'installed_capacity_mw': 'installed_capacity_mw',
        'capacity_mw': 'installed_capacity_mw',
        'generation_gwh': 'generation_gwh',
        'imports_gwh': 'imports_gwh',
        'consumption_gwh': 'consumption_gwh',
        
        # Renewable Generation (GWh)
        'gen_solar_gwh': 'gen_solar_gwh',
        'solar_gwh': 'gen_solar_gwh',
        'gen_wind_gwh': 'gen_wind_gwh',
        'wind_gwh': 'gen_wind_gwh',
        'gen_hydro_gwh': 'gen_hydro_gwh',
        'hydro_gwh': 'gen_hydro_gwh',
        'gen_other_renewables_gwh': 'gen_other_renewables_gwh',
        'other_renewables_gwh': 'gen_other_renewables_gwh',
        'gen_coal_gwh': 'gen_coal_gwh',
        'coal_gwh': 'gen_coal_gwh',
        'gen_gas_gwh': 'gen_gas_gwh',
        'gas_gen_gwh': 'gen_gas_gwh',
        'gen_nuclear_gwh': 'gen_nuclear_gwh',
        'nuclear_gwh': 'gen_nuclear_gwh',
        
        # Grid Demand & T&D Losses (GWh)
        'demand_gwh': 'demand_gwh',
        'grid_demand_gwh': 'demand_gwh',
        'td_losses_gwh': 'td_losses_gwh',
        
        # Primary Energy Total (GWh)
        'primary_energy_gwh': 'primary_energy_gwh',
        
        # Economic Indicators
        'gdp_current_usd': 'gdp_current_usd',
        'gdp_growth_pct': 'gdp_growth_pct',
        'population': 'population',
        'co2_emissions_tonnes': 'co2_emissions_tonnes',
        
        # Gas Balance (BCF)
        'gas_production_bcf': 'gas_production_bcf',
        'production_bcf': 'gas_production_bcf',
        'gas_consumption_bcf': 'gas_consumption_bcf',
        'consumption_bcf': 'gas_consumption_bcf',
        'gas_gap_bcf': 'gas_gap_bcf',
        'gap_bcf': 'gas_gap_bcf',
        'lng_imports_bcf': 'lng_imports_bcf',
        'lng_value_musd': 'lng_value_musd',
        
        # Sustainability Class (STRING FIELD)
        'sustainability_class': 'sustainability_class',
    }
    
    for csv_key, db_key in field_map.items():
        if csv_key in df.columns:
            val = row[csv_key]
            if pd.notna(val):
                # Keep string fields as strings, convert others to float
                if db_key in string_fields:
                    result[db_key] = str(val)
                else:
                    try:
                        result[db_key] = float(val)
                    except (ValueError, TypeError):
                        # If conversion fails, skip this field
                        pass
    
    # Handle breakdown tables (by_source, by_sector, by_province)
    # These would be columns like: supply_source_1, cons_source_1, sector_cons_1, etc.
    for col in df.columns:
        if col.startswith('supply_source_'):
            try:
                sid = int(col.split('_')[-1])
                val = row[col]
                if pd.notna(val):
                    result[f'supply_source_{sid}'] = float(val)
            except (ValueError, TypeError):
                pass
        elif col.startswith('cons_source_'):
            try:
                sid = int(col.split('_')[-1])
                val = row[col]
                if pd.notna(val):
                    result[f'cons_source_{sid}'] = float(val)
            except (ValueError, TypeError):
                pass
        elif col.startswith('sector_cons_'):
            try:
                sid = int(col.split('_')[-1])
                val = row[col]
                if pd.notna(val):
                    result[f'sector_cons_{sid}'] = float(val)
            except (ValueError, TypeError):
                pass
        elif col.startswith('province_cons_'):
            try:
                pid = int(col.split('_')[-1])
                val = row[col]
                if pd.notna(val):
                    result[f'province_cons_{pid}'] = float(val)
            except (ValueError, TypeError):
                pass
    
    return result


def sidebar() -> None:
    st.sidebar.markdown(
        '<div style="padding:14px;background:rgba(14,165,233,0.1);border-radius:10px;'
        'border:1px solid rgba(14,165,233,0.25);margin-bottom:14px;">'
        '<div style="color:#22D3EE;font-size:11px;font-weight:800;'
        'text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px;">'
        'Data Management</div>'
        '<div style="color:#CBD5E1;font-size:12px;line-height:1.5;">'
        'Add, edit, delete, or restore year data.<br>'
        'Only the <b>first</b> or <b>latest</b> year can be deleted.</div>'
        '</div>', unsafe_allow_html=True)

    st.sidebar.markdown(
        '<div style="color:#8B95A7;font-size:10px;text-transform:uppercase;'
        'letter-spacing:1px;padding:4px 12px 6px;">Actions</div>',
        unsafe_allow_html=True)

    summary = get_current_data_summary()
    next_year = summary['next_year']
    all_years = summary.get('all_years', [])

    if st.sidebar.button(
        f"Add Year {next_year}", use_container_width=True, type="primary",
        help=f"Add data for year {next_year} (sequential only)"
    ):
        st.session_state["de_mode"] = "add"
        st.session_state["de_year"] = next_year
        st.rerun()

    st.sidebar.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    if all_years:
        selected = st.sidebar.selectbox(
            "Select Year", options=all_years, index=len(all_years) - 1,
            key="de_year_selector")

        c1, c2 = st.sidebar.columns(2)
        with c1:
            if st.button("Edit", use_container_width=True, key="de_btn_edit",
                         help=f"Edit data for {selected}"):
                st.session_state["de_mode"] = "edit"
                st.session_state["de_year"] = selected
                st.rerun()
        with c2:
            can_del = selected in (all_years[0], all_years[-1]) and len(all_years) > 1
            if st.button("Delete", use_container_width=True, key="de_btn_del",
                         disabled=not can_del,
                         help="Delete first or latest year only"):
                st.session_state["de_mode"] = "delete"
                st.session_state["de_year"] = selected
                st.rerun()

    st.sidebar.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    if st.sidebar.button("Restore Deleted", use_container_width=True,
                         key="de_btn_restore",
                         help="Restore a previously deleted year"):
        st.session_state["de_mode"] = "restore"
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown(
        '<div style="color:#8B95A7;font-size:10px;text-transform:uppercase;'
        'letter-spacing:1px;padding:4px 12px 4px;">Range</div>',
        unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<div style="color:#CBD5E1;font-size:11px;">'
        f'{summary["first_year"]} – {summary["latest_year"]}</div>',
        unsafe_allow_html=True)

# ── Render ────────────────────────────────────────────────────────────────────

def _mode_header(mode: str, year: int) -> None:
    if mode == "add":
        title = f"Add New Year Data"
        sub = (f"Enter energy data for year <b>{year}</b>. "
               "Only sequential years are allowed (the year after the latest existing data). "
               "All dashboards will update automatically after saving.")
    elif mode == "edit":
        title = f"Edit Year {year}"
        sub = (f"Modify existing data for year <b>{year}</b>. "
               "Changes will reflect across all dashboards immediately after saving.")
    elif mode == "delete":
        title = f"Delete Year {year}"
        sub = (f"Delete all data for year <b>{year}</b>. "
               "Only the first or latest year can be deleted. "
               "A backup is kept so you can restore it later.")
    else:
        title = "Restore Deleted Year"
        sub = ("Restore a previously deleted year's data from backup.")

    st.markdown(
        f'<div class="de-panel">'
        f'<div class="de-title">{title}</div>'
        f'<div class="de-subtitle">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True)


def _form_inputs(existing: dict, label: str = "") -> dict:
    """Render all input fields and return the collected values dict."""
    
    # Merge CSV import data (highest priority), then existing DB data, then defaults
    csv_data = st.session_state.get("csv_import_data", {}) or {}
    merged_data = {**existing, **csv_data}
    
    # ── Section 1: Energy Overview ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Energy Overview (TOE)</div>',
        unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]:
        total_primary_supply = st.number_input(
            f"Total Primary Supply (TOE){label}", min_value=0.0,
            value=float(merged_data.get("total_primary_supply_toe") or 0.0),
            step=1000.0, format="%.0f")
    with c[1]:
        total_final_consumption = st.number_input(
            f"Total Final Consumption (TOE){label}", min_value=0.0,
            value=float(merged_data.get("total_final_consumption_toe") or 0.0),
            step=1000.0, format="%.0f")
    with c[2]:
        transformation_losses = st.number_input(
            f"Transformation Losses (TOE){label}", min_value=0.0,
            value=float(merged_data.get("transformation_losses_toe") or 0.0),
            step=1000.0, format="%.0f")
    with c[3]:
        td_losses = st.number_input(
            f"T&D Losses (TOE){label}", min_value=0.0,
            value=float(merged_data.get("td_losses_toe") or 0.0),
            step=1000.0, format="%.0f")
    c = st.columns(4)
    with c[0]:
        total_losses = st.number_input(
            f"Total Losses (TOE){label}", min_value=0.0,
            value=float(merged_data.get("total_losses_toe") or 0.0),
            step=1000.0, format="%.0f")
    with c[1]:
        energy_transformation = st.number_input(
            f"Energy Used in Transformation (TOE){label}", min_value=0.0,
            value=float(merged_data.get("energy_used_in_transformation") or 0.0),
            step=100.0, format="%.0f")
    with c[2]:
        energy_sector_own = st.number_input(
            f"Energy Sector Own Use (TOE){label}", min_value=0.0,
            value=float(merged_data.get("energy_sector_own_use") or 0.0),
            step=100.0, format="%.0f")
    with c[3]:
        savings_toe = st.number_input(
            f"Savings (TOE){label}", min_value=0.0,
            value=float(merged_data.get("savings_toe") or 0.0),
            step=1000.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 2: Electricity Generation ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Electricity Generation (GWh / MW)</div>',
        unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]:
        installed_capacity = st.number_input(
            f"Installed Capacity (MW){label}", min_value=0.0,
            value=float(merged_data.get("installed_capacity_mw") or 0.0),
            step=100.0, format="%.0f")
    with c[1]:
        generation_gwh = st.number_input(
            f"Generation (GWh){label}", min_value=0.0,
            value=float(merged_data.get("generation_gwh") or 0.0),
            step=100.0, format="%.0f")
    with c[2]:
        imports_gwh = st.number_input(
            f"Imports (GWh){label}", min_value=0.0,
            value=float(merged_data.get("imports_gwh") or 0.0),
            step=100.0, format="%.0f")
    with c[3]:
        consumption_gwh = st.number_input(
            f"Consumption (GWh){label}", min_value=0.0,
            value=float(merged_data.get("consumption_gwh") or 0.0),
            step=100.0, format="%.0f")
    c = st.columns(2)
    with c[0]:
        demand_gwh = st.number_input(
            f"Grid Demand (GWh){label}", min_value=0.0,
            value=float(merged_data.get("demand_gwh") or 0.0),
            step=100.0, format="%.0f",
            help="Total grid demand reported in fact_renewable_energy (distinct from billed consumption)")
    with c[1]:
        td_losses_gwh = st.number_input(
            f"T&D Losses (GWh){label}", min_value=0.0,
            value=float(merged_data.get("td_losses_gwh") or 0.0),
            step=100.0, format="%.0f",
            help="Stored in fact_td_losses (GWh); distinct from T&D Losses TOE above")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 3: Renewable Energy Generation ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Renewable Energy Generation (GWh)</div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        gen_solar = st.number_input("Solar (GWh)", min_value=0.0,
                                    value=float(merged_data.get("gen_solar_gwh") or 0.0),
                                    step=100.0, format="%.0f")
        gen_wind = st.number_input("Wind (GWh)", min_value=0.0,
                                   value=float(merged_data.get("gen_wind_gwh") or 0.0),
                                   step=100.0, format="%.0f")
        gen_hydro = st.number_input("Hydro (GWh)", min_value=0.0,
                                    value=float(merged_data.get("gen_hydro_gwh") or 0.0),
                                    step=100.0, format="%.0f")
    with c2:
        gen_other_re = st.number_input("Other Renewables (GWh)", min_value=0.0,
                                       value=float(merged_data.get("gen_other_renewables_gwh") or 0.0),
                                       step=100.0, format="%.0f")
        gen_coal = st.number_input("Coal (GWh)", min_value=0.0,
                                   value=float(merged_data.get("gen_coal_gwh") or 0.0),
                                   step=100.0, format="%.0f")
        gen_gas = st.number_input("Gas (GWh)", min_value=0.0,
                                  value=float(merged_data.get("gen_gas_gwh") or 0.0),
                                  step=100.0, format="%.0f")
        gen_nuclear = st.number_input("Nuclear (GWh)", min_value=0.0,
                                      value=float(merged_data.get("gen_nuclear_gwh") or 0.0),
                                      step=100.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 3b: Primary Energy Total ──
    primary_energy_gwh = st.number_input(
        f"Total Primary Energy (GWh){label}", min_value=0.0,
        value=float(merged_data.get("primary_energy_gwh") or 0.0),
        step=1000.0, format="%.0f",
        help="Primary energy in GWh as stored in fact_renewable_energy.primary_energy_gwh")

    # ── Section 4: Economic Indicators ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Economic Indicators</div>',
        unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]:
        gdp_usd = st.number_input("GDP (Current USD)", min_value=0.0,
                                  value=float(merged_data.get("gdp_current_usd") or 0.0),
                                  step=1000000.0, format="%.0f")
    with c[1]:
        gdp_growth = st.number_input("GDP Growth (%)", min_value=-100.0, max_value=100.0,
                                     value=float(merged_data.get("gdp_growth_pct") or 0.0),
                                     step=0.1, format="%.1f")
    with c[2]:
        population = st.number_input("Population", min_value=0,
                                     value=int(merged_data.get("population") or 0),
                                     step=100000, format="%d")
    with c[3]:
        co2_emissions = st.number_input("CO2 Emissions (tonnes)", min_value=0.0,
                                        value=float(merged_data.get("co2_emissions_tonnes") or 0.0),
                                        step=100000.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 5: Primary Energy Supply by Source ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Primary Energy Supply by Source (TOE)</div>',
        unsafe_allow_html=True)
    sources = _get_sources()
    supply_by_source = {}
    if sources:
        cols = st.columns(min(4, len(sources)))
        for idx, (sid, sname) in enumerate(sources):
            with cols[idx % len(cols)]:
                supply_by_source[sid] = st.number_input(
                    sname, min_value=0.0,
                    value=float(merged_data.get(f"supply_source_{sid}", 0.0)),
                    step=1000.0, format="%.0f", key=f"ss_{sid}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 6: Final Consumption by Source ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Final Energy Consumption by Source (TOE)</div>',
        unsafe_allow_html=True)
    cons_by_source = {}
    if sources:
        cols = st.columns(min(4, len(sources)))
        for idx, (sid, sname) in enumerate(sources):
            with cols[idx % len(cols)]:
                cons_by_source[sid] = st.number_input(
                    sname, min_value=0.0, key=f"cs_{sid}",
                    value=float(merged_data.get(f"cons_source_{sid}", 0.0)),
                    step=1000.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 7: Sector-wise Electricity Consumption ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Sector-wise Electricity Consumption (GWh)</div>',
        unsafe_allow_html=True)
    sectors = _get_sectors()
    sector_cons = {}
    if sectors:
        cols = st.columns(min(4, len(sectors)))
        for idx, (sid, sname) in enumerate(sectors):
            with cols[idx % len(cols)]:
                sector_cons[sid] = st.number_input(
                    sname, min_value=0.0, key=f"sc_{sid}",
                    value=float(merged_data.get(f"sector_cons_{sid}", 0.0)),
                    step=100.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 8: Province-wise Electricity Consumption ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Province-wise Electricity Consumption (GWh)</div>',
        unsafe_allow_html=True)
    provinces = _get_provinces()
    prov_cons = {}
    if provinces:
        cols = st.columns(min(4, len(provinces)))
        for idx, (pid, pname) in enumerate(provinces):
            with cols[idx % len(cols)]:
                prov_cons[pid] = st.number_input(
                    pname, min_value=0.0, key=f"pc_{pid}",
                    value=float(merged_data.get(f"province_cons_{pid}", 0.0)),
                    step=100.0, format="%.0f")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 9: Gas Data ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Gas Balance (BCF)</div>',
        unsafe_allow_html=True)
    c = st.columns(4)
    with c[0]:
        gas_production = st.number_input("Gas Production (BCF)", min_value=0.0,
                                         value=float(merged_data.get("gas_production_bcf") or 0.0),
                                         step=100.0, format="%.0f")
    with c[1]:
        gas_consumption = st.number_input("Gas Consumption (BCF)", min_value=0.0,
                                          value=float(merged_data.get("gas_consumption_bcf") or 0.0),
                                          step=100.0, format="%.0f")
    with c[2]:
        gas_gap = st.number_input(
            "Gas Gap (BCF)", 
            min_value=None, max_value=None,
            value=float(merged_data.get("gas_gap_bcf") or 0.0),
            step=100.0, format="%.1f", help="Negative values indicate consumption exceeding production"
        )
    with c[3]:
        lng_imports = st.number_input("LNG Imports (BCF)", min_value=0.0,
                                      value=float(merged_data.get("lng_imports_bcf") or 0.0),
                                      step=100.0, format="%.0f")
    lng_value_musd = st.number_input(
        f"LNG Imports Value (Million USD){label}", min_value=0.0,
        value=float(merged_data.get("lng_value_musd") or 0.0),
        step=100.0, format="%.0f",
        help="Total cost of LNG imports in million USD (fact_lng_imports.imports_value_musd)")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Section 10: Renewable Capacity ──
    st.markdown(
        '<div class="de-section"><div class="de-section-title">Renewable Installed Capacity (MW)</div>',
        unsafe_allow_html=True)
    re_capacity = st.number_input(
        "Total RE Capacity (MW)", min_value=0.0,
        value=float(merged_data.get("capacity_mw") or 0.0),
        step=100.0, format="%.0f")

    _classes = ["Unsustainable", "Sustainable", "Critical", "Futuristic"]
    _cur_class = str(merged_data.get("sustainability_class") or "Unsustainable")
    sustainability_class = st.selectbox(
        f"Sustainability Class{label}",
        options=_classes,
        index=_classes.index(_cur_class) if _cur_class in _classes else 0)
    st.markdown('</div>', unsafe_allow_html=True)

    return {
        "total_primary_supply_toe": total_primary_supply,
        "total_final_consumption_toe": total_final_consumption,
        "transformation_losses_toe": transformation_losses,
        "td_losses_toe": td_losses,
        "total_losses_toe": total_losses,
        "energy_used_in_transformation": energy_transformation,
        "energy_sector_own_use": energy_sector_own,
        "savings_toe": savings_toe,
        "sustainability_class": sustainability_class,
        "installed_capacity_mw": installed_capacity,
        "generation_gwh": generation_gwh,
        "imports_gwh": imports_gwh,
        "consumption_gwh": consumption_gwh,
        "capacity_mw": re_capacity,
        "gen_solar_gwh": gen_solar,
        "gen_wind_gwh": gen_wind,
        "gen_hydro_gwh": gen_hydro,
        "gen_other_renewables_gwh": gen_other_re,
        "gen_coal_gwh": gen_coal,
        "gen_gas_gwh": gen_gas,
        "gen_nuclear_gwh": gen_nuclear,
        "demand_gwh": demand_gwh,
        "primary_energy_gwh": primary_energy_gwh,
        "gdp_current_usd": gdp_usd,
        "gdp_growth_pct": gdp_growth,
        "population": population,
        "co2_emissions_tonnes": co2_emissions,
        "td_losses_gwh": td_losses_gwh,
        "gas_production_bcf": gas_production,
        "gas_consumption_bcf": gas_consumption,
        "gas_gap_bcf": gas_gap,
        "lng_imports_bcf": lng_imports,
        "lng_value_musd": lng_value_musd,
        "supply_by_source": supply_by_source,
        "cons_by_source": cons_by_source,
        "sector_cons": sector_cons,
        "prov_cons": prov_cons,
    }


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    mode = st.session_state.get("de_mode", "add")
    year = st.session_state.get("de_year", get_next_year())

    _mode_header(mode, year)

    # ── DELETE / RESTORE modes: confirmation only, no form ───────────────────

    if mode == "delete":
        existing = fetch_year_data(year)
        st.warning(
            f"You are about to delete all data for year **{year}**. "
            f"This action can be undone using the Restore button."
        )
        if existing:
            with st.expander("Preview data to be deleted"):
                st.json({k: v for k, v in existing.items() if v is not None})
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button(f"Confirm Delete Year {year}", type="primary", use_container_width=True):
                mode_del = "latest" if year == get_latest_year() else "first"
                success, message = delete_year_data(year, mode_del)
                if success:
                    for k in ("de_mode", "de_year"):
                        st.session_state.pop(k, None)
                    st.success(message)
                else:
                    st.error(message)
        with col_d2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("de_mode", None)
                st.rerun()
        return

    if mode == "restore":
        # Show list of backed-up years from permanent backup files
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "backups")
        backup_years = []
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                if f.startswith("deleted_backup_") and f.endswith(".json"):
                    year_str = f.replace("deleted_backup_", "").replace(".json", "")
                    try:
                        backup_years.append(int(year_str))
                    except ValueError:
                        pass
            backup_years.sort()

        if not backup_years:
            st.info("No deleted years found in backup. Nothing to restore.")
            if st.button("Back", use_container_width=True):
                st.session_state.pop("de_mode", None)
                st.rerun()
            return

        chosen = st.selectbox("Select year to restore", backup_years)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button(f"Restore Year {chosen}", type="primary", use_container_width=True):
                success, message = restore_year_data(chosen)
                if success:
                    st.session_state.pop("de_mode", None)
                    st.success(message)
                else:
                    st.error(message)
        with col_r2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pop("de_mode", None)
                st.rerun()
        return

    # ── ADD / EDIT modes: full form ──────────────────────────────────────────

    existing = fetch_year_data(year) if mode == "edit" else {}
    lbl = "" if mode == "add" else f" ({year})"

    with st.form("de_form", clear_on_submit=False):
        inputs = _form_inputs(existing, lbl)

        st.markdown("<br>", unsafe_allow_html=True)

        btn_label = f"Save Year {year}" if mode == "add" else f"Update Year {year}"
        submitted = st.form_submit_button(btn_label, use_container_width=True, type="primary")

        if submitted:
            data = {k: v for k, v in inputs.items()
                    if k not in ("supply_by_source", "cons_by_source",
                                 "sector_cons", "prov_cons")}
            data = {k: v for k, v in data.items() if v is not None}

            for sid, v in inputs["supply_by_source"].items():
                data[f"supply_source_{sid}"] = v
            for sid, v in inputs["cons_by_source"].items():
                data[f"cons_source_{sid}"] = v
            for sid, v in inputs["sector_cons"].items():
                data[f"sector_cons_{sid}"] = v
            for pid, v in inputs["prov_cons"].items():
                data[f"province_cons_{pid}"] = v

            with st.spinner("Processing..."):
                if mode == "add":
                    success, message = insert_year_data(year, data)
                else:
                    success, message = update_year_data(year, data)

            # Clear CSV import data and all keyed widget states so the form resets
            st.session_state.pop("csv_import_data", None)
            for k in list(st.session_state.keys()):
                if k.startswith(("ss_", "cs_", "sc_", "pc_")):
                    del st.session_state[k]

            st.session_state["de_result"] = {"success": success, "message": message}
            st.rerun()

    # ── Show save result OUTSIDE the form (buttons/status inside a form raise) ──
    result = st.session_state.pop("de_result", None)
    if result:
        if result["success"]:
            st.success(result["message"])
            st.info("All dashboards have been updated.")
        else:
            st.error(result["message"])

    st.markdown(
        '<div class="de-info">'
        '<b>Rules:</b><br>'
        '• <b>Add:</b> Only the next sequential year (e.g., after 2024 → 2025)<br>'
        '• <b>Edit:</b> Any existing year can be modified<br>'
        '• <b>Delete:</b> Only the first or latest year (no mid-year deletion)<br>'
        '• <b>Restore:</b> Restore a previously deleted year from backup<br>'
        '• All values must be positive numbers<br>'
        '• Supply should be ≥ Consumption'
        '</div>',
        unsafe_allow_html=True)

    # ── CSV Upload Section ────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    
    with st.expander("📥 Upload CSV Data (Auto-fill Form)", expanded=False):
        st.markdown(
            "<p style='color:#94A3B8;font-size:13px;margin-bottom:12px;'>"
            "Upload a CSV file containing year data. The form will auto-fill with values. "
            "Ensure your CSV has column headers matching field names below.</p>",
            unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="CSV with columns like: year, total_primary_supply_toe, generation_gwh, etc."
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head(3), use_container_width=True, height=100)
                
                if st.button("🔄 Auto-fill Form with CSV Data", use_container_width=True):
                    csv_data = _parse_csv_for_year(df)
                    if csv_data:
                        # Store parsed data in session state for form prefill
                        st.session_state["csv_import_data"] = csv_data
                        # Clear keyed widget states so breakdown inputs pick up new values
                        # (Streamlit ignores value= for widgets whose key already has state)
                        for k in list(st.session_state.keys()):
                            if k.startswith(("ss_", "cs_", "sc_", "pc_")):
                                del st.session_state[k]
                        st.success(f"✅ Loaded {len(csv_data)} fields from CSV!")
                        st.rerun()
                    else:
                        st.error("⚠️ No recognizable data found. Check column names.")
            
            except Exception as e:
                st.error(f"❌ Error reading CSV: {str(e)}")

    # Apply CSV data to form if available
    if "csv_import_data" in st.session_state and st.session_state.csv_import_data:
        st.info(
            f"ℹ️ {len(st.session_state.csv_import_data)} fields loaded from CSV. "
            "Review values in the form above before saving.",
            icon="💡"
        )
