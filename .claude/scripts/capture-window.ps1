# capture-window.ps1 — 지정한 창 하나만 캡처 (R322 · 다른 업무 창이 섞이지 않게)
#
# 왜: 화면 좌표를 찍는 CopyFromScreen 은 그 위에 겹친 다른 창(예: Excel 업무 문서)까지 찍는다 (2026-11-05 사고).
#     PrintWindow(PW_RENDERFULLCONTENT) 는 창이 자기 내용만 그려 주므로, 다른 창이 위에 있어도 섞이지 않는다.
# 사용:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .claude\scripts\capture-window.ps1 -Title "Visual Studio Code" -Out <경로.png>
#   -Title 은 창 제목의 일부 (대소문자 무시) · 맞는 창이 여러 개면 -Index 로 고른다 (기본 0) · -List 는 후보만 출력
# 화면 전체·여러 모니터는 찍지 않는다. 최소화된 창은 내용이 없어 실패로 끝낸다 (빈 이미지를 성공으로 내지 않음).
param(
    [string]$Title = "Visual Studio Code",
    [string]$Out = "",
    [int]$Index = 0,
    [switch]$List
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class OrcaWin {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
"@

$cands = @(Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Title*" } |
    Sort-Object Id | ForEach-Object { [pscustomobject]@{ Id = $_.Id; Name = $_.ProcessName; Title = $_.MainWindowTitle; Handle = $_.MainWindowHandle } })
if ($List) { $cands | Format-Table -AutoSize; exit 0 }
if ($cands.Count -eq 0) { Write-Error "창 없음: 제목에 '$Title' 이 든 창을 찾지 못함 (-List 로 후보 확인)"; exit 2 }
if ($Index -ge $cands.Count) { Write-Error "Index $Index 범위 밖 (후보 $($cands.Count)개)"; exit 2 }
$w = $cands[$Index]
if ([OrcaWin]::IsIconic($w.Handle)) { Write-Error "최소화된 창은 내용이 없어 캡처하지 않음: $($w.Title)"; exit 3 }

$r = New-Object OrcaWin+RECT
[void][OrcaWin]::GetWindowRect($w.Handle, [ref]$r)
$width = $r.Right - $r.Left; $height = $r.Bottom - $r.Top
if ($width -le 0 -or $height -le 0) { Write-Error "창 크기 0: $($w.Title)"; exit 3 }

$bmp = New-Object System.Drawing.Bitmap($width, $height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [OrcaWin]::PrintWindow($w.Handle, $hdc, 2)   # 2 = PW_RENDERFULLCONTENT (Chromium·VS Code 내용까지)
$g.ReleaseHdc($hdc); $g.Dispose()
if (-not $ok) { $bmp.Dispose(); Write-Error "PrintWindow 실패: $($w.Title)"; exit 4 }

if (-not $Out) { $Out = Join-Path ([System.IO.Path]::GetTempPath()) ("window-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".png") }
$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "[capture-window] $($w.Name) '$($w.Title)' ${width}x${height} -> $Out"
