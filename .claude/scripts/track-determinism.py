"""Non-Determinism 추적 — 같은 prompt 의 결과 분산도 측정.

orca.db `determinism` table:
- prompt_hash, ai, temperature, result_hash, ts
- 같은 prompt_hash 의 result_hash 분산도 ↑ = non-deterministic 경고

5 핵심 부품 #5 Observability + 9 함정 #7 보완.
"""
import sys
import os
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "orca.db"


def ensure_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS determinism (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        prompt_hash TEXT,
        prompt_preview TEXT,
        ai TEXT,
        temperature REAL,
        result_hash TEXT,
        result_preview TEXT,
        task_type TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_det_prompt ON determinism(prompt_hash);
    CREATE INDEX IF NOT EXISTS idx_det_ai ON determinism(ai);
    """)


# task_type 별 권장 temperature
RECOMMENDED_TEMP = {
    "code_implementation": 0.0,    # 코드 = 결정론적
    "design_or_complex_reasoning": 0.3,  # 설계 = 약간 창의
    "fast_verify_or_score": 0.0,   # 검증-분류 = 결정론적
    "long_context_or_multimodal": 0.2,
    "creative": 0.7,               # 창작 = 높음
}


def short_hash(s: str, n: int = 12) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:n]


def log(prompt: str, ai: str, result: str = "", temperature: float = None, task_type: str = "unknown"):
    """determinism 기록 + 분산도 분석."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    ensure_table(conn)

    ph = short_hash(prompt)
    rh = short_hash(result) if result else ""

    conn.execute(
        "INSERT INTO determinism (prompt_hash, prompt_preview, ai, temperature, result_hash, result_preview, task_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ph, prompt[:200], ai, temperature, rh, result[:200], task_type),
    )
    conn.commit()

    # 같은 prompt_hash 의 result_hash 분산도
    cur = conn.execute(
        "SELECT result_hash, COUNT(*) FROM determinism WHERE prompt_hash = ? AND result_hash != '' GROUP BY result_hash",
        (ph,),
    )
    distribution = {rh: count for rh, count in cur.fetchall()}
    total = sum(distribution.values())
    unique = len(distribution)

    warnings = []
    if total >= 3 and unique > 1:
        # 같은 prompt 인데 다른 결과 N개 = non-deterministic
        warnings.append(f"[WARN] prompt_hash={ph} : {total}회 실행 중 {unique}개 다른 결과 — non-deterministic")

    # temperature 권장 비교
    rec_temp = RECOMMENDED_TEMP.get(task_type, 0.0)
    if temperature is not None and abs(temperature - rec_temp) > 0.2:
        warnings.append(f"[WARN] {task_type} 권장 temperature={rec_temp}, 실제={temperature} — 분산도 ↑ 위험")

    conn.close()
    return {
        "logged": True,
        "prompt_hash": ph,
        "ai": ai,
        "unique_results": unique,
        "total_runs": total,
        "warnings": warnings,
    }


def report(top_n: int = 10):
    """가장 non-deterministic 한 prompt top N 보고."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute("""
        SELECT prompt_hash, prompt_preview, ai, task_type,
               COUNT(DISTINCT result_hash) as unique_results,
               COUNT(*) as total
        FROM determinism
        WHERE result_hash != ''
        GROUP BY prompt_hash, ai
        HAVING total >= 2
        ORDER BY unique_results DESC, total DESC
        LIMIT ?
    """, (top_n,))
    rows = cur.fetchall()
    conn.close()
    return [{
        "prompt_hash": r[0],
        "prompt_preview": r[1],
        "ai": r[2],
        "task_type": r[3],
        "unique_results": r[4],
        "total_runs": r[5],
        "determinism_score": 1.0 - (r[4] - 1) / max(r[5] - 1, 1),  # 1.0 = 완전 결정론적
    } for r in rows]


if __name__ == "__main__":
    if "--report" in sys.argv:
        results = report()
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(0)

    if len(sys.argv) < 3:
        print("usage: track-determinism.py '<prompt>' '<result>' [--ai claude] [--temp 0.3] [--task-type code_implementation]")
        print("       또는 --report")
        sys.exit(2)

    prompt = sys.argv[1]
    result = sys.argv[2]
    ai = "claude"
    temp = None
    task_type = "unknown"
    for i, a in enumerate(sys.argv):
        if a == "--ai" and i + 1 < len(sys.argv):
            ai = sys.argv[i + 1]
        if a == "--temp" and i + 1 < len(sys.argv):
            temp = float(sys.argv[i + 1])
        if a == "--task-type" and i + 1 < len(sys.argv):
            task_type = sys.argv[i + 1]

    res = log(prompt, ai, result, temp, task_type)
    print(json.dumps(res, ensure_ascii=False, indent=2))
