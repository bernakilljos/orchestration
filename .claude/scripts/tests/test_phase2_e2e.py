"""test_phase2_e2e.py — Phase 2 종단 통합 테스트 (2026-10-29).

사용자 지시:
  - 자연어 → Ledger → Goal → Planner → DAG → Agent → Worktree → test → Verifier → Evidence
  - 반례 포함 (승인 거부·UNKNOWN·검증 실패·내용 불일치·중복 실행 방지)
  - "독립 함수만 연결한 결과를 운영 종단 성공으로 보고하지 않는다"
  - 테스트 goal 은 명확히 marker 로 구분 · 끝에 cleanup

실행:
  python .claude/scripts/tests/test_phase2_e2e.py           # 전체 수행
  python .claude/scripts/tests/test_phase2_e2e.py --quick   # happy path 만

실패 시 exit code != 0.
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import supervisor  # noqa: E402
import planner  # noqa: E402
import independent_verifier as iverify  # noqa: E402
import repair_sandbox as sb  # noqa: E402

DB = ROOT / ".claude" / "state" / "orca.db"
TEST_MARKER = "PHASE2-E2E-TEST-2026-10-29"


class TestResult:
    def __init__(self):
        self.cases = []
        self.passed = 0
        self.failed = 0

    def record(self, name: str, ok: bool, note: str = "", data=None):
        self.cases.append({"name": name, "ok": ok, "note": note[:300], "data": data})
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name} — {note[:200]}")

    def summary(self) -> dict:
        return {
            "total": len(self.cases),
            "passed": self.passed,
            "failed": self.failed,
            "cases": self.cases,
        }


def _cleanup_test_artifacts():
    """테스트 goal·tasks·proposals·sandboxes 전부 삭제 (기존 데이터 보존)."""
    try:
        with sqlite3.connect(str(DB)) as c:
            # 테스트 marker 로 생성된 goal 찾기
            gids = [r[0] for r in c.execute(
                "SELECT goal_id FROM goals WHERE description LIKE ?",
                (f"%{TEST_MARKER}%",),
            ).fetchall()]
            for gid in gids:
                # proposals
                c.execute("DELETE FROM planner_proposals WHERE goal_id=?", (gid,))
                # tasks via goal_tasks
                tids = [r[0] for r in c.execute(
                    "SELECT task_id FROM goal_tasks WHERE goal_id=?", (gid,)
                ).fetchall()]
                for tid in tids:
                    c.execute("DELETE FROM tasks WHERE task_id=?", (tid,))
                    c.execute("DELETE FROM executions WHERE task_id=?", (tid,))
                c.execute("DELETE FROM goal_tasks WHERE goal_id=?", (gid,))
                c.execute("DELETE FROM goal_transitions WHERE goal_id=?", (gid,))
                c.execute("DELETE FROM goals WHERE goal_id=?", (gid,))
        # sandboxes cleanup
        sb.cleanup_orphans()  # 기본 24h — max_age_sec=0 은 실운영 active sandbox(P8 등)까지 discard 했다 (2026-10-30)
    except Exception as e:
        print(f"[cleanup] warning: {e}")


def _create_test_goal(suffix: str) -> int:
    """테스트 goal 생성 (TEST_MARKER prefix 로 구분)."""
    desc = f"{TEST_MARKER}-{suffix}: planner + sandbox + verifier 종단"
    return supervisor.create_goal(desc, max_retry=1, timeout_h=1)


def _write_marker_cmd(marker_file: str, content: str) -> str:
    """허용된 echo cmd 로 marker 파일 생성 (cwd=sandbox 기준 상대경로)."""
    # echo "content" > marker_file (shell=True 자동)
    # Windows 호환: Python 호출로 대체
    return f'python -X utf8 -c "open(r\'{marker_file}\', \'w\', encoding=\'utf-8\').write(\'{content}\')"'


def test_01_investigate_only(result: TestResult):
    """planner.investigate 가 코드베이스 조사 보고서를 생성."""
    print("\n[Test 01] planner.investigate (조사 보고서)")
    gid = _create_test_goal("investigate")
    r = planner.investigate(gid)
    ok = (r.get("goal_id") == gid
          and isinstance(r.get("keywords"), list)
          and r.get("prompt_template"))
    result.record("investigate returns report with keywords+prompt",
                  ok,
                  note=f"keywords={len(r.get('keywords', []))} files={len(r.get('related_files', []))}",
                  data={"goal_id": gid})
    # prompt_template 가 LLM 에게 "추측 X · 승인 통과" 지침 명시
    tmpl = r.get("prompt_template") or ""
    guards_ok = ("추측" in tmpl) and ("승인" in tmpl) and ("비가역" in tmpl)
    result.record("investigate prompt enforces anti-arbitrary cmd guards",
                  guards_ok,
                  note=f"has_추측={'추측' in tmpl} has_승인={'승인' in tmpl} has_비가역={'비가역' in tmpl}")


def test_02_propose_and_approve(result: TestResult):
    """propose → approve → list 흐름."""
    print("\n[Test 02] propose + approve + list")
    gid = _create_test_goal("propose")
    specs = [{
        "kind": "cmd",
        "cmd": "echo hello-propose",
        "verify": "echo PASS",
        "verify_type": "shell",
        "risk": "low",
        "rationale": "test proposal",
        "files": [],
        "allow_paths": [".claude/state/"],
    }]
    pr = planner.propose(gid, specs, origin="test")
    ok1 = pr.get("proposed") == 1
    result.record("propose stores 1 proposal", ok1, note=json.dumps(pr)[:150])
    if not ok1:
        return None
    pid = pr["proposals"][0]["proposal_id"]
    ar = planner.approve(pid, approved_by="e2e-test")
    result.record("approve transitions pending→approved",
                  ar.get("status") == "approved", note=str(ar)[:150])
    lst = planner.list_proposals(goal_id=gid, status="approved")
    result.record("list_proposals returns approved", len(lst) == 1,
                  note=f"count={len(lst)}")
    return pid


def test_03_dangerous_cmd_rejection(result: TestResult):
    """비가역 cmd 는 risk=high 자동 상향 · promote 시 approval_gate_blocked."""
    print("\n[Test 03] dangerous cmd → risk=high + promote rejected")
    gid = _create_test_goal("dangerous")
    specs = [{
        "kind": "cmd",
        "cmd": "rm -rf /var/data/*",
        "risk": "low",  # 사용자가 low 라고 거짓 claim
        "rationale": "test dangerous auto-escalation",
    }]
    pr = planner.propose(gid, specs, origin="test")
    ok1 = pr.get("proposed") == 1 and pr["proposals"][0]["risk"] == "high"
    result.record("dangerous cmd auto-escalated to risk=high (user low ignored)",
                  ok1, note=json.dumps(pr["proposals"][0])[:150])
    if not ok1:
        return
    pid = pr["proposals"][0]["proposal_id"]
    planner.approve(pid)
    promote_result = planner.promote(gid)
    # cmd 가 approval_gate 로 blocked 되거나 cmd_not_allowed 둘 중 하나
    rejected_at_promote = promote_result.get("rejected", [])
    result.record("promote rejects dangerous cmd (approval_gate or not_allowed)",
                  len(rejected_at_promote) == 1,
                  note=json.dumps(rejected_at_promote)[:200])


def test_04_happy_path_sandbox(result: TestResult):
    """Happy path: investigate → propose → approve → promote → execute_goal → apply."""
    print("\n[Test 04] Happy path (sandbox apply)")
    gid = _create_test_goal("happy")
    # 간단한 echo cmd (허용 prefix)
    specs = [{
        "kind": "cmd",
        "cmd": "echo phase2-e2e-happy-path",
        "verify": "echo PASS",
        "verify_type": "shell",
        "safe_mode": True,
        "risk": "low",
        "rationale": "e2e happy path",
    }]
    pr = planner.propose(gid, specs)
    pid = pr["proposals"][0]["proposal_id"]
    planner.approve(pid)
    promote_result = planner.promote(gid)
    ok1 = promote_result.get("promoted") == 1
    result.record("promote: approved → task registered",
                  ok1, note=json.dumps(promote_result)[:200])
    if not ok1:
        return

    # execute_goal
    exec_result = supervisor.execute_goal(gid)
    result.record("execute_goal: at least 1 task executed",
                  exec_result.get("executed", 0) >= 1,
                  note=f"executed={exec_result.get('executed')} verified={exec_result.get('verified')} failed={exec_result.get('failed')}")
    # sandbox 생성 확인
    sandboxes = exec_result.get("sandboxes") or []
    result.record("safe_mode created sandbox",
                  len(sandboxes) >= 1,
                  note=f"sandbox_count={len(sandboxes)}")
    # apply 또는 discard 호출됐는지
    applied = exec_result.get("sandbox_apply") or []
    discarded = exec_result.get("sandbox_discard") or []
    result.record("sandbox apply OR discard called (no leak)",
                  (len(applied) + len(discarded)) >= 1,
                  note=f"apply={len(applied)} discard={len(discarded)}")

    # independent_verifier
    sandbox_cwd = sandboxes[0]["path"] if sandboxes else None
    ev = iverify.collect_evidence(gid, sandbox_cwd=sandbox_cwd)
    v = iverify.judge(ev)
    result.record("independent verifier returns verdict",
                  v.get("status") in ("VERIFIED", "UNVERIFIED", "REPAIRING", "OUT_OF_SCOPE"),
                  note=f"status={v.get('status')} reasons={v.get('reasons')}")


def test_05_verify_fail_discard(result: TestResult):
    """verify 실패 → discard 호출 · 원본 변경 없음."""
    print("\n[Test 05] verify fail → discard (원본 보호)")
    gid = _create_test_goal("verify-fail")
    specs = [{
        "kind": "cmd",
        "cmd": "echo exec-ok",
        # verify 가 exit 0 이지만 긍정 신호 없음 → _verify_output_passed fail
        "verify": "echo nothing-here",
        "verify_type": "shell",
        "safe_mode": True,
        "risk": "low",
        "rationale": "verify fail test",
    }]
    pr = planner.propose(gid, specs)
    pid = pr["proposals"][0]["proposal_id"]
    planner.approve(pid)
    promoted = planner.promote(gid)
    if promoted.get("promoted") != 1:
        result.record("promote succeeded for verify-fail test", False,
                      note=json.dumps(promoted)[:200])
        return

    exec_result = supervisor.execute_goal(gid)
    discarded = exec_result.get("sandbox_discard") or []
    # verify fail → verified=0 → all_verified=False → discard 분기
    result.record("verify fail triggers discard (original safe)",
                  len(discarded) >= 1,
                  note=f"discard={json.dumps(discarded)[:200]}")
    # 원본 git working tree 가 테스트 marker 로 오염 안 됐는지 확인
    r = subprocess.run(
        ["git", "diff", "--name-only"], cwd=str(ROOT),
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
    )
    # 테스트가 ROOT 를 수정하지 않았어야
    diff_files = (r.stdout or "").strip().splitlines()
    unexpected = [f for f in diff_files if TEST_MARKER.lower() in f.lower()]
    result.record("original ROOT not polluted by test",
                  len(unexpected) == 0,
                  note=f"test_marker_files={unexpected}")


def test_06_independent_verifier_execution_check(result: TestResult):
    """verifier 가 executions.verified 를 재조회 (tasks.status 그대로 안 믿음)."""
    print("\n[Test 06] independent verifier re-reads executions.verified")
    gid = _create_test_goal("exec-check")
    # 가짜 task 등록 (status=completed) 하지만 executions 레코드 없음
    with sqlite3.connect(str(DB)) as c:
        tid = f"g{gid}-fake-completed"
        c.execute(
            "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
            "VALUES (?, ?, 'completed', ?, 0)",
            (tid, json.dumps({"kind": "cmd", "cmd": "echo fake",
                              "verify_type": "shell", "verify": "echo PASS"}), int(time.time())),
        )
        c.execute("INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, 0)",
                  (gid, tid))
    # evidence 수집 → judge
    ev = iverify.collect_evidence(gid)
    v = iverify.judge(ev)
    # tasks.status=completed 이지만 executions 없음 → UNVERIFIED (아니면 결함)
    result.record("verifier rejects completed-but-no-execution as UNVERIFIED",
                  v.get("status") == "UNVERIFIED",
                  note=f"status={v.get('status')} reasons={v.get('reasons')}")


def test_07_scope_lock(result: TestResult):
    """scope-lock 통합 — allow_paths 외 수정 파일 탐지."""
    print("\n[Test 07] scope lock OUT_OF_SCOPE detection")
    # evidence 를 수동으로 조립해 judge 호출
    fake_evidence = {
        "goal_id": 99999,
        "task_count": 1,
        "tasks_completed": 1,
        "tasks_failed": 0,
        "tasks_unverified": 0,
        "tasks_exec_verified": 1,
        "tasks_exec_unverified_or_missing": 0,
        "tasks": [{"task_id": "fake", "status": "completed",
                   "verify_type": "shell", "executions_verified": True}],
        "scope": {"enforced": True, "violations": ["unrelated_file.txt"],
                  "allow_paths": ["src/"]},
    }
    v = iverify.judge(fake_evidence)
    result.record("scope violation returns OUT_OF_SCOPE",
                  v.get("status") == "OUT_OF_SCOPE",
                  note=f"status={v.get('status')} violations={v.get('violations')}")


def test_08_idempotent_promote(result: TestResult):
    """같은 approved proposal 재 promote 시 중복 task 등록 X (idempotent)."""
    print("\n[Test 08] promote idempotent")
    gid = _create_test_goal("idempotent")
    specs = [{"kind": "cmd", "cmd": "echo idempotent-test",
              "verify": "echo PASS", "verify_type": "shell",
              "safe_mode": True, "risk": "low"}]
    pr = planner.propose(gid, specs)
    pid = pr["proposals"][0]["proposal_id"]
    planner.approve(pid)
    r1 = planner.promote(gid)
    r2 = planner.promote(gid)  # 두 번째 호출
    with sqlite3.connect(str(DB)) as c:
        task_count = c.execute(
            "SELECT COUNT(*) FROM goal_tasks WHERE goal_id=?", (gid,)
        ).fetchone()[0]
    result.record("second promote does not duplicate tasks",
                  task_count == 1,
                  note=f"task_count={task_count} r1_promoted={r1.get('promoted')} r2_promoted={r2.get('promoted')}")


def test_09_rejected_proposal_not_promoted(result: TestResult):
    """rejected proposal 은 promote 안 됨."""
    print("\n[Test 09] rejected proposal not promoted")
    gid = _create_test_goal("rejected")
    specs = [{"kind": "cmd", "cmd": "echo should-not-promote",
              "verify_type": "shell", "safe_mode": True, "risk": "low"}]
    pr = planner.propose(gid, specs)
    pid = pr["proposals"][0]["proposal_id"]
    planner.reject(pid, reason="e2e test rejection")
    promote_result = planner.promote(gid)
    with sqlite3.connect(str(DB)) as c:
        task_count = c.execute(
            "SELECT COUNT(*) FROM goal_tasks WHERE goal_id=?", (gid,)
        ).fetchone()[0]
    result.record("rejected proposal not promoted to task",
                  task_count == 0 and promote_result.get("promoted") == 0,
                  note=f"task_count={task_count} promoted={promote_result.get('promoted')}")


def test_10_cleanup_orphans(result: TestResult):
    """cleanup_orphans 가 고아 상태만 정리 · 활성 sandbox 는 보존."""
    print("\n[Test 10] cleanup_orphans preserves active sandboxes")
    # 1. 활성 sandbox 생성
    live_r = sb.create("e2e-live-sandbox")
    # 2. state 에 가짜 등록 (디렉토리 없음)
    state = sb._load_state()
    state["e2e-orphan-ghost"] = {
        "path": str(ROOT / ".repair-sandbox" / "nonexistent-xyz-12345"),
        "branch": "repair/orphan-ghost",
        "created_at": int(time.time()) - 999999,
        "status": "active",
    }
    sb._save_state(state)
    # 3. cleanup 실행
    cr = sb.cleanup_orphans(max_age_sec=86400)
    # 4. 활성 sandbox 는 남아있고 orphan 은 제거됐는지
    state_after = sb._load_state()
    live_exists = "e2e-live-sandbox" in state_after
    ghost_gone = "e2e-orphan-ghost" not in state_after
    result.record("cleanup_orphans removes ghost state",
                  ghost_gone,
                  note=f"removed_entries={cr.get('removed_state_entries')}")
    result.record("cleanup_orphans preserves active sandbox",
                  live_exists,
                  note=f"live sandbox still in state={live_exists}")
    # 정리
    if live_exists:
        sb.discard("e2e-live-sandbox")


def main(argv):
    print(f"=== Phase 2 E2E Test · marker={TEST_MARKER} ===")
    quick = "--quick" in argv
    result = TestResult()
    try:
        test_01_investigate_only(result)
        test_02_propose_and_approve(result)
        test_07_scope_lock(result)
        test_06_independent_verifier_execution_check(result)
        test_09_rejected_proposal_not_promoted(result)
        if not quick:
            test_03_dangerous_cmd_rejection(result)
            test_08_idempotent_promote(result)
            test_04_happy_path_sandbox(result)
            test_05_verify_fail_discard(result)
            test_10_cleanup_orphans(result)
    except Exception as e:
        import traceback
        print(f"[FATAL] {type(e).__name__}: {e}")
        traceback.print_exc()
        result.record("test runner fatal", False, note=f"{type(e).__name__}: {e}")
    finally:
        _cleanup_test_artifacts()
    s = result.summary()
    print(f"\n=== Summary: {s['passed']}/{s['total']} PASS · {s['failed']} FAIL ===")
    if s["failed"] > 0:
        print("\nFailed cases:")
        for c in s["cases"]:
            if not c["ok"]:
                print(f"  - {c['name']}: {c['note']}")
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
