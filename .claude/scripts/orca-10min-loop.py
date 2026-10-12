#!/usr/bin/env python3
"""
10-Minute Memory Recovery Loop
자동 메모리·CPU 모니터링·수집·최적화

실행: python orca-10min-loop.py [--dry-run]
로그: .claude/logs/orca-10min-loop.log
상태: .claude/state/last-10min-loop.json
"""

import os
import sys
import json
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
import psutil

# ============================================================================
# Config
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent  # .claude/scripts/../.. → project root
LOG_DIR = PROJECT_ROOT / ".claude" / "logs"
STATE_DIR = PROJECT_ROOT / ".claude" / "state"
DB_PATH = STATE_DIR / "orca.db"
LOG_FILE = LOG_DIR / "orca-10min-loop.log"
STATE_FILE = STATE_DIR / "last-10min-loop.json"

THRESHOLD_RAM_PERCENT = 80  # RAM ≥80% → 알림
THRESHOLD_PROC_COUNT = 3    # claude 프로세스 ≥3 → 알림
IDLE_THRESHOLD_SEC = 600    # 10분 이상 미사용 세션

DRY_RUN = "--dry-run" in sys.argv

# ============================================================================
# Logging
# ============================================================================

def log_msg(msg: str, level: str = "INFO"):
    """로그 append (메모리 dict 아님 · 파일 기반)"""
    ts = datetime.now().isoformat()
    log_line = f"[{ts}] [{level}] {msg}\n"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Log write failed: {e}", file=sys.stderr)
    if level in ["WARN", "ERROR"]:
        print(log_line.rstrip())

# ============================================================================
# Memory Query
# ============================================================================

def get_system_metrics():
    """psutil로 시스템 메트릭 조회 (1초 이내)"""
    try:
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # claude 프로세스 수
        claude_count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if 'claude' in proc.name().lower():
                    claude_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # VS Code 프로세스 수
        vscode_count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if 'code' in proc.name().lower():
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
# DB Optimization
# ============================================================================

def optimize_orca_db():
    """orca.db VACUUM (경량 정리)"""
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
# Cleanup
# ============================================================================

def run_cleanup_pollution():
    """cleanup-pollution.sh 재발동 (조용 · 0 알림)"""
    try:
        cleanup_script = PROJECT_ROOT / ".claude" / "scripts" / "cleanup-pollution.sh"
        if not cleanup_script.exists():
            log_msg(f"cleanup-pollution.sh not found", "WARN")
            return False

        result = subprocess.run(
            ["bash", str(cleanup_script)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            log_msg("cleanup-pollution.sh: OK")
            return True
        else:
            log_msg(f"cleanup-pollution.sh failed: {result.stderr[:200]}", "WARN")
            return False
    except subprocess.TimeoutExpired:
        log_msg("cleanup-pollution.sh timeout", "WARN")
        return False
    except Exception as e:
        log_msg(f"cleanup-pollution.sh error: {e}", "ERROR")
        return False

# ============================================================================
# Session Idle Detection
# ============================================================================

def detect_idle_sessions():
    """idle 세션 리스트업 (강제 종료 X · 보고만)"""
    try:
        if not DB_PATH.exists():
            return []

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 최근 활동 없는 session_id 찾기 (구조 가정: session_summary 테이블)
        cursor.execute("""
            SELECT session_id, ended_at FROM session_summary
            WHERE ended_at IS NOT NULL
            ORDER BY ended_at DESC LIMIT 10
        """)

        results = cursor.fetchall()
        conn.close()

        idle_sessions = []
        for session_id, ended_at in results:
            # ended_at 이후 경과 시간 계산 (간단 버전)
            # (구체적으로는 DB 시간 형식에 따라 다름)
            if ended_at:
                idle_sessions.append(session_id)

        return idle_sessions[:5]  # 최대 5개만
    except Exception as e:
        log_msg(f"Idle session detection failed: {e}", "WARN")
        return []

# ============================================================================
# Main
# ============================================================================

def main():
    log_msg("=== 10-Min Loop START ===")

    # 1. 시스템 메트릭 조회
    metrics = get_system_metrics()
    if not metrics:
        log_msg("Failed to get metrics", "ERROR")
        return 1

    log_msg(f"Metrics: RAM {metrics['ram_percent']}% / CPU {metrics['cpu_percent']}% / "
            f"claude {metrics['claude_procs']} / vscode {metrics['vscode_procs']}")

    # 2. 임계 감지 (알림 X · 로그만)
    alerts = []
    if metrics['ram_percent'] >= THRESHOLD_RAM_PERCENT:
        alerts.append(f"RAM HIGH: {metrics['ram_percent']}%")
    if metrics['claude_procs'] >= THRESHOLD_PROC_COUNT:
        alerts.append(f"Claude procs HIGH: {metrics['claude_procs']}")

    if alerts:
        log_msg(" | ".join(alerts), "WARN")

    # 3. 메모리 확보 액션 (dry-run 존중)
    if not DRY_RUN:
        # 3a. DB VACUUM
        optimize_orca_db()

        # 3b. cleanup-pollution.sh
        run_cleanup_pollution()

        # 3c. idle session 감지 (리스트업만)
        idle = detect_idle_sessions()
        if idle:
            log_msg(f"Idle sessions (info only): {idle[:3]}")
    else:
        log_msg("DRY-RUN mode: no actions taken")

    # 4. 상태 저장 (last-10min-loop.json)
    state = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "alerts": alerts,
        "dry_run": DRY_RUN
    }

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log_msg(f"State save failed: {e}", "ERROR")

    log_msg("=== 10-Min Loop END ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
