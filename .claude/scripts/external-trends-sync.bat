@echo off
REM external-trends-sync.bat — Windows Task Scheduler wrapper (매시간)
REM CLAUDE_PROJECT_DIR 우선, 없으면 .bat 위치 기준 두 단계 위

chcp 65001 >nul

if not defined CLAUDE_PROJECT_DIR (
  for %%I in ("%~dp0..\..") do set "CLAUDE_PROJECT_DIR=%%~fI"
)
cd /d "%CLAUDE_PROJECT_DIR%"

if not exist ".claude\logs" mkdir ".claude\logs"

REM Git Bash 동적 검색
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
  echo [external-trends] bash.exe not found >> ".claude\logs\external-trends.log"
  exit /b 1
)

"%BASH_EXE%" -c "bash .claude/scripts/external-trends-sync.sh" 1>>".claude\logs\external-trends.log" 2>>&1
exit /b 0
