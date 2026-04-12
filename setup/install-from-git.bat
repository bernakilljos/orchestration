@echo off
chcp 65001 >nul
rem =====================================================
rem install-from-git.bat
rem GitHub에서 clone 후 바로 setup 실행
rem
rem Usage:
rem   install-from-git.bat [TARGET_PATH]
rem   install-from-git.bat C:\work\myproject
rem
rem 또는 이 한 줄로 어디서든 설치:
rem   powershell -c "iwr https://raw.githubusercontent.com/bernakilljos/orchestration/main/setup/install-from-git.bat -OutFile setup.bat; .\setup.bat"
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"

echo.
echo ============================================================
echo   Orchestration Kit - Install from Git
echo ============================================================
echo   Target: %TARGET%
echo ============================================================
echo.

rem --- Git 확인 ---
where git >nul 2>&1
if errorlevel 1 (
  echo [ERROR] git not found. Install git first:
  echo         winget install Git.Git
  echo         OR https://git-scm.com
  pause
  exit /b 1
)

rem --- GitHub PAT 가져오기 ---
set "GH_PAT="
for /f "tokens=*" %%T in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"GITHUB_PERSONAL_ACCESS_TOKEN\",\"User\")" 2^>nul') do set "GH_PAT=%%T"

rem Fallback PAT
if "!GH_PAT!"=="" set "GH_PAT="

rem --- Clone orchestration kit to temp ---
set "TEMP_KIT=%TEMP%\orchestration-kit-%RANDOM%"
echo [1/3] Cloning orchestration kit...

git clone https://!GH_PAT!@github.com/bernakilljos/orchestration.git "!TEMP_KIT!" >nul 2>&1
if errorlevel 1 (
  echo       Token auth failed, trying without token...
  git clone https://github.com/bernakilljos/orchestration.git "!TEMP_KIT!" >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Clone failed. Check network or repository access.
    pause
    exit /b 1
  )
)
echo       [OK] Kit cloned to temp

rem --- setup 폴더 확인 ---
if exist "!TEMP_KIT!\setup\setup.bat" (
  echo [2/3] Running modular setup...
  call "!TEMP_KIT!\setup\setup.bat" "%TARGET%"
) else if exist "!TEMP_KIT!\install.bat" (
  echo [2/3] Running legacy install...
  call "!TEMP_KIT!\install.bat" "%TARGET%"
) else (
  echo [ERROR] No setup script found in cloned repo
  pause
  exit /b 1
)

rem --- Cleanup ---
echo [3/3] Cleaning up temp files...
rd /s /q "!TEMP_KIT!" >nul 2>&1
echo       [OK] Done

echo.
echo ============================================================
echo   Installation complete via git clone!
echo ============================================================
pause
endlocal
exit /b 0
