@echo off
chcp 65001 >nul
rem --- Uninstall npm/Volta Claude Code BEFORE admin elevation ---
where volta >nul 2>&1
if not errorlevel 1 (
  volta list @anthropic-ai/claude-code 2>nul | findstr /C:"@anthropic-ai/claude-code" >nul 2>&1
  if not errorlevel 1 (
    echo [+] Removing Volta Claude Code - switched to native installer
    call volta uninstall @anthropic-ai/claude-code
    echo     Done
  )
  goto SKIP_NPM_UNINSTALL
)
where npm >nul 2>&1 || goto SKIP_NPM_UNINSTALL
call npm list -g @anthropic-ai/claude-code >nul 2>&1 || goto SKIP_NPM_UNINSTALL
echo [+] Removing npm Claude Code - switched to native installer
call npm uninstall -g @anthropic-ai/claude-code
echo     Done
:SKIP_NPM_UNINSTALL

rem --- Auto-elevate to administrator if not already ---
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator privileges...
  echo   ^(관리자 창이 열립니다. 이 창은 닫아도 됩니다.^)
  echo @echo off > "%TEMP%\_inst_elevate.bat"
  echo cd /d "%~dp0" >> "%TEMP%\_inst_elevate.bat"
  echo call "%~f0" %* >> "%TEMP%\_inst_elevate.bat"
  echo pause >> "%TEMP%\_inst_elevate.bat"
  powershell -NoProfile -Command "Start-Process cmd.exe -ArgumentList @('/k', '%TEMP%\_inst_elevate.bat') -Verb RunAs"
  exit /b
)

setlocal enabledelayedexpansion

rem --- 로그 파일 설정 ---
set "LOGFILE=%TEMP%\orchestration-install.log"
echo ============================  > "!LOGFILE!"
echo  Install Log: %DATE% %TIME% >> "!LOGFILE!"
echo ============================  >> "!LOGFILE!"

rem --- 실제 로그인 사용자의 USERPROFILE 가져오기 (관리자 권한으로 올라가도 정확한 경로) ---
echo (Get-WmiObject Win32_Process ^| Where-Object {$_.Name -eq 'explorer.exe'} ^| Select-Object -First 1).GetOwner().User > "%TEMP%\_orch_getuser.ps1"
for /f "tokens=*" %%N in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\_orch_getuser.ps1"') do set "REAL_USERNAME=%%N"
del "%TEMP%\_orch_getuser.ps1" >nul 2>&1
if "!REAL_USERNAME!"=="" set "REAL_USERNAME=%USERNAME%"
set "REAL_USERPROFILE=C:\Users\!REAL_USERNAME!"

rem =====================================================
rem install.bat - Orchestration Kit (Windows)
rem
rem Usage:
rem   install.bat [path]          Install only
rem   install.bat anl [path]      Install + source analysis
rem
rem Examples:
rem   install.bat C:\projects\myapp
rem   install.bat anl C:\projects\myapp
rem   install.bat anl .
rem =====================================================

echo.
echo ============================================================
echo   Orchestration Kit
echo ============================================================

rem --- Parse: install.bat anl [path] OR install.bat [path] OR install.bat restart ---
set ANALYZE_MODE=false
set TARGET=

if /i "%~1"=="restart" goto DO_RESTART
if /i "%~1"=="delete" goto DO_DELETE

if /i "%~1"=="anl" (
  set ANALYZE_MODE=true
  if not "%~2"=="" ( set TARGET=%~2 ) else ( set TARGET=%CD% )
) else (
  if not "%~1"=="" ( set TARGET=%~1 ) else ( set TARGET=%CD% )
)

set SCRIPT_DIR=%~dp0

rem --- Strip trailing spaces and backslashes from TARGET ---
:TRIM_TARGET
if "!TARGET:~-1!"==" "  set "TARGET=!TARGET:~0,-1!" & goto TRIM_TARGET
if "!TARGET:~-1!"=="\"  set "TARGET=!TARGET:~0,-1!" & goto TRIM_TARGET

echo   Mode   : %ANALYZE_MODE% (analyze=%ANALYZE_MODE%)
echo   Target : %TARGET%
echo ============================================================

if not exist "%TARGET%" (
  echo [+] Folder not found - creating: %TARGET%
  mkdir "%TARGET%" >nul 2>&1
  if not exist "%TARGET%" (
    echo [ERROR] Failed to create folder: %TARGET%
    pause & exit /b 1
  )
  echo       Done
)

rem -----------------------------------------
rem [1/5] Backup
rem -----------------------------------------
if exist "%TARGET%\.claude" (
  set BNAME=.claude_backup_%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
  set BNAME=!BNAME: =0!
  echo [1/5] Backing up existing .claude...
  robocopy "%TARGET%\.claude" "%TARGET%\!BNAME!" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1
  echo       Done
) else (
  echo [1/5] Fresh install
)

rem -----------------------------------------
rem [2/5] Copy .claude folder
rem -----------------------------------------
echo [2/5] Installing .claude folder...
if not exist "%TARGET%\.claude" mkdir "%TARGET%\.claude"

robocopy "%SCRIPT_DIR%.claude" "%TARGET%\.claude" /E /NFL /NDL /NJH /NJS /NP >nul 2>&1

if exist "%SCRIPT_DIR%CLAUDE.md" (
  copy /Y "%SCRIPT_DIR%CLAUDE.md" "%TARGET%\CLAUDE.md" >nul
)
echo       Done

rem -----------------------------------------
rem [3/5] Create docs + context/templates/outputs folders
rem -----------------------------------------
echo [3/5] Creating docs folders...
if not exist "%TARGET%\docs\adr"             mkdir "%TARGET%\docs\adr"             >nul 2>&1
if not exist "%TARGET%\docs\deploy-history"  mkdir "%TARGET%\docs\deploy-history"  >nul 2>&1
if not exist "%TARGET%\docs\screens"         mkdir "%TARGET%\docs\screens"         >nul 2>&1

rem Copy design reference screens (skip if already exist)
if exist "%SCRIPT_DIR%docs\screens" (
  for %%F in ("%SCRIPT_DIR%docs\screens\*.*") do (
    if not exist "%TARGET%\docs\screens\%%~nxF" (
      copy /Y "%%F" "%TARGET%\docs\screens\%%~nxF" >nul 2>&1
    )
  )
  echo       Design screens copied to docs\screens\
)

