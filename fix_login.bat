
@echo off
echo ==========================================
echo      NEXUS-AI: LOGIN FIXER
echo ==========================================
echo.
echo Setting environment variables...
set POSTGRES_SERVER=localhost
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=password
set POSTGRES_DB=nexus_ai
set POSTGRES_PORT=5435

echo.
echo Running Password Reset Script...
cd BACKEND
python reset_admin_password.py
cd ..

echo.
echo ==========================================
echo    DONE. TRY LOGGING IN NOW.
echo    Email: admin@nexus.ai
echo    Pass:  password123
echo ==========================================
pause
