@echo off
REM ============================================================================
REM Module 19: Orca 10-Min Loop Scheduler
REM 목적: Task Scheduler 자동 등록 (idempotent)
REM ============================================================================

setlocal enabledelayedexpansion

REM --- NO-SCHTASKS killswitch 존중 ---
if exist "%USERPROFILE%\.claude\NO-SCHTASKS" (
  echo [INFO] NO-SCHTASKS detected. Skipping scheduler registration.
  exit /b 0
)

REM --- wrapper 절대 경로 계산 ---
REM 이 배치 파일 위치에서 ..\..\로 프로젝트 루트
for /f "delims=" %%i in ('cd /d "%~dp0..\..\" ^& cd') do set PROJECT_ROOT=%%i

set WRAPPER_PATH=!PROJECT_ROOT!\.claude\scripts\orca-10min-loop.bat

if not exist "!WRAPPER_PATH!" (
  echo [ERROR] Wrapper not found: !WRAPPER_PATH!
  exit /b 1
)

REM --- 기존 작업 존재 확인 ---
schtasks /query /tn "Orca_10MinLoop" >nul 2>&1
if !errorlevel! equ 0 (
  echo [INFO] Task "Orca_10MinLoop" already exists. Skipping.
  exit /b 0
)

REM --- Task Scheduler 등록 ---
echo [INFO] Registering Orca_10MinLoop...
schtasks /create /tn "Orca_10MinLoop" /tr "!WRAPPER_PATH!" /sc minute /mo 10 /f /rl highest

if errorlevel 1 (
  echo [ERROR] Failed to register Orca_10MinLoop
  exit /b 1
)

echo [INFO] Task "Orca_10MinLoop" registered successfully (10-min interval)
exit /b 0
