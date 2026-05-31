@echo off
REM hourly-report.bat — Task Scheduler wrapper (cross-machine)
REM CLAUDE_PROJECT_DIR 우선, 없으면 현재 .bat 의 두 단계 위 (=프로젝트 루트) 사용
REM Git Bash 경로도 동적 검색

chcp 65001 >nul

REM 1) 프로젝트 루트 결정
if not defined CLAUDE_PROJECT_DIR (
  for %%I in ("%~dp0..\..") do set "CLAUDE_PROJECT_DIR=%%~fI"
)
cd /d "%CLAUDE_PROJECT_DIR%"

REM 2) 로그 디렉토리
if not exist ".claude\logs" mkdir ".claude\logs"

REM 3) Git Bash 위치 동적 검색
set "BASH_EXE="
for %%P in (
  "%PROGRAMFILES%\Git\bin\bash.exe"
  "%PROGRAMFILES(X86)%\Git\bin\bash.exe"
  "%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
) do (
  if exist %%~P set "BASH_EXE=%%~P"
)
if not defined BASH_EXE (
  where bash.exe >nul 2>&1
  if not errorlevel 1 (set "BASH_EXE=bash.exe")
)
if not defined BASH_EXE (
  echo [hourly-report] bash.exe not found >> ".claude\logs\hourly-report.log"
  exit /b 1
)

REM 4) 실행
"%BASH_EXE%" -c "bash .claude/scripts/hourly-report.sh" 1>>".claude\logs\hourly-report.log" 2>>&1
exit /b 0
