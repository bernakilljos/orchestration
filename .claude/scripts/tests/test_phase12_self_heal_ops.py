"""Phase 12 회귀: 무인 Self-Healing 운영 연결의 상태 무결성 (Agent 호출 없음 · 빠름).

- 백그라운드 알림이 Ledger 요청으로 등록되지 않음 (R112~R116 재발 방지)
- opt-in task 만 이벤트 생성 · goal 당 활성 이벤트 1건 (멱등)
- claim 원자성 (두 워커 중 하나만) · lease 만료 시 복원 + 죽은 시도의 repair goal FAILED 처리
- 이벤트 진행 중인 REPAIRING goal 은 supervisor 단순 재시도 대상 아님
"""
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
import self_healing as sh  # noqa: E402
import supervisor  # noqa: E402

DB = ROOT / ".claude" / "state" / "orca.db"
MARK = "P12-OPS-TEST"


def _goal(spec, status="REPAIRING"):
    gid = supervisor.create_goal(f"{MARK} {time.time_ns()}", 1, 4, source_ref=f"{MARK}")
    tid = f"g{gid}-{MARK}"
    with sqlite3.connect(str(DB)) as c:
        c.execute("INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) VALUES (?,?,?,?,0)",
                  (tid, json.dumps(spec), "failed", int(time.time())))
        c.execute("INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?,?,0)", (gid, tid))
        c.execute("UPDATE goals SET status=? WHERE goal_id=?", (status, gid))
    return gid


def _cleanup():
    with sqlite3.connect(str(DB)) as c:
        gids = [r[0] for r in c.execute("SELECT goal_id FROM goals WHERE source_ref=? OR source_ref LIKE ?",
                                        (MARK, f"repair:orig_goal=%:{MARK}"))]
        for gid in gids:
            gids += [r[0] for r in c.execute("SELECT goal_id FROM goals WHERE source_ref LIKE ?",
                                             (f"repair:orig_goal={gid}%",))]
        for gid in set(gids):
            for (tid,) in c.execute("SELECT task_id FROM goal_tasks WHERE goal_id=?", (gid,)).fetchall():
                c.execute("DELETE FROM tasks WHERE task_id=?", (tid,))
            c.execute("DELETE FROM goal_tasks WHERE goal_id=?", (gid,))
            c.execute("DELETE FROM goal_transitions WHERE goal_id=?", (gid,))
            c.execute("DELETE FROM self_heal_events WHERE goal_id=?", (gid,))
            c.execute("DELETE FROM goals WHERE goal_id=?", (gid,))


HEAL = {"test_cmd": "python -m pytest x -q", "allow_paths": ["x/a.py"]}


def setup_module(_):
    sh._ensure_heal_schema()
    _cleanup()


def teardown_module(_):
    _cleanup()


