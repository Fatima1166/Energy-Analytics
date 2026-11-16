# 📝 Dynamic Data Entry Feature

## Overview

Your Energy Dashboard is now **fully dynamic**! You can add new year data directly through the dashboard interface, and all dashboards, KPI cards, graphs, and predictions will automatically update.

## How It Works

### 1. Access the Data Entry Form

- Look for the **"📝 Add New Year Data"** button in the sidebar (below the logout button)
- Click it to open the data entry form
- Or select "📝 Add New Year Data" from the dashboard dropdown

### 2. Sequential Year Entry

The system enforces **sequential year entry**:
- If your latest data is **2024**, you can only add **2025**
- After adding 2025, you can then add **2026**
- You cannot skip years (e.g., jump from 2024 to 2026)

This ensures data integrity and proper timeline progression.

### 3. Data Categories

The form collects data in these categories:

#### 🏭 Energy Overview (TOE)
- **Total Primary Supply** - Total energy supply in tonnes of oil equivalent
- **Total Final Consumption** - Total energy consumption in TOE

#### ⚡ Electricity Generation (GWh / MW)
- **Generation** - Total electricity generation in GWh
- **Installed Capacity** - Total capacity in MW
- **Electricity Consumption** - Total consumption in GWh

#### 🌱 Renewable Energy Generation (GWh)
- Solar, Wind, Hydro generation
- Other Renewables
- Coal, Gas, Nuclear generation

#### 💰 Economic Indicators
- **GDP** - Gross Domestic Product in current USD
- **GDP Growth** - Growth rate percentage
- **Population** - Total population
- **CO2 Emissions** - Total emissions in tonnes

## Validation Rules

The system validates your data before saving:

✅ **Year Validation**
- Must be the next sequential year
- Cannot add a year that already exists

✅ **Numeric Validation**
- All values must be positive numbers
- Supply should be >= consumption
- Generation must be between 1,000 and 500,000 GWh (realistic range for Pakistan)

✅ **Data Quality**
- Reasonable ranges prevent accidental data entry errors
- Clear error messages guide you to fix issues

## What Happens After Adding Data

Once you successfully add data:

1. **Database Updates** - New year is inserted into all relevant tables
2. **Cache Clears** - All dashboard caches are cleared
3. **Automatic Refresh** - You'll see a success message with a refresh button
4. **All Dashboards Update**:
   - ✅ KPI cards show the new year
   - ✅ Graphs extend to include the new year
   - ✅ Sidebar year range sliders extend
   - ✅ Predictions shift forward (e.g., 2024→2035 becomes 2025→2036)
   - ✅ Historical data now includes your new year

## Example Workflow

### Scenario: Adding 2025 Data (when latest is 2024)

1. **Click** "📝 Add New Year Data" in sidebar
2. **Form shows**: "You can add year 2025"
3. **Enter data**:
   - Total Primary Supply: 55,000,000 TOE
   - Total Final Consumption: 48,000,000 TOE
   - Generation: 145,000 GWh
   - Capacity: 42,000 MW
   - Solar: 5,000 GWh
   - Wind: 3,500 GWh
   - GDP: 400,000,000,000 USD
   - Population: 240,000,000
   - ... (other fields)
4. **Click** "💾 Save Data"
5. **System validates** and inserts data
6. **Success message** appears with refresh button
7. **Click refresh** - all dashboards now show 2025!

### What Updates Automatically

| Dashboard | What Changes |
|-----------|--------------|
| **Home Overview** | KPI cards show 2025 data, graphs extend to 2025 |
| **Q1 Parameters** | Correlation data includes 2025, predictions shift to 2036 |
| **Q2 Scenarios** | Baseline is now 2025, scenarios run to 2036 |
| **Q3 Targets** | Target gaps calculated through 2025 |
| **Q4 Demand Forecast** | Historical now includes 2025, forecast extends to 2036 |
| **Q5 Supply Forecast** | Supply path includes 2025 actual data |
| **Q6-Q10** | All analyses now include 2025 in their datasets |

## Data Sources

Use official sources for accurate data:
- 📊 **Pakistan Energy Yearbook** (HDIP)
- 📈 **NEPRA State of the Industry Reports**
- 🏭 **OGRA Annual Reports**
- 💰 **Pakistan Economic Survey**
- 🌍 **World Bank Data**
- ⚡ **Ember Global Electricity Review**
- 🌱 **Our World in Data**

## Tips & Best Practices

1. **Start Small**: Add one year at a time, verify dashboards update correctly
2. **Use Official Data**: Always use verified government or international sources
3. **Check Validation Errors**: The system will tell you exactly what's wrong
4. **Leave Blanks OK**: If you don't have data for a field, leave it blank (defaults to 0)
5. **Refresh After**: Always refresh the page after adding data to see updates
6. **Backup First**: Consider backing up your database before adding new data

## Troubleshooting

### "Can only add year X"
- **Cause**: Trying to add a year that's not the next sequential year
- **Solution**: Add years in order (2024 → 2025 → 2026)

### "Year already exists"
- **Cause**: That year's data already exists in the database
- **Solution**: The year is already added, no action needed

### "Supply should be >= consumption"
- **Cause**: Primary supply is less than final consumption
- **Solution**: Check your numbers - supply should include all energy entering the system

### "Generation seems too low/high"
- **Cause**: Value is outside realistic range (1,000 - 500,000 GWh)
- **Solution**: Verify your generation data - it should be in GWh (not MWh or TWh)

### Data doesn't update after adding
- **Solution**: Click the "🔄 Refresh Page" button that appears after successful insertion

## Advanced: Adding More Tables

Currently, the form inserts into these tables:
- `dim_year` - Year dimension
- `fact_energy_overview` - Primary energy data
- `fact_renewable_energy` - Generation by source
- `fact_economic_indicators` - Economic data
- `fact_elec_generation` - Electricity generation

To add more tables (e.g., gas, LNG, T&D losses), edit `core/data_entry.py` and add new INSERT statements in the `insert_year_data()` function.

## Technical Details

- **Backend**: `core/data_entry.py` - Validation and database insertion
- **Frontend**: `dashboards/data_entry_form/page.py` - User interface
- **Transaction Safety**: All inserts happen in a transaction - if any fail, all roll back
- **Cache Management**: Automatically clears Streamlit caches after insertion
- **Sequential Enforcement**: `get_next_year()` ensures only the next year can be added

---

**Made with ❤️ for Pakistan Energy Analytics Dashboard**
