@echo off
set "SELF_DIR=%~dp0"
chcp 65001 >nul
rem gemini-verify - shortcut for gemini-a --verify
call "%SELF_DIR%gemini-a.bat" --verify %*
