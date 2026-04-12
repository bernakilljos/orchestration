param(
    [string]$GuideFile,
    [string]$UserProfile,
    [string]$GithubPat
)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'SilentlyContinue'

if (-not (Test-Path $GuideFile)) {
    Write-Host "  [SKIP] CLAUDE_SETUP_GUIDE.md not found: $GuideFile"
    exit 0
}

# Get current MCP list
Write-Host "  Checking installed MCPs..."
$job = Start-Job { claude mcp list 2>$null }
$mcpList = if (Wait-Job $job -Timeout 15) { Receive-Job $job } else { Remove-Job $job -Force; '' }
$mcpList = ($mcpList -join ' ')

# Get GEMINI_API_KEY
$geminiKey = [System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')
if (-not $geminiKey) {
    $geminiKey = [System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'Machine')
}
if (-not $geminiKey) {
    $geminiKey = $env:GEMINI_API_KEY
}

# Parse guide for 'claude mcp add' lines
$lines = Get-Content $GuideFile -Encoding UTF8 | Where-Object { $_ -match '^\s*claude mcp add' }

$installed = 0
$skipped = 0
$failed = 0

foreach ($line in $lines) {
    $cmd = $line.Trim()

    # filesystem / github: handled separately in install.bat
    if ($cmd -match '\bfilesystem\b' -or $cmd -match '\bgithub\b') { continue }

    # Extract MCP name: first non-flag token after 'mcp add'
    $parts = ($cmd -split '\s+') | Where-Object { $_ -ne '' }
    $name = ''
    $skipNext = $false
    for ($i = 2; $i -lt $parts.Length; $i++) {
        if ($skipNext) { $skipNext = $false; continue }
        if ($parts[$i] -match '^-') {
            # -s, -e take a value; single-char flags
            if ($parts[$i] -match '^-[se]$') { $skipNext = $true }
            continue
        }
        if ($parts[$i] -eq '--') { continue }
        $name = $parts[$i]; break
    }
    if (-not $name) { continue }

    # Skip if already installed
    if ($mcpList -match "(?<!\w)$([regex]::Escape($name))(?!\w)") {
        Write-Host "  [OK] Already installed: $name"
        $skipped++
        continue
    }

    # Substitute GEMINI_API_KEY placeholder
    if ($cmd -match 'GEMINI_API_KEY=your-key') {
        if (-not $geminiKey) {
            Write-Host "  [WARN] Skipping gemini MCP - GEMINI_API_KEY not set!"
            Write-Host "         Set it with: setx GEMINI_API_KEY `"AI...`""
            Write-Host "         Then reopen terminal and run: $cmd"
            $skipped++
            continue
        }
        $cmd = $cmd -replace 'GEMINI_API_KEY=your-key', "GEMINI_API_KEY=$geminiKey"
    }

    Write-Host "  [+] Adding MCP: $name ..."

    # Execute the claude mcp add command directly (no cmd /c wrapping)
    # The command is already a valid claude CLI invocation
    $mcpArgs = ($cmd -replace '^claude\s+', '') -split '\s+'
    $mcpArgs = $mcpArgs | Where-Object { $_ -ne '' }

    try {
        $p = Start-Process 'claude' -ArgumentList $mcpArgs -NoNewWindow -PassThru -Wait
        if ($p.ExitCode -eq 0) {
            Write-Host "  [OK] $name installed successfully"
            $installed++
        } else {
            Write-Host "  [FAIL] $name install failed (exit code: $($p.ExitCode))"
            Write-Host "         Manual fix: $cmd"
            $failed++
        }
    } catch {
        Write-Host "  [FAIL] $name install error: $_"
        Write-Host "         Manual fix: $cmd"
        $failed++
    }
}

Write-Host ""
Write-Host "  MCP setup complete: $installed added, $skipped skipped, $failed failed"
if ($failed -gt 0) {
    Write-Host "  [!] $failed MCP(s) failed - see manual fix commands above"
}
