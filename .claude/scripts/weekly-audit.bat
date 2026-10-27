@echo on
REM Wrapper for weekly-audit.py (Task Scheduler entrypoint)
REM S4U 환경에서 python PATH 없음 → 동적 검색 (where py / where python)
REM 2026-10-27: FAIL 0x80070002 (file not found · python missing) 수정

setlocal EnableExtensions
title Orca Weekly Audit · %date% %time%
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo [weekly-audit] NO-SCHTASKS present, skipping. >> "%PROJECT_ROOT%\.claude\logs\weekly-audit.log" 2>nul
  timeout /t 2 /nobreak >nul
  exit /b 0
)

set "PY_CMD="
for /f "delims=" %%A in ('where py 2^>nul') do (
  if not defined PY_CMD set "PY_CMD=%%A -3"
)
if not defined PY_CMD (
  for /f "delims=" %%A in ('where python 2^>nul') do (
    if not defined PY_CMD set "PY_CMD=%%A"
  )
)
if not defined PY_CMD (
  echo [weekly-audit] Python not found in PATH >> "%PROJECT_ROOT%\.claude\logs\weekly-audit.log" 2>nul
  timeout /t 5 /nobreak >nul
  exit /b 1
)

echo [weekly-audit] running: %PY_CMD% %SCRIPT_DIR%weekly-audit.py
%PY_CMD% "%SCRIPT_DIR%weekly-audit.py" >> "%PROJECT_ROOT%\.claude\logs\weekly-audit.log" 2>&1
set RC=%ERRORLEVEL%
echo [weekly-audit] exit %RC%
timeout /t 2 /nobreak >nul
exit /b %RC%
