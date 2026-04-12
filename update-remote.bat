@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')"') do set "PAT=%%P"
if "!PAT!"=="" echo [ERROR] PAT not set & exit /b 1
echo [1/3] Downloading latest status-push.ps1...
if exist "%TEMP%\orch-upd" rd /s /q "%TEMP%\orch-upd"
git clone --depth 1 "https://x:!PAT!@github.com/bernakilljos/orchestration-status.git" "%TEMP%\orch-upd" >nul 2>&1
if not exist "%TEMP%\orch-upd\status-push.ps1" echo [ERROR] clone failed & exit /b 1
copy /Y "%TEMP%\orch-upd\status-push.ps1" "%USERPROFILE%\.claude\status-push.ps1" >nul
rd /s /q "%TEMP%\orch-upd"
echo [2/3] Stopping old process...
powershell -NoProfile -Command "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match 'status-push' -and $_.CommandLine -notmatch 'Get-WmiObject' } | ForEach-Object { $_.Terminate() }" >nul 2>&1
timeout /t 2 /nobreak >nul
echo [3/3] Starting status-push...
start "" wscript "%USERPROFILE%\.claude\status-push-silent.vbs"
echo [DONE] Updated and restarted.
endlocal
