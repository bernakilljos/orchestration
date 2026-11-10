<#
broker-setup.ps1 — Agent/Broker 계정 분리 구성을 다른 PC·프로젝트에 전파·검증·뒷정리 (§70)

정본 구성 (DESKTOP 1대 실측 §69 을 그대로 옮김 · 하드 경로 없음):
  %ProgramData%\orca-broker      보호 ACL: SYSTEM F · Administrators F · <Broker> M · <Operator> RX
     python\  표준 라이브러리 사본 (컴퓨터 전체 Python 설치 불필요 §67)
     scripts\ approval-gate.py · lib\broker.py · lib\repair_sandbox.py · lib\state_db.py (kit 사본)
     code-hashes.txt · broker-config.json (원격 주소만 · 인증정보 없음)
     .claude\state · archive  ← 운영 데이터: 전파·삭제 대상 아님 (Uninstall 도 기본 보존)
  %ProgramData%\orca-broker-io   보호 ACL: 위와 같음
     inbox\   + <Agent> M   (Agent → Broker 요청 함)
     outbox\  + <Agent> RX  (Broker → Agent 결과)
     stage\   + <Operator> M · <Agent> RX  (운영자가 놓는 일회성 실행 스크립트 · Agent 는 고칠 수 없음)

동작 (변경 동작은 -Apply 없으면 미리보기만):
  Plan       현재 상태와 Install 이 할 일 표시 (읽기 전용)
  Install    폴더·ACL·Python 사본·코드 사본·해시·설정 (관리자) · 계정이 없으면 -CreateAccounts 로 생성 (암호는 사용자가 입력)
  Verify     ACL·해시·설정 인증정보 0·Python 동작 점검 (읽기 전용 · PASS/FAIL JSON)
  RunAs      -As <계정> -Script <ps1> : 그 계정 창에서 실행 → 결과 파일 → 창 스스로 닫힘 (-NoExit 금지 · 창을 붙잡지 않음)
  Cleanup    뒷정리: 일회성 실행 스크립트·결과·시험 파일 삭제 + Agent/Broker 계정 잔류 프로세스 종료 (관리자)
  Uninstall  코드·Python·요청 함 제거 · 운영 데이터(.claude\state·archive)는 -PurgeData PURGE 일 때만 · 계정은 -RemoveAccounts 일 때만

보안 전제: 어느 계정도 Agent 가 쓸 수 있는 위치(inbox)의 코드를 실행하지 않는다 → 실행 스크립트는 stage\ (운영자만 쓰기) 에만 두고,
          결과만 각 계정이 쓸 수 있는 곳(Agent=inbox · Broker=outbox)에 남긴다. 관리자 권한 불필요.
#>
[CmdletBinding()]
param(
  [ValidateSet('Plan', 'Install', 'Verify', 'RunAs', 'Cleanup', 'Uninstall')]
  [string]$Action = 'Plan',
  [switch]$Apply,
  [string]$Agent = 'orca-agent',
  [string]$Broker = 'orca-broker',
  [string]$Operator = $env:USERNAME,
  [string]$Kit = '',
  [string]$As,
  [string]$Script,
  [int]$TimeoutSec = 600,
  [int]$ShowSec = 5,
  [switch]$CreateAccounts,
  [switch]$RemoveAccounts,
  [string]$PurgeData = '',
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
if (-not $Kit) { $Kit = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) '..\..')).Path }   # PS 5.1: param 기본값 시점엔 $PSScriptRoot 가 비어 있음

$Root = Join-Path $env:ProgramData 'orca-broker'
$Io = Join-Path $env:ProgramData 'orca-broker-io'
$Inbox = Join-Path $Io 'inbox'
$Outbox = Join-Path $Io 'outbox'
$Stage = Join-Path $Io 'stage'
$CodeFiles = @('approval-gate.py', 'lib\broker.py', 'lib\repair_sandbox.py', 'lib\state_db.py')
$SidSystem = 'S-1-5-18'
$SidAdmins = 'S-1-5-32-544'
$SidUsers = 'S-1-5-32-545'

