<#
    run_all.ps1 -- start the whole Energy Analytics stack with ONE command.

        MySQL (XAMPP)   127.0.0.1:3306
        Flask API       127.0.0.1:5000   (bcrypt login endpoint)
        Streamlit       127.0.0.1:8501   (dashboard, embedded in the portal)
        React portal    127.0.0.1:5173   <-- open this one

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
$flask  = Join-Path $root 'login_portal\api_server.py'
$fe     = Join-Path $root 'login_portal\frontend'
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
Write-Host "  Energy Analytics - starting all services" -ForegroundColor Cyan
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

# 1) MySQL -------------------------------------------------------------------
if (Test-Port 3306) {
    Write-Host "  [1/4] MySQL          already running on 3306" -ForegroundColor Green
} else {
    Write-Host "  [1/4] MySQL          starting..." -ForegroundColor Yellow
    if (Test-Path $mysqld) {
        Start-Process -FilePath $mysqld -ArgumentList "--defaults-file=`"$myini`"" -WindowStyle Hidden
        if (Wait-Port 3306 45 'MySQL') { Write-Host "        ready" -ForegroundColor Green }
    } else {
        Write-Host "        mysqld not found - start MySQL from XAMPP Control Panel" -ForegroundColor Red
    }
}

# 2) Flask API ---------------------------------------------------------------
if (Test-Port 5000) {
    Write-Host "  [2/4] Flask API      already running on 5000" -ForegroundColor Green
} else {
    Write-Host "  [2/4] Flask API      starting..." -ForegroundColor Yellow
    Start-Process -FilePath $py -ArgumentList "`"$flask`"" -WorkingDirectory $root -WindowStyle Minimized
    if (Wait-Port 5000 40 'Flask API') { Write-Host "        ready" -ForegroundColor Green }
}

# 3) Streamlit dashboard -----------------------------------------------------
if (Test-Port 8501) {
    Write-Host "  [3/4] Streamlit      already running on 8501" -ForegroundColor Green
} else {
    Write-Host "  [3/4] Streamlit      starting..." -ForegroundColor Yellow
    if (-not (Test-Path $py)) {
        Write-Host "        .venv\Scripts\python.exe not found - create the venv first (README step 2)" -ForegroundColor Red
    } else {
        Start-Process -FilePath $st `
            -ArgumentList (@($stArgs) + @('run', 'app.py', '--server.port', '8501', '--server.headless', 'true')) `
            -WorkingDirectory $root -WindowStyle Minimized
        if (Wait-Port 8501 90 'Streamlit') { Write-Host "        ready" -ForegroundColor Green }
    }
}

# 4) React login portal ------------------------------------------------------
if (Test-Port 5173) {
    Write-Host "  [4/4] React portal   already running on 5173" -ForegroundColor Green
} else {
    Write-Host "  [4/4] React portal   starting (vite)..." -ForegroundColor Yellow
    $viteJs  = Join-Path $fe 'node_modules\vite\bin\vite.js'
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue

    if (-not (Test-Path (Join-Path $fe 'node_modules'))) {
        Write-Host "        node_modules missing - npm install (first time only, a few minutes)..." -ForegroundColor Yellow
        Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'npm install' -WorkingDirectory $fe -Wait -WindowStyle Minimized
    }

    if ((Test-Path $viteJs) -and $nodeCmd) {
        # run vite directly: the most reliable path, no npm wrapper involved
        Start-Process -FilePath $nodeCmd.Source `
            -ArgumentList "`"$viteJs`"", '--port', '5173', '--strictPort' `
            -WorkingDirectory $fe -WindowStyle Minimized
    } else {
        Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'npm run dev' -WorkingDirectory $fe -WindowStyle Minimized
    }
    if (Wait-Port 5173 120 'Vite dev server') { Write-Host "        ready" -ForegroundColor Green }
}

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   LOGIN PAGE   ->   http://localhost:5173" -ForegroundColor White
Write-Host "   Dashboard    ->   http://localhost:8501   (opens inside the portal)" -ForegroundColor DarkGray
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "   Stop everything with:  .\stop_all.ps1" -ForegroundColor DarkGray
Write-Host ""

if (-not $NoBrowser) { Start-Process 'http://localhost:5173' }
