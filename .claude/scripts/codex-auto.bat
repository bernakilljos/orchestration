@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem codex-auto - Codex parallel/continuous worker
rem
rem Usage:
rem   codex-auto                  Default: 10 parallel workers
rem   codex-auto 20               Spawn 20 parallel workers
rem   codex-auto --parallel 30   Spawn 30 parallel workers
rem   codex-auto 1                Single worker mode
rem =====================================================

set "PROJECT_ROOT=%CD%"
set "WORKER_COUNT=10"
set "IS_CHILD=false"
set "CHILD_ID="

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto VALIDATE
if /i "%~1"=="--parallel" ( set "WORKER_COUNT=%~2" & shift & shift & goto PARSE_ARGS )
if /i "%~1"=="--child"    ( set "IS_CHILD=true" & set "CHILD_ID=%~2" & shift & shift & goto PARSE_ARGS )
rem bare number = worker count
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

if %WORKER_COUNT% LEQ 1 (
  rem Single worker - run inline (no new window)
  set "IS_CHILD=true"
  set "CHILD_ID=1"
  goto CHILD_WORKER
)

echo.
echo ============================================================
echo   Codex-Auto: Spawning %WORKER_COUNT% parallel workers
echo   Project: %PROJECT_ROOT%
echo ============================================================

for /L %%i in (1,1,%WORKER_COUNT%) do (
  echo [+] Starting worker %%i / %WORKER_COUNT%
  start "Codex-Worker-%%i" cmd /c "cd /d "%PROJECT_ROOT%" && codex-auto --child %%i"
)

echo.
echo [OK] %WORKER_COUNT% workers launched in separate windows.
echo      Each worker picks the next available task from .claude\tasks\
echo      Close windows or Ctrl+C to stop.
goto END

rem =====================================================
rem CHILD: pick tasks and run codex-a
rem =====================================================
:CHILD_WORKER
echo.
echo ============================================================
echo   Codex-Auto Worker #%CHILD_ID%
echo   Project: %PROJECT_ROOT%
echo   Ctrl+C to stop
echo ============================================================

rem --- 오늘 날짜 docs 폴더 설정 ---
for /f "tokens=*" %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "DOCS_DATE_DIR=%PROJECT_ROOT%\docs\!TODAY!"
if not exist "!DOCS_DATE_DIR!" mkdir "!DOCS_DATE_DIR!" >nul 2>&1

set "IDLE_COUNT=0"

:LOOP
rem --- Stop 파일 체크 ---
if exist "%PROJECT_ROOT%\.claude\tasks\stop" (
  echo [Worker-%CHILD_ID%] Stop file detected. Exiting.
  goto END
)

rem --- Orca-auto 비활성화 체크 ---
if exist "%PROJECT_ROOT%\.claude\orca-stopped" (
  echo [Worker-%CHILD_ID%] orca-stopped flag detected. Exiting.
  goto END
)

rem --- Heartbeat 체크: Claude 종료 여부 확인 (5분 이상 갱신 없으면 종료) ---
if exist "%PROJECT_ROOT%\.claude\orca-heartbeat" (
  powershell -NoProfile -Command "$hb=Get-Item '%PROJECT_ROOT%\.claude\orca-heartbeat' -ErrorAction SilentlyContinue; if($hb -and ([datetime]::Now - $hb.LastWriteTime).TotalMinutes -gt 5){exit 1}else{exit 0}" >nul 2>&1
  if errorlevel 1 (
    echo [Worker-%CHILD_ID%] Heartbeat stale - Claude exited. Stopping.
    goto END
  )
)

pushd "%PROJECT_ROOT%"

rem --- Stale lock cleanup: 30분 이상 된 lock 자동 삭제 ---
if exist "%PROJECT_ROOT%\.claude\tasks\locks\*.lock" (
  powershell -NoProfile -Command "Get-ChildItem '%PROJECT_ROOT%\.claude\tasks\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Write-Host '[Cleanup] Stale lock removed:' $_.Name; Remove-Item $_.FullName -Force }" 2>nul
)

rem --- Find next unlocked task file ---
set "PICKED_TASK="
for %%F in ("%PROJECT_ROOT%\.claude\tasks\task-*.md") do (
  set "TNAME=%%~nF"
  if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
    rem Skip template files
    findstr /i /c:"[Task Title]" /c:"[What to build" "%%F" >nul 2>&1
    if errorlevel 1 (
      rem Try to acquire lock
      echo worker-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" 2>nul
      if exist "%PROJECT_ROOT%\.claude\tasks\locks\!TNAME!.lock" (
        set "PICKED_TASK=%%F"
        goto TASK_PICKED
      )
    )
  )
)

rem --- No task available: fall back to default task-instruction.md ---
if exist "%PROJECT_ROOT%\.claude\tasks\task-instruction.md" (
  if not exist "%PROJECT_ROOT%\.claude\tasks\locks\task-instruction.lock" (
    findstr /i /c:"[Task Title]" /c:"[What to build" "%PROJECT_ROOT%\.claude\tasks\task-instruction.md" >nul 2>&1
    if errorlevel 1 (
      echo worker-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\task-instruction.lock" 2>nul
      set "PICKED_TASK=%PROJECT_ROOT%\.claude\tasks\task-instruction.md"
      goto TASK_PICKED
    )
  )
)

