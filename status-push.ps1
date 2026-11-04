# $ErrorActionPreference = 'SilentlyContinue'
# NOTE: 전역 SilentlyContinue 사용 중. Collect-Status 등에서 Get-ChildItem, Get-Content 등
# 다수의 non-critical 명령이 존재하며, 개별 -ErrorAction SilentlyContinue가 이미 적용되어 있음.
# 전역을 'Stop'으로 변경하면 예상치 못한 곳에서 스크립트가 중단될 위험이 있으므로 현재 유지.
# 중요한 에러(git push 실패, Dashboard POST 실패 등)는 try/catch 블록에서 명시적으로 처리됨.
$ErrorActionPreference = 'SilentlyContinue'

# git 자격: 토큰이 있으면 환경변수 ORCH_GH_PAT 를 읽는 helper 만 쓰고 (명령줄엔 변수 이름만), 없으면 기존 자격 관리자(GCM) 그대로
function Get-GitCredArgs { param($token)
  if (-not $token) { return @() }
  return @('-c', 'credential.helper=', '-c', ('credential.helper={0}f() {{ echo username=x; echo password=$ORCH_GH_PAT; }}; f' -f [char]33))
}

# --- 자동 업데이트 (시작 시 1회, 무한 루프 방지: 최대 1회만 재시작) ---
try {
  $selfPath = $MyInvocation.MyCommand.Path
  # 환경변수로 업데이트 재시작 여부를 추적 — 이미 1회 업데이트했으면 스킵
  $alreadyUpdated = $env:ORCH_STATUS_PUSH_UPDATED -eq '1'
  if ($selfPath -and -not $alreadyUpdated) {
    $pat0 = [System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')
    if (-not $pat0) { $pat0 = '' }
    $updDir = "$env:TEMP\orch-self-update"
    if (Test-Path $updDir) { Remove-Item $updDir -Recurse -Force }
    # PAT 노출 방지 + timeout 30초
# 2026-11-04 감사 P0: 토큰을 URL 에 넣으면 git 명령줄(프로세스 목록)에 노출 → 환경변수 + credential helper (값은 명령줄에 안 나옴)
    $env:ORCH_GH_PAT = $pat0
    $gitJob = Start-Job -ScriptBlock { param($dir,$cred) git @cred clone --depth 1 "https://github.com/bernakilljos/orchestration-status.git" $dir 2>&1 } -ArgumentList $updDir,(Get-GitCredArgs $pat0)
    $null = Wait-Job $gitJob -Timeout 30
    Remove-Job $gitJob -Force -ErrorAction SilentlyContinue
    $remote = "$updDir\status-push.ps1"
    if (Test-Path $remote) {
      $localHash  = (Get-FileHash $selfPath -Algorithm MD5).Hash
      $remoteHash = (Get-FileHash $remote -Algorithm MD5).Hash
      if ($localHash -ne $remoteHash) {
        Copy-Item $remote $selfPath -Force
        Write-Host "[UPDATE] status-push.ps1 업데이트됨 — 재시작 (1회 제한)"
        Remove-Item $updDir -Recurse -Force -ErrorAction SilentlyContinue
        # 환경변수 설정 후 재시작 — 다음 실행에서 업데이트 블록 스킵
        $env:ORCH_STATUS_PUSH_UPDATED = '1'
        & $selfPath
        exit 0
      }
    }
    Remove-Item $updDir -Recurse -Force -ErrorAction SilentlyContinue
  }
} catch {}
# 업데이트 플래그 초기화 (정상 진입 시)
$env:ORCH_STATUS_PUSH_UPDATED = $null

# --- Config ---
$PUSH_INTERVAL = 30  # 30초 (GitHub rate limit 보호: 5000/hr = 최대 ~167/분)
$owner   = 'bernakilljos'
$repo    = 'orchestration-status'
$urlFile = "$env:USERPROFILE\.claude\dashboard-url.txt"

# --- PAT ---
# PAT 노출 방지 정책: PAT가 포함된 git clone/push URL의 에러 메시지가 콘솔에 출력되지 않도록
# 모든 git 명령에 2>&1 | Out-Null 적용. Write-Host 등으로 PAT 변수를 직접 출력하지 않을 것.
$pat = [System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')
if (-not $pat) { $pat = $env:GITHUB_PERSONAL_ACCESS_TOKEN }
if (-not $pat) { $pat = '' }

# --- PC ID ---
$mac = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.MacAddress } | Sort-Object InterfaceIndex | Select-Object -First 1).MacAddress -replace '-','' -replace ':',''
if (-not $mac) { $mac = (Get-NetAdapter | Where-Object { $_.MacAddress } | Sort-Object InterfaceIndex | Select-Object -First 1).MacAddress -replace '-','' -replace ':','' }
if (-not $mac) { $mac = '000000000000' }
$pcName = $env:COMPUTERNAME
$pcId   = "$pcName-$($mac.Substring(0,[Math]::Min(6,$mac.Length)))"

