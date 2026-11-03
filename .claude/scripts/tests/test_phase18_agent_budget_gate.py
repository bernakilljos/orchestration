"""Phase 18 회귀 (2026-11-03 · T3) — 유료 Agent 결제 경계 예산 강제. 실 DB·실 Agent·유료 API 사용 X.

dispatch_agent 가 실제 호출 직전 state_db.agent_budget_reserve 로 검사:
차단기 · 일일 예산 (NULL = 금지) · 호출당 상한 · 동시 실행 · 체인(수정+Judge) 호출 수·합계 · 사용량 UNKNOWN · 실패 정산.
Mock Agent = subprocess.run 대체 (호출 횟수를 센다).
"""
import json
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"
sys.path.insert(0, str(LIB))
import real_repair_chain as rc  # noqa: E402
import repair_sandbox as sb  # noqa: E402
import state_db  # noqa: E402

OK_MEM = {"measured": True, "used_gb": 10.0, "limit_gb": 20.0, "free_gb": 10.0, "percent": 50.0}
POL = {"agent_max_budget_usd": 3.0, "agent_max_parallel": 3, "agent_chain_budget_usd": 5.0,
       "agent_max_calls_per_chain": 3, "agent_daily_budget_usd": None}


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(tmp_path))
    state_db.init_schema()
    monkeypatch.setattr(sb, "commit_memory", lambda: OK_MEM)
    monkeypatch.setattr(sb, "_policy", lambda: dict(POL))
    monkeypatch.setattr("shutil.which", lambda n: "claude")
    path = tmp_path / ".claude" / "state" / "orca.db"
    return path


def _set(db, **kw):
    with sqlite3.connect(str(db)) as c:
        for k, v in kw.items():
            c.execute(f"UPDATE budget SET {k}=? WHERE id=1", (v,))


def _q(db, sql, a=()):
    with sqlite3.connect(str(db)) as c:
        return c.execute(sql, a).fetchall()


class MockAgent:
    """claude -p 대체. cost=None 이면 사용량 UNKNOWN 출력."""
    def __init__(self, cost=0.4, exc=None):
        self.calls, self.cost, self.exc = 0, cost, exc

    def __call__(self, argv, **kw):
        self.calls += 1
        if self.exc:
            raise self.exc
        out = {"session_id": f"s{self.calls}", "result": "{}", "usage": {"input_tokens": 10, "output_tokens": 5}}
        if self.cost is not None:
            out["total_cost_usd"] = self.cost
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(out), stderr="")


def _dispatch(monkeypatch, agent, **kw):
    monkeypatch.setattr(rc.subprocess, "run", agent)
    return rc.dispatch_agent("p", str(ROOT), "haiku", ["Read"], role=kw.pop("role", "fix"), **kw)


# ---------- 호출 0건이어야 하는 경우 ----------

def test_daily_limit_null_blocks_with_zero_calls(db, monkeypatch):
    a = MockAgent()
    r = _dispatch(monkeypatch, a)
    assert r["ok"] is False and r["budget_blocked"] and "미설정" in r["error"] and a.calls == 0
    assert _q(db, "SELECT COUNT(*) FROM agent_budget_reservations")[0][0] == 0


def test_breaker_blocks_with_zero_calls(db, monkeypatch):
    _set(db, daily_limit_usd=10.0, breaker_tripped=1)
    a = MockAgent()
    r = _dispatch(monkeypatch, a)
    assert r["ok"] is False and "차단기" in r["error"] and a.calls == 0


def test_insufficient_daily_budget_blocks(db, monkeypatch):
    _set(db, daily_limit_usd=10.0, today_spent_usd=8.0)
    a = MockAgent()
    r = _dispatch(monkeypatch, a)                          # 8 + 3 > 10
    assert r["ok"] is False and "일일 예산 부족" in r["error"] and a.calls == 0


