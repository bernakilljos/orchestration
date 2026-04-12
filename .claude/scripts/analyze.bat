@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
rem =====================================================
rem analyze.bat - Project source analysis
rem Usage: .claude\scripts\analyze.bat [project-path]
rem
rem Detects stack, maps files, asks about Codex/Gemini
rem deep analysis. DB/Query = suggest only (no modify).
rem =====================================================

set ROOT=%~1
if "%ROOT%"=="" set ROOT=%CD%
cd /d "%ROOT%"

if not exist "docs" mkdir docs

echo.
echo ============================================================
echo   SOURCE ANALYSIS
echo   Project: %ROOT%
echo ============================================================

rem ─────────────────────────────────────────
rem  STEP 1: Stack Detection
rem ─────────────────────────────────────────
echo.
echo [1/4] Detecting stack...

set STACK_FRONTEND=
set STACK_BACKEND=
set STACK_DB=
set STACK_NODE=
set STACK_DOTNET=

rem Frontend detection
if exist "package.json" (
  findstr /i "\"vue\"" package.json >nul 2>&1 && (
    findstr /i "\"2\." package.json >nul 2>&1 && set STACK_FRONTEND=Vue2 || set STACK_FRONTEND=Vue3
  )
  findstr /i "\"react\"" package.json >nul 2>&1 && set STACK_FRONTEND=React
  findstr /i "\"@angular" package.json >nul 2>&1 && set STACK_FRONTEND=Angular
  findstr /i "\"next\"" package.json >nul 2>&1 && set STACK_FRONTEND=Next.js
  findstr /i "\"nuxt\"" package.json >nul 2>&1 && set STACK_FRONTEND=Nuxt.js
  set STACK_NODE=Node.js
)

rem .NET detection
if exist "*.csproj" set STACK_DOTNET=.NET & set STACK_FRONTEND=.NET(Razor/Blazor)
if exist "*.sln"    set STACK_DOTNET=.NET
for /r . %%f in (*.csproj) do set STACK_DOTNET=.NET
for /r . %%f in (*.sln)    do set STACK_DOTNET=.NET

rem Backend detection
if exist "pom.xml"          set STACK_BACKEND=Spring Boot
if exist "build.gradle"     set STACK_BACKEND=Spring Boot(Gradle)
if exist "requirements.txt" set STACK_BACKEND=Python
if exist "manage.py"        set STACK_BACKEND=Django
if exist "app.py"           set STACK_BACKEND=Flask
if exist "go.mod"           set STACK_BACKEND=Go
if "%STACK_DOTNET%"==".NET" set STACK_BACKEND=ASP.NET

rem DB detection
if exist "pom.xml" (
  findstr /i "mysql"       pom.xml >nul 2>&1 && set STACK_DB=MySQL
  findstr /i "sqlserver"   pom.xml >nul 2>&1 && set STACK_DB=MSSQL
  findstr /i "oracle"      pom.xml >nul 2>&1 && set STACK_DB=Oracle
  findstr /i "postgresql"  pom.xml >nul 2>&1 && set STACK_DB=PostgreSQL
  findstr /i "h2"          pom.xml >nul 2>&1 && set STACK_DB=H2(embedded)
)
for /r . %%f in (application*.yml application*.properties) do (
  findstr /i "mysql"      "%%f" >nul 2>&1 && set STACK_DB=MySQL
  findstr /i "sqlserver"  "%%f" >nul 2>&1 && set STACK_DB=MSSQL
  findstr /i "oracle"     "%%f" >nul 2>&1 && set STACK_DB=Oracle
  findstr /i "postgresql" "%%f" >nul 2>&1 && set STACK_DB=PostgreSQL
  findstr /i "mongodb"    "%%f" >nul 2>&1 && set STACK_DB=MongoDB
)

echo   Frontend : %STACK_FRONTEND%
echo   Backend  : %STACK_BACKEND%
echo   Database : %STACK_DB%
echo   Node     : %STACK_NODE%
echo   .NET     : %STACK_DOTNET%

rem ─────────────────────────────────────────
rem  STEP 2: File Count by Type
rem ─────────────────────────────────────────
echo.
echo [2/4] Counting files...

set CNT_VUE=0 & set CNT_JS=0 & set CNT_TS=0 & set CNT_JSX=0
set CNT_JAVA=0 & set CNT_CS=0 & set CNT_PY=0 & set CNT_GO=0
set CNT_SQL=0 & set CNT_XML=0 & set CNT_YML=0

for /r src %%f in (*.vue)  do set /a CNT_VUE+=1  2>nul
for /r src %%f in (*.js)   do set /a CNT_JS+=1   2>nul
for /r src %%f in (*.ts)   do set /a CNT_TS+=1   2>nul
for /r src %%f in (*.jsx *.tsx) do set /a CNT_JSX+=1 2>nul
for /r src %%f in (*.java) do set /a CNT_JAVA+=1 2>nul
for /r .   %%f in (*.cs)   do set /a CNT_CS+=1   2>nul
for /r .   %%f in (*.py)   do set /a CNT_PY+=1   2>nul
for /r .   %%f in (*.go)   do set /a CNT_GO+=1   2>nul
for /r .   %%f in (*.sql)  do set /a CNT_SQL+=1  2>nul
for /r src %%f in (*.xml)  do set /a CNT_XML+=1  2>nul
for /r .   %%f in (*.yml *.yaml) do set /a CNT_YML+=1 2>nul