# --- IP ---
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.254' } | Sort-Object InterfaceIndex | Select-Object -First 1).IPAddress
if (-not $ip) { $ip = '' }

# --- Config ---
$config  = "$env:USERPROFILE\.claude\status-projects.txt"
$headers = @{ Authorization = "token $pat"; Accept = 'application/vnd.github.v3+json' }

function Read-Head { param($path, $lines=20)
  if (-not (Test-Path $path)) { return '' }
  try { (Get-Content $path -Encoding UTF8 -ErrorAction Stop | Select-Object -First $lines) -join "`n" } catch { '' }
}
function Esc { param($s) $s -replace '\\','\\' -replace '"','\"' -replace "`r`n",'\n' -replace "`n",'\n' -replace "`t",'\t' }

# --- Dashboard URL 관리 ---
$script:ghLastFetch   = [DateTime]::MinValue  # GitHub 마지막 조회 시각
$GH_REFETCH_INTERVAL  = 300                   # GitHub 재조회 간격 (5분 - rate limit 보호)

function Fetch-UrlsFromGitHub {
  # GitHub Contents API로 dashboard-url-*.json 읽기 (git clone 대신 API 1회 호출)
  $urls = @()
  try {
    $apiUrl = "https://api.github.com/repos/$owner/$repo/contents"
    $resp = Invoke-RestMethod -Uri $apiUrl -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    $urlFiles = $resp | Where-Object { $_.name -match '^dashboard-url-.*\.json$' }
    foreach ($f in $urlFiles) {
      try {
        $raw = Invoke-RestMethod -Uri $f.download_url -TimeoutSec 10 -ErrorAction Stop
        if ($raw.url -match '^https?://') { $urls += $raw.url }
      } catch {}
    }
  } catch {
    # API 실패 (rate limit 등) → 조용히 빈 배열 반환
  }
  return $urls
}

function Test-DashboardUrl { param($url)
  try {
    $req = [System.Net.HttpWebRequest]::Create("$url/health")
    $req.Method  = 'GET'; $req.Timeout = 5000
    $resp = $req.GetResponse(); $resp.Close()
    return $true
  } catch { return $false }
}

