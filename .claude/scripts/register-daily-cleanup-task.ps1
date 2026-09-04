# register-daily-cleanup-task.ps1 — daily-cleanup.bat 을 Windows Task Scheduler 에 등록
# 사용:
#   powershell -ExecutionPolicy Bypass -File .claude\scripts\register-daily-cleanup-task.ps1                  # 등록
#   powershell -ExecutionPolicy Bypass -File .claude\scripts\register-daily-cleanup-task.ps1 -Remove          # 제거
#   powershell -ExecutionPolicy Bypass -File .claude\scripts\register-daily-cleanup-task.ps1 -Time 03:30      # 시간 변경
#   powershell -ExecutionPolicy Bypass -File .claude\scripts\register-daily-cleanup-task.ps1 -TaskName foo    # 이름 변경
#
# 태스크 이름-경로 모두 호출 프로젝트 기준 동적 결정 (kit 공통, 도메인 의존 없음)

param(
  [switch]$Remove = $false,
  [string]$Time = "04:00",
  [string]$TaskName = ""
)

# 1) 프로젝트 루트 결정 — 스크립트 위치 기준 두 단계 위
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$ProjectName = Split-Path $ProjectRoot -Leaf

if ([string]::IsNullOrWhiteSpace($TaskName)) {
  $TaskName = "$ProjectName-daily-cleanup"
}

$ScriptPath = Join-Path $ProjectRoot ".claude\scripts\daily-cleanup.bat"
$TaskDescription = "Daily cleanup for $ProjectName ($ProjectRoot)"

function Check-Admin {
  $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Check-Admin)) {
  Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
  exit 1
}

if ($Remove) {
  Write-Host "Removing task: $TaskName" -ForegroundColor Yellow
  try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "Task '$TaskName' removed successfully." -ForegroundColor Green
  } catch {
    Write-Host "Failed to remove task: $_" -ForegroundColor Red
  }
  exit 0
}

if (-not (Test-Path $ScriptPath)) {
  Write-Host "Script not found: $ScriptPath" -ForegroundColor Red
  exit 1
}

$action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $ProjectRoot -Argument ""
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable:$false
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel "Highest"

try {
  $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if ($existingTask) {
    Write-Host "Task already exists. Updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  }

  Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description $TaskDescription `
    -Force | Out-Null

  Write-Host "Task '$TaskName' registered successfully!" -ForegroundColor Green
  Write-Host "  Schedule: Daily at $Time" -ForegroundColor Green
  Write-Host "  Script:   $ScriptPath" -ForegroundColor Green
  Write-Host "  Project:  $ProjectRoot" -ForegroundColor Green
} catch {
  Write-Host "Failed to register task: $_" -ForegroundColor Red
  exit 1
}
