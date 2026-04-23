@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem install_gemini.bat — Gemini 단독 환경 셋업 (standalone)
rem
rem 용도: Claude 없이 Gemini 만으로 작업할 수 있는 환경.
rem        검증 뿐 아니라 일반 작업 (구현·요약·문서화) 도 단독 수행.
rem
rem 사용법:
rem   install_gemini C:\work\myproject
rem   install_gemini .
rem
rem 수행:
rem   1. .gemini/ + tasks/ + docs/ 구조 생성 (.claude 의존 없음)
rem   2. GEMINI.md 복사 (Standalone 섹션 포함)
rem   3. .gemini/config.toml 복사 (MCP 설정)
rem   4. gemini-go.bat 생성 (자연어 한 줄로 즉시 작업)
rem   5. tasks/README.md (배치 사용 시 참고)
rem
rem 설치 후 사용:
rem   gemini-go "이 코드 보안 검증해줘"        ← 자연어 한 줄, 끝
rem   gemini-go                              ← 인자 없으면 대화 모드
rem   gemini-a --auto                        ← tasks/ 의 task 파일 일괄 처리
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: install_gemini C:\work\myproject
  exit /b 1
)

if "%TARGET%"=="." set "TARGET=%CD%"

echo.
echo ============================================================
echo   Gemini Standalone 환경 설치: %TARGET%
echo ============================================================
echo   ※ Claude 없이 Gemini 단독으로 작업 가능
echo   ※ 풀 orchestration 원하면 install.bat 사용
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
echo [2/5] GEMINI.md (Gemini 지시서)...
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

rem --- gemini-go.bat (자연어 한 줄 처리) ---
echo [4/5] gemini-go.bat (자연어 → 즉시 작업)...
(
  echo @echo off
  echo chcp 65001 ^>nul
  echo rem gemini-go - 자연어 한 줄로 제미니 실행 ^(또는 인자 없으면 대화 모드^)
  echo rem 사용:  gemini-go "이 코드 검증해줘"
  echo rem        gemini-go                       ^(대화 모드^)
  echo set "PROJECT_ROOT=%%~dp0"
  echo if "%%PROJECT_ROOT:~-1%%"=="\" set "PROJECT_ROOT=%%PROJECT_ROOT:~0,-1%%"
  echo cd /d "%%PROJECT_ROOT%%"
  echo where gemini ^>nul 2^>^&1 ^|^| ^(echo [ERROR] gemini CLI 미설치 ^- npm i -g @google/gemini-cli ^& exit /b 1^)
  echo if "%%~1"=="" ^(
  echo   echo [Gemini 대화 모드 시작 - %%CD%%]
  echo   gemini
  echo ^) else ^(
  echo   echo [Gemini 작업 시작] %%~1
  echo   gemini %%*
  echo ^)
) > "%TARGET%\gemini-go.bat"
echo       [OK] gemini-go.bat

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
    echo gemini-go "이 코드 보안 검증해줘"
    echo gemini-go "긴 로그 요약해줘"        # 1M 컨텍스트 활용
    echo gemini-go "README 작성해줘"
    echo gemini-go                            # 대화 모드
    echo ```
    echo.
    echo ## 배치 처리 ^(여러 작업 한꺼번에^)
    echo 여러 작업을 큐에 쌓아 자동 처리하고 싶을 때만 task 파일 작성.
    echo Gemini 에게 "task 파일 만들어줘" 라고 부탁해도 됨:
    echo.
    echo ```
    echo gemini-go "다음 3개 작업을 tasks/task-001.md, task-002.md, task-003.md 로 정리해줘:
    echo  1. 인증 모듈 보안 검증
    echo  2. 로그 100MB 요약
    echo  3. API 문서 자동 생성"
    echo.
    echo gemini-a --auto    # 큐 자동 처리
    echo ```
    echo.
    echo ## Gemini 강점
    echo - 1M 토큰 컨텍스트 ^(긴 문서·로그 한 번에^)
    echo - 저단가 ^(반복 검증·요약에 좋음^)
    echo - 빠른 응답 속도
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
echo   Gemini Standalone 환경 설치 완료
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
echo     gemini-go "이 코드 검증해줘"          ← 자연어 한 줄
echo     gemini-go                             ← 대화 모드
echo     gemini-a --auto                       ← 배치 처리 ^(tasks/ 큐^)
echo.
echo   파일:
echo     GEMINI.md             Gemini 지시서 ^(Standalone 섹션 포함^)
echo     .gemini\config.toml   MCP 설정
echo     gemini-go.bat          자연어 실행 단축
echo     tasks\README.md        배치 사용법
echo.

endlocal
exit /b 0
