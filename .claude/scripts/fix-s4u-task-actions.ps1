# fix-s4u-task-actions.ps1 — Weekly/Nightly Task Action 을 bat wrapper 로 변경
# 근거: 2026-10-27 S4U 전환 후 LastResult 0x80070002 (python PATH 없음) 수정
# 반드시 관리자 권한 실행
# 2026-10-27 사용자 "백그라운드로 해줘 파워셀 말고" → Start-Process -WindowStyle Hidden 사용
# 로그만 파일로 (console 출력 최소)

$log = "$env:TEMP\fix-s4u-task-actions.log"
"$([DateTime]::Now) start" | Out-File $log -Encoding utf8 -Append

$fixes = @(
    @{Name='Orca_WeeklyAudit'; Bat='C:\pjt\orchestration_v1\.claude\scripts\weekly-audit.bat'},
    @{Name='Orca_NightlyOptimize'; Bat='C:\pjt\orchestration_v1\.claude\scripts\nightly-optimize.bat'}
)

foreach ($f in $fixes) {
    try {
        $t = Get-ScheduledTask -TaskName $f.Name
        $before = $t.Actions[0].Execute
        $newAction = New-ScheduledTaskAction -Execute $f.Bat
        Set-ScheduledTask -TaskName $f.Name -Action $newAction | Out-Null
        $after = (Get-ScheduledTask -TaskName $f.Name).Actions[0].Execute
        Add-Content -Path $log -Value ("  [OK]   {0} · {1} -> {2}" -f $f.Name, $before, $after) -ForegroundColor Green
    } catch {
        Add-Content -Path $log -Value ("  [FAIL] {0} · {1}" -f $f.Name, $_.Exception.Message) -ForegroundColor Red
    }
}

Add-Content -Path $log -Value "`n재확인:" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -in @('Orca_WeeklyAudit','Orca_NightlyOptimize') } | ForEach-Object {
    [PSCustomObject]@{Task=$_.TaskName; Exec=$_.Actions[0].Execute}
} | Format-Table -AutoSize

Add-Content -Path $log -Value "`n5초 후 자동 종료..."
Start-Sleep -Seconds 5
