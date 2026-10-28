@echo on
REM ============================================================================
REM 10-Min Memory Loop Wrapper
REM 동적 Python 검색 + NO-SCHTASKS killswitch
REM 2026-10-27: @echo on + 창 타이틀 + 단계별 표시 (사용자 "글씨 보이게 해")
REM     백그라운드 전환 (S4U) 은 관리자 권한 필요 · 현재 non-admin → echo on fallback
REM ============================================================================
title Orca 10-Min Memory Loop · %date% %time%
color 0A

setlocal enabledelayedexpansion

echo.
echo === Orca 10-Min Memory Loop === %date% %time%
echo.

REM --- NO-SCHTASKS killswitch ---
if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo [STEP] NO-SCHTASKS killswitch detected · skip
  echo [%date% %time%] NO-SCHTASKS detected. Exit 0. >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  timeout /t 2 /nobreak >nul
  exit /b 0
)

REM --- 동적 Python 검색 ---
echo [STEP 1/3] Python 검색 (where python)...
for /f "delims=" %%i in ('where python 2^>nul') do (
  set PYTHON_EXE=%%i
  echo         found: %%i
  goto python_found
)

REM Python 못 찾음
echo [FAIL] Python not found in PATH
echo [%date% %time%] Python not found in PATH >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
timeout /t 5 /nobreak >nul
exit /b 1

:python_found

REM --- 스크립트 경로 (wrapper 기준 상대경로) ---
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%orca-10min-loop.py
echo [STEP 2/3] 스크립트 확인: !SCRIPT_PATH!

if not exist "!SCRIPT_PATH!" (
  echo [FAIL] Script not found
  echo [%date% %time%] Script not found: !SCRIPT_PATH! >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  timeout /t 5 /nobreak >nul
  exit /b 1
)

REM --- Python 실행 ---
echo [STEP 3/3] 실행 중 (메모리 조회·orca.db VACUUM·cleanup-pollution)...
echo [%date% %time%] Running: !PYTHON_EXE! !SCRIPT_PATH! >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
"!PYTHON_EXE!" "!SCRIPT_PATH!" >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log" 2>&1

if errorlevel 1 (
  echo [DONE] Exit code: %ERRORLEVEL% (FAIL)
  echo [%date% %time%] Exit code: %ERRORLEVEL% >> "%USERPROFILE%\.claude\orca-10min-loop-wrapper.log"
  timeout /t 5 /nobreak >nul
  exit /b 1
)

echo [DONE] OK · log: %%USERPROFILE%%\.claude\orca-10min-loop-wrapper.log
timeout /t 2 /nobreak >nul
exit /b 0
