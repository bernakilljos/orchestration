@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem installcodex.bat — 지정 경로에 Codex 환경 세팅
rem
rem 사용법:
rem   installcodex C:\work\myproject
rem   installcodex .
rem
rem 수행 내용:
rem   1. 대상 폴더에 .claude/tasks/ 구조 생성
rem   2. AGENTS.md 복사 (Codex 지시서)
rem   3. .codex/config.toml 복사 (MCP 설정)
rem   4. codex-auto.bat 복사 (워커 실행파일)
rem   5. orca-workers-config.json 복사 (워커 수 설정)
rem   6. task-instruction.md 빈 템플릿 생성
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: installcodex C:\work\myproject
  exit /b 1
)

rem 상대경로 → 절대경로 변환
if not "%TARGET:~0,1%"=="C" if not "%TARGET:~0,1%"=="D" if not "%TARGET:~0,1%"=="E" (
  if "%TARGET%"=="." set "TARGET=%CD%"
)

echo.
echo ============================================================
echo   Codex 환경 설치: %TARGET%
echo ============================================================
echo.

rem --- 폴더 생성 ---
echo [1/6] 폴더 구조 생성...
for %%D in (
  ".claude"
  ".claude\tasks"
  ".claude\tasks\locks"
  ".claude\tasks\done"
  ".claude\state"
  ".codex"
  "docs"
) do (
  if not exist "%TARGET%\%%D" (
    mkdir "%TARGET%\%%D" >nul 2>&1
    echo       created: %%D
  ) else (
    echo       [OK] %%D
  )
)

rem --- AGENTS.md 복사 ---
echo [2/6] AGENTS.md (Codex 지시서) 복사...
if exist "%SCRIPT_DIR%\AGENTS.md" (
  copy /Y "%SCRIPT_DIR%\AGENTS.md" "%TARGET%\AGENTS.md" >nul 2>&1
  echo       [OK] AGENTS.md
) else (
  echo [WARN] AGENTS.md 없음 - 건너뜀
)

rem --- .codex/config.toml 복사 ---
echo [3/6] .codex\config.toml (MCP 설정) 복사...
if exist "%SCRIPT_DIR%\.codex\config.toml" (
  copy /Y "%SCRIPT_DIR%\.codex\config.toml" "%TARGET%\.codex\config.toml" >nul 2>&1
  echo       [OK] .codex\config.toml
) else (
  echo [WARN] .codex\config.toml 없음 - 건너뜀
)

rem --- codex-auto.bat 복사 ---
echo [4/6] codex-auto.bat (워커 실행파일) 복사...
if exist "%SCRIPT_DIR%\codex-auto.bat" (
  copy /Y "%SCRIPT_DIR%\codex-auto.bat" "%TARGET%\codex-auto.bat" >nul 2>&1
  echo       [OK] codex-auto.bat
) else (
  echo [WARN] codex-auto.bat 없음
)

rem --- orca-workers-config.json 복사 ---
echo [5/6] orca-workers-config.json (워커 수 설정) 복사...
if exist "%SCRIPT_DIR%\.claude\orca-workers-config.json" (
  copy /Y "%SCRIPT_DIR%\.claude\orca-workers-config.json" "%TARGET%\.claude\orca-workers-config.json" >nul 2>&1
  echo       [OK] orca-workers-config.json (codex=4, gemini=2, claude=3)
) else (
  rem 직접 생성
  echo {> "%TARGET%\.claude\orca-workers-config.json"
  echo   "workers": {"codex": 4, "gemini": 2, "claude": 3, "local_llm": 1}>> "%TARGET%\.claude\orca-workers-config.json"
  echo }>> "%TARGET%\.claude\orca-workers-config.json"
  echo       [OK] orca-workers-config.json 기본값으로 생성
)

rem --- task-instruction.md 템플릿 생성 ---
echo [6/6] task-instruction.md 빈 템플릿 생성...
if not exist "%TARGET%\.claude\tasks\task-instruction.md" (
  (
    echo # 태스크 제목
    echo.
    echo ## Goal
    echo 구현 목표를 여기에 작성
    echo.
    echo ## Files
    echo - src/파일명.js
    echo.
    echo ## Rules
    echo - 하드코딩 금지
    echo - 기존 파일 전체 재작성 금지
    echo - 상대경로 사용
    echo.
    echo ## Steps
    echo 1. 구현 단계 1
    echo 2. 구현 단계 2
    echo.
    echo ## Expected Output
    echo 완성물 설명
  ) > "%TARGET%\.claude\tasks\task-instruction.md"
  echo       [OK] task-instruction.md
) else (
  echo       [OK] task-instruction.md 이미 존재
)

echo.
echo ============================================================
echo   Codex 환경 설치 완료!
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo   사용법:
echo     cd /d "%TARGET%"
echo     codex-auto 4              병렬 워커 4개로 구현 시작
echo     codex-auto 1              단일 워커 (디버깅용)
echo.
echo   워커 수 설정: .claude\orca-workers-config.json
echo   태스크 작성: .claude\tasks\task-instruction.md
echo   Codex 지시: AGENTS.md
echo   MCP 설정:  .codex\config.toml
echo.

endlocal
exit /b 0
