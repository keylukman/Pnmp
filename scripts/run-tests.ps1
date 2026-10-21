# PNMP - Run backend test suite (hardware-independent, uses mocks/SQLite fixtures)
# Usage: .\scripts\run-tests.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
$py = ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }
& $py -m pytest tests/ -v
exit $LASTEXITCODE
