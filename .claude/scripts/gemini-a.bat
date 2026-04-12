@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem gemini-a.bat - Gemini-A validator (Windows)
rem
rem Usage:
rem   gemini-a.bat                     Interactive mode
rem   gemini-a.bat --verify            Verify against task-instruction.md
rem   gemini-a.bat --verify [file]     Verify specific file/folder
rem   gemini-a.bat --analyze           Full source analysis mode
rem   gemini-a.bat --loop              Continuous watch mode (30s interval)
rem
rem NOTE: DB and SQL files are NEVER modified - suggest only.
rem       Before modifying source files, always asks [Y/N].
rem =====================================================

rem --- Resolve project root: prefer %PROJECT_ROOT%, then walk up from %CD% ---
set ROOT=
if defined PROJECT_ROOT if exist "%PROJECT_ROOT%\.claude" set "ROOT=%PROJECT_ROOT%"
if not defined ROOT (
  set "ROOT=%CD%"
  if not exist "!ROOT!\.claude" (
    rem Walk up to find .claude folder
    for %%D in ("%CD%") do set "ROOT=%%~dpD"
    if not exist "!ROOT!\.claude" set "ROOT=%CD%"
  )
)
rem Strip trailing backslash
if "!ROOT:~-1!"=="\" set "ROOT=!ROOT:~0,-1!"
set TASK_FILE=%ROOT%\.claude\tasks\task-instruction.md
set TARGET_PATH=%ROOT%
set MODE=interactive
set LOOP_MODE=false

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto START
if /i "%~1"=="--verify"     set "MODE=verify"    & shift & goto PARSE_ARGS
if /i "%~1"=="--analyze"    set "MODE=analyze"   & shift & goto PARSE_ARGS
if /i "%~1"=="--research"   set "MODE=research"  & shift & goto PARSE_ARGS
if /i "%~1"=="--full-auto"  set "MODE=full-auto" & shift & goto PARSE_ARGS
if /i "%~1"=="--loop"       set "LOOP_MODE=true" & set "MODE=verify" & shift & goto PARSE_ARGS
if exist "%~1"              set "TARGET_PATH=%~1" & set "TASK_FILE=%~1" & shift & goto PARSE_ARGS
shift & goto PARSE_ARGS

:START
echo.
echo ============================================================
echo   Gemini-A
echo   Mode   : %MODE%
echo   DB/SQL : suggest only - NEVER modified
echo ============================================================

rem --- Interactive mode ---
if "%MODE%"=="interactive" goto DO_INTERACTIVE
rem --- Research mode ---
if "%MODE%"=="research"    goto DO_RESEARCH
goto CHECK_DOCS

:DO_INTERACTIVE
echo [Gemini-A] Interactive session...
gemini --yolo
goto END

:CHECK_DOCS
if not exist "%ROOT%\docs" mkdir "%ROOT%\docs"

rem --- Analyze mode ---
if "%MODE%"=="analyze" goto DO_ANALYZE
rem --- Verify mode ---
if "%MODE%"=="verify" goto DO_VERIFY
goto END

:DO_RESEARCH
echo [Gemini-A] Research mode: %TASK_FILE%
echo.

rem --- 날짜 폴더 설정 ---
for /f "tokens=*" %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "DOCS_DATE_DIR=%ROOT%\docs\!TODAY!"
if not exist "!DOCS_DATE_DIR!" mkdir "!DOCS_DATE_DIR!" >nul 2>&1

rem --- 결과 파일명 ---
for %%F in ("!TASK_FILE!") do set "TASK_BASENAME=%%~nF"
set "RESULT_FILE=!DOCS_DATE_DIR!\research-!TASK_BASENAME!.md"

set TEMPFILE=%TEMP%\gemini-research-%RANDOM%.txt

if not exist "!TASK_FILE!" (
  echo [ERROR] Task file not found: !TASK_FILE!
  goto END
)

echo Perform a research and documentation task right now. Start immediately. > "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo TASK FILE: !TASK_FILE! >> "!TEMPFILE!"
echo Read the task file above carefully, then execute all research steps described in it. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo OUTPUT RULES: >> "!TEMPFILE!"
echo - Write all findings, research results, drafts, and documents to: !RESULT_FILE! >> "!TEMPFILE!"
echo - Structure the output in clear markdown sections >> "!TEMPFILE!"
echo - If the task requires a PPT/presentation outline: write it as a structured outline with slide titles and bullet points >> "!TEMPFILE!"
echo - If the task requires diagrams: write Mermaid syntax >> "!TEMPFILE!"
echo - If the task requires data/statistics: cite sources >> "!TEMPFILE!"
echo - At the end of the file write: [RESEARCH_COMPLETE] >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Do not ask questions. Use your best judgment. Start now. >> "!TEMPFILE!"
type "!TEMPFILE!" | gemini --yolo
del "!TEMPFILE!" 2>nul

echo.
if exist "!RESULT_FILE!" (
  echo [DONE] 결과: !RESULT_FILE!
  findstr /i "RESEARCH_COMPLETE" "!RESULT_FILE!" >nul 2>&1
  if not errorlevel 1 (
    echo [OK] 리서치 완료
  ) else (
    echo [WARN] 완료 마커 없음 - 결과 확인 필요
  )
) else (
  echo [WARN] 결과 파일 없음: !RESULT_FILE!
)
goto END

