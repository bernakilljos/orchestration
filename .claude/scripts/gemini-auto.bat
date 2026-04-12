@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem gemini-auto - Gemini parallel/continuous verifier
rem
rem Usage:
rem   gemini-auto                  Default: 10 parallel verifiers
rem   gemini-auto 20               Spawn 20 parallel verifiers
rem   gemini-auto --parallel 30   Spawn 30 parallel verifiers
rem   gemini-auto 1                Single verifier mode
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

rem --- gemini 없으면 claude-auto로 폴백 ---
where gemini >nul 2>&1
if errorlevel 1 (
  echo [WARN] gemini not found - claude-auto로 폴백합니다...
  where claude-auto >nul 2>&1
  if not errorlevel 1 (
    echo [INFO] claude-auto %* 실행 중...
    claude-auto %*
  ) else (
    echo [ERROR] gemini, claude-auto 모두 없음. 설치 후 재시도하세요.
    exit /b 1
  )
  exit /b 0
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
echo   Gemini-Auto: Spawning %WORKER_COUNT% parallel verifiers
echo   Project: %PROJECT_ROOT%
echo ============================================================

for /L %%i in (1,1,%WORKER_COUNT%) do (
  echo [+] Starting verifier %%i / %WORKER_COUNT%
  start "Gemini-Verifier-%%i" cmd /c "cd /d "%PROJECT_ROOT%" && gemini-auto --child %%i"
)

echo.
echo [OK] %WORKER_COUNT% verifiers launched in separate windows.
echo      Each verifier picks the next completed task to review.
echo      Close windows or Ctrl+C to stop.
goto END

rem =====================================================
rem CHILD: pick completed tasks and verify (with retry + escalation)
rem =====================================================
:CHILD_WORKER
echo.
echo ============================================================
echo   Gemini-Auto Verifier #%CHILD_ID%
echo   Project: %PROJECT_ROOT%
echo   Ctrl+C or create .claude\tasks\stop to halt
echo ============================================================

rem --- 오늘 날짜 docs 폴더 설정 ---
for /f "tokens=*" %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "DOCS_DATE_DIR=%PROJECT_ROOT%\docs\!TODAY!"
if not exist "!DOCS_DATE_DIR!" mkdir "!DOCS_DATE_DIR!" >nul 2>&1

set "IDLE_COUNT=0"

:LOOP
rem --- Stop 파일 체크 ---
if exist "%PROJECT_ROOT%\.claude\tasks\stop" (
  echo [Verifier-%CHILD_ID%] Stop file detected. Exiting.
  goto END
)

rem --- Orca-auto 비활성화 체크 ---
if exist "%PROJECT_ROOT%\.claude\orca-stopped" (
  echo [Verifier-%CHILD_ID%] orca-stopped flag detected. Exiting.
  goto END
)

rem --- Heartbeat 체크: Claude 종료 여부 확인 (5분 이상 갱신 없으면 종료) ---
if exist "%PROJECT_ROOT%\.claude\orca-heartbeat" (
  powershell -NoProfile -Command "$hb=Get-Item '%PROJECT_ROOT%\.claude\orca-heartbeat' -ErrorAction SilentlyContinue; if($hb -and ([datetime]::Now - $hb.LastWriteTime).TotalMinutes -gt 5){exit 1}else{exit 0}" >nul 2>&1
  if errorlevel 1 (
    echo [Verifier-%CHILD_ID%] Heartbeat stale - Claude exited. Stopping.
    goto END
  )
)

pushd "%PROJECT_ROOT%"

rem --- Stale lock cleanup: 30분 이상 된 lock 자동 삭제 ---
if exist "%PROJECT_ROOT%\.claude\tasks\locks\*.lock" (
  powershell -NoProfile -Command "Get-ChildItem '%PROJECT_ROOT%\.claude\tasks\locks\*.lock' -ErrorAction SilentlyContinue | Where-Object { ([datetime]::Now - $_.LastWriteTime).TotalMinutes -gt 30 } | ForEach-Object { Write-Host '[Cleanup] Stale lock removed:' $_.Name; Remove-Item $_.FullName -Force }" 2>nul
)

rem --- [1] 리서치 태스크 먼저 확인 (task-research-*.md 또는 내용에 [RESEARCH] 포함) ---
set "PICKED_RESEARCH="
for %%F in ("%PROJECT_ROOT%\.claude\tasks\task-*.md") do (
  set "RNAME=%%~nF"
  rem 파일명에 research/조사/ppt/문서 포함 여부 체크
  echo !RNAME! | findstr /i "research 조사 ppt 문서 report" >nul 2>&1
  if not errorlevel 1 (
    if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" (
      findstr /i /c:"[Task Title]" /c:"[What to build" "%%F" >nul 2>&1
      if errorlevel 1 (
        echo verifier-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" 2>nul
        if exist "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" (
          set "PICKED_RESEARCH=%%F"
          goto RESEARCH_PICKED
        )
      )
    )
  )
  rem 내용에 [RESEARCH] 태그 있는지 체크
  findstr /i /c:"[RESEARCH]" /c:"[조사]" /c:"[PPT]" "%%F" >nul 2>&1
  if not errorlevel 1 (
    if not exist "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" (
      findstr /i /c:"[Task Title]" /c:"[What to build" "%%F" >nul 2>&1
      if errorlevel 1 (
        echo verifier-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" 2>nul
        if exist "%PROJECT_ROOT%\.claude\tasks\locks\!RNAME!.lock" (
          set "PICKED_RESEARCH=%%F"
          goto RESEARCH_PICKED
        )
      )
    )
  )
)
goto SKIP_RESEARCH

