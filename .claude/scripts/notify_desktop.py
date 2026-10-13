"""
notify_desktop — Windows/Mac/Linux 데스크톱 알림 (Task 38)
백그라운드 task 완료-크리티컬 5 알림 - watchdog 통합
사용: python notify_desktop.py "제목" "본문" [urgency]
"""
from __future__ import annotations
import platform
import subprocess
import sys


def _windows(title: str, body: str) -> None:
    # PowerShell BurntToast 또는 Windows Runtime
    try:
        ps = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.BalloonTipTitle = "{title}"
$n.BalloonTipText = "{body}"
$n.Visible = $true
$n.ShowBalloonTip(5000)
Start-Sleep -Seconds 6
$n.Dispose()
'''.strip()
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            timeout=10,
        )
    except Exception as e:
        sys.stderr.write(f"[notify-win] {e}\n")


def _mac(title: str, body: str) -> None:
    try:
        script = f'display notification "{body}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception as e:
        sys.stderr.write(f"[notify-mac] {e}\n")


def _linux(title: str, body: str, urgency: str = "normal") -> None:
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, title, body], capture_output=True, timeout=5
        )
    except Exception as e:
        sys.stderr.write(f"[notify-linux] {e}\n")


def notify(title: str, body: str, urgency: str = "normal") -> None:
    system = platform.system()
    if system == "Windows":
        _windows(title, body)
    elif system == "Darwin":
        _mac(title, body)
    elif system == "Linux":
        _linux(title, body, urgency)
    else:
        sys.stderr.write(f"[notify] unsupported OS: {system}\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('usage: notify_desktop.py "제목" "본문" [urgency=normal|low|critical]')
        sys.exit(0)
    title = sys.argv[1]
    body = sys.argv[2]
    urg = sys.argv[3] if len(sys.argv) > 3 else "normal"
    notify(title, body, urg)
    print(f"[ok] notified: {title}")
