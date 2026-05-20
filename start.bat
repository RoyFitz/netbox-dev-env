@echo off
REM Start NetBox development environment

echo Starting NetBox development environment...
docker compose up -d

echo.
echo Waiting for NetBox to be ready...
echo This may take a minute on first startup...

:wait_loop
timeout /t 5 /nobreak > nul
curl -sf http://localhost:8000/login/ > nul 2>&1
if errorlevel 1 (
    echo   Still waiting...
    goto wait_loop
)

echo.
echo ==========================================
echo NetBox is ready!
echo ==========================================
echo.
echo URL:      http://localhost:8000
echo Username: admin
echo Password: admin
echo API Token: 0123456789abcdef0123456789abcdef01234567
echo.
echo To import data:  import.bat
echo To view logs:    docker compose logs -f netbox
echo To stop:         docker compose down
echo.
