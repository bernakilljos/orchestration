"""R317 실전 REPAIR 5건 0% 원인 재현·수정 검증 (모두 임시 폴더 · 운영 orca.db 무관).

원인: supervisor 가 REPAIR goal 의 RUNNING 판정에 verify-improvement.py 의 없는 인자(--source-ref)를 넘겨
항상 exit 2 → REPAIRING ↔ RUNNING 왕복 → 재시도 상한 FAILED (수리 작업 0회). self-heal 수리 goal 도 같은 판정이 끼어들어
복구 성공을 FAILED 로 덮었다.
"""
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUP = ROOT / ".claude" / "scripts" / "lib" / "supervisor.py"
RT = ROOT / ".claude" / "scripts" / "recurrence-tracker.py"
VI = ROOT / ".claude" / "scripts" / "verify-improvement.py"


def _sup(tmp, monkeypatch):
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    (tmp / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    # 운영과 같게 검증 스크립트를 둔다 (없으면 옛 코드가 판정을 건너뛰어 덮어쓰기 결함이 재현 안 됨)
    (tmp / ".claude" / "scripts" / "verify-improvement.py").write_bytes(VI.read_bytes())
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp))
    sp = importlib.util.spec_from_file_location(f"sup317_{id(tmp)}", SUP)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _rt(tmp, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp), "PYTHONUTF8": "1"}
    env.pop("ORCA_TEST_MODE", None)
    return subprocess.run([sys.executable, "-X", "utf8", str(RT), *args], env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=300)


def _goal(m, gid):
    with sqlite3.connect(str(m.DB)) as c:
        return c.execute("SELECT status, retry_count, failure_reason FROM goals WHERE goal_id=?", (gid,)).fetchone()


def _last_reason(m, gid):
    with sqlite3.connect(str(m.DB)) as c:
        return c.execute("SELECT reason FROM goal_transitions WHERE goal_id=? ORDER BY id DESC LIMIT 1", (gid,)).fetchone()[0]


def test_old_verify_call_always_failed(tmp_path):
    """수정 전 경로 재현: 예전 호출 형태는 어떤 규칙이든 exit 2 (판정이 아니라 사용법 오류)."""
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    r = subprocess.run([sys.executable, str(VI), "--source-ref", "rule:미반영"], env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 2 and "unknown" in r.stderr
    assert '"--source-ref"' not in SUP.read_text(encoding="utf-8")   # 수정 후 판정 본문에 그 호출이 없다 (주석 설명만 남음)


def test_rule_repair_waits_instead_of_burning_retries_then_verifies_on_real_fix(tmp_path, monkeypatch):
    m = _sup(tmp_path, monkeypatch)
    gid = m.create_repair_goal("미반영", "dev", 5, "샘플")
    for _ in range(6):                                   # 예전엔 이 주기 수면 retry 상한 FAILED
        m.advance_all_pending(trigger_source="stop_hook")
    st, retry, fr = _goal(m, gid)
    assert st == "BLOCKED" and retry == 0 and fr is None
    assert "해결 시험 통과 기록 없음" in _last_reason(m, gid)
    # 실제 해결 경로: 근본 원인 확정 → 연결 시험을 지금 실행해 통과 (가짜 VERIFIED 삽입 아님)
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    ev = json.loads(_rt(tmp_path, "record", "미반영", "dev", "반영 안 됐잖아").stdout)["event_id"]
    assert _rt(tmp_path, "root-cause", str(ev), "--cause", "캐시 무효화 누락", "--evidence", "cache.py:42 무효화 호출 없음",
               "--status", "confirmed").returncode == 0
    assert _rt(tmp_path, "fix-result", str(ev), "passed", "--evidence", "cache.py:42 무효화 호출 추가",
               "--test", "t_fix.py::test_ok").returncode == 0
    out = m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, gid)[0] == "VERIFIED", out
    assert "해결 시험 통과" in _last_reason(m, gid)


def test_reopened_fix_does_not_verify(tmp_path, monkeypatch):
    """역방향: 해결 기록이 있어도 재발로 verified=0(REOPENED)·FIX_FAILED 면 통과시키지 않는다."""
    m = _sup(tmp_path, monkeypatch)
    gid = m.create_repair_goal("공통우회개발", "dev", 3)
    m.advance_all_pending()
    with sqlite3.connect(str(m.DB)) as c:
        c.execute("CREATE TABLE IF NOT EXISTS recurrence_improvements (improvement_id INTEGER PRIMARY KEY, rule_id TEXT, "
                  "status TEXT, verified INTEGER)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('공통우회개발','REOPENED',0)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('공통우회개발','VERIFIED',0)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('다른규칙','VERIFIED',1)")
    for _ in range(3):
        m.advance_all_pending()
    assert _goal(m, gid)[:2] == ("BLOCKED", 0)


def test_self_heal_repair_goal_not_hijacked(tmp_path, monkeypatch):
    """self-heal 수리 goal(Agent 수리 중 RUNNING)은 supervisor 가 REPAIRING 으로 바꾸지 않는다 (e43·e52 덮어쓰기 재현)."""
    m = _sup(tmp_path, monkeypatch)
    gid = m.create_goal("Self-Healing: goal #1 복구", max_retry=1, timeout_h=4, workflow_type="REPAIR",
                        source_ref="repair:orig_goal=1")
    m.advance(gid, "PLANNING", "agent repair start", "self-healing")
    m.advance(gid, "RUNNING", "agent repair start", "self-healing")
    for _ in range(3):
        m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, gid)[:2] == ("RUNNING", 0)
    assert m.advance(gid, "VERIFIED", "agent fix · judge", "self-healing")   # 수리 성공 기록이 그대로 들어간다
