@echo off
rem =====================================================
rem Module 01: Core Files - .claude 폴더 복사, 디렉토리 생성
rem Usage: 01-core.bat [TARGET] [SCRIPT_DIR]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "SCRIPT_DIR=%~2"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1
if "%SCRIPT_DIR%"=="" echo [ERROR] SCRIPT_DIR required & exit /b 1

echo.
echo [1/4] Backup existing .claude...
if exist "%TARGET%\.claude" (
  set BNAME=.claude_backup_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
  set BNAME=!BNAME: =0!
  robocopy "%TARGET%\.claude" "%TARGET%\!BNAME!" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       Backed up to !BNAME!
) else (
  echo       Fresh install
)

echo [2/4] Installing .claude folder + plugin manifest + local plugins...
if not exist "%TARGET%\.claude" mkdir "%TARGET%\.claude"
robocopy "%SCRIPT_DIR%.claude" "%TARGET%\.claude" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
if exist "%SCRIPT_DIR%CLAUDE.md" copy /Y "%SCRIPT_DIR%CLAUDE.md" "%TARGET%\CLAUDE.md" >nul

rem --- Plugin manifest (.claude-plugin/) ---
if exist "%SCRIPT_DIR%.claude-plugin" (
  if not exist "%TARGET%\.claude-plugin" mkdir "%TARGET%\.claude-plugin"
  robocopy "%SCRIPT_DIR%.claude-plugin" "%TARGET%\.claude-plugin" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       .claude-plugin/ copied
)

rem --- Local plugins (exec_*, design_*, mcp_*, review_*, exec_session_guard 등) ---
if exist "%SCRIPT_DIR%plugins" (
  if not exist "%TARGET%\plugins" mkdir "%TARGET%\plugins"
  robocopy "%SCRIPT_DIR%plugins" "%TARGET%\plugins" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       plugins/ copied
)
echo       Done

echo [3/4] Creating project folders...
for %%D in (docs\adr docs\deploy-history docs\screens context templates outputs) do (
  if not exist "%TARGET%\%%D" mkdir "%TARGET%\%%D" >nul 2>&1
)
rem Copy design screens
if exist "%SCRIPT_DIR%docs\screens" (
  for %%F in ("%SCRIPT_DIR%docs\screens\*.*") do (
    if not exist "%TARGET%\docs\screens\%%~nxF" copy /Y "%%F" "%TARGET%\docs\screens\%%~nxF" >nul 2>&1
  )
)
rem Copy sample files
for %%P in (context\rules.md context\project.md templates\prd-template.md templates\api-template.md templates\screen-template.md outputs\result-sample.md) do (
  if exist "%SCRIPT_DIR%%%P" if not exist "%TARGET%\%%P" copy /Y "%SCRIPT_DIR%%%P" "%TARGET%\%%P" >nul 2>&1
)
echo       Done

echo [4/4] Configuring deploy-config and .gitignore...
if not exist "%TARGET%\.claude\deploy-config.env" (
  if exist "%TARGET%\.claude\deploy-config.env.example" (
    copy /Y "%TARGET%\.claude\deploy-config.env.example" "%TARGET%\.claude\deploy-config.env" >nul 2>&1
    echo       deploy-config.env created
  )
)
if not exist "%TARGET%\.gitignore" echo.> "%TARGET%\.gitignore"
findstr /C:".claude/deploy-config.env" "%TARGET%\.gitignore" >nul 2>&1 || (
  echo .claude/deploy-config.env>> "%TARGET%\.gitignore"
  echo .claude/context-cache/>> "%TARGET%\.gitignore"
  echo docs/secret-scan.txt>> "%TARGET%\.gitignore"
  echo docs/build-result.txt>> "%TARGET%\.gitignore"
)
echo       Done

echo [Module 01] Core files installed OK
endlocal
exit /b 0
