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
                pass

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

def run_cleanup_pollution():
    """Execute cleanup-pollution.sh (exit code 0 expected)."""
    try:
        cleanup_script = PROJECT_ROOT / ".claude" / "scripts" / "cleanup-pollution.sh"

        if not cleanup_script.exists():
            log_msg(f"cleanup-pollution.sh not found: {cleanup_script}", "WARN")
            return False

        # Windows compatibility: find bash in PATH
        bash_exe = shutil.which("bash") or "bash.exe"

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
    if metrics['claude_procs'] >= THRESHOLD_PROC_COUNT:
        alerts.append(f"Claude procs HIGH: {metrics['claude_procs']}")

    if alerts:
        log_msg(" | ".join(alerts), "WARN")

    # 3. Execute cleanup if not dry-run
    if not DRY_RUN:
        # 3a. DB VACUUM
        optimize_orca_db()

        # 3b. cleanup-pollution.sh
        run_cleanup_pollution()

        # 3c. Idle session info (list only)
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
