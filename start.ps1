# NEXUS-AI Startup Script
# Starts backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEXUS-AI - Starting System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# Detect Venv
$venvDir = ""
if (Test-Path "backend\venv") { 
    $venvDir = "venv" 
} elseif (Test-Path "backend\.venv") { 
    $venvDir = ".venv" 
} else {
    Write-Host "❌ Virtual environment not found. Run setup first:" -ForegroundColor Red
    Write-Host "   .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Check frontend
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "❌ Frontend dependencies not found. Run setup first:" -ForegroundColor Red
    Write-Host "   .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] Starting Backend (FastAPI)..." -ForegroundColor Yellow
Write-Host "  Location: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start Backend
$backendCmd = "& '$PSScriptRoot\backend\$venvDir\Scripts\Activate.ps1'; cd '$PSScriptRoot\backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend_debug.log 2>&1"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "$backendCmd"

# Wait a moment
Start-Sleep -Seconds 5
Write-Host "  Backend process launched." -ForegroundColor Green
Write-Host ""

Write-Host "[2/2] Starting Frontend (Next.js)..." -ForegroundColor Yellow
Write-Host "  Location: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""

# Start Frontend
$frontendCmd = "cd '$PSScriptRoot\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "$frontendCmd"

Write-Host "  Frontend process launched." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ System Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Press Ctrl+C in the popup windows to stop servers." -ForegroundColor Yellow
Write-Host ""
