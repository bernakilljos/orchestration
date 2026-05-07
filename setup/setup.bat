@echo off
chcp 65001 >nul
rem =====================================================
rem setup.bat - Orchestration Kit Modular Installer
rem
rem Usage:
rem   setup.bat                             GUI 마법사 자동 실행 (있을 때)
rem   setup.bat --console [path]            콘솔 모드 강제 (GUI 무시)
rem   setup.bat full   [path]               Full 콘솔 (Claude+Codex+Gemini)
rem   setup.bat codex  [path]               Codex 단독 (Claude 없이)
rem   setup.bat gemini [path]               Gemini 단독 (Claude 없이)
rem   setup.bat anl    [path]               Full + 소스 분석
rem
rem Can also be called from setup.exe (Inno Setup)
rem =====================================================

rem --- GUI 자동 호출: 빌드된 setup.exe 가 있고 --console 아니면 GUI 마법사 띄움 ---
if /i "%~1"=="--console" (
  shift
  goto SKIP_GUI
)
if /i "%~1"=="full" goto SKIP_GUI
if /i "%~1"=="codex" goto SKIP_GUI
if /i "%~1"=="gemini" goto SKIP_GUI
if /i "%~1"=="anl" goto SKIP_GUI

if exist "%~dp0Output\OrchestrationKit-Setup.exe" (
  echo.
  echo [+] GUI 마법사 실행 중...
  echo     ^(콘솔 모드 강제: setup --console^)
  start "" "%~dp0Output\OrchestrationKit-Setup.exe"
  exit /b 0
)

:SKIP_GUI

rem --- Uninstall old npm Claude Code (only for full mode) ---
where volta >nul 2>&1
if not errorlevel 1 (
  volta list @anthropic-ai/claude-code 2>nul | findstr /C:"@anthropic-ai/claude-code" >nul 2>&1
  if not errorlevel 1 call volta uninstall @anthropic-ai/claude-code >nul 2>&1
  goto SKIP_NPM_UNINSTALL
)
where npm >nul 2>&1 || goto SKIP_NPM_UNINSTALL
call npm list -g @anthropic-ai/claude-code >nul 2>&1 || goto SKIP_NPM_UNINSTALL
call npm uninstall -g @anthropic-ai/claude-code >nul 2>&1
:SKIP_NPM_UNINSTALL

rem --- Auto-elevate ---
rem (test 우회: SKIP_ELEVATION=1 환경변수 시 admin 검사 건너뜀)
if "%SKIP_ELEVATION%"=="1" goto _SETUP_ELEV_DONE
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator privileges...
  echo @echo off > "%TEMP%\_setup_elevate.bat"
  echo chcp 65001 ^>nul >> "%TEMP%\_setup_elevate.bat"
  echo cd /d "%~dp0" >> "%TEMP%\_setup_elevate.bat"
  echo call "%~f0" %* >> "%TEMP%\_setup_elevate.bat"
  echo pause >> "%TEMP%\_setup_elevate.bat"
  powershell -NoProfile -Command "Start-Process cmd.exe -ArgumentList @('/k','%TEMP%\_setup_elevate.bat') -Verb RunAs"
  exit /b
)
:_SETUP_ELEV_DONE

setlocal enabledelayedexpansion

rem --- Log ---
set "LOGFILE=%TEMP%\orchestration-setup.log"
echo ============================ > "!LOGFILE!"
echo  Setup Log: %DATE% %TIME%   >> "!LOGFILE!"
echo ============================ >> "!LOGFILE!"

rem --- Real user profile ---
echo ^(Get-WmiObject Win32_Process ^| Where-Object {$_.Name -eq 'explorer.exe'} ^| Select-Object -First 1^).GetOwner^(^).User > "%TEMP%\_getuser.ps1"
for /f "tokens=*" %%N in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\_getuser.ps1"') do set "REAL_USERNAME=%%N"
del "%TEMP%\_getuser.ps1" >nul 2>&1
if "!REAL_USERNAME!"=="" set "REAL_USERNAME=%USERNAME%"
set "REAL_USERPROFILE=C:\Users\!REAL_USERNAME!"

rem --- Mode parse (full | codex | gemini) ---
set "MODE=full"
if /i "%~1"=="full"   ( set "MODE=full"   & shift )
if /i "%~1"=="codex"  ( set "MODE=codex"  & shift )
if /i "%~1"=="gemini" ( set "MODE=gemini" & shift )

rem --- Analyze flag (full mode only) ---
set "ANALYZE_MODE=false"
if /i "%~1"=="anl" ( set "ANALYZE_MODE=true" & shift )

rem --- Target path ---
if not "%~1"=="" (set "TARGET=%~1") else (set "TARGET=%CD%")

rem SCRIPT_DIR = orchestration kit root (parent of setup/)
set "SETUP_DIR=%~dp0"
rem SETUP_DIR 끝 \ 제거 → 그 path 의 parent dir 추출
set "SETUP_DIR_NS=%SETUP_DIR:~0,-1%"
for %%P in ("%SETUP_DIR_NS%") do set "SCRIPT_DIR=%%~dpP"

:TRIM_TARGET
if "!TARGET:~-1!"==" "  set "TARGET=!TARGET:~0,-1!" & goto TRIM_TARGET
if "!TARGET:~-1!"=="\"  set "TARGET=!TARGET:~0,-1!" & goto TRIM_TARGET