rem context / templates / outputs (quality scaffolding)
if not exist "%TARGET%\context"   mkdir "%TARGET%\context"   >nul 2>&1
if not exist "%TARGET%\templates" mkdir "%TARGET%\templates" >nul 2>&1
if not exist "%TARGET%\outputs"   mkdir "%TARGET%\outputs"   >nul 2>&1

rem Copy sample files (skip if already exist)
if exist "%SCRIPT_DIR%context\rules.md"            if not exist "%TARGET%\context\rules.md"            copy /Y "%SCRIPT_DIR%context\rules.md"            "%TARGET%\context\rules.md"            >nul 2>&1
if exist "%SCRIPT_DIR%context\project.md"          if not exist "%TARGET%\context\project.md"          copy /Y "%SCRIPT_DIR%context\project.md"          "%TARGET%\context\project.md"          >nul 2>&1
if exist "%SCRIPT_DIR%templates\prd-template.md"   if not exist "%TARGET%\templates\prd-template.md"   copy /Y "%SCRIPT_DIR%templates\prd-template.md"   "%TARGET%\templates\prd-template.md"   >nul 2>&1
if exist "%SCRIPT_DIR%templates\api-template.md"   if not exist "%TARGET%\templates\api-template.md"   copy /Y "%SCRIPT_DIR%templates\api-template.md"   "%TARGET%\templates\api-template.md"   >nul 2>&1
if exist "%SCRIPT_DIR%templates\screen-template.md" if not exist "%TARGET%\templates\screen-template.md" copy /Y "%SCRIPT_DIR%templates\screen-template.md" "%TARGET%\templates\screen-template.md" >nul 2>&1
if exist "%SCRIPT_DIR%outputs\result-sample.md"    if not exist "%TARGET%\outputs\result-sample.md"    copy /Y "%SCRIPT_DIR%outputs\result-sample.md"    "%TARGET%\outputs\result-sample.md"    >nul 2>&1

echo       Done

rem -----------------------------------------
rem [4/5] deploy-config.env
rem -----------------------------------------
echo [4/5] Checking deploy config...
if not exist "%TARGET%\.claude\deploy-config.env" (
  if exist "%TARGET%\.claude\deploy-config.env.example" (
    copy /Y "%TARGET%\.claude\deploy-config.env.example" "%TARGET%\.claude\deploy-config.env" >nul 2>&1
    echo       deploy-config.env created - edit server info before deploy
  ) else (
    echo       deploy-config.env.example not found - skipped
  )
) else (
  echo       deploy-config.env already exists - kept
)

rem -----------------------------------------
rem [5/5] .gitignore
rem -----------------------------------------
echo [5/5] Updating .gitignore...
if not exist "%TARGET%\.gitignore" echo.> "%TARGET%\.gitignore"
findstr /C:".claude/deploy-config.env" "%TARGET%\.gitignore" >nul 2>&1 || (
  echo .claude/deploy-config.env   >> "%TARGET%\.gitignore"
  echo .claude/context-cache/      >> "%TARGET%\.gitignore"
  echo docs/secret-scan.txt        >> "%TARGET%\.gitignore"
  echo docs/build-result.txt       >> "%TARGET%\.gitignore"
)
echo       Done

rem -----------------------------------------
rem [+] Windows Defender 예외 추가 (.claude 폴더)
rem -----------------------------------------
echo [+] Adding Windows Defender exclusion for .claude folder...
echo [STEP] Defender exclusion start %TIME% >> "!LOGFILE!"
set "DEFENDER_PATH1=!REAL_USERPROFILE!\.claude"
set "DEFENDER_PATH2=%APPDATA%\npm"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$svc=Get-Service -Name WinDefend -ErrorAction SilentlyContinue; if($svc -and $svc.Status -eq 'Running'){ try { Add-MpPreference -ExclusionPath '!DEFENDER_PATH1!' -ErrorAction Stop; Write-Host 'Defender OK' } catch { Write-Host ('Defender WARN: ' + $_.Exception.Message) } } else { Write-Host 'Defender service not running - skipped' }" >> "!LOGFILE!" 2>&1
echo [STEP] Defender exclusion done %TIME% >> "!LOGFILE!"
echo       Done

rem -----------------------------------------
rem [+] status-push.bat + Task Scheduler
rem -----------------------------------------
echo [STEP] status-push start %TIME% >> "!LOGFILE!"
echo [+] Installing status-push files...
if not exist "!REAL_USERPROFILE!\.claude" mkdir "!REAL_USERPROFILE!\.claude" >nul 2>&1
if not exist "%SCRIPT_DIR%status-push.ps1" goto SP_SKIP

copy /Y "%SCRIPT_DIR%status-push.ps1"         "!REAL_USERPROFILE!\.claude\status-push.ps1"         >nul 2>&1
copy /Y "%SCRIPT_DIR%status-push-silent.vbs"  "!REAL_USERPROFILE!\.claude\status-push-silent.vbs"  >nul 2>&1
copy /Y "%SCRIPT_DIR%remote-agent.ps1"         "!REAL_USERPROFILE!\.claude\remote-agent.ps1"         >nul 2>&1
copy /Y "%SCRIPT_DIR%remote-agent-silent.vbs" "!REAL_USERPROFILE!\.claude\remote-agent-silent.vbs" >nul 2>&1
echo       Copied to !REAL_USERPROFILE!\.claude\
echo [LOG] copy done %TIME% >> "!LOGFILE!"

rem Try to download latest status-push.ps1 from GitHub repo
where git >nul 2>&1
if errorlevel 1 goto SP_SKIP_GIT
echo       Attempting to download latest status-push.ps1 from GitHub...
set "SP_DEST=!REAL_USERPROFILE!\.claude\status-push.ps1"
powershell -NoProfile -Command "try { $pat=[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User'); $headers=@{Accept='application/vnd.github.v3.raw'}; if($pat){$headers['Authorization']=('token ' + $pat)}; $url='https://api.github.com/repos/bernakilljos/orchestration/contents/status-push.ps1'; $r=Invoke-WebRequest -Uri $url -Headers $headers -TimeoutSec 10 -ErrorAction Stop; [System.IO.File]::WriteAllBytes('!SP_DEST!', $r.Content); Write-Host '      Latest downloaded' } catch { Write-Host '      GitHub download failed - using kit version' }" 2>nul
:SP_SKIP_GIT
echo [LOG] github done %TIME% >> "!LOGFILE!"

