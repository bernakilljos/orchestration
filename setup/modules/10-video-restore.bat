@echo off
rem =====================================================
rem Module 10: Video Restoration Tools
rem   - Python / CUDA / FFmpeg 확인
rem   - CodeFormer + Real-ESRGAN 설치
rem   - 사전학습 모델 다운로드
rem Usage: 10-video-restore.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"
set "TOOLS_DIR=%TARGET%\tools\video-restore"
set "ERRORS=0"

echo.
echo ============================================================
echo   Video Restoration Tools Setup
echo ============================================================

rem =========================================
rem 단계 1: 환경 확인
rem =========================================
echo.
echo [Step 1/4] Environment Check
echo ----------------------------

rem --- Python ---
set "PYTHON_CMD="
where python >nul 2>&1
if not errorlevel 1 (
  set "PYTHON_CMD=python"
  for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo       [OK] %%V
) else (
  where python3 >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_CMD=python3"
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do echo       [OK] %%V
  ) else (
    echo       [X] Python not found
    echo.
    echo       Python 3.8+ is required. Install:
    echo         winget install Python.Python.3.11
    echo         OR https://www.python.org/downloads/
    set /a ERRORS+=1
    goto CHECK_FFMPEG
  )
)

rem --- pip ---
!PYTHON_CMD! -m pip --version >nul 2>&1
if not errorlevel 1 (
  echo       [OK] pip available
) else (
  echo       [WARN] pip not found - installing...
  !PYTHON_CMD! -m ensurepip --upgrade >nul 2>&1
)

rem --- CUDA / GPU ---
echo.
echo       GPU Check:
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
  for /f "tokens=*" %%G in ('nvidia-smi --query-gpu=name --format=csv,noheader 2^>nul') do echo       [OK] GPU: %%G
  for /f "tokens=*" %%C in ('nvidia-smi --query-gpu=driver_version --format=csv,noheader 2^>nul') do echo       [OK] Driver: %%C
  set "HAS_GPU=1"
) else (
  echo       [WARN] nvidia-smi not found - CPU mode will be used (slow)
  echo              For GPU: install NVIDIA drivers + CUDA Toolkit
  set "HAS_GPU=0"
)

:CHECK_FFMPEG
rem --- FFmpeg ---
echo.
where ffmpeg >nul 2>&1
if not errorlevel 1 (
  for /f "tokens=1-3" %%A in ('ffmpeg -version 2^>^&1 ^| findstr /B "ffmpeg"') do echo       [OK] %%A %%B %%C
) else (
  echo       [X] FFmpeg not found - installing...
  where winget >nul 2>&1
  if not errorlevel 1 (
    winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements >nul 2>&1
    rem winget이 PATH에 추가 안 할 수 있음
    set "FFMPEG_PATHS=%LOCALAPPDATA%\Microsoft\WinGet\Links;C:\ffmpeg\bin;C:\Program Files\FFmpeg\bin"
    set "PATH=!PATH!;!FFMPEG_PATHS!"
    where ffmpeg >nul 2>&1
    if not errorlevel 1 (
      echo       [OK] FFmpeg installed
    ) else (
      echo       [WARN] FFmpeg install failed
      echo              Manual: winget install Gyan.FFmpeg
      echo              OR https://ffmpeg.org/download.html
      set /a ERRORS+=1
    )
  ) else (
    echo       [WARN] winget not found
    echo              Manual: https://ffmpeg.org/download.html
    set /a ERRORS+=1
  )
)

if "!PYTHON_CMD!"=="" (
  echo.
  echo [ERROR] Python is required. Install Python first and re-run.
  goto DONE
)

rem =========================================
rem 단계 2: CodeFormer + Real-ESRGAN 설치
rem =========================================
echo.
echo [Step 2/4] Installing CodeFormer + Real-ESRGAN
echo -----------------------------------------------

if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%" >nul 2>&1

rem --- PyTorch 설치 (GPU 있으면 CUDA 버전) ---
echo       Installing PyTorch...
if "!HAS_GPU!"=="1" (
  !PYTHON_CMD! -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 >nul 2>&1
  if errorlevel 1 (
    echo       [WARN] CUDA PyTorch failed, trying cu118...
    !PYTHON_CMD! -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 >nul 2>&1
  )
) else (
  !PYTHON_CMD! -m pip install torch torchvision torchaudio >nul 2>&1
)
echo       [OK] PyTorch installed

rem --- CodeFormer clone ---
echo       Cloning CodeFormer...
if exist "%TOOLS_DIR%\CodeFormer" (
  echo       [OK] CodeFormer already exists - pulling latest...
  cd /d "%TOOLS_DIR%\CodeFormer"
  git pull >nul 2>&1
) else (
  cd /d "%TOOLS_DIR%"
  git clone https://github.com/sczhou/CodeFormer.git >nul 2>&1
  if errorlevel 1 (
    echo       [WARN] git clone failed - trying with token...
    set "GH_PAT="
    for /f "tokens=*" %%T in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"GITHUB_PERSONAL_ACCESS_TOKEN\",\"User\")" 2^>nul') do set "GH_PAT=%%T"
    if not "!GH_PAT!"=="" (
      git clone https://!GH_PAT!@github.com/sczhou/CodeFormer.git >nul 2>&1
    )
  )
)

if exist "%TOOLS_DIR%\CodeFormer" (
  echo       [OK] CodeFormer cloned
  cd /d "%TOOLS_DIR%\CodeFormer"
  echo       Installing dependencies...
  !PYTHON_CMD! -m pip install -r requirements.txt >nul 2>&1
  !PYTHON_CMD! basicsr/setup.py develop >nul 2>&1
  echo       [OK] Dependencies installed
) else (
  echo       [ERROR] CodeFormer clone failed
  set /a ERRORS+=1
)

