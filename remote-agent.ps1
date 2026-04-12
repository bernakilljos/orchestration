$ErrorActionPreference = 'SilentlyContinue'

$pat    = [System.Environment]::GetEnvironmentVariable('GITHUB_PERSONAL_ACCESS_TOKEN','User')
if (-not $pat) { $pat = '' }
$owner  = 'bernakilljos'
$repo   = 'orchestration-status'
$pcId   = ($env:COMPUTERNAME + '-' + ((Get-NetAdapter | Where-Object {$_.MacAddress} | Sort-Object InterfaceIndex | Select-Object -First 1).MacAddress -replace '-','').Substring(0,6))
$hdrs   = @{ Authorization="token $pat"; Accept='application/vnd.github.v3+json' }
$base   = "https://api.github.com/repos/$owner/$repo/contents/remote/$pcId"
$urlFile = "$env:USERPROFILE\.claude\dashboard-url.txt"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -MemberDefinition @"
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(uint f, int x, int y, uint d, int e);
[DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, int e);
"@ -Name "Win32" -Namespace "PInvoke"

# --- Dashboard URL ---
$dashUrl = ''
function Get-DashUrl {
    # 1) 로컬 캐시
    if (Test-Path $urlFile) {
        $cached = Get-Content $urlFile -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cached -match '^https?://') { return $cached.Trim() }
    }
    # 2) GitHub
    try {
        $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$repo/contents/dashboard-url.json" -Headers $hdrs -ErrorAction Stop
        $urlJson = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($resp.content)) | ConvertFrom-Json
        if ($urlJson.url) {
            $urlJson.url | Set-Content $urlFile -Encoding UTF8
            return $urlJson.url
        }
    } catch {}
    return ''
}

# --- GitHub helpers (fallback) ---
function GhGet($path) {
    try { Invoke-RestMethod -Uri "$base/$path" -Headers $hdrs -ErrorAction Stop } catch { $null }
}
$shaCache = @{}
function GhPut($path, $bytes, $msg) {
    $body = @{ message=$msg; content=[Convert]::ToBase64String($bytes) }
    if ($shaCache[$path]) { $body.sha = $shaCache[$path] }
    else {
        $existing = GhGet $path
        if ($existing.sha) { $body.sha = $existing.sha }
    }
    try {
        $result = Invoke-RestMethod -Uri "$base/$path" -Method Put -Headers $hdrs -Body ($body|ConvertTo-Json) -ContentType 'application/json' -ErrorAction Stop
        if ($result.content.sha) { $shaCache[$path] = $result.content.sha }
    } catch {
        $shaCache.Remove($path)
        $existing = GhGet $path
        $body2 = @{ message=$msg; content=[Convert]::ToBase64String($bytes) }
        if ($existing.sha) { $body2.sha = $existing.sha }
        $result2 = Invoke-RestMethod -Uri "$base/$path" -Method Put -Headers $hdrs -Body ($body2|ConvertTo-Json) -ContentType 'application/json' -ErrorAction SilentlyContinue
        if ($result2.content.sha) { $shaCache[$path] = $result2.content.sha }
    }
}
function GhPutText($path, $text, $msg) {
    GhPut $path ([System.Text.Encoding]::UTF8.GetBytes($text)) $msg
}

# --- Screen Capture ---
function CaptureScreen($idx) {
    $s = [System.Windows.Forms.Screen]::AllScreens[$idx]
    $b = $s.Bounds
    $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Left, $b.Top, 0, 0, (New-Object System.Drawing.Size($b.Width, $b.Height)))
    $g.Dispose()
    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object {$_.MimeType -eq 'image/jpeg'}
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 50L)
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, $codec, $ep)
    $bmp.Dispose()
    return $ms.ToArray()
}

# --- Upload Screenshots: Dashboard 직접 → GitHub fallback ---
function TakeAllScreenshots {
    $screens = [System.Windows.Forms.Screen]::AllScreens
    for ($i = 0; $i -lt $screens.Count; $i++) {
        $imgBytes = CaptureScreen $i
        $sent = $false
        if ($script:dashUrl) {
            try {
                $req = [System.Net.HttpWebRequest]::Create("$($script:dashUrl)/push-screen")
                $req.Method = 'POST'
                $req.ContentType = 'application/octet-stream'
                $req.ContentLength = $imgBytes.Length
                $req.Headers.Add('X-PC-ID', $pcId)
                $req.Headers.Add('X-Monitor', "$i")
                $req.Timeout = 10000
                $stream = $req.GetRequestStream()
                $stream.Write($imgBytes, 0, $imgBytes.Length)
                $stream.Close()
                $resp = $req.GetResponse()
                $resp.Close()
                $sent = $true
            } catch {
                # Dashboard 전송 실패 → URL 캐시 삭제
                Remove-Item $urlFile -ErrorAction SilentlyContinue
                $script:dashUrl = ''
            }
        }
        # dashUrl 없을 때 GitHub fallback 안 함 (rate limit 방지)
    }
}

# --- Push Remote Status ---
function PushScreensJson {
    $screens = [System.Windows.Forms.Screen]::AllScreens
    $arr = @()
    for ($i = 0; $i -lt $screens.Count; $i++) {
        $b = $screens[$i].Bounds
        $arr += "{`"i`":$i,`"w`":$($b.Width),`"h`":$($b.Height),`"x`":$($b.Left),`"y`":$($b.Top)}"
    }
    $json = "{`"pc_id`":`"$pcId`",`"state`":`"ready`",`"count`":$($screens.Count),`"screens`":[" + ($arr -join ',') + "]}"

    $sent = $false
    if ($script:dashUrl) {
        try {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            $req = [System.Net.HttpWebRequest]::Create("$($script:dashUrl)/push-remote-status")
            $req.Method = 'POST'
            $req.ContentType = 'application/json'
            $req.ContentLength = $bytes.Length
            $req.Timeout = 10000
            $stream = $req.GetRequestStream()
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Close()
            $resp = $req.GetResponse()
            $resp.Close()
            $sent = $true
        } catch {}
    }
    # dashUrl 없을 때 GitHub fallback 안 함 (rate limit 방지)
}

