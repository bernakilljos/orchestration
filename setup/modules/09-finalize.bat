@echo off
rem =====================================================
rem Module 09: 프로젝트 초기화, npm install, Claude 실행
rem Usage: 09-finalize.bat [TARGET] [ANALYZE_MODE]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "ANALYZE_MODE=%~2"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1

echo.
echo ============================================================
echo   Finalize
echo ============================================================

rem --- init.bat ---
if exist "%TARGET%\.claude\scripts\init.bat" (
  echo [+] Running project init...
  call "%TARGET%\.claude\scripts\init.bat" "%TARGET%"
) else (
  echo       init.bat not found - skipped
)

rem --- Source analysis (optional) ---
if /i "%ANALYZE_MODE%"=="true" (
  if exist "%TARGET%\.claude\scripts\analyze.bat" (
    echo [+] Running source analysis...
    call "%TARGET%\.claude\scripts\analyze.bat" "%TARGET%"
  )
)

rem --- npm install ---
if exist "%TARGET%\package.json" (
  echo [+] Installing project dependencies...
  cd /d "%TARGET%"
  call npm install
  echo       Done
)

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo   Target: %TARGET%
echo.

where claude >nul 2>&1
if errorlevel 1 (
  echo   [WARN] claude not found in PATH
  echo          Install: https://claude.ai/download/cli
  echo          Then run:
  echo            cd /d "%TARGET%"
  echo            claude --dangerously-skip-permissions
  goto END
)

rem --- Local LLM 감지 및 설정 ---
echo [+] Local LLM 감지 중...
set "LOCAL_LLM_TYPE=null"
where ollama >nul 2>&1 && set "LOCAL_LLM_TYPE=ollama"
if "!LOCAL_LLM_TYPE!"=="null" where lms >nul 2>&1 && set "LOCAL_LLM_TYPE=lm-studio"
if "!LOCAL_LLM_TYPE!"=="null" where llamafile >nul 2>&1 && set "LOCAL_LLM_TYPE=llamafile"

if not "!LOCAL_LLM_TYPE!"=="null" (
  echo       감지됨: !LOCAL_LLM_TYPE!
  echo       로컬 LLM 워커를 활성화할까요? (워커 1개, 보조 역할)
  set /p "USE_LLM=  [Y/N]: "
  if /i "!USE_LLM!"=="Y" (
    powershell -NoProfile -Command ^
      "$cfg = Get-Content '%TARGET%\.claude\orca-workers-config.json' | ConvertFrom-Json; $cfg.local_llm.type = '!LOCAL_LLM_TYPE!'; $cfg | ConvertTo-Json -Depth 5 | Set-Content '%TARGET%\.claude\orca-workers-config.json'"
    echo       [OK] orca-workers-config.json 업데이트됨
  ) else (
    echo       [SKIP] 로컬 LLM 비활성화
  )
) else (
  echo       로컬 LLM 없음 - 나중에 설치 후 .claude\orca-workers-config.json 에서 설정 가능
)

echo   Start Claude now?
echo     [Y] Yes - launch Claude
echo     [N] No  - exit
echo.
set /p "RUN_CLAUDE=Select [Y/N]: "
if /i "!RUN_CLAUDE!"=="Y" (
  cd /d "%TARGET%"
  echo [OK] Starting claude...
  claude --dangerously-skip-permissions
)

:END
echo [Module 09] Finalize OK
endlocal
exit /b 0