def test_policy_daily_cap_is_used_when_lower(db, monkeypatch):
    _set(db, daily_limit_usd=100.0)
    monkeypatch.setattr(sb, "_policy", lambda: {**POL, "agent_daily_budget_usd": 2.0})
    a = MockAgent()
    r = _dispatch(monkeypatch, a)                          # min(100, 2) = 2 < 3
    assert r["ok"] is False and a.calls == 0


def test_per_call_cap_violation_blocks(db, monkeypatch):
    _set(db, daily_limit_usd=100.0)
    a = MockAgent()
    r = _dispatch(monkeypatch, a, max_budget_usd=4.0)       # > agent_max_budget_usd 3.0
    assert r["ok"] is False and "호출당 상한" in r["error"] and r["retryable"] is False and a.calls == 0


# ---------- 재시도·체인 ----------

def test_chain_retry_cap(db, monkeypatch):
    _set(db, daily_limit_usd=100.0)
    monkeypatch.setattr(sb, "_policy", lambda: {**POL, "agent_chain_budget_usd": 100.0})
    a = MockAgent(cost=0.4)
    for _ in range(3):
        assert _dispatch(monkeypatch, a, chain_id="c1", max_budget_usd=1.0)["ok"]
    r = _dispatch(monkeypatch, a, chain_id="c1", max_budget_usd=1.0)
    assert r["ok"] is False and "재시도 상한" in r["error"] and a.calls == 3
    assert _dispatch(monkeypatch, a, chain_id="c2", max_budget_usd=1.0)["ok"]   # 다른 체인은 영향 없음


def test_fix_plus_judge_share_chain_budget(db, monkeypatch):
    _set(db, daily_limit_usd=100.0)
    a = MockAgent(cost=None)          # UNKNOWN → 예약액 그대로 체인에 차감
    assert _dispatch(monkeypatch, a, chain_id="g1", max_budget_usd=3.0, role="fix")["budget_status"] == "unknown"
    assert _dispatch(monkeypatch, a, chain_id="g1", max_budget_usd=2.0, role="judge")["ok"]   # 3 + 2 ≤ 5
    r = _dispatch(monkeypatch, a, chain_id="g1", max_budget_usd=0.5, role="judge")
    assert r["ok"] is False and "체인 예산" in r["error"] and a.calls == 2


def test_fix_plus_judge_chain_cap_measured(db, monkeypatch):
    _set(db, daily_limit_usd=100.0)
    a = MockAgent(cost=2.9)
    assert _dispatch(monkeypatch, a, chain_id="g2", max_budget_usd=3.0, role="fix")["ok"]
    assert _dispatch(monkeypatch, a, chain_id="g2", max_budget_usd=2.0, role="judge")["ok"]   # 2.9 + 2.0 ≤ 5
    r = _dispatch(monkeypatch, a, chain_id="g2", max_budget_usd=0.5, role="judge")            # 2.9+2.9+0.5 > 5
    assert r["ok"] is False and "체인 예산" in r["error"] and a.calls == 2


# ---------- 정산 ----------

def test_actual_usage_settled_and_spend_recorded(db, monkeypatch):
    _set(db, daily_limit_usd=5.0)
    a = MockAgent(cost=0.4)
    r = _dispatch(monkeypatch, a, max_budget_usd=3.0)
    assert r["ok"] and r["budget_status"] == "settled"
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("settled", 0.4)]
    assert abs(_q(db, "SELECT today_spent_usd FROM budget")[0][0] - 0.4) < 1e-9
    # 정산 후에는 예약 3.0 이 아니라 실측 0.4 기준 → 0.4 + 3 ≤ 5 이므로 다시 호출 가능
    assert _dispatch(monkeypatch, a, max_budget_usd=3.0)["ok"] and a.calls == 2


