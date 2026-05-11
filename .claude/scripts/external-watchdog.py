#!/usr/bin/env python3
"""External OS-level watchdog — runs OUTSIDE Claude Code via Task Scheduler.

Claude Code 의 내부 watchdog.py 는 Claude 가 살아 있을 때만 동작한다.
VSCode 자체가 hang 되면 내부 watchdog 도 같이 죽어서 복구 불가 → 이 외부 데몬이 보완.

스케줄: Windows Task Scheduler 가 1분 간격으로 호출.
체크:
  1. heartbeat 파일 (.claude/orca-heartbeat) mtime
  2. Code.exe / claude.exe 프로세스 존재
  3. 5분 이상 heartbeat 정지 + VSCode 프로세스 살아있음 → hang 의심

행동:
  - 기본: 로그만 남김 (./claude/state/external-watchdog.log)
  - WATCHDOG_AUTO_RESTART=1 환경변수 있으면 VSCode 강제 재시작 (데이터 손실 위험)
  - WATCHDOG_NOTIFY=1 이면 Windows 토스트 알림

사용:
  python .claude/scripts/external-watchdog.py
  python .claude/scripts/external-watchdog.py --once  (한 번 실행, Task Scheduler 용)
  python .claude/scripts/external-watchdog.py --loop  (디버그용 무한 루프)
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
STALE_THRESHOLD_SEC = 300  # 5분 무갱신 = hang 의심
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB 초과 시 회전


def project_root() -> Path:
    """script 위치 기반 프로젝트 루트 추정 (.claude/scripts/external-watchdog.py)."""
    if "ORCHESTRATION_ROOT" in os.environ:
        return Path(os.environ["ORCHESTRATION_ROOT"])
    return Path(__file__).resolve().parent.parent.parent


def log(root: Path, msg: str, level: str = "info") -> None:
    """프로젝트 루트 기준 log 파일에 한 줄 append."""
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
    """tasklist 로 프로세스 존재 확인 (Windows). Unix 면 pgrep."""
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
    """heartbeat 파일 마지막 갱신 후 경과 초 (없으면 None)."""
    hb = root / HEARTBEAT_FILE
    if not hb.exists():
        return None
    return int(time.time() - hb.stat().st_mtime)


def windows_toast(title: str, msg: str) -> None:
    """선택적 Windows 토스트 — 의존성 없이 powershell BurntToast 사용 시도."""
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
        pass  # BurntToast 미설치면 조용히 skip


def restart_vscode(root: Path) -> None:
    """VSCode 강제 종료 + 재시작 (위험 — WATCHDOG_AUTO_RESTART=1 필요)."""
    log(root, "VSCode 강제 재시작 시작 (auto-restart 활성)", "warn")
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
            log(root, f"VSCode 재시작 명령 발행: {code_path} {proj}", "warn")
        else:
            log(root, f"VSCODE_PATH 부재: {code_path}", "error")


def run_once(root: Path) -> int:
    """1회 점검. 정상=0, hang 의심=2, 프로세스 죽음=1."""
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

    # hang 의심: VSCode 살아있는데 heartbeat 오래됨
    if code_alive and hb_age is not None and hb_age > STALE_THRESHOLD_SEC:
        log(root, f"HANG_SUSPECTED — {state}", "warn")
        if notify:
            windows_toast("Claude Orca 경고", f"VSCode hang 의심 (hb {hb_age}s)")
        if auto_restart:
            restart_vscode(root)
        return 2

    if not code_alive:
        log(root, f"VSCODE_NOT_RUNNING — {state}", "info")
        return 1

    log(root, f"OK — {state}", "info")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="1회 실행 후 종료 (Task Scheduler 권장)")
    parser.add_argument("--loop", action="store_true", help="60초 간격 무한 루프 (디버그)")
    args = parser.parse_args()

    root = project_root()

    if args.loop:
        while True:
            try:
                run_once(root)
            except Exception as e:
                log(root, f"FATAL: {e}", "error")
            time.sleep(60)
    else:
        return run_once(root)


if __name__ == "__main__":
    sys.exit(main() or 0)
