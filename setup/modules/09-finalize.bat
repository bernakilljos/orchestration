@echo off
rem =====================================================
rem Module 09: 프로젝트 초기화, npm install, Claude 실행
rem Usage: 09-finalize.bat [TARGET] [ANALYZE_MODE]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
set "ANALYZE_MODE=%~2"
if "%TARGET%"=="" echo [ERROR] TARGET required & exit /b 1

echo.
echo ============================================================
echo   Finalize
echo ============================================================

rem --- init.bat ---
if exist "%TARGET%\.claude\scripts\init.bat" (
  echo [+] Running project init...
  call "%TARGET%\.claude\scripts\init.bat" "%TARGET%"
) else (
  echo       init.bat not found - skipped
)

rem --- Source analysis (optional) ---
if /i "%ANALYZE_MODE%"=="true" (
  if exist "%TARGET%\.claude\scripts\analyze.bat" (
    echo [+] Running source analysis...
    call "%TARGET%\.claude\scripts\analyze.bat" "%TARGET%"
  )
)

rem --- npm install ---
if exist "%TARGET%\package.json" (
  echo [+] Installing project dependencies...
  cd /d "%TARGET%"
  call npm install
  echo       Done
)

echo.
echo ============================================================
echo   Installation Complete! — Orchestration Kit v1.0
echo ============================================================
echo.
echo   Target: %TARGET%
echo.
echo   AI 명칭 정리:
echo     codex-a      단일 태스크 실행
echo     codex-auto   병렬 구현 워커 (기본 4개)
echo     gemini-a     단일 검증 실행
echo     gemini-auto  병렬 검증 워커 (기본 2개)
echo     claude-auto  Claude 병렬 워커 (기본 3개)
echo.

where claude >nul 2>&1
if errorlevel 1 (
  echo   [WARN] claude not found in PATH
  echo          Install: https://claude.ai/download/cli
  echo          Then run:
  echo            cd /d "%TARGET%"
  echo            claude --dangerously-skip-permissions
  goto END
)

rem --- Local LLM 감지 및 설정 ---
echo [+] Local LLM 감지 중...
set "LOCAL_LLM_TYPE=null"
where ollama >nul 2>&1 && set "LOCAL_LLM_TYPE=ollama"
if "!LOCAL_LLM_TYPE!"=="null" where lms >nul 2>&1 && set "LOCAL_LLM_TYPE=lm-studio"
if "!LOCAL_LLM_TYPE!"=="null" where llamafile >nul 2>&1 && set "LOCAL_LLM_TYPE=llamafile"

if not "!LOCAL_LLM_TYPE!"=="null" (
  echo       감지됨: !LOCAL_LLM_TYPE!
  echo       로컬 LLM 워커를 활성화할까요? (10초 후 자동 N)
  choice /c YN /n /m "  [Y/N]: " /t 10 /d N
  if errorlevel 2 (
    echo       [SKIP] 로컬 LLM 비활성화
  ) else (
    powershell -NoProfile -Command "$cfg = Get-Content '%TARGET%\.claude\orca-workers-config.json' | ConvertFrom-Json; $cfg.local_llm.type = '!LOCAL_LLM_TYPE!'; $cfg | ConvertTo-Json -Depth 5 | Set-Content '%TARGET%\.claude\orca-workers-config.json'"
    echo       [OK] orca-workers-config.json 업데이트됨
  )
) else (
  echo       로컬 LLM 없음 - 나중에 설치 후 .claude\orca-workers-config.json 에서 설정 가능
)

echo.
echo ============================================================
echo   추가 MCP 설치 (Claude 실행 후 슬래시 커맨드로)
echo ============================================================
echo.
echo   /plug_dev     GitHub, Docker, AWS, Firebase, Vercel...  개발/배포 자동화
echo   /plug_data    MySQL, MongoDB, BigQuery, Sheets...       데이터 분석/리포트
echo   /plug_design  Canva, Figma, Gamma, Mermaid...           슬라이드/다이어그램
echo   /plug_collab  Slack, Notion, Jira, Gmail...             협업/알림 자동화
echo   /plug_web     Playwright, Puppeteer, Apify...           크롤링/웹 자동화
echo   /plug_docs    PDF, DOCX, OCR...                         문서 처리/분석
echo   /plug_media   Whisper, TTS, FFmpeg...                   음성/영상 처리
echo   /plug_all     위 전체 한 번에 설치
echo.
echo   기본 MCP (이미 설치됨): context7, playwright, thinking
echo   자동 연결 (claude.ai): Figma, Gamma, Gmail, Canva, Mermaid
echo ============================================================
echo.
echo   Start Claude now? (15초 후 자동 N)
echo     [Y] Yes - launch Claude
echo     [N] No  - exit
echo.
choice /c YN /n /m "Select [Y/N]: " /t 15 /d N
if errorlevel 2 goto END
cd /d "%TARGET%"
echo [OK] Starting claude...
claude --dangerously-skip-permissions

:END
echo [Module 09] Finalize OK
endlocal
exit /b 0
