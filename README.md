# Pakistan Renewable Energy Outlook Dashboard

An interactive energy analytics platform — **React login portal + Streamlit dashboard** — backed by MySQL.

---

## Quick start (ONE command)

```powershell
cd "D:\Fatima Projects\energy_dashboard"
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

Or just double-click **`run_all.bat`**.

The launcher starts everything and opens the browser:

| # | Service | Port |
|---|---|---|
| 1 | MySQL (XAMPP) | 3306 |
| 2 | Flask API (bcrypt login) | 5000 |
| 3 | Streamlit dashboard | 8501 |
| 4 | **React login portal ← open this** | **5173** |

**Open http://localhost:5173** → sign in → the dashboard loads inside the portal.

Stop everything:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
#  add -WithMySQL to also stop MySQL
```

> Services that are already running are detected and skipped, so re-running the
> launcher is safe.

---

## Project Structure

```
energy_dashboard/
├── run_all.ps1 / run_all.bat     # one-command launcher
├── stop_all.ps1                  # stops portal + API + dashboard
├── app.py                        # Streamlit entry point
├── config/                       # settings (incl. LOGIN_MODE) + MySQL connection
├── core/
│   ├── auth.py                   # optional Streamlit login screen (LOGIN_MODE)
│   ├── units.py                  # unit registry + conversion engine
│   ├── unit_slicer.py            # sidebar unit selection (per-dashboard domains)
│   ├── queries.py                # SQL (all in base units)
│   ├── projections.py            # Q2 scenario engine
│   ├── bottleneck_metrics.py     # Q3 projection + gap engine
│   ├── demand_forecast.py        # Q4 demand history, drivers, scenarios, backtest
│   ├── supply_forecast.py        # Q5 supply history, technology mix, capacity, adequacy
│   ├── targets.py                # Q3 benchmarks (dim_target + policy override)
│   ├── styles.py                 # global CSS
│   └── components.py / icons.py  # UI building blocks (cards, footer)
├── dashboards/
│   ├── registry.py               # dashboard list + each one's unit domains
│   ├── q2_renewable_scenarios/   # Q2: page, charts, config, README.md, REPORT.md
│   ├── q3_target_bottlenecks/    # Q3: page, charts, config, README.md
│   ├── q4_forecast_demand/       # Q4: page, charts, config, README.md
│   └── q5_forecast_supply/       # Q5: page, charts, config, README.md
├── scripts/
│   ├── verify_demand_forecast.py # Q4 numbers, printed from live MySQL
│   ├── verify_supply_forecast.py # Q5 numbers, printed from live MySQL
│   └── smoke_test_app.py         # headless render check of every dashboard
├── login_portal/                 # React login portal + Flask API
│   ├── api_server.py             # Flask API (port 5000)
│   ├── db_core.py                # MySQL auth helpers
│   ├── generate_hash.py          # create a bcrypt user
│   └── frontend/                 # React + Vite (port 5173)
├── sql/unit_dimension.sql        # dim_unit + conversion views
├── assets/login_hero.jpg         # hero image
├── requirements.txt
├── UNIT_GUIDE.md                 # unit strategy + formulas + verification
└── energy_database_new.sql       # MySQL schema + seed data
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ (for the React portal) |
| MySQL / MariaDB | 8.0+ / 10.4+ (XAMPP is fine) |

---

## Step 1 — Set Up the Database

1. Start MySQL and (if needed) import the database:

```sql
CREATE DATABASE energy_database_new;
USE energy_database_new;
SOURCE path/to/energy_database_new.sql;
```

2. Set your MySQL credentials in `.env` (create if missing):

```env
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=
DB_NAME=energy_database_new
DB_PORT=3306
```

3. (Optional) add the unit dimension objects:

```powershell
& "D:\Fatima Programs\xampp\mysql\bin\mysql.exe" -u root energy_database_new -e "source D:/Fatima Projects/energy_dashboard/sql/unit_dimension.sql"
```

---

## Step 2 — Install dependencies

```powershell
cd "D:\Fatima Projects\energy_dashboard"
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

