@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem codex.bat - Codex AI worker (Windows)
rem
rem Usage:
rem   codex.bat                     Interactive mode
rem   codex.bat --auto              Auto (reads task-instruction.md)
rem   codex.bat --auto [task-file]  Auto with custom task file
rem   codex.bat --full-auto         Fully automated, no prompts
rem   codex.bat --analyze           Source analysis mode
rem
rem NOTE: Even with bypass permissions, this script ALWAYS
rem       asks for confirmation before modifying existing files.
rem =====================================================

set ROOT=%CD%
set TASK_FILE=%ROOT%\.claude\tasks\task-instruction.md
set MODE=interactive
set CONFIRM_MODIFY=true

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto START
if /i "%~1"=="--auto"       ( set MODE=auto        & shift & goto PARSE_ARGS )
if /i "%~1"=="--full-auto"  ( set MODE=full-auto   & shift & goto PARSE_ARGS )
if /i "%~1"=="--analyze"    ( set MODE=analyze     & shift & goto PARSE_ARGS )
if /i "%~1"=="--no-confirm" ( set CONFIRM_MODIFY=false & shift & goto PARSE_ARGS )
if exist "%~1"              ( set TASK_FILE=%~1    & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS

:START
echo.
echo ============================================================
echo   Codex Worker
echo   Mode          : %MODE%
echo   Confirm modify: %CONFIRM_MODIFY%
echo ============================================================

rem ─── Interactive mode ───────────────────────────────────────
if "%MODE%"=="interactive" (
  echo [Codex] Interactive session...
  echo [NOTE]  Codex may ask to modify files - review carefully
  codex --dangerously-skip-permissions
  goto END
)

rem ─── Analyze mode ───────────────────────────────────────────
if "%MODE%"=="analyze" (
  echo [Codex] Source analysis mode
  echo         Will map code, find patterns, suggest improvements
  echo         DB/Query files: read-only, suggest only
  echo.

  if "%CONFIRM_MODIFY%"=="true" (
    echo [SAFETY] Before modifying any existing file,
    echo          Codex will show you the change and ask for confirmation.
    echo.
  )

  set ANALYZE_PROMPT=Analyze the entire project source code. Do the following steps: STEP 1 - Read docs\project-analysis.md for stack context. STEP 2 - Map all source files: list each file with its role (component/service/controller/model/etc). STEP 3 - Identify patterns: state management, API call patterns, auth flow, error handling. STEP 4 - Find improvements: list specific issues in frontend and backend code with file+line references. STEP 5 - For any .sql files or query/mapper files, DO NOT MODIFY THEM. Instead describe what they do and write suggested optimizations to docs\query-suggestions.md. STEP 6 - Write complete analysis to docs\codex-analysis.md. IMPORTANT RULE: Before modifying any existing source file, display exactly what you plan to change and ask the user 'OK to apply this change? (Y/N)'.

  codex --dangerously-skip-permissions "%ANALYZE_PROMPT%"
  goto END
)

rem ─── Auto / Full-auto modes ─────────────────────────────────
if not exist "%TASK_FILE%" (
  echo [ERROR] Task file not found: %TASK_FILE%
  echo         Create task-instruction.md first
  echo         Or run: codex.bat  (interactive)
  exit /b 1
)

echo [Codex] Task: %TASK_FILE%
echo.
echo --- Task Preview (first 5 lines) ---
set LINE=0
for /f "tokens=*" %%L in ('type "%TASK_FILE%"') do (
  set /a LINE+=1
  if !LINE! LEQ 5 echo   %%L
)
echo ------------------------------------
echo.

rem Safety confirmation prompt for full-auto
if "%CONFIRM_MODIFY%"=="true" (
  echo [SAFETY] Codex will ask for confirmation before modifying
  echo          any EXISTING file. New files can be created freely.
  echo.
)

set PROMPT=Read the task instruction at %TASK_FILE% and implement everything described. Follow all constraints. IMPORTANT: Before modifying any existing file, show what you plan to change and ask 'OK to apply? (Y/N)'. New file creation does not need confirmation. After implementation write docs\implementation-report.md.

if "%MODE%"=="full-auto" (
  echo [Codex] Full-auto mode starting...
  codex --dangerously-skip-permissions --approval-mode full-auto "%PROMPT%"
) else (
  echo [Codex] Auto mode starting...
  codex --dangerously-skip-permissions "%PROMPT%"
)

echo.
echo [DONE] Codex complete
echo        Next: .claude\scripts\gemini.bat --verify

:END
endlocal
