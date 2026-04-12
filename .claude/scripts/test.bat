@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem test.bat - Run tests (Windows)
rem Usage: .claude\scripts\test.bat [component-path]
rem =====================================================

set TARGET_FILE=%~1

echo.
echo === SKILL-06 Test ===

if not exist "docs"       mkdir docs
if not exist "tests\unit" mkdir tests\unit

rem Frontend tests
if exist package.json (
  echo [Test] Jest...
  call npx jest --passWithNoTests 2>&1 | tee docs\test-result.txt
  if %errorlevel%==0 ( echo [PASS] Frontend tests ) else ( echo [FAIL] Frontend tests & exit /b 1 )
)

rem Backend tests
if exist pom.xml (
  echo [Test] Maven...
  call mvnw test -q 2>&1 | tee docs\test-result.txt
  if %errorlevel%==0 ( echo [PASS] Backend tests ) else ( echo [FAIL] Backend tests & exit /b 1 )
)

echo.
echo [DONE] Tests complete
endlocal