cd login_portal\frontend
npm install
```

> Use `python.exe -m pip` / `python.exe -m streamlit`, **not** the
> `.venv\Scripts\*.exe` shims. Those launchers embed the absolute path the venv
> was created at, so they break silently the moment the project folder is moved
> or renamed. The interpreter itself keeps working.

---

## Step 3 — Run

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

Then open **http://localhost:5173**.

---

## How Login Works

```
Browser  →  http://localhost:5173   (React portal)
                │
        POST /api/login   (Vite proxies /api → :5000)
                ▼
        Flask API  (:5000)  ──bcrypt.checkpw──►  MySQL `dim_users`
                │
        success │ failure
                ▼            ▼
        iframe loads     error message
        http://localhost:8501
        (Streamlit dashboard)
```

* Credentials are bcrypt hashes in the `dim_users` table.
* The dashboard is embedded in the portal, so the login is asked **once**.

### LOGIN_MODE (optional)

`config/settings.py`, or the `.env` variable `LOGIN_MODE`, controls who guards
the dashboard:

| Value | Behaviour |
|---|---|
| `react` *(default)* | The React portal on :5173 is the login; :8501 opens directly (needed for the iframe). |
| `streamlit` | The built-in Streamlit login screen in `core/auth.py` protects :8501 on its own — useful when running the dashboard without the portal. |

### Adding a user

```powershell
cd "D:\Fatima Projects\energy_dashboard"
.venv\Scripts\python.exe -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt(rounds=12)).decode())"
```

Paste the resulting `$2b$12$...` hash into `dim_users.password_hash`.

---

## Dashboards

Three dashboards, switched from the sidebar. Each shows only the unit families it
actually renders, and each ends with a short data-driven footer describing the
view currently on screen.

### Q2 — Renewable Scenarios

*What are the potential outcomes of installing renewable energy sources in different energy scenarios?*

| KPI / Visual | What it shows |
|---|---|
| RE Share % | Renewable share of generation at the range's final year, per scenario |
| RE Capacity | Installed renewable capacity the scenario builds to |
| CO₂ Emissions | Emissions remaining at the horizon (auto-scaled t / kt / Mt) |
| LNG Savings | Cumulative import bill avoided by displacing gas |
| CO₂ Intensity | Grid carbon intensity, kgCO₂/MWh |
| Visuals 1–6 | RE share path, generation mix, outcomes, CO₂ vs RE, capacity by source, capacity vs generation vs T&D |
| Slicers | Scenario, Growth Rate %, Year Range, Unit Selection |

Full details: [`dashboards/q2_renewable_scenarios/README.md`](dashboards/q2_renewable_scenarios/README.md)

### Q3 — Target Bottlenecks

*What are the bottlenecks in achieving planned targets?*

| KPI / Visual | What it shows |
|---|---|
| K1 Losses % | Energy losses against the 28.23% benchmark |
| K2 Import Dependence % | Imported share of primary supply |
| K3 Renewable Share % | Against the 30% ARE Policy target |
| K4 Gas Self-Sufficiency % | Domestic production vs consumption |
| Visuals 1–6 | Loss waterfall, losses vs benchmark, import dependence, gas balance, benchmark gaps, achievement vs benchmark |
| Slicers | Year Range, Unit Selection |

Full details: [`dashboards/q3_target_bottlenecks/README.md`](dashboards/q3_target_bottlenecks/README.md)

### Q4 — Forecasted Energy Demand (1999–2035)

*What is forecasted energy demand?*

| KPI / Visual | What it shows |
|---|---|
| K1 Total Demand | Total final energy now and at the horizon, per scenario |
| K2 Electricity Demand | Grid demand in GWh, now and at the horizon |
| K3 Demand Growth | Forecast CAGR against the reported CAGR |
| K4 Income Elasticity | ε from ln(demand/head) ~ ln(real GDP/head), with R² |
| K5 Supply–Demand Gap | Horizon gap as a share of primary supply, plus the supply CAGR needed to close it |
| Visuals 1–7 | History 1999–2024, scenario fan 2025–2035, demand drivers, growth decomposition, sector & province mix, supply gap & import dependency, backtest reliability |
| Slicers | Scenarios, Forecast basis (Driver/Trend), Calibration start, Forecast horizon, Base GDP growth, Scenario spread, Unit Selection |

Eight elements covering the six objectives: history (1), scenarios (2), drivers
(3), sector and province (4), supply gap and imports (5), backtest MAPE / RMSE /
R² (6).

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_demand_forecast.py
```