# --- Pull Command from Dashboard ---
function PullDashboardCmd {
    if (-not $script:dashUrl) { return $null }
    try {
        $resp = Invoke-RestMethod -Uri "$($script:dashUrl)/pull-cmd/$pcId" -TimeoutSec 5 -ErrorAction Stop
        if ($resp -and $resp.action) { return $resp }
    } catch {
        Remove-Item $urlFile -ErrorAction SilentlyContinue
        $script:dashUrl = ''
    }
    return $null
}

# --- Input Actions ---
function DoClick($x, $y, $btn, $monitor) {
    $screens = [System.Windows.Forms.Screen]::AllScreens
    $idx = if ($monitor -ne $null -and $monitor -lt $screens.Count) { $monitor } else { 0 }
    $b = $screens[$idx].Bounds
    $ax = [int]($b.Left + $x * $b.Width)
    $ay = [int]($b.Top  + $y * $b.Height)
    [PInvoke.Win32]::SetCursorPos($ax, $ay)
    Start-Sleep -Milliseconds 50
    if ($btn -eq 'right') {
        [PInvoke.Win32]::mouse_event(8,  0, 0, 0, 0)
        [PInvoke.Win32]::mouse_event(16, 0, 0, 0, 0)
    } else {
        [PInvoke.Win32]::mouse_event(2, 0, 0, 0, 0)
        [PInvoke.Win32]::mouse_event(4, 0, 0, 0, 0)
    }
}

function DoKey($key) {
    if ($key -eq '{HANGUL}') { [PInvoke.Win32]::keybd_event(0x15, 0, 0, 0); [PInvoke.Win32]::keybd_event(0x15, 0, 2, 0); return }
    if ($key -eq '{HANJA}')  { [PInvoke.Win32]::keybd_event(0x19, 0, 0, 0); [PInvoke.Win32]::keybd_event(0x19, 0, 2, 0); return }
    [System.Windows.Forms.SendKeys]::SendWait($key)
}

function HandleCmd($cmd) {
    switch ($cmd.action) {
        'stop'     { Write-Host "[Remote] Stop"; PushScreensJson; exit }
        'click'    { DoClick $cmd.x $cmd.y $cmd.btn $cmd.monitor }
        'dblclick' { DoClick $cmd.x $cmd.y 'left' $cmd.monitor; Start-Sleep -Milliseconds 80; DoClick $cmd.x $cmd.y 'left' $cmd.monitor }
        'key'      { DoKey $cmd.key }
        'drag'     {
            $screens = [System.Windows.Forms.Screen]::AllScreens
            $idx = if ($cmd.monitor -ne $null -and $cmd.monitor -lt $screens.Count) { $cmd.monitor } else { 0 }
            $b = $screens[$idx].Bounds
            $x0 = [int]($b.Left + $cmd.x0 * $b.Width)
            $y0 = [int]($b.Top  + $cmd.y0 * $b.Height)
            $x1 = [int]($b.Left + $cmd.x1 * $b.Width)
            $y1 = [int]($b.Top  + $cmd.y1 * $b.Height)
            [PInvoke.Win32]::SetCursorPos($x0, $y0)
            Start-Sleep -Milliseconds 50
            [PInvoke.Win32]::mouse_event(2, 0, 0, 0, 0)
            Start-Sleep -Milliseconds 50
            $steps = 10
            for ($s = 1; $s -le $steps; $s++) {
                $mx = [int]($x0 + ($x1 - $x0) * $s / $steps)
                $my = [int]($y0 + ($y1 - $y0) * $s / $steps)
                [PInvoke.Win32]::SetCursorPos($mx, $my)
                Start-Sleep -Milliseconds 20
            }
            [PInvoke.Win32]::mouse_event(4, 0, 0, 0, 0)
        }
    }
}

# ══════════════════════════════════════════
#  메인 루프
# ══════════════════════════════════════════
Write-Host "[Remote] Agent started for $pcId"

$dashUrl = Get-DashUrl
Write-Host "[Remote] Dashboard: $(if ($dashUrl) { $dashUrl } else { 'not found (GitHub fallback)' })"

# 초기
TakeAllScreenshots
PushScreensJson

$lastCmdSha = ''
$urlTick = 0

while ($true) {
    Start-Sleep -Milliseconds 200

    # Dashboard URL 주기적 갱신 (5분마다)
    $urlTick++
    if ($urlTick -ge 1500 -and -not $dashUrl) {
        $dashUrl = Get-DashUrl
        $urlTick = 0
    }

    # 1) Dashboard에서 명령 polling
    $cmd = PullDashboardCmd
    if ($cmd) {
        HandleCmd $cmd
        Start-Sleep -Milliseconds 300
        TakeAllScreenshots
        $urlTick = 0
        continue
    }

    # 2) GitHub fallback 명령 확인
    if (-not $dashUrl) {
        $cmdFile = GhGet "cmd.json"
        if ($cmdFile -and $cmdFile.sha -ne $lastCmdSha -and $cmdFile.content) {
            $lastCmdSha = $cmdFile.sha
            $cmd2 = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($cmdFile.content)) | ConvertFrom-Json
            HandleCmd $cmd2
            Start-Sleep -Milliseconds 300
            TakeAllScreenshots
            $urlTick = 0
            continue
        }
    }

    TakeAllScreenshots
}
