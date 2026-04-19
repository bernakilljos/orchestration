@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem gemini-auto-global - Gemini worker for global orca queue
rem Mirrors codex-auto-global but calls gemini-a and picks
rem tasks whose frontmatter sets agent=gemini.
rem =====================================================

set "ORCA_ROOT=%USERPROFILE%\.claude\orca"
set "WORKERS_DIR=%ORCA_ROOT%\workers"
set "IS_CHILD=false"
set "CHILD_ID="
set "REQUESTED_COUNT="

if not exist "%ORCA_ROOT%" exit /b 1
if not exist "%WORKERS_DIR%" mkdir "%WORKERS_DIR%" >nul 2>&1

set "MAX_WORKERS=2"
if exist "%ORCA_ROOT%\workers-config.json" (
  set "_MW_TMP=%TEMP%\_orca_max_gemini_%RANDOM%.txt"
  powershell -NoProfile -Command "try { (Get-Content '%ORCA_ROOT%\workers-config.json' -Raw | ConvertFrom-Json).max_workers.gemini } catch { '' }" > "!_MW_TMP!" 2>nul
  if exist "!_MW_TMP!" (
    set /p _MW_VAL=<"!_MW_TMP!"
    if not "!_MW_VAL!"=="" set "MAX_WORKERS=!_MW_VAL!"
    del "!_MW_TMP!" >nul 2>&1
  )
)

