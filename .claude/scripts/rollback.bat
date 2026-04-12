@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem rollback.bat - Auto rollback (Windows)
rem =====================================================

for /f "usebackq tokens=1,2 delims==" %%a in (".claude\deploy-config.env") do (
  if not "%%a"=="" (
    echo %%a | findstr /b "#" >nul || set "%%a=%%b"
  )
)

echo.
echo ==============================
echo  SKILL-07 Rollback
echo  Host: %REMOTE_HOST%
echo ==============================

echo [1/3] Checking latest backup...
ssh %REMOTE_USER%@%REMOTE_HOST% "ls -t %APP_PATH%/backup/ | head -5"

echo [2/3] Running rollback...
ssh %REMOTE_USER%@%REMOTE_HOST% ^
  "LAST=$(ls -t %APP_PATH%/backup/ | grep dist_ | head -1) && ^
   rm -rf %APP_PATH%/dist && ^
   cp -r %APP_PATH%/backup/$LAST %APP_PATH%/dist && ^
   sudo nginx -t && sudo systemctl reload nginx && ^
   echo Rollback OK: $LAST"

echo [3/3] Health check...
timeout /t 5 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://%REMOTE_HOST%:%SERVICE_PORT% > .tmp_status.txt
set /p HTTP_STATUS=<.tmp_status.txt
del .tmp_status.txt

if "%HTTP_STATUS%"=="200" (
  echo [OK] Rollback success
) else (
  echo [FAIL] Still failing [%HTTP_STATUS%] - manual check required
  exit /b 1
)

endlocal
