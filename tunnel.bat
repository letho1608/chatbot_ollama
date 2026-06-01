@echo off
REM Tysor - Cloudflare Tunnel Launcher
REM Requires: cloudflared.exe in PATH or same directory
REM Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

echo Checking for cloudflared...
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if exist "%~dp0cloudflared.exe" (
        set CMD="%~dp0cloudflared.exe"
    ) else (
        echo ERROR: cloudflared not found.
        echo Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
        echo Or place cloudflared.exe in this directory.
        pause
        exit /b 1
    )
) else (
    set CMD=cloudflared
)

echo Starting Cloudflare tunnel to http://127.0.0.1:8000 ...
echo Tunnel URL will appear below (trycloudflare.com)
echo Press Ctrl+C to stop.
echo.

%CMD% tunnel --url http://127.0.0.1:8000

pause
