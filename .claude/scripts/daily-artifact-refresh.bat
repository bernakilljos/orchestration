@echo off
REM Wrapper for daily-artifact-refresh.py (Task Scheduler entrypoint).
REM Dynamic python discovery (where py / where python) - no hardcoded path.

setlocal EnableExtensions
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo [daily-artifact-refresh] NO-SCHTASKS present, skipping. >>"%PROJECT_ROOT%\.claude\logs\daily-artifact-refresh.log" 2>nul
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
  echo [daily-artifact-refresh] python not found on PATH. >>"%PROJECT_ROOT%\.claude\logs\daily-artifact-refresh.log" 2>nul
  exit /b 0
)

pushd "%PROJECT_ROOT%"
%PY_CMD% "%SCRIPT_DIR%daily-artifact-refresh.py" >>".claude\logs\daily-artifact-refresh.log" 2>&1
popd
exit /b 0
