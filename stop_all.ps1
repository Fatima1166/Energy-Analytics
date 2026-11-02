<#
    stop_all.ps1 -- stop the Energy Analytics services.

        .\stop_all.ps1                 stop the dashboard
        .\stop_all.ps1 -WithMySQL      also stop MySQL
#>
[CmdletBinding()]
param([switch]$WithMySQL)

function Stop-Port([int]$Port, [string]$Name) {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        Write-Host ("  {0,-16} not running (port {1})" -f $Name, $Port) -ForegroundColor DarkGray
        return
    }
    foreach ($l in $listeners) {
        $proc = Get-Process -Id $l.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host ("  {0,-16} stopping {1} (PID {2})" -f $Name, $proc.ProcessName, $proc.Id) -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "  Stopping Energy Analytics" -ForegroundColor Cyan
Stop-Port 8501 'Streamlit'

if ($WithMySQL) { Stop-Port 3306 'MySQL' }
Write-Host "  done" -ForegroundColor Green
Write-Host ""
