@echo off
rem =====================================================
rem Module 11: Media Enhance 의존성 설치
rem   - 오디오: demucs, noisereduce, pydub, librosa
rem   - PDF: PyMuPDF, pytesseract, Tesseract-OCR
rem   - PPT: python-pptx
rem   - GUI: streamlit
rem   - 공통: tqdm, Pillow
rem   (동영상/이미지는 10-video-restore에서 처리)
rem Usage: 11-media-enhance.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"
set "TOOLS_DIR=%TARGET%\tools\media-enhance"

echo.
echo ============================================================
echo   Media Enhance Dependencies
echo ============================================================

rem --- Python 확인 ---
set "PYTHON_CMD="
where python >nul 2>&1 && set "PYTHON_CMD=python"
if "!PYTHON_CMD!"=="" where python3 >nul 2>&1 && set "PYTHON_CMD=python3"
if "!PYTHON_CMD!"=="" (
  echo       [X] Python not found - skip media enhance setup
  goto DONE
)

echo [1/4] Audio processing libs...
!PYTHON_CMD! -m pip install noisereduce pydub librosa soundfile >nul 2>&1
echo       [OK] noisereduce, pydub, librosa, soundfile
!PYTHON_CMD! -m pip install demucs >nul 2>&1
if not errorlevel 1 (echo       [OK] demucs) else (echo       [WARN] demucs failed - large model, install manually)

echo [2/4] PDF processing libs...
!PYTHON_CMD! -m pip install PyMuPDF pytesseract Pillow >nul 2>&1
echo       [OK] PyMuPDF, pytesseract, Pillow

rem Tesseract-OCR 설치 확인
where tesseract >nul 2>&1
if not errorlevel 1 (
  echo       [OK] Tesseract-OCR
) else (
  echo       [+] Installing Tesseract-OCR...
  where winget >nul 2>&1
  if not errorlevel 1 (
    winget install UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements >nul 2>&1
    where tesseract >nul 2>&1
    if not errorlevel 1 (echo       [OK] Tesseract installed) else (echo       [WARN] Tesseract install failed - manual: winget install UB-Mannheim.TesseractOCR)
  ) else (
    echo       [WARN] winget not found - manual: https://github.com/UB-Mannheim/tesseract/wiki
  )
)

echo [3/4] PPT + GUI libs...
!PYTHON_CMD! -m pip install python-pptx streamlit tqdm >nul 2>&1
echo       [OK] python-pptx, streamlit, tqdm

echo [4/4] Project structure...
if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%" >nul 2>&1
if not exist "%TOOLS_DIR%\enhancers" mkdir "%TOOLS_DIR%\enhancers" >nul 2>&1
if not exist "%TOOLS_DIR%\utils" mkdir "%TOOLS_DIR%\utils" >nul 2>&1

rem requirements.txt 생성
(
  echo # Media Enhance Dependencies
  echo torch
  echo torchvision
  echo realesrgan
  echo basicsr
  echo facexlib
  echo gfpgan
  echo opencv-python-headless
  echo noisereduce
  echo pydub
  echo librosa
  echo soundfile
  echo demucs
  echo PyMuPDF
  echo pytesseract
  echo Pillow
  echo python-pptx
  echo streamlit
  echo tqdm
) > "%TOOLS_DIR%\requirements.txt"
echo       [OK] requirements.txt created

:DONE
echo.
echo [Module 11] Media Enhance OK
endlocal
exit /b 0
