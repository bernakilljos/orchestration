# install-plugins.ps1
# Claude 플러그인 설치 헬퍼 - install.bat / 08-plugins.bat 에서 호출
# 사용법: powershell -File install-plugins.ps1 [-UserProfile "C:\Users\..."]
param(
    [string]$UserProfile = $env:USERPROFILE
)

$ErrorActionPreference = 'SilentlyContinue'

# installed_plugins.json 직접 읽어서 설치 여부 확인 (claude plugin list 실행 안 함)
$pluginJson = Join-Path $UserProfile '.claude\plugins\installed_plugins.json'
$mktJson    = Join-Path $UserProfile '.claude\plugins\known_marketplaces.json'

$installedText = if (Test-Path $pluginJson) { Get-Content $pluginJson -Raw -Encoding UTF8 } else { '' }
$mktText       = if (Test-Path $mktJson)    { Get-Content $mktJson    -Raw -Encoding UTF8 } else { '' }

function Install-Plugin {
    param([string]$PluginName, [int]$TimeoutSec = 30)
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo.FileName               = 'claude'
    $proc.StartInfo.Arguments              = "plugin install $PluginName"
    $proc.StartInfo.UseShellExecute        = $false
    $proc.StartInfo.RedirectStandardInput  = $true
    $proc.StartInfo.RedirectStandardOutput = $true
    $proc.StartInfo.RedirectStandardError  = $true
    $proc.StartInfo.CreateNoWindow         = $true
    try {
        [void]$proc.Start()
        $proc.StandardInput.WriteLine('y')
        $proc.StandardInput.Close()
        if (-not $proc.WaitForExit($TimeoutSec * 1000)) { $proc.Kill() }
    } catch {}
}

function Add-Marketplace {
    param([string]$MarketplaceName, [int]$TimeoutSec = 30)
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo.FileName               = 'claude'
    $proc.StartInfo.Arguments              = "plugin marketplace add $MarketplaceName"
    $proc.StartInfo.UseShellExecute        = $false
    $proc.StartInfo.RedirectStandardInput  = $true
    $proc.StartInfo.RedirectStandardOutput = $true
    $proc.StartInfo.RedirectStandardError  = $true
    $proc.StartInfo.CreateNoWindow         = $true
    try {
        [void]$proc.Start()
        $proc.StandardInput.WriteLine('y')
        $proc.StandardInput.Close()
        if (-not $proc.WaitForExit($TimeoutSec * 1000)) { $proc.Kill() }
    } catch {}
}

# --- Official plugins ---
foreach ($p in @('claude-md-management', 'code-review', 'commit-commands')) {
    if ($installedText -match [regex]::Escape($p)) {
        Write-Host "      [OK] $p"
    } else {
        Write-Host "      Installing $p..."
        Install-Plugin $p 30
        # json 다시 읽기
        $installedText = if (Test-Path $pluginJson) { Get-Content $pluginJson -Raw -Encoding UTF8 } else { '' }
    }
}

# --- Superpowers marketplace ---
if ($mktText -notmatch 'superpowers-marketplace') {
    Write-Host '      Adding superpowers marketplace...'
    Add-Marketplace 'obra/superpowers-marketplace' 30
    $mktText = if (Test-Path $mktJson) { Get-Content $mktJson -Raw -Encoding UTF8 } else { '' }
} else {
    Write-Host '      [OK] superpowers marketplace'
}

# --- Superpowers plugin ---
if ($installedText -match 'superpowers') {
    Write-Host '      [OK] superpowers'
} else {
    Write-Host '      Installing superpowers...'
    Install-Plugin 'superpowers@superpowers-marketplace' 60
    $installedText = if (Test-Path $pluginJson) { Get-Content $pluginJson -Raw -Encoding UTF8 } else { '' }
}

# --- Community plugins ---
foreach ($p in @('ui-ux-pro-max', 'everything-claude-code', 'awesome-claude-code', 'get-shit-done')) {
    if ($installedText -match [regex]::Escape($p)) {
        Write-Host "      [OK] $p"
    } else {
        Write-Host "      Installing $p..."
        Install-Plugin $p 30
        $installedText = if (Test-Path $pluginJson) { Get-Content $pluginJson -Raw -Encoding UTF8 } else { '' }
    }
}

Write-Host '      Plugins Done'
