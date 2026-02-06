# NEXUS-AI Setup Script
# Installs all dependencies for first-time setup

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEXUS-AI - System Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

# Check prerequisites
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

# Check Python (3.11+)
try {
    $pythonVersion = python --version 2>&1 | Out-String
    $pythonVersion = $pythonVersion.Trim()
    if ($pythonVersion -match "Python 3\.([0-9]+)") {
        $minorVersion = [int]$Matches[1]
        if ($minorVersion -lt 11) {
            Write-Host "  [X] Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "  [OK] Python: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  [X] Python not found. Install from python.org" -ForegroundColor Red
    exit 1
}

# Check Node.js (18+)
try {
    $nodeVersion = node --version 2>&1 | Out-String
    $nodeVersion = $nodeVersion.Trim()
    if ($nodeVersion -match "v([0-9]+)\.") {
        $majorVersion = [int]$Matches[1]
        if ($majorVersion -lt 18) {
            Write-Host "  [X] Node.js 18+ required. Found: $nodeVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "  [OK] Node.js: $nodeVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "  [X] Node.js not found. Install from nodejs.org" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Backend Setup
Write-Host "[2/7] Setting up backend..." -ForegroundColor Yellow
if (-not (Test-Path "backend")) {
    Write-Host "[X] Backend directory not found!" -ForegroundColor Red
    exit 1
}
Push-Location "backend"

# Detect or Create Venv
$venvDir = ".venv"
if (Test-Path "venv") { 
    $venvDir = "venv"
    Write-Host "  [OK] Found existing venv in 'venv'" -ForegroundColor Green
} elseif (Test-Path ".venv") {
    Write-Host "  [OK] Found existing venv in '.venv'" -ForegroundColor Green
} else {
    Write-Host "  Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
    $venvDir = ".venv"
}

# Activate virtual environment checks
$activateScript = ".\$venvDir\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
     Write-Host "  [X] Activation script not found at $activateScript" -ForegroundColor Red
     Pop-Location
     exit 1
}

# Install dependencies via PIP (using the venv python directly)
Write-Host "  Installing Python dependencies..." -ForegroundColor Cyan
& ".\$venvDir\Scripts\python.exe" -m pip install --upgrade pip
& ".\$venvDir\Scripts\python.exe" -m pip install -r requirements.txt

# Explicitly ensure openrouteservice is installed (sometimes missed)
Write-Host "  Verifying openrouteservice..." -ForegroundColor Cyan
& ".\$venvDir\Scripts\python.exe" -m pip install openrouteservice==2.3.3

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  [X] Backend installation failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host ""

# Frontend Setup
Write-Host "[3/7] Setting up frontend..." -ForegroundColor Yellow
Push-Location "frontend"

Write-Host "  Installing Node.js dependencies..." -ForegroundColor Cyan
# Use cmd /c to ensure npm runs correctly on Windows
cmd /c "npm install"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  [X] Frontend installation failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host ""

# Environment Configuration
Write-Host "[4/7] Configuring environment..." -ForegroundColor Yellow

# Backend .env content
$backendEnvContent = @(
    "# Database",
    "POSTGRES_SERVER=localhost",
    "POSTGRES_USER=postgres",
    "POSTGRES_PASSWORD=postgres",
    "POSTGRES_DB=nexus_ai",
    "",
    "# API Keys (REQUIRED)",
    "OPENTOPOGRAPHY_API_KEY=6edea2848557220e2ffeae77ff336885",
    "OPENROUTE_API_KEY=eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjkxMDM5N2M0ZjM1ODQxMWJhMDIyYzAyOTFiZDhkMzU2IiwiaCI6Im11cm11cjY0In0=",
    "",
    "# Redis",
    "REDIS_HOST=localhost",
    "REDIS_PORT=6379",
    "",
    "# Paths",
    "ML_ARTIFACTS_DIR=ml_engine/artifacts",
    "WEATHER_CACHE_DIR=data/weather_cache",
    "DEM_CACHE_DIR=data/dem_cache"
)

if (-not (Test-Path "backend\.env")) {
    Write-Host "  Creating backend/.env file..." -ForegroundColor Cyan
    $backendEnvContent | Out-File -FilePath "backend\.env" -Encoding UTF8
    Write-Host "  [OK] Created backend/.env" -ForegroundColor Green
} else {
    Write-Host "  [i] backend/.env already exists (skipping)" -ForegroundColor Cyan
}

# Frontend .env.local content
$frontendEnvContent = @(
    "# Backend API",
    "NEXT_PUBLIC_API_BASE=/api/proxy",
    "BACKEND_URL=http://localhost:8000",
    "",
    "# Mapbox",
    "NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here",
    "",
    "# Demo Mode",
    "NEXT_PUBLIC_DEMO_MODE=false"
)

if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "  Creating frontend/.env.local file..." -ForegroundColor Cyan
    $frontendEnvContent | Out-File -FilePath "frontend\.env.local" -Encoding UTF8
    Write-Host "  [OK] Created frontend/.env.local" -ForegroundColor Green
    Write-Host "  [!] IMPORTANT: Add your Mapbox token to frontend/.env.local" -ForegroundColor Yellow
} else {
    Write-Host "  [i] frontend/.env.local already exists (skipping)" -ForegroundColor Cyan
}

Write-Host ""

# Create data directories
Write-Host "[5/7] Creating data directories..." -ForegroundColor Yellow
$dataDirs = @(
    "backend\data\weather_cache",
    "backend\data\dem_cache",
    "backend\data\conditioned_cache",
    "backend\data\ground_truth_cache",
    "backend\data\ml_training",
    "backend\ml_engine\artifacts"
)

foreach ($dir in $dataDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "  [OK] Data directories created" -ForegroundColor Green
Write-Host ""

# Verification
Write-Host "[6/7] Verifying core libraries..." -ForegroundColor Yellow
$verifyCmd = "import openrouteservice; print('  [OK] OpenRouteService verified')"
try {
    & "backend\$venvDir\Scripts\python.exe" -c $verifyCmd
} catch {
    Write-Host "  [!] OpenRouteService check failed" -ForegroundColor Yellow
}
Write-Host ""

# Database Instructions
Write-Host "[7/7] Database setup instructions..." -ForegroundColor Yellow
Write-Host "  To set up PostgreSQL database:" -ForegroundColor Cyan
Write-Host "  1. Install PostgreSQL 15+ with PostGIS" -ForegroundColor Cyan
Write-Host "  2. Create database: CREATE DATABASE nexus_ai;" -ForegroundColor Cyan
Write-Host "  3. Create extension: CREATE EXTENSION postgis;" -ForegroundColor Cyan
Write-Host ""

# Final
Write-Host "========================================" -ForegroundColor Green
Write-Host "  [OK] Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the system:" -ForegroundColor Cyan
Write-Host "  .\start.ps1" -ForegroundColor Yellow
Write-Host ""