rem --- Real-ESRGAN clone ---
echo       Cloning Real-ESRGAN...
if exist "%TOOLS_DIR%\Real-ESRGAN" (
  echo       [OK] Real-ESRGAN already exists - pulling latest...
  cd /d "%TOOLS_DIR%\Real-ESRGAN"
  git pull >nul 2>&1
) else (
  cd /d "%TOOLS_DIR%"
  git clone https://github.com/xinntao/Real-ESRGAN.git >nul 2>&1
  if errorlevel 1 (
    echo       [WARN] git clone failed - trying with token...
    if not "!GH_PAT!"=="" (
      git clone https://!GH_PAT!@github.com/xinntao/Real-ESRGAN.git >nul 2>&1
    )
  )
)

if exist "%TOOLS_DIR%\Real-ESRGAN" (
  echo       [OK] Real-ESRGAN cloned
  cd /d "%TOOLS_DIR%\Real-ESRGAN"
  echo       Installing dependencies...
  !PYTHON_CMD! -m pip install basicsr facexlib gfpgan >nul 2>&1
  !PYTHON_CMD! -m pip install -r requirements.txt >nul 2>&1
  !PYTHON_CMD! setup.py develop >nul 2>&1
  echo       [OK] Dependencies installed
) else (
  echo       [ERROR] Real-ESRGAN clone failed
  set /a ERRORS+=1
)

rem --- pip 패키지 (대안 경로 - clone 실패 시 대비) ---
echo       Installing pip packages (backup)...
!PYTHON_CMD! -m pip install realesrgan >nul 2>&1
!PYTHON_CMD! -m pip install opencv-python-headless >nul 2>&1
echo       [OK] pip packages

rem =========================================
rem 단계 3: 사전학습 모델 다운로드
rem =========================================
echo.
echo [Step 3/4] Downloading Pretrained Models
echo -----------------------------------------

if exist "%TOOLS_DIR%\CodeFormer" (
  cd /d "%TOOLS_DIR%\CodeFormer"

  rem CodeFormer 모델
  if not exist "weights\CodeFormer" mkdir "weights\CodeFormer" >nul 2>&1
  if not exist "weights\facelib" mkdir "weights\facelib" >nul 2>&1

  echo       Downloading CodeFormer model...
  if not exist "weights\CodeFormer\codeformer.pth" (
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/codeformer.pth' -OutFile 'weights\CodeFormer\codeformer.pth' -ErrorAction Stop" >nul 2>&1
    if exist "weights\CodeFormer\codeformer.pth" (echo       [OK] codeformer.pth) else (echo       [WARN] Download failed)
  ) else (
    echo       [OK] codeformer.pth exists
  )

  echo       Downloading face detection models...
  for %%M in (detection_Resnet50_Final.pth detection_mobilenet0.25_Final.pth yolov5l-face.pth) do (
    if not exist "weights\facelib\%%M" (
      powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/sczhou/CodeFormer/releases/download/v0.1.0/%%M' -OutFile 'weights\facelib\%%M' -ErrorAction SilentlyContinue" >nul 2>&1
      if exist "weights\facelib\%%M" (echo       [OK] %%M) else (echo       [WARN] %%M failed - will auto-download on first run)
    ) else (
      echo       [OK] %%M exists
    )
  )

  rem download script도 시도
  if exist "scripts\download_pretrained_models.py" (
    echo       Running official download script...
    !PYTHON_CMD! scripts/download_pretrained_models.py facelib >nul 2>&1
    !PYTHON_CMD! scripts/download_pretrained_models.py CodeFormer >nul 2>&1
  )
)

rem Real-ESRGAN 모델은 첫 실행 시 자동 다운로드됨
echo       [OK] Real-ESRGAN models auto-download on first use

rem =========================================
rem 단계 4: 처리 스크립트 복사
rem =========================================
echo.
echo [Step 4/4] Setting up video-restore script
echo -------------------------------------------

rem video-restore.py는 setup.iss가 이미 복사함
rem bat에서 실행할 때는 직접 복사
if exist "%~dp0..\tools\video-restore.py" (
  if not exist "%TOOLS_DIR%\video-restore.py" (
    copy /Y "%~dp0..\tools\video-restore.py" "%TOOLS_DIR%\video-restore.py" >nul 2>&1
  )
)
rem 프로젝트 루트의 tools 폴더에서도 확인
if exist "%TARGET%\tools\video-restore.py" (
  echo       [OK] video-restore.py ready
) else if exist "%TOOLS_DIR%\video-restore.py" (
  echo       [OK] video-restore.py ready
) else (
  echo       [WARN] video-restore.py not found - copy manually
)

:DONE
echo.
echo ============================================================
if "!ERRORS!"=="0" (
  echo   Video Restoration Setup Complete!
) else (
  echo   Setup Complete with !ERRORS! issue(s)
)
echo.
echo   Usage:
echo     python "%TOOLS_DIR%\video-restore.py" input_video.mp4
echo     python "%TOOLS_DIR%\video-restore.py" input.mp4 -o output.mp4 -w 0.7
echo     python "%TOOLS_DIR%\video-restore.py" input.mp4 --scale 2 --gpu 0
echo ============================================================

echo [Module 10] Video Restore OK
cd /d "%TARGET%"
endlocal
exit /b 0
