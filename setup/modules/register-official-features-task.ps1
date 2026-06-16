# register-official-features-task.ps1 — Task Scheduler daily 등록 (idempotent)
#
# 트리거: install/setup 또는 SessionStart hook 가 task 미등록 감지 시 자동 호출
# 동작: 매일 09:00 Claude Code 공식 changelog 자동 점검 (claude 세션과 무관)
# 룰: CLAUDE.md § 3.6 24/7 자동화 · feedback_official_features_auto_check.md
#
# Zero-touch (CLAUDE.md § 7-11): 사용자 액션 없이 등록. 이미 있으면 skip.
# Cross-machine (CLAUDE.md § 7-4): wrapper.bat 가 where bash 동적 검색.
# PowerShell 5.1 호환: cmd /c 로 native command stderr 함정 회피.

$ErrorActionPreference = "Continue"

$projectRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$wrapperBat = Join-Path $projectRoot ".claude\scripts\run-official-features-check.bat"
$taskName = "OrchestrationV1-OfficialFeaturesCheck"
$runTime = "09:00"

if (-not (Test-Path $wrapperBat)) {
    Write-Host "[FAIL] wrapper not found: $wrapperBat"
    exit 1
}

# 이미 등록됐는지 확인 — cmd /c 안에서 stderr 처리 (5.1 NativeCommandError 회피)
& cmd /c "schtasks /Query /TN `"$taskName`" >nul 2>&1"
$exists = ($LASTEXITCODE -eq 0)

if ($exists) {
    Write-Host "[SKIP] $taskName already registered"
    exit 0
}

# Daily 09:00 등록 — cmd /c 안에서 호출 (stderr 함정 회피)
$wrapperEsc = $wrapperBat.Replace('"', '\"')
$cmdLine = "schtasks /Create /TN `"$taskName`" /TR `"\`"$wrapperEsc\`"`" /SC DAILY /ST $runTime /F"
$result = & cmd /c $cmdLine 2>&1
$createRC = $LASTEXITCODE

if ($createRC -eq 0) {
    Write-Host "[OK] $taskName registered (daily $runTime)"
    Write-Host "[INFO] wrapper: $wrapperBat"
}
else {
    Write-Host "[WARN] schtasks failed (exit=$createRC): $result"
    exit 0
}
