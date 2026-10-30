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


# ── 디스크 안전 (2026-10-30 C: 1.85GB 사고 재발 방지) ─────────────────────────────
def _sb_test():
    import repair_sandbox as sb
    sb.use_test_root()
    return sb


def test_sparse_estimate_excludes_large_assets():
    sb = _sb_test()
    full = sb._estimate_bytes("HEAD", [])
    sparse = sb._estimate_bytes("HEAD", sb._policy().get("sparse_exclude") or [])
    assert sparse < full and sparse < 300 * 1024 ** 2


def test_reservation_and_total_cap_block_creation(monkeypatch):
    sb = _sb_test()
    import shutil as _sh, os as _os
    free = _sh.disk_usage(str(sb.SANDBOX_ROOT.parent)).free
    with sb._reservation_lock():
        res = sb._live_reservations()
        res["other-process"] = {"bytes": free, "pid": _os.getpid(), "ts": int(time.time())}
        sb._save_reservations(res)
    try:
        r = sb.create(f"resv-{time.time_ns()}")
        assert r["ok"] is False and r["retryable"] and "예약" in r["reason"]
    finally:
        with sb._reservation_lock():
            res = sb._live_reservations(); res.pop("other-process", None); sb._save_reservations(res)
    monkeypatch.setenv("REPAIR_SANDBOX_MAX_TOTAL_GB", "0.001")
    r = sb.create(f"cap-{time.time_ns()}")
    assert r["ok"] is False and r["retryable"] and "상한" in r["reason"]


def test_concurrent_creates_never_overcommit():
    sb = _sb_test()
    import shutil as _sh, os as _os
    est = sb._estimate_bytes("HEAD", sb._policy().get("sparse_exclude") or []) * 1.2
    free = _sh.disk_usage(str(sb.SANDBOX_ROOT.parent)).free
    min_free_gb = (free - 1.5 * est) / 1024 ** 3          # 1개만 들어갈 예산
    code = ("import sys,json;sys.path.insert(0,r'%s');import repair_sandbox as sb;sb.use_test_root();"
            "print(json.dumps(sb.create(sys.argv[1])))") % (ROOT / ".claude" / "scripts" / "lib")
    env = {**_os.environ, "REPAIR_SANDBOX_MIN_FREE_GB": str(min_free_gb)}
    ids = [f"conc-{time.time_ns()}-{i}" for i in range(3)]
    procs = [subprocess.Popen([sys.executable, "-X", "utf8", "-c", code, i], env=env, stdout=subprocess.PIPE,
                              text=True, encoding="utf-8") for i in ids]
    outs = [json.loads(p.communicate(timeout=600)[0].strip().splitlines()[-1]) for p in procs]
    ok = [i for i, o in zip(ids, outs) if o["ok"]]
    assert len(ok) <= 1 and all(o.get("retryable") for o in outs if not o["ok"])
    for i in ok:
        sb.discard(i, force=True)


def test_lifecycle_protects_active_and_retained(monkeypatch):
    sb = _sb_test()
    a, k, v = (f"life-{x}-{time.time_ns()}" for x in ("active", "kept", "verified"))
    for i in (a, k, v):
        assert sb.create(i)["ok"]
    st = sb._load_state()
    old = int(time.time()) - 10 ** 6
    st[a]["created_at"] = old
    st[k].update(created_at=old, status="applied", applied_at=old, preserve=True)
    st[v].update(created_at=old, status="applied", applied_at=old)
    sb._save_state(st)
    out = sb.cleanup_orphans(max_age_sec=86400)
    st = sb._load_state()
    assert (sb.SANDBOX_ROOT / a).exists() and a in [x["goal_id"] for x in out["stale_active_retained"]]
    assert (sb.SANDBOX_ROOT / k).exists() and sb.lifecycle(st[k]) == "RETAINED"
    assert not (sb.SANDBOX_ROOT / v).exists() and sb.lifecycle(st[v]) == "REMOVED"
    assert subprocess.run(["git", "rev-parse", "--verify", "-q", f"refs/heads/repair/{v}"],
                          capture_output=True).returncode == 0          # branch 는 유지
    # 운영 root 처럼 동작할 때 출처 불명 폴더는 보고만
    stray = sb.SANDBOX_ROOT / f"stray-{time.time_ns()}"; stray.mkdir()
    monkeypatch.setattr(sb, "IS_OPERATIONAL_ROOT", True)
    out = sb.cleanup_orphans(max_age_sec=86400)
    assert str(stray) in out["orphan_dirs_reported"] and stray.exists()
    monkeypatch.setattr(sb, "IS_OPERATIONAL_ROOT", False)
    stray.rmdir()
    for i in (a, k, v):        # 테스트가 만든 branch 는 테스트가 정리 (v 는 checkout 만 제거된 상태)
        sb.discard(i, force=True)


