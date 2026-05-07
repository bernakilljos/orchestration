@echo off
rem =====================================================
rem Module 14: ClaudeTalkToFigma MCP 등록
rem npx 런타임 기반 (로컬 clone 불필요) — claude mcp add 만 실행
rem Usage: 14-mcp-figma.bat
rem =====================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   ClaudeTalkToFigma MCP Registration
echo ============================================================

where claude >nul 2>&1
if errorlevel 1 (
  echo [SKIP] claude not found - run setup again after Claude Code install
  endlocal
  exit /b 0
)

where npx >nul 2>&1
if errorlevel 1 (
  echo [SKIP] npx not found - install Node.js first
  endlocal
  exit /b 0
)

rem --- 이미 등록되어 있으면 skip ---
claude mcp list 2>nul | findstr /I /C:"ClaudeTalkToFigma" >nul 2>&1
if not errorlevel 1 (
  echo [OK] ClaudeTalkToFigma already registered
  endlocal
  exit /b 0
)

rem --- 등록 ---
echo [+] Adding ClaudeTalkToFigma MCP...
call claude mcp add ClaudeTalkToFigma -- npx -p claude-talk-to-figma-mcp@latest claude-talk-to-figma-mcp-server >nul 2>&1
if errorlevel 1 (
  echo [WARN] MCP registration failed - run manually:
  echo        claude mcp add ClaudeTalkToFigma -- npx -p claude-talk-to-figma-mcp@latest claude-talk-to-figma-mcp-server
) else (
  echo [OK] ClaudeTalkToFigma MCP registered
)

echo [Module 14] ClaudeTalkToFigma MCP done
endlocal
exit /b 0
