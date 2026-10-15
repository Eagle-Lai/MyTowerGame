@echo off
rem ============================================================
rem  FreedomTower - stop local hot-update server
rem  Kills ONLY a python.exe process that listens on TCP :8000.
rem  (If you started the server in a console window yourself,
rem   simply press Ctrl+C there instead.)
rem ============================================================
setlocal enabledelayedexpansion
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr /i "LISTENING"') do (
    tasklist /FI "PID eq %%p" 2>nul | findstr /i "python.exe" >nul
    if not errorlevel 1 (
        taskkill /F /PID %%p >nul 2>nul
        echo   killed python.exe  PID %%p
        set FOUND=1
    )
)
if "!FOUND!"=="0" echo   No running hot-update server found (no python.exe listening on TCP :8000).
echo.
pause
