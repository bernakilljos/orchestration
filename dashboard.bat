@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(''GITHUB_PERSONAL_ACCESS_TOKEN'',''User'')"') do set "PAT=%%P"

if "!PAT!"=="" ( echo [WARN] GITHUB_PERSONAL_ACCESS_TOKEN not set - GitHub features disabled )

set "GITHUB_PERSONAL_ACCESS_TOKEN=!PAT!"
echo [+] 대시보드 시작...
timeout /t 1 /nobreak >nul
start http://localhost:8787
python "%~dp0dashboard.py"
pause