#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-Minute Memory Recovery Loop.

System metrics monitoring + cleanup automation.
Runs: python orca-10min-loop.py [--dry-run]
Logs: .claude/logs/orca-10min-loop.log
State: .claude/state/last-10min-loop.json
"""

import os
import sys
import json
import subprocess
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

# ============================================================================
# Config
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # -> project root
LOG_DIR = PROJECT_ROOT / ".claude" / "logs"
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
DB_PATH = STATE_DIR / "orca.db"
LOG_FILE = LOG_DIR / "orca-10min-loop.log"
STATE_FILE = STATE_DIR / "last-10min-loop.json"

THRESHOLD_RAM_PERCENT = 80  # RAM usage threshold
THRESHOLD_PROC_COUNT = 3    # Claude process threshold
IDLE_THRESHOLD_SEC = 600    # 10 minutes idle

DRY_RUN = "--dry-run" in sys.argv

# ============================================================================
# Logging (UTF-8 safe)
# ============================================================================

def log_msg(msg: str, level: str = "INFO"):
    """Append log line (UTF-8 safe, no interpolation issues)."""
    ts = datetime.now().isoformat()
    log_line = f"[{ts}] [{level}] {msg}"

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"[ERROR] Log write failed: {e}", file=sys.stderr)

    if level in ["WARN", "ERROR"]:
        print(log_line)

# ============================================================================
# System Metrics
# ============================================================================

def get_system_metrics():
    """Query system metrics using psutil (if available)."""
    try:
        if psutil is None:
            log_msg("psutil not installed, skipping metrics", "WARN")
            return {
                "ram_percent": 0,
                "cpu_percent": 0,
                "claude_procs": 0,
                "vscode_procs": 0,
                "timestamp": datetime.now().isoformat()
            }

        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        claude_count = 0
        vscode_count = 0

        for proc in psutil.process_iter(['name']):
            try:
                name = proc.name().lower()
                if 'claude' in name:
                    claude_count += 1
                if 'code' in name:
                    vscode_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass  # noqa: BLE001

        return {
            "ram_percent": round(ram_percent, 1),
            "cpu_percent": round(cpu_percent, 1),
            "claude_procs": claude_count,
            "vscode_procs": vscode_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log_msg(f"Metric query failed: {e}", "ERROR")
        return None

# ============================================================================
# Database Optimization
# ============================================================================

def optimize_orca_db():
    """Run VACUUM on orca.db (optimize storage)."""
    try:
        if not DB_PATH.exists():
            log_msg(f"DB not found: {DB_PATH}", "WARN")
            return False

        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("VACUUM")
        conn.close()
        log_msg("DB VACUUM: OK")
        return True
    except Exception as e:
        log_msg(f"DB VACUUM failed: {e}", "ERROR")
        return False

# ============================================================================
# Cleanup Execution
# ============================================================================

def find_bash():
    """Git Bash 경로. 작업 스케줄러는 사용자 PATH 를 못 받아 shutil.which("bash") 가 None →
    "bash.exe" 로 실행해 [WinError 2] 가 10분마다 났다 (2026-10-13~16 · 453건).
    PATH → git.exe 위치에서 역산 → Program Files 기본 위치 순으로 찾는다 (하드코딩 X · 환경변수 기준)."""
    b = shutil.which("bash")
    if b:
        return b
    cands = []
    g = shutil.which("git")
    if g:
        root = Path(g).resolve().parent.parent  # ...\Git\cmd\git.exe -> ...\Git
        cands += [root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"]
    for env in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            cands += [Path(base) / "Git" / "bin" / "bash.exe", Path(base) / "Programs" / "Git" / "bin" / "bash.exe"]
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def run_cleanup_pollution():
    """Execute cleanup-pollution.sh (exit code 0 expected)."""
    try:
        cleanup_script = PROJECT_ROOT / ".claude" / "scripts" / "cleanup-pollution.sh"

        if not cleanup_script.exists():
            log_msg(f"cleanup-pollution.sh not found: {cleanup_script}", "WARN")
            return False

        bash_exe = find_bash()
        if not bash_exe:
            log_msg("cleanup-pollution.sh skip: bash 없음 (Git for Windows 미설치)", "WARN")
            return False

        # Cross-platform subprocess call
        result = subprocess.run(
            [bash_exe, str(cleanup_script)],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False  # More secure on Windows
        )

        if result.returncode == 0:
            log_msg("cleanup-pollution.sh: OK")
            return True
        else:
            err_text = result.stderr[:200] if result.stderr else "unknown error"
            log_msg(f"cleanup-pollution.sh FAIL: {err_text}", "WARN")
            return False

    except subprocess.TimeoutExpired:
        log_msg("cleanup-pollution.sh timeout (30s)", "WARN")
        return False
    except Exception as e:
        log_msg(f"cleanup-pollution.sh exception: {e}", "ERROR")
        return False

# ============================================================================
# Idle Session Detection
# ============================================================================

def detect_idle_sessions():
    """List recent idle sessions (info only, no killing)."""
    try:
        if not DB_PATH.exists():
            return []

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Query last 10 ended sessions
        cursor.execute("""
            SELECT session_id, ended_at FROM session_summary
            WHERE ended_at IS NOT NULL
            ORDER BY ended_at DESC LIMIT 10
        """)

        results = cursor.fetchall()
        conn.close()

        idle_sessions = []
        for session_id, ended_at in results:
            if ended_at:
                idle_sessions.append(session_id)

        return idle_sessions[:5]

    except Exception as e:
        log_msg(f"Idle session detection failed: {e}", "WARN")
        return []

def reap_stuck_orphans(min_age_hours: float = 1.0) -> int:
    """부모가 죽은 채 멈춘 kit hook·스크립트 python 을 정리한다.

    2026-10-14 실측: 부모 없는 python 65개가 최대 289시간 CPU 0초로 멈춰 있었다
    (approval-gate.py 51 · 옛 check-mojibake 의 python -c 9 · `python --version` 까지 멈춤).
    `--version` 도 멈춘 것 = 원인은 스크립트가 아니라 이 PC 의 python 기동 단계(환경).
    → hook 이 python 을 덜 띄우게 고치고(예방), 그래도 남은 것은 여기서 치운다(정리).
    안전 조건 (셋 다): 부모 프로세스 없음 · min_age_hours 이상 · kit hook/스크립트 흔적
    (명령줄에 /.claude/ 또는 python -c / --version). 서버(run.py 등)·사용자 작업은 대상이 아니다.
    """
    import time as _t
    reaped = 0
    alive = set(psutil.pids())
    for proc in psutil.process_iter(["pid", "ppid", "name", "cmdline", "create_time"]):
        try:
            info = proc.info
            pname = (info["name"] or "").lower()
            # 2026-10-14 확장: python 만이 아니라 Claude 셸이 남긴 bash·grep·find 등도 (09-23 부터 남은 bash 9개 · CPU 43% grep 실측)
            if not (pname.startswith("python") or pname in ("bash.exe", "grep.exe", "find.exe", "sed.exe", "awk.exe", "cat.exe", "sh.exe")):
                continue
            if info["ppid"] in alive:
                continue
            if (_t.time() - (info["create_time"] or _t.time())) < min_age_hours * 3600:
                continue
            cmd = " ".join(info["cmdline"] or []).replace("\\", "/")
            kit_trace = ("/.claude/" in cmd or " -c " in f" {cmd} " or cmd.endswith("--version")
                         or "shell-snapshots" in cmd or "export TEMP=" in cmd)
            if not kit_trace and pname.startswith("python"):
                continue
            if not pname.startswith("python") and not kit_trace:
                # grep·find 등은 명령줄에 흔적이 없을 수 있다 — 부모 없음 + 1시간 + CPU 를 계속 쓰는 것만
                try:
                    if proc.cpu_percent(interval=0.5) < 5:
                        continue
                except Exception:
                    continue
            # 자식부터 정리 (bash 밑에서 도는 grep 등)
            for ch in proc.children(recursive=True):
                try:
                    ch.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            proc.kill()
            reaped += 1
            log_msg(f"stuck orphan python 정리: pid={info['pid']} cmd={cmd[:120]}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if reaped:
        log_msg(f"stuck orphan python {reaped}개 정리", "WARN")
    return reaped


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    log_msg("=== 10-Min Loop START ===")

    # 1. Get system metrics
    metrics = get_system_metrics()
    if not metrics:
        log_msg("Failed to get metrics", "ERROR")
        return 1

    log_msg(
        f"Metrics: RAM {metrics['ram_percent']}% / "
        f"CPU {metrics['cpu_percent']}% / "
        f"claude {metrics['claude_procs']} / "
        f"vscode {metrics['vscode_procs']}"
    )

    # 2. Check thresholds (warn only, no action)
    alerts = []
    if metrics['ram_percent'] >= THRESHOLD_RAM_PERCENT:
        alerts.append(f"RAM HIGH: {metrics['ram_percent']}%")
    # 2026-10-16: 세션 여러 개는 평소 사용이다 — 3개 기준(근거 없음)으로 10분마다 WARN 420건이 쌓였다.
    #   조치할 일이 생기는 것은 메모리가 찰 때뿐이므로 RAM HIGH 와 겹칠 때만 경고한다.
    if metrics['claude_procs'] >= THRESHOLD_PROC_COUNT and metrics['ram_percent'] >= THRESHOLD_RAM_PERCENT:
        alerts.append(f"Claude procs HIGH: {metrics['claude_procs']} (RAM {metrics['ram_percent']}%)")

    if alerts:
        log_msg(" | ".join(alerts), "WARN")

    # 3. Execute cleanup if not dry-run
    if not DRY_RUN:
        # 3a. DB VACUUM
        optimize_orca_db()

        # 3b. cleanup-pollution.sh
        run_cleanup_pollution()

        # 3c. 멈춘 고아 python 정리 (2026-10-14 · 좀비 62개 사례)
        reap_stuck_orphans()

        # 3c-ledger. Ledger → Goal 자동 변환 (2026-10-28 사용자 지시 "자동 연결 필요")
        try:
            ledger_py = PROJECT_ROOT / ".claude" / "scripts" / "request-ledger.py"
            if ledger_py.exists():
                lresult = subprocess.run(
                    [sys.executable, str(ledger_py), "to-goals"],
                    capture_output=True, text=True, timeout=60,
                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
                    cwd=str(PROJECT_ROOT)
                )
                if lresult.returncode == 0 and lresult.stdout:
                    log_msg(f"ledger to-goals: {lresult.stdout.strip()[:200]}")
        except Exception as e:
            log_msg(f"ledger to-goals exception: {e}", "WARN")

        # 3d. Supervisor 자동 진행 (2026-10-27 · P0-2 fix) — goals DB PENDING/PLANNING/RUNNING 상태 자동 전환
        try:
            sup_py = PROJECT_ROOT / ".claude" / "scripts" / "lib" / "supervisor.py"
            if sup_py.exists():
                # 2026-10-27 사용자 지시 "실행 주체 식별" — --trigger scheduler
                result = subprocess.run(
                    [sys.executable, str(sup_py), "advance-all", "--trigger", "scheduler"],
                    capture_output=True, text=True, timeout=120,
                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
                    cwd=str(PROJECT_ROOT)
                )
                if result.returncode == 0:
                    log_msg(f"supervisor advance-all: OK · {result.stdout[:200]}")
                else:
                    log_msg(f"supervisor advance-all FAIL: {result.stderr[:200]}", "WARN")
        except Exception as e:
            log_msg(f"supervisor advance-all exception: {e}", "WARN")

        # 3e. Self-Healing 이벤트 처리 (2026-10-30 Phase 12) — advance-all 이 영속화한 실패 이벤트를
        #     Agent 수정 → runner pytest → Judge → 브랜치 반영. 시간이 길어 advance-all 과 분리.
        try:
            sh_py = PROJECT_ROOT / ".claude" / "scripts" / "lib" / "self_healing.py"
            if sh_py.exists():
                hres = subprocess.run(
                    [sys.executable, str(sh_py), "heal-tick", "--trigger", "scheduler"],
                    capture_output=True, text=True, timeout=1500,
                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
                    cwd=str(PROJECT_ROOT)
                )
                log_msg(f"self-heal tick rc={hres.returncode}: {(hres.stdout or hres.stderr)[:300]}")
        except Exception as e:
            log_msg(f"self-heal tick exception: {e}", "WARN")

        # 3d. Idle session info (list only)
        idle = detect_idle_sessions()
        if idle:
            log_msg(f"Idle sessions (info only): {idle[:3]}")
    else:
        log_msg("DRY-RUN mode: no actions taken")

    # 4. Save state
    state = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "alerts": alerts,
        "dry_run": DRY_RUN
    }

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_msg(f"State save failed: {e}", "ERROR")

    log_msg("=== 10-Min Loop END ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
