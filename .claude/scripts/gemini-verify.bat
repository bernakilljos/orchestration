@echo off
chcp 65001 >nul
rem gemini-verify - shortcut for gemini-a --verify
call gemini-a --verify %*
