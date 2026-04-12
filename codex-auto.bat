@echo off
chcp 65001 >nul
rem codex-auto - project-root shortcut for codex-a --auto
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"
call codex-a --auto %*
