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

rem 정규화된 경로 — wrapper .bat 만 schtasks 에 등록 (하드 경로 금지)
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI"
set "WRAPPER_BAT=%PROJECT_ROOT%\.claude\scripts\run-external-watchdog.bat"

if not exist "%WRAPPER_BAT%" (
    echo [ERROR] %WRAPPER_BAT% 없음
    exit /b 1
)

rem 기존 작업 있으면 삭제 (idempotent)
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

rem 1분 간격 등록 — wrapper.bat 만 등록, python 위치는 wrapper 가 매번 동적 검색
schtasks /Create ^
    /SC MINUTE /MO 1 ^
    /TN "%TASK_NAME%" ^
    /TR "\"%WRAPPER_BAT%\"" ^
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
