#requires -version 5.1
<#
.SYNOPSIS
  Claude Code winget upgrade with proper exit code handling.
  Called from install.bat / setup module to avoid inline PowerShell parsing in cmd blocks.
#>

$ErrorActionPreference = 'SilentlyContinue'

$args_list = @(
    'upgrade',
    '--id', 'Anthropic.ClaudeCode',
    '--accept-source-agreements',
    '--accept-package-agreements'
)

$p = Start-Process 'winget' -ArgumentList $args_list -NoNewWindow -PassThru
if (-not $p) {
    Write-Host '[WARN] winget process start failed'
    exit 0
}

if (-not $p.WaitForExit(120000)) {
    $p.Kill()
    Write-Host '[WARN] winget upgrade timeout'
    exit 0
}

$c = $p.ExitCode
if ($c -eq 0) {
    Write-Host '[OK] Claude Code updated'
}
elseif ($c -eq -1978335189) {
    Write-Host '[OK] Already up to date'
}
else {
    $hex = '{0:X8}' -f $c
    Write-Host "[WARN] Update failed (exit 0x$hex) - close Claude Code and retry"
}
exit 0
