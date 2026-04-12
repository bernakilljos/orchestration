@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem deploy.bat - Deploy script (Windows)
rem Usage: .claude\scripts\deploy.bat [--confirmed]
rem =====================================================

rem Load deploy-config.env
for /f "usebackq tokens=1,2 delims==" %%a in (".claude\deploy-config.env") do (
  if not "%%a"=="" (
    echo %%a | findstr /b "#" >nul || set "%%a=%%b"
  )
)

set CONFIRMED=false
if "%~1"=="--confirmed" set CONFIRMED=true

echo.
echo ==============================
echo  SKILL-05 Deploy
echo  Env : %TARGET_ENV%
echo  Host: %REMOTE_HOST%
echo ==============================

rem Block prod without --confirmed
if "%TARGET_ENV%"=="prod" if "%CONFIRMED%"=="false" (
  echo [BLOCK] PROD requires --confirmed flag
  exit /b 1
)

rem Quality gate
echo [1/4] Quality gate...
call .claude\scripts\quality-gate.bat
if %errorlevel% NEQ 0 (
  echo [BLOCK] Quality gate failed - deploy aborted
  exit /b 1
)

rem Build
echo [2/4] Build...
if exist package.json (
  call npm run build
  if %errorlevel% NEQ 0 ( echo [FAIL] Build failed & exit /b 1 )
)
if exist pom.xml (
  call mvnw clean package -DskipTests -q
  if %errorlevel% NEQ 0 ( echo [FAIL] Maven build failed & exit /b 1 )
)

rem SSH transfer
echo [3/4] File transfer...
ssh %REMOTE_USER%@%REMOTE_HOST% "echo SSH OK"
if %errorlevel% NEQ 0 ( echo [BLOCK] SSH connect failed & exit /b 1 )

rsync -avz --delete dist/ %REMOTE_USER%@%REMOTE_HOST%:%APP_PATH%/dist/ 2>nul || (
  echo rsync not found - using scp
  scp -r dist/* %REMOTE_USER%@%REMOTE_HOST%:%APP_PATH%/dist/
)
ssh %REMOTE_USER%@%REMOTE_HOST% "sudo nginx -t && sudo systemctl reload nginx"

rem Health check
echo [4/4] Health check...
timeout /t 5 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://%REMOTE_HOST%:%SERVICE_PORT% > .tmp_status.txt
set /p HTTP_STATUS=<.tmp_status.txt
del .tmp_status.txt

if "%HTTP_STATUS%"=="200" (
  echo [OK] Deploy success - http://%REMOTE_HOST%:%SERVICE_PORT%
) else (
  echo [FAIL] Health check failed [%HTTP_STATUS%] - running rollback
  call .claude\scripts\rollback.bat
  exit /b 1
)

echo.
echo [DONE] Deploy complete
endlocal
