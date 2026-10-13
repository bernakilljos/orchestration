#!/usr/bin/env python3
"""External OS-level watchdog ??runs OUTSIDE Claude Code via Task Scheduler.

Claude Code ???대? watchdog.py ??Claude 媛 ?댁븘 ?덉쓣 ?뚮쭔 ?숈옉?쒕떎.
VSCode ?먯껜媛 hang ?섎㈃ ?대? watchdog ??媛숈씠 二쎌뼱??蹂듦뎄 遺덇? -> ???몃? ?곕が??蹂댁셿.

?ㅼ?以? Windows Task Scheduler 媛 1遺?媛꾧꺽?쇰줈 ?몄텧.
泥댄겕:
  1. heartbeat ?뚯씪 (.claude/orca-heartbeat) mtime
  2. Code.exe / claude.exe ?꾨줈?몄뒪 議댁옱
  3. 5遺??댁긽 heartbeat ?뺤? + VSCode ?꾨줈?몄뒪 ?댁븘?덉쓬 -> hang ?섏떖

?됰룞:
  - 湲곕낯: 濡쒓렇留??④? (./claude/state/external-watchdog.log)
  - WATCHDOG_AUTO_RESTART=1 ?섍꼍蹂???덉쑝硫?VSCode 媛뺤젣 ?ъ떆??(?곗씠???먯떎 ?꾪뿕)
  - WATCHDOG_NOTIFY=1 ?대㈃ Windows ?좎뒪???뚮┝

?ъ슜:
  python .claude/scripts/external-watchdog.py
  python .claude/scripts/external-watchdog.py --once  (??踰??ㅽ뻾, Task Scheduler ??
  python .claude/scripts/external-watchdog.py --loop  (?붾쾭洹몄슜 臾댄븳 猷⑦봽)
"""
import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HEARTBEAT_FILE = ".claude/orca-heartbeat"
LOG_FILE = ".claude/state/external-watchdog.log"
STALE_THRESHOLD_SEC = 300  # 5遺?臾닿갚??= hang ?섏떖
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB 珥덇낵 ???뚯쟾


def project_root() -> Path:
    """script ?꾩튂 湲곕컲 ?꾨줈?앺듃 猷⑦듃 異붿젙 (.claude/scripts/external-watchdog.py)."""
    if "ORCHESTRATION_ROOT" in os.environ:
        return Path(os.environ["ORCHESTRATION_ROOT"])
    return Path(__file__).resolve().parent.parent.parent


def log(root: Path, msg: str, level: str = "info") -> None:
    """?꾨줈?앺듃 猷⑦듃 湲곗? log ?뚯씪????以?append."""
    log_path = root / LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if log_path.exists() and log_path.stat().st_size > LOG_MAX_BYTES:
            backup = log_path.with_suffix(log_path.suffix + ".1")
            if backup.exists():
                backup.unlink()
            log_path.rename(backup)
    except OSError:
        pass
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [{level}] {msg}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def find_process(name: str) -> bool:
    """tasklist 濡??꾨줈?몄뒪 議댁옱 ?뺤씤 (Windows). Unix 硫?pgrep."""
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                stderr=subprocess.DEVNULL, timeout=5,
            ).decode("utf-8", "ignore")
            return "No tasks" not in out and name.lower() in out.lower()
        else:
            r = subprocess.run(["pgrep", "-f", name], capture_output=True, timeout=5)
            return r.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def heartbeat_age_sec(root: Path):
    """heartbeat ?뚯씪 留덉?留?媛깆떊 ??寃쎄낵 珥?(?놁쑝硫?None)."""
    hb = root / HEARTBEAT_FILE
    if not hb.exists():
        return None
    return int(time.time() - hb.stat().st_mtime)


def windows_toast(title: str, msg: str) -> None:
    """?좏깮??Windows ?좎뒪?????섏〈???놁씠 powershell BurntToast ?ъ슜 ?쒕룄."""
    if platform.system() != "Windows":
        return
    try:
        ps = (
            f"New-BurntToastNotification -Text '{title}','{msg}'"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        pass  # BurntToast 誘몄꽕移섎㈃ 議곗슜??skip


def restart_vscode(root: Path) -> None:
    """VSCode 媛뺤젣 醫낅즺 + ?ъ떆??(?꾪뿕 ??WATCHDOG_AUTO_RESTART=1 ?꾩슂)."""
    log(root, "VSCode 媛뺤젣 ?ъ떆???쒖옉 (auto-restart ?쒖꽦)", "warn")
    if platform.system() == "Windows":
        subprocess.run(
            ["taskkill", "/F", "/IM", "Code.exe", "/T"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        code_path = os.environ.get(
            "VSCODE_PATH",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        )
        proj = str(root)
        if os.path.exists(code_path):
            subprocess.Popen([code_path, proj])
            log(root, f"VSCode ?ъ떆??紐낅졊 諛쒗뻾: {code_path} {proj}", "warn")
        else:
            log(root, f"VSCODE_PATH 遺?? {code_path}", "error")


def run_once(root: Path) -> int:
    """1???먭?. ?뺤긽=0, hang ?섏떖=2, ?꾨줈?몄뒪 二쎌쓬=1."""
    code_alive = find_process("Code.exe")
    claude_alive = find_process("claude.exe")
    hb_age = heartbeat_age_sec(root)

    state = (
        f"vscode={'alive' if code_alive else 'DEAD'} "
        f"claude={'alive' if claude_alive else 'DEAD'} "
        f"hb_age={hb_age}s"
    )

    auto_restart = os.environ.get("WATCHDOG_AUTO_RESTART") == "1"
    notify = os.environ.get("WATCHDOG_NOTIFY") == "1"

    # hang ?섏떖: VSCode ?댁븘?덈뒗??heartbeat ?ㅻ옒??
    if code_alive and hb_age is not None and hb_age > STALE_THRESHOLD_SEC:
        log(root, f"HANG_SUSPECTED ??{state}", "warn")
        if notify:
            windows_toast("Claude Orca 寃쎄퀬", f"VSCode hang ?섏떖 (hb {hb_age}s)")
        if auto_restart:
            restart_vscode(root)
        return 2

    if not code_alive:
        log(root, f"VSCODE_NOT_RUNNING ??{state}", "info")
        return 1

    log(root, f"OK ??{state}", "info")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="1???ㅽ뻾 ??醫낅즺 (Task Scheduler 沅뚯옣)")
    parser.add_argument("--loop", action="store_true", help="60珥?媛꾧꺽 臾댄븳 猷⑦봽 (?붾쾭洹?")
    args = parser.parse_args()

    root = project_root()

    if args.loop:
        while True:
            try:
                run_once(root)
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
                log(root, f"FATAL: {e}", "error")
            time.sleep(60)
    else:
        return run_once(root)


if __name__ == "__main__":
    sys.exit(main() or 0)

