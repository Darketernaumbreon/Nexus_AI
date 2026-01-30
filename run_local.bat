@echo off
echo ==========================================
echo      NEXUS-AI: HYBRID LOCAL LAUNCHER
echo      (Bypassing Docker Build Issues)
echo ==========================================

:: Set Environment Variables for Local Execution
set POSTGRES_SERVER=localhost
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=password
set POSTGRES_DB=nexus_ai
set POSTGRES_PORT=5435

echo.
echo [1/4] Starting Database & Redis (Docker)...
docker-compose up -d db redis

echo.
echo [2/4] Waiting for Database...
timeout /t 5

echo.
echo [2.2/4] Installing Python Dependencies...
cd BACKEND
pip install -r requirements.txt
python force_refresh_data.py
cd ..

echo.
echo [3/4] Starting Backend Server...
start "Nexus Backend" cmd /k "cd BACKEND && echo Starting Backend... && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [4/4] Starting Frontend Server...
echo       (Installing dependencies & starting...)
start "Nexus Frontend" cmd /k "cd Frontend && npm install && npm start"

echo.
echo ==========================================
echo    ALL SYSTEMS GO
echo ==========================================
echo.
echo Dashboard: http://localhost:3000
echo Backend:   http://localhost:8000/docs
echo.
echo Note: If a window closes with an error, check that window.
echo.
timeout /t 5
start http://localhost:3000
pause
