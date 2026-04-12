@echo off
chcp 65001 >nul
setlocal
rem =====================================================
rem design.bat - Design Asset Generator (Windows)
rem
rem Usage:
rem   design.bat                     Interactive design session
rem   design.bat --canva             Canva design via Gemini
rem   design.bat --image [desc]      DALL-E image generation prompt
rem   design.bat --video [desc]      Video generation prompt
rem   design.bat --check             Check design reference system
rem =====================================================

set ROOT=%CD%
set MODE=interactive
set DESC=

rem --- Parse args ---
:PARSE_ARGS
if "%~1"=="" goto START
if /i "%~1"=="--canva"       ( set MODE=canva   & shift & goto PARSE_ARGS )
if /i "%~1"=="--image"       ( set MODE=image   & shift & set DESC=%~1 & shift & goto PARSE_ARGS )
if /i "%~1"=="--video"       ( set MODE=video   & shift & set DESC=%~1 & shift & goto PARSE_ARGS )
if /i "%~1"=="--check"       ( set MODE=check   & shift & goto PARSE_ARGS )
shift & goto PARSE_ARGS

:START
echo.
echo ============================================================
echo   Design Asset Generator
echo   Mode : %MODE%
echo ============================================================

if not exist "%ROOT%\docs\screens" mkdir "%ROOT%\docs\screens"
if not exist "%ROOT%\docs\screens\videos" mkdir "%ROOT%\docs\screens\videos"

rem --- Check design reference system ---
if "%MODE%"=="check" (
  echo [Design] Checking design reference system...
  echo.
  if exist "%ROOT%\docs\design-system" (
    echo [OK] docs\design-system found
    dir /B "%ROOT%\docs\design-system\layouts" 2>nul && echo      layouts OK || echo      [WARN] no layouts
    dir /B "%ROOT%\docs\design-system\components" 2>nul && echo      components OK || echo      [WARN] no components
  ) else if exist "%ROOT%\ai_design_reference_system" (
    echo [OK] ai_design_reference_system found
  ) else (
    echo [WARN] No design reference system found
    echo        Copy ai_design_reference_system_template to project root
  )
  goto END
)

rem --- Interactive mode ---
if "%MODE%"=="interactive" (
  echo [Design] Starting design session with Gemini...
  echo          Use Canva MCP / DALL-E / Figma for asset generation
  gemini --yolo
  goto END
)

rem --- Canva mode ---
if "%MODE%"=="canva" (
  echo [Design] Canva design generation via Gemini...
  gemini --yolo -p "Help me create a design using Canva. Read docs\design-system\ for brand context if available. Use the Canva MCP tools to: (1) generate a design, (2) export it as PNG, (3) save to docs\screens\. Ask me what type of design I need."
  goto END
)

rem --- Image mode ---
if "%MODE%"=="image" (
  if "%DESC%"=="" (
    echo [ERROR] Provide a description: design.bat --image "your description"
    exit /b 1
  )
  echo [Design] Generating DALL-E image prompt for: %DESC%
  gemini --yolo -p "Write a detailed English image generation prompt for DALL-E 3 based on this description: %DESC%. Output only the prompt text, max 400 characters. Consider the brand style in docs\design-system\ if available."
  echo.
  echo [Next] Use the prompt above with OpenAI Images API (OPENAI_API_KEY required)
  echo        Save result to docs\screens\
  goto END
)

rem --- Video mode ---
if "%MODE%"=="video" (
  if "%DESC%"=="" (
    echo [ERROR] Provide a description: design.bat --video "your description"
    exit /b 1
  )
  echo [Design] Generating video prompt for: %DESC%
  echo          VIDEO_PROVIDER=%VIDEO_PROVIDER%
  gemini --yolo -p "Write a concise video generation prompt for %VIDEO_PROVIDER% based on: %DESC%. Output only the prompt, max 200 characters. Focus on visual style, motion, and mood."
  echo.
  echo [Next] Use the prompt above with your video API (VIDEO_API_KEY required)
  echo        Save result to docs\screens\videos\
  goto END
)

:END
endlocal