def test_dead_process_reservation_is_released():
    sb = _sb_test()
    dead = subprocess.Popen([sys.executable, "-c", "pass"]); dead.wait()
    with sb._reservation_lock():
        res = sb._live_reservations()
        res["crashed"] = {"bytes": 10 ** 15, "pid": dead.pid, "ts": int(time.time())}
        sb._save_reservations(res)
    assert "crashed" not in sb._live_reservations()
    sid = f"after-crash-{time.time_ns()}"
    assert sb.create(sid)["ok"]
    sb.discard(sid, force=True)


# ── Multi-Agent DAG (스텁 Agent · 비용 0) ───────────────────────────────────────
def _dag_env(tmp_path):
    import agent_registry as ar
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    calls = []

    def fake(prompt, cwd, model, tools, role="", **kw):
        calls.append((role, time.time()))
        time.sleep(0.2)
        node = role.split(":", 1)[1]
        if node == "fail":
            return {"ok": False, "invocation": "fake"}
        out = {"spawn": '{"followups":[{"id":"fixB","needs":["read","edit"],"allow_paths":["b.py"],"prompt":"fix b"},'
                        '{"id":"evil","needs":["read","edit"],"allow_paths":["secret.py"],"prompt":"x"}]}'}.get(node, "{}")
        return {"ok": True, "invocation": "fake", "agent_session_id": f"fake-{node}", "result": out, "cost_usd": 0.01}
    return ar, fake, calls


def test_dag_conflicts_cap_spawn_and_isolation(tmp_path):
    ar, fake, calls = _dag_env(tmp_path)
    T = lambda i, **k: {"id": i, "needs": ["read", "edit"], "skills": ["python"], "prompt": i, **k}
    tasks = [T("a1", allow_paths=["a.py"]), T("a2", allow_paths=["a.py"]), T("b0", allow_paths=["c.py"]),
             {"id": "spawn", "needs": ["read"], "skills": ["review"], "prompt": "r", "depends_on": ["a1", "a2"],
              "may_spawn": True, "spawn_allow_paths": ["b.py"]},
             {"id": "fail", "needs": ["read"], "prompt": "f"},
             {"id": "after_fail", "needs": ["read"], "prompt": "x", "depends_on": ["fail"]},
             {"id": "ghost_dep", "needs": ["read"], "prompt": "x", "depends_on": ["nope"]}]
    r = ar.run_dag(tasks, str(tmp_path), max_parallel=3, dispatch=fake)
    waves = r["waves"]
    assert not any({"a1", "a2"} <= set(w) for w in waves)              # 같은 파일 → 다른 wave
    assert any({"a1", "b0"} <= set(w) for w in waves)                   # 다른 파일 → 병렬
    assert all(len(w) <= 3 for w in waves)
    res = r["results"]
    assert res["spawn"]["spawned"] == ["spawn.fixB"] and res["spawn.fixB"]["status"] == "ok"
    assert any("edit without permitted paths" in x for x in res["spawn"]["spawn_rejected"])
    assert res["fail"]["status"] == "failed" and res["after_fail"]["status"] == "skipped"
    assert res["ghost_dep"]["status"] == "skipped" and res["a1"]["status"] == "ok"
    m = r["metrics"]
    assert m["failed"] == 1 and m["skipped"] == 2 and m["cost_usd"] > 0 and m["max_wave"] <= 3
    r1 = ar.run_dag([T("x", allow_paths=["x.py"]), T("y", allow_paths=["y.py"])], str(tmp_path),
                    max_parallel=1, dispatch=fake)
    assert r1["waves"] == [["x"], ["y"]]                                 # 병렬 상한 1