function Get-DashboardUrl {
  # 1) 캐시된 URL 시도
  if (Test-Path $urlFile) {
    $cached = (Get-Content $urlFile -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($cached -match '^https?://' -and (Test-DashboardUrl $cached)) {
      return $cached
    }
    Remove-Item $urlFile -ErrorAction SilentlyContinue
  }

  # 2) git clone으로 URL 조회 (10초 간격 제한)
  $elapsed = ([DateTime]::Now - $script:ghLastFetch).TotalSeconds
  if ($script:ghLastFetch -ne [DateTime]::MinValue -and $elapsed -lt $GH_REFETCH_INTERVAL) {
    return ''
  }

  $script:ghLastFetch = [DateTime]::Now
  $urls = Fetch-UrlsFromGitHub
  foreach ($url in $urls) {
    if (Test-DashboardUrl $url) {
      $url | Set-Content $urlFile -Encoding UTF8
      Write-Host "[OK] 대시보드 발견: $url"
      return $url
    }
  }
  return ''
}

# --- Status JSON 수집 ---
function Collect-Status {
  $ts = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
  if (-not (Test-Path $config)) { return $null }

  $pending=0; $runCodex=0; $runGemini=0; $runClaude=0; $done=0
  $projects=''; $pendingList=@(); $runningList=@(); $doneList=@()
  $taskSummary=''; $implSummary=''; $reviewSummary=''
  $recentReport=''; $projectDetails=@()

  $dirs = Get-Content $config -Encoding UTF8 | Where-Object { $_.Trim() -ne '' }

  foreach ($pdir in $dirs) {
    if (-not (Test-Path "$pdir\.claude")) { continue }
    $pname = Split-Path $pdir -Leaf
    $projects += "$pname "

    $pPending=0; $pRunCodex=0; $pRunGemini=0; $pRunClaude=0; $pDone=0
    $pPendList=@(); $pRunList=@(); $pDoneList=@()

    # Pending tasks
    $taskFiles = Get-ChildItem "$pdir\.claude\tasks\task-*.md" -ErrorAction SilentlyContinue
    foreach ($tf in $taskFiles) {
      if (Test-Path "$pdir\.claude\tasks\done\$($tf.Name)") { continue }
      $content = Get-Content $tf.FullName -Encoding UTF8 -ErrorAction SilentlyContinue -Raw
      if ($content -match '\[Task Title\]|\[What to build') { continue }
      $pending++; $pPending++
      $pendingList += $tf.BaseName; $pPendList += $tf.BaseName
      if ($taskSummary -eq '') { $taskSummary = Read-Head $tf.FullName 25 }
    }
    $tiFile = "$pdir\.claude\tasks\task-instruction.md"
    if ((Test-Path $tiFile) -and -not (Test-Path "$pdir\.claude\tasks\locks\task-instruction.lock")) {
      $tic = Get-Content $tiFile -Encoding UTF8 -Raw -ErrorAction SilentlyContinue
      if ($tic -notmatch '\[Task Title\]|\[What to build') {
        $pending++; $pPending++
        $pendingList += 'task-instruction'; $pPendList += 'task-instruction'
        if ($taskSummary -eq '') { $taskSummary = Read-Head $tiFile 25 }
      }
    }

    # Stale lock 정리 (30분 이상)
    Get-ChildItem "$pdir\.claude\tasks\locks\*.lock" -ErrorAction SilentlyContinue | Where-Object {
      ([DateTime]::Now - $_.LastWriteTime).TotalMinutes -gt 30
    } | ForEach-Object {
      Write-Host "[Cleanup] Stale lock: $($_.Name)"
      Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }

    # Running (lock files)
    $locks = Get-ChildItem "$pdir\.claude\tasks\locks\*.lock" -ErrorAction SilentlyContinue
    foreach ($lk in $locks) {
      $lname = $lk.BaseName
      $lcontent = (Get-Content $lk.FullName -ErrorAction SilentlyContinue | Select-Object -First 1)
      if ($lname -match '^verify-') { $runGemini++; $pRunGemini++; $ai='gemini' }
      elseif ($lcontent -match '^claude-worker-') { $runClaude++; $pRunClaude++; $ai='claude' }
      elseif ($lcontent -match 'worker-') { $runCodex++; $pRunCodex++; $ai='codex' }
      else { $runClaude++; $pRunClaude++; $ai='claude' }
      $entry = @{task=$lname; worker=$lcontent; ai=$ai; project=$pname}
      $runningList += $entry; $pRunList += $entry
    }

    # Done tasks
    $doneMd = Get-ChildItem "$pdir\.claude\tasks\done\*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    $pDone = $doneMd.Count; $done += $pDone
    $pDoneNames = ($doneMd | Select-Object -First 10).BaseName
    $doneList += $pDoneNames; $pDoneList += $pDoneNames

    # Recent report
    $rpts = Get-ChildItem "$pdir\docs\report-*.md" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    $pReport = if ($rpts) { $rpts[0].Name } else { '' }
    if ($pReport) { $recentReport = $pReport }

    $pImpl   = Read-Head "$pdir\docs\implementation-report.md" 30
    $pReview = Read-Head "$pdir\docs\review-result.txt" 30
    if ($implSummary -eq '')   { $implSummary   = $pImpl }
    if ($reviewSummary -eq '') { $reviewSummary = $pReview }

    $pRunTotal = $pRunCodex + $pRunGemini + $pRunClaude
    $pPendJson = ($pPendList | ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
    $pDoneJson = ($pDoneList | ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
    $pRunJson  = ($pRunList  | ForEach-Object { "{`"task`":`"$(Esc $_.task)`",`"worker`":`"$(Esc $_.worker)`",`"ai`":`"$($_.ai)`"}" }) -join ','
    $projectDetails += "{`"name`":`"$(Esc $pname)`",`"path`":`"$(Esc $pdir)`",`"pending`":$pPending,`"running`":$pRunTotal,`"running_codex`":$pRunCodex,`"running_gemini`":$pRunGemini,`"running_claude`":$pRunClaude,`"done`":$pDone,`"recent_report`":`"$(Esc $pReport)`",`"pending_tasks`":[$pPendJson],`"running_tasks`":[$pRunJson],`"done_tasks`":[$pDoneJson],`"impl_summary`":`"$(Esc $pImpl)`",`"review_summary`":`"$(Esc $pReview)`"}"
  }

  $runTotal = $runCodex + $runGemini + $runClaude
  $pendJson = ($pendingList | ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
  $doneJson = ($doneList    | ForEach-Object { '"' + (Esc $_) + '"' }) -join ','
  $runJson  = ($runningList | ForEach-Object { "{`"task`":`"$(Esc $_.task)`",`"worker`":`"$(Esc $_.worker)`",`"ai`":`"$($_.ai)`",`"project`":`"$(Esc $_.project)`"}" }) -join ','
  $projJson = $projectDetails -join ','

  return @"
{
  "pc": "$pcName",
  "pc_id": "$pcId",
  "mac": "$mac",
  "updated_at": "$ts",
  "pending": $pending,
  "running": $runTotal,
  "running_codex": $runCodex,
  "running_gemini": $runGemini,
  "running_claude": $runClaude,
  "done": $done,
  "ip": "$ip",
  "projects": "$($projects.Trim())",
  "recent_report": "$recentReport",
  "pending_tasks": [$pendJson],
  "running_tasks": [$runJson],
  "done_tasks": [$doneJson],
  "project_details": [$projJson],
  "task_summary": "$(Esc $taskSummary)",
  "impl_summary": "$(Esc $implSummary)",
  "review_summary": "$(Esc $reviewSummary)"
}
"@
}

# --- Dashboard로 직접 POST ---
function Invoke-Dashboard { param($endpoint, $bodyObj, $dashUrl)
  try {
    $jsonStr = $bodyObj | ConvertTo-Json -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonStr)
    $req = [System.Net.HttpWebRequest]::Create("$dashUrl$endpoint")
    $req.Method = 'POST'
    $req.ContentType = 'application/json'
    $req.ContentLength = $bytes.Length
    $req.Timeout = 8000
    $stream = $req.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()
    $resp = $req.GetResponse()
    $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
    $result = $sr.ReadToEnd() | ConvertFrom-Json
    $resp.Close()
    return $result
  } catch {
    return $null
  }
}

# --- Dashboard로 상태 전송 ---
function Push-ToDashboard { param($jsonStr, $dashUrl)
  try {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($jsonStr)
    $req = [System.Net.HttpWebRequest]::Create("$dashUrl/push")
    $req.Method = 'POST'
    $req.ContentType = 'application/json'
    $req.ContentLength = $bytes.Length
    $req.Timeout = 8000
    $stream = $req.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()
    $resp = $req.GetResponse()
    $resp.Close()
    return $true
  } catch {
    return $false
  }
}

# --- Dashboard로 스크린 캡처 전송 ---
function Push-ScreenToDashboard { param($dashUrl)
  try {
    Add-Type -AssemblyName System.Windows.Forms,System.Drawing -ErrorAction Stop
    # DPI 인식 활성화 — 고배율 모니터에서 전체 화면 캡처
    try {
      Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class DpiAware { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }' -ErrorAction Stop
      [DpiAware]::SetProcessDPIAware()
    } catch {}
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($screen.Left, $screen.Top, 0, 0, (New-Object System.Drawing.Size($screen.Width, $screen.Height)))
    $g.Dispose()
    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 90L)
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, $codec, $ep); $bmp.Dispose()
    $imgBytes = $ms.ToArray()
    # HTTP POST
    $req = [System.Net.HttpWebRequest]::Create("$dashUrl/push-screen")
    $req.Method = 'POST'
    $req.ContentType = 'image/jpeg'
    $req.ContentLength = $imgBytes.Length
    $req.Timeout = 8000
    $req.Headers.Add('X-PC-ID', $pcId)
    $req.Headers.Add('X-Monitor', '0')
    $stream = $req.GetRequestStream()
    $stream.Write($imgBytes, 0, $imgBytes.Length)
    $stream.Close()
    $resp = $req.GetResponse(); $resp.Close()
    # remote-status도 전송
    $monCount = [System.Windows.Forms.Screen]::AllScreens.Count
    $statusObj = @{ pc_id=$pcId; state='ready'; count=$monCount } | ConvertTo-Json -Compress
    $bytes2 = [System.Text.Encoding]::UTF8.GetBytes($statusObj)
    $req2 = [System.Net.HttpWebRequest]::Create("$dashUrl/push-remote-status")
    $req2.Method = 'POST'
    $req2.ContentType = 'application/json'
    $req2.ContentLength = $bytes2.Length
    $req2.Timeout = 5000
    $s2 = $req2.GetRequestStream(); $s2.Write($bytes2, 0, $bytes2.Length); $s2.Close()
    $r2 = $req2.GetResponse(); $r2.Close()
  } catch {}
}