:DO_ANALYZE
echo [Gemini-A] Full source analysis mode
echo            Checking: code quality, security, bugs, query optimization
echo.
set TEMPFILE=%TEMP%\gemini-analyze-%RANDOM%.txt
echo Perform a complete source code analysis of this project right now. > "!TEMPFILE!"
echo Do each section in order and write all results immediately. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo First, take time to THINK through the architecture before writing findings. >> "!TEMPFILE!"
echo Consider: what patterns are used, what the intent is, where the risks are. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo SECTION 1 - FRONTEND REVIEW: >> "!TEMPFILE!"
echo   Read every component and page file. >> "!TEMPFILE!"
echo   Rate each file PASS, WARN, or FAIL. >> "!TEMPFILE!"
echo   List specific bugs and anti-patterns with exact file+line references. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo SECTION 2 - BACKEND REVIEW: >> "!TEMPFILE!"
echo   Check controllers, services, repositories. >> "!TEMPFILE!"
echo   Find: missing validation, exception handling gaps, N+1 queries, security holes. >> "!TEMPFILE!"
echo   Report each issue with file+line. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo SECTION 3 - SECURITY SCAN: >> "!TEMPFILE!"
echo   Check for: hardcoded credentials, SQL injection risk, XSS vectors, insecure endpoints. >> "!TEMPFILE!"
echo   Each finding is a FAIL with file+line. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo SECTION 4 - DB AND QUERY ANALYSIS (READ ONLY): >> "!TEMPFILE!"
echo   Read all .sql files and mapper files. >> "!TEMPFILE!"
echo   For each query suggest: optimized version, missing indexes, performance issues. >> "!TEMPFILE!"
echo   Write all suggestions to docs\query-suggestions.md - DO NOT modify any .sql file. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo SECTION 5 - TOP 10 IMPROVEMENTS: >> "!TEMPFILE!"
echo   List top 10 most impactful improvements ordered by priority. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Write final report to docs\gemini-analysis.md. >> "!TEMPFILE!"
echo Before modifying any source file: show the exact change and ask [Y/N]. >> "!TEMPFILE!"
echo Never modify .sql or DB migration files under any circumstances. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Start now. >> "!TEMPFILE!"
type "!TEMPFILE!" | gemini --yolo
del "!TEMPFILE!" 2>nul
goto DONE_ANALYZE_MSG

:DO_VERIFY
echo [Gemini-A] Task    : %TASK_FILE%
echo [Gemini-A] Target  : %TARGET_PATH%
echo [Gemini-A] Report  : docs\review-result.txt
echo.
echo [Gemini-A] Starting review... (Gemini is reading your code)
echo [Gemini-A] Results will be saved to: docs\review-result.txt
echo.

set TEMPFILE=%TEMP%\gemini-verify-%RANDOM%.txt

if not exist "%TASK_FILE%" goto VERIFY_GENERAL

rem --- Task-based verify (fall-through when task file exists) ---
echo Perform a code review right now. Do not ask for further instructions - start immediately. > "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo STEP 1: Read the task requirements file: %TASK_FILE% >> "!TEMPFILE!"
echo STEP 2: Read coding rules if this file exists: %ROOT%\context\rules.md >> "!TEMPFILE!"
echo STEP 3: Review all source files in: %TARGET_PATH% >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo For each acceptance criterion in the task file: report PASS or FAIL with file+line evidence. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Check these violations: >> "!TEMPFILE!"
echo   - Vue2 optional chaining: FAIL >> "!TEMPFILE!"
echo   - Hardcoded values not using process.env: FAIL >> "!TEMPFILE!"
echo   - Security issues: FAIL >> "!TEMPFILE!"
echo   - Missing error handling on API calls: FAIL >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Write complete review to docs\review-result.txt >> "!TEMPFILE!"
echo Format: [PASS/FAIL/WARN/BLOCK] description - file:line >> "!TEMPFILE!"
echo Start now. >> "!TEMPFILE!"
goto RUN_VERIFY

:VERIFY_GENERAL
echo [WARN] task-instruction.md not found - running general review
echo Perform a code review right now. Do not ask for further instructions - start immediately. > "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo If context\rules.md exists, read it first for project coding rules. >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Check each file and report PASS, FAIL, WARN, or BLOCK: >> "!TEMPFILE!"
echo   - Bugs and logic errors: FAIL >> "!TEMPFILE!"
echo   - Security issues: FAIL >> "!TEMPFILE!"
echo   - Hardcoded values: FAIL >> "!TEMPFILE!"
echo   - Missing error handling: FAIL >> "!TEMPFILE!"
echo. >> "!TEMPFILE!"
echo Write full report to docs\review-result.txt with file+line for each issue. >> "!TEMPFILE!"
echo Start reviewing now. >> "!TEMPFILE!"

:RUN_VERIFY
type "!TEMPFILE!" | gemini --yolo
del "!TEMPFILE!" 2>nul

echo.
if exist "%ROOT%\docs\review-result.txt" (
  echo [DONE] Report: docs\review-result.txt
  echo.
  echo --- Issues Found ---
  findstr /i "FAIL BLOCK WARN ERROR BUG" "%ROOT%\docs\review-result.txt" 2>nul
  echo --------------------
)
if exist "%ROOT%\docs\query-suggestions.md" (
  echo [INFO] DB/Query suggestions: docs\query-suggestions.md
  echo        Review with DBA before applying any DB changes
)

if "%LOOP_MODE%"=="true" (
  echo.
  echo [Loop] Next check in 30s... Ctrl+C to stop
  timeout /t 30 /nobreak >nul
  goto START
)
goto END

:DONE_ANALYZE_MSG
echo.
echo [DONE] Gemini-A analysis complete
echo   docs\gemini-analysis.md   - Full analysis report
echo   docs\query-suggestions.md - DB/Query suggestions (review with DBA)
echo.
echo [REMINDER] DB changes require DBA review before applying.

:END
endlocal
