@echo off
rem =====================================================
rem Module 13: SQLite State DB 초기화 (v1.0+ 24/7 자동화)
rem Usage: 13-init-state-db.bat [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=%CD%"

echo.
echo [+] Orchestration Kit SQLite State DB 초기화...

pushd "%TARGET%" 2>nul || (
  echo       [WARN] target not found: %TARGET%
  goto END
)

rem --- Python 확인 ---
where python >nul 2>&1
if errorlevel 1 (
  echo       [WARN] Python 3 이(가) 없음 - .claude\scripts\init-state-db.py 수동 실행 필요
  echo       수동 실행: python .claude/scripts/init-state-db.py
  goto POPD_END
)

rem --- State DB 초기화 ---
if exist ".claude\scripts\init-state-db.py" (
  echo       .claude\state\orca.db 생성 + 마이그레이션...
  python .claude\scripts\init-state-db.py 2>nul
  if errorlevel 0 (
    echo       [OK] SQLite State DB 준비 완료
    echo.
    echo       24/7 자동화 설정 (선택):
    echo         1. 예산 상한 설정:
    echo            python .claude/scripts/route.py --set-daily-limit 50
    echo         2. Watchdog 시작:
    echo            .claude/scripts/watchdog-start.bat
  ) else (
    echo       [ERR] init-state-db.py 실패
  )
) else (
  echo       [WARN] init-state-db.py 없음
)

rem --- 상태 확인 (선택) ---
if exist ".claude\scripts\route.py" (
  echo.
  echo       현황 확인:
  echo         python .claude/scripts/route.py --status
)

:POPD_END
popd

:END
echo [Module 13] State DB Init OK
endlocal
exit /b 0