rem --- Self-install 방지: TARGET 이 setup 폴더면 부모 (kit root) 로 자동 변경 ---
for %%I in ("%TARGET%") do set "TARGET_FULL=%%~fI"
set "SETUP_DIR_NOSLASH=%SETUP_DIR:~0,-1%"
if /i "!TARGET_FULL!"=="!SETUP_DIR_NOSLASH!" (
  for %%I in ("%SCRIPT_DIR%.") do set "TARGET=%%~fI"
  echo.
  echo [INFO] Setup 폴더가 target 으로 지정됨. Kit root 로 자동 변경:
  echo        !SETUP_DIR_NOSLASH! ^=^> !TARGET!
  echo.
)

if not exist "%TARGET%" mkdir "%TARGET%" >nul 2>&1

echo.
echo ============================================================
echo   Orchestration Kit Setup
echo ============================================================
echo   Mode   : !MODE!
echo   Target : %TARGET%
echo   Kit    : %SCRIPT_DIR%
echo ============================================================
echo.

rem ════════════════════════════════════════════════════════
rem  Mode 분기
rem ════════════════════════════════════════════════════════

if /i "!MODE!"=="codex" (
  echo [Codex Standalone Mode] Claude 없이 Codex 만 설치
  echo [STEP] install_codex %TIME% >> "!LOGFILE!"
  call "%SCRIPT_DIR%install_codex.bat" "%TARGET%"
  set ERR=!ERRORLEVEL!
  goto MODE_DONE
)

if /i "!MODE!"=="gemini" (
  echo [Gemini Standalone Mode] Claude 없이 Gemini 만 설치
  echo [STEP] install_gemini %TIME% >> "!LOGFILE!"
  call "%SCRIPT_DIR%install_gemini.bat" "%TARGET%"
  set ERR=!ERRORLEVEL!
  goto MODE_DONE
)

rem ════════════════════════════════════════════════════════
rem  Full Mode (Claude+Codex+Gemini)
rem ════════════════════════════════════════════════════════

set "MOD=%SETUP_DIR%modules"
set "ERRORS=0"

echo [Step 1/10] Core files...
echo [STEP] 01-core %TIME% >> "!LOGFILE!"
call "%MOD%\01-core.bat" "%TARGET%" "%SCRIPT_DIR%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 2/10] Defender exclusion...
echo [STEP] 02-defender %TIME% >> "!LOGFILE!"
call "%MOD%\02-defender.bat" "!REAL_USERPROFILE!"
if errorlevel 1 set /a ERRORS+=1

echo [Step 3/10] Settings...
echo [STEP] 03-settings %TIME% >> "!LOGFILE!"
call "%MOD%\03-settings.bat" "!REAL_USERPROFILE!" "%TARGET%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 4/10] Global commands...
echo [STEP] 04-commands %TIME% >> "!LOGFILE!"
call "%MOD%\04-commands.bat" "%TARGET%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 5/10] Services...
echo [STEP] 05-services %TIME% >> "!LOGFILE!"
call "%MOD%\05-services.bat" "%TARGET%" "%SCRIPT_DIR%" "!REAL_USERPROFILE!"
if errorlevel 1 set /a ERRORS+=1

echo [Step 6/10] Prerequisites (Node.js, Claude, Cloudflared)...
echo [STEP] 06-prereqs %TIME% >> "!LOGFILE!"
call "%MOD%\06-prereqs.bat"
if errorlevel 1 set /a ERRORS+=1

echo [Step 7/10] GitHub setup...
echo [STEP] 07-github %TIME% >> "!LOGFILE!"
call "%MOD%\07-github.bat" "%TARGET%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 8/10] Plugins...
echo [STEP] 08-plugins %TIME% >> "!LOGFILE!"
call "%MOD%\08-plugins.bat" "%TARGET%" "%SCRIPT_DIR%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 9/11] Kit Sync (plugins/ to .claude/)...
echo [STEP] 12-kit-sync %TIME% >> "!LOGFILE!"
call "%MOD%\12-kit-sync.bat" "%TARGET%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 10/11] Finalize...
echo [STEP] 09-finalize %TIME% >> "!LOGFILE!"
call "%MOD%\09-finalize.bat" "%TARGET%" "%ANALYZE_MODE%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 11/12] Media Enhance Dependencies...
echo [STEP] 11-media-enhance %TIME% >> "!LOGFILE!"
call "%MOD%\11-media-enhance.bat" "%TARGET%"
if errorlevel 1 set /a ERRORS+=1

echo [Step 12/12] ClaudeTalkToFigma MCP...
echo [STEP] 14-mcp-figma %TIME% >> "!LOGFILE!"
call "%MOD%\14-mcp-figma.bat"
if errorlevel 1 set /a ERRORS+=1

set "ERR=!ERRORS!"
goto MODE_DONE

rem ════════════════════════════════════════════════════════
rem  Common end
rem ════════════════════════════════════════════════════════

:MODE_DONE
echo.
echo ============================================================
if "!MODE!"=="full" (
  if "!ERR!"=="0" ( echo   Setup Complete (Full)! No errors. ) else ( echo   Setup Complete with !ERR! warning^(s^). )
) else (
  echo   Setup Complete (Mode: !MODE!)
)
echo   Log: %TEMP%\orchestration-setup.log
echo ============================================================
echo.
echo   Mode 별 사용법:
if /i "!MODE!"=="codex"  echo     cd /d "%TARGET%" ^&^& codex-go "회원가입 페이지 만들어줘"
if /i "!MODE!"=="gemini" echo     cd /d "%TARGET%" ^&^& gemini-go "이 코드 검증해줘"
if /i "!MODE!"=="full"   echo     cd /d "%TARGET%" ^&^& claude
echo.
echo [DONE] %TIME% >> "!LOGFILE!"
pause
endlocal
exit /b 0
