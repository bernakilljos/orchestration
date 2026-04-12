@echo off
rem =====================================================
rem Module 05: status-push + remote-agent 설치/등록/시작
rem Usage: 05-services.bat [TARGET] [SCRIPT_DIR] [REAL_USERPROFILE]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "SCRIPT_DIR=%~2"
set "REAL_USERPROFILE=%~3"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1
if "%SCRIPT_DIR%"=="" set "SCRIPT_DIR=%~dp0..\"
if "%REAL_USERPROFILE%"=="" set "REAL_USERPROFILE=%USERPROFILE%"

set "SVC_FAIL=0"

echo.
echo [+] Installing service files...
if not exist "!REAL_USERPROFILE!\.claude" mkdir "!REAL_USERPROFILE!\.claude" >nul 2>&1
if not exist "%SCRIPT_DIR%status-push.ps1" (
  echo       [WARN] status-push.ps1 not found - skipped
  goto SKIP_SERVICES
)

for %%F in (status-push.ps1 status-push-silent.vbs remote-agent.ps1 remote-agent-silent.vbs) do (
  if exist "%SCRIPT_DIR%%%F" copy /Y "%SCRIPT_DIR%%%F" "!REAL_USERPROFILE!\.claude\%%F" >nul 2>&1
)
echo       Files copied to !REAL_USERPROFILE!\.claude\

rem Register project path
set "PROJ_CONFIG=!REAL_USERPROFILE!\.claude\status-projects.txt"
if not exist "!PROJ_CONFIG!" echo.> "!PROJ_CONFIG!"
findstr /i /x /c:"%TARGET%" "!PROJ_CONFIG!" >nul 2>&1
if errorlevel 1 echo %TARGET%>> "!PROJ_CONFIG!"
echo       Project registered: %TARGET%

rem Cleanup duplicates
powershell -NoProfile -Command ^
  "$f='!PROJ_CONFIG!'; ^
   $lines=Get-Content $f -Encoding UTF8 -ErrorAction SilentlyContinue|Where-Object{$_.Trim()-ne''}; ^
   $clean=@();$seen=@{}; ^
   foreach($l in $lines){$n=$l.Trim().Replace('/','\').TrimEnd('\'); ^
     if(-not $n -or $n.Length -lt 3 -or $n -notmatch '^[A-Za-z]:\\'){continue} ^
     if($seen[$n.ToLower()]){continue} ^
     if(-not(Test-Path $n -PathType Container)){continue} ^
     $seen[$n.ToLower()]=$true;$clean+=$n}; ^
   Set-Content $f $clean -Encoding UTF8" >nul 2>&1

rem --- Registry + Start ---
set "VBS_PATH=!REAL_USERPROFILE!\.claude\status-push-silent.vbs"
set "RA_VBS=!REAL_USERPROFILE!\.claude\remote-agent-silent.vbs"

echo [+] Registering status-push (auto-start)...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationStatusPush" /t REG_SZ /d "wscript.exe \"!VBS_PATH!\"" /f >nul 2>&1
if errorlevel 1 (echo       [WARN] Registration failed & set "SVC_FAIL=1") else (echo       Registered)

start "" wscript "!VBS_PATH!" >nul 2>&1
if not errorlevel 1 (echo       Started) else (echo       [WARN] Start failed & set "SVC_FAIL=1")

echo [+] Registering remote-agent (auto-start)...
taskkill /f /fi "WINDOWTITLE eq remote-agent*" >nul 2>&1
timeout /t 1 /nobreak >nul

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationRemoteAgent" /t REG_SZ /d "wscript.exe \"!RA_VBS!\"" /f >nul 2>&1
if errorlevel 1 (echo       [WARN] Registration failed & set "SVC_FAIL=1") else (echo       Registered)

start "" wscript "!RA_VBS!" >nul 2>&1
if not errorlevel 1 (echo       Started) else (echo       [WARN] Start failed & set "SVC_FAIL=1")

rem --- RDP 활성화 ---
echo [+] Enabling Remote Desktop...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name 'fDenyTSConnections' -Value 0 -Force; ^
   Enable-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue" >nul 2>&1
if not errorlevel 1 (echo       RDP enabled) else (echo       [WARN] RDP failed)

if "!SVC_FAIL!"=="1" (
  echo.
  echo       [!] Some services failed. Manual start:
  echo           wscript "!VBS_PATH!"
  echo           wscript "!RA_VBS!"
)

:SKIP_SERVICES
echo [Module 05] Services OK
endlocal
exit /b 0