rem Register this project path in status-projects.txt
set "PROJ_CONFIG=!REAL_USERPROFILE!\.claude\status-projects.txt"
if not exist "!PROJ_CONFIG!" echo.> "!PROJ_CONFIG!"
findstr /i /x /c:"%TARGET%" "!PROJ_CONFIG!" >nul 2>&1
if errorlevel 1 echo %TARGET%>> "!PROJ_CONFIG!"
echo       Registered project: %TARGET%

rem Cleanup: 중복 제거 + 존재하지 않는 경로 제거
powershell -NoProfile -Command "$f='!PROJ_CONFIG!';$lines=Get-Content $f -Encoding UTF8 -ErrorAction SilentlyContinue|Where-Object{$_.Trim()-ne''};$clean=@();$seen=@{};foreach($l in $lines){$n=$l.Trim().Replace('/','\').TrimEnd('\');if(-not $n){continue}if($n.Length -lt 3 -or $n -notmatch '^[A-Za-z]:\\'){continue}if($seen[$n.ToLower()]){continue}if(-not(Test-Path $n -PathType Container)){continue}if(-not(Test-Path ($n+'\.claude'))){continue}$seen[$n.ToLower()]=$true;$clean+=$n};Set-Content $f $clean -Encoding UTF8;Write-Host ('      Projects: '+$clean.Count)" 2>nul
echo [LOG] cleanup done %TIME% >> "!LOGFILE!"

rem --- status-push / remote-agent 등록 + 실행 ---
set "VBS_PATH=!REAL_USERPROFILE!\.claude\status-push-silent.vbs"
set "RA_VBS=!REAL_USERPROFILE!\.claude\remote-agent-silent.vbs"
set "SVC_FAIL=0"

echo [LOG] registry start %TIME% >> "!LOGFILE!"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationStatusPush" /t REG_SZ /d "wscript.exe \"!VBS_PATH!\"" /f >nul 2>&1
if not errorlevel 1 (echo       status-push registered) else (echo [WARN] status-push registration failed & set "SVC_FAIL=1")

set "SP_OK=0"
start "" wscript "!VBS_PATH!" >nul 2>&1
if not errorlevel 1 set "SP_OK=1"
if "!SP_OK!"=="0" (
  powershell -NoProfile -Command "Start-Process wscript -ArgumentList '!VBS_PATH!' -Verb RunAs -ErrorAction SilentlyContinue" >nul 2>&1
  timeout /t 2 /nobreak >nul
  start "" wscript "!VBS_PATH!" >nul 2>&1
  if not errorlevel 1 set "SP_OK=1"
)
if "!SP_OK!"=="1" (echo       status-push started) else (echo [WARN] status-push 실행 실패 & set "SVC_FAIL=1")
echo [LOG] sp done %TIME% >> "!LOGFILE!"
goto SP_END
:SP_SKIP
echo [WARN] status-push.ps1 not found in kit folder - skipped
:SP_END


rem --- Remote Agent: 기존 종료 + 재등록 + 재시작 ---
echo [+] Registering remote-agent (auto-start at logon)...
rem 기존 프로세스 종료
taskkill /f /fi "WINDOWTITLE eq remote-agent*" >nul 2>&1
wmic process where "CommandLine like '%%remote-agent%%'" call terminate >nul 2>&1
timeout /t 1 /nobreak >nul

rem 1) Registry Run 키 등록
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationRemoteAgent" /t REG_SZ /d "wscript.exe \"!RA_VBS!\"" /f >nul 2>&1
if not errorlevel 1 (
  echo       Remote agent registered ^(Registry Run key^)
) else (
  echo [WARN] Remote agent registration failed
  set "SVC_FAIL=1"
)

rem 2) 즉시 실행: 일반 → 실패 시 관리자 → 실패 시 일반 재시도
set "RA_OK=0"
start "" wscript "!RA_VBS!" >nul 2>&1
if not errorlevel 1 set "RA_OK=1"
if "!RA_OK!"=="0" (
  echo       [retry 1/2] 관리자 모드로 재시도...
  powershell -NoProfile -Command "Start-Process wscript -ArgumentList @('!RA_VBS!') -Verb RunAs -ErrorAction SilentlyContinue" >nul 2>&1
  timeout /t 2 /nobreak >nul
  start "" wscript "!RA_VBS!" >nul 2>&1
  if not errorlevel 1 set "RA_OK=1"
)
if "!RA_OK!"=="0" (
  echo       [retry 2/2] 일반 모드로 재시도...
  wscript "!RA_VBS!" >nul 2>&1
  if not errorlevel 1 set "RA_OK=1"
)
if "!RA_OK!"=="1" (
  echo       Remote agent started
) else (
  echo [WARN] remote-agent 실행 실패
  set "SVC_FAIL=1"
)

rem 3) 실패 시 가이드 안내
if "!SVC_FAIL!"=="1" (
  echo.
  echo ============================================================
  echo   [!] status-push / remote-agent 자동 실행에 실패했습니다.
  echo       수동 실행 방법:
  echo         1. 탐색기에서 더블클릭:
  echo            !VBS_PATH!
  echo            !RA_VBS!
  echo         2. 또는 CMD ^(관리자^)에서:
  echo            wscript "!VBS_PATH!"
  echo            wscript "!RA_VBS!"
  echo         3. Claude 첫 실행 시 CLAUDE_SETUP_GUIDE.md 에서 자동 재시도
  echo   자세한 내용: guide.txt 참고
  echo ============================================================
  echo.
)

