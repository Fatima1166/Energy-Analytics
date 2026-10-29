# Unit Selection & Unit Conversion — Implementation Guide

**Project:** `D:\Fatima Projects\energy_dashboard`
**Database:** `energy_database_new` (MySQL / MariaDB 10.4.32, XAMPP)
**Date:** 2026

---

## 1. Short answer to the question

> *"The database uses a different unit for almost everything — can the units be
> organised?"*

**Yes — but not by rewriting the stored data.** The safe, standard approach has
three layers:

| Layer | What it does | Where |
|---|---|---|
| **1. Storage** | Exactly **one** canonical base unit per domain | MySQL fact tables |
| **2. Metadata** | Base unit → display unit + exact factor | `dim_unit`, `dim_unit_metadata` |
| **3. Presentation** | The unit the user picked, converted at render time | Streamlit sidebar (`core/units.py`) |

*No stored value has to be touched.* The data stays exactly as it is in its base
unit, and the dashboard applies
`value_display = value_base × factor` only when it draws something. That means:

* no loss of precision (the stored numbers never change),
* no extra column needed for every new display unit,
* changing a factor in one place updates the whole dashboard.

---

## 2. What was actually found in the live database

`dim_unit_metadata` (105 rows) already exists and every row resolves to a real
column — the storage layer had **already been normalised** before this change:

| Domain | Base unit (storage) | Display units available |
|---|---|---|
| Energy | `TOE` | TOE, MTOE, KTOE |
| Electricity | `GWh` | GWh, TWh, MWh |
| Power | `MW` | MW, GW, kW |
| Gas | `BCF` | BCF, TCF, MMSCF |
| Emission | `t` (tonnes CO₂) | t, Mt, kt |
| Economic | `USD` / `%` / `Persons` | fixed — not converted |

Conversion only ever touches a value that was **reported for its own year**. A
year inside the reported window (up to 2024) that the database did not report
stays blank — it is not filled with 0, carried from another year, or
interpolated — so the unit dropdown converts real readings and nothing else.
Projections start at 2025 (`Projected` in the data layer). See *Missing years &
the projection window* in the root [README.md](README.md).

**However the Streamlit code was still reading the OLD column names**
(`gen_solar_twh`, `total_primary_supply_mtoe`, `imports_mmcf`,
`proved_reserves_tcm`), which no longer exist. The dashboard was therefore
broken *and* had no unit selector. Both problems are fixed in this change.

---

## 3. Conversion formulas used

```
ENERGY        (base TOE)
    TOE   = TOE              KTOE = TOE × 0.001          MTOE = TOE × 1e-06

ELECTRICITY   (base GWh)
    GWh   = GWh              MWh  = GWh × 1000           TWh  = GWh × 0.001

POWER         (base MW)
    MW    = MW               kW   = MW  × 1000           GW   = MW  × 0.001

GAS           (base BCF)
    BCF   = BCF              MMSCF = BCF × 1000          TCF  = BCF × 0.001
                             (MMSCF == MMCF)

EMISSION      (base t = tonnes of CO2)
    t     = t                kt   = t   × 0.001          Mt   = t   × 1e-06

ECONOMIC      (fixed)
    USD / % / Persons — no conversion
```

Emission factors stay as they are (`tCO₂/MWh` — a ratio, unit-system independent).
CO₂ mass is derived in the base unit and converted only for display:

```
CO2_t = gen_GWh × 1000 (MWh/GWh) × Σ(fuel_generation_share × emission_factor)
```

---

## 4. How the slicer works

Sidebar order: dashboard switcher, then the active dashboard's own slicers, then
unit selection. Each dashboard declares which unit families it renders in
`dashboards/registry.py`, so the sidebar never offers a unit that dashboard does
not use.

**Q2 — Renewable Scenarios** (`units: electricity, power, emission`):

```
Dashboards        ( o ) Renewable Scenarios
─────────────────────────────────────────────
Slicers & Parameters
  Scenario          [ Accelerated ▾ ]
  Growth Rate %     [ ──────●──── ] 15.0
  Year Range        [ ●──────────● ] 2000 – 2035
─────────────────────────────────────────────
Unit Selection
  Electricity  [ GWh ▾ ]
  Power        [ MW  ▾ ]
  Emission     [ t   ▾ ]
```

**Q3 — Target Bottlenecks** (`units: energy, gas`):

```
Dashboards        ( o ) Target Bottlenecks
─────────────────────────────────────────────
Analysis Range
  Year Range        [ ●──────────● ] 2002 – 2035
─────────────────────────────────────────────
Unit Selection
  Energy       [ TOE ▾ ]
  Gas          [ BCF ▾ ]
```

**Q4 — Forecasted Demand** (`units: energy, electricity`):

```
Dashboards        ( o ) Forecasted Demand
─────────────────────────────────────────────
Forecast
  Scenarios to show [ Low / Base / High ]
  Forecast up to    [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Energy       [ TOE ▾ ]
  Electricity  [ GWh ▾ ]
```

**Q5 — Forecasted Supply** (`units: energy, electricity`):

