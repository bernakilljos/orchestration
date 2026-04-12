@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem claude-auto - Claude parallel subagent dispatcher
rem
rem Usage:
rem   claude-auto                  Default: agent+skill count (18 workers)
rem   claude-auto 20               20 workers
rem   claude-auto --parallel 30    30 workers
rem   claude-auto 1                Single worker (sequential)
rem
rem How it works:
rem   1. Reads all task files from .claude\tasks\
rem   2. Spawns N claude instances (claude -p) in parallel
rem   3. Each picks a task, executes, moves to done\
rem   4. Loops until no tasks remain or user stops
rem
rem Task files:
rem   .claude\tasks\task-01-*.md   Subtasks (from team-lead split)
rem   .claude\tasks\task-instruction.md   Single task (fallback)
rem =====================================================

set "PROJECT_ROOT=%CD%"
set "WORKER_COUNT=18"
set "IS_CHILD=false"
set "CHILD_ID="

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto VALIDATE
if /i "%~1"=="--parallel" ( set "WORKER_COUNT=%~2" & shift & shift & goto PARSE_ARGS )
if /i "%~1"=="--child"    ( set "IS_CHILD=true" & set "CHILD_ID=%~2" & shift & shift & goto PARSE_ARGS )
echo %~1| findstr /r "^[0-9][0-9]*$" >nul 2>&1
if %errorlevel%==0 ( set "WORKER_COUNT=%~1" & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS

:VALIDATE
if not exist "%PROJECT_ROOT%\.claude" (
  echo [ERROR] No .claude folder found in %PROJECT_ROOT%
  echo         Run this from the project root directory.
  pause
  exit /b 1
)

if not exist "%PROJECT_ROOT%\.claude\tasks" mkdir "%PROJECT_ROOT%\.claude\tasks" >nul 2>&1
if not exist "%PROJECT_ROOT%\.claude\tasks\done" mkdir "%PROJECT_ROOT%\.claude\tasks\done" >nul 2>&1
if not exist "%PROJECT_ROOT%\.claude\tasks\locks" mkdir "%PROJECT_ROOT%\.claude\tasks\locks" >nul 2>&1

rem =====================================================
rem PARENT: spawn N child windows
rem =====================================================
if "%IS_CHILD%"=="true" goto CHILD_WORKER

echo.
echo ============================================================
echo   Claude-Auto: Parallel Subagent Dispatcher
echo   Project:  %PROJECT_ROOT%
echo   Workers:  %WORKER_COUNT%
echo ============================================================
echo.

if %WORKER_COUNT% LEQ 1 (
  set "IS_CHILD=true"
  set "CHILD_ID=1"
  goto CHILD_WORKER
)

for /L %%i in (1,1,%WORKER_COUNT%) do (
  echo [+] Starting Claude worker %%i / %WORKER_COUNT%
  start "Claude-Worker-%%i" cmd /c "cd /d "%PROJECT_ROOT%" && claude-auto --child %%i"
)

echo.
echo [OK] %WORKER_COUNT% Claude workers launched.
echo      Each worker picks a task from .claude\tasks\
echo      Close windows or Ctrl+C to stop.
echo.
echo      Monitor progress:
echo        dir .claude\tasks\done\
echo        dir .claude\tasks\locks\
goto END

rem =====================================================
rem CHILD: pick task and run claude -p
rem =====================================================
:CHILD_WORKER
echo.
echo ============================================================
echo   Claude Worker #%CHILD_ID%
echo   Project: %PROJECT_ROOT%
echo ============================================================

:LOOP
cd /d "%PROJECT_ROOT%"

rem --- Stale lock cleanup: 30분 이상 된 lock 자동 삭제 ---
if exist "%PROJECT_ROOT%\.claude\tasks\locks\*.lock" (
  powershell -NoProfile -Command "Get-ChildItem '%PROJECT_ROOT%\.claude\tasks\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Write-Host '[Cleanup] Stale lock removed:' $_.Name; Remove-Item $_.FullName -Force }" 2>nul
)

rem --- Find next unlocked task ---
set "PICKED_TASK="
for %%F in ("%PROJECT_ROOT%\.claude\tasks\task-*.md") do (
  set "TNAME=%%~nF"
  rem Skip files in done folder
  if not exist "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" (
    if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
      rem Skip templates
      findstr /i /c:"[Task Title]" /c:"[What to build" "%%F" >nul 2>&1
      if errorlevel 1 (
        echo claude-worker-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" 2>nul
        if exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
          set "PICKED_TASK=%%F"
          goto CLAUDE_TASK_PICKED
        )
      )
    )
  )
)

rem --- Try task-instruction.md ---
if exist "%PROJECT_ROOT%\.claude\tasks\task-instruction.md" (
  if not exist "%PROJECT_ROOT%\.claude\tasks\locks\task-instruction.lock" (
    findstr /i /c:"[Task Title]" /c:"[What to build" "%PROJECT_ROOT%\.claude\tasks\task-instruction.md" >nul 2>&1
    if errorlevel 1 (
      echo claude-worker-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\task-instruction.lock" 2>nul
      set "PICKED_TASK=%PROJECT_ROOT%\.claude\tasks\task-instruction.md"
      goto CLAUDE_TASK_PICKED
    )
  )
)

echo [Worker-%CHILD_ID%] No tasks available. Waiting 60s...
timeout /t 60 /nobreak >nul
goto LOOP

:CLAUDE_TASK_PICKED
echo [Worker-%CHILD_ID%] Picked: %PICKED_TASK%
echo [Worker-%CHILD_ID%] Running claude -p ...
echo.

rem --- Build prompt from task file ---
set "TASK_CONTENT="
for /f "usebackq delims=" %%L in ("%PICKED_TASK%") do (
  if defined TASK_CONTENT (
    set "TASK_CONTENT=!TASK_CONTENT! %%L"
  ) else (
    set "TASK_CONTENT=%%L"
  )
)

rem --- Run Claude non-interactively (Sonnet + Opus advisor, unlimited) ---
rem Sonnet이 실행, 복잡한 판단은 Opus가 조언 (제한 없음)
claude -p "You are a worker agent. Read and implement this task file: %PICKED_TASK%. Follow all rules in CLAUDE.md and context\rules.md. After completion, write a brief report to docs\report-%CHILD_ID%.md. Do not ask questions - make reasonable decisions and proceed." --dangerously-skip-permissions --model claude-sonnet-4-6 --advisor claude-opus-4-6

set "CLAUDE_EXIT=%errorlevel%"

rem --- 필수 검증 (문법/인코딩/보호파일) ---
echo [Worker-%CHILD_ID%] Running mandatory verification...
set "VERIFY_PASS=true"
if exist "%PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" (
  bash "%PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" 2>&1
  if errorlevel 1 set "VERIFY_PASS=false"
)

rem --- Move to done + clean lock ---
for %%F in ("%PICKED_TASK%") do (
  if %CLAUDE_EXIT% EQU 0 if "!VERIFY_PASS!"=="true" (
    copy /Y "%%F" "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" >nul 2>&1
    echo [Worker-%CHILD_ID%] DONE: %%~nxF
  ) else (
    echo [Worker-%CHILD_ID%] FAILED: %%~nxF (exit=%CLAUDE_EXIT%, verify=!VERIFY_PASS!)
  )
  del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" 2>nul
)

echo.
goto LOOP

:END
endlocal
