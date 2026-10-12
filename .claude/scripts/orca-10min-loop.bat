@echo off
REM ============================================================================
REM 10-Min Memory Loop Wrapper
REM 동적 Python 검색 + NO-SCHTASKS killswitch
REM ============================================================================

setlocal enabledelayedexpansion

REM --- NO-SCHTASKS killswitch ---
if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo [%date% %time%] NO-SCHTASKS detected. Exit 0. >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  exit /b 0
)

REM --- 동적 Python 검색 ---
for /f "delims=" %%i in ('where python 2^>nul') do (
  set PYTHON_EXE=%%i
  goto python_found
)

REM Python 못 찾음
echo [%date% %time%] Python not found in PATH >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
exit /b 1

:python_found

REM --- 스크립트 경로 (wrapper 기준 상대경로) ---
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%orca-10min-loop.py

if not exist "!SCRIPT_PATH!" (
  echo [%date% %time%] Script not found: !SCRIPT_PATH! >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  exit /b 1
)

REM --- Python 실행 ---
echo [%date% %time%] Running: !PYTHON_EXE! !SCRIPT_PATH! >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
"!PYTHON_EXE!" "!SCRIPT_PATH!" >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log" 2>&1

if errorlevel 1 (
  echo [%date% %time%] Exit code: %ERRORLEVEL% >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  exit /b 1
)

exit /b 0
