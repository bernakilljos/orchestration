@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem codex-a.bat - Codex-A AI worker (Windows)
rem
rem Usage:
rem   codex-a.bat                     Interactive mode
rem   codex-a.bat --auto              Auto (reads task-instruction.md)
rem   codex-a.bat --auto [task-file]  Auto with custom task file
rem   codex-a.bat --full-auto         Fully automated, no prompts
rem   codex-a.bat --analyze           Source analysis mode
rem =====================================================

rem --- Resolve project root: prefer %PROJECT_ROOT%, then walk up from %CD% ---
set ROOT=
if defined PROJECT_ROOT if exist "%PROJECT_ROOT%\.claude" set "ROOT=%PROJECT_ROOT%"
if not defined ROOT (
  set "ROOT=%CD%"
  if not exist "!ROOT!\.claude" (
    rem Walk up to find .claude folder
    for %%D in ("%CD%") do set "ROOT=%%~dpD"
    if not exist "!ROOT!\.claude" set "ROOT=%CD%"
  )
)
rem Strip trailing backslash
if "!ROOT:~-1!"=="\" set "ROOT=!ROOT:~0,-1!"
set TASK_FILE=%ROOT%\.claude\tasks\task-instruction.md
set MODE=interactive
set "UTF8_EXCLUDE=node_modules|\.claude|dist|\.git|build|target"

rem --- ANALYZE_PROMPT must be outside if blocks ---
set ANALYZE_PROMPT=Analyze the entire project source code. Steps: (1) Read docs\project-analysis.md for stack context. (2) Map all source files with their role. (3) Identify patterns: state management, API calls, auth flow, error handling. (4) Find improvements: list issues with file+line references. (5) For .sql or mapper files: DO NOT MODIFY. Write suggestions to docs\query-suggestions.md. (6) Write full analysis to docs\codex-analysis.md. Proceed automatically without asking for confirmation.

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto START
if /i "%~1"=="--auto"       ( set "MODE=auto"      & shift & goto PARSE_ARGS )
if /i "%~1"=="--full-auto"  ( set "MODE=full-auto" & shift & goto PARSE_ARGS )
if /i "%~1"=="--analyze"    ( set "MODE=analyze"   & shift & goto PARSE_ARGS )
if exist "%~1"              ( set "TASK_FILE=%~1"  & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS

:START
echo.
echo ============================================================
echo   Codex-A Worker
echo   Mode : %MODE%
echo ============================================================

rem --- Interactive mode ---
if "%MODE%"=="interactive" (
  echo [Codex-A] Interactive session...
  codex
  goto END
)

rem --- Analyze mode ---
if "%MODE%"=="analyze" (
  echo [Codex-A] Source analysis mode
  echo.
  codex exec --dangerously-bypass-approvals-and-sandbox "!ANALYZE_PROMPT!"
  goto END
)

rem --- Auto / Full-auto modes ---
if not exist "%TASK_FILE%" (
  echo [WAIT] No task file found. Waiting for task-instruction.md...
  exit /b 2
)

rem --- Skip if task is still a template (unfilled placeholder) ---
findstr /i /c:"[Task Title]" /c:"[What to build" "%TASK_FILE%" >nul 2>&1
if %errorlevel% EQU 0 (
  echo [WAIT] task-instruction.md is still a template. Waiting for real task...
  exit /b 2
)

rem --- Skip if already done (moved to done folder) ---
rem (codex-a moves completed tasks to .claude\tasks\done\ after finish)

echo [Codex-A] Task: %TASK_FILE%
echo.
echo --- Task Preview ---
set LINE=0
for /f "tokens=*" %%L in ('type "%TASK_FILE%"') do (
  set /a LINE+=1
  if !LINE! LEQ 5 echo   %%L
)
echo --------------------
echo.

set CODEX_PROMPT=Read the task instruction at %TASK_FILE% and implement everything described. If context\rules.md exists, follow all rules there too. Before modifying any existing file, log what you are changing and why - then proceed without waiting for input (auto mode). If referenced files do not exist, create them. New files can be created freely. After implementation: (1) write docs\implementation-report.md, (2) move %TASK_FILE% to .claude\tasks\done\ folder.

set RETRY_DELAY=300
set MAX_RETRIES=3
set RETRY_COUNT=0

if not exist "%ROOT%\.claude\tasks\done" mkdir "%ROOT%\.claude\tasks\done"

:RUN_CODEX
if "%MODE%"=="full-auto" (
  echo [Codex-A] Full-auto mode...
  codex exec --full-auto "!CODEX_PROMPT!"
) else (
  echo [Codex-A] Auto mode...
  codex exec --dangerously-bypass-approvals-and-sandbox "!CODEX_PROMPT!"
)

set EXIT_CODE=%errorlevel%

if %EXIT_CODE% EQU 0 (
  echo.
  echo [+] Converting source files to UTF-8...
  powershell -NoProfile -Command "Get-ChildItem '%ROOT%' -Recurse -Include '*.vue','*.js','*.ts','*.jsx','*.tsx' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '%UTF8_EXCLUDE%' } | ForEach-Object { try { $c = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::Default); [System.IO.File]::WriteAllText($_.FullName, $c, [System.Text.Encoding]::UTF8) } catch {} }" >nul 2>&1
  echo [DONE] Codex-A complete
  echo        Next: gemini-a --verify
  goto END
)

set /a RETRY_COUNT+=1
if !RETRY_COUNT! GTR %MAX_RETRIES% (
  echo [ERROR] Codex-A failed after %MAX_RETRIES% retries. Exit code: %EXIT_CODE%
  goto END
)

echo.
echo [RETRY] Codex-A exited with code %EXIT_CODE% - retry !RETRY_COUNT!/%MAX_RETRIES% in %RETRY_DELAY%s...
timeout /t %RETRY_DELAY% /nobreak >nul
goto RUN_CODEX

:END
endlocal
