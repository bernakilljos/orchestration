@echo off
chcp 65001 >nul
rem gemini-auto - project-root shortcut for gemini-a --verify
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"
rem 2026-11-06: PATH 이름이면 APPDATA npm 의 예전 사본이 실행됨 - kit 사본을 경로로
call "%PROJECT_ROOT%\.claude\scripts\gemini-a.bat" --verify %*
