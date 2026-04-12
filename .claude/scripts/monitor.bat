@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem monitor.bat - Server health monitoring (Windows)
rem Usage: .claude\scripts\monitor.bat [--all]
rem =====================================================

for /f "usebackq tokens=1,2 delims==" %%a in (".claude\deploy-config.env") do (
  if not "%%a"=="" (
    echo %%a | findstr /b "#" >nul || set "%%a=%%b"
  )
)

echo.
echo ==============================
echo  AGENT-05 Monitor
echo  Host: %REMOTE_HOST%
echo ==============================

if "%~1"=="--all" goto CHECK_ALL

rem Single server check
ssh %REMOTE_USER%@%REMOTE_HOST% "pm2 list --no-color 2>/dev/null | head -10; free -h | awk 'NR==2{print}'; df -h / | awk 'NR==2{print}'"

echo.
echo === Health Check ===
set RETRY=0
:HEALTH_LOOP
set /a RETRY+=1
curl -s -o nul -w "%%{http_code}" http://%REMOTE_HOST%:%SERVICE_PORT% > .tmp_status.txt
set /p STATUS=<.tmp_status.txt
del .tmp_status.txt

if "%STATUS%"=="200" (
  echo [OK] Service healthy [%STATUS%]
  goto DONE
)
echo [%RETRY%/5] FAIL [%STATUS%]
if %RETRY% LSS 5 ( timeout /t 10 /nobreak >nul & goto HEALTH_LOOP )

echo [FAIL] Health check failed - running rollback
call .claude\scripts\rollback.bat
goto DONE

:CHECK_ALL
echo === All Servers Check ===
for %%H in (YOUR_DEMO_SERVER YOUR_UPG_SERVER YOUR_CCP_SERVER) do (
  echo.
  echo --- %%H ---
  ssh -o ConnectTimeout=5 ec2-user@%%H "pm2 list --no-color 2>/dev/null | grep -E 'online|error' | head -3; df -h / | awk 'NR==2{print \"Disk:\", $5}'" 2>nul || echo [FAIL] Connect failed
)

:DONE
echo.
echo [DONE] Monitor complete
endlocal
