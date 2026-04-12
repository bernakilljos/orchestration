@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

rem =====================================================
rem status-push.bat - Orchestration Status Pusher
rem Runs every 1 minute via Task Scheduler
rem Project list: %USERPROFILE%\.claude\status-projects.txt
rem =====================================================

set "CONFIG=%USERPROFILE%\.claude\status-projects.txt"

rem --- PAT ---
for /f "tokens=*" %%P in ('powershell -NoProfile -Command "[System.Environment]::GetEnvironmentVariable(\"GITHUB_PERSONAL_ACCESS_TOKEN\",\"User\")"') do set "PAT=%%P"
if "!PAT!"=="" ( echo [WARN] GITHUB_PERSONAL_ACCESS_TOKEN not set - run: setx GITHUB_PERSONAL_ACCESS_TOKEN "ghp_..." & exit /b 1 )

if not exist "!CONFIG!" ( echo [WARN] No projects registered & exit /b 1 )

rem --- MAC 주소 ---
for /f "tokens=*" %%M in ('powershell -NoProfile -Command "(Get-NetAdapter | Where-Object {$_.Status -eq ''Up'' -and $_.MacAddress -ne $null -and $_.MacAddress -ne ''} | Sort-Object InterfaceIndex | Select-Object -First 1).MacAddress -replace ''-'','' -replace '':'','''') do set "MAC=%%M"
if "!MAC!"=="" for /f "tokens=*" %%M in ('powershell -NoProfile -Command "(Get-NetAdapter | Where-Object {$_.MacAddress} | Sort-Object InterfaceIndex | Select-Object -First 1).MacAddress -replace ''-'','' -replace '':'','''') do set "MAC=%%M"
if "!MAC!"=="" set "MAC=000000000000"
set "PC_ID=%COMPUTERNAME%-!MAC:~0,6!"

rem --- PowerShell로 JSON 빌드 및 Push ---
set "PS_SCRIPT=%TEMP%\status-push-!PC_ID!.ps1"
set "CONFIG_ESC=!CONFIG:\=\\!"

powershell -NoProfile -Command "Set-Content -Path '%TEMP%\status-push-cfg.txt' -Value '%CONFIG%' -Encoding UTF8"

(
echo $ErrorActionPreference = 'SilentlyContinue'
echo $pat     = '!PAT!'
echo $pcId    = '!PC_ID!'
echo $pcName  = '!COMPUTERNAME!'
echo $mac     = '!MAC!'
echo $ts      = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
echo $config  = '%USERPROFILE%\.claude\status-projects.txt'
echo $owner   = 'bernakilljos'
echo $repo    = 'orchestration-status'
echo $headers = @{Authorization="token $pat"; Accept='application/vnd.github.v3+json'}
echo.
echo function Read-Head { param($path, $lines=20)
echo   if (-not (Test-Path $path)) { return '' }
echo   try { (Get-Content $path -Encoding UTF8 -ErrorAction Stop ^| Select-Object -First $lines) -join "`n" } catch { '' }
echo }
echo function Esc { param($s) $s -replace '\\','\\' -replace '"','\"' -replace "`r`n",'\n' -replace "`n",'\n' -replace "`t",'\t' }
echo.
echo $pending=0; $runCodex=0; $runGemini=0; $runClaude=0; $done=0
echo $projects=''; $pendingList=@(); $runningList=@(); $doneList=@()
echo $taskSummary=''; $implSummary=''; $reviewSummary=''
echo $recentReport=''; $projectDetails=@()
echo.
echo $dirs = Get-Content $config -Encoding UTF8 ^| Where-Object { $_.Trim() -ne '' }
echo foreach ($pdir in $dirs) {
echo   if (-not (Test-Path "$pdir\.claude")) { continue }
echo   $pname = Split-Path $pdir -Leaf
echo   $projects += "$pname "
echo.
echo   # 프로젝트별 집계
echo   $pPending=0; $pRunCodex=0; $pRunGemini=0; $pRunClaude=0; $pDone=0
echo   $pPendList=@(); $pRunList=@(); $pDoneList=@()
echo.
echo   # Pending tasks
echo   $taskFiles = Get-ChildItem "$pdir\.claude\tasks\task-*.md" -ErrorAction SilentlyContinue
echo   foreach ($tf in $taskFiles) {
echo     if (Test-Path "$pdir\.claude\tasks\done\$($tf.Name)") { continue }
echo     $content = Get-Content $tf.FullName -Encoding UTF8 -ErrorAction SilentlyContinue -Raw
echo     if ($content -match '\[Task Title\]|\[What to build') { continue }
echo     $pending++; $pPending++
echo     $pendingList += $tf.BaseName; $pPendList += $tf.BaseName
echo     if ($taskSummary -eq '') { $taskSummary = Read-Head $tf.FullName 25 }
echo   }
echo   $tiFile = "$pdir\.claude\tasks\task-instruction.md"
echo   if ((Test-Path $tiFile) -and -not (Test-Path "$pdir\.claude\tasks\locks\task-instruction.lock")) {
echo     $tic = Get-Content $tiFile -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
echo     if ($tic -notmatch '\[Task Title\]|\[What to build') {
echo       $pending++; $pPending++
echo       $pendingList += 'task-instruction'; $pPendList += 'task-instruction'
echo       if ($taskSummary -eq '') { $taskSummary = Read-Head $tiFile 25 }
echo     }
echo   }
echo.
echo   # Running (lock files)
echo   $locks = Get-ChildItem "$pdir\.claude\tasks\locks\*.lock" -ErrorAction SilentlyContinue
echo   foreach ($lk in $locks) {
echo     $lname = $lk.BaseName
echo     $lcontent = (Get-Content $lk.FullName -ErrorAction SilentlyContinue | Select-Object -First 1)
echo     if ($lname -match '^verify-') { $runGemini++; $pRunGemini++; $ai='gemini' }
echo     elseif ($lcontent -match 'worker-') { $runCodex++; $pRunCodex++; $ai='codex' }
echo     else { $runClaude++; $pRunClaude++; $ai='claude' }
echo     $entry = @{task=$lname; worker=$lcontent; ai=$ai; project=$pname}
echo     $runningList += $entry; $pRunList += $entry
echo   }
echo.
echo   # Done tasks
echo   $doneMd = Get-ChildItem "$pdir\.claude\tasks\done\*.md" -ErrorAction SilentlyContinue ^| Sort-Object LastWriteTime -Descending
echo   $pDone = $doneMd.Count; $done += $pDone
echo   $pDoneNames = ($doneMd ^| Select-Object -First 10).BaseName
echo   $doneList += $pDoneNames; $pDoneList += $pDoneNames
echo.
echo   # Recent report
echo   $rpts = Get-ChildItem "$pdir\docs\report-*.md" -ErrorAction SilentlyContinue ^| Sort-Object LastWriteTime -Descending
echo   $pReport = if ($rpts) { $rpts[0].Name } else { '' }
echo   if ($pReport) { $recentReport = $pReport }
echo.
echo   # 요약 (프로젝트별)
echo   $pImpl   = Read-Head "$pdir\docs\implementation-report.md" 30
echo   $pReview = Read-Head "$pdir\docs\review-result.txt" 30
echo   if ($implSummary -eq '')   { $implSummary   = $pImpl }
echo   if ($reviewSummary -eq '') { $reviewSummary = $pReview }
echo.
echo   # 프로젝트 상세 배열에 추가
echo   $pRunTotal = $pRunCodex + $pRunGemini + $pRunClaude
echo   $pPendJson  = ($pPendList ^| ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
echo   $pDoneJson  = ($pDoneList ^| ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
echo   $pRunJson   = ($pRunList  ^| ForEach-Object { "{`"task`":`"$(Esc $_.task)`",`"worker`":`"$(Esc $_.worker)`",`"ai`":`"$($_.ai)`"}" }) -join ','
echo   $projectDetails += "{`"name`":`"$(Esc $pname)`",`"path`":`"$(Esc $pdir)`",`"pending`":$pPending,`"running`":$pRunTotal,`"running_codex`":$pRunCodex,`"running_gemini`":$pRunGemini,`"running_claude`":$pRunClaude,`"done`":$pDone,`"recent_report`":`"$(Esc $pReport)`",`"pending_tasks`":[$pPendJson],`"running_tasks`":[$pRunJson],`"done_tasks`":[$pDoneJson],`"impl_summary`":`"$(Esc $pImpl)`",`"review_summary`":`"$(Esc $pReview)`"}"
echo }
echo.
echo $runTotal = $runCodex + $runGemini + $runClaude
echo.
echo # JSON 빌드
echo $pendJson  = ($pendingList ^| ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
echo $doneJson  = ($doneList    ^| ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
echo $runJson   = ($runningList ^| ForEach-Object { "{`"task`":`"$(Esc $_.task)`",`"worker`":`"$(Esc $_.worker)`",`"ai`":`"$($_.ai)`",`"project`":`"$(Esc $_.project)`"}" }) -join ','
echo $projJson  = $projectDetails -join ','
echo.
echo $json = @"
echo {
echo   "pc": "$pcName",
echo   "pc_id": "$pcId",
echo   "mac": "$mac",
echo   "updated_at": "$ts",
echo   "pending": $pending,
echo   "running": $runTotal,
echo   "running_codex": $runCodex,
echo   "running_gemini": $runGemini,
echo   "running_claude": $runClaude,
echo   "done": $done,
echo   "projects": "$($projects.Trim())",
echo   "recent_report": "$recentReport",
echo   "pending_tasks": [$pendJson],
echo   "running_tasks": [$runJson],
echo   "done_tasks": [$doneJson],
echo   "project_details": [$projJson],
echo   "task_summary": "$(Esc $taskSummary)",
echo   "impl_summary": "$(Esc $implSummary)",
echo   "review_summary": "$(Esc $reviewSummary)"
echo }
echo "@
echo.
echo $tmpFile = "$env:TEMP\$pcId-status.json"
echo [System.IO.File]::WriteAllText($tmpFile, $json, [System.Text.Encoding]::UTF8)
echo.
echo # --- Git Push (API rate limit 무관) ---
echo $repoUrl = "https://x:$pat@github.com/$owner/$repo.git"
echo $gitDir = "$env:TEMP\orch-push-$pcId"
echo if (Test-Path $gitDir) { Remove-Item $gitDir -Recurse -Force -ErrorAction SilentlyContinue }
echo git clone --depth 1 $repoUrl $gitDir 2^>^&1 ^| Out-Null
echo if (-not (Test-Path $gitDir)) { Write-Host '[WARN] git clone failed'; exit 1 }
echo.
echo # 현재 상태 저장
echo $statusDir = "$gitDir\status"
echo if (-not (Test-Path $statusDir)) { New-Item $statusDir -ItemType Directory -Force ^| Out-Null }
echo Copy-Item $tmpFile "$statusDir\$pcId.json" -Force
echo.
echo # 이력 저장
echo $tsFile = $ts -replace '[:\-T]','' -replace 'Z',''
echo $histDir = "$gitDir\history\$pcId"
echo if (-not (Test-Path $histDir)) { New-Item $histDir -ItemType Directory -Force ^| Out-Null }
echo Copy-Item $tmpFile "$histDir\$tsFile.json" -Force
echo.
echo # Incoming 태스크 수신 및 로컬 복사
echo $incomingDir = "$gitDir\incoming\$pcId"
echo if (Test-Path $incomingDir) {
echo   $dirs = Get-Content $config -Encoding UTF8 ^| Where-Object { $_.Trim() -ne '' }
echo   $taskDir = if ($dirs) { "$($dirs[0])\.claude\tasks" } else { $null }
echo   $inFiles = Get-ChildItem "$incomingDir\*.md" -ErrorAction SilentlyContinue
echo   foreach ($f in $inFiles) {
echo     $taskContent = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
echo     if ($taskContent -eq '{}') { continue }
echo     if ($taskDir -and (Test-Path (Split-Path $taskDir))) {
echo       if (-not (Test-Path $taskDir)) { New-Item $taskDir -ItemType Directory -Force ^| Out-Null }
echo       $localPath = "$taskDir\$($f.Name)"
echo       if (-not (Test-Path $localPath)) {
echo         [System.IO.File]::WriteAllText($localPath, $taskContent, [System.Text.Encoding]::UTF8)
echo         Write-Host "[TASK] Received: $($f.Name)"
echo       }
echo     }
echo     # 수신 완료 — 내용을 빈 것으로 덮어쓰기
echo     [System.IO.File]::WriteAllText($f.FullName, '{}', [System.Text.Encoding]::UTF8)
echo   }
echo }
echo.
echo # Control 명령 확인
echo $ctrlFile = "$gitDir\control\$pcId.json"
echo if (Test-Path $ctrlFile) {
echo   $ctrlJson = [System.IO.File]::ReadAllText($ctrlFile, [System.Text.Encoding]::UTF8) ^| ConvertFrom-Json
echo   $action = $ctrlJson.action
echo   if ($action) {
echo     Write-Host "[CTRL] Action: $action"
echo     if ($action -eq 'pause') {
echo       Disable-ScheduledTask -TaskName 'OrchestrationStatusPush' -ErrorAction SilentlyContinue ^| Out-Null
echo       Write-Host "[CTRL] Task Scheduler paused"
echo     } elseif ($action -eq 'resume') {
echo       Enable-ScheduledTask -TaskName 'OrchestrationStatusPush' -ErrorAction SilentlyContinue ^| Out-Null
echo       Write-Host "[CTRL] Task Scheduler resumed"
echo     } elseif ($action -eq 'stop') {
echo       Get-Process -Name 'codex','gemini','claude' -ErrorAction SilentlyContinue ^| Stop-Process -Force -ErrorAction SilentlyContinue
echo       Write-Host "[CTRL] Worker processes stopped"
echo     }
echo     # 처리 후 control 파일 삭제
echo     [System.IO.File]::WriteAllText($ctrlFile, '{}', [System.Text.Encoding]::UTF8)
echo   }
echo }
echo.
echo # git commit + push
echo Set-Location $gitDir
echo git add -A 2^>^&1 ^| Out-Null
echo $diff = git diff --cached --quiet 2^>^&1; $changed = $LASTEXITCODE
echo if ($changed -ne 0) {
echo   git -c user.name='status-push' -c user.email='auto@bot' commit -m "status: $pcId $ts" 2^>^&1 ^| Out-Null
echo   git push 2^>^&1 ^| Out-Null
echo }
echo Set-Location $env:TEMP
echo Remove-Item $gitDir -Recurse -Force -ErrorAction SilentlyContinue
echo.
echo Write-Host "[OK] $pcId at $ts (codex:$runCodex gemini:$runGemini claude:$runClaude pending:$pending done:$done)"
) > "!PS_SCRIPT!"

powershell -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "!PS_SCRIPT!"

endlocal
