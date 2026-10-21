# PNMP - Start backend dev server (single instance guard: refuses to start if port 8000 is busy)
# Usage: .\scripts\start-backend.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
$py = ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }

$busy = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    Write-Host ("Port 8000 already in use (PID {0}). Avoid running multiple backend copies - stop the existing one first." -f ($busy.OwningProcess | Select-Object -First 1)) -ForegroundColor Red
    exit 1
}
Write-Host "Starting uvicorn on http://127.0.0.1:8000 (Ctrl+C = graceful shutdown incl. monitoring scheduler)" -ForegroundColor Cyan
& $py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
