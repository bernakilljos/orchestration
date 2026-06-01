# resource-guard.ps1 — CPU/RAM/Defender/Bash 통합 리소스 모니터
# 사용: powershell -NoProfile -ExecutionPolicy Bypass -File resource-guard.ps1 [-IntervalSec 5]
# 안정화 후 자동으로 10분 간격 전환
param(
  [int]$IntervalSec = 5,          # 초기 5초
  [int]$CruiseIntervalSec = 600,  # 안정 시 10분
  [int]$CpuThreshold = 80,
  [int]$RamThreshold = 80,
  [int]$DefenderMaxMB = 200,
  [int]$BashMaxAgeSec = 120,
  [int]$StableCountForCruise = 12, # 12회 연속 OK = cruise 모드 전환
  [switch]$Once
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $ScriptRoot "..\logs\resource-guard.log"
$LogDir = Split-Path $LogFile
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-Log($msg) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$ts] $msg"
  Write-Host $line
  try { Add-Content -Path $LogFile -Value $line -Encoding UTF8 -ErrorAction SilentlyContinue } catch {}
}

function Get-ResourceUsage {
  $os = Get-CimInstance Win32_OperatingSystem
  $totalMB = [math]::Round($os.TotalVisibleMemorySize / 1024)
  $freeMB = [math]::Round($os.FreePhysicalMemory / 1024)
  $usedMB = $totalMB - $freeMB
  $ramPct = [math]::Round($usedMB / $totalMB * 100, 1)
  # CPU (fast sample 1s)
  $cpu = 0
  try {
    $cpu = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue, 1)
  } catch { $cpu = 0 }
  return @{ Cpu=$cpu; RamPct=$ramPct; UsedMB=$usedMB; TotalMB=$totalMB }
}

# --- Zombie bash killer ---
function Kill-ZombieBash {
  $now = Get-Date; $killed = 0
  Get-Process -Name "bash" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
      if ($_.StartTime -and ($now - $_.StartTime).TotalSeconds -gt $BashMaxAgeSec) {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $killed++
      }
    } catch {}
  }
  if ($killed -gt 0) { Write-Log "  BASH: killed $killed zombie (age>${BashMaxAgeSec}s)" }
  return $killed
}

# --- Defender memory trim ---
function Limit-Defender {
  $proc = Get-Process -Name "MsMpEng" -ErrorAction SilentlyContinue
  if (!$proc) { return }
  $mb = [math]::Round($proc.WorkingSet64 / 1MB)
  if ($mb -gt $DefenderMaxMB) {
    Write-Log "  DEFENDER: ${mb}MB > ${DefenderMaxMB}MB limit — trimming"
    try {
      $handle = (Get-Process -Id $proc.Id)
      $handle.MinWorkingSet = [IntPtr]::new(1MB)
      $handle.MaxWorkingSet = [IntPtr]::new($DefenderMaxMB * 1MB)
    } catch {
      Write-Log "  DEFENDER: trim failed (needs admin) — $($_.Exception.Message)"
    }
  }
}

# --- Bloatware killer ---
$Bloatware = @("LGSmartAssistantExtension","GameBar","GameBarPresenceWriter",
               "YourPhone","PhoneExperienceHost","MusNotification",
               "Video.UI","HelpPane","OneDrive","SearchHost",
               "StartMenuExperienceHost","sqlservr")

function Kill-Bloatware {
  foreach ($name in $Bloatware) {
    $p = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($p) {
      Stop-Process -Name $name -Force -ErrorAction SilentlyContinue
      Write-Log "  BLOAT: killed $name"
    }
  }
}

# --- Heavy node killer (RAM emergency) ---
function Kill-HeavyNode($res) {
  $killed = @()
  $targets = Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.WorkingSet64 -gt 300MB } |
    Sort-Object WorkingSet64 -Descending
  foreach ($p in $targets) {
    if ($res.RamPct -le $RamThreshold) { break }
    $mb = [math]::Round($p.WorkingSet64/1MB)
    Write-Log "  NODE: kill PID=$($p.Id) (${mb}MB)"
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    $killed += "node:$($p.Id)(${mb}MB)"
    Start-Sleep 1
    $res = Get-ResourceUsage
  }
  return $killed
}

function Show-Top5 {
  Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 | ForEach-Object {
    "$($_.Name):$([math]::Round($_.WorkingSet64/1MB))MB"
  }
}

# === Main loop ===
$currentInterval = $IntervalSec
$stableCount = 0
$run = 0
$isCruise = $false

Write-Log "=== RESOURCE-GUARD START (fast:${IntervalSec}s cruise:${CruiseIntervalSec}s defender<${DefenderMaxMB}MB bash-ttl:${BashMaxAgeSec}s) ==="

do {
  $run++
  $r = Get-ResourceUsage
  $isWarn = ($r.Cpu -gt $CpuThreshold -or $r.RamPct -gt $RamThreshold)

  # Always run cleanup
  Kill-ZombieBash | Out-Null
  Limit-Defender
  Kill-Bloatware

  if ($isWarn) {
    $stableCount = 0
    if ($isCruise) {
      $currentInterval = $IntervalSec
      $isCruise = $false
      Write-Log "!! BACK TO FAST MODE (${IntervalSec}s)"
    }
    $status = "CPU=$($r.Cpu)% RAM=$($r.RamPct)% ($($r.UsedMB)/$($r.TotalMB)MB)"
    Write-Log "WARN $status"
    $top = (Show-Top5) -join " | "
    Write-Log "  TOP5: $top"

    if ($r.RamPct -gt $RamThreshold) {
      $killed = Kill-HeavyNode $r
      if ($killed.Count -gt 0) { Write-Log "  THROTTLED: $($killed -join ', ')" }
    }
  } else {
    $stableCount++
    # Report every 10th run or first run
    if ($run -eq 1 -or $run % 10 -eq 0) {
      $status = "CPU=$($r.Cpu)% RAM=$($r.RamPct)% ($($r.UsedMB)/$($r.TotalMB)MB)"
      Write-Log "OK $status [stable:$stableCount]"
    }
    # Switch to cruise mode
    if (!$isCruise -and $stableCount -ge $StableCountForCruise) {
      $currentInterval = $CruiseIntervalSec
      $isCruise = $true
      Write-Log ">> CRUISE MODE (${CruiseIntervalSec}s interval) after $stableCount stable checks"
    }
  }

  if (!$Once) { Start-Sleep -Seconds $currentInterval }
} while (!$Once)

Write-Log "=== RESOURCE-GUARD END ==="
