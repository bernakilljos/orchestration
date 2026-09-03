@echo off
REM 17-community-standards - 2026 커뮤니티 표준 6개 자동 설치 (WebSearch 2026-09-03)
REM 근거: Effective Claude Code Workflows in 2026 · Firecrawl · Anthropic 공식 skills
REM 대상: 새 프로젝트 install 시 자동 반영

echo [17] Community standards install...

REM 1. Firecrawl MCP (dev 중 웹 리서치 자동)
where npx >nul 2>&1
if %ERRORLEVEL%==0 (
  echo   - Firecrawl MCP registration...
  claude mcp add firecrawl -- cmd /c npx -y firecrawl-mcp 2>nul
)

REM 2. Anthropic 공식 Frontend Design skill
if not exist "%USERPROFILE%\.claude\skills\frontend-design" (
  echo   - Frontend Design skill install...
  claude plugin install anthropics/skills#frontend-design 2>nul
)

REM 3. React Best Practices skill
if not exist "%USERPROFILE%\.claude\skills\react-best-practices" (
  echo   - React Best Practices skill install...
  claude plugin install anthropics/skills#react-best-practices 2>nul
)

REM 4. /go command (plan-then-build) - kit 안에 이미 있음 · sync 로 복사
if exist "%CD%\.claude\scripts\sync-plugins.sh" (
  bash "%CD%\.claude\scripts\sync-plugins.sh" 2>nul
)

REM 5. git worktree - built-in EnterWorktree tool · 별도 설치 X

REM 6. Skills = slash commands 통합 - Anthropic v2.1+ default · 별도 설치 X

echo [17] Community standards done.
exit /b 0
