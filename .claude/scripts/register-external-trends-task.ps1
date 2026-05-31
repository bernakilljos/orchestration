# register-external-trends-task.ps1 — Windows Task Scheduler 등록
# 매시간 17분에 external-trends-sync.bat 실행 (cron :00 회피)

param(
  [switch]$Remove = $false,
  [int]$Minute = 17,
  [string]$TaskName = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$ProjectName = Split-Path $ProjectRoot -Leaf

if ([string]::IsNullOrWhiteSpace($TaskName)) {
  $TaskName = "$ProjectName-external-trends"
}

$ScriptPath = Join-Path $ProjectRoot ".claude\scripts\external-trends-sync.bat"

function Check-Admin {
  $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Check-Admin)) {
  Write-Host "관리자 권한 필요." -ForegroundColor Red
  exit 1
}

if ($Remove) {
  try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "Task '$TaskName' removed." -ForegroundColor Green
  } catch {
    Write-Host "Failed to remove: $_" -ForegroundColor Red
  }
  exit 0
}

if (-not (Test-Path $ScriptPath)) {
  Write-Host "Script not found: $ScriptPath" -ForegroundColor Red
  exit 1
}

$action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $ProjectRoot
# 매시간 (Hourly) 17분
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date "00:$($Minute.ToString('00'))") `
  -RepetitionInterval (New-TimeSpan -Hours 1) `
  -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -RunLevel "Highest" -LogonType S4U

try {
  $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }
  Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Hourly external prompt-engineering trends sync for $ProjectName" `
    -Force | Out-Null
  Write-Host "Task '$TaskName' registered — hourly at minute $Minute." -ForegroundColor Green
} catch {
  Write-Host "Failed: $_" -ForegroundColor Red
  exit 1
}
