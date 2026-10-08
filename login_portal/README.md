# Energy Analytics Login

React login frontend with a Flask API, MySQL authentication, and bcrypt password verification. The project does not use Streamlit.

## Requirements

- Python 3.10 or newer
- Node.js and npm
- MySQL running locally or on a reachable server

## Backend setup

Create and activate the Python environment, then install the dependencies:

```powershell
cd "D:\Fatima Projects\energy_analytics"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set database values before starting the API:

```powershell
$env:ENERGY_DB_HOST = "localhost"
$env:ENERGY_DB_PORT = "3306"
$env:ENERGY_DB_USER = "energy_user"
$env:ENERGY_DB_PASSWORD = "your-password"
$env:ENERGY_DB_NAME = "energy_analytics"
```

The API expects a MySQL database containing a `dim_users` table with these columns:

`user_id`, `username`, `password_hash`, `full_name`, and `role`.

## Start the backend

Open a PowerShell terminal in the project root:

```powershell
cd "D:\Fatima Projects\energy_analytics"
\.venv\Scripts\Activate.ps1
python api_server.py
```

The API runs at `http://localhost:5000`. Verify it with `http://localhost:5000/api/health`.

## Start the frontend

Open a second PowerShell terminal:

```powershell
cd "D:\Fatima Projects\energy_analytics\frontend"
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies frontend `/api` requests to the Flask API at `http://localhost:5000`.

## Build the frontend

```powershell
cd "D:\Fatima Projects\energy_analytics\frontend"
npm run build
```

## Create a test user

The helper creates or replaces the configured test user in `dim_users`:

```powershell
python generate_hash.py
```
