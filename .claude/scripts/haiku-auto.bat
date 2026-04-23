@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem haiku-auto — Claude Haiku 4.5 validation parallel worker
rem
rem Usage:
rem   haiku-auto              Default: read from config (usually 2)
rem   haiku-auto 4            Spawn 4 workers
rem   haiku-auto --child 1    Single child worker (internal)
rem =====================================================

set "PROJECT_ROOT=%CD%"
set "WORKER_COUNT=2"
set "IS_CHILD=false"
set "CHILD_ID="

rem --- Read haiku worker count from .claude/orca-workers-config.json ---
if not exist "%PROJECT_ROOT%\.claude\orca-workers-config.json" goto CFG_FALLBACK
set "_WC_TMP=%TEMP%\_haiku_wc_%RANDOM%.txt"
powershell -NoProfile -Command "try { (Get-Content '%PROJECT_ROOT%\.claude\orca-workers-config.json' -Raw | ConvertFrom-Json).workers.haiku } catch { '' }" > "%_WC_TMP%" 2>nul
if not exist "%_WC_TMP%" goto CFG_DONE
set /p _WC_VAL=<"%_WC_TMP%"
if not "%_WC_VAL%"=="" set "WORKER_COUNT=%_WC_VAL%"
del "%_WC_TMP%" >nul 2>&1
goto CFG_DONE
:CFG_FALLBACK
if exist "%PROJECT_ROOT%\.claude\orca-workers" set /p WORKER_COUNT=<"%PROJECT_ROOT%\.claude\orca-workers"
:CFG_DONE

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

rem --- Check Python availability ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3 not found. Install Python 3.8+ and add to PATH.
  exit /b 1
)

if not exist "%PROJECT_ROOT%\.claude\tasks\done" mkdir "%PROJECT_ROOT%\.claude\tasks\done" >nul 2>&1
if not exist "%PROJECT_ROOT%\.claude\tasks\locks" mkdir "%PROJECT_ROOT%\.claude\tasks\locks" >nul 2>&1

rem =====================================================
rem PARENT: spawn N child windows
rem =====================================================
if "%IS_CHILD%"=="true" goto CHILD_WORKER

if %WORKER_COUNT% LEQ 1 (
  set "IS_CHILD=true"
  set "CHILD_ID=1"
  goto CHILD_WORKER
)

echo.
echo ============================================================
echo   Haiku-Auto: Spawning %WORKER_COUNT% parallel validators
echo   Project: %PROJECT_ROOT%
echo ============================================================

for /L %%i in (1,1,%WORKER_COUNT%) do (
  echo [+] Starting Haiku validator %%i / %WORKER_COUNT%
  start "Haiku-Validator-%%i" cmd /c "cd /d "%PROJECT_ROOT%" && haiku-auto --child %%i"
)

echo.
echo [OK] %WORKER_COUNT% validators launched in separate windows.
echo      Each validator picks task-review-* or task-* files and validates with Haiku.
echo      Close windows or Ctrl+C to stop.
goto END

rem =====================================================
rem CHILD: pick tasks and validate with Haiku
rem =====================================================
:CHILD_WORKER
echo.
echo ============================================================
echo   Haiku-Auto Validator #%CHILD_ID%
echo   Project: %PROJECT_ROOT%
echo   Model: claude-haiku-4-5
echo   Ctrl+C or create .claude\tasks\stop to halt
echo ============================================================

rem --- Today's docs folder ---
for /f "tokens=*" %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "DOCS_DATE_DIR=%PROJECT_ROOT%\docs\!TODAY!"
if not exist "!DOCS_DATE_DIR!" mkdir "!DOCS_DATE_DIR!" >nul 2>&1

set "IDLE_COUNT=0"

:LOOP
rem --- Worker heartbeat update ---
if not exist "%PROJECT_ROOT%\.claude\state\workers" mkdir "%PROJECT_ROOT%\.claude\state\workers" >nul 2>&1
python -c "import time; open('%PROJECT_ROOT%\.claude\state\workers\haiku-%CHILD_ID%.hb', 'w').write(str(int(time.time())))" >nul 2>&1

rem --- Stop file check ---
if exist "%PROJECT_ROOT%\.claude\tasks\stop" (
  echo [Validator-%CHILD_ID%] Stop file detected. Exiting.
  goto END
)

