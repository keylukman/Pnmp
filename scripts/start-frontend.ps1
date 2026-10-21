# PNMP - Start frontend dev server (Vite). Run in a SECOND terminal while backend runs.
# Usage: .\scripts\start-frontend.ps1
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."
if (-not (Test-Path "node_modules")) { Write-Host "Running npm install first..." -ForegroundColor Yellow; npm install }
Write-Host "Starting Vite dev server at http://localhost:3000 (Ctrl+C to stop)" -ForegroundColor Cyan
npm run dev
