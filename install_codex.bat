@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem install_codex.bat — Codex 단독 환경 셋업 (standalone)
rem 버전: v1
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
rem   3. .env.example 복사 (API 키·예산 설정 템플릿)
rem   4. .codex/config.toml 복사 (MCP 설정)
rem   5. codex-go.bat 생성 (자연어 한 줄로 즉시 작업)
rem   6. tasks/README.md (배치 사용 시 참고)
rem   7. .codex/usage-log.py 복사 (토큰 사용량 기록)
rem
rem 설치 후 사용:
rem   codex-go "회원가입 페이지 만들어줘"      <- 자연어 한 줄, 끝
rem   codex-go                                <- 인자 없으면 대화 모드
rem   codex-a --auto                          <- tasks/ 의 task 파일 일괄 처리
rem
rem 다음 단계:
rem   - API 키 설정: setx OPENAI_API_KEY "sk-..."
rem   - 예산 상한: .env 에 CODEX_DAILY_LIMIT_USD=10 추가 (선택)
rem   - Full 모드: install.bat <폴더> (기존 .codex/ 유지 + .claude/ 추가)
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
echo   * Claude 없이 Codex 단독으로 작업 가능
echo   * 풀 orchestration 원하면 install.bat 사용
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

rem --- .env.example ---
echo [3/6] .env.example (API 키 및 설정 템플릿)...
if not exist "%TARGET%\.env.example" (
  (
    echo [#] Codex Standalone 환경변수
    echo [#] 필수: OPENAI_API_KEY 설정
    echo.
    echo OPENAI_API_KEY=sk-YOUR_API_KEY_HERE
    echo.
    echo [#] 선택: 일일 토큰 한도 ^(초과 시 경고, 기본값: 무제한^)
    echo [#] CODEX_DAILY_LIMIT_USD=10
    echo.
    echo [#] 선택: Codex 모델 선택 ^(기본값: gpt-4^)
    echo [#] CODEX_MODEL=gpt-4
  ) > "%TARGET%\.env.example"
  echo       [OK] .env.example
) else (
  echo       [OK] .env.example 이미 존재
)

rem --- .codex/config.toml ---
echo [4/6] .codex\config.toml (MCP 설정)...
if exist "%SCRIPT_DIR%\.codex\config.toml" (
  copy /Y "%SCRIPT_DIR%\.codex\config.toml" "%TARGET%\.codex\config.toml" >nul 2>&1
  echo       [OK] .codex\config.toml
) else (
  echo [WARN] .codex\config.toml 없음
)

rem --- codex-go.bat (자연어 한 줄 처리) ---
echo [5/6] codex-go.bat ^(자연어 -^> 즉시 작업^)...
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo rem codex-go - 자연어 한 줄로 코덱스 실행 ^(또는 인자 없으면 대화 모드^)
  echo rem 사용:  codex-go "회원가입 페이지 만들어줘"
  echo rem        codex-go                       ^(대화 모드^)
  echo.
  echo setlocal enabledelayedexpansion
  echo set "PROJECT_ROOT=%%~dp0"
  echo if "%%PROJECT_ROOT:~-1%%"=="\" set "PROJECT_ROOT=%%PROJECT_ROOT:~0,-1%%"
  echo cd /d "%%PROJECT_ROOT%%"
  echo.
  echo rem --- API 키 검증 ---
  echo if "%%OPENAI_API_KEY%%"=="" ^(
  echo   if exist "!PROJECT_ROOT!\.env" ^(
  echo     for /f "usebackq tokens=2 delims==" %%%%I in ^(`findstr /B "OPENAI_API_KEY" "!PROJECT_ROOT!\.env"`^ do set "OPENAI_API_KEY=%%%%I"
  echo   ^)
  echo ^)
  echo if "%%OPENAI_API_KEY%%"=="" ^(
  echo   echo [ERROR] OPENAI_API_KEY 설정되지 않음
  echo   echo.
  echo   echo 다음 중 하나를 실행하세요:
  echo   echo   1. 환경변수 설정: setx OPENAI_API_KEY "sk-..."
  echo   echo   2. .env 파일 편집: %%PROJECT_ROOT%%\.env
  echo   echo   3. 직접 명령: set OPENAI_API_KEY=sk-... ^&^& codex-go "..."
  echo   echo.
  echo   exit /b 1
  echo ^)
  echo.
  echo rem --- CLI 검증 ---
  echo where codex ^>nul 2^>^&1 ^|^| ^(echo [ERROR] codex CLI 미설치 ^- npm i -g @openai/codex ^& exit /b 1^)
  echo.
  echo rem --- 일일 예산 체크 ^(선택^) ---
  echo if not "%%CODEX_DAILY_LIMIT_USD%%"=="" ^(
  echo   if exist "!PROJECT_ROOT!\.codex\usage.jsonl" ^(
  echo     findstr /C """ts""" "!PROJECT_ROOT!\.codex\usage.jsonl" | find /c /v "" ^>nul
  echo     if not errorlevel 1 echo [INFO] 오늘의 사용량은 .codex\usage.jsonl 확인
  echo   ^)
  echo ^)
  echo.
  echo if "%%~1"=="" ^(
  echo   echo [Codex 대화 모드 시작 - %%CD%%]
  echo   codex
  echo ^) else ^(
  echo   echo [Codex 작업 시작] %%~1
  echo   codex %%*
  echo ^)
  echo endlocal
) > "%TARGET%\codex-go.bat"
echo       [OK] codex-go.bat

rem --- tasks/README.md (배치 사용 안내) ---
echo [6/6] tasks\README.md (배치 처리 안내)...
if not exist "%TARGET%\tasks\README.md" (
  (
    echo [#] tasks/ — 배치 작업 폴더 ^(선택^)
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
echo   [OK] Codex Standalone v1 설치 완료
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo ============================================================
echo   다음 단계 (필수)
echo ============================================================
echo.
echo   1. API 키 설정 ^(3가지 방법^):
echo.
echo      a. 환경변수 ^(권장^):
echo         setx OPENAI_API_KEY "sk-YOUR_API_KEY"
echo.
echo      b. .env 파일:
echo         copy "%TARGET%\.env.example" "%TARGET%\.env"
echo         [편집기로 OPENAI_API_KEY 값 입력]
echo.
echo      c. 명령줄에서:
echo         set OPENAI_API_KEY=sk-YOUR_API_KEY ^&^& codex-go "작업"
echo.
echo ============================================================
echo   사용 방법 ^(자연어 한 줄이면 끝^)
echo ============================================================
echo.
echo   1. 자연어 직시 ^(권장^):
echo.
echo      cd /d "%TARGET%"
echo      codex-go "회원가입 페이지 만들어줘"
echo      codex-go "이 모듈 리팩토링 — DRY 원칙"
echo      codex-go                             # 대화 모드
echo.
echo   2. 배치 처리 ^(여러 작업 한꺼번에^):
echo.
echo      codex-go "task-*.md 파일들을 만들어줘"
echo      codex-a --auto
echo.
echo ============================================================
echo   파일 및 설정
echo ============================================================
echo.
echo   설치 파일:
echo     AGENTS.md               Codex 지시서 ^(업무 규칙^)
echo     .codex\config.toml      MCP 설정
echo     .codex\usage.jsonl      토큰 사용량 기록 ^(자동 생성^)
echo     .env.example            API 키 및 예산 설정 템플릿
echo     codex-go.bat            자연어 명령 단축기
echo     tasks\README.md         배치 사용법
echo.
echo   선택 설정:
echo     - 일일 예산 상한: .env 에 CODEX_DAILY_LIMIT_USD=10 추가
echo     - 모델 선택: .env 에 CODEX_MODEL=gpt-4 추가
echo.
echo ============================================================
echo   Full 모드로 업그레이드 ^(Claude + Codex + Gemini^)
echo ============================================================
echo.
echo   언제든 아래 명령으로 Full orchestration 추가 가능:
echo     install.bat "%TARGET%"
echo.
echo   -> 기존 .codex\ 유지 + .claude\ 레이어 추가
echo   -> Claude 설계 -> Codex 구현 -> Gemini 검증 자동화
echo.
echo ============================================================
echo.

endlocal
exit /b 0
