# switch-orca-tasks-to-s4u.ps1 — Orca Task Scheduler 작업을 백그라운드 (S4U) 로 전환
# 근거: 2026-10-27 사용자 "창 뜨는 거 왜 그래 · 관리자 권한 주면 되자나"
# S4U (Service for User) = 비밀번호 저장 X · 사용자 자격 · 창 안 뜸
# 반드시 관리자 권한으로 실행 (Set-ScheduledTask Principal 변경 요구)

Write-Host "`n=== Orca Task Scheduler → S4U (Background) 전환 ===`n" -ForegroundColor Cyan

$targets = Get-ScheduledTask | Where-Object {
    $_.TaskName -like 'Orca_*' -or $_.TaskName -eq 'OrchestrationV1-OfficialFeaturesCheck'
}

$ok = 0; $fail = 0
foreach ($t in $targets) {
    try {
        $before = (Get-ScheduledTask -TaskName $t.TaskName).Principal.LogonType
        $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
        Set-ScheduledTask -TaskName $t.TaskName -Principal $principal | Out-Null
        $after = (Get-ScheduledTask -TaskName $t.TaskName).Principal.LogonType
        Write-Host ("  [OK]   {0,-40}  {1} -> {2}" -f $t.TaskName, $before, $after) -ForegroundColor Green
        $ok++
    } catch {
        Write-Host ("  [FAIL] {0,-40}  {1}" -f $t.TaskName, $_.Exception.Message) -ForegroundColor Red
        $fail++
    }
}

Write-Host "`n--- 결과: $ok OK · $fail FAIL ---`n" -ForegroundColor Cyan
if ($fail -eq 0) {
    Write-Host "완료. 다음 10분 주기부터 cmd 창 안 뜸 (백그라운드 실행)." -ForegroundColor Green
}
Write-Host "`n5초 후 자동 종료..."
Start-Sleep -Seconds 5
