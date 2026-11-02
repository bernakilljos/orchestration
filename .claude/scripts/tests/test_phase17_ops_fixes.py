"""Phase 17 회귀 (2026-11-02 · 24h 운영 보고서 결함 4건) — 실 DB·실 ledger·실 Agent·유료 API 사용 X.

1. commit(가상 메모리) 부족 → 신규 sandbox·Agent 시작 보류 (retryable) · 10분 루프는 WinError 1455 로 죽지 않고 단계 실패로 기록
2. 10분 루프 subprocess 출력 utf-8 디코딩 (cp949 UnicodeDecodeError 144회) · 하위 명령 실패를 0 으로 숨기지 않음
3. 사용량 미측정 = cost NULL(UNKNOWN) · 측정된 0 비용은 0 · 예전 0/0/0 행은 DB 수정 없이 집계에서만 미측정
4. approval_required(사용자 승인 대기) 는 Stop 을 막지 않음 · stop_hook_active 무한 차단 해소 · 실제 미완료는 계속 차단
"""
import ast
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"
sys.path.insert(0, str(LIB))
import repair_sandbox as sb  # noqa: E402

LOW = {"measured": True, "used_gb": 19.5, "limit_gb": 19.7, "free_gb": 0.2, "percent": 99.0}
OK = {"measured": True, "used_gb": 10.0, "limit_gb": 20.0, "free_gb": 10.0, "percent": 50.0}
POL = {"min_commit_free_gb": 2, "max_commit_percent": 90}


# ---------- 1. commit 메모리 ----------

def test_commit_memory_measures_real_machine():
    cm = sb.commit_memory()
    if not cm.get("measured"):
        pytest.skip(f"commit 측정 불가 환경: {cm}")
    assert 0 < cm["used_gb"] <= cm["limit_gb"] and 0 <= cm["percent"] <= 100


def test_memory_gate_low_ok_unknown():
    low = sb.memory_gate(POL, LOW)
    assert low and low["ok"] is False and low["retryable"] and low["deferred"] and "commit" in low["reason"]
    assert sb.memory_gate(POL, OK) is None
    assert sb.memory_gate(POL, {"measured": False, "reason": "x"}) is None   # 측정 불가 = 막지 않음


def test_sandbox_create_deferred_on_low_commit(monkeypatch):
    sb.use_test_root()
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)
    gid = f"p17-mem-{time.time_ns()}"
    r = sb.create(gid)
    assert r["ok"] is False and r["retryable"] and r.get("deferred")
    assert not (sb.SANDBOX_ROOT / gid).exists()      # worktree 를 만들지 않았다


def test_agent_dispatch_deferred_without_launch(monkeypatch):
    import real_repair_chain as rc
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)

    def boom(*a, **k):
        raise AssertionError("commit 부족인데 Agent 프로세스를 띄웠다")
    monkeypatch.setattr(rc.subprocess, "run", boom)
    r = rc.dispatch_agent("x", str(ROOT), "haiku", ["Read"], role="p17")
    assert r["ok"] is False and r["deferred"] and r["retryable"]


def test_dag_deferred_is_skipped_not_failed():
    import agent_registry as ar
    deferred = lambda *a, **k: {"ok": False, "deferred": True, "retryable": True, "error": "commit 부족"}
    out = ar.run_dag([{"id": "t1", "needs": ["read"], "prompt": "p"}], str(ROOT), max_parallel=1, dispatch=deferred)
    assert out["results"]["t1"]["status"] == "skipped" and out["results"]["t1"]["deferred"]
    assert out["metrics"]["failed"] == 0 and out["metrics"]["deferred"] == 1


# ---------- 1·2. 10분 루프 ----------

