param(
  [string]$Start = '2026-10-27T15:30:00',
  [string]$End = '2026-10-27T19:10:00'
)
Write-Host '=== Operational Log 활성 상태 ==='
$cfg = Get-WinEvent -ListLog 'Microsoft-Windows-TaskScheduler/Operational' -ErrorAction SilentlyContinue
if ($cfg) {
  Write-Host ("IsEnabled: " + $cfg.IsEnabled + ", LogMode: " + $cfg.LogMode + ", RecordCount: " + $cfg.RecordCount)
} else {
  Write-Host 'Log not found'
}
Write-Host ''
Write-Host '=== Event Log 15:30~19:10 (TaskName filter 안 함) ==='
$events = Get-WinEvent -FilterHashtable @{
  LogName = 'Microsoft-Windows-TaskScheduler/Operational'
  StartTime = [datetime]$Start
  EndTime = [datetime]$End
} -ErrorAction SilentlyContinue |
  Where-Object { $_.Properties[0].Value -match 'Orca_10MinLoop' -or $_.Message -match 'Orca' } |
  Sort-Object TimeCreated |
  ForEach-Object {
    "{0} ID={1} Properties0={2}" -f $_.TimeCreated.ToString('HH:mm:ss'), $_.Id, $_.Properties[0].Value
  }
if ($events) { $events | ForEach-Object { Write-Host $_ } }
else { Write-Host 'NO_ORCA_EVENTS' }
