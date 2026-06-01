@echo off
cd /d "%~dp0"

echo Starting Tysor AI Server...
start /b python -m uvicorn main:app --host 127.0.0.1 --port 8000
timeout /t 3 >nul

echo.
echo === Server: http://127.0.0.1:8000 ===
echo.

where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    if not exist "%~dp0cloudflared.exe" (
        echo cloudflared not found. Install from:
        echo   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
        pause
        exit /b 1
    )
)

python wait_for_tunnel.py
pause