# stage1-agent-isolation-check.ps1 — Stage 1 Agent 계정 인증정보 격리 실측 (§53-3 1~7 · §55 8~14 · 완료 기준 1·2·3)
#
# 실행: orca-agent 로 Windows 에 로그인한 뒤 (별도 세션 · runas 아님)
#   powershell -NoProfile -ExecutionPolicy Bypass -File <kit>\.claude\scripts\stage1-agent-isolation-check.ps1
#   (-ExecutionPolicy Bypass = 이 프로세스만 · 시스템 정책 변경 없음. 새 계정은 LocalMachine 미정의 → Restricted 라 빼면 실행 거부)
#   실행 전 원래 사용자가 기록한 SHA256 과 대조한다 (kit 은 Authenticated Users 수정 가능 → 실행 전 변조 확인 필요).
#
# 원칙 (§55): 읽기 전용 · 값 출력·복사·기록 0 (존재 여부와 거부 원문만) · 계정·ACL·자격 증명 변경 0 · push 0
#   원격 쓰기 시험(§55-2 · 완료 기준 4)은 승인된 시험 저장소가 필요해 이 스크립트에서 하지 않는다 → BLOCKED 로 기록.
# 원래 사용자로 실행하면 자가 점검 모드: 자격 증명 조회(git credential fill)를 하지 않고, 결과는 «격리 전 기준선» 이다.
param(
    [string]$Kit = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$OutDir = $env:TEMP
)
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$me = [Security.Principal.WindowsIdentity]::GetCurrent()
$ownerAcct = (Get-Acl $Kit).Owner
try {
    $ownerSid = ([Security.Principal.NTAccount]$ownerAcct).Translate([Security.Principal.SecurityIdentifier]).Value
} catch { $ownerSid = $null }
$ownerProfile = $null
if ($ownerSid) {
    $p = Get-CimInstance Win32_UserProfile -Filter ("SID='{0}'" -f $ownerSid) -ErrorAction SilentlyContinue
    if ($p) { $ownerProfile = $p.LocalPath }
}
$selfTest = ($ownerSid -and $me.User.Value -eq $ownerSid)
$results = New-Object System.Collections.Generic.List[object]

function Add-Result($id, $item, $status, $evidence) {
    $results.Add([pscustomobject]@{ id = $id; item = $item; status = $status; evidence = $evidence })
}

function Test-ReadDenied($id, $item, $path) {
    # PASS = 읽기 거부(Access denied) · FAIL = 읽힘 · NA = 없음 (내용은 읽지 않고 열기만 시도)
    if (-not $path) { Add-Result $id $item "BLOCKED" "원래 사용자 프로필 경로를 찾지 못함"; return }
    try {
        if (Test-Path -LiteralPath $path -PathType Container -ErrorAction Stop) {
            $null = Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop | Select-Object -First 1
        } elseif (Test-Path -LiteralPath $path -ErrorAction Stop) {
            $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite'); $fs.Close()
        } else {
            Add-Result $id $item "NA" ("없음: " + $path); return
        }
        Add-Result $id $item "FAIL" ("읽기 가능: " + $path)
    } catch [UnauthorizedAccessException] {
        Add-Result $id $item "PASS" ("거부: " + $_.Exception.Message)
    } catch {
        if ($_.Exception.Message -match "denied|거부") { Add-Result $id $item "PASS" ("거부: " + $_.Exception.Message) }
        else { Add-Result $id $item "BLOCKED" ("확인 실패: " + $_.Exception.GetType().Name) }
    }
}

function Test-WriteDenied($id, $item, $path) {
    # 쓰기 권한만 확인 (내용 변경 없음: 쓰기 모드로 열었다가 바로 닫음 · 파일 크기·시각 그대로)
    if (-not (Test-Path -LiteralPath $path)) { Add-Result $id $item "NA" ("없음: " + $path); return }
    try {
        $fs = [IO.File]::Open($path, 'Open', 'ReadWrite', 'ReadWrite'); $fs.Close()
        Add-Result $id $item "FAIL" ("쓰기 가능: " + $path)
    } catch [UnauthorizedAccessException] {
        Add-Result $id $item "PASS" ("거부: " + $_.Exception.Message)
    } catch { Add-Result $id $item "BLOCKED" ("확인 실패: " + $_.Exception.GetType().Name) }
}

