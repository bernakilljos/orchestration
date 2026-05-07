@echo off
rem =====================================================
rem install_codex.bat — install_codex.ps1 wrapper
rem 한글 echo 깨짐 방지를 위해 PowerShell 본체 호출
rem =====================================================
set "PSPATH=%~dp0install_codex.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PSPATH%" %*
exit /b %ERRORLEVEL%
