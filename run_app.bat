@echo off
echo ==========================================
echo      NEXUS-AI: ONE-CLICK SETUP
echo ==========================================
echo.
echo [1/3] Stopping old containers...
docker-compose down

echo.
echo [2/3] Building and Starting Application...
echo       (This may take a few minutes on first run)
docker-compose up --build -d

echo.
echo [3/3] Application Started!
echo       Backend: http://localhost:8000/docs
echo       Frontend: http://localhost:3000
echo.
echo Opening Dashboard in Browser...
timeout /t 5
start http://localhost:3000

echo.
echo Logs are streaming below (Press Ctrl+C to exit logs, App will keep running):
docker-compose logs -f
pause
