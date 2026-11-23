<#
elevated-task.ps1 — 최초 1회 UAC 승인 후 «허용된 관리자 작업» 을 UAC 없이 실행하는 예약 작업 계층 (R365 · 2026-11-23)

  Install    (관리자 1회) 보호 폴더·ACL·실행기/작업 스크립트 사본·해시·허용 목록 구성 + 예약 작업 \Orca\ElevatedRunner 등록
             (SYSTEM · 가장 높은 권한 · 트리거 없음 = 요청할 때만) + 작업 보안: 인증된 사용자 읽기·실행만 (수정·삭제 X)
  Status     (일반) 작업 등록·사본 해시 일치·최근 감사 기록 (읽기 전용 · JSON)
  Request    (일반) -Op <작업> -Path <대상> : inbox 에 요청 → schtasks /run → outbox 결과 대기 → 결과 코드로 종료
  Uninstall  (관리자) 작업·코드·요청 함 제거 (감사 기록 audit.log 는 보존)

허용 작업 (고정 · 늘리려면 이 파일과 elevated-runner.ps1 을 고쳐 다시 Install = 다시 UAC 승인):
  remove-shadow-command  — %SystemRoot%\System32 바로 아래 «확장자 없는 이름» 만 · 실제 삭제 조건은 remove-shadow-command.ps1 (0바이트·링크 아님·
                           서명 없음·같은 이름 .exe 존재) 가 실행 시점에 다시 검사 (TOCTOU 방지)