rem --- RDP 원격 데스크탑 활성화 ---
echo [+] Enabling Remote Desktop (RDP)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name 'fDenyTSConnections' -Value 0 -Force; Enable-NetFirewallRule -DisplayGroup 'Remote Desktop' -ErrorAction SilentlyContinue; Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name 'UserAuthentication' -Value 1 -Force -ErrorAction SilentlyContinue" >nul 2>&1
if not errorlevel 1 (
  echo       RDP enabled
) else (
  echo [WARN] RDP 활성화 실패 - 수동으로 켜주세요
)

rem --- CRLF fix: .bat scripts (no LF-only wrappers) ---
echo [+] Ensuring CRLF line endings in scripts...
powershell -NoProfile -Command "$enc = New-Object System.Text.UTF8Encoding($false); Get-ChildItem '%TARGET%\.claude\scripts' -Filter '*.bat' -File -ErrorAction SilentlyContinue | ForEach-Object { $c = Get-Content $_.FullName -Raw -Encoding UTF8; $c = $c -replace '\r?\n', ([char]13+[char]10); [System.IO.File]::WriteAllText($_.FullName, $c, $enc) }" >nul 2>&1
if errorlevel 1 (
  echo [WARN] Failed to normalize .claude\scripts\*.bat line endings
) else (
  echo       Done
)

