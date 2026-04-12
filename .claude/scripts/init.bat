@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem init.bat - Project first-time setup (Windows)
rem Usage: .claude\scripts\init.bat [project-path]
rem =====================================================

set TARGET=%~1
if "%TARGET%"=="" set TARGET=%CD%
cd /d "%TARGET%" 2>nul

echo.
echo ==============================
echo  HOOK-00 Init
echo ==============================

rem Create required folders
if not exist "docs\adr"              mkdir "docs\adr"              >nul 2>&1
if not exist "docs\deploy-history"   mkdir "docs\deploy-history"   >nul 2>&1
if not exist ".claude\context-cache" mkdir ".claude\context-cache" >nul 2>&1
if not exist ".claude\tasks"         mkdir ".claude\tasks"         >nul 2>&1
if not exist ".claude\learning"      mkdir ".claude\learning"      >nul 2>&1
echo [OK] Folders ready

rem Copy deploy-config.env if missing
if not exist ".claude\deploy-config.env" (
  if exist ".claude\deploy-config.env.example" (
    copy /Y ".claude\deploy-config.env.example" ".claude\deploy-config.env" >nul 2>&1
    echo [OK] deploy-config.env created - edit server info
  )
) else (
  echo [OK] deploy-config.env exists
)

rem CLI check
echo.
echo === CLI Check ===
where claude   >nul 2>&1 && echo [OK] claude    || echo [X]  claude    - https://docs.anthropic.com/claude-code
where codex    >nul 2>&1 && echo [OK] codex     || echo [X]  codex     - npm install -g @openai/codex
where codex-a  >nul 2>&1 && echo [OK] codex-a   || echo [X]  codex-a   - npm install -g @openai/codex
where gemini   >nul 2>&1 && echo [OK] gemini    || echo [X]  gemini    - npm install -g @google/gemini-cli
where gemini-a >nul 2>&1 && echo [OK] gemini-a  || echo [X]  gemini-a  - npm install -g @google/gemini-cli
where git      >nul 2>&1 && echo [OK] git       || echo [X]  git       - https://git-scm.com

echo.
echo [DONE] Init complete
endlocal
