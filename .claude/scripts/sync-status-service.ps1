# sync-status-service.ps1 — kit 의 status-push.ps1 이 설치본(%USERPROFILE%\.claude)과 다르면 교체하고 상주 서비스를 재시작한다.
# R363 (2026-11-23): 사용자 지시 «git pull 받는 다른 PC 에도 자동 적용» — 설치본은 setup 모듈 05-services 가 복사하므로
#   kit 를 pull 해도 상주 프로세스는 옛 코드로 계속 돌았다. SessionStart(auto-install-deps)에서 하루 1번 이 스크립트를 부른다.
# 규칙: 설치본이 없으면(서비스 미설치 PC) 아무것도 안 함 · 해시가 같으면 아무것도 안 함 · 교체 시 기존 인스턴스만 종료 후
#   설치 모듈과 같은 숨김 시작(status-push-silent.vbs) · 결과는 .claude\logs\status-service-sync.log 에 한 줄
param([string]$Kit = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$ErrorActionPreference = 'Stop'
$log = Join-Path $Kit '.claude\logs\status-service-sync.log'
function Write-Log([string]$m) {
  try { Add-Content -Path $log -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) -Encoding utf8 } catch {}
}
try {
  $src = Join-Path $Kit 'status-push.ps1'
  $dst = Join-Path $env:USERPROFILE '.claude\status-push.ps1'
  $vbs = Join-Path $env:USERPROFILE '.claude\status-push-silent.vbs'
  if (-not (Test-Path $src) -or -not (Test-Path $dst)) { exit 0 }   # 서비스 미설치 PC
  $hs = (Get-FileHash $src -Algorithm SHA256).Hash
  $hd = (Get-FileHash $dst -Algorithm SHA256).Hash
  if ($hs -eq $hd) { exit 0 }
  $procs = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -match [regex]::Escape($dst) })
  foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Milliseconds 800
  Copy-Item $src $dst -Force
  $restarted = $false
  if ($procs.Count -gt 0 -and (Test-Path $vbs)) {
    Start-Process wscript.exe -ArgumentList ('"' + $vbs + '"') -WindowStyle Hidden
    $restarted = $true
  }
  Write-Log ("교체 {0} -> {1} · 종료 {2}개 · 재시작 {3}" -f $hd.Substring(0, 12), $hs.Substring(0, 12), $procs.Count, $restarted)
} catch {
  Write-Log ("실패: " + $_.Exception.Message)
}
exit 0
