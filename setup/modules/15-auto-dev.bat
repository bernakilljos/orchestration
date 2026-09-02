@echo off
rem [차단] 스케줄 자동 등록 킬스위치 — 파일 있으면 아무것도 안 하고 종료
if exist "%USERPROFILE%\.claude\NO-SCHTASKS" exit /b 0
rem =====================================================
rem Module 15: 24/7 자동 개발 에이전트 등록
rem Usage: 15-auto-dev.bat [TARGET] [SCRIPT_DIR] [REAL_USERPROFILE]
rem
rem 역할:
rem   1. auto-dev-wrapper.bat 복사
rem   2. Windows Task Scheduler 4시간 간격 등록
rem   3. Claude Code SessionStart hook 에서 CronCreate 자동 등록
rem   4. Remote Trigger 등록 안내 (OAuth 필요)
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "SCRIPT_DIR=%~2"
set "REAL_USERPROFILE=%~3"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%~dp0..\"
if "%REAL_USERPROFILE%"=="" set "REAL_USERPROFILE=%USERPROFILE%"

set "FAIL=0"

echo.
echo ===== Module 15: 24/7 Auto-Dev Agent =====

rem === 1. auto-dev-wrapper.bat 복사 ===
echo [+] Copying auto-dev-wrapper.bat...
set "WRAPPER_SRC=%SCRIPT_DIR%scripts\auto-dev-wrapper.bat"
set "WRAPPER_DST=%TARGET%\.claude\scripts\auto-dev-wrapper.bat"

if not exist "%TARGET%\.claude\scripts" mkdir "%TARGET%\.claude\scripts" >nul 2>&1

if exist "%WRAPPER_SRC%" (
  copy /Y "%WRAPPER_SRC%" "%WRAPPER_DST%" >nul 2>&1
  echo       Copied to %WRAPPER_DST%
) else (
  echo       [WARN] auto-dev-wrapper.bat not found at %WRAPPER_SRC%
  set "FAIL=1"
)

rem === 2. Windows Task Scheduler 등록 (4시간 간격) ===
echo [+] Registering Task Scheduler (every 4 hours)...
set "TASK_NAME=OrchestrationAutoDev"

rem 기존 등록 삭제 (idempotent)
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

rem 새로 등록 — 4시간 간격, 무기한 반복
schtasks /create /tn "%TASK_NAME%" /tr "\"%WRAPPER_DST%\"" /sc HOURLY /mo 4 /st 00:07 /f >nul 2>&1
if errorlevel 1 (
  echo       [WARN] Task Scheduler registration failed
  echo       Manual: schtasks /create /tn "%TASK_NAME%" /tr "%WRAPPER_DST%" /sc HOURLY /mo 4 /f
  set "FAIL=1"
) else (
  echo       Registered: %TASK_NAME% (every 4h)
)

rem === 3. auto-dev 활성 플래그 ===
echo enabled > "%TARGET%\.claude\auto-dev-enabled"
echo       Auto-dev flag: %TARGET%\.claude\auto-dev-enabled

rem === 4. SessionStart hook 등록 (CronCreate 자동 등록) ===
echo [+] Creating session-start auto-dev hook...
set "HOOK_FILE=%TARGET%\.claude\hooks\auto-dev-session-cron.sh"
(
echo #!/usr/bin/env bash
echo # auto-dev-session-cron.sh — SessionStart 시 CronCreate 자동 등록 reminder
echo # Sub-project guard
echo [ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] ^|^| exit 0
echo.
echo PROJECT_DIR="$(cd "$(dirname "$0")/.." ^&^& pwd)"
echo FLAG="$PROJECT_DIR/auto-dev-enabled"
echo.
echo if [ -f "$FLAG" ]; then
echo   cat ^<^<'MSG'
echo.
echo [auto-dev] 24/7 자동 개발 활성. Task Scheduler 4시간 간격 등록됨.
echo   pending task 확인: ls .claude/tasks/*.md
echo   중단: rm .claude/auto-dev-enabled
echo.
echo MSG
echo fi
echo exit 0
) > "%HOOK_FILE%"
echo       Created: %HOOK_FILE%

rem === 5. Remote Trigger 안내 ===
echo.
echo [i] Remote Trigger (cloud-based 24/7):
echo     Claude Code 세션에서:
echo       claude trigger create --schedule "0 */4 * * *" --project "%TARGET%" --prompt "자동 개발"
echo     또는 /schedule 커맨드 사용
echo.

echo [Module 15] Auto-Dev OK
if "!FAIL!"=="1" echo       [!] Some steps had warnings

endlocal
exit /b 0
