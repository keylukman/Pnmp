# PNMP - Recover Alembic version pointer without touching application data.
#
# Use when:  alembic upgrade head  fails with
#   "Can't locate revision identified by '<some-hash>'"
# meaning the alembic_version table in your database contains a revision id
# that no longer exists in backend\alembic\versions (created by an older or
# divergent copy of the project).
#
# This script ONLY rewrites the single-row alembic_version bookkeeping table.
# It never drops, recreates, or modifies any application table or row.
#
# Usage (from repo root):
#   .\scripts\fix-alembic-version.ps1                     # read current pointer + list valid revisions
#   .\scripts\fix-alembic-version.ps1 -Repair             # stamp DB to repo head (uses alembic stamp --purge)
#   .\scripts\fix-alembic-version.ps1 -Repair -Revision 20261012_0002   # stamp to a specific known-good rev
#
param(
    [switch]$Repair,
    [string]$Revision
)
$ErrorActionPreference = "Stop"

$backend = Join-Path $PSScriptRoot "..\backend"
$envFile = Join-Path $backend ".env"
if (-not (Test-Path $envFile)) { Write-Host "backend\.env not found - run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }

# Read DATABASE_URL from backend\.env (no secrets printed)
$dbUrl = (Get-Content $envFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1) -replace '^DATABASE_URL=', '' -replace '"', ''
if (-not $dbUrl) { Write-Host "DATABASE_URL missing in backend\.env" -ForegroundColor Red; exit 1 }
$dbName = ($dbUrl -split '/')[-1]
Write-Host "Target database: $dbName (credentials loaded from backend\.env)" -ForegroundColor Cyan

# Locate psql.exe from the installed PostgreSQL Windows service binary path
$svc = Get-CimInstance Win32_Service -Filter "Name LIKE 'postgresql%'" | Select-Object -First 1
if (-not $svc) { Write-Host "PostgreSQL Windows service not found. Is it installed and running?" -ForegroundColor Red; exit 1 }
$pgBin = Split-Path (($svc.PathName -split '"')[1]) -Parent
$psql = Join-Path $pgBin "psql.exe"
if (-not (Test-Path $psql)) { Write-Host "psql.exe not found at $psql" -ForegroundColor Red; exit 1 }

# Extract user/password/host/port from URL like postgresql+psycopg://user:pass@host:port/db
if ($dbUrl -match '://([^:@]+)(?::([^@]*))?@([^:/]+):?(\d*)') {
    $user = $Matches[1]; $pass = $Matches[2]; $hostp = $Matches[3]; $port = if ($Matches[4]) { $Matches[4] } else { "5432" }
} else { Write-Host "Could not parse DATABASE_URL" -ForegroundColor Red; exit 1 }

$py = Join-Path $backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "backend\.venv missing - run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }

Push-Location $backend
try {
    # Valid revisions in THIS repo (revision ids only, e.g. 20261022_0003)
    $validRevs = & $py -m alembic heads | ForEach-Object { ($_ -split ' ')[0] }
    $headRev = $validRevs | Select-Object -Last 1

    if (-not $Repair) {
        $cur = & $psql -h $hostp -p $port -U $user -d $dbName -tA -c "SELECT version_num FROM alembic_version;" 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host "Cannot connect to $dbName via psql - check DATABASE_URL / pg_hba.conf." -ForegroundColor Red; exit 1 }
        Write-Host "Current alembic_version value : '$cur'" -ForegroundColor Yellow
        Write-Host "Repo head revision          : '$headRev'" -ForegroundColor Cyan
        Write-Host "Repo revisions available:" -ForegroundColor Cyan
        & $py -m alembic history | ForEach-Object { Write-Host ("  " + $_) }
        Write-Host ""
        Write-Host "To repair the pointer (bookkeeping table ONLY, no data changes):" -ForegroundColor Green
        Write-Host "  .\scripts\fix-alembic-version.ps1 -Repair" -ForegroundColor White
        return
    }

    $target = if ($Revision) { $Revision } else { $headRev }
    if ($validRevs -notcontains $target) {
        Write-Host "Revision '$target' does not exist in backend\alembic\versions - refusing." -ForegroundColor Red
        exit 1
    }

    Write-Host "Stamping alembic_version -> $target (UPDATE/DELETE on the one-row bookkeeping table only)..." -ForegroundColor Cyan
    & $py -m alembic stamp --purge $target
    if ($LASTEXITCODE -ne 0) { Write-Host "stamp failed - inspect output above." -ForegroundColor Red; exit 1 }

    Write-Host "Verifying..." -ForegroundColor Cyan
    & $py -m alembic current
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK. Now run:  .\scripts\migrate.ps1" -ForegroundColor Green
    } else {
        Write-Host "alembic current still failing - report the output; do NOT drop/recreate the database." -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}