# --- Incoming 태스크 수신 (Dashboard) ---
function Receive-IncomingTasks { param($dashUrl)
  $dirs = Get-Content $config -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object { $_.Trim() -ne '' }
  $taskDir = if ($dirs) { "$($dirs[0])\.claude\tasks" } else { $null }
  if (-not $taskDir) { return }

  $result = Invoke-Dashboard '/incoming-recv' @{ pc_id=$pcId } $dashUrl
  if (-not $result -or -not $result.ok) { return }
  foreach ($t in $result.tasks) {
    if (-not $t.filename -or -not $t.content) { continue }
    if (-not (Test-Path (Split-Path $taskDir))) { continue }
    if (-not (Test-Path $taskDir)) { New-Item $taskDir -ItemType Directory -Force | Out-Null }
    $localPath = "$taskDir\$($t.filename)"
    if (-not (Test-Path $localPath)) {
      [System.IO.File]::WriteAllText($localPath, $t.content, [System.Text.Encoding]::UTF8)
      Write-Host "[TASK] Received: $($t.filename)"
    }
    Invoke-Dashboard '/incoming-ack' @{ pc_id=$pcId; filename=$t.filename } $dashUrl | Out-Null
  }
}

# --- 원격 명령 검증 (2026-11-04 감사 H) ---
# 서명(HMAC-SHA256 · 공유 비밀 ORCH_REMOTE_CMD_SECRET)·만료(10분 이내)·일회성 id 가 모두 맞는 명령만 실행.
# 비밀이 설정되지 않았거나 서명이 없으면 실행하지 않고 기록만 한다 (대시보드 요청 인증이 생기기 전까지 기본 차단).
# key·drag 는 서명이 맞아도 ORCH_REMOTE_ALLOW_KEYS=1 일 때만.
function Test-RemoteCommand { param($cmd, [string]$action)
  $secret = [System.Environment]::GetEnvironmentVariable('ORCH_REMOTE_CMD_SECRET','User')
  if (-not $secret) { $secret = $env:ORCH_REMOTE_CMD_SECRET }
  if (-not $secret) { return 'no-secret' }
  if (-not $cmd -or -not $cmd.id -or -not $cmd.sig -or -not $cmd.expires) { return 'unsigned' }
  $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $exp = 0L; if (-not [int64]::TryParse([string]$cmd.expires, [ref]$exp)) { return 'expired' }
  if ($exp -lt $now -or $exp -gt ($now + 600)) { return 'expired' }
  $seenFile = Join-Path $env:USERPROFILE '.claude\remote-cmd-seen.txt'
  if ((Test-Path $seenFile) -and ((Get-Content $seenFile -ErrorAction SilentlyContinue) -contains [string]$cmd.id)) { return 'replayed' }
  $msg = "$($cmd.id)|$action|$exp|$($cmd.x)|$($cmd.y)|$($cmd.x0)|$($cmd.y0)|$($cmd.x1)|$($cmd.y1)|$($cmd.btn)|$($cmd.monitor)|$($cmd.key)"
  $h = New-Object System.Security.Cryptography.HMACSHA256 (,[System.Text.Encoding]::UTF8.GetBytes($secret))
  $expect = -join ($h.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($msg)) | ForEach-Object { $_.ToString('x2') })
  if ($expect -ne ([string]$cmd.sig).ToLower()) { return 'bad-signature' }
  if (($action -eq 'key' -or $action -eq 'drag') -and [System.Environment]::GetEnvironmentVariable('ORCH_REMOTE_ALLOW_KEYS','User') -ne '1') { return 'disabled' }
  Add-Content -Path $seenFile -Value ([string]$cmd.id) -Encoding UTF8
  return 'ok'
}
# stop = kit 가 띄운 워커 창 (codex-auto·gemini-auto·claude-auto .bat) 과 그 자식만 · 이름이 같은 다른 프로세스는 건드리지 않음
function Stop-OwnedWorkers {
  Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '(codex-auto|gemini-auto|claude-auto)\.bat' } |
    ForEach-Object { taskkill /T /F /PID $_.ProcessId 2>&1 | Out-Null; Write-Host "[CTRL] stop worker tree pid=$($_.ProcessId)" }
}

