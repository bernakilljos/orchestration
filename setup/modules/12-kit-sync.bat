@echo off
rem =====================================================
rem Module 12: Orchestration Kit 플러그인 sync + 검증
rem Usage: 12-kit-sync.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"

echo.
echo [+] Orchestration Kit sync...

pushd "%TARGET%" 2>nul || (
  echo       [WARN] target not found: %TARGET%
  goto END
)

rem --- Git Bash 확인 ---
where bash >nul 2>&1
if errorlevel 1 (
  echo       [WARN] bash 없음 - Git for Windows 필요
  echo       수동 sync: bash .claude/scripts/sync-plugins.sh
  goto POPD_END
)

rem --- sync 실행 ---
if exist ".claude\scripts\sync-plugins.sh" (
  echo       plugins/ to .claude/ 동기화...
  bash .claude/scripts/sync-plugins.sh 2>nul | findstr /R "Summary copied skipped renamed orphan"
  echo.
  echo       [내장 코어 플러그인]
  echo         exec_orch    멀티AI 라우팅 (Claude+Codex+Gemini)
  echo         exec_claude  Claude 깊이 활용 (NEW 2026-04-23)
  echo                       /claude-status  /claude-ask  /claude-artifact
  echo                       /claude-connectors  /claude-thinking
  echo       [신규 다이어그램 커맨드]
  echo         /arch-mindmap /arch-layered /arch-cheatsheet /arch-auto
  echo       [R51 디자인 도구 (2026-04-30)]
  echo         /design_ppt   PPT 자동 생성 (HTML -^> Playwright -^> PPTX)
  echo         /pdf-generate PDF 자동 생성 (A4/Letter/Digital 1920x1080)
  echo         render-screens.py  단일 PNG (README 표지/마케팅 카드)
  echo         차트 + SVG 다이어그램 + 카드 그리드 4 패턴 표준화
) else (
  echo       [WARN] sync-plugins.sh 없음
)

rem --- 스키마 검증 ---
where python >nul 2>&1
if not errorlevel 1 (
  if exist ".claude\scripts\validate-plugin-schema.py" (
    echo       plugin.json 스키마 검증...
    python .claude/scripts/validate-plugin-schema.py 2>nul | findstr /R "통과 오류 경고"
  )
)

rem --- 전역 orca 큐 초기화 ---
if not exist "%USERPROFILE%\.claude\orca\tasks" (
  echo       전역 orca 큐 초기화...
  mkdir "%USERPROFILE%\.claude\orca\tasks" 2>nul
  mkdir "%USERPROFILE%\.claude\orca\done" 2>nul
  mkdir "%USERPROFILE%\.claude\orca\locks" 2>nul
  mkdir "%USERPROFILE%\.claude\orca\logs" 2>nul
  if not exist "%USERPROFILE%\.claude\orca\workers-config.json" (
    > "%USERPROFILE%\.claude\orca\workers-config.json" echo {"max_workers":{"codex":4,"gemini":2,"claude":2},"heartbeat_interval_sec":30}
  )
)

:POPD_END
popd

:END
echo [Module 12] Kit sync OK
endlocal
exit /b 0
