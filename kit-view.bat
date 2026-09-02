@echo off
REM 쉬운 실행 · 더블클릭 → dashboard 생성 + 브라우저 자동 열기
chcp 65001 >nul
cd /d %~dp0
python .claude\scripts\kit-dashboard.py --open
