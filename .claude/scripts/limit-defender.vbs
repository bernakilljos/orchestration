Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File C:\pjt\orchestration_v1\.claude\scripts\disable-defender.ps1", "", "runas", 1
