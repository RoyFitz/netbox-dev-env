@echo off
REM Reset the NetBox environment (destroys all data)

set /p confirm="This will destroy ALL data. Are you sure? (y/N) "

if /i "%confirm%"=="y" (
    echo Stopping containers...
    docker compose down -v
    echo Environment reset complete.
    echo Run start.bat to start fresh.
) else (
    echo Cancelled.
)