rem --- Idle timeout: 태스크 없이 1시간(60회 x 60초) 대기 시 자동 종료 ---
set /a IDLE_COUNT+=1
if !IDLE_COUNT! GEQ 60 (
  echo [Worker-%CHILD_ID%] Idle timeout (1h no tasks). Exiting.
  popd
  goto END
)
echo [Worker-%CHILD_ID%] No tasks available. Waiting 60s... (idle: !IDLE_COUNT!/60)
popd
timeout /t 60 /nobreak >nul
goto LOOP

:TASK_PICKED
set "IDLE_COUNT=0"
echo [Worker-%CHILD_ID%] Picked: %PICKED_TASK%

rem --- 지시서 원본 보호: 읽기 전용 + 백업 ---
for %%F in ("%PICKED_TASK%") do (
  attrib +r "%%F" >nul 2>&1
  if not exist "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" (
    copy /Y "%%F" "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF.bak" >nul 2>&1
  )
)

call codex-a --auto "%PICKED_TASK%" 2>"%TEMP%\codex-last-err.log"
set "CODEX_EXIT=!errorlevel!"

rem --- 토큰 소진 감지 → 대기 → 복구 시 재개 ---
if !CODEX_EXIT! NEQ 0 (
  findstr /i /c:"rate" /c:"limit" /c:"quota" /c:"429" /c:"exceeded" "%TEMP%\codex-last-err.log" >nul 2>&1
  if not errorlevel 1 (
    echo [Worker-%CHILD_ID%] TOKEN EXHAUSTED — 10분 간격 체크 시작
    echo exhausted> "%PROJECT_ROOT%\.claude\codex-token-status"
    :CODEX_TOKEN_WAIT
    if exist "%PROJECT_ROOT%\.claude\tasks\stop" goto END
    timeout /t 600 /nobreak >nul
    echo [Worker-%CHILD_ID%] Token check...
    codex exec "echo ok" >nul 2>&1
    if errorlevel 1 (
      echo [Worker-%CHILD_ID%] Still exhausted. Waiting 10m more...
      goto CODEX_TOKEN_WAIT
    )
    echo [Worker-%CHILD_ID%] TOKEN RESTORED — 재개!
    del "%PROJECT_ROOT%\.claude\codex-token-status" 2>nul
    rem 같은 태스크 다시 실행
    call codex-a --auto "%PICKED_TASK%" 2>nul
  )
)

rem --- 읽기 전용 해제 ---
for %%F in ("%PICKED_TASK%") do (
  attrib -r "%%F" >nul 2>&1
)

rem --- 필수 검증 (Stage 1,2,3) — 실패 시 완료 처리 안 함 ---
echo [Worker-%CHILD_ID%] Running mandatory verification...
if exist "%PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" (
  bash "%PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" 2>&1
  if errorlevel 1 (
    echo [Worker-%CHILD_ID%] [VERIFY FAIL] Errors found — task NOT marked as done
    for %%F in ("%PICKED_TASK%") do del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" 2>nul
    goto LOOP
  )
  echo [Worker-%CHILD_ID%] [VERIFY OK] All checks passed
)

rem --- 지시서가 삭제/손상됐으면 백업에서 복원 ---
for %%F in ("%PICKED_TASK%") do (
  if not exist "%%F" (
    if exist "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF.bak" (
      copy /Y "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF.bak" "%%F" >nul 2>&1
      echo [Worker-%CHILD_ID%] [WARN] Task file was deleted by codex - restored from backup
    )
  )
)

rem --- Clean up lock after completion ---
for %%F in ("%PICKED_TASK%") do (
  del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" 2>nul
)

rem --- Git commit + push (git 설정된 경우) ---
if exist "%PROJECT_ROOT%\.git" (
  for %%F in ("%PICKED_TASK%") do set "COMMIT_MSG=codex: complete %%~nF"
  git -C "%PROJECT_ROOT%" add . >nul 2>&1
  git -C "%PROJECT_ROOT%" commit -m "!COMMIT_MSG!" >nul 2>&1
  git -C "%PROJECT_ROOT%" push >nul 2>&1
  if not errorlevel 1 (
    echo [Worker-%CHILD_ID%] Git push 완료
  ) else (
    echo [Worker-%CHILD_ID%] Git push 실패 (원격 없거나 인증 오류)
  )
)

rem --- Create review task for Claude ---
for %%F in ("%PICKED_TASK%") do (
  set "TNAME_CHECK=%%~nF"
  if "!TNAME_CHECK:task-review=!"=="!TNAME_CHECK!" (
  set "REVIEW_TASK=!DOCS_DATE_DIR!\task-review-%%~nF.md"
  if not exist "!REVIEW_TASK!" (
    (
      echo # Review Implementation: %%~nF
      echo.
      echo ## Goal
      echo Codex has completed implementation of %%~nxF. Review the result and verify quality.
      echo.
      echo ## Steps
      echo 1. Read the original task: `.claude\tasks\done\%%~nxF`
      echo 2. Read implementation report: `docs\implementation-report.md`
      echo 3. Check that the implementation matches the task requirements
      echo 4. Fix any issues directly if minor
      echo 5. Write review summary to `docs\claude-review-%%~nF.md`
      echo.
      echo ## Rules
      echo - Relative paths only
      echo - Follow all rules in CLAUDE.md
    ) > "!REVIEW_TASK!"
    echo [Worker-%CHILD_ID%] Created review task: task-review-%%~nF.md
  )
  )
)

popd
echo.
echo [Worker-%CHILD_ID%] Task done. Next check in 30s...
timeout /t 30 /nobreak >nul
goto LOOP

:END
endlocal
