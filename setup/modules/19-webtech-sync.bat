@echo off
REM setup/modules/19-webtech-sync.bat
REM WebTech Sync 자동화 Task Scheduler 등록
REM 목적: 주 1회(일요일 05:00) 최신 기술 버전 자동 fetch

setlocal enabledelayedexpansion

echo [19-webtech-sync] Task Scheduler 작업 등록 중...

REM Python 경로 동적 검색
for /f "delims=" %%A in ('where python 2^>nul') do set "PYTHON_PATH=%%A"

if not defined PYTHON_PATH (
  echo [ERROR] python 못 찾음. Python 설치 필수.
  exit /b 1
)

REM 프로젝트 경로 (하드코딩 금지 — 상대경로 + 스크립트 위치 기반)
cd /d "%~dp0..\..\."
set "PROJECT_ROOT=%cd%"
set "SCRIPT_PATH=%PROJECT_ROOT%\.claude\scripts\webtech-sync.py"

REM Task Scheduler 작업 생성 (일요일 05:00)
echo [19-webtech-sync] Task 'Orca_WebTechSync' 등록...

schtasks /create /tn "Orca_WebTechSync" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /sc weekly /d SUN /st 05:00 ^
  /f /ru SYSTEM 2>nul

if errorlevel 1 (
  REM 작업 이미 있으면 업데이트
  echo [19-webtech-sync] 기존 Task 업데이트...
  schtasks /delete /tn "Orca_WebTechSync" /f 2>nul
  schtasks /create /tn "Orca_WebTechSync" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc weekly /d SUN /st 05:00 ^
    /f /ru SYSTEM
)

echo [19-webtech-sync] ✓ Task 등록 완료 (일요일 05:00 실행)

call "%~dp0_task-allow-battery.bat" "Orca_WebTechSync"
REM 즉시 실행 옵션 (사용자 선택)
choice /C YN /M "[19-webtech-sync] 지금 즉시 실행할까요?" /T 3 /D N
if errorlevel 2 goto :end
if errorlevel 1 (
  echo [19-webtech-sync] 즉시 실행 중...
  "%PYTHON_PATH%" "%SCRIPT_PATH%"
)

:end
echo [19-webtech-sync] 완료
exit /b 0
