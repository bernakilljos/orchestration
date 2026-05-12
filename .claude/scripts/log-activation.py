"""Skill / Hook / Subagent 활성 측정 — orca.db 통합 로그.

5 레이어 ★2 (Skill 측정) + ★3 (Hook trace) 보완.
"""
import sys
import os
import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "orca.db"
LOG_DIR = PROJECT_ROOT / ".claude" / "logs"


def ensure_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        layer TEXT,         -- skill | hook | subagent
        name TEXT,
        trigger_text TEXT,
        result TEXT,        -- success | fail | skip
        duration_ms INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_act_layer ON activations(layer, name);
    CREATE INDEX IF NOT EXISTS idx_act_ts ON activations(ts);
    """)


def log(layer: str, name: str, trigger_text: str = "", result: str = "success", duration_ms: int = 0):
    """활성 기록."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    ensure_table(conn)
    conn.execute(
        "INSERT INTO activations (layer, name, trigger_text, result, duration_ms) VALUES (?, ?, ?, ?, ?)",
        (layer, name, trigger_text[:200], result, duration_ms),
    )
    conn.commit()
    conn.close()

    # 추가: hook trace 로그 (디버깅용)
    if layer == "hook":
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trace = LOG_DIR / "hook-trace.log"
        with open(trace, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {name} → {result} ({duration_ms}ms) | {trigger_text[:100]}\n")


def report(layer: str = None, top_n: int = 10):
    """활성 통계 — 어느 skill/hook 자주 발동, 실패율, 평균 시간."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(str(DB_PATH))
    if layer:
        cur = conn.execute("""
            SELECT name, COUNT(*) as total,
                   SUM(CASE WHEN result='success' THEN 1 ELSE 0 END) as success,
                   AVG(duration_ms) as avg_ms
            FROM activations WHERE layer = ?
            GROUP BY name ORDER BY total DESC LIMIT ?
        """, (layer, top_n))
    else:
        cur = conn.execute("""
            SELECT layer, name, COUNT(*) as total,
                   SUM(CASE WHEN result='success' THEN 1 ELSE 0 END) as success,
                   AVG(duration_ms) as avg_ms
            FROM activations
            GROUP BY layer, name ORDER BY total DESC LIMIT ?
        """, (top_n,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip([d[0] for d in cur.description], r)) for r in rows]


if __name__ == "__main__":
    if "--report" in sys.argv:
        layer = None
        if "--layer" in sys.argv:
            i = sys.argv.index("--layer")
            if i + 1 < len(sys.argv):
                layer = sys.argv[i + 1]
        results = report(layer)
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        sys.exit(0)

    if len(sys.argv) < 3:
        print("usage: log-activation.py <layer> <name> [trigger] [--result success|fail] [--duration N]")
        print("       --report [--layer hook|skill|subagent]")
        sys.exit(2)

    layer = sys.argv[1]
    name = sys.argv[2]
    trigger = sys.argv[3] if len(sys.argv) >= 4 and not sys.argv[3].startswith("--") else ""
    result = "success"
    duration = 0
    for i, a in enumerate(sys.argv):
        if a == "--result" and i + 1 < len(sys.argv):
            result = sys.argv[i + 1]
        if a == "--duration" and i + 1 < len(sys.argv):
            duration = int(sys.argv[i + 1])

    log(layer, name, trigger, result, duration)
    print(json.dumps({"logged": True, "layer": layer, "name": name}, ensure_ascii=False))
