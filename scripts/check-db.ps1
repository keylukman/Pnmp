# PNMP - Verify PostgreSQL connectivity using backend/.env DATABASE_URL
# Usage: .\scripts\check-db.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\..\backend"
$py = ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run .\scripts\setup-backend.ps1 first." -ForegroundColor Red; exit 1 }

& $py -c @"
from app.core.config import settings
from sqlalchemy import create_engine, text
try:
    eng = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with eng.connect() as c:
        v = c.execute(text('SELECT version()')).scalar()
    print('[OK] Connected to database for URL:', settings.DATABASE_URL.split('@')[-1])
    print('[OK] Server says:', v.split(',')[0])
except Exception as e:
    print('[FAIL] Cannot connect:', type(e).__name__)
    print('  Check: PostgreSQL service running, database/role created, password correct in backend\\.env')
    print('  Create DB/role via psql (as postgres superuser):')
    print("    CREATE DATABASE pnmp; CREATE USER pnmp WITH PASSWORD 'password'; GRANT ALL PRIVILEGES ON DATABASE pnmp TO pnmp;")
    raise SystemExit(1)
"@
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Next: .\scripts\migrate.ps1" -ForegroundColor Green