rem -----------------------------------------
rem PowerShell Profile - UTF-8 OutputEncoding
rem -----------------------------------------
echo [+] Setting PowerShell profile UTF-8 encoding...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$lines = @('[Console]::OutputEncoding = [System.Text.Encoding]::UTF8', '$OutputEncoding = [System.Text.Encoding]::UTF8'); foreach ($prof in @($PROFILE.CurrentUserAllHosts, $PROFILE.CurrentUserCurrentHost)) { try { $dir = Split-Path $prof; if (!(Test-Path $dir)) { New-Item $dir -ItemType Directory -Force | Out-Null }; $cur = if (Test-Path $prof) { Get-Content $prof -Raw -Encoding UTF8 } else { '' }; $add = $lines | Where-Object { $cur -notmatch [regex]::Escape($_) }; if ($add) { ($cur.TrimEnd() + \"`n\" + ($add -join \"`n\") + \"`n\") | Set-Content $prof -Encoding UTF8 } } catch {} }" >nul 2>&1
echo       Done

rem -----------------------------------------
rem Install global commands (codex-a, gemini-a) - AFTER encoding fix
rem -----------------------------------------
echo [+] Installing global commands...
if not exist "%APPDATA%\npm" mkdir "%APPDATA%\npm" >nul 2>&1
for %%F in (codex-a codex-auto gemini-a gemini-auto gemini-verify claude-auto) do (
  if exist "%TARGET%\.claude\scripts\%%F.bat" (
    if exist "%APPDATA%\npm\%%F.bat" attrib -r "%APPDATA%\npm\%%F.bat" >nul 2>&1
    copy /Y "%TARGET%\.claude\scripts\%%F.bat" "%APPDATA%\npm\%%F.bat" >nul 2>&1
    if exist "%APPDATA%\npm\%%F.bat" (
      echo       %%F.bat -^> %APPDATA%\npm\
    ) else (
      echo [WARN] %%F.bat copy failed - run as administrator
    )
  )
)
echo [+] Normalizing global command wrappers (CRLF)...
powershell -NoProfile -Command "$enc = New-Object System.Text.UTF8Encoding($false); foreach($n in 'codex-a','codex-auto','gemini-a','gemini-auto','gemini-verify','claude-auto'){ $p = Join-Path '%APPDATA%\npm' ($n + '.bat'); if(Test-Path $p){ $c = Get-Content $p -Raw -Encoding UTF8; $c = $c -replace '\r?\n', ([char]13+[char]10); [System.IO.File]::WriteAllText($p, $c, $enc) } }" >nul 2>&1
if errorlevel 1 (
  echo [WARN] Failed to normalize one or more global wrappers in %APPDATA%\npm
) else (
  echo       Done
)

rem --- Orca-auto 활성화 플래그 생성 (orca-stopped 없을 때만) ---
if not exist "%TARGET%\.claude\orca-stopped" (
  if not exist "%TARGET%\.claude\orca-enabled" (
    echo enabled > "%TARGET%\.claude\orca-enabled"
    echo       Orca-auto enabled ^(workers auto-start when Claude opens^)
  )
)

rem --- claude settings: bypassPermissions + autoUpdatesChannel + checkpointing ---
echo [+] Configuring claude global settings...
if not exist "!REAL_USERPROFILE!\.claude" mkdir "!REAL_USERPROFILE!\.claude" >nul 2>&1
powershell -NoProfile -Command "$f = '!REAL_USERPROFILE!\.claude\settings.json'; if (Test-Path $f) { $j = Get-Content $f -Raw | ConvertFrom-Json } else { $j = [PSCustomObject]@{} }; if (-not $j.PSObject.Properties['permissions']) { $j | Add-Member -NotePropertyName 'permissions' -NotePropertyValue ([PSCustomObject]@{}) }; $j.permissions | Add-Member -NotePropertyName 'defaultMode' -NotePropertyValue 'bypassPermissions' -Force; $j | Add-Member -NotePropertyName 'skipDangerousModePermissionPrompt' -NotePropertyValue $true -Force; $j | Add-Member -NotePropertyName 'autoUpdatesChannel' -NotePropertyValue 'latest' -Force; $j | Add-Member -NotePropertyName 'checkpointingEnabled' -NotePropertyValue $true -Force; $j | ConvertTo-Json -Depth 10 | Set-Content $f -Encoding UTF8" >nul 2>&1
echo       Done

echo [CHECKPOINT 1/3] %TIME% >> "!LOGFILE!"
echo.
echo ============================================================
echo   [체크포인트 1/3] 기본 설치 완료
echo   계속하려면 아무 키나 누르세요...
echo ============================================================
pause >nul

rem --- Install Claude plugins ---
echo [+] Installing Claude plugins...
where claude >nul 2>&1
if not errorlevel 1 (
  rem 마켓플레이스 업데이트 (30초 타임아웃)
  powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','marketplace','update') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  rem 설치된 목록 확인 (15초 타임아웃)
  set "PLUGIN_LIST_CACHE="
  for /f "delims=" %%L in ('powershell -NoProfile -Command "$j=Start-Job{claude plugin list 2>$null};if(Wait-Job $j -Timeout 15){Receive-Job $j}else{Remove-Job $j -Force}" 2^>nul') do set "PLUGIN_LIST_CACHE=!PLUGIN_LIST_CACHE! %%L"
  echo "!PLUGIN_LIST_CACHE!" | findstr /C:"claude-md-management" >nul 2>&1 || (
    echo       Installing claude-md-management...
    powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','install','claude-md-management') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  )
  echo "!PLUGIN_LIST_CACHE!" | findstr /C:"code-review" >nul 2>&1 || (
    echo       Installing code-review...
    powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','install','code-review') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  )
  echo "!PLUGIN_LIST_CACHE!" | findstr /C:"commit-commands" >nul 2>&1 || (
    echo       Installing commit-commands...
    powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','install','commit-commands') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
  )
  echo "!PLUGIN_LIST_CACHE!" | findstr /C:"superpowers" >nul 2>&1 || (
    echo       Adding superpowers marketplace...
    powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','marketplace','add','obra/superpowers-marketplace') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
    echo       Installing superpowers...
    powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','install','superpowers@superpowers-marketplace') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(60000)){$p.Kill()}}" >nul 2>&1
  )
  for %%P in (ui-ux-pro-max everything-claude-code awesome-claude-code get-shit-done) do (
    echo "!PLUGIN_LIST_CACHE!" | findstr /C:"%%P" >nul 2>&1 || (
      echo       Installing %%P...
      powershell -NoProfile -Command "$p=Start-Process 'claude' -ArgumentList @('plugin','install','%%P') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(30000)){$p.Kill()}}" >nul 2>&1
    )
  )
  echo       Plugins Done
) else (
  echo [WARN] claude not found - plugins will be installed after Claude install
)

rem --- Copy CLAUDE_SETUP_GUIDE.md to target docs ---
echo [+] Copying setup guide...
if exist "%SCRIPT_DIR%docs\CLAUDE_SETUP_GUIDE.md" (
  if not exist "%TARGET%\docs" mkdir "%TARGET%\docs" >nul 2>&1
  copy /Y "%SCRIPT_DIR%docs\CLAUDE_SETUP_GUIDE.md" "%TARGET%\docs\CLAUDE_SETUP_GUIDE.md" >nul 2>&1
  echo       CLAUDE_SETUP_GUIDE.md -^> docs\
)

rem --- Check API Key environment variables ---
echo [+] Checking API keys...
set "KEY_MISSING=0"
if not defined ANTHROPIC_API_KEY (
  echo [WARN] ANTHROPIC_API_KEY not set - Claude API calls will fail
  set "KEY_MISSING=1"
) else (
  echo       ANTHROPIC_API_KEY = configured
)
if not defined OPENAI_API_KEY (
  echo [WARN] OPENAI_API_KEY not set - Codex will not work
  set "KEY_MISSING=1"
) else (
  echo       OPENAI_API_KEY   = configured
)
if not defined GEMINI_API_KEY (
  echo [WARN] GEMINI_API_KEY not set - Gemini will not work
  set "KEY_MISSING=1"
) else (
  echo       GEMINI_API_KEY   = configured
)

rem --- GitHub PAT ---
echo [+] GitHub PAT 확인 중...
set "FALLBACK_PAT=%GITHUB_PERSONAL_ACCESS_TOKEN%"

rem 1) User 환경변수에 저장된 PAT 확인 (temp file - for/f 싱글쿼트 파싱 오류 방지)
powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')" > "%TEMP%\_ghpat_saved.txt" 2>nul
set "SAVED_PAT="
set /p "SAVED_PAT=" < "%TEMP%\_ghpat_saved.txt"
del "%TEMP%\_ghpat_saved.txt" >nul 2>&1

if not "!SAVED_PAT!"=="" (
  rem 저장된 PAT 유효성 테스트
  powershell -NoProfile -Command "$r=Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers @{Authorization='token !SAVED_PAT!'} -ErrorAction SilentlyContinue; exit ($r.login -eq $null)" >nul 2>&1
  if not errorlevel 1 (
    echo       GITHUB_PAT = configured [OK]
    goto SKIP_GITHUB_PAT
  )
  echo [WARN] 저장된 PAT 가 유효하지 않습니다.
)

rem 2) Fallback PAT 테스트
powershell -NoProfile -Command "$r=Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers @{Authorization='token !FALLBACK_PAT!'} -ErrorAction SilentlyContinue; exit ($r.login -eq $null)" >nul 2>&1
if not errorlevel 1 (
  echo       Fallback PAT 유효 - 환경변수에 저장합니다.
  powershell -NoProfile -Command "[System.Environment]::SetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','!FALLBACK_PAT!','User')" >nul 2>&1
  echo       GITHUB_PAT = saved [OK]
  goto SKIP_GITHUB_PAT
)

rem 3) 둘 다 실패 - rate limit 가능성 있으므로 fallback PAT 그냥 저장 후 계속
echo [WARN] PAT 검증 실패 ^(rate limit 또는 만료^) - fallback PAT 사용
powershell -NoProfile -Command "[System.Environment]::SetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','!FALLBACK_PAT!','User')" >nul 2>&1
:SKIP_GITHUB_PAT

rem --- 최종 PAT 값을 GITHUB_PAT 변수에 저장 (temp file) ---
powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')" > "%TEMP%\_ghpat_final.txt" 2>nul
set "GITHUB_PAT="
set /p "GITHUB_PAT=" < "%TEMP%\_ghpat_final.txt"
del "%TEMP%\_ghpat_final.txt" >nul 2>&1
if "!GITHUB_PAT!"=="" set "GITHUB_PAT=!FALLBACK_PAT!"

echo [CHECKPOINT 2/3] %TIME% >> "!LOGFILE!"
echo.
echo ============================================================
echo   [체크포인트 2/3] 플러그인/MCP/설정 완료
echo   계속하려면 아무 키나 누르세요...
echo ============================================================
pause >nul

rem -----------------------------------------
rem GitHub 프로젝트 생성 + Git 초기화
rem -----------------------------------------
echo [STEP] GitHub init start %TIME% >> "!LOGFILE!"
echo.
echo ============================================================
echo   GitHub 프로젝트 설정
echo ============================================================
where git >nul 2>&1
if errorlevel 1 (
  echo [WARN] git not found - GitHub 프로젝트 생성 건너뜀
  goto SKIP_GITHUB_INIT
)

if exist "%TARGET%\.git" (
  echo [OK] git already initialized in %TARGET%
  goto SKIP_GITHUB_INIT
)

rem 프로젝트 이름 추출 (폴더명, 공백→하이픈)
for %%P in ("%TARGET%") do set "PROJ_BASE=%%~nxP"
set "PROJ_BASE=!PROJ_BASE: =-!"

rem GitHub 저장소 생성 (같은 이름 있으면 -2, -3 ... 순서로)
echo [+] GitHub 저장소 생성 중: !PROJ_BASE! ...
set "GH_REPO_URL="
powershell -NoProfile -ExecutionPolicy Bypass -Command "$pat='!GITHUB_PAT!'; $base='!PROJ_BASE!'; $headers=@{Authorization=('token ' + $pat);Accept='application/vnd.github.v3+json'}; $url=''; for($i=0;$i-le10;$i++){$name=if($i-eq0){$base}else{$base+'-'+$i}; try{ $b=@{name=$name;private=$false;auto_init=$false}|ConvertTo-Json; $r=Invoke-RestMethod -Uri 'https://api.github.com/user/repos' -Method Post -Headers $headers -Body $b -ContentType 'application/json' -ErrorAction Stop -TimeoutSec 15; $url=$r.clone_url; break }catch{ if($_.Exception.Response.StatusCode.value__ -eq 422){continue}else{Write-Host ('[WARN] GitHub API: ' + $_.Exception.Message); break} }}; if($url){$url|Set-Content ('!TARGET!\.github-repo-url.txt') -Encoding UTF8; Write-Host ('[OK] 저장소: ' + $url)}else{Write-Host '[WARN] GitHub 저장소 생성 실패'}"

rem git 초기화 + 원격 연결 + 초기 커밋
if exist "%TARGET%\.github-repo-url.txt" (
  for /f "tokens=*" %%U in ("%TARGET%\.github-repo-url.txt") do set "GH_REPO_URL=%%U"
)
cd /d "%TARGET%"
git init >nul 2>&1
if not "!GH_REPO_URL!"=="" (
  git remote add origin "!GH_REPO_URL!" >nul 2>&1
  echo [OK] Remote: !GH_REPO_URL!
)
if not exist "%TARGET%\.gitignore" (
  (
    echo node_modules/
    echo .env
    echo .env.local
    echo *.log
    echo .claude/context-cache/
    echo .claude/tasks/locks/
    echo .claude/orca-heartbeat
  ) > "%TARGET%\.gitignore"
)
git add . >nul 2>&1
git commit -m "Initial commit from orchestration install" >nul 2>&1
if not errorlevel 1 (
  echo [OK] 초기 커밋 완료
  if not "!GH_REPO_URL!"=="" (
    echo [INFO] Push는 Claude 실행 후 직접 하거나 codex-auto가 자동으로 합니다
    echo         git push -u origin main
  )
)

:SKIP_GITHUB_INIT
echo [STEP] GitHub init done %TIME% >> "!LOGFILE!"

rem --- MCP servers: CLAUDE_SETUP_GUIDE.md 가 Claude 첫 실행 시 자동 처리 ---
rem    install.bat에서는 MCP 설치 안 함 (claude mcp add가 TTY 대기로 hang 발생)
echo [+] MCP servers: Claude 첫 실행 시 CLAUDE_SETUP_GUIDE.md 자동 처리
echo [STEP] MCP skipped %TIME% >> "!LOGFILE!"

if "!KEY_MISSING!"=="1" (
  echo.
  echo       Set missing keys as system environment variables:
  echo         setx ANTHROPIC_API_KEY "sk-ant-..."
  echo         setx OPENAI_API_KEY "sk-..."
  echo         setx GEMINI_API_KEY "AI..."
)
echo [STEP] MCP done, starting npm tools %TIME% >> "!LOGFILE!"
echo.
echo ============================================================
echo   Installing npm CLI tools
echo ============================================================
where npm >nul 2>&1
if not errorlevel 1 goto CHECK_CODEX
echo Node.js not found.
set /p "INSTALL_NODE=Node.js 설치? [Y/N] (기본:Y, 엔터=Y): "
if /i "!INSTALL_NODE!"=="N" goto SKIP_NPM
where winget >nul 2>&1
if errorlevel 1 (
  echo [WARN] winget not found - install manually: https://nodejs.org
  goto SKIP_NPM
)
call winget install --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
if errorlevel 1 (
  echo [WARN] Node.js install failed - install manually: https://nodejs.org
  goto SKIP_NPM
)
echo [OK] Node.js installed - reloading PATH...
call refreshenv >nul 2>&1
set "PATH=!PATH!;%ProgramFiles%\nodejs"
where npm >nul 2>&1
if errorlevel 1 (
  echo [WARN] npm still not found - open a new terminal and re-run install.bat
  goto SKIP_NPM
)

:CHECK_CODEX
where codex >nul 2>&1
if not errorlevel 1 (
  echo [OK] codex already installed
  goto CHECK_GEMINI
)
set /p "INSTALL_CODEX=@openai/codex 설치? [Y/N] (기본:Y, 엔터=Y): "
if /i "!INSTALL_CODEX!"=="N" goto CHECK_GEMINI
echo [+] Installing @openai/codex...
call npm install -g @openai/codex

:CHECK_GEMINI
where gemini >nul 2>&1
if not errorlevel 1 (
  echo [OK] gemini already installed
  goto SKIP_NPM
)
set /p "INSTALL_GEMINI=@google/gemini-cli 설치? [Y/N] (기본:Y, 엔터=Y): "
if /i "!INSTALL_GEMINI!"=="N" goto SKIP_NPM
echo [+] Installing @google/gemini-cli...
call npm install -g @google/gemini-cli

:SKIP_NPM
echo.

rem -----------------------------------------
rem cloudflared (Tunnel)
rem -----------------------------------------
echo.
echo ============================================================
echo   Cloudflared (Tunnel)
echo ============================================================
rem WinGet Links 경로를 사용자 PATH에 영구 등록
set "WINGET_LINKS=!LOCALAPPDATA!\Microsoft\WinGet\Links"
set "PATH=!PATH!;!WINGET_LINKS!"
powershell -NoProfile -Command "$p=[System.Environment]::GetEnvironmentVariable('Path','User'); if($p -notmatch 'WinGet\\Links'){[System.Environment]::SetEnvironmentVariable('Path',$p+';!WINGET_LINKS!','User')}" >nul 2>&1

where cloudflared >nul 2>&1
if errorlevel 1 (
  echo [+] Installing cloudflared...
  winget install Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
  rem winget 설치 후 PATH에 Packages 경로도 추가
  set "CF_FOUND=0"
  where cloudflared >nul 2>&1 && set "CF_FOUND=1"
  if "!CF_FOUND!"=="0" (
    for /f "tokens=*" %%F in ('dir /s /b "!LOCALAPPDATA!\Microsoft\WinGet\Packages\cloudflared.exe" 2^>nul') do (
      set "CF_DIR=%%~dpF"
      set "PATH=!PATH!;!CF_DIR!"
      powershell -NoProfile -Command "$p=[System.Environment]::GetEnvironmentVariable('Path','User'); if($p -notmatch 'cloudflared'){[System.Environment]::SetEnvironmentVariable('Path',$p+';!CF_DIR!','User')}" >nul 2>&1
      set "CF_FOUND=1"
    )
  )
  if "!CF_FOUND!"=="1" (
    echo       cloudflared installed
  ) else (
    echo [WARN] cloudflared 설치 실패
    echo        수동 설치: winget install Cloudflare.cloudflared
  )
) else (
  echo [OK] cloudflared already installed
)
echo.

rem -----------------------------------------
rem CLI Check
rem -----------------------------------------
echo.
echo ============================================================
echo   CLI Environment Check
echo ============================================================
where claude      >nul 2>&1 && echo [OK] claude       || echo [X]  claude       - https://docs.anthropic.com/claude-code
where codex       >nul 2>&1 && echo [OK] codex        || echo [X]  codex        - npm install -g @openai/codex
where codex-a     >nul 2>&1 && echo [OK] codex-a      || echo [X]  codex-a      (auto-installed above)
where gemini      >nul 2>&1 && echo [OK] gemini       || echo [X]  gemini       - npm install -g @google/gemini-cli
where gemini-a    >nul 2>&1 && echo [OK] gemini-a     || echo [X]  gemini-a     (auto-installed above)
where cloudflared >nul 2>&1 && echo [OK] cloudflared  || echo [X]  cloudflared  - winget install Cloudflare.cloudflared
where git         >nul 2>&1 && echo [OK] git          || echo [X]  git          - https://git-scm.com
echo.

rem -----------------------------------------
rem Init
rem -----------------------------------------
echo ============================================================
echo   Project Init
echo ============================================================
if exist "%TARGET%\.claude\scripts\init.bat" (
  call "%TARGET%\.claude\scripts\init.bat" "%TARGET%"
) else (
  echo [WARN] init.bat not found - skipping
)

rem -----------------------------------------
rem [ANL] Source Analysis (only if anl mode)
rem -----------------------------------------
if "%ANALYZE_MODE%"=="true" (
  echo.
  echo ============================================================
  echo   Source Analysis Mode
  echo ============================================================
  if exist "%TARGET%\.claude\scripts\analyze.bat" (
    call "%TARGET%\.claude\scripts\analyze.bat" "%TARGET%"
  ) else (
    echo [WARN] analyze.bat not found - skipping
  )
)

rem -----------------------------------------
rem npm install (if package.json exists in target)
rem -----------------------------------------
if exist "%TARGET%\package.json" (
  echo.
  echo ============================================================
  echo   Installing project dependencies
  echo ============================================================
  cd /d "%TARGET%"
  call npm install
  echo       Done
)

echo [STEP] Starting Claude Code native install %TIME% >> "!LOGFILE!"
rem -----------------------------------------
rem Install Claude Code native (if not already)
rem -----------------------------------------
echo.
echo ============================================================
echo   Claude Code Native Install
echo ============================================================
where claude >nul 2>&1
if errorlevel 1 (
  echo [+] Claude Code not found - installing native version...
  where winget >nul 2>&1
  if not errorlevel 1 (
    call winget install Anthropic.ClaudeCode --accept-source-agreements --accept-package-agreements
    echo [OK] Claude Code native installed
    call refreshenv >nul 2>&1
  ) else (
    echo [WARN] winget not found - install manually: https://claude.ai/download/cli
  )
) else (
  echo [OK] Claude Code already installed
  echo [+] Checking for updates ^(60s timeout^)...
  powershell -NoProfile -Command "$p=Start-Process 'winget' -ArgumentList @('upgrade','--id','Anthropic.ClaudeCode','--accept-source-agreements','--accept-package-agreements') -NoNewWindow -PassThru -ErrorAction SilentlyContinue; if($p){if(-not $p.WaitForExit(60000)){$p.Kill(); Write-Host '[WARN] winget upgrade timeout - 건너뜀'}else{Write-Host '[OK] Claude Code updated'}}" 2>nul
)

rem -----------------------------------------
rem Claude 실행
rem -----------------------------------------
echo [CHECKPOINT 3/3] %TIME% >> "!LOGFILE!"
echo.
echo ============================================================
echo   [체크포인트 3/3] 모든 설치 완료!
echo   로그: %TEMP%\orchestration-install.log
echo.
where claude >nul 2>&1
if errorlevel 1 (
  echo   [WARN] claude not found in PATH
  echo          설치 후 직접 실행하세요:
  echo            cd /d "%TARGET%"
  echo            claude --dangerously-skip-permissions
  echo ============================================================
  goto INSTALL_DONE
)
echo   Claude를 지금 실행하시겠습니까?
echo     [Y] 예 - 지금 바로 Claude 시작
echo     [N] 아니오 - 창 닫기
echo ============================================================
set /p "RUN_CLAUDE=선택 [Y/N]: "
if /i "!RUN_CLAUDE!"=="Y" (
  cd /d "%TARGET%"
  echo [OK] claude --dangerously-skip-permissions 실행 중...
  echo.
  claude --dangerously-skip-permissions
)

:INSTALL_DONE
echo.
echo ============================================================
echo   설치 완료. 로그: %TEMP%\orchestration-install.log
echo   아무 키나 누르면 창이 닫힙니다.
echo ============================================================
echo [DONE] %TIME% >> "!LOGFILE!" 2>&1
pause
endlocal
exit /b

rem =====================================================
rem 이 아래는 특수 모드 (install.bat delete / restart)
rem 일반 install 흐름에서는 절대 도달하지 않음
rem =====================================================

rem -----------------------------------------
rem DELETE MODE: status-push / remote-agent 제거
rem -----------------------------------------
:DO_DELETE
echo.
echo ============================================================
echo   Delete Mode — status-push / remote-agent 제거
echo ============================================================

echo (Get-WmiObject Win32_Process ^| Where-Object {$_.Name -eq 'explorer.exe'} ^| Select-Object -First 1).GetOwner().User > "%TEMP%\_orch_getuser.ps1"
for /f "tokens=*" %%N in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\_orch_getuser.ps1"') do set "REAL_USERNAME=%%N"
del "%TEMP%\_orch_getuser.ps1" >nul 2>&1
if "!REAL_USERNAME!"=="" set "REAL_USERNAME=%USERNAME%"
set "REAL_USERPROFILE=C:\Users\!REAL_USERNAME!"

rem 1) 실행 중인 프로세스 종료
echo [1/3] Stopping running processes...
powershell -NoProfile -Command "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match 'status-push' -or $_.CommandLine -match 'remote-agent' } | ForEach-Object { $_.Terminate() }" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq remote-agent*" >nul 2>&1
echo       Done

rem 2) Registry Run 키 제거
echo [2/3] Removing Registry Run keys...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationStatusPush" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationRemoteAgent" /f >nul 2>&1
echo       Done

rem 3) status-projects.txt 에서 경로 제거
if not "%~2"=="" (
  echo [3/3] Removing project path from status-projects.txt...
  set "DEL_TARGET=%~2"
  set "PROJ_CONFIG=!REAL_USERPROFILE!\.claude\status-projects.txt"
  if exist "!PROJ_CONFIG!" (
    powershell -NoProfile -Command "$p='!PROJ_CONFIG!'; $t='!DEL_TARGET!'; $lines = Get-Content $p -Encoding UTF8 | Where-Object { $_.Trim() -ne $t.Trim() }; $lines | Set-Content $p -Encoding UTF8"
    echo       Removed: %~2
  )
) else (
  echo [3/3] No path specified — status-projects.txt unchanged
)

