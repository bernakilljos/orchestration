@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem notify.bat - Slack/Teams notification (Windows)
rem Usage: .claude\scripts\notify.bat [color] [message]
rem color: good | warning | danger
rem =====================================================

for /f "usebackq tokens=1,2 delims==" %%a in (".claude\deploy-config.env") do (
  if not "%%a"=="" (
    echo %%a | findstr /b "#" >nul || set "%%a=%%b"
  )
)

set COLOR=%~1
set MESSAGE=%~2
set TITLE=Orchestration

if "%NOTIFY_TYPE%"=="none" ( echo [SKIP] Notify disabled & exit /b 0 )
if "%NOTIFY_TYPE%"==""     ( echo [SKIP] Notify not configured & exit /b 0 )

rem Slack
if "%NOTIFY_TYPE%"=="slack" goto SLACK
if "%NOTIFY_TYPE%"=="both"  goto SLACK
goto TEAMS

:SLACK
if "%SLACK_WEBHOOK_URL%"=="" ( echo [SKIP] Slack webhook not set & goto TEAMS )
curl -s -X POST "%SLACK_WEBHOOK_URL%" ^
  -H "Content-type: application/json" ^
  -d "{\"attachments\":[{\"color\":\"%COLOR%\",\"title\":\"%TITLE%\",\"text\":\"%MESSAGE%\"}]}" >nul
echo [OK] Slack sent

:TEAMS
if "%NOTIFY_TYPE%"=="teams" goto DO_TEAMS
if "%NOTIFY_TYPE%"=="both"  goto DO_TEAMS
goto DONE

:DO_TEAMS
if "%TEAMS_WEBHOOK_URL%"=="" ( echo [SKIP] Teams webhook not set & goto DONE )
curl -s -X POST "%TEAMS_WEBHOOK_URL%" ^
  -H "Content-type: application/json" ^
  -d "{\"@type\":\"MessageCard\",\"title\":\"%TITLE%\",\"text\":\"%MESSAGE%\"}" >nul
echo [OK] Teams sent

:DONE
endlocal