def test_notification_not_registered(tmp_path):
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    hook = ROOT / ".claude" / "hooks" / "prompt" / "ledger_auto_register.py"
    env = {**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    for prompt in ("<task-notification>\n<summary>Run regression tests completed</summary>\n</task-notification>",
                   "Self-Healing 테스트 추가해줘"):
        subprocess.run([sys.executable, "-X", "utf8", str(hook)], input=json.dumps({"prompt": prompt, "session_id": "t"}),
                       text=True, encoding="utf-8", env=env, capture_output=True, check=True)
    reqs = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"]
    assert [r["desc"][:14] for r in reqs] == ["Self-Healing 테"]


def test_enqueue_only_opt_in_and_idempotent():
    plain = _goal({"kind": "cmd", "cmd": "x"})
    opted = _goal({"kind": "cmd", "cmd": "x", "self_heal": HEAL})
    assert sh.enqueue_failure_event(plain)["enqueued"] is False
    first = sh.enqueue_failure_event(opted)
    assert first["enqueued"] is True
    assert sh.enqueue_failure_event(opted)["enqueued"] is False
    assert sh.has_active_event(opted) and not sh.has_active_event(plain)


def test_claim_is_atomic_and_stale_lease_recovers():
    gid = _goal({"kind": "cmd", "cmd": "x", "self_heal": HEAL})
    eid = sh.enqueue_failure_event(gid)["event_id"]
    a = sh._claim_event("w1", lease_s=1800, event_id=eid)   # 운영 이벤트는 건드리지 않는다
    b = sh._claim_event("w2", lease_s=1800, event_id=eid)
    assert a and a["event_id"] == eid and b is None
    # 죽은 시도가 남긴 repair goal
    rg = supervisor.create_goal(f"{MARK} repair", 1, 4, source_ref=f"repair:orig_goal={gid}")
    supervisor.advance(rg, "PLANNING", "t"); supervisor.advance(rg, "RUNNING", "t")
    with sqlite3.connect(str(DB)) as c:
        c.execute("UPDATE self_heal_events SET claimed_at=claimed_at-100 WHERE event_id=?", (eid,))
    again = sh._claim_event("w3", lease_s=10, event_id=eid)
    assert again and again["recovered_from"] == "claimed" and again["attempts"] == 2
    assert sh.close_stale_repair_goals(gid, "w3") == [rg]
    with sqlite3.connect(str(DB)) as c:
        assert c.execute("SELECT status FROM goals WHERE goal_id=?", (rg,)).fetchone()[0] == "FAILED"


def test_supervisor_skips_repairing_goal_with_active_event():
    gid = _goal({"kind": "cmd", "cmd": "x", "self_heal": HEAL})
    sh.enqueue_failure_event(gid)
    res = supervisor.advance_all_pending(dry_run=True)
    assert {"goal_id": gid, "action": "skip(self_heal_event_active)"} in res["details"]


def test_discovery_rejects_unsourced_and_requires_approval(tmp_path):
    import tech_discovery as td
    (tmp_path / "requirements.txt").write_text("somepkg>=1.0\n", encoding="utf-8")
    reply = json.dumps({"findings": [
        {"domain": "backend", "technology": "somepkg", "latest_version": "2.0", "source_url": "https://example.org/rel",
         "checked_at": "2026-10-30"},
        {"domain": "backend", "technology": "nosource", "latest_version": "9"}],
        "gaps": [{"domain": "backend", "technology": "somepkg", "as_is": "1.0", "to_be": "2.0", "description": "d",
                  "priority": "high", "evidence_urls": ["https://example.org/rel"]},
                 {"domain": "backend", "technology": "x", "as_is": "1", "to_be": "2", "description": "d",
                  "evidence_urls": ["https://unverified.example/"]}]})
    fake = lambda *a, **k: {"ok": True, "invocation": "fake", "result": reply, "agent_session_id": "fake"}
    r = td.run_discovery(str(tmp_path), dispatch=fake)
    assert [e["technology"] for e in r["evidence"]] == ["somepkg"]
    assert len(r["candidates"]) == 1 and len(r["rejected"]) == 2
    cid = r["candidates"][0]["candidate_id"]
    with sqlite3.connect(str(DB)) as c:
        assert c.execute("SELECT status, goal_id FROM tech_candidates WHERE candidate_id=?", (cid,)).fetchone() == ("proposed", None)
        assert c.execute("SELECT COUNT(*) FROM goals WHERE source_ref=?", (f"discovery:{cid}",)).fetchone()[0] == 0
    a = td.approve_candidate(cid, "pytest")
    assert a["ok"] and td.approve_candidate(cid, "pytest")["ok"] is False
    with sqlite3.connect(str(DB)) as c:   # 테스트 산출물 정리
        c.execute("DELETE FROM goal_transitions WHERE goal_id=?", (a["goal_id"],))
        c.execute("DELETE FROM goals WHERE goal_id=?", (a["goal_id"],))
        c.execute("DELETE FROM tech_candidates WHERE run_id=?", (r["run_id"],))
        c.execute("DELETE FROM tech_gaps WHERE project_path=?", (str(tmp_path.resolve()),))
        c.execute("DELETE FROM tech_evidence WHERE source_url='https://example.org/rel'")
        c.execute("DELETE FROM tech_discovery_runs WHERE run_id=?", (r["run_id"],))