def test_dag_records_tasks_and_metrics(tmp_path):
    ar, fake, _ = _dag_env(tmp_path)
    gid = _goal({"kind": "cmd", "cmd": "x"})
    ar.run_dag([{"id": "n1", "needs": ["read"], "prompt": "p"}], str(tmp_path), dispatch=fake, goal_id=gid)
    with sqlite3.connect(str(DB)) as c:
        assert c.execute("SELECT status FROM tasks WHERE task_id=?", (f"g{gid}-dag-n1",)).fetchone()[0] == "completed"
        m = json.loads(c.execute("SELECT metrics FROM agent_dag_runs WHERE goal_id=?", (gid,)).fetchone()[0])
        assert m["ok"] == 1 and m["success_rate"] == 1.0
        c.execute("DELETE FROM agent_dag_runs WHERE goal_id=?", (gid,))


# ── Phase 15: 관측성 · Platform API · 자원 정책 ───────────────────────────────
def test_ops_metrics_unknown_not_zero(tmp_path, monkeypatch):
    import ops_metrics as om
    monkeypatch.setattr(om, "LOOP_LOG", tmp_path / "missing.log")
    assert om.scheduler(0)["status"] == "UNKNOWN"
    r = om.report(0.0001)                              # 거의 빈 기간 → 측정 없음
    assert r["self_heal"]["success_rate"] == "UNKNOWN"
    assert r["goals"]["repair_success_rate"] == "UNKNOWN"


def test_platform_api_safety_contract():
    import platform_api as api
    assert api.decide("candidate", 1, "approve", "claude-agent")["ok"] is False
    assert api.decide("candidate", 1, "approve", "self-healing")["ok"] is False
    assert api.decide("merge", 1, "approve", "human")["ok"] is False
    assert api.decide("task", "x", "deploy", "human")["ok"] is False
    r = api.register_goal(f"{MARK} api goal", source=MARK)
    gid = r["goal_id"]
    with sqlite3.connect(str(DB)) as c:
        c.execute("UPDATE goals SET source_ref=? WHERE goal_id=?", (MARK, gid))       # 정리 대상 표시
        assert c.execute("SELECT status FROM goals WHERE goal_id=?", (gid,)).fetchone()[0] == "PENDING"
        assert c.execute("SELECT COUNT(*) FROM goal_tasks WHERE goal_id=?", (gid,)).fetchone()[0] == 0
    assert api.goal_status(gid)["ok"] and api.evidence(gid)["executions"] == []


def test_resource_policy_is_single_source(monkeypatch):
    import repair_sandbox as sb, agent_registry as ar, real_repair_chain as rc
    pol = sb._policy()
    for k in ("agent_max_parallel", "agent_max_budget_usd", "heal_max_events_per_tick", "min_free_gb", "max_total_active_gb"):
        assert k in pol
    seen = {}
    monkeypatch.setattr(sb, "_policy", lambda: {**pol, "agent_max_parallel": 1})
    r = ar.run_dag([{"id": "p", "needs": ["read"], "prompt": "x"}, {"id": "q", "needs": ["read"], "prompt": "y"}],
                   str(ROOT), dispatch=lambda *a, **k: {"ok": True, "result": "{}"})
    assert r["waves"] == [["p"], ["q"]]                # 정책값 1 → 병렬 1


def test_policy_ignores_unrelated_root_changes(tmp_path):
    import real_repair_chain as rc
    sbx = tmp_path / "sbx"; sbx.mkdir()
    subprocess.run(["git", "init", "-q", str(sbx)], check=True)
    (sbx / "a.py").write_text("x=1\n"); (sbx / "t.py").write_text("t\n")
    subprocess.run(["git", "-C", str(sbx), "add", "."], check=True)
    subprocess.run(["git", "-C", str(sbx), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "b"], check=True)
    (sbx / "a.py").write_text("x=2\n")
    before = " M some/unrelated.log\n"                      # ROOT 의 무관한 변경은 판정에 영향 X
    r = rc.policy_check(str(sbx), ["a.py"], ["t.py"], before)
    assert r["ok"], r
    (sbx / "t.py").write_text("hacked\n")
    assert "protected_modified" in rc.policy_check(str(sbx), ["a.py"], ["t.py"], before)["issues"]
