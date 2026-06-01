' defender-exclude-pjt.vbs — C:\pjt\ 폴더를 Defender 스캔 제외 (UAC 자동 elevate)
' 사용: 파일 익스플로러에서 더블클릭 → UAC "예" 클릭 → 자동 완료
Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "powershell.exe", "-NoProfile -ExecutionPolicy Bypass -Command ""Add-MpPreference -ExclusionPath 'C:\pjt'; Add-MpPreference -ExclusionPath 'C:\Users\ja205\.claude'; Add-MpPreference -ExclusionProcess 'python.exe'; Add-MpPreference -ExclusionProcess 'node.exe'; Add-MpPreference -ExclusionProcess 'bash.exe'; Write-Host '[OK] Defender exclusion 추가 완료 - C:\pjt, ~/.claude, python/node/bash'; Get-MpPreference | Select-Object -ExpandProperty ExclusionPath; Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess; Read-Host '아무 키나 누르면 닫힘'""", "", "runas", 1
