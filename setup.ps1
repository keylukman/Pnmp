# PNMP Setup Script untuk Windows 11
# Jalankan dengan: .\setup.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PNMP - PSSN Network Management Platform" -ForegroundColor Cyan
Write-Host "  Setup Script untuk Windows 11" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cek Node.js
Write-Host "[1/4] Mengecek Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js $nodeVersion ditemukan" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js tidak ditemukan!" -ForegroundColor Red
    Write-Host "  Download dari: https://nodejs.org" -ForegroundColor Yellow
    Write-Host "  Install Node.js LTS (v18 atau lebih baru)" -ForegroundColor Yellow
    exit 1
}

# Cek npm
Write-Host "[2/4] Mengecek npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "  ✓ npm v$npmVersion ditemukan" -ForegroundColor Green
} catch {
    Write-Host "  ✗ npm tidak ditemukan!" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "[3/4] Menginstall dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Gagal menginstall dependencies!" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Dependencies berhasil diinstall" -ForegroundColor Green

# Build
Write-Host "[4/4] Building application..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Gagal build application!" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Build berhasil" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup selesai!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Untuk menjalankan aplikasi:" -ForegroundColor Cyan
Write-Host "  Development: npm run dev" -ForegroundColor White
Write-Host "  Production:  npx serve dist" -ForegroundColor White
Write-Host ""
Write-Host "Akses di browser:" -ForegroundColor Cyan
Write-Host "  http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Login:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host ""
