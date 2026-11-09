# fix-s4u-task-actions.ps1 — Weekly/Nightly Task Action 을 bat wrapper 로 변경
# 근거: 2026-10-27 S4U 전환 후 LastResult 0x80070002 (python PATH 없음) 수정
# 반드시 관리자 권한 실행
# 2026-10-27 사용자 "백그라운드로 해줘 파워셀 말고" → Start-Process -WindowStyle Hidden 사용
# 로그만 파일로 (console 출력 최소)

$log = "$env:TEMP\fix-s4u-task-actions.log"
"$([DateTime]::Now) start" | Out-File $log -Encoding utf8 -Append

$fixes = @(
    # 2026-11-09: kit 절대 경로 대신 이 스크립트 위치 기준 (다른 PC·대상 프로젝트로 전파돼도 동작 · 헌장 A1)
    @{Name='Orca_WeeklyAudit'; Bat=(Join-Path $PSScriptRoot 'weekly-audit.bat')},
    @{Name='Orca_NightlyOptimize'; Bat=(Join-Path $PSScriptRoot 'nightly-optimize.bat')}
)

foreach ($f in $fixes) {
    try {
        $t = Get-ScheduledTask -TaskName $f.Name
        $before = $t.Actions[0].Execute
        $newAction = New-ScheduledTaskAction -Execute $f.Bat
        Set-ScheduledTask -TaskName $f.Name -Action $newAction | Out-Null
        $after = (Get-ScheduledTask -TaskName $f.Name).Actions[0].Execute
        # Add-Content 에는 -ForegroundColor 가 없다 (2026-11-09 · 결과 줄 대신 예외 → 로그에 start 만 남음) · 숨김 실행이라 색은 쓰지 않는다
        Add-Content -Path $log -Encoding utf8 -Value ("  [OK]   {0} · {1} -> {2}" -f $f.Name, $before, $after)
    } catch {
        Add-Content -Path $log -Encoding utf8 -Value ("  [FAIL] {0} · {1}" -f $f.Name, $_.Exception.Message)
    }
}

Add-Content -Path $log -Encoding utf8 -Value "`n재확인:"
Get-ScheduledTask | Where-Object { $_.TaskName -in @('Orca_WeeklyAudit','Orca_NightlyOptimize') } | ForEach-Object {
    [PSCustomObject]@{Task=$_.TaskName; Exec=$_.Actions[0].Execute}
} | Format-Table -AutoSize | Out-String | Add-Content -Path $log -Encoding utf8

Add-Content -Path $log -Encoding utf8 -Value "`n5초 후 자동 종료..."
Start-Sleep -Seconds 5
