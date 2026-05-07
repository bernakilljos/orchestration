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

  rem --- Fanout: plugins/*/commands|skills|agents|hooks → .claude/{commands,skills,agents,hooks} ---
  rem Claude Code는 .claude/ 하위만 읽으므로 plugin 자산을 중복 복사 (plugins/ 는 마스터 보관)
  rem 이름 충돌 방지: 여러 플러그인이 같은 파일명(make.md/status.md/install.md)을 쓰는 경우
  rem → plugin명 접두사로 리네임 (예: design_excel/make.md → excel-make.md, mcp_dev/install.md → mcp_dev-install.md)
  if not exist "%TARGET%\.claude\commands" mkdir "%TARGET%\.claude\commands"
  if not exist "%TARGET%\.claude\skills" mkdir "%TARGET%\.claude\skills"
  if not exist "%TARGET%\.claude\agents" mkdir "%TARGET%\.claude\agents"
  if not exist "%TARGET%\.claude\hooks" mkdir "%TARGET%\.claude\hooks"

  for /d %%P in ("%TARGET%\plugins\*") do (
    set "PLUGIN_NAME=%%~nxP"
    rem 접두사 정규화: design_excel → excel, design_word → word, design_ppt → ppt, exec_voice → voice, mcp_* → mcp_*
    set "PREFIX=!PLUGIN_NAME!"
    if /i "!PLUGIN_NAME!"=="design_excel" set "PREFIX=excel"
    if /i "!PLUGIN_NAME!"=="design_word"  set "PREFIX=word"
    if /i "!PLUGIN_NAME!"=="design_ppt"   set "PREFIX=ppt"
    if /i "!PLUGIN_NAME!"=="exec_voice"   set "PREFIX=voice"

    if exist "%%P\commands" (
      for %%F in ("%%P\commands\*.md") do (
        set "BASENAME=%%~nxF"
        set "DEST=%TARGET%\.claude\commands\!BASENAME!"
        rem 충돌 예상 파일(make/status/install)은 무조건 접두사 붙임
        if /i "!BASENAME!"=="make.md"    set "DEST=%TARGET%\.claude\commands\!PREFIX!-make.md"
        if /i "!BASENAME!"=="status.md"  set "DEST=%TARGET%\.claude\commands\!PREFIX!-status.md"
        if /i "!BASENAME!"=="install.md" set "DEST=%TARGET%\.claude\commands\!PREFIX!-install.md"
        if not exist "!DEST!" copy /Y "%%F" "!DEST!" >nul 2>&1
      )
    )
    if exist "%%P\skills" (
      robocopy "%%P\skills" "%TARGET%\.claude\skills" *.md /NFL /NDL /NJH /NJS /NP /XC /XN /XO >nul 2>&1
    )
    if exist "%%P\agents" (
      robocopy "%%P\agents" "%TARGET%\.claude\agents" *.md /NFL /NDL /NJH /NJS /NP /XC /XN /XO >nul 2>&1
    )
    if exist "%%P\hooks" (
      robocopy "%%P\hooks" "%TARGET%\.claude\hooks" /NFL /NDL /NJH /NJS /NP /XC /XN /XO >nul 2>&1
    )
  )
  echo       plugins/*/{commands,skills,agents,hooks} → .claude/ fanout (네임스페이스 충돌 해결)
)
echo       Done

echo [3/4] Creating project folders...
for %%D in (docs\adr docs\deploy-history docs\screens docs\ini context templates outputs) do (
  if not exist "%TARGET%\%%D" mkdir "%TARGET%\%%D" >nul 2>&1
)
rem Copy design screens
if exist "%SCRIPT_DIR%docs\screens" (
  for %%F in ("%SCRIPT_DIR%docs\screens\*.*") do (
    if not exist "%TARGET%\docs\screens\%%~nxF" copy /Y "%%F" "%TARGET%\docs\screens\%%~nxF" >nul 2>&1
  )
)
rem Copy docs/ini/ — 내부 PC 전용 (PAT 등)
if exist "%SCRIPT_DIR%docs\ini" (
  for %%F in ("%SCRIPT_DIR%docs\ini\*.*") do (
    if not exist "%TARGET%\docs\ini\%%~nxF" copy /Y "%%F" "%TARGET%\docs\ini\%%~nxF" >nul 2>&1
  )
)
rem github.ini 없거나 비어있으면 placeholder + PAT 입력 안내
set "INI_VALID=0"
if exist "%TARGET%\docs\ini\github.ini" (
  for /f "tokens=2 delims==" %%A in ('findstr /i "^GITHUB_PAT" "%TARGET%\docs\ini\github.ini" 2^>nul') do (
    set "_PAT_M01=%%A"
    set "_PAT_TRIM=!_PAT_M01: =!"
    if not "!_PAT_TRIM!"=="" if not "!_PAT_TRIM!"=="ghp_YOUR_TOKEN_HERE" set "INI_VALID=1"
  )
)
if "!INI_VALID!"=="1" goto _INI_M01_DONE
(
  echo # GitHub Personal Access Token
  echo # - install/setup 에서 git commit/push 시 사용
  echo # - PAT 발급: https://github.com/settings/tokens ^(scope: repo + workflow^)
  echo.
  echo GITHUB_PAT=ghp_YOUR_TOKEN_HERE
) > "%TARGET%\docs\ini\github.ini"
echo       [!] docs\ini\github.ini 생성됨 — GITHUB_PAT 에 본인 토큰 입력하세요
:_INI_M01_DONE
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
