# PNMP - Backend health check + graceful-stop hint
# Usage: .\scripts\health-check.ps1
param([string]$BaseUrl = "http://127.0.0.1:8000")
try {
    $h = Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 10
    Write-Host ("[OK] status={0} database={1} monitoring_worker={2} version={3}" -f $h.status, $h.database, $h.monitoring_worker, $h.version) -ForegroundColor Green
    if ($h.status -ne "healthy") { Write-Host "[WARN] Backend reports unhealthy - inspect output above." -ForegroundColor Yellow; exit 1 }
    exit 0
} catch {
    Write-Host "[FAIL] Backend not reachable at $BaseUrl - is .\scripts\start-backend.ps1 running?" -ForegroundColor Red
    exit 1
}