:PARSE_ARGS
if "%~1"=="" goto POST_PARSE
if /i "%~1"=="--child" ( set "IS_CHILD=true" & set "CHILD_ID=%~2" & shift & shift & goto PARSE_ARGS )
echo %~1| findstr /r "^[0-9][0-9]*$" >nul 2>&1
if %errorlevel%==0 ( set "REQUESTED_COUNT=%~1" & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS
:POST_PARSE

if "%IS_CHILD%"=="true" goto CHILD_WORKER

set "_ALIVE_TMP=%TEMP%\_orca_alive_gemini_%RANDOM%.txt"
powershell -NoProfile -Command ^
  "$dir='%WORKERS_DIR%';" ^
  "if(-not (Test-Path $dir)){ '0'; exit };" ^
  "$n=@(Get-ChildItem -Path $dir -Filter 'gemini-*.hb' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -lt 2 }).Count;" ^
  "$n" > "%_ALIVE_TMP%" 2>nul
set /p ALIVE_COUNT=<"%_ALIVE_TMP%"
del "%_ALIVE_TMP%" >nul 2>&1
if "%ALIVE_COUNT%"=="" set "ALIVE_COUNT=0"

set /a ROOM=%MAX_WORKERS% - %ALIVE_COUNT%
if %ROOM% LEQ 0 (
  echo [gemini-auto-global] At cap: %ALIVE_COUNT%/%MAX_WORKERS% — no spawn.
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
echo   gemini-auto-global
echo   Alive: %ALIVE_COUNT% / Max: %MAX_WORKERS% / Spawning: %SPAWN_COUNT%
echo ============================================================

for /L %%i in (1,1,%SPAWN_COUNT%) do (
  set /a CID=%ALIVE_COUNT% + %%i
  echo [+] Spawn gemini worker #!CID!
  start "Gemini-Global-!CID!" /min cmd /c "gemini-auto-global --child !CID!"
)

exit /b 0

:CHILD_WORKER

for /f %%T in ('powershell -NoProfile -Command "[Guid]::NewGuid().ToString('N').Substring(0,8)"') do set "WORKER_TAG=%%T"
set "HB_FILE=%WORKERS_DIR%\gemini-%CHILD_ID%-%WORKER_TAG%.hb"
echo started %DATE% %TIME%> "%HB_FILE%"

echo.
echo ============================================================
echo   gemini-auto-global Worker #%CHILD_ID% [%WORKER_TAG%]
echo ============================================================

set "IDLE_COUNT=0"

:LOOP
echo alive %DATE% %TIME%> "%HB_FILE%"

if exist "%ORCA_ROOT%\stop" goto UNREGISTER

if exist "%ORCA_ROOT%\heartbeat" (
  powershell -NoProfile -Command "$hb=Get-Item '%ORCA_ROOT%\heartbeat' -ErrorAction SilentlyContinue; if($hb -and ([datetime]::Now - $hb.LastWriteTime).TotalMinutes -gt 5){exit 1}else{exit 0}" >nul 2>&1
  if errorlevel 1 goto UNREGISTER
)

if exist "%ORCA_ROOT%\locks\*.lock" (
  powershell -NoProfile -Command "Get-ChildItem '%ORCA_ROOT%\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Remove-Item $_.FullName -Force }" 2>nul
)

powershell -NoProfile -Command "Get-ChildItem '%WORKERS_DIR%\gemini-*.hb' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 10 } | ForEach-Object { Remove-Item $_.FullName -Force }" 2>nul

set "PICKED_TASK="
set "PICKED_NAME="
for %%F in ("%ORCA_ROOT%\tasks\task-*.md") do (
  set "TNAME=%%~nF"
  if not exist "%ORCA_ROOT%\locks\!TNAME!.lock" (
    rem Only pick tasks with agent=gemini
    powershell -NoProfile -Command "$c=Get-Content '%%F' -Raw -ErrorAction SilentlyContinue; if($c -match '(?ms)^---\s*\r?\n(.*?)\r?\n---'){ $fm=$matches[1]; if($fm -match '(?m)^agent:\s*(\S+)'){ if($matches[1] -eq 'gemini'){ exit 0 } else { exit 1 } } else { exit 1 } } else { exit 1 }" >nul 2>&1
    if not errorlevel 1 (
      echo %WORKER_TAG% %DATE% %TIME%> "%ORCA_ROOT%\locks\!TNAME!.lock" 2>nul
      if exist "%ORCA_ROOT%\locks\!TNAME!.lock" (
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

set /a IDLE_COUNT+=1
if !IDLE_COUNT! GEQ 60 (
  echo [Worker-%CHILD_ID%] Idle. Exit.
  goto UNREGISTER
)
timeout /t 60 /nobreak >nul
goto LOOP

:TASK_PICKED
set "IDLE_COUNT=0"
echo [Worker-%CHILD_ID%] Picked: %PICKED_NAME%

set "_PR_TMP=%TEMP%\_orca_pr_%CHILD_ID%_%RANDOM%.txt"
powershell -NoProfile -Command "$c=Get-Content '%PICKED_TASK%' -Raw; if($c -match '(?ms)^---\s*\r?\n(.*?)\r?\n---'){ $fm=$matches[1]; if($fm -match '(?m)^project_root:\s*(.+)$'){ $matches[1].Trim() } }" > "%_PR_TMP%" 2>nul
set /p TASK_PROJECT_ROOT=<"%_PR_TMP%"
del "%_PR_TMP%" >nul 2>&1

if "%TASK_PROJECT_ROOT%"=="" goto INVALID_TASK
if not exist "%TASK_PROJECT_ROOT%\.claude" goto INVALID_TASK

echo [Worker-%CHILD_ID%] Project: %TASK_PROJECT_ROOT%
pushd "%TASK_PROJECT_ROOT%"

attrib +r "%PICKED_TASK%" >nul 2>&1
copy /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.bak" >nul 2>&1

call gemini-a --verify "%PICKED_TASK%" 2>"%TEMP%\gemini-global-%CHILD_ID%-err.log"
set "GEM_EXIT=!errorlevel!"

if !GEM_EXIT! NEQ 0 (
  findstr /i /c:"rate" /c:"limit" /c:"quota" /c:"429" /c:"exceeded" "%TEMP%\gemini-global-%CHILD_ID%-err.log" >nul 2>&1
  if not errorlevel 1 (
    echo [Worker-%CHILD_ID%] TOKEN EXHAUSTED
    :GEM_TOKEN_WAIT
    if exist "%ORCA_ROOT%\stop" goto UNREGISTER_POP
    echo alive %DATE% %TIME%> "%HB_FILE%"
    timeout /t 600 /nobreak >nul
    gemini -p "echo ok" >nul 2>&1
    if errorlevel 1 goto GEM_TOKEN_WAIT
    call gemini-a --verify "%PICKED_TASK%" 2>nul
  )
)

attrib -r "%PICKED_TASK%" >nul 2>&1
move /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.md" >nul 2>&1
del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
popd
echo [Worker-%CHILD_ID%] Done.
timeout /t 15 /nobreak >nul
goto LOOP

:INVALID_TASK
echo [Worker-%CHILD_ID%] [ERROR] Invalid task: %PICKED_NAME%
move /Y "%PICKED_TASK%" "%ORCA_ROOT%\done\%PICKED_NAME%.invalid.md" >nul 2>&1
del "%ORCA_ROOT%\locks\%PICKED_NAME%.lock" 2>nul
goto LOOP

:UNREGISTER_POP
popd

:UNREGISTER
del "%HB_FILE%" >nul 2>&1

:END
endlocal
