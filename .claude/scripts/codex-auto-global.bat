@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem codex-auto-global - Codex worker for global orca queue
rem
rem Reads tasks from %USERPROFILE%\.claude\orca\tasks\ and
rem runs them in the project_root embedded in each task's frontmatter.
rem
rem Usage:
rem   codex-auto-global            Parent: spawn workers up to global cap
rem   codex-auto-global N          Parent: spawn up to N workers (capped)
rem   codex-auto-global --child ID Child: single worker loop
rem =====================================================

set "ORCA_ROOT=%USERPROFILE%\.claude\orca"
set "WORKERS_DIR=%ORCA_ROOT%\workers"
set "IS_CHILD=false"
set "CHILD_ID="
set "REQUESTED_COUNT="

if not exist "%ORCA_ROOT%" (
  echo [ERROR] Global orca dir missing: %ORCA_ROOT%
  exit /b 1
)
if not exist "%WORKERS_DIR%" mkdir "%WORKERS_DIR%" >nul 2>&1

rem --- Global max workers for codex ---
set "MAX_WORKERS=4"
if exist "%ORCA_ROOT%\workers-config.json" (
  set "_MW_TMP=%TEMP%\_orca_max_codex_%RANDOM%.txt"
  powershell -NoProfile -Command "try { (Get-Content '%ORCA_ROOT%\workers-config.json' -Raw | ConvertFrom-Json).max_workers.codex } catch { '' }" > "!_MW_TMP!" 2>nul
  if exist "!_MW_TMP!" (
    set /p _MW_VAL=<"!_MW_TMP!"
    if not "!_MW_VAL!"=="" set "MAX_WORKERS=!_MW_VAL!"
    del "!_MW_TMP!" >nul 2>&1
  )
)

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto POST_PARSE
if /i "%~1"=="--child" ( set "IS_CHILD=true" & set "CHILD_ID=%~2" & shift & shift & goto PARSE_ARGS )
echo %~1| findstr /r "^[0-9][0-9]*$" >nul 2>&1
if %errorlevel%==0 ( set "REQUESTED_COUNT=%~1" & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS
:POST_PARSE

if "%IS_CHILD%"=="true" goto CHILD_WORKER

rem =====================================================
rem PARENT: count alive codex workers via heartbeat files,
rem         spawn enough to fill up to cap.
rem =====================================================

rem --- Count fresh codex worker heartbeats (updated within 2 min) ---
set "_ALIVE_TMP=%TEMP%\_orca_alive_codex_%RANDOM%.txt"
powershell -NoProfile -Command ^
  "$dir='%WORKERS_DIR%';" ^
  "if(-not (Test-Path $dir)){ '0'; exit };" ^
  "$n=@(Get-ChildItem -Path $dir -Filter 'codex-*.hb' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -lt 2 }).Count;" ^
  "$n" > "%_ALIVE_TMP%" 2>nul
set /p ALIVE_COUNT=<"%_ALIVE_TMP%"
del "%_ALIVE_TMP%" >nul 2>&1
if "%ALIVE_COUNT%"=="" set "ALIVE_COUNT=0"

set /a ROOM=%MAX_WORKERS% - %ALIVE_COUNT%
if %ROOM% LEQ 0 (
  echo [codex-auto-global] At cap: %ALIVE_COUNT%/%MAX_WORKERS% — no spawn.
  exit /b 0
)
if defined REQUESTED_COUNT (
  set "SPAWN_COUNT=%REQUESTED_COUNT%"
  if !SPAWN_COUNT! GTR %ROOM% set "SPAWN_COUNT=%ROOM%"
) else (
  set "SPAWN_COUNT=%ROOM%"
)

echo.
echo ============================================================
echo   codex-auto-global
echo   Alive: %ALIVE_COUNT% / Max: %MAX_WORKERS% / Spawning: %SPAWN_COUNT%
echo ============================================================

for /L %%i in (1,1,%SPAWN_COUNT%) do (
  set /a CID=%ALIVE_COUNT% + %%i
  echo [+] Spawn worker #!CID!
  start "Codex-Global-!CID!" /min cmd /c "codex-auto-global --child !CID!"
)

echo [OK] %SPAWN_COUNT% workers launched ^(minimized windows^).
exit /b 0

rem =====================================================
rem CHILD: heartbeat file + poll loop
rem =====================================================
:CHILD_WORKER

rem --- Heartbeat file uses unique id so multiple workers don't collide ---
for /f %%T in ('powershell -NoProfile -Command "[Guid]::NewGuid().ToString('N').Substring(0,8)"') do set "WORKER_TAG=%%T"
set "HB_FILE=%WORKERS_DIR%\codex-%CHILD_ID%-%WORKER_TAG%.hb"
echo started %DATE% %TIME%> "%HB_FILE%"

echo.
echo ============================================================
echo   codex-auto-global Worker #%CHILD_ID% [%WORKER_TAG%]
echo   Queue: %ORCA_ROOT%\tasks
echo ============================================================

set "IDLE_COUNT=0"

:LOOP
rem --- Refresh heartbeat ---
echo alive %DATE% %TIME%> "%HB_FILE%"

rem --- Global stop flag ---
if exist "%ORCA_ROOT%\stop" (
  echo [Worker-%CHILD_ID%] Global stop. Exit.
  goto UNREGISTER
)

rem --- Claude heartbeat staleness ---
if exist "%ORCA_ROOT%\heartbeat" (
  powershell -NoProfile -Command "$hb=Get-Item '%ORCA_ROOT%\heartbeat' -ErrorAction SilentlyContinue; if($hb -and ([datetime]::Now - $hb.LastWriteTime).TotalMinutes -gt 5){exit 1}else{exit 0}" >nul 2>&1
  if errorlevel 1 (
    echo [Worker-%CHILD_ID%] Claude heartbeat stale. Exit.
    goto UNREGISTER
  )
)

rem --- Stale lock cleanup (30 min) ---
if exist "%ORCA_ROOT%\locks\*.lock" (
  powershell -NoProfile -Command "Get-ChildItem '%ORCA_ROOT%\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Remove-Item $_.FullName -Force }" 2>nul
)

rem --- Stale worker-heartbeat cleanup (10 min) ---
powershell -NoProfile -Command "Get-ChildItem '%WORKERS_DIR%\codex-*.hb' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 10 } | ForEach-Object { Remove-Item $_.FullName -Force }" 2>nul

rem --- Find next unlocked codex task ---
set "PICKED_TASK="
set "PICKED_NAME="
for %%F in ("%ORCA_ROOT%\tasks\task-*.md") do (
  set "TNAME=%%~nF"
  if not exist "%ORCA_ROOT%\locks\!TNAME!.lock" (
    powershell -NoProfile -Command "$c=Get-Content '%%F' -Raw -ErrorAction SilentlyContinue; if($c -match '(?ms)^---\s*\r?\n(.*?)\r?\n---'){ $fm=$matches[1]; if($fm -match '(?m)^agent:\s*(\S+)'){ if($matches[1] -eq 'codex'){ exit 0 } else { exit 1 } } else { exit 0 } } else { exit 0 }" >nul 2>&1
    if not errorlevel 1 (
      echo %WORKER_TAG% %DATE% %TIME%> "%ORCA_ROOT%\locks\!TNAME!.lock" 2>nul
      if exist "%ORCA_ROOT%\locks\!TNAME!.lock" (
        rem Verify lock is ours (race check)
        set /p LOCK_OWNER=<"%ORCA_ROOT%\locks\!TNAME!.lock"
        for /f "tokens=1" %%O in ("!LOCK_OWNER!") do (
          if /i "%%O"=="%WORKER_TAG%" (
            set "PICKED_TASK=%%F"
            set "PICKED_NAME=!TNAME!"
            goto TASK_PICKED
          )
        )
      )
    )
  )
)

rem --- Idle ---
set /a IDLE_COUNT+=1
if !IDLE_COUNT! GEQ 60 (
  echo [Worker-%CHILD_ID%] Idle 60min. Exit.
  goto UNREGISTER
)
timeout /t 60 /nobreak >nul
goto LOOP

:TASK_PICKED
set "IDLE_COUNT=0"
echo [Worker-%CHILD_ID%] Picked: %PICKED_NAME%

rem --- HITL Approval Gate (CLAUDE.md §7-23) — 위험 패턴 task 차단 ---
rem 글로벌 큐: project 한정 못해 task 를 quarantine/ 으로 이동 (다음 LOOP 재pick 차단)
rem 각 project 가 quarantine 검토 후 승인 시 .claude/tasks/ 로 다시 enqueue
findstr /R /I /C:"DROP[ ]*TABLE" /C:"rm -rf" /C:"git push --force" /C:"sudo " /C:"curl .* | .*bash" /C:"--auto-approve" /C:"npm publish" /C:"docker push" "%PICKED_TASK%" >nul 2>&1
if not errorlevel 1 (
  echo [Worker-%CHILD_ID%] [HITL BLOCK] 위험 패턴 감지 — quarantine 으로 이동
  if not exist "%ORCA_ROOT%\quarantine" mkdir "%ORCA_ROOT%\quarantine" >nul 2>&1
  move /Y "%PICKED_TASK%" "%ORCA_ROOT%\quarantine\%PICKED_NAME%.md" >nul 2>&1
  del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
  echo [Worker-%CHILD_ID%] [HITL] Quarantined: %ORCA_ROOT%\quarantine\%PICKED_NAME%.md
  timeout /t 30 /nobreak >nul
  goto LOOP
)

rem --- Extract project_root ---
set "_PR_TMP=%TEMP%\_orca_pr_%CHILD_ID%_%RANDOM%.txt"
powershell -NoProfile -Command "$c=Get-Content '%PICKED_TASK%' -Raw; if($c -match '(?ms)^---\s*\r?\n(.*?)\r?\n---'){ $fm=$matches[1]; if($fm -match '(?m)^project_root:\s*(.+)$'){ $matches[1].Trim() } }" > "%_PR_TMP%" 2>nul
set /p TASK_PROJECT_ROOT=<"%_PR_TMP%"
del "%_PR_TMP%" >nul 2>&1

if "%TASK_PROJECT_ROOT%"=="" goto INVALID_TASK
if not exist "%TASK_PROJECT_ROOT%\.claude" goto INVALID_TASK

echo [Worker-%CHILD_ID%] Project: %TASK_PROJECT_ROOT%
pushd "%TASK_PROJECT_ROOT%"

rem --- Readonly + backup ---
attrib +r "%PICKED_TASK%" >nul 2>&1
copy /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.bak" >nul 2>&1

rem --- Run codex-a ---
call codex-a --auto "%PICKED_TASK%" 2>"%TEMP%\codex-global-%CHILD_ID%-err.log"
set "CODEX_EXIT=!errorlevel!"

rem --- Token exhaustion handling ---
if !CODEX_EXIT! NEQ 0 (
  findstr /i /c:"rate" /c:"limit" /c:"quota" /c:"429" /c:"exceeded" "%TEMP%\codex-global-%CHILD_ID%-err.log" >nul 2>&1
  if not errorlevel 1 (
    echo [Worker-%CHILD_ID%] TOKEN EXHAUSTED — 10m retry loop
    :CODEX_TOKEN_WAIT
    if exist "%ORCA_ROOT%\stop" goto UNREGISTER_POP
    echo alive %DATE% %TIME%> "%HB_FILE%"
    timeout /t 600 /nobreak >nul
    codex exec "echo ok" >nul 2>&1
    if errorlevel 1 goto CODEX_TOKEN_WAIT
    echo [Worker-%CHILD_ID%] TOKEN RESTORED
    call codex-a --auto "%PICKED_TASK%" 2>nul
  )
)

attrib -r "%PICKED_TASK%" >nul 2>&1

rem --- 필수 검증 (post-impl-verify.sh) — codex-auto.bat 와 정합 ---
echo [Worker-%CHILD_ID%] Running mandatory verification...
if exist "%TASK_PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" (
  set "PROJECT_ROOT=%TASK_PROJECT_ROOT%"
  bash "%TASK_PROJECT_ROOT%\.claude\hooks\post-impl-verify.sh" 2>&1
  if errorlevel 1 (
    echo [Worker-%CHILD_ID%] [VERIFY FAIL] Errors — task NOT marked done
    del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
    popd
    goto LOOP
  )
  echo [Worker-%CHILD_ID%] [VERIFY OK]
)

rem --- Metrics 기록 (route_dispatch.md §5 Step 5) ---
for %%F in ("%PICKED_TASK%") do set /a TOKENS_IN=(%%~zF)/4
python "%TASK_PROJECT_ROOT%\.claude\scripts\lib\record_call.py" ^
  --ai codex --model codex ^
  --tokens-in !TOKENS_IN! --tokens-out 0 ^
  --latency-ms 0 --success 1 ^
  --task-id "%PICKED_NAME%" 2>nul

rem --- Haiku/Claude 샌드위치 — review task 자동 생성 (route_dispatch.md §7) ---
echo !PICKED_NAME! | findstr /i "task-review task-escalate" >nul 2>&1
if errorlevel 1 (
  set "REVIEW_TASK=%TASK_PROJECT_ROOT%\.claude\tasks\task-review-%PICKED_NAME%.md"
  if not exist "!REVIEW_TASK!" (
    (
      echo # Review: %PICKED_NAME%
      echo.
      echo ## Goal
      echo Global codex worker completed %PICKED_NAME%. Haiku/Claude review the result.
      echo.
      echo ## Steps
      echo 1. Read original task: `.claude\tasks\done\%PICKED_NAME%.bak`
      echo 2. Verify implementation matches task requirements
      echo 3. Fix minor issues directly
      echo 4. Write review to `docs\claude-review-%PICKED_NAME%.md`
      echo.
      echo ## Rules
      echo - Relative paths only
      echo - Follow all rules in CLAUDE.md
    ) > "!REVIEW_TASK!"
    echo [Worker-%CHILD_ID%] Sandwich review task created
  )
)

move /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.md" >nul 2>&1
del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
popd
echo [Worker-%CHILD_ID%] Done. Next in 15s.
timeout /t 15 /nobreak >nul
goto LOOP

:INVALID_TASK
echo [Worker-%CHILD_ID%] [ERROR] Invalid task ^(no project_root or path^): %PICKED_NAME%
move /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.invalid.md" >nul 2>&1
del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
goto LOOP

:UNREGISTER_POP
popd

:UNREGISTER
del "%HB_FILE%" >nul 2>&1

:END
endlocal
