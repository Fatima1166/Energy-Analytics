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
│   ├── supply_forecast.py        # Q5 supply history, technology mix, adequacy, backtest
│   ├── targets.py                # Q3 benchmarks (dim_target + policy override)
│   ├── styles.py                 # global CSS
│   └── components.py / icons.py  # UI building blocks (cards, footer)
├── dashboards/
│   ├── registry.py               # dashboard list + each one's unit domains
│   ├── q2_renewable_scenarios/   # Q2: page, charts, config, README.md
│   ├── q3_target_bottlenecks/    # Q3: page, charts, README.md
│   ├── q4_forecast_demand/       # Q4: page, charts, README.md
│   ├── q5_forecast_supply/       # Q5: page, charts, README.md
│   ├── q6_supply_chain_optimization/ # Q6: page, charts, config, README.md
│   └── q7_forecast_cost/         # Q7: page, charts, config, README.md
├── scripts/
│   ├── verify_demand_forecast.py # Q4 numbers, printed from live MySQL
│   ├── verify_supply_forecast.py # Q5 numbers, printed from live MySQL
│   ├── verify_q7_cost.py         # Q7 numbers + sanity checks, from live MySQL
│   ├── audit_axes.py             # prints every Q4/Q5/Q6/Q7 axis title
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
└── energy_database_new (1).sql # MySQL schema + seed data (current dump, FY1999-2000..FY2025-26)
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
SOURCE "path/to/energy_database_new (1).sql";
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
| Renewable Share | How much of the power is renewable in the range's final year, for the chosen scenario |
| Renewable Power Built | Clean plant capacity the scenario has to build |
| CO₂ Avoided | Total emissions the scenario keeps out of the air ("million tonnes of CO₂", auto-scaled) |
| Gas Import Savings | Money not spent importing gas ("million USD") |
| Visuals 1–4 | Renewable share over time, where the power comes from, results (one year at a time or all five scenarios), power plants built by source |
| Slicers | Pick a scenario, Years to show, Unit Selection |

Full details: [`dashboards/q2_renewable_scenarios/README.md`](dashboards/q2_renewable_scenarios/README.md)

### Q3 — Target Bottlenecks

*What are the bottlenecks in achieving planned targets?*

| KPI / Visual | What it shows |
|---|---|
| K1 Losses % | Energy losses against the 28.23% benchmark |
| K2 Import Dependence % | Imported share of primary supply |
| K3 Renewable Share % | Against the 30% ARE Policy target |
| K4 Gas Self-Sufficiency % | Domestic production vs consumption |
| Visuals 1–4 | Where the energy is lost, energy we import, gas made vs gas used, distance to each target |
| Slicers | Years to show, Unit Selection |

Full details: [`dashboards/q3_target_bottlenecks/README.md`](dashboards/q3_target_bottlenecks/README.md)

### Q4 — Forecasted Energy Demand (1999–2035)

*What is forecasted energy demand?*

| KPI / Visual | What it shows |
|---|---|
| K1 Total Demand | Total energy demand now and at the horizon, per scenario |
| K2 Electricity Demand | Grid demand, now and at the horizon, with its yearly growth |
| K3 Demand Growth | Forecast growth a year against the growth the data shows |
| Visuals 1–5 | Demand so far, the three paths to the horizon, what moves demand, who uses the electricity, how far to trust the forecast |
| Slicers | Scenarios to show, Forecast up to, Unit Selection |

Three cards and five charts, all of them part of the answer to "what will demand
be?": where demand has been (1), the scenarios (2), the drivers (3), the sectors
(4) and the accuracy test (5). Supply-side content — gap and import dependency —
lives on Q5.

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_demand_forecast.py
```

Full details: [`dashboards/q4_forecast_demand/README.md`](dashboards/q4_forecast_demand/README.md)

### Q5 — Forecasted Energy Supply (1999–2035)

*What is forecasted energy supply?*

| KPI / Visual | What it shows |
|---|---|
| K1 Total primary energy supply | Measured for the year the card names (2024: 75.7 MTOE) and the level at 2035 under the chosen scenario (Base ~93.2 MTOE), with the % change |
| K2 Electricity generation | Measured for the year the card names (2024: 154,480 GWh) and 2035 (Base ~385,837 GWh), with the yearly growth rate |
| K3 Does supply cover demand | How far supply sits above or below demand at the horizon, against the comfortable 15%–25% band |
| Visuals 1–6 | Supply so far, the three paths to the horizon, what the electricity is made of, supply against demand, made at home vs bought abroad, and the accuracy test |
| Slicers | Scenarios to show, Forecast up to, Unit Selection |

Three cards and six charts, all of them part of the answer to "what will supply
be?". Installed capacity (MW) is left off on purpose — a build plan is not a
supply — and the demand the supply is measured against is Q4's subject.

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_supply_forecast.py
```

Full details: [`dashboards/q5_forecast_supply/README.md`](dashboards/q5_forecast_supply/README.md)

### Q6 — Supply Chain Optimization (2002–2024)

*What is the optimal utilization of fuel and renewable energy supply chains?*

| KPI / Visual | What it shows |
|---|---|
| K1 How well the chains are used | The overall score out of 100, which part the chosen strategy counts hardest, and how many of the four parts it was built from |
| K2 Electricity that reached people | The share that arrived (82.1% in 2019), the loss behind it and how much of the loss aim was reached |
| K3 Clean plant made vs what it could make | The share of its year-round potential the clean plant actually made (41.2% in 2024) |
| Visuals 1–5 | The score and its four parts year by year, electricity lost on the wires, clean plant built and what it made, the gas chain, and what is made now against the target mix |
| Slicers | Which part counts most, Years to judge, Unit Selection (Electricity, Power, Gas) |