# ── 완료 기준 1: 비관리자 · 무결성 Medium ──
# UAC 로 필터된 토큰에는 관리자 그룹이 «거부 전용» 이라 Groups 에 안 보인다 → 로컬 그룹 구성원 여부를 따로 확인 (§55 기준 1)
$groups = $me.Groups | ForEach-Object { $_.Value }
$member = $null
try {
    $member = [bool](Get-LocalGroupMember -SID "S-1-5-32-544" -ErrorAction Stop | Where-Object { $_.SID.Value -eq $me.User.Value })
} catch { $member = $null }
$c1a = $(if ($member -eq $null) { "BLOCKED" } elseif ($member -or ($groups -contains "S-1-5-32-544")) { "FAIL" } else { "PASS" })
Add-Result "C1a" "Administrators 비구성원 (로컬 그룹 S-1-5-32-544 · 토큰)" $c1a ("사용자 SID " + $me.User.Value + " · 그룹 구성원 " + $member)
$sys32 = Join-Path $env:SystemRoot "System32"   # PATH 의 다른 whoami·cmdkey (Git 등) 를 잡지 않게
$il = (& (Join-Path $sys32 "whoami.exe") /groups /fo csv 2>$null | Select-String "S-1-16-" | ForEach-Object { ($_.Line -split '","')[2] }) -join " "
Add-Result "C1b" "무결성 수준 Medium (S-1-16-8192)" ($(if ($il -match "S-1-16-8192") { "PASS" } elseif ($il) { "FAIL" } else { "BLOCKED" })) ($il -replace "\s+", " ")

# ── §53-3 1~4·6·7 ──
$gh = @(& (Join-Path $sys32 "cmdkey.exe") /list 2>$null | Select-String -Pattern "github" -SimpleMatch)
Add-Result "1" "자격 증명 관리자 GitHub 대상 (현재 계정 vault)" ($(if ($gh.Count -eq 0) { "PASS" } else { "FAIL" })) ("GitHub 대상 " + $gh.Count + "개 (이름·값 미기록)")
$hk = [Environment]::GetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "User")
Add-Result "2" "HKCU GITHUB_PERSONAL_ACCESS_TOKEN" ($(if ($hk) { "FAIL" } else { "PASS" })) ($(if ($hk) { "설정됨 (값 미기록)" } else { "없음" }))
$pe = [Environment]::GetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "Process")
Add-Result "3" "프로세스 환경 GITHUB_PERSONAL_ACCESS_TOKEN" ($(if ($pe) { "FAIL" } else { "PASS" })) ($(if ($pe) { "설정됨 (값 미기록)" } else { "없음" }))
if ($ownerProfile) {
    Test-ReadDenied "4" "원래 사용자 .claude.json" (Join-Path $ownerProfile ".claude.json")
    Test-ReadDenied "6" "원래 사용자 Claude transcript" (Join-Path $ownerProfile ".claude\projects")
    Test-ReadDenied "7" "원래 사용자 prompt history" (Join-Path $ownerProfile ".claude\history.jsonl")
} else { foreach ($i in "4", "6", "7") { Add-Result $i "원래 사용자 프로필" "BLOCKED" "프로필 경로를 찾지 못함" } }
$db = Join-Path $Kit ".claude\state\orca.db"
Test-ReadDenied "5" "kit orca.db 읽기 (대화 기록 속 토큰 사본 · §53-3 5)" $db
Test-WriteDenied "5w" "kit orca.db 쓰기 (승인 행 자기 승인 위험)" $db
Test-WriteDenied "5g" "승인 게이트 코드 쓰기 (approval-gate.py)" (Join-Path $Kit ".claude\scripts\approval-gate.py")
Test-WriteDenied "5h" "승인 감지 훅 쓰기 (approval_gate_detect.py)" (Join-Path $Kit ".claude\hooks\tool\approval_gate_detect.py")

