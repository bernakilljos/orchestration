@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem installcodex.bat — Codex 단독 환경 셋업 (standalone)
rem
rem 용도: Claude 없이 Codex 만으로 작업할 수 있는 환경.
rem        풀 orchestration 은 install.bat (Claude+Codex+Gemini)
rem        오케스트레이션 로직은 plugins/exec_orch/ 에 있음
rem
rem 사용법:
rem   installcodex C:\work\myproject
rem   installcodex .
rem
rem 수행:
rem   1. tasks/ 폴더 + .codex/ 구조 생성 (.claude 의존 없음)
rem   2. AGENTS.md 복사 (Standalone 섹션 포함)
rem   3. .codex/config.toml 복사 (MCP 설정)
rem   4. codex-go.bat 생성 (CLI 단축 — 폴더에서 즉시 실행)
rem   5. tasks/task-template.md (수동 작업 의뢰용)
rem
rem 작업 방식:
rem   (A) tasks/ 에 task-NNN.md 작성 → codex-a --auto 가 자동 처리
rem   (B) codex-go     → 일반 대화 모드 (task 파일 없이)
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: installcodex C:\work\myproject
  exit /b 1
)

if "%TARGET%"=="." set "TARGET=%CD%"

echo.
echo ============================================================
echo   Codex Standalone 환경 설치: %TARGET%
echo ============================================================
echo   ※ Claude 없이 Codex 단독으로 작업 가능
echo   ※ 풀 orchestration 원하면 install.bat 사용
echo.

rem --- 폴더 ---
echo [1/5] 폴더 구조...
for %%D in (
  ".codex"
  "tasks"
  "tasks\done"
  "docs"
) do (
  if not exist "%TARGET%\%%D" (
    mkdir "%TARGET%\%%D" >nul 2>&1
    echo       created: %%D
  ) else (
    echo       [OK] %%D
  )
)

rem --- AGENTS.md ---
echo [2/5] AGENTS.md (Codex 지시서 — Standalone 모드 포함)...
if exist "%SCRIPT_DIR%\AGENTS.md" (
  copy /Y "%SCRIPT_DIR%\AGENTS.md" "%TARGET%\AGENTS.md" >nul 2>&1
  echo       [OK] AGENTS.md
) else (
  echo [WARN] AGENTS.md 없음
)

rem --- .codex/config.toml ---
echo [3/5] .codex\config.toml (MCP 설정)...
if exist "%SCRIPT_DIR%\.codex\config.toml" (
  copy /Y "%SCRIPT_DIR%\.codex\config.toml" "%TARGET%\.codex\config.toml" >nul 2>&1
  echo       [OK] .codex\config.toml
) else (
  echo [WARN] .codex\config.toml 없음
)

rem --- codex-go.bat (CLI 단축) ---
echo [4/5] codex-go.bat (대화 모드 단축)...
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo rem codex-go - 이 폴더에서 codex CLI 대화 모드 시작
  echo set "PROJECT_ROOT=%%~dp0"
  echo if "%%PROJECT_ROOT:~-1%%"=="\" set "PROJECT_ROOT=%%PROJECT_ROOT:~0,-1%%"
  echo cd /d "%%PROJECT_ROOT%%"
  echo where codex ^>nul 2^>^&1 ^|^| ^(echo [ERROR] codex CLI 미설치 ^& exit /b 1^)
  echo codex %%*
) > "%TARGET%\codex-go.bat"
echo       [OK] codex-go.bat

rem --- tasks/task-template.md ---
echo [5/5] tasks\task-template.md (의뢰용 템플릿)...
if not exist "%TARGET%\tasks\task-template.md" (
  (
    echo # 태스크 제목
    echo.
    echo ^> 사용법: 이 파일을 복사해 task-001.md, task-002.md 등으로 저장.
    echo ^> 그러면 codex-a --auto 가 자동 처리. 또는 codex-go 로 대화 모드.
    echo.
    echo ## Goal
    echo 무엇을 만들지 한 줄
    echo.
    echo ## Files
    echo - src/파일명.js
    echo - tests/파일명.test.js
    echo.
    echo ## Rules
    echo - 하드코딩 금지 ^(경로·포트·도메인 → 환경변수^)
    echo - 서버 파일 한글 문자열 금지
    echo - 기존 파일 전체 재작성 금지 — 필요 부분만 수정
    echo - optional chaining ^(`?.`^) 금지
    echo.
    echo ## Steps
    echo 1. 단계 1
    echo 2. 단계 2
    echo.
    echo ## Expected Output
    echo 완성물 설명
  ) > "%TARGET%\tasks\task-template.md"
  echo       [OK] tasks\task-template.md
) else (
  echo       [OK] tasks\task-template.md 이미 존재
)

echo.
echo ============================================================
echo   Codex Standalone 환경 설치 완료
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo   사용법 두 가지:
echo.
echo   (A) Task 파일 자동 처리:
echo       cp tasks\task-template.md tasks\task-001.md   ^(편집^)
echo       codex-a --auto
echo.
echo   (B) 대화 모드:
echo       cd /d "%TARGET%"
echo       codex-go        ^(이 폴더에서 codex CLI 실행^)
echo.
echo   파일:
echo     AGENTS.md            Codex 지시서 ^(Standalone 섹션 포함^)
echo     .codex\config.toml   MCP 설정
echo     tasks\                작업 의뢰 폴더
echo     tasks\done\           완료 보관
echo.

endlocal
exit /b 0