# --- Control 명령 확인 (Dashboard) ---
function Check-Control { param($dashUrl)
  $result = Invoke-Dashboard '/control-recv' @{ pc_id=$pcId } $dashUrl
  if (-not $result -or -not $result.ok -or -not $result.action) { return }
  $action = $result.action
  $v = Test-RemoteCommand $result $action
  if ($v -ne 'ok') { Write-Host "[CTRL BLOCKED] $action ($v)"; return }
  Write-Host "[CTRL] Action: $action"
  if ($action -eq 'stop') {
    Stop-OwnedWorkers
  } elseif ($action -eq 'pause') {
    # 실행 방식 = Run 키 + 상주 루프 (예약 작업 아님) → 일시정지 표시 파일로 전송 중단
    New-Item -ItemType File -Force -Path $script:pauseFlag | Out-Null
  } elseif ($action -eq 'resume') {
    Remove-Item $script:pauseFlag -Force -ErrorAction SilentlyContinue
  }
}

# --- Git Push Fallback (터널 안 될 때) ---
$script:gitPushInterval = 60  # git push 최소 간격 (초)
$script:lastGitPush = [DateTime]::MinValue

function Capture-Screen {
  # 스크린 캡처 → JPEG (품질 25, 50% 리사이즈)
  try {
    Add-Type -AssemblyName System.Windows.Forms,System.Drawing -ErrorAction Stop
    try {
      Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class DpiAware2 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }' -ErrorAction Stop
      [DpiAware2]::SetProcessDPIAware()
    } catch {}
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($screen.Left, $screen.Top, 0, 0, (New-Object System.Drawing.Size($screen.Width, $screen.Height)))
    $g.Dispose()
    # 50% 리사이즈 (용량 줄이기)
    $w = [int]($screen.Width / 2); $h = [int]($screen.Height / 2)
    $small = New-Object System.Drawing.Bitmap($w, $h)
    $g2 = [System.Drawing.Graphics]::FromImage($small)
    $g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::Bilinear
    $g2.DrawImage($bmp, 0, 0, $w, $h)
    $g2.Dispose(); $bmp.Dispose()
    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 25L)
    $ms = New-Object System.IO.MemoryStream
    $small.Save($ms, $codec, $ep); $small.Dispose()
    return $ms.ToArray()
  } catch { return $null }
}

