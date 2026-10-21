# PNMP - Backend venv + dependency setup (native Windows)
# Usage: .\scripts\setup-backend.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
Push-Location backend

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
}
$py = ".venv\Scripts\python.exe"

Write-Host "Installing pinned dependencies..." -ForegroundColor Cyan
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "Dependency installation FAILED." -ForegroundColor Red; Pop-Location; exit 1 }

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend\.env from .env.example - EDIT IT before first run:" -ForegroundColor Yellow
    Write-Host "  DATABASE_URL, JWT_SECRET_KEY, APP_SECRET_KEY, PNMP_ENCRYPTION_KEY" -ForegroundColor Yellow
    Write-Host "  Generate a JWT/secret value, e.g.: & $py -c \"import secrets; print(secrets.token_urlsafe(48))\"" -ForegroundColor Yellow
    Write-Host "  Generate the encryption key:      & $py -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"" -ForegroundColor Yellow
} else {
    Write-Host "backend\.env already exists - left untouched." -ForegroundColor Green
}

Write-Host "Import sanity check..." -ForegroundColor Cyan
& $py -c "from app.main import app; print('Backend imports OK:', app.title)"
Pop-Location
Write-Host "Backend setup complete. Next: .\scripts\check-db.ps1" -ForegroundColor Green
