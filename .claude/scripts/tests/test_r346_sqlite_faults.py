"""R346 P1 장애 실험 — orca.db 정본 연결(state_db.tx · WAL · BEGIN IMMEDIATE · busy_timeout) 의 잠금·중간 쓰기 (격리 사본 · 운영 DB 금지).

① 다른 프로세스가 쓰기 잠금을 쥔 동안 쓰기 → 'database is locked' 없이 기다렸다 성공 (대기 시간 측정)
② 트랜잭션 도중 강제 종료(kill) → 반쪽 기록 0 · integrity_check ok · 잠금 풀려 다음 쓰기 즉시 성공 (복구 시간 측정)
"""
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"

_HOLDER = r"""
import sys, time
sys.path.insert(0, sys.argv[1])
import state_db
with state_db.tx() as c:
    c.execute("CREATE TABLE IF NOT EXISTS fault_t (who TEXT, n INTEGER)")
    for i in range(200):
        c.execute("INSERT INTO fault_t VALUES ('holder', ?)", (i,))
    print("LOCKED", flush=True)
    time.sleep(float(sys.argv[2]))
print("DONE", flush=True)
"""

_WRITER = r"""
import sys, time
sys.path.insert(0, sys.argv[1])
import state_db
t = time.time()
with state_db.tx() as c:
    c.execute("CREATE TABLE IF NOT EXISTS fault_t (who TEXT, n INTEGER)")
    c.execute("INSERT INTO fault_t VALUES ('writer', 1)")
print(f"WROTE {time.time() - t:.2f}", flush=True)
"""


def _env(tmp: Path) -> dict:
    (tmp / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    return {**os.environ, "ORCHESTRATION_ROOT": str(tmp), "PYTHONUTF8": "1"}


def _start_holder(env, hold_sec: float) -> subprocess.Popen:
    p = subprocess.Popen([sys.executable, "-c", _HOLDER, str(LIB), str(hold_sec)], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "LOCKED", p.stderr.read()
    return p


def _db(tmp: Path) -> Path:
    return tmp / ".claude" / "state" / "orca.db"


def test_writer_waits_for_lock_then_succeeds(tmp_path):
    env = _env(tmp_path)
    holder = _start_holder(env, 2.0)
    w = subprocess.run([sys.executable, "-c", _WRITER, str(LIB)], env=env, capture_output=True, text=True, timeout=60)
    holder.communicate(timeout=30)
    assert w.returncode == 0 and "locked" not in w.stderr.lower(), w.stderr
    waited = float(w.stdout.split()[-1])
    assert waited >= 1.0                                                        # 실제로 잠금을 기다렸다
    c = sqlite3.connect(_db(tmp_path))
    assert c.execute("SELECT COUNT(*) FROM fault_t WHERE who='holder'").fetchone()[0] == 200
    assert c.execute("SELECT COUNT(*) FROM fault_t WHERE who='writer'").fetchone()[0] == 1


def test_killed_mid_transaction_leaves_no_partial_rows(tmp_path):
    env = _env(tmp_path)
    holder = _start_holder(env, 60.0)
    holder.kill()                                                               # 커밋 전 강제 종료
    holder.communicate(timeout=30)
    t = time.time()
    w = subprocess.run([sys.executable, "-c", _WRITER, str(LIB)], env=env, capture_output=True, text=True, timeout=60)
    rto = time.time() - t
    assert w.returncode == 0, w.stderr
    c = sqlite3.connect(_db(tmp_path))
    assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert c.execute("SELECT COUNT(*) FROM fault_t WHERE who='holder'").fetchone()[0] == 0   # 반쪽 기록 0
    assert c.execute("SELECT COUNT(*) FROM fault_t WHERE who='writer'").fetchone()[0] == 1
    assert rto < 10, rto                                                         # 잠금이 남지 않음