function Push-ViaGit { param($jsonStr)
  $elapsed = ([DateTime]::Now - $script:lastGitPush).TotalSeconds
  if ($elapsed -lt $script:gitPushInterval) { return }
  $script:lastGitPush = [DateTime]::Now
  $tmpDir = "$env:TEMP\orch-git-push-$([guid]::NewGuid().ToString('N').Substring(0,8))"
  try {
    $repoUrl = "https://github.com/$owner/$repo.git"   # 토큰 없는 URL (자격은 credential helper)
    $env:ORCH_GH_PAT = $pat
    $cloneJob2 = Start-Job -ScriptBlock { param($u,$d,$cred) git @cred clone --depth 1 $u $d 2>&1 } -ArgumentList $repoUrl,$tmpDir,(Get-GitCredArgs $pat)
    $null = Wait-Job $cloneJob2 -Timeout 30
    Remove-Job $cloneJob2 -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $tmpDir)) { Write-Host "[WARN] git clone failed"; return }

    # 상태 JSON 저장
    $statusDir = "$tmpDir\status"
    if (-not (Test-Path $statusDir)) { New-Item $statusDir -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText("$statusDir\$pcId.json", $jsonStr, [System.Text.Encoding]::UTF8)

    # 스크린 캡처 저장
    $remoteDir = "$tmpDir\remote\$pcId"
    if (-not (Test-Path $remoteDir)) { New-Item $remoteDir -ItemType Directory -Force | Out-Null }
    $screenBytes = Capture-Screen
    if ($screenBytes) {
      [System.IO.File]::WriteAllBytes("$remoteDir\screen.jpg", $screenBytes)
      $monCount = [System.Windows.Forms.Screen]::AllScreens.Count
      $statusObj = @{ pc_id=$pcId; state='ready'; count=$monCount } | ConvertTo-Json -Compress
      [System.IO.File]::WriteAllText("$remoteDir\status.json", $statusObj, [System.Text.Encoding]::UTF8)
    }

    # 명령 확인 + 실행
    $cmdFile = "$remoteDir\cmd.json"
    if (Test-Path $cmdFile) {
      try {
        $cmdJson = Get-Content $cmdFile -Encoding UTF8 -Raw | ConvertFrom-Json
        $act = $cmdJson.action
        if ($act -and ($script:cmdVerdict = Test-RemoteCommand $cmdJson $act) -ne 'ok') {
          Write-Host "[CMD BLOCKED] $act ($script:cmdVerdict)"
        } elseif ($act) {
          Write-Host "[CMD] $act"
          if ($act -eq 'stop') {
            Stop-OwnedWorkers
          }
          elseif ($act -eq 'click' -or $act -eq 'dblclick') {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
            $csDef = '[DllImport("user32.dll")]public static extern bool SetCursorPos(int x,int y);' + '[DllImport("user32.dll")]public static extern void mouse_event(uint f,int x,int y,uint d,int e);'
            try { Add-Type -MemberDefinition $csDef -Name W -Namespace P -ErrorAction Stop } catch {}
            $mon = [int]($cmdJson.monitor); $scr = [System.Windows.Forms.Screen]::AllScreens[$mon].Bounds
            $ax = [int]($scr.Left + $cmdJson.x * $scr.Width); $ay = [int]($scr.Top + $cmdJson.y * $scr.Height)
            [P.W]::SetCursorPos($ax, $ay); Start-Sleep -Milliseconds 50
            if ($cmdJson.btn -eq 'right') { [P.W]::mouse_event(8,0,0,0,0); [P.W]::mouse_event(16,0,0,0,0) }
            else { [P.W]::mouse_event(2,0,0,0,0); [P.W]::mouse_event(4,0,0,0,0) }
            if ($act -eq 'dblclick') { Start-Sleep -Milliseconds 80; [P.W]::mouse_event(2,0,0,0,0); [P.W]::mouse_event(4,0,0,0,0) }
          }
          elseif ($act -eq 'key') {
            Add-Type -AssemblyName System.Windows.Forms -ErrorAction SilentlyContinue
            [System.Windows.Forms.SendKeys]::SendWait($cmdJson.key)
          }
          Remove-Item $cmdFile -Force
        }
      } catch { Write-Host "[CMD ERROR] $_" }
    }

    # git commit + push
    Set-Location $tmpDir
    git add -A 2>&1 | Out-Null
    $diff = git diff --cached --quiet 2>&1; $changed = $LASTEXITCODE
    if ($changed -ne 0) {
      $ts = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
      git -c user.name='status-push' -c user.email='auto@bot' commit -m "status: $pcId $ts" 2>&1 | Out-Null
      $cred = Get-GitCredArgs $pat; git @cred push 2>&1 | Out-Null
      Write-Host "[OK] → Git push (status+screen) at $([DateTime]::Now.ToString('HH:mm:ss'))"
    }
    Set-Location $env:TEMP
  } catch {
    Write-Host "[WARN] git push failed"
  } finally { if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue } }
}