echo.
echo ============================================================
echo   제거 완료. 아무 키나 누르면 창이 닫힙니다.
echo ============================================================
pause >nul
endlocal
exit /b

rem -----------------------------------------
rem RESTART MODE: 서비스만 재시작
rem -----------------------------------------
:DO_RESTART
echo.
echo ============================================================
echo   Restart Mode — 서비스 재시작만 수행
echo ============================================================

echo (Get-WmiObject Win32_Process ^| Where-Object {$_.Name -eq 'explorer.exe'} ^| Select-Object -First 1).GetOwner().User > "%TEMP%\_orch_getuser.ps1"
for /f "tokens=*" %%N in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\_orch_getuser.ps1"') do set "REAL_USERNAME=%%N"
del "%TEMP%\_orch_getuser.ps1" >nul 2>&1
if "!REAL_USERNAME!"=="" set "REAL_USERNAME=%USERNAME%"
set "REAL_USERPROFILE=C:\Users\!REAL_USERNAME!"

set "SCRIPT_DIR=%~dp0"

rem --- 최신 파일 복사 ---
echo [1/3] Copying latest scripts...
if exist "%SCRIPT_DIR%status-push.ps1"         copy /Y "%SCRIPT_DIR%status-push.ps1"         "!REAL_USERPROFILE!\.claude\status-push.ps1"         >nul
if exist "%SCRIPT_DIR%status-push-silent.vbs"  copy /Y "%SCRIPT_DIR%status-push-silent.vbs"  "!REAL_USERPROFILE!\.claude\status-push-silent.vbs"  >nul
if exist "%SCRIPT_DIR%remote-agent.ps1"        copy /Y "%SCRIPT_DIR%remote-agent.ps1"        "!REAL_USERPROFILE!\.claude\remote-agent.ps1"        >nul
if exist "%SCRIPT_DIR%remote-agent-silent.vbs" copy /Y "%SCRIPT_DIR%remote-agent-silent.vbs" "!REAL_USERPROFILE!\.claude\remote-agent-silent.vbs" >nul
echo       Done

