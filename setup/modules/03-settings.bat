@echo off
rem =====================================================
rem Module 03: Claude 글로벌 설정 + PowerShell UTF-8 프로필
rem Usage: 03-settings.bat [REAL_USERPROFILE] [TARGET]
rem =====================================================
setlocal enabledelayedexpansion

set "REAL_USERPROFILE=%~1"
set "TARGET=%~2"
if "%REAL_USERPROFILE%"=="" set "REAL_USERPROFILE=%USERPROFILE%"

echo.
echo [+] Configuring Claude global settings...
if not exist "!REAL_USERPROFILE!\.claude" mkdir "!REAL_USERPROFILE!\.claude" >nul 2>&1
powershell -NoProfile -Command ^
  "$f='!REAL_USERPROFILE!\.claude\settings.json'; ^
   if(Test-Path $f){$j=Get-Content $f -Raw|ConvertFrom-Json}else{$j=[PSCustomObject]@{}}; ^
   if(-not $j.PSObject.Properties['permissions']){$j|Add-Member -NotePropertyName 'permissions' -NotePropertyValue ([PSCustomObject]@{})}; ^
   $j.permissions|Add-Member -NotePropertyName 'defaultMode' -NotePropertyValue 'bypassPermissions' -Force; ^
   $j|Add-Member -NotePropertyName 'skipDangerousModePermissionPrompt' -NotePropertyValue $true -Force; ^
   $j|Add-Member -NotePropertyName 'autoUpdatesChannel' -NotePropertyValue 'latest' -Force; ^
   $j|Add-Member -NotePropertyName 'checkpointingEnabled' -NotePropertyValue $true -Force; ^
   $j|ConvertTo-Json -Depth 10|Set-Content $f -Encoding UTF8" >nul 2>&1
echo       Done

echo [+] Setting PowerShell UTF-8 encoding...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$lines=@('[Console]::OutputEncoding=[System.Text.Encoding]::UTF8','$OutputEncoding=[System.Text.Encoding]::UTF8'); ^
   foreach($prof in @($PROFILE.CurrentUserAllHosts,$PROFILE.CurrentUserCurrentHost)){ ^
     try{ $dir=Split-Path $prof; if(!(Test-Path $dir)){New-Item $dir -ItemType Directory -Force|Out-Null}; ^
     $cur=if(Test-Path $prof){Get-Content $prof -Raw -Encoding UTF8}else{''}; ^
     $add=$lines|Where-Object{$cur -notmatch [regex]::Escape($_)}; ^
     if($add){($cur.TrimEnd()+\"`n\"+($add -join \"`n\")+\"`n\")|Set-Content $prof -Encoding UTF8} }catch{} }" >nul 2>&1
echo       Done

rem --- 글로벌 커맨드 설치 (godmode, devil, 10x 등 13개) ---
echo [+] Installing global slash commands...
if not exist "!REAL_USERPROFILE!\.claude\commands" mkdir "!REAL_USERPROFILE!\.claude\commands" >nul 2>&1
set "CMD_SRC=%~dp0..\.claude\commands"
if exist "!CMD_SRC!" (
  robocopy "!CMD_SRC!" "!REAL_USERPROFILE!\.claude\commands" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       Done ^(godmode, devil, 10x, pitch, ghost, compare, scout, artifacts, ooda, critique, explainlikeim5, brief, teacher^)
) else (
  echo       [SKIP] commands source not found: !CMD_SRC!
)

rem --- 토큰 최적화 환경변수 설정 ---
echo [+] Setting token optimization env vars...
setx CLAUDE_CODE_MAX_THINKING_TOKENS 10000 >nul 2>&1
setx CLAUDE_AUTOCOMPACT_THRESHOLD 50 >nul 2>&1
setx CLAUDE_CODE_SUBAGENT_MODEL claude-haiku-4-5-20251001 >nul 2>&1
echo       Done (MAX_THINKING=10000, AUTOCOMPACT=50%%, SUBAGENT=haiku)

rem Orca-auto 활성화 플래그
if not "%TARGET%"=="" (
  if not exist "%TARGET%\.claude\orca-stopped" (
    if not exist "%TARGET%\.claude\orca-enabled" (
      echo enabled> "%TARGET%\.claude\orca-enabled"
      echo       Orca-auto enabled
    )
  )
)

echo [Module 03] Settings OK
endlocal
exit /b 0