```
Dashboards        ( o ) Forecasted Supply
─────────────────────────────────────────────
Supply
  Scenarios to show [ Low / Base / High ]
  Forecast up to    [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Energy       [ TOE ▾ ]
  Electricity  [ GWh ▾ ]
```

**Q6 — Supply Chain Optimization** (`units: electricity, power, gas`):

```
Dashboards        ( o ) Supply Chain Optimization
─────────────────────────────────────────────
Supply Chain
  Which part counts most [ All four parts equally ▾ ]
  Years to judge         [ ●──────────● ] 2002 – 2024
─────────────────────────────────────────────
Unit Selection
  Electricity  [ GWh ▾ ]
  Power        [ MW  ▾ ]
  Gas          [ BCF ▾ ]
```

**Q7 — Forecasted Producer Cost** (`units: cost`):

```
Dashboards        ( o ) Forecasted Producer Cost
─────────────────────────────────────────────
Producer Cost
  Build-out cases to show [ Little clean power / … ]
  Forecast up to          [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Cost  [ USD bn ▾ ]
```

**Q8 — Sustainable Strategy** (`units: cost`):

```
Dashboards        ( o ) Sustainable Strategy
─────────────────────────────────────────────
Sustainable Strategy
  What counts most              [ Balanced (planner's default) ▾ ]
  Money a year for new measures [ ────●──── ] 8.0
  Plan up to                    [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Cost  [ USD bn ▾ ]
```

Only three figures on Q8 follow the Cost dropdown — K3's money, the cost line in
V2's tooltip and the cost column of the funded list. The four-pillar score and the
points-per-$bn ranking are unitless yardsticks and stay as they are; the ranking's
yardstick is fixed at $bn on purpose, because one measure costs 0.2 to 3.0 bn and
any smaller unit turns the bars into decimals.

**Q9 — Operational Bottlenecks** (`units: electricity, power, gas`):

```
Dashboards        ( o ) Operational Bottlenecks
─────────────────────────────────────────────
Operational Bottlenecks
  Year to judge [ ●──────────● ] 2024
─────────────────────────────────────────────
Unit Selection
  Electricity  [ GWh ▾ ]
  Power        [ MW  ▾ ]
  Gas          [ BCF ▾ ]
```

Only the physical amounts move with the dropdowns — the energy in V3, the gas in
V4, and the MW / GWh / BCF rows inside the three cards.  The severity scores and
every percentage (capacity factors, home gas met, fuel bought abroad) are ratios
of two figures in the same unit, so they stay put whatever the reader picks.

**Q10 — Optimal Resource Allocation** (`units: electricity, cost, emission`):

```
Dashboards        ( o ) Optimal Resource Allocation
─────────────────────────────────────────────
Resource Allocation
  What the plan should favour   [ Balanced (planner's default) ▾ ]
  How fast demand grows (% a year) [ ────●──── ] 4.5
  Plan up to                    [ ─────────●─ ] 2035
─────────────────────────────────────────────
Unit Selection
  Electricity  [ GWh    ▾ ]
  Cost         [ USD bn ▾ ]
  Emission     [ t      ▾ ]
```

The three dropdowns cover everything the page draws: Electricity drives the need
on K1, the V1 and V3 axes and the four power columns of the plan table; Cost
drives K2, V2's cost line and the table's cost column; Emission drives K2's CO₂
row, V2's carbon line and the table's CO₂ column.

What does *not* move: the clean share, the fuel-bought-abroad share, the
"1.6× the 2024 need" ratio, the unserved percentage, and the six 0–100 scores on
V4 — each is a ratio of two figures in the same unit, or a fixed-reference
yardstick.  `Gas` was dropped from this page's declaration when the gas
self-sufficiency card went; nothing on Q10 prints BCF any more, so the sidebar
would otherwise offer a slicer with nothing to slice.

* **Default of every dropdown = the database BASE UNIT** of that domain  (`TOE`, `GWh`, `MW`, `BCF`, `t`; `USD bn` on the three pages whose money is worked
  out rather than stored — Q7, Q8 and Q10 — whose Cost domain stores in `USD`
  but starts a national yearly bill in billions, since in plain dollars the
  numbers run to ten digits) — i.e. the screen initially shows exactly what
  is stored in MySQL.
* Choosing any other unit re-renders that dashboard in the chosen unit: KPI
  cards, impact metrics, chart axes, hover tooltips and section badges.
* The choice lives in `st.session_state["unit_prefs"]` and is read by the page
  through `core.unit_slicer.get_units()`. A preference set on one dashboard
  survives while the other is open.
* Every sidebar uses one plain animated section title per block — there are no
  cards, badges or expanders around the controls.

### 4.1 Sidebar scrolling — exactly ONE scrollbar (important)

Streamlit 1.40's real scroll container is:

```js
div[data-testid="stSidebarContent"]   // styled: position:relative; height:100%; overflow:auto
```

`div[data-testid="stSidebarUserContent"]` is just a padded wrapper with **no**
overflow of its own, and the outer `section[data-testid="stSidebar"]` clips.

Two earlier mistakes were fixed here:

