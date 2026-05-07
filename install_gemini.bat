@echo off
rem =====================================================
rem install_gemini.bat — install_gemini.ps1 wrapper
rem 한글 echo 깨짐 방지를 위해 PowerShell 본체 호출
rem =====================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_gemini.ps1" %*
exit /b %ERRORLEVEL%
