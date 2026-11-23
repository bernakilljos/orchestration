# remove-shadow-command.ps1 — 실행 파일 이름을 가리는 «확장자 없는 0바이트 가짜 파일» 정리 (R363 · 2026-11-23)
# 증상: C:\Windows\System32\powershell (0바이트) 때문에 PowerShell 에서 `powershell` 을 부르면 진짜 powershell.exe 대신
#   이 파일이 먼저 잡혀 Windows «앱 선택» 창이 떴다 (Get-Command powershell -All 첫 줄 · MS 문서: 실행 파일이 아니면 연결 프로그램으로 연다).
# 지우는 조건 (모두 만족할 때만): 파일 존재 · 0바이트 · 재분석점(링크·접합점) 아님 · 디렉터리 아님 · 서명 없음 ·
#   같은 폴더 또는 PATH 에 같은 이름의 진짜 <이름>.exe 존재
# 결과 코드: 0 삭제·검증 완료 / 3 이미 없음 / 10 조건 불충족(안 지움) / 20 권한 부족(관리자·UAC 필요) / 30 삭제 후 검증 실패
param([Parameter(Mandatory = $true)][string]$Path, [switch]$DryRun)
$ErrorActionPreference = 'Stop'
function Out-Result([int]$code, [string]$msg) { Write-Output ("[{0}] {1}" -f $code, $msg); exit $code }

if (-not (Test-Path -LiteralPath $Path)) { Out-Result 3 "이미 없음: $Path" }
$i = Get-Item -LiteralPath $Path -Force
if ($i.PSIsContainer) { Out-Result 10 "폴더라 지우지 않음" }
if ($i.Attributes -band [IO.FileAttributes]::ReparsePoint) { Out-Result 10 "링크(재분석점)라 지우지 않음" }
if ($i.Length -ne 0) { Out-Result 10 "0바이트가 아니라 지우지 않음 ($($i.Length)바이트)" }
if ($i.Extension) { Out-Result 10 "확장자가 있는 파일이라 대상 아님" }
$sig = Get-AuthenticodeSignature -LiteralPath $Path
if ($sig.Status -eq 'Valid') { Out-Result 10 "서명된 파일이라 지우지 않음" }
$name = $i.Name
$real = Join-Path $i.DirectoryName ($name + '.exe')
$realExists = (Test-Path -LiteralPath $real) -or [bool](Get-Command ($name + '.exe') -CommandType Application -ErrorAction SilentlyContinue)
if (-not $realExists) { Out-Result 10 "같은 이름의 진짜 $name.exe 가 없어 가짜인지 확정 못 함" }
if ($DryRun) { Out-Result 0 "조건 충족 (DryRun · 삭제 안 함): $Path" }
try {
  Remove-Item -LiteralPath $Path -Force
} catch [System.UnauthorizedAccessException] {
  Out-Result 20 "권한 부족 — 관리자 권한(UAC)으로 다시 실행 필요: $($_.Exception.Message)"
} catch {
  if ($_.Exception.Message -match 'denied|거부') { Out-Result 20 "권한 부족 — 관리자 권한(UAC)으로 다시 실행 필요: $($_.Exception.Message)" }
  throw
}
if (Test-Path -LiteralPath $Path) { Out-Result 30 "삭제 후에도 남아 있음" }
$now = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
Out-Result 0 ("삭제·검증 완료: 남아 있지 않음 · 이제 '{0}' → {1}" -f $name, $(if ($now) { $now.Source } else { '(PATH 에 없음)' }))