def _load_loop(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("orca_loop_p17", ROOT / ".claude" / "scripts" / "orca-10min-loop.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "LOG_FILE", tmp_path / "loop.log")
    monkeypatch.setattr(m, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(m, "STATE_DIR", tmp_path)
    monkeypatch.setattr(m, "DRY_RUN", False)
    monkeypatch.setattr(m, "optimize_orca_db", lambda: True)
    monkeypatch.setattr(m, "run_cleanup_pollution", lambda: True)
    monkeypatch.setattr(m, "detect_idle_sessions", lambda: [])
    return m


def test_loop_survives_winerror_1455_and_reports_failure(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    calls = []

    def reap():
        raise OSError(22, "페이징 파일이 너무 작습니다", None, 1455)
    monkeypatch.setattr(m, "reap_stuck_orphans", reap)
    monkeypatch.setattr(m.subprocess, "run",
                        lambda argv, **k: calls.append(argv) or subprocess.CompletedProcess(argv, 0, "ok", ""))
    rc = m.main()
    assert rc == 2                                     # 성공(0)으로 숨기지 않음
    assert len(calls) == 3                             # 이후 단계(to-goals·advance-all·heal-tick)는 계속 실행
    st = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert any("reap_stuck_orphans" in s for s in st["step_failures"])
    assert "commit" in st["metrics"]


def test_loop_substep_nonzero_rc_not_masked(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "reap_stuck_orphans", lambda: 0)
    monkeypatch.setattr(m.subprocess, "run",
                        lambda argv, **k: subprocess.CompletedProcess(argv, 3 if "advance-all" in argv else 0, "", "에러 원문"))
    assert m.main() == 2
    log = (tmp_path / "loop.log").read_text(encoding="utf-8")
    assert "advance-all FAIL rc=3" in log and "에러 원문" in log


def test_loop_low_commit_alert(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "reap_stuck_orphans", lambda: 0)
    monkeypatch.setattr(m.subprocess, "run", lambda argv, **k: subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)
    monkeypatch.setattr(sb, "_policy", lambda: POL)
    assert m.main() == 0                               # 경고는 실패가 아님
    st = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert any(a.startswith("COMMIT LOW") for a in st["alerts"])


def test_loop_all_subprocess_calls_decode_utf8():
    tree = ast.parse((ROOT / ".claude" / "scripts" / "orca-10min-loop.py").read_text(encoding="utf-8"))
    runs = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "run"
            and getattr(n.func.value, "id", "") == "subprocess"]
    assert len(runs) == 4
    for n in runs:
        kw = {k.arg: k.value for k in n.keywords}
        assert getattr(kw.get("encoding"), "value", None) == "utf-8", f"line {n.lineno}"


def test_utf8_decode_keeps_korean_bad_bytes_and_rc():
    child = ("import sys;sys.stdout.buffer.write('한글 ✓ '.encode('utf-8')+b'\\xe2\\x28\\xa1');"
             "sys.stderr.buffer.write('실패 원문'.encode('utf-8'));sys.exit(5)")
    r = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True,
                       encoding="utf-8", errors="backslashreplace", timeout=30)
    assert r.returncode == 5 and "한글 ✓" in r.stdout and "\\xe2" in r.stdout and r.stderr == "실패 원문"


# ---------- 3. 비용 관측 ----------

def _tmp_db(tmp_path):
    env = {**os.environ, "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONUTF8": "1"}
    subprocess.run([sys.executable, "-c", f"import sys;sys.path.insert(0,{str(LIB)!r});import state_db;state_db.init_schema()"],
                   env=env, check=True, timeout=60)
    return env, tmp_path / ".claude" / "state" / "orca.db"


def test_usage_unknown_records_null_and_no_spend(tmp_path):
    env, db = _tmp_db(tmp_path)
    out = subprocess.run([sys.executable, str(LIB / "record_call.py"), "--ai", "claude", "--model", "subagent-x",
                          "--usage-unknown", "--latency-ms", "10", "--success", "1"],
                         env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0 and "cost=UNKNOWN" in out.stdout
    with sqlite3.connect(str(db)) as c:
        assert c.execute("SELECT cost_usd FROM metrics").fetchall() == [(None,)]
        assert c.execute("SELECT today_spent_usd FROM budget").fetchone()[0] in (0, 0.0, None)


def test_ops_metrics_measured_vs_unknown(tmp_path, monkeypatch):
    import ops_metrics
    _, db = _tmp_db(tmp_path)
    now = int(time.time())
    with sqlite3.connect(str(db)) as c:
        rows = [("a", "agent", 100, 50, 0.0, now),     # 측정된 0 비용 (토큰 있음) → 0
                ("b", "agent", 200, 0, 0.25, now),     # 측정
                ("c", "agent", 0, 0, None, now),       # UNKNOWN (NULL)
                ("d", "legacy", 0, 0, 0.0, now)]       # 예전 hook 0/0/0 → 미측정 (DB 는 그대로)
        c.executemany("INSERT INTO metrics (task_id, ai, tokens_in, tokens_out, cost_usd, recorded_at, model_id, "
                      "latency_ms, success, cache_hit) VALUES (?,?,?,?,?,?,'m',1,1,0)", rows)
    monkeypatch.setattr(ops_metrics, "DB", db)
    tc = ops_metrics.report(1)["tokens_cost"]
    assert tc["agent"]["cost_usd"] == 0.25 and tc["agent"]["tokens_in"] == 300
    assert tc["agent"]["measured_calls"] == 2 and tc["agent"]["unmeasured_calls"] == 1
    assert tc["legacy"]["cost_usd"] == "UNKNOWN" and tc["legacy"]["unmeasured_calls"] == 1
    with sqlite3.connect(str(db)) as c:          # 기존 0 기록은 수정하지 않았다
        assert c.execute("SELECT cost_usd FROM metrics WHERE task_id='d'").fetchone()[0] == 0.0


# ---------- 4. Stop gate ----------

def _gate(tmp_path, reqs, payload=None):
    st = tmp_path / ".claude" / "state"
    st.mkdir(parents=True, exist_ok=True)
    (st / "request-ledger.json").write_text(json.dumps({"session_id": "s1", "requests": reqs}, ensure_ascii=False),
                                            encoding="utf-8")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(ROOT / ".claude" / "scripts" / "request-ledger.py"), "gate"],
                          input=json.dumps(payload) if payload is not None else "", env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def _r(rid, status):
    return {"id": rid, "desc": f"{rid} desc", "status": status}


def test_gate_approval_required_does_not_block(tmp_path):
    r = _gate(tmp_path, [_r("R1", "completed"), _r("R2", "approval_required")], {"session_id": "s1"})
    assert r.returncode == 0 and "R2" in r.stderr                  # 알리되 막지 않음
    led = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))
    assert led["requests"][1]["status"] == "approval_required"     # 완료 처리하지 않음


