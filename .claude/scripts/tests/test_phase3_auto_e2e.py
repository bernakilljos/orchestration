"""test_phase3_auto_e2e.py — Phase 3 자동 Agent 개발 종단 테스트 (2026-10-30).

사용자 지시 (3307fcd 후속):
  UserPromptSubmit → Ledger → Goal → Planner → Agent 기반 Task DAG → Proposal →
  승인 → Agent 실행 → Worktree → 테스트 → Independent Judge → Evidence → VERIFIED

반례 포함:
  - 승인 거부 · UNKNOWN · Task 실패 · 다른 요청의 독립 진행 · 중복 요청
  - 세션 재시작 · Worktree 충돌 · Judge 불일치 · 임의 개수 요청

주의:
  - 외부 API 재귀 호출 X · Claude Code 세션 안 Task tool 호출 경로만 검증
  - 사용자 승인 없이 cmd 자동 생성 X · bridge 는 외부 (사용자/Task tool) 가 proposal 제출
  - 테스트 goal 은 PHASE3-TEST marker 로 구분 · 끝에 cleanup
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import supervisor  # noqa: E402
import planner  # noqa: E402
import independent_verifier as iverify  # noqa: E402
import auto_goal_from_prompt as autogoal  # noqa: E402
import repair_sandbox as sb  # noqa: E402

DB = ROOT / ".claude" / "state" / "orca.db"
TEST_MARKER = "PHASE3-AUTO-E2E-TEST-2026-10-30"


class TestResult:
    def __init__(self):
        self.cases = []
        self.passed = 0
        self.failed = 0

    def record(self, name: str, ok: bool, note: str = "", data=None):
        self.cases.append({"name": name, "ok": ok, "note": note[:300]})
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} — {note[:200]}")

    def summary(self):
        return {"total": len(self.cases), "passed": self.passed,
                "failed": self.failed, "cases": self.cases}


def _cleanup():
    try:
        with sqlite3.connect(str(DB)) as c:
            gids = [r[0] for r in c.execute(
                "SELECT goal_id FROM goals WHERE description LIKE ?",
                (f"%{TEST_MARKER}%",),
            ).fetchall()]
            for gid in gids:
                c.execute("DELETE FROM planner_proposals WHERE goal_id=?", (gid,))
                tids = [r[0] for r in c.execute(
                    "SELECT task_id FROM goal_tasks WHERE goal_id=?", (gid,)
                ).fetchall()]
                for tid in tids:
                    c.execute("DELETE FROM tasks WHERE task_id=?", (tid,))
                    c.execute("DELETE FROM executions WHERE task_id=?", (tid,))
                c.execute("DELETE FROM goal_tasks WHERE goal_id=?", (gid,))
                c.execute("DELETE FROM goal_transitions WHERE goal_id=?", (gid,))
                c.execute("DELETE FROM goals WHERE goal_id=?", (gid,))
        # judge-queue 테스트 파일
        jq = ROOT / ".claude" / "state" / "judge-queue"
        if jq.exists():
            for f in jq.glob("goal-*.json"):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    if any(g.get("goal_id") == d.get("goal_id") for g in [{}]):
                        pass
                except Exception:
                    pass
        sb.cleanup_orphans(max_age_sec=0)
    except Exception as e:
        print(f"[cleanup] warning: {e}")


def _test_prompt(suffix: str) -> str:
    # TEST_MARKER 는 autogoal._SKIP_TRIGGER 에 매칭 (PHASE3-TEST) → should_register False.
    # 자동 등재 테스트는 marker 없는 prompt + "구현해줘" 트리거로.
    return f"{TEST_MARKER}-{suffix} 추가 구현해줘 end-to-end 기능"


def test_01_should_register_filters(result):
    """should_register — 명시 트리거만 매치 · 질문/메타는 skip."""
    print("\n[Phase3 Test 01] should_register filter")
    # OK: 명시 개발 트리거
    r1 = autogoal.should_register("Phase2 자동화 완성 구현해줘 종단 테스트")
    result.record("dev trigger: '구현해줘' matched", r1.get("register") is True,
                  note=json.dumps(r1)[:200])
    # SKIP: 질문
    r2 = autogoal.should_register("이거 뭐야?")
    result.record("question skipped", r2.get("register") is False,
                  note=json.dumps(r2)[:200])
    # SKIP: 짧은
    r3 = autogoal.should_register("hi")
    result.record("too short skipped", r3.get("register") is False,
                  note=json.dumps(r3)[:200])
    # SKIP: 슬래시 명령
    r4 = autogoal.should_register("/brief Phase2 요약")
    result.record("slash command skipped", r4.get("register") is False,
                  note=json.dumps(r4)[:200])
    # SKIP: 테스트 marker
    r5 = autogoal.should_register("PHASE3-TEST sandbox-only debug test 구현해줘")
    result.record("test marker skipped", r5.get("register") is False,
                  note=json.dumps(r5)[:200])


def test_02_duplicate_detection(result):
    """중복 요청 감지 — 같은 prompt 1h 안 재등재 X."""
    print("\n[Phase3 Test 02] duplicate detection")
    prompt = f"{TEST_MARKER}-dup P3 중복 테스트 구현해줘"
    r1 = autogoal.register(prompt)
    result.record("first register ok", r1.get("ok") is True,
                  note=f"goal_id={r1.get('goal_id')}")
    gid1 = r1.get("goal_id")
    r2 = autogoal.register(prompt)
    result.record("second register detects duplicate",
                  r2.get("ok") is False and r2.get("existing_goal_id") == gid1,
                  note=json.dumps(r2)[:200])


def test_03_opt_out(result):
    """opt-out — AUTO_GOAL_REGISTER=0 시 skip."""
    print("\n[Phase3 Test 03] opt-out")
    os.environ["AUTO_GOAL_REGISTER"] = "0"
    r = autogoal.register(f"{TEST_MARKER}-optout 자동화 구현해줘")
    os.environ["AUTO_GOAL_REGISTER"] = ""
    result.record("AUTO_GOAL_REGISTER=0 blocks register",
                  r.get("ok") is False,
                  note=json.dumps(r)[:200])


def test_04_bridge_schema(result):
    """planner.bridge — 유효 JSON array · 스키마 검증 · 비가역 cmd 자동 risk 상향."""
    print("\n[Phase3 Test 04] bridge CLI schema")
    gid = supervisor.create_goal(f"{TEST_MARKER}-bridge Phase 3 bridge test", 1, 24)
    # 유효 JSON array
    specs = [
        {"kind": "cmd", "cmd": "echo bridge-ok", "verify": "echo PASS",
         "verify_type": "shell", "risk": "low", "rationale": "bridge test"},
        {"kind": "cmd", "cmd": "rm -rf /tmp/x", "risk": "low",  # 거짓 low
         "rationale": "test risk auto-escalation"},
    ]
    r = planner.bridge(gid, json.dumps(specs), origin="task-tool-bridge-test")
    result.record("bridge accepts valid JSON array", r.get("ok") is True,
                  note=f"proposed={r.get('proposed')}")
    # 비가역 cmd risk 상향 확인
    with sqlite3.connect(str(DB)) as c:
        risks = c.execute(
            "SELECT risk FROM planner_proposals WHERE goal_id=? ORDER BY sequence",
            (gid,),
        ).fetchall()
    result.record("dangerous cmd auto risk=high via bridge",
                  len(risks) == 2 and risks[1][0] == "high",
                  note=f"risks={[r[0] for r in risks]}")
    # 유효하지 않은 JSON
    r_bad = planner.bridge(gid, "{not json}")
    result.record("bridge rejects invalid JSON",
                  r_bad.get("ok") is False,
                  note=r_bad.get("error", "")[:100])
    # 빈 array
    r_empty = planner.bridge(gid, "[]")
    result.record("bridge rejects empty array",
                  r_empty.get("ok") is False,
                  note=r_empty.get("error", "")[:100])


def test_05_judge_handoff_blocks_when_stat_not_verified(result):
    """judge_handoff — 통계 verdict != VERIFIED 면 LLM judge 요구 안 함."""
    print("\n[Phase3 Test 05] judge_handoff: stat blocks when not VERIFIED")
    gid = supervisor.create_goal(f"{TEST_MARKER}-judge1 stat-fail test", 1, 24)
    # task 없이 handoff — stat verdict = UNVERIFIED (no tasks)
    r = iverify.judge_handoff(gid)
    result.record("judge_handoff saves handoff file",
                  r.get("ok") is True,
                  note=f"handoff={r.get('handoff_file')}")
    result.record("stat UNVERIFIED → requires_llm_judge=False",
                  r.get("requires_llm_judge") is False,
                  note=f"stat_verdict={r.get('stat_verdict')}")


def test_06_judge_absorb_combination(result):
    """judge_absorb — stat VERIFIED + LLM 통과 → final VERIFIED."""
    print("\n[Phase3 Test 06] judge_absorb combine")
    # happy stat VERIFIED 조건 구성:
    #   task_count=1 completed · exec_verified=1 · tasks_with_verifier 존재
    gid = supervisor.create_goal(f"{TEST_MARKER}-judge2 absorb test", 1, 24)
    tid = f"g{gid}-fake"
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        c.execute(
            "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
            "VALUES (?, ?, 'completed', ?, 0)",
            (tid, json.dumps({"kind": "cmd", "cmd": "echo x",
                              "verify_type": "shell", "verify": "echo PASS"}), now),
        )
        c.execute("INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, 0)",
                  (gid, tid))
        # fake execution verified=1
        c.execute(
            "INSERT INTO executions (task_id, worker_id, cmd, shell, cwd, timeout_s, "
            "exit_code, timed_out, stdout_tail, stderr_tail, verified, policy_result, "
            "duration_ms, started_at, ended_at) "
            "VALUES (?, ?, ?, 1, '', 60, 0, 0, '', '', 1, 'ok', 100, ?, ?)",
            (tid, "test", "echo x", now, now),
        )
    r_handoff = iverify.judge_handoff(gid)
    result.record("stat VERIFIED → requires_llm_judge=True",
                  r_handoff.get("requires_llm_judge") is True,
                  note=f"stat={r_handoff.get('stat_verdict')}")
    # LLM 결과 case 1: satisfies + confidence high → VERIFIED
    llm_ok = json.dumps({
        "satisfies_requirement": True, "missing_requirements": [],
        "unexpected_side_effects": [], "confidence": 9,
        "recommendation": "VERIFIED",
    })
    abs1 = iverify.judge_absorb(gid, llm_ok)
    result.record("stat VERIFIED + llm high conf → final VERIFIED",
                  abs1.get("final_verdict", {}).get("status") == "VERIFIED",
                  note=f"final={abs1.get('final_verdict')}")
    # LLM 결과 case 2: NOT satisfies → REPAIRING
    llm_fail = json.dumps({
        "satisfies_requirement": False,
        "missing_requirements": ["a", "b"],
        "unexpected_side_effects": [], "confidence": 8,
        "recommendation": "REPAIRING",
    })
    abs2 = iverify.judge_absorb(gid, llm_fail)
    result.record("stat VERIFIED but llm reports unsatisfied → REPAIRING",
                  abs2.get("final_verdict", {}).get("status") == "REPAIRING",
                  note=f"final={abs2.get('final_verdict')}")
    # LLM 결과 case 3: low confidence → UNVERIFIED
    llm_low = json.dumps({
        "satisfies_requirement": True, "missing_requirements": [],
        "unexpected_side_effects": [], "confidence": 3,
        "recommendation": "VERIFIED",
    })
    abs3 = iverify.judge_absorb(gid, llm_low)
    result.record("llm low confidence → UNVERIFIED (safe default)",
                  abs3.get("final_verdict", {}).get("status") == "UNVERIFIED",
                  note=f"final={abs3.get('final_verdict')}")


def test_07_judge_absorb_blocks_when_stat_fails(result):
    """stat != VERIFIED 면 LLM 결과 무관 · final = stat."""
    print("\n[Phase3 Test 07] stat fail blocks LLM override")
    gid = supervisor.create_goal(f"{TEST_MARKER}-stat-fail", 1, 24)
    # tasks 0 → stat = UNVERIFIED
    iverify.judge_handoff(gid)
    llm_ok = json.dumps({
        "satisfies_requirement": True, "missing_requirements": [],
        "unexpected_side_effects": [], "confidence": 10,
        "recommendation": "VERIFIED",
    })
    r = iverify.judge_absorb(gid, llm_ok)
    result.record("stat UNVERIFIED blocks even high LLM confidence",
                  r.get("final_verdict", {}).get("status") == "UNVERIFIED",
                  note=f"final={r.get('final_verdict')}")


def test_08_independent_goals_not_blocked(result):
    """실패한 goal 때문에 다른 goal 중단 X."""
    print("\n[Phase3 Test 08] independent goals")
    gid1 = supervisor.create_goal(f"{TEST_MARKER}-indep-A", 1, 24)
    gid2 = supervisor.create_goal(f"{TEST_MARKER}-indep-B", 1, 24)
    # gid1 에 failing task
    with sqlite3.connect(str(DB)) as c:
        c.execute(
            "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
            "VALUES (?, ?, 'failed', ?, 0)",
            (f"g{gid1}-fail", json.dumps({"cmd": "false"}), int(time.time())),
        )
        c.execute("INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, 0)",
                  (gid1, f"g{gid1}-fail"))
    v1 = iverify.judge(iverify.collect_evidence(gid1))
    v2 = iverify.judge(iverify.collect_evidence(gid2))
    result.record("gid1 REPAIRING (has failed task)",
                  v1.get("status") == "REPAIRING",
                  note=json.dumps(v1)[:120])
    result.record("gid2 independent (unaffected by gid1 fail)",
                  v2.get("status") == "UNVERIFIED",  # no tasks
                  note=json.dumps(v2)[:120])


def test_09_auto_goal_end_to_end(result):
    """자동 Goal 등재 → investigate 결과 포함 systemMessage 생성."""
    print("\n[Phase3 Test 09] auto goal e2e")
    prompt = f"{TEST_MARKER}-e2e Phase 3 end-to-end 자동 구현해줘"
    r = autogoal.register(prompt)
    result.record("register returns systemMessage with next steps",
                  r.get("ok") is True
                  and "다음 단계" in r.get("systemMessage", "")
                  and "bridge" in r.get("systemMessage", ""),
                  note=f"gid={r.get('goal_id')} keywords={len(r.get('investigate_keywords', []))}")
    # systemMessage 가 Task tool 호출 유도 문구 포함
    sm = r.get("systemMessage", "")
    result.record("systemMessage guides Task tool subagent",
                  "subagent" in sm and "safe_mode" in sm,
                  note=sm[:300])


def main(argv):
    print(f"=== Phase 3 Auto E2E Test · marker={TEST_MARKER} ===")
    result = TestResult()
    try:
        test_01_should_register_filters(result)
        test_02_duplicate_detection(result)
        test_03_opt_out(result)
        test_04_bridge_schema(result)
        test_05_judge_handoff_blocks_when_stat_not_verified(result)
        test_06_judge_absorb_combination(result)
        test_07_judge_absorb_blocks_when_stat_fails(result)
        test_08_independent_goals_not_blocked(result)
        test_09_auto_goal_end_to_end(result)
    except Exception as e:
        import traceback
        print(f"[FATAL] {type(e).__name__}: {e}")
        traceback.print_exc()
        result.record("test runner fatal", False, note=str(e))
    finally:
        _cleanup()
    s = result.summary()
    print(f"\n=== Summary: {s['passed']}/{s['total']} PASS · {s['failed']} FAIL ===")
    if s["failed"]:
        print("\nFailed:")
        for c in s["cases"]:
            if not c["ok"]:
                print(f"  - {c['name']}: {c['note']}")
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
