@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem install_codex.bat — Codex 단독 환경 셋업 (standalone)
rem
rem 용도: Claude 없이 Codex 만으로 작업할 수 있는 환경.
rem        풀 orchestration 은 install.bat (Claude+Codex+Gemini)
rem        오케스트레이션 로직은 plugins/exec_orch/ 에 있음
rem
rem 사용법:
rem   install_codex C:\work\myproject
rem   install_codex .
rem
rem 수행:
rem   1. .codex/ + tasks/ + docs/ 구조 생성 (.claude 의존 없음)
rem   2. AGENTS.md 복사 (Standalone 섹션 포함)
rem   3. .codex/config.toml 복사 (MCP 설정)
rem   4. codex-go.bat 생성 (자연어 한 줄로 즉시 작업)
rem   5. tasks/README.md (배치 사용 시 참고)
rem
rem 설치 후 사용:
rem   codex-go "회원가입 페이지 만들어줘"      ← 자연어 한 줄, 끝
rem   codex-go                                ← 인자 없으면 대화 모드
rem   codex-a --auto                          ← tasks/ 의 task 파일 일괄 처리
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: install_codex C:\work\myproject
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
echo [2/5] AGENTS.md (Codex 지시서)...
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

rem --- codex-go.bat (자연어 한 줄 처리) ---
echo [4/5] codex-go.bat (자연어 → 즉시 작업)...
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo rem codex-go - 자연어 한 줄로 코덱스 실행 ^(또는 인자 없으면 대화 모드^)
  echo rem 사용:  codex-go "회원가입 페이지 만들어줘"
  echo rem        codex-go                       ^(대화 모드^)
  echo set "PROJECT_ROOT=%%~dp0"
  echo if "%%PROJECT_ROOT:~-1%%"=="\" set "PROJECT_ROOT=%%PROJECT_ROOT:~0,-1%%"
  echo cd /d "%%PROJECT_ROOT%%"
  echo where codex ^>nul 2^>^&1 ^|^| ^(echo [ERROR] codex CLI 미설치 ^- npm i -g @openai/codex ^& exit /b 1^)
  echo if "%%~1"=="" ^(
  echo   echo [Codex 대화 모드 시작 - %%CD%%]
  echo   codex
  echo ^) else ^(
  echo   echo [Codex 작업 시작] %%~1
  echo   codex %%*
  echo ^)
) > "%TARGET%\codex-go.bat"
echo       [OK] codex-go.bat

rem --- tasks/README.md (배치 사용 안내) ---
echo [5/5] tasks\README.md (배치 처리 안내)...
if not exist "%TARGET%\tasks\README.md" (
  (
    echo # tasks/ — 배치 작업 폴더 ^(선택^)
    echo.
    echo ## 일반 사용 — 자연어 한 줄
    echo 그냥 이렇게 하면 됨, task 파일 만들 필요 없음:
    echo.
    echo ```
    echo codex-go "회원가입 페이지 만들어줘"
    echo codex-go "이 모듈 리팩토링해줘 — DRY 원칙"
    echo codex-go                           # 대화 모드
    echo ```
    echo.
    echo ## 배치 처리 ^(여러 작업 한꺼번에^)
    echo 여러 작업을 큐에 쌓아 자동 처리하고 싶을 때만 task 파일 작성.
    echo Codex 에게 "task 파일 만들어줘" 라고 부탁해도 됨:
    echo.
    echo ```
    echo codex-go "다음 3개 작업을 tasks/task-001.md, task-002.md, task-003.md 로 정리해줘:
    echo  1. 로그인 페이지
    echo  2. 회원가입 페이지
    echo  3. 비밀번호 리셋"
    echo.
    echo codex-a --auto    # 큐 자동 처리
    echo ```
    echo.
    echo ## 폴더 의미
    echo - `tasks/`        대기 중인 작업 ^(task-NNN.md^)
    echo - `tasks/done/`   완료된 작업 보관 ^(자동 이동^)
  ) > "%TARGET%\tasks\README.md"
  echo       [OK] tasks\README.md
) else (
  echo       [OK] tasks\README.md 이미 존재
)

echo.
echo ============================================================
echo   Codex Standalone 환경 설치 완료
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo   ※ task 파일 수동 편집 필요 없음 — 자연어 한 줄이면 끝!
echo.
echo   사용법:
echo.
echo     cd /d "%TARGET%"
echo.
echo     codex-go "회원가입 페이지 만들어줘"   ← 자연어 한 줄
echo     codex-go                              ← 대화 모드
echo     codex-a --auto                        ← 배치 처리 ^(tasks/ 큐^)
echo.
echo   파일:
echo     AGENTS.md            Codex 지시서 ^(Standalone 섹션 포함^)
echo     .codex\config.toml   MCP 설정
echo     codex-go.bat          자연어 실행 단축
echo     tasks\README.md       배치 사용법
echo.

endlocal
exit /b 0