1. The original stylesheet forced `overflow-y: hidden !important` on the
   sidebar ("Compact & Non-Scrollable"). Once the unit selectors were added
   the lower widgets were clipped and unreachable.
2. Replacing that with `overflow-y: auto` on **all three** elements produced
   **two nested scrollbars**.

The correct rule set is now (in `core/styles.py`):

```css
section[data-testid="stSidebar"]              { overflow: hidden !important; }
section[data-testid="stSidebar"] > div:first-child,
div[data-testid="stSidebarContent"]           { overflow-y: auto !important;
                                                overflow-x: hidden !important;
                                                height: 100% !important;
                                                max-height: 100vh !important; }
div[data-testid="stSidebarUserContent"]       { overflow: visible !important;
                                                height: auto !important;
                                                max-height: none !important; }
```

**Rule:** only `stSidebarContent` may carry `overflow-y: auto`. Give the other
two `visible`/`hidden`, otherwise the double scrollbar comes back.

---

## 5. Files added / changed

| File | Status | Purpose |
|---|---|---|
| `core/units.py` | **new** | Unit registry, conversion engine, formulas, DB metadata bridge |
| `core/unit_slicer.py` | **new** | Sidebar unit selector + session accessors |
| `sql/unit_dimension.sql` | **new** | `dim_unit` master table + conversion/validation views |
| `core/queries.py` | changed | Queries updated to normalised base-unit columns |
| `core/projections.py` | changed | Scenario engine now works in GWh / MW / t / M USD |
| `core/icons.py` | changed | Added `units` and `convert` icons |
| `core/styles.py` | changed | Sidebar CSS reworked so it scrolls with exactly ONE scrollbar |
| `app.py` | changed | Runs dashboard slicers, then the global unit slicer, then the body |
| `dashboards/registry.py` | changed | Exposes the module (so `sidebar()` and `render()` can be split) |
| `dashboards/q2_renewable_scenarios/page.py` | changed | Unit-aware KPIs & metrics + `sidebar()` hook |
| `dashboards/q2_renewable_scenarios/charts.py` | changed | All 6 visuals convert axes/hover/labels |

Original files are backed up in `_backup_units_<timestamp>/` inside the project.

---

## 6. Verification performed (all green)

| # | Test | Result |
|---|---|---|
| 1 | Conversion engine — option lists, every formula, `base → display → base` round trips, aliases (`MMCF`, `tonnes`, `TWH`) | **passed** |
| 2 | Defaults are the DB base units for every domain | **TOE / GWh / MW / BCF / t** |
| 3 | Database cross-check — all 20 distinct `(domain, display_unit, conversion_factor)` groups in `dim_unit_metadata` vs the app factors | **0 mismatches** |
| 4 | Metadata integrity — all 105 `dim_unit_metadata` rows resolve to real columns | **105 OK, 0 orphans** |
| 5 | Headless app run (`streamlit.testing.v1.AppTest`, real MySQL) | **no exceptions** |
| 6 | Sidebar order — each dashboard shows its own slicers, then only its own unit dropdowns | **passed** |
| 7 | Conversion-reference table removed | **absent from the page** |
| 8 | Unit switching — KPI values update, stored base value never changes | **passed** |
| 9 | Chart-level check — y-axis titles, trace names, hover text and values for all 6 visuals | **passed** |
| 10 | Removed UI stays removed — no reset button, no "Conversion formulas" expander, no unit-metadata expander | **passed** |
| 11 | Fresh browser load (no unit ever selected) — KPI cards **and** every chart use the base units | **passed** (charts badged `GWh` / `t` / `MW` on Q2, `TOE` / `BCF` on Q3) |
| 12 | Sidebar CSS: exactly one `overflow-y: auto` (on `stSidebarContent`), `stSidebarUserContent` visible, outer section hidden | **passed** |
| 13 | Q4 sidebar order — its own six slicers, then only Energy and Electricity unit dropdowns | **passed** |
| 14 | Q4 unit switching — `TOE → MTOE` turns K1 from `76,561,193` into `76.56`, `GWh → TWh` turns K2 from `175,440` into `175.44` | **passed** |
| 15 | Q4 analysis engine reproduced from the command line (`scripts/verify_demand_forecast.py`) | **passed** — hold-out MAPE 3.7–23.3%, calibration R² 0.88–0.99 |
| 16 | All three dashboards render headless (`scripts/smoke_test_app.py`) | **no exceptions** |

Live proof from the headless run (KPI row, before → after changing the sidebar):

```
default : 41.0%  | 17,525 MW | 179,800,380 tCO₂ | $3,392 M USD | 24,000 GWh
changed : 41.0%  | 17.53 GW  | 179,800 ktCO₂     | $3,392 M USD | 24.00 TWh
```

---

## 7. Adding a new display unit later

1. Insert one row into `dim_unit` (`unit_code`, `domain`, `to_base`, …).
2. Add the code to the `units` list in `core/units.py` → `DOMAINS`
   (and set `"default"` to the base unit if it should be the initial choice).
3. Re-seed metadata for the affected columns (template in
   `sql/unit_dimension.sql` section 6).

No fact table is touched, and no chart/KPI code changes — they all read the
factor from the registry.