Three cards and five charts: the score and the gas chain share a row, the two
electricity charts share the next, and the mix spans the page. The score has four
parts, not five: the old "fuel waste" part was computed from the same
transmission-loss column as the grid part.
Where supply comes from is Q5's page and what imported gas costs is Q7's, so the
import and gas numbers count inside the score but get no charts here.

Check every axis title from the command line:

```powershell
.venv\Scripts\python.exe scripts\audit_axes.py
```

Full details: [`dashboards/q6_supply_chain_optimization/README.md`](dashboards/q6_supply_chain_optimization/README.md)

### Q7 — Forecasted Producer Cost (2000–2035)

*What is the forecasted cost of energy power producers?*

| KPI / Visual | What it shows |
|---|---|
| K1 What buying electricity cost | The 2024 bill (8.21 USD bn) at an average 53.1 US$ per unit over 154,480 GWh, with the fuel part of it |
| K2 The bill it points to | The bill at the year asked for under the chosen build-out case (24.01 USD bn at 2035, planned), its growth per year and the gap on 2024 |
| K3 What one unit costs | The price of one unit at the same year (62.2 US$), up 9.1 from 2024, with the clean share of the mix behind it |
| Visuals 1–5 | What each source was paid and what a unit cost, the bill's path per build-out case, a step-by-step walk of where the extra money goes, the price of one unit, and the fuel-price band beside the model's own average error |
| Slicers | Build-out cases to show, Forecast up to, Unit Selection (Cost) |

Three cards and five charts. What a cleaner pathway would *save* is Q8's answer,
so the avoided-cost card and chart are gone; the purchase-tariff heat-map only
restated the prices that were fed into the model, and the hold-out table repeated
the two bars in Visual 5. The bill is worked out from reported generation at
stated purchase prices — the warehouse holds no producer invoices — and the fuel
assumption moves the 2035 answer (21.1–27.6 USD bn) about three and a half times
as much as the choice of build-out case does (23.1–24.9).

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_q7_cost.py
```

Full details: [`dashboards/q7_forecast_cost/README.md`](dashboards/q7_forecast_cost/README.md)


### Q8 — Sustainable Strategy (1999–2035)

*What optimal strategy may be opted to make energy development sustainable?*

| KPI / Visual | What it shows |
|---|---|
| K1 Where things stand | The latest score out of 100 (71.9) — the year it names (2018) is the latest one all four pillars reported — with each pillar's own year on the rows |
| K2 What the plan reaches | 94.1 by 2035 under the funded package, against 82.0 if nothing changes — worth +12.1 — with 8 of 13 measures paid for |
| K3 What the plan costs a year | 7.90 USD bn a year of the 8.0 asked for, 0.10 left over, 5 measures put off |
| Visuals 1–4 | Each pillar's latest score against ten years earlier, with the year it came from and how many measures back it; all thirteen options ranked by points per $bn, paid-for against put-off; the three paths to the horizon; and what the package adds pillar by pillar |
| Slicers | What counts most (five presets), Money a year for new measures, Plan up to, Unit Selection (Cost) |

Three cards and four charts in two rows of two, then the funded list. Gone: the
index trajectory, the cost-impact bubble map and the component diagnostics — each
redrew a number another
visual already carries — plus the fourth card, the thirteen-row ledger, four weight
sliders and an evaluation-year slider that only moved the baseline onto thinner
evidence.

The headline changed when four engine defects were fixed first: a year with no
imports reported was read as *zero* imports and scored perfect security; national
CO₂ was divided by electricity-only generation, so every year scored nought on a
scope error; the composite renormalised over whatever pillars existed, so the index
rose as coverage decayed (2024 showed two pillars and scored 84); and the
projection started from a different 2024 number than the card showed (62.5 against
69.4). The score is now 70.7 on the page and on the chart.

Reproduce every figure from the command line:

```powershell
.venv\Scripts\python.exe scripts\verify_q8_strategy.py
```

Full details: [`dashboards/q8_sustainable_strategy/README.md`](dashboards/q8_sustainable_strategy/README.md)


### Missing years & the projection window

A year inside the reported window (up to **2024**) that the database did not
report prints **blank** — never a zero, never carried over from another year,
never interpolated. A stored `0` is a real reading; only a missing or NULL value
blanks.

A card's year label belongs to its value, not to a slider: when a metric has no
reading for 2024, the card names the latest year its value really came from, or
says *"no reading"* when there is none at all. "2024" is never printed above a
number that came from 2018.

Nothing inside the reported window is projected. What the dashboards model
starts at **2025** and is tagged `Projected` in the data layer (drawn dashed).
`scripts/verify_missing_year_blanks.py` greps the engines and charts for
`fillna` / `ffill` / `interpolate` and checks that boundary, so a bridge cannot
creep back in.

### Units

Every KPI and chart re-renders in the unit chosen in the sidebar. Q2 offers
Electricity, Power and Emission; Q3 offers Energy and Gas; Q4 offers Energy and
Electricity; Q5 offers Energy and Electricity; Q6 offers Electricity, Power and
Gas; Q7 offers Cost; Q8 offers Cost (the index itself is unitless). The sidebar shows only
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