rem --- Orca-auto disabled check ---
if exist "%PROJECT_ROOT%\.claude\orca-stopped" (
  echo [Validator-%CHILD_ID%] orca-stopped flag detected. Exiting.
  goto END
)

rem --- Heartbeat check: verify Claude session is alive (5min tolerance) ---
if exist "%PROJECT_ROOT%\.claude\orca-heartbeat" (
  powershell -NoProfile -Command "$hb=Get-Item '%PROJECT_ROOT%\.claude\orca-heartbeat' -ErrorAction SilentlyContinue; if($hb -and ([datetime]::Now - $hb.LastWriteTime).TotalMinutes -gt 5){exit 1}else{exit 0}" >nul 2>&1
  if errorlevel 1 (
    echo [Validator-%CHILD_ID%] Heartbeat stale - Claude exited. Stopping.
    goto END
  )
)

pushd "%PROJECT_ROOT%"

rem --- Stale lock cleanup: 30+ minutes old locks auto-deleted ---
powershell -NoProfile -Command "Get-ChildItem '%PROJECT_ROOT%\.claude\tasks\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Write-Host '[Cleanup] Stale lock removed:' $_.Name; Remove-Item $_.FullName -Force }" 2>nul

rem --- [1] Prioritize task-review-*.md (explicit validation tasks) ---
set "PICKED_TASK="
for %%F in ("%PROJECT_ROOT%\.claude\tasks\task-review-*.md") do (
  set "TNAME=%%~nF"
  if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
    echo validator-haiku-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" 2>nul
    if exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
      set "PICKED_TASK=%%F"
      goto TASK_PICKED
    )
  )
)

rem --- [2] Fall back to general task-*.md (if not other type) ---
for %%F in ("%PROJECT_ROOT%\.claude\tasks\task-*.md") do (
  set "TNAME=%%~nF"
  echo !TNAME! | findstr /i "task-review" >nul 2>&1
  if errorlevel 1 (
    if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
      echo validator-haiku-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" 2>nul
      if exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
        set "PICKED_TASK=%%F"
        goto TASK_PICKED
      )
    )
  )
)

rem --- No task found: idle ---
set /a IDLE_COUNT+=1
if !IDLE_COUNT! GEQ 60 (
  echo [Validator-%CHILD_ID%] Idle timeout (60 min). Exiting.
  popd
  goto END
)
echo [Validator-%CHILD_ID%] No task found. Waiting 60s... ^(idle: !IDLE_COUNT!/60^)
popd
timeout /t 60 /nobreak >nul
goto LOOP

:TASK_PICKED
set "IDLE_COUNT=0"
echo [Validator-%CHILD_ID%] Processing: !PICKED_TASK!

rem --- Call haiku-validate.py ---
python "%PROJECT_ROOT%\.claude\scripts\haiku-validate.py" "!PICKED_TASK!" --worker-id "haiku-%CHILD_ID%" --project-root "%PROJECT_ROOT%"
set "HAIKU_EXIT=!errorlevel!"

rem --- Handle quota exceeded (exit 3) ---
if !HAIKU_EXIT!==3 (
  echo [Validator-%CHILD_ID%] Quota exceeded during validation - waiting 10 minutes
  del "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" 2>nul
  popd
  timeout /t 600 /nobreak >nul
  goto LOOP
)

rem --- Handle validation failure (exit 1) ---
if !HAIKU_EXIT!==1 (
  echo [Validator-%CHILD_ID%] Validation failed. Moving to done/ for review.
  for %%F in ("!PICKED_TASK!") do (
    copy "!PICKED_TASK!" "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" >nul 2>&1
    del "!PICKED_TASK!" >nul 2>&1
    del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" 2>nul
  )
  popd
  echo [Validator-%CHILD_ID%] Next check in 30s...
  timeout /t 30 /nobreak >nul
  goto LOOP
)

rem --- Success (exit 0) ---
echo [Validator-%CHILD_ID%] Validation succeeded. Review written to docs/%TODAY%/
for %%F in ("!PICKED_TASK!") do (
  copy "!PICKED_TASK!" "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" >nul 2>&1
  del "!PICKED_TASK!" >nul 2>&1
  del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" 2>nul
)

popd
echo [Validator-%CHILD_ID%] Done. Next check in 30s...
timeout /t 30 /nobreak >nul
goto LOOP

:END
endlocal
