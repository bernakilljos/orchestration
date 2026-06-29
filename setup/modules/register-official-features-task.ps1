# register-official-features-task.ps1 — Task Scheduler daily + ONLOGON 이중 등록 (idempotent)
#
# 트리거: install/setup 또는 SessionStart hook 가 task 미등록 감지 시 자동 호출
# 동작: 매일 09:00 + 사용자 로그온 시 자동 점검 — claude 세션과 무관
# 룰: CLAUDE.md § 3.6 24/7 자동화 · feedback_official_features_auto_check.md
#
# 2026-06-19 강화: 단일 DAILY task 가 PC 꺼져 있을 때 누락되는 문제 — ONLOGON 추가로 catch-up
# PowerShell 5.1 호환: cmd /c 로 NativeCommandError 회피

$ErrorActionPreference = "Continue"

$projectRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$wrapperBat = Join-Path $projectRoot ".claude\scripts\run-official-features-check.bat"
$runTime = "09:00"

if (-not (Test-Path $wrapperBat)) {
    Write-Host "[FAIL] wrapper not found: $wrapperBat"
    exit 1
}

# 등록할 task 목록 (DAILY + ONLOGON 이중)
$tasks = @(
    @{ Name = "OrchestrationV1-OfficialFeaturesCheck"; Schedule = "DAILY"; Time = $runTime },
    @{ Name = "OrchestrationV1-OfficialFeaturesCheck-OnLogon"; Schedule = "ONLOGON"; Time = $null }
)

foreach ($t in $tasks) {
    $taskName = $t.Name

    # 이미 등록됐는지 확인
    & cmd /c "schtasks /Query /TN `"$taskName`" >nul 2>&1"
    $exists = ($LASTEXITCODE -eq 0)

    if ($exists) {
        Write-Host "[SKIP] $taskName already registered"
        continue
    }

    # 등록
    $trArg = '"' + $wrapperBat + '"'
    if ($t.Schedule -eq "DAILY") {
        $cmdLine = "schtasks /Create /TN `"$taskName`" /TR `"\`"$wrapperBat\`"`" /SC DAILY /ST $($t.Time) /F"
    } else {
        $cmdLine = "schtasks /Create /TN `"$taskName`" /TR `"\`"$wrapperBat\`"`" /SC ONLOGON /F"
    }
    $result = & cmd /c $cmdLine 2>&1
    $createRC = $LASTEXITCODE

    if ($createRC -eq 0) {
        Write-Host "[OK] $taskName registered ($($t.Schedule))"
    } else {
        Write-Host "[WARN] $taskName failed (exit=$createRC): $result"
    }
}

Write-Host "[INFO] wrapper: $wrapperBat"
Write-Host "[INFO] manual run: cmd /c `"$wrapperBat`""
