@echo off
REM setup/modules/16-mcp-headroom-claude-mem.bat
REM Headroom (프롬프트 압축 60~95%) + claude-mem (자동 세션 관측) 자동 설치
REM 원칙: Zero-touch · idempotent · 실패 조용
REM 근거: .claude/rules/mcp-integration.md · CLAUDE.md § 3.6-5

setlocal enabledelayedexpansion
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"

echo.
echo [16] Headroom + claude-mem MCP 통합 설치
echo.

REM ===== Headroom (pip) =====
where python >nul 2>&1
if errorlevel 1 (
  echo   [skip] python not found - Headroom install skipped
  goto CLAUDE_MEM
)

python -m pip show headroom-ai >nul 2>&1
if not errorlevel 1 (
  echo   [skip] headroom-ai already installed
) else (
  echo   [install] pip install headroom-ai[all]
  python -m pip install "headroom-ai[all]" --quiet 2>nul
  if errorlevel 1 (
    echo   [warn] headroom-ai install failed - continue
  ) else (
    echo   [ok] headroom-ai installed
  )
)

REM Headroom MCP 자동 등록 (Claude Code + Codex)
where headroom >nul 2>&1
if not errorlevel 1 (
  echo   [register] headroom mcp install
  headroom mcp install >nul 2>&1
  if not errorlevel 1 echo   [ok] Headroom MCP registered
)

:CLAUDE_MEM
REM ===== claude-mem (npx) =====
where npx >nul 2>&1
if errorlevel 1 (
  echo   [skip] npx not found - claude-mem install skipped
  goto DONE
)

REM idempotent 체크: plugin dir 존재
if exist "%USERPROFILE%\.claude\plugins\marketplaces\thedotmack\claude-mem" (
  echo   [skip] claude-mem already installed
) else (
  echo   [install] npx claude-mem install --provider claude
  cmd /c "npx -y claude-mem install --provider claude" >nul 2>&1
  if errorlevel 1 (
    echo   [warn] claude-mem install failed - continue
  ) else (
    echo   [ok] claude-mem installed
  )
)

REM ===== task-observer (Skill · npx) =====
where npx >nul 2>&1
if errorlevel 1 (
  echo   [skip] npx not found - task-observer install skipped
  goto DONE
)

if exist "%TARGET%\.claude\skills\task-observer\SKILL.md" (
  echo   [skip] task-observer already installed
) else (
  echo   [install] npx skills add task-observer
  cmd /c "npx -y skills add rebelytics/one-skill-to-rule-them-all --skill task-observer --agent claude-code" >nul 2>&1
  if errorlevel 1 (
    echo   [warn] task-observer install failed - continue
  ) else (
    echo   [ok] task-observer installed
  )
)

:DONE
REM ===== settings.json SessionStart 확인 (kit sync 후 자동 반영되므로 skip) =====
echo   [note] mcp-autostart.sh is registered via kit sync (12-kit-sync)
echo.
echo [16] Done
exit /b 0
