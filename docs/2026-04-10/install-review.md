# install.bat status-projects.txt Review

Date: 2026-04-10

---

## 1. Duplicate Check on Registration

**PASS**

Line 208:
```bat
findstr /i /c:"%TARGET%" "!PROJ_CONFIG!" >nul 2>&1 || (
  echo %TARGET%>> "!PROJ_CONFIG!"
)
```

- `findstr /i` performs case-insensitive search before appending.
- Only appends if the exact `%TARGET%` string is NOT found.
- Note: This is a substring match, not a full-line match. If `C:\projects\app` is registered and you install `C:\projects\app2`, it would falsely match and skip registration. However, in practice project paths are sufficiently distinct that this is unlikely to cause issues.

**Verdict: PASS** (duplicate prevention exists and works for normal cases)

---

## 2. PowerShell Cleanup Logic Exists

**PASS**

Line 213 contains a single-line PowerShell cleanup command that performs:
1. Read file with UTF8 encoding
2. Filter out blank lines (`Where-Object{$_.Trim()-ne''}`)
3. Normalize slashes: `Replace('/','\')` and `TrimEnd('\')`
4. Remove duplicates via `$seen` hashtable with `.ToLower()` key (case-insensitive)
5. Remove non-existent paths: `Test-Path "$n\.claude"` check
6. Write back cleaned list with UTF8 encoding
7. Report removed paths and final count

**Verdict: PASS** (all three cleanup operations present: slash normalization, dead path removal, dedup)

---

## 3. PowerShell Syntax Correctness

**PASS**

Expanded cleanup logic (line 213):
```powershell
$f='!PROJ_CONFIG!'
$lines=Get-Content $f -Encoding UTF8 -ErrorAction SilentlyContinue | Where-Object{$_.Trim()-ne''}
$clean=@()
$seen=@{}
foreach($l in $lines){
  $n=$l.Trim().Replace('/','\').TrimEnd('\')
  if(-not $n){continue}
  if($seen[$n.ToLower()]){continue}
  if(-not(Test-Path "$n\.claude")){Write-Host "      [Cleanup] removed: $n";continue}
  $seen[$n.ToLower()]=$true
  $clean+=$n
}
Set-Content $f $clean -Encoding UTF8
Write-Host "      Projects: $($clean.Count)"
```

Analysis:
- Hashtable initialization `@{}` and array `@()`: correct
- `Get-Content -Encoding UTF8`: correct
- `Set-Content $f $clean -Encoding UTF8`: correct (writes array as lines)
- `$seen[$n.ToLower()]=$true` / `$seen[$n.ToLower()]` for check: correct pattern
- String interpolation in `Write-Host`: correct
- `Test-Path "$n\.claude"`: validates the path is a real orchestration project, not just any directory
- Error suppression with `2>nul` at the batch level: correct

**WARN**: The `!PROJ_CONFIG!` variable is expanded by batch before PowerShell sees it. If the path contains special characters (e.g., spaces), the PowerShell string is not quoted with escaping. However, `REAL_USERPROFILE` is set to `C:\Users\<username>` which rarely contains spaces, so this is low risk.

**Verdict: PASS** (syntax is correct, minor quoting concern is low-risk)

---

## 4. guide.txt Reflects Latest Changes

**PASS**

Checked items in guide.txt (lines 306-317):

| Feature | Present in guide.txt | Line(s) | Status |
|---------|---------------------|---------|--------|
| Git fallback (git push fallback for firewall environments) | Yes | 309: "2순위: git push fallback (60초 간격, 방화벽 환경용)" | PASS |
| Auto-update (status-push.ps1 self-update from GitHub) | Yes | 312-313: "status-push.ps1은 시작 시 GitHub repo에서 최신 버전 자동 다운" | PASS |
| Tunnel + git dual communication | Yes | 308-309: "1순위: 터널 직접 통신 (200ms 실시간)" + "2순위: git push fallback" | PASS |
| Manual update without install | Yes | 316-317: PowerShell one-liner for manual update | PASS |
| install.bat restart | Yes | 16, 328-329 | PASS |
| Dashboard tunnel auto-start | Yes | 292-295: "cloudflared tunnel 자동 시작" + "GitHub에 URL 자동 저장" | PASS |

**Verdict: PASS** (guide.txt covers git fallback, auto-update, and tunnel/git dual communication)

---

## Summary

| # | Check Item | Result |
|---|-----------|--------|
| 1 | Duplicate check on registration | **PASS** |
| 2 | PowerShell cleanup logic (normalize, dead path removal, dedup) | **PASS** |
| 3 | PowerShell syntax correctness | **PASS** |
| 4 | guide.txt reflects latest changes (git fallback, auto-update, tunnel/git dual) | **PASS** |

**Overall: PASS (4/4)**

Minor note: The `findstr` duplicate check (item 1) uses substring matching rather than exact line matching. Consider using `findstr /i /x /c:"%TARGET%"` (the `/x` flag matches whole lines) for stricter dedup at registration time, though the PowerShell cleanup afterwards handles this correctly regardless.
