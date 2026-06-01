# disable-defender.ps1 — Defender 영구 비활성화 (Tamper Protection OFF 상태에서 실행)
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -DisableBlockAtFirstSeen $true
Set-MpPreference -ScanScheduleDay 8
Write-Host "Realtime + Behavior + IOAV + BlockFirstSeen DISABLED, Scan=Never"

# 레지스트리 영구화 (재부팅 후에도)
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender' -Name 'DisableAntiSpyware' -Value 1 -Type DWord
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection' -Force | Out-Null
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection' -Name 'DisableRealtimeMonitoring' -Value 1 -Type DWord
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection' -Name 'DisableBehaviorMonitoring' -Value 1 -Type DWord
Write-Host "Registry permanent keys SET"

# 확인
Write-Host ""
Write-Host "=== Verify ==="
$pref = Get-MpPreference
Write-Host "RealtimeMonitoring: $($pref.DisableRealtimeMonitoring)"
Write-Host "BehaviorMonitoring: $($pref.DisableBehaviorMonitoring)"
$p = Get-Process MsMpEng -ErrorAction SilentlyContinue
if ($p) { Write-Host "MsMpEng still running: PID=$($p.Id) MB=$([math]::Round($p.WorkingSet64/1MB))" }
else { Write-Host "MsMpEng: NOT running" }
