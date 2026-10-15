@echo off
rem ============================================================
rem  FreedomTower - start local hot-update server
rem    HTTP static :8000  +  UDP auto-discovery broadcast :28000
rem  Keep this window OPEN while testing.
rem  Stop = press Ctrl+C in this window, or close the window,
rem  (or double-click "停止热更服务器.bat").
rem
rem  Extra args are passed through, e.g.:
rem    --self-test        send one broadcast and receive it (3s sanity check)
rem    --http-port 8080   use another HTTP port
rem ============================================================
cd /d "%~dp0..\.."
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] "python" not found in PATH.
    echo         Use a full python.exe path instead, e.g.:
    echo         "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" .workbuddy\tools\hotupdate_server.py
    pause
    exit /b 1
)
echo Starting hot-update server... (HTTP :8000 / UDP :28000)
echo Close this window or press Ctrl+C to stop.
echo.
python .workbuddy\tools\hotupdate_server.py %*
echo.
echo [server exited]
pause
