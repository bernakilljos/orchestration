@echo off
REM 18-daily-artifact-refresh.bat
REM Register DAILY 04:00 Task Scheduler job for artifact freshness auto-refresh.
REM Idempotent - honors NO-SCHTASKS killswitch.

setlocal EnableExtensions

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"

set "WRAPPER=%TARGET%\.claude\scripts\daily-artifact-refresh.bat"
set "TASK_NAME=Orca_DailyArtifactRefresh"

if not exist "%WRAPPER%" (
  echo   [18] wrapper missing: %WRAPPER% -- skip
  exit /b 0
)

if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo   [18] NO-SCHTASKS killswitch present -- skip
  exit /b 0
)

schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
schtasks /create /tn "%TASK_NAME%" /tr "\"%WRAPPER%\"" /sc DAILY /st 04:00 /f >nul 2>&1
if errorlevel 1 (
  echo   [18] schtasks register FAILED
  echo       Manual: schtasks /create /tn "%TASK_NAME%" /tr "%WRAPPER%" /sc DAILY /st 04:00 /f
  exit /b 0
)

echo   [18] Registered: %TASK_NAME% DAILY 04:00
exit /b 0
