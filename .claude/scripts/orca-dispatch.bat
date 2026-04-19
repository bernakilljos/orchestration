@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem orca-dispatch - Drop a task into the global orca queue
rem
rem Usage:
rem   orca-dispatch <task_file> [agent]
rem     task_file : path to local task-*.md (relative or absolute)
rem     agent     : codex (default) | gemini | claude
rem
rem Behavior:
rem   - Reads source task, prepends frontmatter with project_root
rem     (current working directory) + task_id + agent
rem   - Copies to %USERPROFILE%\.claude\orca\tasks\task-<id>.md
rem   - Prints the global task path on stdout
rem =====================================================

set "SRC=%~1"
set "AGENT=%~2"
if "%AGENT%"=="" set "AGENT=codex"

if "%SRC%"=="" (
  echo [orca-dispatch] ERROR: task file argument required
  echo   Usage: orca-dispatch ^<task_file^> [codex^|gemini^|claude]
  exit /b 1
)

if not exist "%SRC%" (
  echo [orca-dispatch] ERROR: task file not found: %SRC%
  exit /b 1
)

set "ORCA_ROOT=%USERPROFILE%\.claude\orca"
if not exist "%ORCA_ROOT%\tasks" mkdir "%ORCA_ROOT%\tasks" >nul 2>&1

rem --- Resolve absolute paths ---
for %%F in ("%SRC%") do set "SRC_ABS=%%~fF"
set "PROJECT_ROOT=%CD%"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

rem --- Derive project_id from folder name ---
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ID=%%~nxI"

rem --- Build unique task id: YYYYMMDD-HHMMSS-<project>-<rand> ---
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "TS=%%T"
for /f %%R in ('powershell -NoProfile -Command "'{0:x4}' -f (Get-Random -Max 65535)"') do set "RNDHEX=%%R"
set "TASK_ID=%TS%-%PROJECT_ID%-%RNDHEX%"
set "GLOBAL_TASK=%ORCA_ROOT%\tasks\task-%TASK_ID%.md"

rem --- Compose frontmatter + original body ---
powershell -NoProfile -Command ^
  "$src = Get-Content -LiteralPath '%SRC_ABS%' -Raw;" ^
  "$body = if($src -match '(?ms)^---\s*\r?\n.*?\r?\n---\s*\r?\n(.*)'){ $matches[1] } else { $src };" ^
  "$fm = @('---','task_id: %TASK_ID%','project_root: %PROJECT_ROOT%','project_id: %PROJECT_ID%','agent: %AGENT%','source: ' + (Resolve-Path -LiteralPath '%SRC_ABS%').Path,'created_at: ' + (Get-Date).ToString('s'),'---','') -join \"`n\";" ^
  "[System.IO.File]::WriteAllText('%GLOBAL_TASK%', $fm + $body, [System.Text.Encoding]::UTF8)"

if not exist "%GLOBAL_TASK%" (
  echo [orca-dispatch] ERROR: failed to write %GLOBAL_TASK%
  exit /b 1
)

echo [orca-dispatch] Queued: %GLOBAL_TASK%
echo [orca-dispatch] agent=%AGENT% project=%PROJECT_ID% id=%TASK_ID%
echo %GLOBAL_TASK%
endlocal
exit /b 0
