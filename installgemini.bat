@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem installgemini.bat — 지정 경로에 Gemini 환경 세팅
rem
rem 사용법:
rem   installgemini C:\work\myproject
rem   installgemini .
rem
rem 수행 내용:
rem   1. 대상 폴더에 .claude/tasks/ 구조 생성
rem   2. GEMINI.md 복사 (Gemini 검증 지시서)
rem   3. .gemini/config.toml 복사 (MCP 설정)
rem   4. gemini-auto.bat 복사 (워커 실행파일)
rem   5. orca-workers-config.json 복사 (워커 수 설정)
rem   6. verify-instruction.md 빈 템플릿 생성
rem =====================================================

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "TARGET=%~1"
if "%TARGET%"=="" (
  echo [ERROR] 대상 경로를 입력하세요.
  echo 사용법: installgemini C:\work\myproject
  exit /b 1
)

rem 상대경로 → 절대경로 변환
if not "%TARGET:~0,1%"=="C" if not "%TARGET:~0,1%"=="D" if not "%TARGET:~0,1%"=="E" (
  if "%TARGET%"=="." set "TARGET=%CD%"
)

echo.
echo ============================================================
echo   Gemini 환경 설치: %TARGET%
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
  ".gemini"
  "docs"
) do (
  if not exist "%TARGET%\%%D" (
    mkdir "%TARGET%\%%D" >nul 2>&1
    echo       created: %%D
  ) else (
    echo       [OK] %%D
  )
)

rem --- GEMINI.md 복사 ---
echo [2/6] GEMINI.md (Gemini 검증 지시서) 복사...
if exist "%SCRIPT_DIR%\GEMINI.md" (
  copy /Y "%SCRIPT_DIR%\GEMINI.md" "%TARGET%\GEMINI.md" >nul 2>&1
  echo       [OK] GEMINI.md
) else (
  echo [WARN] GEMINI.md 없음 - 건너뜀
)

rem --- .gemini/config.toml 복사 ---
echo [3/6] .gemini\config.toml (MCP 설정) 복사...
if exist "%SCRIPT_DIR%\.gemini\config.toml" (
  copy /Y "%SCRIPT_DIR%\.gemini\config.toml" "%TARGET%\.gemini\config.toml" >nul 2>&1
  echo       [OK] .gemini\config.toml
) else (
  echo [WARN] .gemini\config.toml 없음 - 건너뜀
)

rem --- gemini-auto.bat 복사 ---
echo [4/6] gemini-auto.bat (워커 실행파일) 복사...
if exist "%SCRIPT_DIR%\gemini-auto.bat" (
  copy /Y "%SCRIPT_DIR%\gemini-auto.bat" "%TARGET%\gemini-auto.bat" >nul 2>&1
  echo       [OK] gemini-auto.bat
) else (
  echo [WARN] gemini-auto.bat 없음
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

rem --- verify-instruction.md 템플릿 생성 ---
echo [6/6] verify-instruction.md 빈 템플릿 생성...
if not exist "%TARGET%\.claude\tasks\verify-instruction.md" (
  (
    echo # 검증 제목
    echo.
    echo ## Target
    echo 검증 대상 ^(PR / 모듈 / 파일^)
    echo.
    echo ## Files
    echo - src/파일명.js
    echo.
    echo ## Checks
    echo - Security: 시크릿 하드코딩, OWASP Top 10
    echo - Quality: 복잡도, 중복, 네이밍, 에러 처리
    echo - Tests: 커버리지, 엣지케이스
    echo - Docs: README, 주석 일관성
    echo.
    echo ## Code Rules ^(위반 시 불합격^)
    echo - 하드코딩 금지
    echo - 서버 파일 한글 문자열 금지
    echo - optional chaining ^(`?.`^) 금지
    echo - 주석에 "주인" 사용 금지
    echo - 기존 파일 전체 재작성 금지
    echo.
    echo ## Pass Criteria
    echo 합격 기준 명시
    echo.
    echo ## Expected Output
    echo `.claude/tasks/done/TASK-ID-review.md` ^(PASS/FAIL + 이슈 목록^)
  ) > "%TARGET%\.claude\tasks\verify-instruction.md"
  echo       [OK] verify-instruction.md
) else (
  echo       [OK] verify-instruction.md 이미 존재
)

echo.
echo ============================================================
echo   Gemini 환경 설치 완료!
echo ============================================================
echo.
echo   대상: %TARGET%
echo.
echo   사용법:
echo     cd /d "%TARGET%"
echo     gemini-auto 2             병렬 검증 워커 2개
echo     gemini-auto 1             단일 워커 (디버깅용)
echo.
echo   워커 수 설정:  .claude\orca-workers-config.json
echo   검증 작성:    .claude\tasks\verify-instruction.md
echo   Gemini 지시: GEMINI.md
echo   MCP 설정:    .gemini\config.toml
echo.
echo   ※ Gemini 결과는 참고용 — 최종 채택은 Claude (팀장) 결정
echo.

endlocal
exit /b 0