임의 명령·임의 스크립트 실행은 없다. Request 는 관리자 권한이 필요 없고 UAC 창도 뜨지 않는다.
결과 코드: 작업 결과 코드 그대로 · 40 허용 안 됨 · 41 형식 오류 · 42 해시 불일치 · 50 작업 미설치 · 51 결과 시간 초과 · 52 실행 요청 실패
#>
[CmdletBinding()]
param(
  [ValidateSet('Install', 'Status', 'Request', 'Uninstall')]
  [string]$Action = 'Status',
  [string]$Op,
  [string]$Path,
  [int]$TimeoutSec = 90,
  [string]$Root = (Join-Path $env:ProgramData 'orca-elevated'),
  [string]$Io = (Join-Path $env:ProgramData 'orca-elevated-io'),
  [switch]$NoTrigger          # 시험용: 요청만 쓰고 예약 작업은 부르지 않음 (격리 시험에서 실행기를 직접 돌림)
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$TaskPath = '\Orca\'
$TaskName = 'ElevatedRunner'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$PS = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$inbox = Join-Path $Io 'inbox'
$outbox = Join-Path $Io 'outbox'
$Files = @('elevated-runner.ps1', 'remove-shadow-command.ps1')

function Invoke-Schtasks([string[]]$a) {
  # PS 5.1: $ErrorActionPreference=Stop 에서 외부 프로그램 stderr 가 예외가 되는 것 방지 → 종료 코드만 돌려줌
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $null = & schtasks.exe @a 2>&1; return $LASTEXITCODE } finally { $ErrorActionPreference = $eap }
}
function Is-Admin {
  $p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Rule([string]$sid, [string]$rights) {
  $id = New-Object Security.Principal.SecurityIdentifier($sid)
  New-Object Security.AccessControl.FileSystemAccessRule($id, $rights, 'ContainerInherit,ObjectInherit', 'None', 'Allow')
}
function Set-Acl2([string]$dir, [array]$rules) {
  $acl = New-Object Security.AccessControl.DirectorySecurity
  $acl.SetAccessRuleProtection($true, $false)
  $acl.SetOwner((New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')))
  foreach ($r in $rules) { $acl.AddAccessRule($r) }
  Set-Acl -LiteralPath $dir -AclObject $acl
}

switch ($Action) {
  'Install' {
    if (-not (Is-Admin)) { Write-Output '[50] 관리자 PowerShell(UAC 승인)에서 실행해야 합니다'; exit 50 }
    foreach ($d in @($Root, $Io, $inbox, $outbox)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
    $base = @((Rule 'S-1-5-18' 'FullControl'), (Rule 'S-1-5-32-544' 'FullControl'))
    Set-Acl2 $Root ($base + (Rule 'S-1-5-32-545' 'ReadAndExecute'))
    Set-Acl2 $Io ($base + (Rule 'S-1-5-32-545' 'ReadAndExecute'))
    Set-Acl2 $inbox ($base + (Rule 'S-1-5-32-545' 'Modify'))
    Set-Acl2 $outbox ($base + (Rule 'S-1-5-32-545' 'ReadAndExecute'))
    $lines = @()
    foreach ($f in $Files) {
      Copy-Item -LiteralPath (Join-Path $Here $f) -Destination (Join-Path $Root $f) -Force
      $lines += ((Get-FileHash -LiteralPath (Join-Path $Root $f) -Algorithm SHA256).Hash + ' ' + $f)
    }
    [IO.File]::WriteAllLines((Join-Path $Root 'hashes.txt'), $lines)
    $sys = [regex]::Escape((Join-Path $env:SystemRoot 'System32'))
    $allow = [ordered]@{ 'remove-shadow-command' = @{ path_regex = '(?i)^' + $sys + '\\[a-z0-9_-]{1,64}$' } }
    [IO.File]::WriteAllText((Join-Path $Root 'allow.json'), ($allow | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    $act = New-ScheduledTaskAction -Execute $PS -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $Root 'elevated-runner.ps1') + '"')
    $pr = New-ScheduledTaskPrincipal -UserId 'S-1-5-18' -LogonType ServiceAccount -RunLevel Highest
    $st = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -MultipleInstances Queue
    Register-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -Action $act -Principal $pr -Settings $st -Force | Out-Null
    # 작업 보안: SYSTEM·관리자 전체 · 인증된 사용자(AU) 읽기·실행만 → 일반 권한으로 실행 요청 가능, 수정·삭제 불가
    $svc = New-Object -ComObject 'Schedule.Service'; $svc.Connect()
    $t = $svc.GetFolder($TaskPath.TrimEnd('\')).GetTask($TaskName)
    $t.SetSecurityDescriptor('D:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;GRGX;;;AU)', 0)
    Write-Output ('[0] 설치 완료: ' + $TaskPath + $TaskName + ' · 사본 ' + $Files.Count + '개 · 허용 작업 1종')
    exit 0
  }
  'Status' {
    $o = [ordered]@{ installed = $false; hashes_ok = $null; last_audit = @() }
    $o.installed = ((Invoke-Schtasks @('/query', '/tn', ($TaskPath + $TaskName))) -eq 0)
    $hp = Join-Path $Root 'hashes.txt'
    if (Test-Path -LiteralPath $hp) {
      $ok = $true
      foreach ($line in (Get-Content -LiteralPath $hp)) {
        $kv = $line -split '\s+', 2
        $fp = Join-Path $Root $kv[1]
        if (-not (Test-Path -LiteralPath $fp) -or (Get-FileHash -LiteralPath $fp -Algorithm SHA256).Hash -ne $kv[0]) { $ok = $false }
      }
      $o.hashes_ok = $ok
    }
    $al = Join-Path $Root 'audit.log'
    if (Test-Path -LiteralPath $al) { $o.last_audit = @(Get-Content -LiteralPath $al -Tail 5 -Encoding utf8) }
    $o | ConvertTo-Json -Compress
    exit 0
  }
  'Request' {
    if (-not $Op -or -not $Path) { Write-Output '[41] -Op 와 -Path 가 필요합니다'; exit 41 }
    if (-not (Test-Path -LiteralPath $inbox)) { Write-Output '[50] 관리자 실행 계층이 설치되지 않음 (elevated-task.ps1 -Action Install 을 관리자로 1회)'; exit 50 }
    $id = 'r' + (Get-Date -Format 'yyyyMMddHHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    $req = [ordered]@{ id = $id; op = $Op; path = $Path; requested_by = $env:USERNAME; requested_at = (Get-Date -Format 'o') }
    $tmp = Join-Path $inbox ($id + '.tmp')
    [IO.File]::WriteAllText($tmp, ($req | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination (Join-Path $inbox ($id + '.json'))
    if (-not $NoTrigger) {
      $src = Invoke-Schtasks @('/run', '/tn', ($TaskPath + $TaskName))
      if ($src -ne 0) { Write-Output "[52] 예약 작업 실행 요청 실패 (schtasks rc=$src · 설치 여부 확인)"; exit 52 }
    }
    $res = Join-Path $outbox ($id + '.json')
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
      if (Test-Path -LiteralPath $res) {
        $r = Get-Content -LiteralPath $res -Raw -Encoding utf8 | ConvertFrom-Json
        Write-Output ("[{0}] {1}" -f $r.code, $r.message)
        exit [int]$r.code
      }
      Start-Sleep -Milliseconds 300
    }
    Write-Output "[51] 결과 시간 초과 ($TimeoutSec 초) · 요청 id=$id"
    exit 51
  }
  'Uninstall' {
    if (-not (Is-Admin)) { Write-Output '[50] 관리자 PowerShell(UAC 승인)에서 실행해야 합니다'; exit 50 }
    $null = Invoke-Schtasks @('/delete', '/tn', ($TaskPath + $TaskName), '/f')
    foreach ($f in $Files + @('hashes.txt', 'allow.json')) { Remove-Item -LiteralPath (Join-Path $Root $f) -Force -ErrorAction SilentlyContinue }
    foreach ($d in @($inbox, $outbox)) { Get-ChildItem -LiteralPath $d -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue }
    Write-Output '[0] 제거 완료 (audit.log 보존)'
    exit 0
  }
}
