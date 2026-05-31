@echo off
REM daily-cleanup.bat — 일 1회 정리 wrapper (cross-machine)
REM CLAUDE_PROJECT_DIR 우선, 없으면 .bat 위치 기준 두 단계 위 사용
REM cleanup-pollution.sh + temp file 삭제 + log truncate + done task 30일 archive

setlocal enabledelayedexpansion

if not defined CLAUDE_PROJECT_DIR (
  for %%I in ("%~dp0..\..") do set "CLAUDE_PROJECT_DIR=%%~fI"
)
set "PROJECT_ROOT=%CLAUDE_PROJECT_DIR%"
set "LOG_DIR=%PROJECT_ROOT%\.claude\logs"
set "CLEANUP_LOG=%LOG_DIR%\daily-cleanup.log"
set "TIMESTAMP=%date% %time%"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%TIMESTAMP%] Starting daily cleanup (root=%PROJECT_ROOT%) >> "%CLEANUP_LOG%"

REM 1) bash cleanup script (있으면 실행)
if exist "%PROJECT_ROOT%\.claude\scripts\cleanup-pollution.sh" (
  set "BASH_EXE="
  for %%P in (
    "%PROGRAMFILES%\Git\bin\bash.exe"
    "%PROGRAMFILES(X86)%\Git\bin\bash.exe"
    "%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
  ) do (
    if exist %%~P set "BASH_EXE=%%~P"
  )
  if not defined BASH_EXE (
    where bash.exe >nul 2>&1
    if not errorlevel 1 (set "BASH_EXE=bash.exe")
  )
  if defined BASH_EXE (
    "!BASH_EXE!" -c "bash '%PROJECT_ROOT%/.claude/scripts/cleanup-pollution.sh'" >> "%CLEANUP_LOG%" 2>&1
    echo [%date% %time%] cleanup-pollution.sh completed >> "%CLEANUP_LOG%"
  )
)

REM 2) bak / tmp / orig 파일 삭제
for /f "delims=" %%F in ('dir /b /s "%PROJECT_ROOT%\*.bak" 2^>nul') do (
  del /q "%%F" >nul 2>&1
  echo [%date% %time%] Removed: %%F >> "%CLEANUP_LOG%"
)
for /f "delims=" %%F in ('dir /b /s "%PROJECT_ROOT%\*.tmp" 2^>nul') do (
  del /q "%%F" >nul 2>&1
  echo [%date% %time%] Removed: %%F >> "%CLEANUP_LOG%"
)
for /f "delims=" %%F in ('dir /b /s "%PROJECT_ROOT%\*.orig" 2^>nul') do (
  del /q "%%F" >nul 2>&1
  echo [%date% %time%] Removed: %%F >> "%CLEANUP_LOG%"
)

REM 3) 5MB 초과 log truncate (마지막 1000줄만 유지)
for /f "delims=" %%F in ('dir /b "%LOG_DIR%\*.log" 2^>nul') do (
  for /f %%S in ('powershell -NoProfile -Command "[System.IO.FileInfo]::new(\"%LOG_DIR%\%%F\").Length"') do (
    if %%S GTR 5242880 (
      powershell -NoProfile -Command "Get-Content '%LOG_DIR%\%%F' -Tail 1000 | Set-Content '%LOG_DIR%\%%F.new'; Move-Item '%LOG_DIR%\%%F.new' '%LOG_DIR%\%%F' -Force"
      echo [%date% %time%] Truncated log: %%F >> "%CLEANUP_LOG%"
    )
  )
)

REM 4) 30일+ done task archive
if exist "%PROJECT_ROOT%\.claude\tasks\done" (
  for /f "delims=" %%F in ('forfiles /S /D +30 /P "%PROJECT_ROOT%\.claude\tasks\done" 2^>nul') do (
    del /q "%%F" >nul 2>&1
    echo [%date% %time%] Archived task: %%F >> "%CLEANUP_LOG%"
  )
)

echo [%date% %time%] Daily cleanup completed >> "%CLEANUP_LOG%"
exit /b 0
