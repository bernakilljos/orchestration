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
rem 강화: /R:3 /W:5 재시도 + log
robocopy "%SCRIPT_DIR%.claude" "%TARGET%\.claude" /E /R:3 /W:5 /NFL /NDL /NJH /NJS /NP /LOG:"%TEMP%\install-claude.log" >nul 2>&1
if exist "%SCRIPT_DIR%CLAUDE.md" copy /Y "%SCRIPT_DIR%CLAUDE.md" "%TARGET%\CLAUDE.md" >nul

rem --- Plugin manifest (.claude-plugin/) ---
if exist "%SCRIPT_DIR%.claude-plugin" (
  if not exist "%TARGET%\.claude-plugin" mkdir "%TARGET%\.claude-plugin"
  robocopy "%SCRIPT_DIR%.claude-plugin" "%TARGET%\.claude-plugin" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       .claude-plugin/ copied
)

rem --- Local plugins (exec_*, design_*, mcp_*, review_*, exec_session_guard 등) ---
rem 강화: /R:3 /W:5 (locked file 재시도) + log + 사후 검증 + 누락 시 재시도
if exist "%SCRIPT_DIR%plugins" (
  if not exist "%TARGET%\plugins" mkdir "%TARGET%\plugins"
  set "ROBOCOPY_LOG=%TEMP%\install-plugins.log"
  robocopy "%SCRIPT_DIR%plugins" "%TARGET%\plugins" /E /R:3 /W:5 /NFL /NDL /NJH /NJS /NP /LOG:"!ROBOCOPY_LOG!" >nul 2>&1

  rem --- 사후 검증: orch 와 target 파일 갯수 비교 ---
  set "SRC_COUNT=0"
  set "DST_COUNT=0"
  for /f %%C in ('dir "%SCRIPT_DIR%plugins" /S /B /A:-D 2^>nul ^| find /C /V ""') do set "SRC_COUNT=%%C"
  for /f %%C in ('dir "%TARGET%\plugins" /S /B /A:-D 2^>nul ^| find /C /V ""') do set "DST_COUNT=%%C"

  if !DST_COUNT! LSS !SRC_COUNT! (
    echo       [WARN] plugins/ 일부 누락 ^(src=!SRC_COUNT! dst=!DST_COUNT!^) - 재시도
    robocopy "%SCRIPT_DIR%plugins" "%TARGET%\plugins" /E /R:5 /W:10 /NFL /NDL /NJH /NJS /NP /LOG+:"!ROBOCOPY_LOG!" >nul 2>&1
    for /f %%C in ('dir "%TARGET%\plugins" /S /B /A:-D 2^>nul ^| find /C /V ""') do set "DST_COUNT=%%C"
    if !DST_COUNT! LSS !SRC_COUNT! (
      echo       [WARN] 재시도 후에도 부족 ^(src=!SRC_COUNT! dst=!DST_COUNT!^) - 로그: !ROBOCOPY_LOG!
    ) else (
      echo       plugins/ copied ^(재시도 OK, src=!SRC_COUNT! dst=!DST_COUNT!^)
    )
  ) else (
    echo       plugins/ copied ^(src=!SRC_COUNT! dst=!DST_COUNT!^)
  )

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

rem --- Sanity check: 핵심 hook 파일 누락 검출 + 개별 재시도 ---
rem 사용자가 settings.json 의 hook 경로 No such file 에러 보지 않도록 사전 검증
echo [Sanity] 핵심 hook 파일 검증...
set "MISSING_COUNT=0"
for %%H in (
  "plugins\exec_session_guard\hooks\auto-compact-check.sh"
  "plugins\exec_session_guard\hooks\outbox-write.sh"
  "plugins\exec_session_guard\hooks\stop-snapshot.sh"
  "plugins\exec_session_guard\hooks\process-outbox.sh"
  "plugins\exec_session_guard\hooks\cleanup-orphans.sh"
  "plugins\exec_session_guard\hooks\hook-token-log.sh"
  "plugins\exec_session_guard\hooks\hook-gemini-recap.sh"
  "plugins\exec_orch\hooks\hook-00-init.sh"
  "plugins\exec_orch\hooks\hook-08-ai-handoff.sh"
  "plugins\exec_orch\hooks\hook-01-pre-task.sh"
  "plugins\exec_orch\hooks\install-external-watchdog.sh"
  "plugins\exec_orch\hooks\pre-build-reminder.sh"
  "plugins\exec_learning\hooks\hook-worker-failure.sh"
) do (
  if not exist "%TARGET%\%%~H" (
    if exist "%SCRIPT_DIR%%%~H" (
      for %%D in ("%TARGET%\%%~H") do if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
      copy /Y "%SCRIPT_DIR%%%~H" "%TARGET%\%%~H" >nul 2>&1
      if exist "%TARGET%\%%~H" (
        echo       [복원] %%~H
      ) else (
        echo       [실패] %%~H
        set /a MISSING_COUNT+=1
      )
    ) else (
      echo       [원본없음] %%~H
      set /a MISSING_COUNT+=1
    )
  )
)
if !MISSING_COUNT! GTR 0 (
  echo       [WARN] !MISSING_COUNT! 개 hook 파일 복원 실패 - settings.json No such file 에러 가능
) else (
  echo       [OK] 핵심 hook 13개 모두 존재
)
echo       Done

echo [Module 01] Core files installed OK
endlocal
exit /b 0
