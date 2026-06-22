@echo off
chcp 65001 >nul 2>&1
rem =====================================================
rem watchdog-start.bat — Start orchestration_v1 watchdog
rem
rem 100% silent launch — no cmd window, no taskbar entry.
rem Strategy (in order):
rem   1) pythonw.exe via `where pythonw` (windowless Python — preferred)
rem   2) wscript + run-watchdog-silent.vbs (SW_HIDE) with explicit python.exe path
rem   3) inline VBS one-shot (last resort)
rem Logs to .claude\state\watchdog.log
rem =====================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\"

cd /d "%PROJECT_ROOT%"

rem Already running? (PID file check)
if exist "%PROJECT_ROOT%.claude\state\watchdog.pid" (
    for /f "usebackq delims=" %%A in ("%PROJECT_ROOT%.claude\state\watchdog.pid") do set EXISTING_PID=%%A
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | findstr /R "!EXISTING_PID!" >nul
    if not errorlevel 1 (
        echo [Watchdog] Already running at PID !EXISTING_PID!
        exit /b 0
    )
)

echo [Watchdog] Starting silently...

rem --- Strategy 1: pythonw.exe (no console, no taskbar) ---
set "PYW="
for /f "delims=" %%P in ('where pythonw 2^>nul') do if not defined PYW set "PYW=%%P"
if defined PYW (
    start "" /B "!PYW!" "%SCRIPT_DIR%watchdog.py" >> "%PROJECT_ROOT%.claude\state\watchdog.log" 2>&1
    goto :verify
)

rem --- Strategy 2: VBS hidden launcher with explicit python.exe path ---
set "PY="
for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if not defined PY set "PY=python"
if exist "%SCRIPT_DIR%run-watchdog-silent.vbs" (
    wscript //nologo "%SCRIPT_DIR%run-watchdog-silent.vbs" "!PY!"
    goto :verify
)

rem --- Strategy 3: inline VBS one-shot ---
> "%TEMP%\_wd_oneshot.vbs" echo Set s=CreateObject("WScript.Shell"): s.Run "cmd /c """"!PY!"""" """"%SCRIPT_DIR%watchdog.py"""" >> """"%PROJECT_ROOT%.claude\state\watchdog.log"""" 2>^&1", 0, False
wscript //nologo "%TEMP%\_wd_oneshot.vbs"
del /q "%TEMP%\_wd_oneshot.vbs" >nul 2>&1

:verify
timeout /t 2 /nobreak >nul
echo [Watchdog] Started in background (hidden).
echo           Log: %PROJECT_ROOT%.claude\state\watchdog.log
exit /b 0
