@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem quality-gate.bat - Quality gate check (Windows)
rem =====================================================
set PASS=0
set FAIL=0

echo.
echo === Quality Gate ===

rem ESLint
if exist package.json (
  echo [Lint] Running...
  call npm run lint --if-present >nul 2>&1
  if %errorlevel%==0 ( echo [PASS] Lint & set /a PASS+=1 ) else ( echo [FAIL] Lint & set /a FAIL+=1 )
)

rem Build
if exist package.json (
  echo [Build] Running...
  call npm run build >nul 2>&1
  if %errorlevel%==0 ( echo [PASS] Build & set /a PASS+=1 ) else ( echo [FAIL] Build & set /a FAIL+=1 )
)

rem Maven
if exist pom.xml (
  echo [Maven] Running...
  call mvnw compile -q >nul 2>&1
  if %errorlevel%==0 ( echo [PASS] Maven & set /a PASS+=1 ) else ( echo [FAIL] Maven & set /a FAIL+=1 )
)

echo.
echo === Result: PASS=%PASS% FAIL=%FAIL% ===

if %FAIL% GTR 0 (
  echo [BLOCK] Quality gate failed
  exit /b 1
)

echo [OK] Quality gate passed
exit /b 0