# ── §55 8~14 ──
# Agent 계정에서는 kit 소유자가 달라 git 이 저장소를 거부한다 (dubious ownership · exit 128) → 오류를 버리면 0건 = 거짓 PASS.
# 명령줄 -c safe.directory 는 보호 설정이라 이 프로세스에서만 허용 (설정 파일 변경 없음) · 그래도 못 읽으면 BLOCKED.
$gitOk = [bool](Get-Command git -ErrorAction SilentlyContinue)
$kitGit = $Kit -replace "\\", "/"
$repoOk = $false
if ($gitOk) { git -c "safe.directory=$kitGit" -C $Kit rev-parse --git-dir *> $null; $repoOk = ($LASTEXITCODE -eq 0) }
$helpers = @(git config --show-origin --get-all credential.helper 2>$null)
$fillEvidence = "자가 점검 모드 — 원래 사용자 자격 증명 조회 안 함"
$fillStatus = "BLOCKED"
if (-not $gitOk) { $fillEvidence = "git 없음 — 확인 불가" }
elseif (-not $selfTest) {
    $env:GIT_TERMINAL_PROMPT = "0"; $env:GCM_INTERACTIVE = "Never"; $env:GIT_ASKPASS = ""; $env:SSH_ASKPASS = ""
    $fill = "protocol=https`nhost=github.com`n`n" | git credential fill 2>$null
    $has = [bool]($fill | Select-String -Pattern "^password=" -Quiet)
    $fill = $null
    $fillStatus = $(if ($has) { "FAIL" } else { "PASS" })
    $fillEvidence = $(if ($has) { "자격 증명 반환됨 (값 미기록)" } else { "반환 없음" })
}
Add-Result "8" "credential helper + git credential fill (github.com)" $fillStatus ("helper " + $helpers.Count + "개 · " + $fillEvidence)
if ($ownerProfile) {
    Test-ReadDenied "9a" "원래 사용자 .git-credentials" (Join-Path $ownerProfile ".git-credentials")
    Test-ReadDenied "9b" "원래 사용자 .gitconfig" (Join-Path $ownerProfile ".gitconfig")
    Test-ReadDenied "9c" "원래 사용자 .config\git" (Join-Path $ownerProfile ".config\git")
    Test-ReadDenied "10a" "원래 사용자 .ssh" (Join-Path $ownerProfile ".ssh")
    Test-ReadDenied "11a" "원래 사용자 GitHub CLI 설정" (Join-Path $ownerProfile "AppData\Roaming\GitHub CLI")
}
$myKeys = @(Get-ChildItem -Path (Join-Path $HOME ".ssh") -Filter "id_*" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "*.pub" })
Add-Result "10b" "현재 계정 .ssh 개인키" ($(if ($myKeys.Count -eq 0) { "PASS" } else { "FAIL" })) ("개인키 " + $myKeys.Count + "개")
$agentKeys = $null
if (Get-Command ssh-add -ErrorAction SilentlyContinue) { $agentKeys = @(ssh-add -l 2>$null | Where-Object { $_ -match "SHA256" }).Count }
Add-Result "10c" "ssh-agent 등록 키" ($(if ($agentKeys -eq $null) { "NA" } elseif ($agentKeys -eq 0) { "PASS" } else { "FAIL" })) ("키 " + $agentKeys + "개")
if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh auth status *> $null
    Add-Result "11b" "gh CLI 로그인" ($(if ($LASTEXITCODE -eq 0) { "FAIL" } else { "PASS" })) ("exit " + $LASTEXITCODE)
} else { Add-Result "11b" "gh CLI 로그인" "NA" "gh 없음" }
$names = "GITHUB_TOKEN", "GH_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH", "GIT_SSH_COMMAND"
$found = @()
foreach ($scope in "Process", "User", "Machine") {
    foreach ($n in $names) { if ([Environment]::GetEnvironmentVariable($n, $scope)) { $found += ($scope + ":" + $n) } }
    foreach ($k in [Environment]::GetEnvironmentVariables($scope).Keys) { if ($k -like "GIT_CONFIG_*") { $found += ($scope + ":" + $k) } }
}
Add-Result "12" "인증 관련 환경 변수 (프로세스·사용자·시스템)" ($(if ($found.Count -eq 0) { "PASS" } elseif ($found -match "^Machine:") { "FAIL" } else { "FAIL" })) ("설정된 이름: " + ($found -join ", "))
$ind = @()
foreach ($sc in "--system", "--global") {
    $ind += @(git config $sc --name-only --get-regexp "^(includeif\..*\.path|include\.path|core\.askpass|core\.sshcommand|url\..*\.insteadof)$" 2>$null | ForEach-Object { $sc + ":" + $_ })
}
if ($repoOk) {
    $ind += @(git -c "safe.directory=$kitGit" -C $Kit config --local --name-only --get-regexp "^(includeif\..*\.path|include\.path|core\.askpass|core\.sshcommand|url\..*\.insteadof)$" 2>$null | ForEach-Object { "--local:" + $_ })
    Add-Result "13" "간접 인증 경로 설정 (include·askPass·sshCommand·insteadOf)" ($(if ($ind.Count -eq 0) { "PASS" } else { "FAIL" })) ("설정 키: " + ($ind -join ", "))
    $urls = @(git -c "safe.directory=$kitGit" -C $Kit remote -v 2>$null)
    $embedded = @($urls | Where-Object { $_ -match "://[^/\s]+@" }).Count
    Add-Result "14" "원격 URL 내장 자격 증명" ($(if ($embedded -eq 0) { "PASS" } else { "FAIL" })) ("원격 " + $urls.Count + "줄 확인 · 내장 " + $embedded + "개 (URL 미기록)")
} else {
    $why = $(if ($gitOk) { "kit 저장소를 git 으로 열지 못함 — 확인 불가" } else { "git 없음 — 확인 불가" })
    Add-Result "13" "간접 인증 경로 설정 (include·askPass·sshCommand·insteadOf)" "BLOCKED" ($why + " · system/global 설정 키: " + ($ind -join ", "))
    Add-Result "14" "원격 URL 내장 자격 증명" "BLOCKED" $why
}
Add-Result "C4" "승인 없는 HTTPS·SSH push 실패 + 원격 불변 (§55-2)" "BLOCKED" "승인된 시험 저장소·브랜치 필요 — 이 스크립트 범위 밖"

