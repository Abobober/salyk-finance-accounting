# Run dev: superuser, demo data, backend, bot, frontend
# Usage: .\scripts\run_dev.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot | Split-Path -Parent

Set-Location $ProjectRoot

$venvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$Python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$venvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "Using venv" -ForegroundColor Cyan
    & $venvActivate
}

Write-Host "`n=== Init ===" -ForegroundColor Green

Write-Host "Migrations..." -ForegroundColor Cyan
Set-Location (Join-Path $ProjectRoot "backend")
& $Python manage.py migrate --noinput

Write-Host "Superuser..." -ForegroundColor Cyan
& $Python manage.py ensure_superuser

Write-Host "`nActivity codes..." -ForegroundColor Cyan
& $Python manage.py import_activities_code

Write-Host "`nDemo data..." -ForegroundColor Cyan
& $Python manage.py setup_demo_data --user admin@gmail.com --skip-if-populated

Set-Location $ProjectRoot

Write-Host "`n=== Starting services ===" -ForegroundColor Green

$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"

Write-Host "Backend (http://127.0.0.1:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BackendPath'; & '$Python' manage.py runserver"

Write-Host "Telegram bot..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$Python' '$(Join-Path $ProjectRoot 'tg_bot\run_bot.py')'"

Write-Host "Frontend (http://localhost:3000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendPath'; npm run dev"

Write-Host "`nDone. 3 windows: backend, bot, frontend." -ForegroundColor Green
Write-Host 'Login: admin@gmail.com / admin' -ForegroundColor Yellow