def test_gate_still_blocks_real_pending(tmp_path):
    r = _gate(tmp_path, [_r("R1", "pending"), _r("R2", "approval_required")], {"session_id": "s1"})
    assert r.returncode == 2 and "R1" in r.stderr


def test_gate_breaks_stop_hook_active_loop_but_resets_on_progress(tmp_path):
    reqs = [_r("R1", "pending")]
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": False}).returncode == 2
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 2
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 2
    last = _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True})
    assert last.returncode == 0 and "loop" in last.stderr          # 진전 없는 4번째 → 통과
    assert (tmp_path / ".claude/logs/stop-gate-loop.log").exists()
    # 진전(상태 변경)이 있으면 카운터 초기화 → 다시 막는다
    assert _gate(tmp_path, [_r("R1", "implemented")], {"session_id": "s1", "stop_hook_active": True}).returncode == 2


def test_gate_without_stop_hook_active_always_blocks(tmp_path):
    for _ in range(6):
        assert _gate(tmp_path, [_r("R1", "pending")], {"session_id": "s1"}).returncode == 2


def test_six_guards_does_not_rerun_ledger_gate():
    txt = (ROOT / ".claude" / "hooks" / "stop-six-guards.sh").read_text(encoding="utf-8")
    assert "stop-request-ledger-gate.sh" in txt and "</dev/null" in txt
    hook = (ROOT / ".claude" / "hooks" / "stop-request-ledger-gate.sh").read_text(encoding="utf-8")
    assert "gate 2>/dev/null" not in hook
