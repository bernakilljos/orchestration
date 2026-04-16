@echo off
rem =====================================================
rem Module 08: Claude 플러그인 설치
rem Usage: 08-plugins.bat [TARGET] [SCRIPT_DIR]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "SCRIPT_DIR=%~2"

echo.
echo [+] Claude plugins...

where claude >nul 2>&1
if errorlevel 1 (
  echo       [WARN] claude not found - plugins deferred to first run
  goto COPY_GUIDE
)

rem install-plugins.ps1 사용 (TTY 없이 안정적 설치)
if exist "%SCRIPT_DIR%install-plugins.ps1" (
  echo [+] install-plugins.ps1 로 플러그인 설치 중...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install-plugins.ps1" -UserProfile "%USERPROFILE%"
) else (
  rem 폴백: 직접 설치
  echo [+] Fallback 플러그인 설치...
  for %%P in (claude-md-management code-review commit-commands) do (
    powershell -NoProfile -Command ^
      "$p=Start-Process 'claude' -ArgumentList @('plugin','install','%%P') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; ^
       if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
    echo       %%P
  )
)

rem --- Superpowers marketplace + plugin ---
echo [+] Superpowers + community plugins...
echo "!PLUGIN_LIST!" | findstr /C:"superpowers" >nul 2>&1
if errorlevel 1 (
  echo       Adding superpowers marketplace...
  powershell -NoProfile -Command ^
    "$p=Start-Process 'claude' -ArgumentList @('plugin','marketplace','add','obra/superpowers-marketplace') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; ^
     if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  echo       Installing superpowers...
  powershell -NoProfile -Command ^
    "$p=Start-Process 'claude' -ArgumentList @('plugin','install','superpowers@superpowers-marketplace') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; ^
     if($p){if(-not $p.WaitForExit(60000)){$p.Kill()}}" >nul 2>&1
) else (
  echo       [OK] superpowers
)

rem --- Community plugins (누락분만 설치) ---
for %%P in (ui-ux-pro-max everything-claude-code awesome-claude-code get-shit-done) do (
  echo "!PLUGIN_LIST!" | findstr /C:"%%P" >nul 2>&1
  if errorlevel 1 (
    echo       Installing %%P...
    powershell -NoProfile -Command ^
      "$p=Start-Process 'claude' -ArgumentList @('plugin','install','%%P') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; ^
       if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  ) else (
    echo       [OK] %%P
  )
)

:COPY_GUIDE
rem Copy CLAUDE_SETUP_GUIDE.md for first-run MCP setup
if not "%SCRIPT_DIR%"=="" (
  if exist "%SCRIPT_DIR%docs\CLAUDE_SETUP_GUIDE.md" (
    if not "%TARGET%"=="" (
      if not exist "%TARGET%\docs" mkdir "%TARGET%\docs" >nul 2>&1
      copy /Y "%SCRIPT_DIR%docs\CLAUDE_SETUP_GUIDE.md" "%TARGET%\docs\CLAUDE_SETUP_GUIDE.md" >nul 2>&1
      echo       Setup guide copied for first-run MCP config
    )
  )
)

rem --- API Key check ---
echo [+] API Keys...
set "KEY_MISSING=0"
if defined ANTHROPIC_API_KEY (echo       ANTHROPIC_API_KEY = OK) else (echo       [WARN] ANTHROPIC_API_KEY not set & set "KEY_MISSING=1")
if defined OPENAI_API_KEY   (echo       OPENAI_API_KEY   = OK) else (echo       [WARN] OPENAI_API_KEY not set & set "KEY_MISSING=1")
if defined GEMINI_API_KEY   (echo       GEMINI_API_KEY   = OK) else (echo       [WARN] GEMINI_API_KEY not set & set "KEY_MISSING=1")

if "!KEY_MISSING!"=="1" (
  echo.
  echo       Set missing keys:
  echo         setx ANTHROPIC_API_KEY "sk-ant-..."
  echo         setx OPENAI_API_KEY "sk-..."
  echo         setx GEMINI_API_KEY "AI..."
)

echo [Module 08] Plugins OK
endlocal
exit /b 0
