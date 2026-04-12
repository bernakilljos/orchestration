@echo off
rem gemini-auto - project-root shortcut for gemini-a --verify
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"
call gemini-a --verify %*