echo   .vue  : %CNT_VUE%
echo   .js   : %CNT_JS%
echo   .ts   : %CNT_TS%
echo   .jsx/tsx: %CNT_JSX%
echo   .java : %CNT_JAVA%
echo   .cs   : %CNT_CS%
echo   .py   : %CNT_PY%
echo   .sql  : %CNT_SQL%

rem ─────────────────────────────────────────
rem  STEP 3: Scope Declaration
rem ─────────────────────────────────────────
echo.
echo [3/4] Analysis scope...
echo.
echo   [CAN MODIFY]
echo     Frontend  : *.vue *.jsx *.tsx *.js *.ts *.css *.html
echo     Backend   : *.java *.cs *.py *.go controller/service/repository
echo     Config    : application.yml package.json pom.xml
echo.
echo   [SUGGEST ONLY - no direct modification]
echo     Database  : *.sql schema migration DDL
echo     Queries   : MyBatis mapper, JPA JPQL, raw SQL
echo     DB config : datasource connection strings
echo.
echo     Reason: DB changes require DBA review and
echo             safe migration planning. Claude will
echo             propose the change and you approve.

rem ─────────────────────────────────────────
rem  STEP 4: Save project-analysis.md
rem ─────────────────────────────────────────
echo.
echo [4/4] Saving docs\project-analysis.md...

(
  echo # Project Analysis
  echo Generated: %DATE% %TIME%
  echo.
  echo ## Stack
  echo - Frontend : %STACK_FRONTEND%
  echo - Backend  : %STACK_BACKEND%
  echo - Database : %STACK_DB%
  echo - Node     : %STACK_NODE%
  echo - .NET     : %STACK_DOTNET%
  echo.
  echo ## File Counts
  echo ^| Type ^| Count ^|
  echo ^|------|-------|
  echo ^| .vue   ^| %CNT_VUE%  ^|
  echo ^| .js    ^| %CNT_JS%   ^|
  echo ^| .ts    ^| %CNT_TS%   ^|
  echo ^| .jsx/tsx^| %CNT_JSX% ^|
  echo ^| .java  ^| %CNT_JAVA% ^|
  echo ^| .cs    ^| %CNT_CS%   ^|
  echo ^| .py    ^| %CNT_PY%   ^|
  echo ^| .sql   ^| %CNT_SQL%  ^|
  echo.
  echo ## Scope
  echo ### CAN MODIFY
  echo - Frontend: vue jsx tsx js ts css html
  echo - Backend: java cs py go controllers services repositories
  echo - Config: yml json xml
  echo.
  echo ### SUGGEST ONLY (no direct edit^)
  echo - Database: sql DDL schema migration
  echo - Query files: MyBatis mapper JPQL raw SQL
  echo - DB connection config
) > docs\project-analysis.md

echo       Saved.

rem ─────────────────────────────────────────
rem  MENU: Codex + Gemini deep analysis?
rem ─────────────────────────────────────────
echo.
echo ============================================================
echo.
echo  Initial analysis complete.
echo  Would you like a deeper analysis?
echo.
echo  Stack detected: %STACK_FRONTEND% / %STACK_BACKEND% / %STACK_DB%
echo.
echo  [C] Codex   - Deep implementation analysis
echo              (reads all source, maps patterns,
echo               finds improvement points)
echo  [G] Gemini  - Validation + security + query suggestions
echo              (reviews code quality, finds bugs,
echo               proposes DB/query improvements)
echo  [B] Both    - Codex then Gemini (comprehensive)
echo  [S] Skip    - Start Claude directly
echo.
echo ============================================================
set /p CHOICE="  Your choice (C/G/B/S): "

if /i "%CHOICE%"=="C" goto DO_CODEX
if /i "%CHOICE%"=="G" goto DO_GEMINI
if /i "%CHOICE%"=="B" goto DO_BOTH
if /i "%CHOICE%"=="S" goto DO_SKIP
echo Invalid choice - skipping analysis
goto DO_SKIP

rem ─────────────────────────────────────────
:DO_CODEX
echo.
echo [Codex] Starting implementation analysis...
echo         Will ask before making any modifications.
echo.
call .claude\scripts\codex.bat --analyze
goto DONE

rem ─────────────────────────────────────────
:DO_GEMINI
echo.
echo [Gemini] Starting validation analysis...
echo          DB/Query: suggest only, no modification.
echo.
call .claude\scripts\gemini.bat --analyze
goto DONE

rem ─────────────────────────────────────────
:DO_BOTH
echo.
echo [Both] Codex analysis first, then Gemini...
echo.
echo --- Phase 1: Codex ---
call .claude\scripts\codex.bat --analyze
echo.
echo --- Phase 2: Gemini ---
call .claude\scripts\gemini.bat --analyze
goto DONE

rem ─────────────────────────────────────────
:DO_SKIP
echo [Skip] Proceeding to Claude...

:DONE
echo.
echo ============================================================
echo  Analysis complete. Docs saved in docs\
echo    - project-analysis.md   (stack + file map)
echo    - codex-analysis.md     (if Codex ran)
echo    - gemini-analysis.md    (if Gemini ran)
echo ============================================================
echo.

endlocal
