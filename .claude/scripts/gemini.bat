@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem gemini.bat - Gemini validator (Windows)
rem
rem Usage:
rem   gemini.bat                     Interactive mode
rem   gemini.bat --verify            Verify against task-instruction.md
rem   gemini.bat --verify [file]     Verify specific file/folder
rem   gemini.bat --analyze           Full source analysis mode
rem   gemini.bat --loop              Continuous watch mode (30s interval)
rem   gemini.bat --full-auto         No prompts, write to docs\review-result.txt
rem
rem NOTE: Even with bypass permissions, this script ALWAYS
rem       asks for confirmation before modifying existing files.
rem       DB and SQL files are NEVER modified - suggest only.
rem =====================================================

set ROOT=%CD%
set TASK_FILE=%ROOT%\.claude\tasks\task-instruction.md
set TARGET_PATH=%ROOT%
set MODE=interactive
set LOOP_MODE=false
set CONFIRM_MODIFY=true

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto START
if /i "%~1"=="--verify"     ( set MODE=verify    & shift & goto PARSE_ARGS )
if /i "%~1"=="--analyze"    ( set MODE=analyze   & shift & goto PARSE_ARGS )
if /i "%~1"=="--full-auto"  ( set MODE=full-auto & shift & goto PARSE_ARGS )
if /i "%~1"=="--loop"       ( set LOOP_MODE=true & set MODE=verify & shift & goto PARSE_ARGS )
if /i "%~1"=="--no-confirm" ( set CONFIRM_MODIFY=false & shift & goto PARSE_ARGS )
if exist "%~1"              ( set TARGET_PATH=%~1 & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS

:START
echo.
echo ============================================================
echo   Gemini Validator
echo   Mode          : %MODE%
echo   Confirm modify: %CONFIRM_MODIFY%
echo   DB/SQL        : suggest only (NEVER modified)
echo ============================================================

rem ─── Interactive mode ───────────────────────────────────────
if "%MODE%"=="interactive" (
  echo [Gemini] Interactive session...
  gemini --yolo
  goto END
)

if not exist "%ROOT%\docs" mkdir "%ROOT%\docs"

rem ─── Analyze mode ───────────────────────��───────────────────
if "%MODE%"=="analyze" (
  echo [Gemini] Full source analysis mode
  echo         Checking: code quality, security, bugs, query optimization
  echo.

  set ANALYZE_PROMPT=Analyze the project in the current directory. Read docs\project-analysis.md for stack context. Perform the following analysis and write results to docs\gemini-analysis.md: SECTION 1 - FRONTEND REVIEW: Check each component/page file. Rate each: PASS/WARN/FAIL. List specific bugs and anti-patterns with file+line references. SECTION 2 - BACKEND REVIEW: Check controllers, services, repositories. Look for: missing validation, exception handling gaps, N+1 queries, security holes. SECTION 3 - SECURITY SCAN: Check for: hardcoded credentials, SQL injection risk, XSS vectors, insecure API endpoints. SECTION 4 - DB AND QUERY ANALYSIS (READ ONLY - DO NOT MODIFY ANY .sql OR MAPPER FILES): Read all SQL files and mapper files. For each query, suggest: optimized version, missing indexes, potential performance issues. Write all DB suggestions to docs\query-suggestions.md. SECTION 5 - IMPROVEMENT SUMMARY: List top 10 most impactful improvements, ordered by priority. IMPORTANT RULE: Before modifying any existing source file, display exactly what you plan to change and ask the user 'OK to apply this change? (Y/N)'. NEVER modify .sql files or any DB migration files.

  gemini --yolo "%ANALYZE_PROMPT%"
  goto DONE_MSG
)

rem ─── Verify mode ────────────────────────────────────────────
if "%MODE%"=="verify" (
  if not exist "%TASK_FILE%" (
    echo [WARN] task-instruction.md not found - running general review
    set VERIFY_PROMPT=Review all recently changed files in this project. Find: bugs, security issues, performance problems, error handling gaps. Check each Acceptance Criteria if docs\task-instruction.md exists. Report each as PASS/FAIL with line references. List all issues found. RULE: Before fixing any file, show the fix and ask 'Apply this fix? (Y/N)'. NEVER modify .sql or DB migration files.
    goto RUN_GEMINI_VERIFY
  )

  echo [Gemini] Verifying against: %TASK_FILE%

  set VERIFY_PROMPT=You are a strict code reviewer. Read task instruction at %TASK_FILE%. Then review implementation in %TARGET_PATH%. Check: (1) Each Acceptance Criteria: PASS or FAIL with evidence. (2) No forbidden operations violated. (3) No hardcoded values. (4) Lint and build would pass. (5) Security issues. (6) Edge cases and error handling. For any .sql or DB files found: read-only, write suggestions to docs\query-suggestions.md only. Write full report to docs\review-result.txt. RULE: Before modifying any existing file, show the change and ask 'Apply? (Y/N)'.

  :RUN_GEMINI_VERIFY
  echo.
  if "%MODE%"=="full-auto" (
    gemini --yolo -p "%VERIFY_PROMPT%"
  ) else (
    gemini --yolo "%VERIFY_PROMPT%"
  )

  echo.
  if exist "%ROOT%\docs\review-result.txt" (
    echo [DONE] Report: docs\review-result.txt
    echo.
    echo --- Issues Summary ---
    findstr /i "FAIL\|ERROR\|BUG\|WARN\|BLOCK" "%ROOT%\docs\review-result.txt" 2>nul
    echo ----------------------
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
)

:DONE_MSG
echo.
echo [DONE] Gemini analysis complete
echo   docs\gemini-analysis.md   - Full analysis report
echo   docs\query-suggestions.md - DB/Query suggestions (review with DBA)
echo.
echo [REMINDER] DB changes require DBA review before applying.

:END
endlocal