$summary = [pscustomobject]@{
    checked_at = (Get-Date).ToString("s"); computer = $env:COMPUTERNAME; user = $me.Name; user_sid = $me.User.Value
    self_test = [bool]$selfTest; kit = $Kit; owner_sid = $ownerSid
    pass = @($results | Where-Object status -eq "PASS").Count; fail = @($results | Where-Object status -eq "FAIL").Count
    blocked = @($results | Where-Object status -eq "BLOCKED").Count; na = @($results | Where-Object status -eq "NA").Count
    verdict = $(if ($selfTest) { "SELF-TEST (격리 전 기준선 · 판정 아님)" } elseif (@($results | Where-Object status -in "FAIL", "BLOCKED").Count -eq 0) { "PASS" } elseif (@($results | Where-Object status -eq "FAIL").Count) { "FAIL" } else { "PARTIAL" })
    results = $results
}
$json = $summary | ConvertTo-Json -Depth 4
$name = "stage1-isolation-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json"
$out = Join-Path $OutDir $name
$json | Out-File -LiteralPath $out -Encoding utf8
$copied = $null
try {
    $dst = Join-Path $Kit ".claude\state\stage1"
    New-Item -ItemType Directory -Force -Path $dst -ErrorAction Stop | Out-Null
    Copy-Item -LiteralPath $out -Destination (Join-Path $dst $name) -ErrorAction Stop
    $copied = Join-Path $dst $name
} catch { $copied = "kit 복사 실패 (쓰기 거부면 정상) — 결과는 " + $out }
$results | Format-Table id, status, item -AutoSize | Out-String -Width 200 | Write-Output
Write-Output ("판정: " + $summary.verdict + " · PASS " + $summary.pass + " · FAIL " + $summary.fail + " · BLOCKED " + $summary.blocked)
Write-Output ("결과 파일: " + $out)
Write-Output ("kit 사본: " + $copied)
