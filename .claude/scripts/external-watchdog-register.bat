@echo off
chcp 65001 >nul
rem =====================================================
rem external-watchdog-register.bat
rem Windows Task Scheduler 에 외부 watchdog 을 1분 간격 등록
rem
rem 사용: 더블클릭 또는 cmd 에서 실행 (관리자 권한 불필요 — 현재 사용자 권한)
rem
rem 환경변수 (선택):
rem   WATCHDOG_AUTO_RESTART=1   hang 감지 시 VSCode 강제 재시작 (위험)
rem   WATCHDOG_NOTIFY=1         Windows 토스트 알림 (BurntToast 필요)
rem
rem 해제: external-watchdog-unregister.bat
rem =====================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "TASK_NAME=ClaudeOrcaExternalWatchdog"

rem Python 절대 경로 자동 감지 (Task Scheduler 는 user PATH 못 받으므로 풀패스 필수)
set "PY_PATH="
for /f "tokens=*" %%P in ('where python 2^>nul') do (
    if not defined PY_PATH set "PY_PATH=%%P"
)
if not defined PY_PATH (
    echo [ERROR] python 명령을 찾을 수 없음. PATH 확인 필요.
    exit /b 1
)

rem 정규화된 경로
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI"
set "WATCHDOG_PY=%PROJECT_ROOT%\.claude\scripts\external-watchdog.py"

if not exist "%WATCHDOG_PY%" (
    echo [ERROR] %WATCHDOG_PY% 없음
    exit /b 1
)

rem 기존 작업 있으면 삭제 (idempotent)
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

rem 1분 간격 등록 — python 절대 경로 사용 (Task Scheduler PATH 한계 우회)
schtasks /Create ^
    /SC MINUTE /MO 1 ^
    /TN "%TASK_NAME%" ^
    /TR "\"%PY_PATH%\" \"%WATCHDOG_PY%\" --once" ^
    /F ^
    /RU "%USERNAME%"

if errorlevel 1 (
    echo [FAIL] Task Scheduler 등록 실패
    exit /b 1
)

echo [OK] %TASK_NAME% 등록 완료
echo      간격: 1분
echo      스크립트: %WATCHDOG_PY%
echo      로그: %PROJECT_ROOT%\.claude\state\external-watchdog.log
echo.
echo 해제는: %SCRIPT_DIR%external-watchdog-unregister.bat
echo 상태 확인: schtasks /Query /TN "%TASK_NAME%"

endlocal
exit /b 0
