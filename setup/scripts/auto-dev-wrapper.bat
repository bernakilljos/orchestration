@echo off
rem auto-dev-wrapper.bat — Task Scheduler 가 주기적으로 호출
rem Claude Code 를 깨워서 자동 개발 수행
rem 하드 경로 금지 — 동적 검색

setlocal enabledelayedexpansion

rem === 1. 프로젝트 경로 (이 파일 기준 2단계 위) ===
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_DIR=%%~fI"

rem === 2. Claude CLI 찾기 ===
where claude >nul 2>&1
if errorlevel 1 (
  echo [auto-dev] Claude CLI not found in PATH
  exit /b 1
)

rem === 3. 중복 실행 방지 (lock file) ===
set "LOCK=%PROJECT_DIR%\.claude\state\auto-dev.lock"
if exist "%LOCK%" (
  rem lock 이 1시간 이상 오래됐으면 stale 판정
  for %%F in ("%LOCK%") do set "LOCK_TIME=%%~tF"
  echo [auto-dev] Lock exists — another instance running. Skip.
  exit /b 0
)
echo %DATE% %TIME% > "%LOCK%"

rem === 4. Claude Code 실행 ===
cd /d "%PROJECT_DIR%"
echo [auto-dev] Starting at %DATE% %TIME% in %PROJECT_DIR%

claude --print --dangerously-skip-permissions -p "당신은 24/7 자동 개발 에이전트입니다. 다음을 순서대로 수행하세요: 1) .claude/tasks/ 에 pending task 있으면 처리 2) 없으면 코드 품질 개선 (lint, 테스트 추가, 문서 갱신, 보안 스캔) 3) 변경사항 있으면 commit + push 4) 없으면 조용히 종료. 5분 이내로 완료."

rem === 5. lock 해제 ===
del "%LOCK%" >nul 2>&1

echo [auto-dev] Finished at %DATE% %TIME%

rem === 6. 로그 ===
set "LOG_DIR=%PROJECT_DIR%\.claude\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%DATE% %TIME%] auto-dev completed >> "%LOG_DIR%\auto-dev.log"

endlocal
exit /b 0