def test_unknown_usage_charges_reserved_amount(db, monkeypatch):
    _set(db, daily_limit_usd=5.0)
    a = MockAgent(cost=None)
    r = _dispatch(monkeypatch, a, max_budget_usd=3.0)
    assert r["budget_status"] == "unknown" and r["cost_usd"] is None
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("unknown", 3.0)]
    assert _q(db, "SELECT today_spent_usd FROM budget")[0][0] in (0, 0.0)   # 측정값은 그대로 (추정치를 섞지 않음)
    r2 = _dispatch(monkeypatch, a, max_budget_usd=3.0)                       # 3(UNKNOWN) + 3 > 5
    assert r2["ok"] is False and a.calls == 1


def test_timeout_charges_reserved_amount(db, monkeypatch):
    _set(db, daily_limit_usd=10.0)
    a = MockAgent(exc=subprocess.TimeoutExpired("claude", 1))
    r = _dispatch(monkeypatch, a, max_budget_usd=3.0)
    assert r["ok"] is False and r["budget_status"] == "unknown"
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("unknown", 3.0)]


def test_launch_failure_releases_reservation(db, monkeypatch):
    _set(db, daily_limit_usd=10.0)
    a = MockAgent(exc=OSError("not executable"))
    r = _dispatch(monkeypatch, a, max_budget_usd=3.0)
    assert r["ok"] is False and "launch failed" in r["error"]
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("released", 0.0)]


def test_unclear_failure_keeps_reserved_amount(db, monkeypatch):
    _set(db, daily_limit_usd=10.0)
    a = MockAgent(exc=RuntimeError("pipe broken after request"))   # 요청 도달 여부 불명
    r = _dispatch(monkeypatch, a, max_budget_usd=3.0)
    assert r["ok"] is False and r["budget_status"] == "unknown"
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("unknown", 3.0)]


def test_nonzero_exit_without_usage_is_unknown(db, monkeypatch):
    _set(db, daily_limit_usd=10.0)

    def crashed(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="connection reset")
    monkeypatch.setattr(rc.subprocess, "run", crashed)
    r = rc.dispatch_agent("p", str(ROOT), "haiku", ["Read"], role="judge", max_budget_usd=2.0)
    assert r["ok"] is False and r["budget_status"] == "unknown"
    assert _q(db, "SELECT status, charged_usd FROM agent_budget_reservations") == [("unknown", 2.0)]


def test_memory_deferred_makes_no_reservation(db, monkeypatch):
    _set(db, daily_limit_usd=10.0)
    monkeypatch.setattr(sb, "commit_memory", lambda: {**OK_MEM, "free_gb": 0.1, "percent": 99.5})
    a = MockAgent()
    r = _dispatch(monkeypatch, a)
    assert r["deferred"] and a.calls == 0
    assert not _q(db, "SELECT 1 FROM sqlite_master WHERE name='agent_budget_reservations'") or         _q(db, "SELECT COUNT(*) FROM agent_budget_reservations")[0][0] == 0


# ---------- 동시 실행 ----------

def test_concurrent_reservations_never_double_book(db):
    _set(db, daily_limit_usd=5.0)
    results = []

    def worker():
        results.append(state_db.agent_budget_reserve(3.0, "dag", policy={**POL, "agent_max_parallel": 10}))
    ts = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sum(1 for r in results if r["ok"]) == 1            # 3 + 3 > 5 → 1건만
    assert _q(db, "SELECT COUNT(*) FROM agent_budget_reservations WHERE status='open'")[0][0] == 1


def test_concurrency_slot_limit(db):
    _set(db, daily_limit_usd=100.0)
    pol = {**POL, "agent_max_parallel": 2}
    got = [state_db.agent_budget_reserve(1.0, "dag", policy=pol) for _ in range(3)]
    assert [g["ok"] for g in got] == [True, True, False] and "동시 실행" in got[2]["reason"]
    state_db.agent_budget_settle(got[0]["reservation_id"], 0.1, launched=True)
    assert state_db.agent_budget_reserve(1.0, "dag", policy=pol)["ok"]   # 슬롯 반환 후 다시 가능


