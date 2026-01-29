@echo off
echo [NEXUS-AI] Starting Backend Server...
cd /d "%~dp0"
cd BACKEND

:: Set Python Path to current directory to avoid import errors
set PYTHONPATH=%CD%

echo [INFO] PYTHONPATH set to %PYTHONPATH%
echo [INFO] Launching Uvicorn...

python app/main.py

pause
