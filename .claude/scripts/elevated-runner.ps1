<#
elevated-runner.ps1 — 관리자 예약 작업(\Orca\ElevatedRunner)이 SYSTEM 으로 실행하는 고정 실행기 (R365 · 2026-11-23)

목적: 사용자가 최초 설치 때 UAC 를 한 번 승인하면, 이후에는 «허용 목록에 있는 작업 종류 + 허용 경로» 만 UAC 없이 실행한다.
      임의 명령 실행기가 아니다 — 작업 종류는 이 파일의 switch 에 고정되어 있고, 경로는 보호 폴더의 allow.json 정규식으로만 허용.

보안 전제 (elevated-task.ps1 Install 이 구성):
  %ProgramData%\orca-elevated     SYSTEM·Administrators F · Users RX   ← 이 실행기·허용 목록·작업 스크립트 사본·해시 (일반 권한 수정 불가)
  %ProgramData%\orca-elevated-io\inbox   + Users Modify   ← 요청 JSON 만 (내용은 아래에서 엄격 검증 · 코드 실행 X)
  %ProgramData%\orca-elevated-io\outbox  Users RX         ← 결과 JSON (SYSTEM 만 씀 → 미리 심은 링크로 덮어쓰기 불가)
흐름: inbox\*.json → 재분석점(링크) 거부 → id·op·path 검증 → 작업 스크립트 사본 해시 확인 → 실행 → outbox\<id>.json + audit.log
결과 코드: 작업 스크립트의 코드 그대로 (0/3/10/20/30) · 40 허용 안 된 작업·경로 · 41 요청 형식 오류 · 42 작업 스크립트 해시 불일치
#>
param(
  [string]$Root = (Join-Path $env:ProgramData 'orca-elevated'),
  [string]$Io = (Join-Path $env:ProgramData 'orca-elevated-io')
)
$ErrorActionPreference = 'Stop'
$inbox = Join-Path $Io 'inbox'
$outbox = Join-Path $Io 'outbox'
$audit = Join-Path $Root 'audit.log'
$PS = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

function Write-Audit([string]$m) {
  try { Add-Content -LiteralPath $audit -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) -Encoding utf8 } catch {}
}
function Write-Result([string]$id, [int]$code, [string]$msg) {
  $safe = if ($id -match '^[a-z0-9-]{1,40}$') { $id } else { 'invalid-' + [guid]::NewGuid().ToString('N').Substring(0, 8) }
  $obj = [ordered]@{ id = $safe; code = $code; message = $msg; finished_at = (Get-Date -Format 'o') }
  $tmp = Join-Path $outbox ($safe + '.tmp')
  $dst = Join-Path $outbox ($safe + '.json')
  [IO.File]::WriteAllText($tmp, ($obj | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $tmp -Destination $dst -Force
  Write-Audit ("결과 id={0} code={1} {2}" -f $safe, $code, $msg)
}

if (-not (Test-Path -LiteralPath $inbox)) { exit 0 }
$allowPath = Join-Path $Root 'allow.json'
$allow = if (Test-Path -LiteralPath $allowPath) { Get-Content -LiteralPath $allowPath -Raw -Encoding utf8 | ConvertFrom-Json } else { $null }
$hashes = @{}
$hp = Join-Path $Root 'hashes.txt'
if (Test-Path -LiteralPath $hp) {
  foreach ($line in (Get-Content -LiteralPath $hp -Encoding utf8)) { $kv = $line -split '\s+', 2; if ($kv.Count -eq 2) { $hashes[$kv[1]] = $kv[0] } }
}

foreach ($f in @(Get-ChildItem -LiteralPath $inbox -File -Filter '*.json' -Force -ErrorAction SilentlyContinue)) {
  $id = ''
  try {
    if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) { Write-Audit "링크 요청 거부: $($f.Name)"; Remove-Item -LiteralPath $f.FullName -Force; continue }
    if ($f.Length -gt 4096) { Write-Result '' 41 "요청 파일이 너무 큼"; Remove-Item -LiteralPath $f.FullName -Force; continue }
    $req = Get-Content -LiteralPath $f.FullName -Raw -Encoding utf8 | ConvertFrom-Json
    Remove-Item -LiteralPath $f.FullName -Force          # 읽은 뒤 바로 제거 (같은 요청 재실행 방지)
    $id = [string]$req.id
    if ($id -notmatch '^[a-z0-9-]{1,40}$') { Write-Result '' 41 "id 형식 오류"; continue }
    $op = [string]$req.op
    $path = [string]$req.path
    $rule = if ($allow) { $allow.$op } else { $null }
    if (-not $rule) { Write-Result $id 40 "허용 목록에 없는 작업: $op"; continue }
    if (-not $path -or $path -notmatch [string]$rule.path_regex -or $path.Contains('..')) { Write-Result $id 40 "허용 경로 아님: $path"; continue }
    switch ($op) {
      'remove-shadow-command' {
        $script = Join-Path $Root 'remove-shadow-command.ps1'
        $want = $hashes['remove-shadow-command.ps1']
        $have = (Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash
        if (-not $want -or $want -ne $have) { Write-Result $id 42 "작업 스크립트 해시 불일치"; break }
        $out = & $PS -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $script -Path $path 2>&1 | Out-String
        $code = $LASTEXITCODE
        $left = Test-Path -LiteralPath $path
        Write-Result $id $code (($out.Trim()) + " · 실행 후 남아 있음=" + $left)
      }
      default { Write-Result $id 40 "실행기에 구현되지 않은 작업: $op" }
    }
  } catch {
    Write-Result $id 41 ("처리 실패: " + $_.Exception.Message)
  }
}
exit 0
