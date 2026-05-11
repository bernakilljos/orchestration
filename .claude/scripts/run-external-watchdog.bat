@echo off
rem run-external-watchdog.bat -- Task Scheduler wrapper.
rem Resolves python dynamically (no hard-coded paths) and runs watchdog.
rem Reason: Task Scheduler does not inherit user PATH; python.exe absolute
rem path varies per user/version. This wrapper does a fresh lookup each run.

setlocal

set "SCRIPT_DIR=%~dp0"
set "WATCHDOG_PY=%SCRIPT_DIR%external-watchdog.py"

rem 1: try `python`
set "PY_EXE="
for /f "tokens=*" %%P in ('where python 2^>nul') do (
    if not defined PY_EXE set "PY_EXE=%%P"
)

rem 2: try `python3`
if not defined PY_EXE (
    for /f "tokens=*" %%P in ('where python3 2^>nul') do (
        if not defined PY_EXE set "PY_EXE=%%P"
    )
)

rem 3: try Windows py launcher
if not defined PY_EXE (
    where py >nul 2>&1 && set "PY_EXE=py"
)

rem 4: last resort -- HKCU registry PythonCore InstallPath
if not defined PY_EXE (
    for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Python\PythonCore" /s /v InstallPath 2^>nul ^| findstr "InstallPath"') do (
        if exist "%%B\python.exe" set "PY_EXE=%%B\python.exe"
    )
)

if not defined PY_EXE (
    echo [run-external-watchdog] python not found
    exit /b 1
)

"%PY_EXE%" "%WATCHDOG_PY%" --once
exit /b %errorlevel%
