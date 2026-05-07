@echo off
rem =====================================================
rem Module 02: Windows Defender 예외 추가
rem Usage: 02-defender.bat [REAL_USERPROFILE]
rem =====================================================
setlocal enabledelayedexpansion

set "REAL_USERPROFILE=%~1"
if "%REAL_USERPROFILE%"=="" set "REAL_USERPROFILE=%USERPROFILE%"

echo.
echo [+] Adding Windows Defender exclusion...
set "DEFENDER_PATH=!REAL_USERPROFILE!\.claude"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$svc=Get-Service -Name WinDefend -ErrorAction SilentlyContinue; if($svc -and $svc.Status -eq 'Running'){ try { Add-MpPreference -ExclusionPath '%DEFENDER_PATH%' -ErrorAction Stop; Write-Host '      Defender exclusion added' } catch { Write-Host ('      [WARN] ' + $_.Exception.Message) } } else { Write-Host '      Defender not running - skipped' }" 2>nul
echo [Module 02] Defender OK
endlocal
exit /b 0