function Say([string]$m) { Write-Output $m }
function Is-Admin {
  $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Need-Admin { if (-not (Is-Admin)) { throw "관리자 PowerShell 에서 실행해야 합니다 ($Action)" } }
function Acct([string]$n) { "$env:COMPUTERNAME\$n" }
function Sid-Of([string]$n) {
  try { (New-Object Security.Principal.NTAccount((Acct $n))).Translate([Security.Principal.SecurityIdentifier]).Value } catch { $null }
}
function Rule($id, [string]$rights) {
  $ref = if ($id -like 'S-1-*') { New-Object Security.Principal.SecurityIdentifier($id) } else { New-Object Security.Principal.NTAccount((Acct $id)) }
  New-Object Security.AccessControl.FileSystemAccessRule($ref, $rights, 'ContainerInherit,ObjectInherit', 'None', 'Allow')
}
function Set-ProtectedAcl([string]$path, [array]$rules) {
  $acl = New-Object Security.AccessControl.DirectorySecurity
  $acl.SetAccessRuleProtection($true, $false)
  foreach ($r in $rules) { $acl.AddAccessRule($r) }
  # Set-Acl 은 새 객체의 감사(SACL) 영역까지 쓰려다 SeSecurityPrivilege 오류 → 권한 목록(DACL)만 기록
  (Get-Item -LiteralPath $path).SetAccessControl($acl)
}
function Add-ExplicitRule([string]$path, $rule) {
  $acl = (Get-Item -LiteralPath $path).GetAccessControl('Access'); $acl.AddAccessRule($rule)
  (Get-Item -LiteralPath $path).SetAccessControl($acl)
}
function Base-Rules {
  @((Rule $SidSystem 'FullControl'), (Rule $SidAdmins 'FullControl'), (Rule $Broker 'Modify'), (Rule $Operator 'ReadAndExecute'))
}
function Kit-Origin {
  $u = (& git -c "safe.directory=$($Kit -replace '\\','/')" -C $Kit remote get-url origin 2>$null)
  if (-not $u) { return '' }
  ($u.Trim() -replace '://[^/@\s]+@', '://')   # 인증정보가 박힌 주소면 걷어냄
}
function Find-PythonBase {
  $py = (Get-Command python -ErrorAction SilentlyContinue).Source
  if (-not $py) { throw 'python 을 찾지 못했습니다 (PATH)' }
  (& $py -c 'import sys;print(sys.base_prefix)').Trim()
}

# ---------- Plan / Verify ----------
function Get-State {
  $s = [ordered]@{}
  $s.accounts = [ordered]@{}
  foreach ($a in @($Agent, $Broker)) {
    $sid = Sid-Of $a
    $admin = $false
    if ($sid) { try { $admin = [bool](Get-LocalGroupMember -SID $SidAdmins -ErrorAction Stop | Where-Object { $_.SID.Value -eq $sid }) } catch { $admin = $null } }
    $s.accounts[$a] = [ordered]@{ exists = [bool]$sid; sid = $sid; is_admin = $admin }
  }
  $s.root = Test-Path $Root; $s.io = Test-Path $Io; $s.inbox = Test-Path $Inbox; $s.outbox = Test-Path $Outbox; $s.stage = Test-Path $Stage
  $s.python = Test-Path (Join-Path $Root 'python\python.exe')
  $s.code = @{}
  foreach ($c in $CodeFiles) {
    $dst = Join-Path $Root "scripts\$c"; $src = Join-Path $Kit ".claude\scripts\$c"
    $s.code[$c] = if (-not (Test-Path $dst)) { 'missing' } elseif ((Get-FileHash $dst).Hash -eq (Get-FileHash $src).Hash) { 'same' } else { 'differs' }
  }
  $s.config = Test-Path (Join-Path $Root 'broker-config.json')
  $s
}

function Check-Acl([string]$path, [hashtable]$expect, [bool]$protect = $true) {
  # expect: SID → 'F'|'M'|'RX' · 그 외 신원이 있으면 FAIL · inbox·outbox 는 보호된 io 에서 상속받는 구조라 $protect=$false
  $out = @()
  try { $acl = Get-Acl $path } catch { return @("ACL 읽기 실패: $path") }
  if ($protect -and -not $acl.AreAccessRulesProtected) { $out += "상속 보호 꺼짐: $path" }
  $seen = @{}
  foreach ($r in $acl.Access) {
    try { $sid = $r.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value } catch { $sid = "$($r.IdentityReference)" }
    $rt = "$($r.FileSystemRights)"
    $lvl = if ($rt -match 'FullControl') { 'F' } elseif ($rt -match 'Modify|Write') { 'M' } else { 'RX' }
    if (-not $expect.ContainsKey($sid)) { $out += "예상 밖 권한: $path ← $($r.IdentityReference) $rt"; continue }
    if ($seen[$sid] -ne 'F' -and $seen[$sid] -ne 'M') { $seen[$sid] = $lvl }
  }
  foreach ($k in $expect.Keys) {
    if (-not $seen.ContainsKey($k)) { $out += "권한 없음: $path ← $k ($($expect[$k]) 필요)" }
    elseif ($expect[$k] -eq 'RX' -and $seen[$k] -ne 'RX') { $out += "권한 과다: $path ← $k = $($seen[$k]) (RX 여야 함)" }
  }
  $out
}

function Do-Verify {
  $fail = @(); $st = Get-State
  foreach ($a in $st.accounts.Keys) {
    if (-not $st.accounts[$a].exists) { $fail += "계정 없음: $a" }
    elseif ($st.accounts[$a].is_admin -ne $false) { $fail += "관리자 그룹이거나 확인 불가: $a" }
  }
  $bs = Sid-Of $Broker; $as_ = Sid-Of $Agent; $os = Sid-Of $Operator
  if ($bs -and $os) {
    $base = @{ $SidSystem = 'F'; $SidAdmins = 'F'; $bs = 'M'; $os = 'RX' }
    if ($st.root) { $fail += Check-Acl $Root $base } else { $fail += "폴더 없음: $Root" }
    if ($st.io) { $fail += Check-Acl $Io $base } else { $fail += "폴더 없음: $Io" }
    if ($as_ -and $st.inbox) { $e = $base.Clone(); $e[$as_] = 'M'; $fail += Check-Acl $Inbox $e $false }
    if ($as_ -and $st.outbox) { $e = $base.Clone(); $e[$as_] = 'RX'; $fail += Check-Acl $Outbox $e $false }
    if (-not $st.stage) { $fail += "폴더 없음: $Stage (RunAs 용 · Install -Apply)" } elseif ($as_) { $e = $base.Clone(); $e[$as_] = 'RX'; $e[$os] = 'M'; $fail += Check-Acl $Stage $e $false }
  }
  foreach ($c in $st.code.Keys) { if ($st.code[$c] -ne 'same') { $fail += "코드 $($st.code[$c]): $c (kit 과 다름 → Install -Apply 로 갱신)" } }
  $hf = Join-Path $Root 'code-hashes.txt'
  if (Test-Path $hf) {
    foreach ($line in Get-Content $hf) {
      $h, $p = $line -split '\s+', 2
      if ($p -and (Test-Path $p) -and (Get-FileHash $p).Hash -ne $h) { $fail += "해시 목록 불일치: $p" }
    }
  } else { $fail += 'code-hashes.txt 없음' }
  $cf = Join-Path $Root 'broker-config.json'
  if (Test-Path $cf) {
    $txt = Get-Content $cf -Raw -Encoding UTF8
    if ($txt -match '://[^/"\s]+@|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_') { $fail += 'broker-config.json 에 인증정보로 보이는 값' }
  } else { $fail += 'broker-config.json 없음' }
  $pe = Join-Path $Root 'python\python.exe'
  if (Test-Path $pe) {
    # PS 5.1 은 네이티브 인자 속 큰따옴표를 지운다 → 따옴표 없는 식만 넘김 · stderr 는 오류 기록으로 바뀌므로 Continue 로 받음
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    $r = & $pe -I -c 'import sqlite3,json,hashlib;print(6*7)' 2>&1 | Out-String
    $ErrorActionPreference = $eap
    if ($r.Trim() -ne '42') { $fail += "Broker Python 동작 실패: $($r.Trim())" }
  } else { $fail += 'Broker Python 사본 없음' }
  $res = [ordered]@{ verdict = $(if ($fail.Count) { 'FAIL' } else { 'PASS' }); fail = @($fail); computer = $env:COMPUTERNAME; at = (Get-Date -Format s) }
  $res | ConvertTo-Json -Depth 4
  if ($fail.Count) { exit 1 }
}

# ---------- Install ----------
function Do-Install {
  $st = Get-State
  $plan = @()
  foreach ($a in @($Agent, $Broker)) { if (-not $st.accounts[$a].exists) { $plan += "계정 생성 $a (Users 그룹만 · 암호 직접 입력) — -CreateAccounts 필요" } }
  if (-not $st.root) { $plan += "폴더 $Root" }
  if (-not $st.io) { $plan += "폴더 $Io · inbox · outbox" }
  if (-not $st.stage) { $plan += "폴더 $Stage (운영자 M · Agent RX · RunAs 용)" }
  $plan += '보호 ACL 적용 (root·io · inbox +Agent M · outbox +Agent RX · stage +운영자 M +Agent RX)'
  if (-not $st.python) { $plan += "Python 표준 라이브러리 사본 → $Root\python" }
  foreach ($c in $st.code.Keys) { if ($st.code[$c] -ne 'same') { $plan += "코드 사본 $c ($($st.code[$c]))" } }
  $plan += 'code-hashes.txt 재작성'
  if (-not $st.config -or $Force) { $plan += "broker-config.json (원격 $(Kit-Origin) · main)" } else { $plan += 'broker-config.json 보존 (대상 고유 · -Force 로 교체)' }
  Say '[Install 계획]'; $plan | ForEach-Object { Say "  - $_" }
  if (-not $Apply) { Say '미리보기입니다. 실행하려면 관리자 PowerShell 에서 -Apply'; return }
  Need-Admin
  foreach ($a in @($Agent, $Broker)) {
    if ($st.accounts[$a].exists) { continue }
    if (-not $CreateAccounts) { throw "계정 $a 가 없습니다. -CreateAccounts 를 붙이면 암호를 물어 만듭니다." }
    $pw = Read-Host "새 계정 $a 의 암호" -AsSecureString
    New-LocalUser -Name $a -Password $pw -Description 'orchestration 분리 계정' -PasswordNeverExpires | Out-Null
    Add-LocalGroupMember -SID $SidUsers -Member $a
    Say "계정 생성: $a (Users)"
  }
  foreach ($d in @($Root, $Io, $Inbox, $Outbox, $Stage, (Join-Path $Root 'scripts\lib'))) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
  Set-ProtectedAcl $Root (Base-Rules)
  Set-ProtectedAcl $Io (Base-Rules)
  Add-ExplicitRule $Inbox (Rule $Agent 'Modify')
  Add-ExplicitRule $Outbox (Rule $Agent 'ReadAndExecute')
  Add-ExplicitRule $Stage (Rule $Agent 'ReadAndExecute')
  Add-ExplicitRule $Stage (Rule $Operator 'Modify')
  if (-not $st.python) {
    $pb = Find-PythonBase
    & robocopy $pb (Join-Path $Root 'python') /E /XD __pycache__ site-packages /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Python 사본 실패 robocopy=$LASTEXITCODE" }
  }
  $lines = @()
  foreach ($c in $CodeFiles) {
    $src = Join-Path $Kit ".claude\scripts\$c"; $dst = Join-Path $Root "scripts\$c"
    Copy-Item $src $dst -Force
    $lines += "$((Get-FileHash $dst).Hash)  $dst"
  }
  $lines | Set-Content (Join-Path $Root 'code-hashes.txt') -Encoding utf8
  $cf = Join-Path $Root 'broker-config.json'
  if (-not (Test-Path $cf) -or $Force) {
    [ordered]@{ repos = [ordered]@{ kit = [ordered]@{ branches = @('main'); remote_url = (Kit-Origin) } }; inbox = $Inbox } |
      ConvertTo-Json -Depth 5 | Set-Content $cf -Encoding utf8
  }
  Say '설치 완료 → Verify 실행'
  Do-Verify
}

# ---------- RunAs (창 자동 닫힘) ----------
function Do-RunAs {
  if (-not $As -or -not $Script) { throw 'RunAs 는 -As <계정> -Script <ps1> 필요' }
  if (-not (Test-Path $Script)) { throw "스크립트 없음: $Script" }
  if (-not (Sid-Of $As)) { throw "계정 없음: $As" }
  if (-not (Test-Path $Stage)) { throw "단계 폴더 없음: $Stage → Install -Apply 먼저" }
  $stage = $Stage                                              # 운영자만 쓰기 · Agent 는 실행 코드를 못 고침
  $outDir = if ($As -eq $Broker) { $Outbox } else { $Inbox }   # 결과는 그 계정이 쓸 수 있는 곳
  $id = Get-Date -Format 'yyyyMMdd-HHmmss'
  $body = Join-Path $stage "run-$id.ps1"
  $wrap = Join-Path $stage "run-$id.wrap.ps1"
  $result = Join-Path $outDir "result-$id.txt"
  $wrapText = @"
`$ErrorActionPreference = 'Continue'
Get-ChildItem '$outDir' -Filter 'result-*.txt' -ErrorAction SilentlyContinue | Where-Object { `$_.LastWriteTime -lt (Get-Date).AddMinutes(-10) } | Remove-Item -Force -ErrorAction SilentlyContinue
try { `$o = & '$body' 2>&1 | Out-String; `$code = `$LASTEXITCODE } catch { `$o = "예외: `$(`$_.Exception.Message)"; `$code = 99 }
("user=`$env:USERNAME exit=`$code at=`$(Get-Date -Format s)`r`n" + `$o) | Out-File '$result' -Encoding utf8
Write-Host "[완료] 결과를 저장했습니다. $ShowSec 초 뒤 이 창은 자동으로 닫힙니다."
Start-Sleep -Seconds $ShowSec
exit
"@
  Say "[RunAs] $As 로 실행 · 단계 폴더 $stage"
  if (-not $Apply) { Say '미리보기입니다. -Apply 로 실행 (창이 뜨면 그 계정 암호만 입력)'; return }
  Copy-Item $Script $body -Force
  $wrapText | Set-Content $wrap -Encoding utf8
  $cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$wrap`""   # -NoExit 금지 — 끝나면 창이 닫힘
  $env:ALLOW_VISIBLE_WINDOW = '1'
  Start-Process -FilePath runas.exe -ArgumentList @("/user:$(Acct $As)", "`"$cmd`"")
  $t0 = Get-Date
  while (-not (Test-Path $result) -and ((Get-Date) - $t0).TotalSeconds -lt $TimeoutSec) { Start-Sleep -Seconds 2 }
  Start-Sleep -Seconds ($ShowSec + 2)
  Remove-Item $body, $wrap -Force -ErrorAction SilentlyContinue   # 단계 파일은 운영자가 바로 정리
  if (-not (Test-Path $result)) { Say "[시간 초과] $TimeoutSec 초 안에 결과가 없습니다 (암호 미입력·거부 등) · 단계 파일은 정리함"; exit 2 }
  Get-Content $result -Encoding UTF8
  $left = Get-Process -IncludeUserName -ErrorAction SilentlyContinue | Where-Object { $_.UserName -like "*\$As" -and $_.ProcessName -match 'powershell|pwsh|conhost' }
  if ($left) { Say "[경고] $As 계정 셸 프로세스 잔류: $(($left.Id) -join ',') → Cleanup -Apply 로 종료" } else { Say "[확인] $As 계정 창·프로세스 남은 것 없음" }
}

# ---------- Cleanup (뒷정리) ----------
function Do-Cleanup {
  $items = @()
  foreach ($d in @($Inbox, $Outbox, $Stage)) {
    if (Test-Path $d) { $items += Get-ChildItem $d -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^(run-.*\.ps1|result-.*\.txt|agent-probe.*\.txt|c4-.*|.*probe.*\.(txt|ps1))$' } }
  }
  $procs = @()
  try { $procs = Get-Process -IncludeUserName -ErrorAction Stop | Where-Object { $_.UserName -like "*\$Agent" -or $_.UserName -like "*\$Broker" } } catch { Say '[참고] 다른 계정 프로세스 목록은 관리자 권한에서만 보입니다' }
  Say '[Cleanup 계획]'
  $items | ForEach-Object { Say "  - 파일 삭제 $($_.FullName)" }
  $procs | ForEach-Object { Say "  - 프로세스 종료 $($_.Id) $($_.ProcessName) ($($_.UserName))" }
  if (-not $items -and -not $procs) { Say '  (정리할 것 없음)'; return }
  if (-not $Apply) { Say '미리보기입니다. 관리자 PowerShell 에서 -Apply'; return }
  Need-Admin
  $items | Remove-Item -Force
  $procs | Stop-Process -Force
  Say "정리 완료: 파일 $(@($items).Count) · 프로세스 $(@($procs).Count)"
}

# ---------- Uninstall ----------
function Do-Uninstall {
  $plan = @("코드·Python·설정·해시 제거 ($Root\scripts · python · broker-config.json · code-hashes.txt)", "요청 함·단계 폴더 제거 ($Io)")
  $keep = @((Join-Path $Root '.claude'), (Join-Path $Root 'archive'))
  if ($PurgeData -eq 'PURGE') { $plan += "운영 데이터 삭제 (승인 DB·토큰 원본 보관본): $($keep -join ' · ')" } else { $plan += "운영 데이터 보존: $($keep -join ' · ') (삭제는 -PurgeData PURGE)" }
  if ($RemoveAccounts) { $plan += "계정 삭제: $Agent · $Broker" } else { $plan += '계정 유지 (삭제는 -RemoveAccounts)' }
  if (Test-Path $Inbox) { $pending = Get-ChildItem $Inbox -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '^(run-|result-|agent-probe|c4-)' }; if ($pending) { $plan += "주의: 처리 안 된 요청 $(@($pending).Count) 건이 요청 함에 있음" } }
  Say '[Uninstall 계획]'; $plan | ForEach-Object { Say "  - $_" }
  if (-not $Apply) { Say '미리보기입니다. 관리자 PowerShell 에서 -Apply'; return }
  Need-Admin
  Do-Cleanup
  foreach ($p in @('scripts', 'python', 'broker-config.json', 'code-hashes.txt')) { Remove-Item (Join-Path $Root $p) -Recurse -Force -ErrorAction SilentlyContinue }
  Remove-Item $Io -Recurse -Force -ErrorAction SilentlyContinue
  if ($PurgeData -eq 'PURGE') { Remove-Item $Root -Recurse -Force -ErrorAction SilentlyContinue }
  if ($RemoveAccounts) { foreach ($a in @($Agent, $Broker)) { if (Sid-Of $a) { Remove-LocalUser -Name $a } } }
  Say '제거 완료'
}

switch ($Action) {
  'Plan' { Get-State | ConvertTo-Json -Depth 5; Do-Install }
  'Install' { Do-Install }
  'Verify' { Do-Verify }
  'RunAs' { Do-RunAs }
  'Cleanup' { Do-Cleanup }
  'Uninstall' { Do-Uninstall }
}