:RESEARCH_PICKED
echo [Verifier-%CHILD_ID%] Research task: %PICKED_RESEARCH%
call gemini-a --research "%PICKED_RESEARCH%"
rem 완료된 태스크 done 폴더로 이동
for %%F in ("%PICKED_RESEARCH%") do (
  copy "%%F" "%PROJECT_ROOT%\.claude\tasks\done\%%~nxF" >nul 2>&1
  del "%%F" >nul 2>&1
  del "%PROJECT_ROOT%\.claude\tasks\locks\%%~nF.lock" >nul 2>&1
)
popd
echo [Verifier-%CHILD_ID%] Research done. Next check in 10s...
timeout /t 10 /nobreak >nul
goto LOOP

:SKIP_RESEARCH

rem --- [2] 검증 태스크: implementation reports ---
set "PICKED_REPORT="
for %%F in ("%PROJECT_ROOT%\docs\implementation-report*.md") do (
  set "RNAME=%%~nF"
  if not exist "%PROJECT_ROOT%\.claude\tasks\locks\verify-!RNAME!.lock" (
    echo verifier-%CHILD_ID%> "%PROJECT_ROOT%\.claude\tasks\locks\verify-!RNAME!.lock" 2>nul
    if exist "%PROJECT_ROOT%\.claude\tasks\locks\verify-!RNAME!.lock" (
      set "PICKED_REPORT=%%F"
      goto REPORT_PICKED
    )
  )
)

rem --- No report: fall back to general verify ---
rem --- Idle timeout: 1시간 대기 시 자동 종료 ---
set /a IDLE_COUNT+=1
if !IDLE_COUNT! GEQ 60 (
  echo [Verifier-%CHILD_ID%] Idle timeout (1h). Exiting.
  popd
  goto END
)
echo [Verifier-%CHILD_ID%] No report found. Waiting 60s... (idle: !IDLE_COUNT!/60)
popd
timeout /t 60 /nobreak >nul
goto LOOP

:REPORT_PICKED
set "IDLE_COUNT=0"
echo [Verifier-%CHILD_ID%] Verifying: %PICKED_REPORT%

rem --- Retry loop: up to 3 attempts ---
set "RETRY=0"
set "VERIFY_OK=false"

:RETRY_LOOP
if %RETRY% GEQ 3 goto ESCALATE

set /a RETRY+=1
echo [Verifier-%CHILD_ID%] Attempt %RETRY%/3...
call gemini-a --verify "%PICKED_REPORT%"

rem Check result: gemini-a writes exit code or result to review-result.txt
if exist "%PROJECT_ROOT%\docs\review-result.txt" (
  findstr /i /c:"PASS" /c:"OK" /c:"passed" "%PROJECT_ROOT%\docs\review-result.txt" >nul 2>&1
  if not errorlevel 1 (
    set "VERIFY_OK=true"
    goto VERIFY_DONE
  )
)

