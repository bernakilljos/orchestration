@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem installgemini.bat — Gemini 단독 환경 셋업 (standalone)
rem
rem 용도: Claude 없이 Gemini 만으로 작업할 수 있는 환경.
rem        검증·문서화 뿐 아니라 일반 작업도 Gemini 단독 수행.
rem
rem 사용법:
rem   installgemini C:\work\myproject
rem   installgemini .
rem
rem 수행:
rem   1. tasks/ 폴더 + .gemini/ 구조 생성 (.claude 의존 없음)
rem   2. GEMINI.md 복사 (Standalone 섹션 포함)
rem   3. .gemini/config.toml 복사 (MCP 설정)
rem   4. gemini-go.bat 생성 (CLI 단축 — 폴더에서 즉시 실행)
rem   5. tasks/task-template.md (수동 작업 의뢰용)
rem
rem 작업 방식:
rem   (A) tasks/ 에 task-NNN.md 작성 → gemini-a --auto 가 자동 처리
rem   (B) gemini-go    → 일반 대화 모드 (task 파일 없이)
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: installgemini C:\work\myproject
  exit /b 1
)

if "%TARGET%"=="." set "TARGET=%CD%"

echo.
echo ============================================================
echo   Gemini Standalone 환경 설치: %TARGET%
echo ============================================================
echo   ※ Claude 없이 Gemini 단독으로 작업 가능
echo.

rem --- 폴더 ---
echo [1/5] 폴더 구조...
for %%D in (
  ".gemini"
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

rem --- GEMINI.md ---
echo [2/5] GEMINI.md (Gemini 지시서 — Standalone 모드 포함)...
if exist "%SCRIPT_DIR%\GEMINI.md" (
  copy /Y "%SCRIPT_DIR%\GEMINI.md" "%TARGET%\GEMINI.md" >nul 2>&1
  echo       [OK] GEMINI.md
) else (
  echo [WARN] GEMINI.md 없음
)

rem --- .gemini/config.toml ---
echo [3/5] .gemini\config.toml (MCP 설정)...
if exist "%SCRIPT_DIR%\.gemini\config.toml" (
  copy /Y "%SCRIPT_DIR%\.gemini\config.toml" "%TARGET%\.gemini\config.toml" >nul 2>&1
  echo       [OK] .gemini\config.toml
) else (
  echo [WARN] .gemini\config.toml 없음
)

rem --- gemini-go.bat (CLI 단축) ---
echo [4/5] gemini-go.bat (대화 모드 단축)...
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo rem gemini-go - 이 폴더에서 gemini CLI 대화 모드 시작
  echo set "PROJECT_ROOT=%%~dp0"
  echo if "%%PROJECT_ROOT:~-1%%"=="\" set "PROJECT_ROOT=%%PROJECT_ROOT:~0,-1%%"
  echo cd /d "%%PROJECT_ROOT%%"
  echo where gemini ^>nul 2^>^&1 ^|^| ^(echo [ERROR] gemini CLI 미설치 ^& exit /b 1^)
  echo gemini %%*
) > "%TARGET%\gemini-go.bat"
echo       [OK] gemini-go.bat

rem --- tasks/task-template.md ---
echo [5/5] tasks\task-template.md (의뢰용 템플릿)...
if not exist "%TARGET%\tasks\task-template.md" (
  (
    echo # 태스크 제목
    echo.
    echo ^> 사용법: 이 파일을 복사해 task-001.md, task-002.md 등으로 저장.
    echo ^> 그러면 gemini-a --auto 가 자동 처리. 또는 gemini-go 로 대화 모드.
    echo.
    echo ## Goal
    echo 무엇을 할지 한 줄 ^(구현·검증·문서화·요약 모두 가능^)
    echo.
    echo ## Files
    echo - src/파일명.js   ^(검증 대상 또는 수정 대상^)
    echo.
    echo ## Mode
    echo - implement   ^(일반 구현^)
    echo - verify      ^(코드 리뷰·보안·품질 검증^)
    echo - summarize   ^(긴 문서·로그 요약 — 1M 컨텍스트 활용^)
    echo - document    ^(README·docstring·CHANGELOG^)
    echo.
    echo ## Rules
    echo - 하드코딩 금지
    echo - 서버 파일 한글 문자열 금지
    echo - 기존 파일 전체 재작성 금지
    echo - optional chaining ^(`?.`^) 금지
    echo.
    echo ## Expected Output
    echo - implement → 수정된 파일
    echo - verify    → tasks\done\TASK-ID-review.md ^(PASS/FAIL + 이슈^)
    echo - summarize → docs\summary-^<topic^>.md
    echo - document  → README.md 등 갱신
  ) > "%TARGET%\tasks\task-template.md"
  echo       [OK] tasks\task-template.md
) else (
  echo       [OK] tasks\task-template.md 이미 존재
)

echo.
echo ============================================================
echo   Gemini Standalone 환경 설치 완료
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo   사용법 두 가지:
echo.
echo   (A) Task 파일 자동 처리:
echo       cp tasks\task-template.md tasks\task-001.md   ^(편집^)
echo       gemini-a --auto
echo.
echo   (B) 대화 모드:
echo       cd /d "%TARGET%"
echo       gemini-go       ^(이 폴더에서 gemini CLI 실행^)
echo.
echo   파일:
echo     GEMINI.md             Gemini 지시서 ^(Standalone 섹션 포함^)
echo     .gemini\config.toml   MCP 설정
echo     tasks\                 작업 의뢰 폴더
echo     tasks\done\            완료 보관
echo.

endlocal
exit /b 0
