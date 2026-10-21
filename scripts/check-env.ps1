# PNMP - Environment verification (Windows 11 native, no Docker/WSL)
# Usage: .\scripts\check-env.ps1   (run from F:\pnmp)
$ErrorActionPreference = "Continue"
Write-Host "=== PNMP environment check ===" -ForegroundColor Cyan
$ok = $true

foreach ($t in @(
    @{n="Node.js";   c={ node --version }},
    @{n="npm";       c={ npm --version }},
    @{n="Python";    c={ python --version 2>&1 }},
    @{n="git";       c={ git --version }}
)) {
    try {
        $v = & $t.c
        Write-Host ("[OK]   {0}: {1}" -f $t.n, $v) -ForegroundColor Green
    } catch {
        Write-Host ("[MISS] {0} not found on PATH" -f $t.n) -ForegroundColor Red
        $ok = $false
    }
}

# Python version must be >= 3.10 (project targets 3.12+)
try {
    $pyver = python -c "import sys; print('%d.%d' % sys.version_info[:2])"
    $major,$minor = $pyver.Split(".")
    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
        Write-Host "[WARN] Python $pyver is older than 3.10 - upgrade recommended (project targets 3.12+)" -ForegroundColor Yellow
    }
} catch {}

# PostgreSQL service (Windows service name varies by install; check common patterns)
$pgsvc = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgsvc) {
    if ($pgsvc.Status -eq "Running") {
        Write-Host ("[OK]   PostgreSQL service running: {0}" -f $pgsvc.Name) -ForegroundColor Green
    } else {
        Write-Host ("[WARN] PostgreSQL service '{0}' exists but is {1}. Start it with: Start-Service '{0}' (may require admin)" -f $pgsvc.Name, $pgsvc.Status) -ForegroundColor Yellow
    }
} else {
    Write-Host "[MISS] No PostgreSQL Windows service found. Install PostgreSQL 16+ (https://www.postgresql.org/download/windows/) and re-run." -ForegroundColor Red
    $ok = $false
}

# Project files
foreach ($f in @("backend\requirements.txt","backend\app\main.py","package.json","src\main.tsx","backend\.env.example")) {
    if (Test-Path $f) { Write-Host ("[OK]   {0}" -f $f) -ForegroundColor Green }
    else { Write-Host ("[MISS] {0}" -f $f) -ForegroundColor Red; $ok = $false }
}

if ($ok) { Write-Host "`nEnvironment looks good. Next: .\scripts\setup-backend.ps1" -ForegroundColor Green }
else     { Write-Host "`nFix the items above before continuing." -ForegroundColor Red }
exit 0
