@echo off
chcp 65001 >nul
set "TASK_NAME=ClaudeOrcaExternalWatchdog"
schtasks /Delete /TN "%TASK_NAME%" /F
if errorlevel 1 (
    echo [INFO] %TASK_NAME% 등록 없음 (이미 해제됨)
    exit /b 0
)
echo [OK] %TASK_NAME% 해제 완료
exit /b 0
