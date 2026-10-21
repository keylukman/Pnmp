# PNMP - Apply Alembic migrations (schema changes ONLY via Alembic; never drops data)
# Usage: .\scripts\migrate.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
$py = ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }

Write-Host "Current revision:" -ForegroundColor Cyan
& $py -m alembic current
Write-Host "Upgrading to head..." -ForegroundColor Cyan
& $py -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Write-Host "Migration FAILED - do NOT drop/recreate the database. Inspect output above." -ForegroundColor Red; exit 1 }
Write-Host "Migrations applied. History:" -ForegroundColor Green
& $py -m alembic history --verbose | Select-Object -Last 10
