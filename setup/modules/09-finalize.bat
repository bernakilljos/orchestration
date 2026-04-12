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
