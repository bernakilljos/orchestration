@echo off
REM run-official-features-check.bat — Task Scheduler wrapper
REM 트리거: Task Scheduler daily (register-official-features-task.ps1 로 등록)
REM 동작: check-official-features.sh 강제 실행 (24h throttle 만료시키지 않고 호출)
REM Zero-touch: cross-machine 호환을 위해 git bash 동적 검색

setlocal

REM 프로젝트 루트 = 이 wrapper 의 ..\..  (.. = scripts, ..\.. = root)
set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

REM git bash 동적 검색 (하드 경로 금지 - CLAUDE.md § 7-4)
for /f "delims=" %%i in ('where bash 2^>nul') do (
    set "BASH=%%i"
    goto :found
)
echo [ERROR] bash not found in PATH
exit /b 1

:found
"%BASH%" "%PROJECT_ROOT%\.claude\scripts\check-official-features.sh"
exit /b %ERRORLEVEL%