rem Retry on failure
echo [Verifier-%CHILD_ID%] Attempt %RETRY% failed. Retrying in 10s...
timeout /t 10 /nobreak >nul
goto RETRY_LOOP

:ESCALATE
rem --- 3회 실패 → Claude 에스컬레이션 태스크 생성 ---
echo [Verifier-%CHILD_ID%] 3 retries failed. Creating Claude escalation task...
for %%F in ("%PICKED_REPORT%") do (
  set "ESC_TASK=%PROJECT_ROOT%\.claude\tasks\task-escalate-%%~nF.md"
  if not exist "!ESC_TASK!" (
    (
      echo # [ESCALATION] Gemini Verification Failed: %%~nF
      echo.
      echo ## Situation
      echo Gemini-Auto attempted verification 3 times and failed.
      echo Claude must review and fix this directly.
      echo.
      echo ## Steps
      echo 1. Read the implementation report: `docs\%%~nxF`
      echo 2. Read Gemini review result: `docs\review-result.txt`
      echo 3. Identify the root cause of the failure
      echo 4. Fix the issues directly
      echo 5. Write escalation report to `docs\escalation-report.md`
      echo.
      echo ## Rules
      echo - Relative paths only
      echo - Follow all rules in CLAUDE.md
    ) > "!ESC_TASK!"
    echo [Verifier-%CHILD_ID%] Escalation task created: !ESC_TASK!
  )
)
goto VERIFY_DONE

:VERIFY_DONE
rem Clean up lock
for %%F in ("%PICKED_REPORT%") do (
  del "%PROJECT_ROOT%\.claude\tasks\locks\verify-%%~nF.lock" 2>nul
)

if "%VERIFY_OK%"=="true" (
  rem --- Create adopt task for Claude ---
  for %%F in ("%PICKED_REPORT%") do (
    set "ADOPT_TASK=%PROJECT_ROOT%\.claude\tasks\task-adopt-%%~nF.md"
    if not exist "!ADOPT_TASK!" (
      (
        echo # Adopt Review: %%~nF
        echo.
        echo ## Goal
        echo Gemini has completed verification successfully. Apply valid improvements.
        echo.
        echo ## Steps
        echo 1. Read `docs\review-result.txt`
        echo 2. Read `%%F`
        echo 3. Apply improvements that are valid - use your judgment
        echo 4. Do NOT apply suggestions that conflict with project rules in CLAUDE.md
        echo 5. Write adoption summary to `docs\adopt-report.md`
        echo.
        echo ## Rules
        echo - Relative paths only
        echo - Follow all rules in CLAUDE.md
      ) > "!ADOPT_TASK!"
      echo [Verifier-%CHILD_ID%] Created adopt task: task-adopt-%%~nF.md
    )
  )
)

rem --- Daily report at 09:00 ---
for /f "tokens=1-2 delims=:" %%H in ("%TIME%") do (
  if "%%H"=="09" if "%%I"==" 0" (
    call :DAILY_REPORT
  )
)

popd
echo.
echo [Verifier-%CHILD_ID%] Done. Next check in 30s...
timeout /t 30 /nobreak >nul
goto LOOP

rem =====================================================
rem DAILY REPORT
rem =====================================================
:DAILY_REPORT
set "REPORT_FILE=!DOCS_DATE_DIR!\daily-report-!TODAY!.md"
if not exist "!REPORT_FILE!" (
  set "DONE_COUNT=0"
  for %%F in ("%PROJECT_ROOT%\.claude\tasks\done\*.md") do set /a DONE_COUNT+=1
  set "ESC_COUNT=0"
  for %%F in ("%PROJECT_ROOT%\docs\escalation-report*.md") do set /a ESC_COUNT+=1
  (
    echo # [%DATE% %TIME:~0,5%] Overnight Loop Completion Report
    echo.
    echo - Completed tasks : !DONE_COUNT!
    echo - Claude escalations: !ESC_COUNT!
    echo - Next scheduled tasks: see .claude\tasks\task-*.md
  ) > "!REPORT_FILE!"
  echo [Verifier-%CHILD_ID%] Daily report: !REPORT_FILE!
)
goto :EOF

:END
endlocal
