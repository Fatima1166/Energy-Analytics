<#
    run_all.ps1 -- start the Energy Analytics stack with ONE command.

        Streamlit       127.0.0.1:8501   <-- open this one (login page + dashboard)
        MySQL (XAMPP)   127.0.0.1:3306   (dev data backend; cloud uses energy.db)

    The React portal (:5173) and Flask API (:5000) are no longer started --
    LOGIN_MODE=streamlit in .env makes app.py show the login itself.

    Usage:
        powershell -ExecutionPolicy Bypass -File .\run_all.ps1
        powershell -ExecutionPolicy Bypass -File .\run_all.ps1 -NoBrowser
#>
[CmdletBinding()]
param([switch]$NoBrowser)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py     = Join-Path $root '.venv\Scripts\python.exe'
# Streamlit is started through the interpreter (`python -m streamlit`) instead of
# .venv\Scripts\streamlit.exe.  The console-script shims embed the path the venv
# was CREATED at, so they fail silently once the project folder is moved or
# renamed -- which is what happened here, and it left port 8501 dead while MySQL,
# Flask and Vite all came up fine.
$st     = $py
$stArgs = @('-m', 'streamlit')
$mysqld = 'D:\Fatima Programs\xampp\mysql\bin\mysqld.exe'
$myini  = 'D:\Fatima Programs\xampp\mysql\bin\my.ini'

function Test-Port([int]$Port) {
    # Vite binds IPv6 (::1) on this machine and Flask/Streamlit bind IPv4, so a
    # service counts as up when EITHER family answers.
    foreach ($addr in @('127.0.0.1', '::1')) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $c.Connect($addr, $Port); $c.Close(); return $true
        } catch { }
    }
    return $false
}

function Wait-Port([int]$Port, [int]$Seconds, [string]$Name) {
    $end = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $end) {
        if (Test-Port $Port) { return $true }
        Start-Sleep -Milliseconds 700
    }
    Write-Host "        !! $Name did not come up on port $Port" -ForegroundColor Red
    return $false
}

Write-Host ""
Write-Host "  Energy Analytics - starting services" -ForegroundColor Cyan
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

# 1) Streamlit dashboard (login gate built in) -------------------------------
if (Test-Port 8501) {
    Write-Host "  [1/2] Streamlit      already running on 8501" -ForegroundColor Green
    Write-Host "        NOTE: if it was started before the login change, stop it" -ForegroundColor Yellow
    Write-Host "        first with .\stop_all.ps1 so the new LOGIN_MODE loads." -ForegroundColor Yellow
} else {
    Write-Host "  [1/2] Streamlit      starting..." -ForegroundColor Yellow
    if (-not (Test-Path $py)) {
        Write-Host "        .venv\Scripts\python.exe not found - create the venv first (README step 2)" -ForegroundColor Red
    } else {
        Start-Process -FilePath $st `
            -ArgumentList (@($stArgs) + @('run', 'app.py', '--server.port', '8501', '--server.headless', 'true')) `
            -WorkingDirectory $root -WindowStyle Minimized
        if (Wait-Port 8501 90 'Streamlit') { Write-Host "        ready" -ForegroundColor Green }
    }
}

# 2) MySQL (optional dev backend; skipped if it is not installed) -------------
if (Test-Port 3306) {
    Write-Host "  [2/2] MySQL          already running on 3306" -ForegroundColor Green
} elseif (Test-Path $mysqld) {
    Write-Host "  [2/2] MySQL          starting..." -ForegroundColor Yellow
    Start-Process -FilePath $mysqld -ArgumentList "--defaults-file=`"$myini`"" -WindowStyle Hidden
    if (Wait-Port 3306 45 'MySQL') { Write-Host "        ready" -ForegroundColor Green }
} else {
    Write-Host "  [2/2] MySQL          not installed - app will use energy.db (SQLite)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   LOGIN + DASHBOARD  ->   http://localhost:8501" -ForegroundColor White
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   Stop everything with:  .\stop_all.ps1" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) { Start-Process 'http://localhost:8501' }
