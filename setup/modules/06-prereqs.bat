@echo off
rem =====================================================
rem Module 06: 필수 도구 설치 (Node.js, Claude Code, cloudflared)
rem Usage: 06-prereqs.bat
rem =====================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Prerequisites Check
echo ============================================================

rem --- Node.js / npm ---
where npm >nul 2>&1
if not errorlevel 1 (
  echo [OK] Node.js / npm
  goto CHECK_CODEX
)
echo [+] Node.js not found - installing...
where winget >nul 2>&1
if errorlevel 1 (
  echo [WARN] winget not found - install Node.js manually: https://nodejs.org
  goto CHECK_CLAUDE
)
call winget install --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
call refreshenv >nul 2>&1
set "PATH=!PATH!;%ProgramFiles%\nodejs"
where npm >nul 2>&1
if errorlevel 1 (
  echo [WARN] npm still not found - restart terminal after install
  goto CHECK_CLAUDE
)
echo [OK] Node.js installed

:CHECK_CODEX
where codex >nul 2>&1
if not errorlevel 1 (
  echo [OK] @openai/codex
) else (
  echo [+] Installing @openai/codex...
  call npm install -g @openai/codex >nul 2>&1
  where codex >nul 2>&1
  if not errorlevel 1 (echo [OK] codex installed) else (echo [WARN] codex install failed)
)

rem --- Gemini CLI ---
where gemini >nul 2>&1
if not errorlevel 1 (
  echo [OK] @google/gemini-cli
) else (
  echo [+] Installing @google/gemini-cli...
  call npm install -g @google/gemini-cli >nul 2>&1
  where gemini >nul 2>&1
  if not errorlevel 1 (echo [OK] gemini installed) else (echo [WARN] gemini install failed)
)

:CHECK_CLAUDE
rem --- Claude Code ---
where claude >nul 2>&1
if not errorlevel 1 (
  echo [OK] Claude Code
  rem --- claude.exe 가 실행 중이면 winget 이 .exe 를 교체할 수 없어 0x8a150003 발생 → skip ---
  tasklist /FI "IMAGENAME eq claude.exe" 2>nul | findstr /I /B "claude.exe" >nul 2>&1
  if errorlevel 1 (
    echo [+] Checking for updates...
    powershell -NoProfile -Command "$p=Start-Process 'winget' -ArgumentList @('upgrade','--id','Anthropic.ClaudeCode','--accept-source-agreements','--accept-package-agreements') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(120000)){$p.Kill();Write-Host '[WARN] Update timeout'}else{$c=$p.ExitCode; if($c -eq 0){Write-Host '[OK] Claude Code updated'}elseif($c -eq -1978335189){Write-Host '[OK] Already up to date'}else{Write-Host ('[WARN] Update failed (exit 0x{0:X8}) - skipping' -f $c)}}}" 2>nul
  ) else (
    echo       [SKIP] Update skipped — claude.exe is running. Close Claude Code first to update.
  )
) else (
  echo [+] Installing Claude Code...
  where winget >nul 2>&1
  if not errorlevel 1 (
    call winget install Anthropic.ClaudeCode --accept-source-agreements --accept-package-agreements
    call refreshenv >nul 2>&1
    echo [OK] Claude Code installed
  ) else (
    echo [WARN] Install manually: https://claude.ai/download/cli
  )
)

rem --- Cloudflared ---
set "WINGET_LINKS=!LOCALAPPDATA!\Microsoft\WinGet\Links"
set "PATH=!PATH!;!WINGET_LINKS!"
powershell -NoProfile -Command "$p=[System.Environment]::GetEnvironmentVariable('Path','User'); if($p -notmatch 'WinGet\\Links'){[System.Environment]::SetEnvironmentVariable('Path',$p+';!WINGET_LINKS!','User')}" >nul 2>&1

where cloudflared >nul 2>&1
if not errorlevel 1 (
  echo [OK] cloudflared
) else (
  echo [+] Installing cloudflared...
  where winget >nul 2>&1
  if not errorlevel 1 (
    winget install Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements >nul 2>&1
    for /f "tokens=*" %%F in ('dir /s /b "!LOCALAPPDATA!\Microsoft\WinGet\Packages\cloudflared.exe" 2^>nul') do (
      set "CF_DIR=%%~dpF"
      set "PATH=!PATH!;!CF_DIR!"
      powershell -NoProfile -Command "$p=[System.Environment]::GetEnvironmentVariable('Path','User'); if($p -notmatch 'cloudflared'){[System.Environment]::SetEnvironmentVariable('Path',$p+';!CF_DIR!','User')}" >nul 2>&1
    )
  )
  where cloudflared >nul 2>&1
  if not errorlevel 1 (echo [OK] cloudflared installed) else (echo [WARN] cloudflared install failed)
)

echo.
echo ============================================================
echo   CLI Status
echo ============================================================
where claude      >nul 2>&1 && echo [OK] claude       || echo [X]  claude
where codex       >nul 2>&1 && echo [OK] codex        || echo [X]  codex
where codex-a     >nul 2>&1 && echo [OK] codex-a      || echo [X]  codex-a
where gemini      >nul 2>&1 && echo [OK] gemini       || echo [X]  gemini
where gemini-a    >nul 2>&1 && echo [OK] gemini-a     || echo [X]  gemini-a
where cloudflared >nul 2>&1 && echo [OK] cloudflared  || echo [X]  cloudflared
where git         >nul 2>&1 && echo [OK] git          || echo [X]  git

echo [Module 06] Prerequisites OK
endlocal
exit /b 0