rem --- 기존 프로세스 종료 ---
echo [2/3] Stopping existing services...
taskkill /f /fi "WINDOWTITLE eq remote-agent*" >nul 2>&1
wmic process where "CommandLine like '%%remote-agent%%'" call terminate >nul 2>&1
wmic process where "CommandLine like '%%status-push%%'" call terminate >nul 2>&1
timeout /t 1 /nobreak >nul
echo       Done

rem --- 태스크 재등록 + 재시작 ---
echo [3/3] Registering and restarting services...

rem status-push 재등록 (Registry Run key)
set "VBS_PATH=!REAL_USERPROFILE!\.claude\status-push-silent.vbs"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationStatusPush" /t REG_SZ /d "wscript.exe \"!VBS_PATH!\"" /f >nul 2>&1

rem remote-agent 재등록 (Registry Run key)
set "RA_VBS=!REAL_USERPROFILE!\.claude\remote-agent-silent.vbs"
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationRemoteAgent" /t REG_SZ /d "wscript.exe \"!RA_VBS!\"" /f >nul 2>&1

rem 실행
start "" wscript "!VBS_PATH!"
echo       status-push    registered + started
start "" wscript "!RA_VBS!"
echo       remote-agent   started (background process)
echo.
echo ============================================================
echo   재시작 완료. 아무 키나 누르면 창이 닫힙니다.
echo ============================================================
pause >nul
endlocal
exit /b