def test_db_error_fails_closed(db, monkeypatch):
    monkeypatch.setattr(state_db, "tx", lambda: (_ for _ in ()).throw(sqlite3.OperationalError("locked")))
    r = state_db.agent_budget_reserve(1.0, "fix", policy=POL)
    assert r["ok"] is False and "fail-closed" in r["reason"]


# ---------- 스케줄러 경로: 예산 없으면 sandbox 도 만들지 않음 ----------

def test_heal_tick_without_budget_creates_nothing(db, monkeypatch):
    import self_healing as sh
    monkeypatch.setattr(sh, "DB", db)
    sh._ensure_heal_schema()
    now = int(time.time())
    cfg = {"test_cmd": "pytest", "allow_paths": ["a.py"], "base_ref": "HEAD"}
    with sqlite3.connect(str(db)) as c:
        c.execute("INSERT INTO self_heal_events (goal_id, task_id, config, status, created_at, updated_at) "
                  "VALUES (1, 't', ?, 'pending', ?, ?)", (json.dumps(cfg), now, now))

    def boom(*a, **k):
        raise AssertionError("예산이 없는데 sandbox/Agent 를 시작했다")
    monkeypatch.setattr(sb, "create", boom)
    monkeypatch.setattr(sh, "run_repair", boom)
    out = sh.process_events("scheduler", max_events=1)
    ev = out["events"][0]
    assert ev["status"] == "waiting" and "미설정" in ev["error"]
    status, attempts = _q(db, "SELECT status, attempts FROM self_heal_events")[0]
    assert status == "pending" and attempts == 0                 # 시도 횟수 차감 X · 다음 tick 재시도


def test_repair_chain_passes_chain_id_to_fix_and_judge():
    import inspect
    src = inspect.getsource(rc.agent_repair_chain)
    assert src.count("chain_id=chain") == 2


# ---------- Judge 결합 규칙: Judge 가 거부·모순 판정을 내면 VERIFIED 로 새지 않는다 ----------

@pytest.mark.parametrize("patch,want", [
    ({}, "VERIFIED"),
    ({"satisfies_requirement": False, "recommendation": "REPAIRING"}, "REPAIRING"),
    ({"recommendation": "UNVERIFIED"}, "UNVERIFIED"),
    ({"recommendation": "REPAIRING"}, "REPAIRING"),
    ({"missing_requirements": ["R3 errors hidden"]}, "REPAIRING"),
    ({"scope_adequacy": "too_broad"}, "REPAIRING"),
    ({"recommendation": None}, "UNVERIFIED"),
    ({"confidence": "high"}, "UNVERIFIED"),
    ({"satisfies_requirement": "yes"}, "REPAIRING"),     # 문자열 true 를 승인으로 보지 않음
])
def test_judge_absorb_fail_closed(tmp_path, monkeypatch, patch, want):
    import independent_verifier as iv
    monkeypatch.setattr(iv, "JUDGE_QUEUE", tmp_path)
    (tmp_path / "goal-1.json").write_text(json.dumps({"stat_verdict": {"status": "VERIFIED", "reasons": []}}))
    v = {"satisfies_requirement": True, "missing_requirements": [], "unexpected_side_effects": [],
         "scope_adequacy": "ok", "confidence": 9, "recommendation": "VERIFIED", "reasoning": "x", **patch}
    v = {k: x for k, x in v.items() if x is not None}
    assert iv.judge_absorb(1, json.dumps(v))["final_verdict"]["status"] == want


def test_judge_absorb_parse_failure_not_verified(tmp_path, monkeypatch):
    import independent_verifier as iv
    monkeypatch.setattr(iv, "JUDGE_QUEUE", tmp_path)
    (tmp_path / "goal-1.json").write_text(json.dumps({"stat_verdict": {"status": "VERIFIED"}}))
    r = iv.judge_absorb(1, "not json {")
    assert r["ok"] is False and "final_verdict" not in r