Full details: [`dashboards/q4_forecast_demand/README.md`](dashboards/q4_forecast_demand/README.md)

### Q5 — Forecasted Energy Supply (1999–2035)

*What is forecasted energy supply?*

| KPI / Visual | What it shows |
|---|---|
| K1 Total Primary Supply | Reported 2024 (75.7 MTOE) vs Horizon 2035 (Base ~93.2 MTOE) and implied CAGR % |
| K2 Power Generation Supply | Reported 2024 (154,480 GWh) vs Horizon 2035 (Base ~385,837 GWh) |
| K3 Clean Energy Share % | Clean generation share vs 60% national benchmark & 30% ARE solar+wind target |
| K4 Installed Capacity | Required installed capacity (MW/GW) across technology assets to 2035 |
| K5 Reserve Margin Adequacy | Supply vs demand reserve margin % corridor (15%–25% safe corridor, deficit vs trap) |
| Visuals 1–7 | History 1999–2024, scenario fan 2025–2035, technology mix, capacity expansion (MW), supply adequacy, energy security (indigenous vs imports), backtest reliability |
| Slicers | Scenarios, Forecast basis (Driver/Trend), Calibration start, Horizon, Base GDP growth, Spread, Clean policy target, Unit Selection |

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_supply_forecast.py
```

Full details: [`dashboards/q5_forecast_supply/README.md`](dashboards/q5_forecast_supply/README.md)

### Units

Every KPI and chart re-renders in the unit chosen in the sidebar. Q2 offers
Electricity, Power and Emission; Q3 offers Energy and Gas; Q4 offers Energy and
Electricity; Q5 offers Energy, Electricity and Power. The sidebar shows only
the domains the active dashboard uses — see [UNIT_GUIDE.md](UNIT_GUIDE.md) for
the formulas and the storage strategy.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Login says *"Could not connect to server"* | Flask API not running — re-run `run_all.ps1` |
| Login returns 503 | MySQL not reachable — start MySQL (XAMPP) / check `.env` |
| Portal page blank | `npm install` in `login_portal\frontend`, then re-run the launcher |
| Dashboard blank inside the portal | Streamlit not up — check http://localhost:8501 |
| **Streamlit never starts** (8501 never listens, MySQL/API/portal fine) | The project folder was moved after the venv was built: `.venv\Scripts\streamlit.exe` and `pip.exe` embed their creation path and fail silently. `run_all.ps1` now starts Streamlit as `python -m streamlit`; if you call a shim by hand, use `python.exe -m streamlit` / `python.exe -m pip` instead. To repair the shims for good, recreate the venv in place: `python -m venv .venv` then `python.exe -m pip install -r requirements.txt` |
| Launcher says *"Vite dev server did not come up"* although the portal opens | Fixed in `run_all.ps1` — `Test-Port` now checks IPv4 **and** IPv6 (Vite binds `::1` here) |
| Port already in use | `.\stop_all.ps1` then re-run `run_all.ps1` |
| Sidebar widgets cut off / can't scroll | Do **not** set `overflow-y: hidden` on the sidebar (see UNIT_GUIDE.md §4.1) |
| Changes not visible | Press `C` in the browser (clear cache) or restart the launcher |
