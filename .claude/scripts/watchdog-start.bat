@echo off
chcp 65001 >nul
rem =====================================================
rem watchdog-start.bat — Start orchestration_v1 watchdog
rem
rem Checks if watchdog already running, starts if not.
rem Logs to .claude\state\watchdog.log
rem =====================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\"

rem Normalize paths
cd /d "%PROJECT_ROOT%"

rem Check if already running (simple PID file check)
if exist "%PROJECT_ROOT%.claude\state\watchdog.pid" (
    for /f "usebackq delims=" %%A in ("%PROJECT_ROOT%.claude\state\watchdog.pid") do set EXISTING_PID=%%A
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | findstr /R "!EXISTING_PID!" >nul
    if not errorlevel 1 (
        echo [Watchdog] Already running at PID !EXISTING_PID!
        exit /b 0
    )
)

echo [Watchdog] Starting...

rem Start Python watchdog in background
start /min cmd /c "cd /d "%PROJECT_ROOT%" && python "%SCRIPT_DIR%watchdog.py" >> "%PROJECT_ROOT%.claude\state\watchdog.log" 2>&1"

rem Wait a moment for process to start
timeout /t 2 /nobreak >nul

echo [Watchdog] Started in background.
echo           Log: %PROJECT_ROOT%.claude\state\watchdog.log
exit /b 0