# ══════════════════════════════════════════
#  메인 루프
# ══════════════════════════════════════════

# 대시보드 PC이면 status-push 불필요 (dashboard.py가 직접 처리)
if (Test-DashboardUrl 'http://localhost:8787') {
  Write-Host "[status-push] 대시보드 PC 감지 — status-push 종료 (dashboard.py가 직접 처리)"
  exit 0
}

Write-Host "[status-push] Started (interval: ${PUSH_INTERVAL}s, pc: $pcId)"

$script:pauseFlag = Join-Path $env:USERPROFILE '.claude\status-push.paused'
while ($true) {
  if (Test-Path $script:pauseFlag) { Start-Sleep -Seconds $PUSH_INTERVAL; continue }   # 원격 pause (서명된 명령만)
  $json = Collect-Status
  if (-not $json) {
    Write-Host "[WARN] No projects registered"
    Start-Sleep -Seconds $PUSH_INTERVAL
    continue
  }

  # 대시보드 URL 확인 (로컬 캐시 → git clone)
  $dashUrl = Get-DashboardUrl

  if ($dashUrl) {
    $pushed = Push-ToDashboard $json $dashUrl
    if ($pushed) {
      Write-Host "[OK] → Dashboard at $([DateTime]::Now.ToString('HH:mm:ss'))"
      Push-ScreenToDashboard $dashUrl
      Receive-IncomingTasks $dashUrl
      Check-Control $dashUrl
    } else {
      Remove-Item $urlFile -ErrorAction SilentlyContinue
      $script:ghLastFetch = [DateTime]::MinValue
      Push-ViaGit $json
    }
  } else {
    Push-ViaGit $json
  }

  Start-Sleep -Seconds $PUSH_INTERVAL
}
