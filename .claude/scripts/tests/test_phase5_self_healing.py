"""test_phase5_self_healing.py — Self-Healing 실 run 종단 테스트 (2026-10-30).

사용자 지시 (b03dbf8 후속 · "scaffold → 실제 자동복구 실증"):
  실패 감지 → 로그 수집 → 분석 → 수정 Proposal → 승인 → sandbox 수정 → 재테스트 →
  독립 검증 → 성공 시 안전 반영 · 실패 시 롤백

안전 원칙:
  - 격리 테스트 goal (PHASE5-TEST marker · 끝에 cleanup)
  - 실제 git 저장소 수정 X (sandbox 격리만)
  - 특정 오류 하드코딩 X (범용 패턴)
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
import independent_verifier as iv  # noqa: E402
import self_healing as sh  # noqa: E402
import repair_sandbox as sb  # noqa: E402

DB = ROOT / ".claude" / "state" / "orca.db"
MARKER = "PHASE5-TEST-2026-10-30"


class R:
    def __init__(self):
        self.cases = []; self.passed = 0; self.failed = 0
    def rec(self, name, ok, note="", data=None):
        self.cases.append({"name": name, "ok": ok, "note": note[:300]})
        if ok: self.passed += 1
        else: self.failed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} — {note[:200]}")
    def sum(self):
        return {"total": len(self.cases), "passed": self.passed, "failed": self.failed, "cases": self.cases}


def _cleanup():
    try:
        with sqlite3.connect(str(DB)) as c:
            gids = [r[0] for r in c.execute(
                "SELECT goal_id FROM goals WHERE description LIKE ? OR source_ref LIKE ?",
                (f"%{MARKER}%", f"repair:orig_goal=%:test={MARKER}%"),
            ).fetchall()]
            # repair goal 도 cleanup (orig_goal 참조)
            for gid in list(gids):
                rep_rows = c.execute(
                    "SELECT goal_id FROM goals WHERE source_ref LIKE ?",
                    (f"repair:orig_goal={gid}%",),
                ).fetchall()
                gids.extend(r[0] for r in rep_rows)
            for gid in set(gids):
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
        sb.cleanup_orphans(max_age_sec=0)
    except Exception as e:
        print(f"[cleanup] {e}")


def _create_failed_goal(suffix: str, failing_cmd: str) -> int:
    """실패 goal 생성: 승인된 proposal → execute → 실패 execution 기록."""
    desc = f"{MARKER}-{suffix}"
    gid = supervisor.create_goal(desc, 1, 24)
    # 직접 tasks + executions 등재 (planner bridge/promote 우회 — 실패 재현 목적)
    tid = f"g{gid}-fail"
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        c.execute(
            "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
            "VALUES (?, ?, 'failed', ?, 0)",
            (tid, json.dumps({"kind": "cmd", "cmd": failing_cmd,
                              "verify_type": "shell"}), now),
        )
        c.execute("INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, 0)",
                  (gid, tid))
        # 실패 execution (ModuleNotFoundError 시뮬레이션)
        c.execute(
            "INSERT INTO executions (task_id, worker_id, cmd, shell, cwd, timeout_s, "
            "exit_code, timed_out, stdout_tail, stderr_tail, verified, policy_result, "
            "duration_ms, started_at, ended_at) "
            "VALUES (?, 'test-sim', ?, 1, '', 60, 1, 0, '', ?, 0, 'ok', 100, ?, ?)",
            (tid, failing_cmd,
             "ModuleNotFoundError: No module named 'nonexistent_pkg_xyz'",
             now, now),
        )
    return gid


def test_01_analyze_failure(r):
    """analyze_failure — 실패 execution 수집 + 13 패턴 어휘 매칭 hint."""
    print("\n[P5 Test 01] analyze_failure")
    gid = _create_failed_goal("analyze", "python -c 'import nonexistent_pkg_xyz'")
    a = sh.analyze_failure(goal_id=gid)
    r.rec("analyze returns failure_hints with ModuleNotFound",
          any(h.get("kind") == "missing_module" for h in a.get("failure_hints", [])),
          note=f"hints={a.get('failure_hints')}")
    r.rec("analyze includes repair_prompt",
          bool(a.get("repair_prompt")) and "repair" in a.get("repair_prompt", "").lower(),
          note=f"prompt_len={len(a.get('repair_prompt', ''))}")
    r.rec("failed_executions captured",
          len(a.get("failed_executions") or []) >= 1,
          note=f"n={len(a.get('failed_executions') or [])}")


def test_02_create_repair_goal(r):
    print("\n[P5 Test 02] create_repair_goal")
    orig = _create_failed_goal("create-repair", "false")
    rg = sh.create_repair_goal(orig, f"test repair for {orig}")
    r.rec("repair goal created",
          rg.get("ok") and rg.get("repair_goal_id") != orig,
          note=f"orig={orig} repair={rg.get('repair_goal_id')}")
    # workflow_type=REPAIR 확인
    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT workflow_type, source_ref FROM goals WHERE goal_id=?",
            (rg.get("repair_goal_id"),),
        ).fetchone()
    r.rec("repair goal has workflow_type=REPAIR",
          row and row[0] == "REPAIR",
          note=f"wt={row[0] if row else None} src={row[1] if row else None}")


def test_03_run_repair_without_specs(r):
    """repair_specs 미제공 시 Task tool 호출 유도 systemMessage 반환."""
    print("\n[P5 Test 03] run_repair (no specs → pending task_tool)")
    orig = _create_failed_goal("run-nospec", "false")
    rr = sh.run_repair(orig)
    r.rec("run_repair without specs halts at pending_task_tool",
          rr.get("ok") and rr.get("stage_completed") == "create_repair",
          note=f"stage={rr.get('stage_completed')}")
    chain = rr.get("chain", {}).get("stages") or []
    propose_stage = next((s for s in chain if s.get("stage") == "propose"), {})
    r.rec("chain includes propose stage with pending_task_tool",
          propose_stage.get("status") == "pending_task_tool",
          note=f"stage={propose_stage}")
    r.rec("next_action guides Task tool subagent",
          "Task tool" in (rr.get("next_action") or "")
          and "bridge" in (rr.get("next_action") or ""),
          note=rr.get("next_action", "")[:200])


def test_04_run_repair_with_specs_auto_approve(r):
    """repair_specs 제공 + auto_approve → bridge → approve → promote → execute → judge."""
    print("\n[P5 Test 04] run_repair with specs + auto_approve → full chain")
    orig = _create_failed_goal("run-full", "false")
    # 수정 spec: 격리 공간에 marker 파일 생성 (허용된 echo cmd)
    specs = [{
        "kind": "cmd",
        "cmd": "echo repair-marker",
        "verify": "echo PASS",
        "verify_type": "shell",
        "safe_mode": True,
        "risk": "low",
        "rationale": "test self-healing full chain",
        "files": [],
        "allow_paths": [".claude/state/"],
    }]
    rr = sh.run_repair(orig, repair_specs=specs, auto_approve=True)
    r.rec("full chain reaches judge_handoff",
          rr.get("stage_completed") == "judge_handoff",
          note=f"stage={rr.get('stage_completed')} ok={rr.get('ok')}")
    stages = {s["stage"]: s for s in (rr.get("chain", {}).get("stages") or [])}
    r.rec("execute stage ran",
          stages.get("execute", {}).get("executed", 0) >= 1,
          note=f"execute={stages.get('execute')}")
    r.rec("sandbox apply or discard (no leak)",
          bool(stages.get("execute", {}).get("sandbox_apply"))
          or bool(stages.get("execute", {}).get("sandbox_discard")),
          note=f"apply={stages.get('execute', {}).get('sandbox_apply')} "
               f"discard={stages.get('execute', {}).get('sandbox_discard')}")
    r.rec("judge_handoff file created",
          bool(stages.get("judge_handoff", {}).get("handoff_file")),
          note=f"handoff={stages.get('judge_handoff', {}).get('handoff_file')}")


def test_05_dangerous_repair_blocked(r):
    """비가역 repair cmd 는 promote 단계에서 approval_gate 차단."""
    print("\n[P5 Test 05] dangerous repair cmd blocked at promote")
    orig = _create_failed_goal("dangerous", "false")
    specs = [{
        "kind": "cmd",
        "cmd": "rm -rf /var/data/*",
        "risk": "low",  # 거짓 low
        "rationale": "test dangerous block",
    }]
    rr = sh.run_repair(orig, repair_specs=specs, auto_approve=True)
    stages = {s["stage"]: s for s in (rr.get("chain", {}).get("stages") or [])}
    promote_rejected = stages.get("promote", {}).get("rejected_at_promote") or []
    r.rec("dangerous repair blocked at promote (approval_gate or not_allowed)",
          len(promote_rejected) >= 1
          or rr.get("stage") == "promote",
          note=f"rejected={promote_rejected} stage={rr.get('stage')}")


def test_06_invalid_registration_state(r):
    """invalid_registration 상태 CLI 동작."""
    print("\n[P5 Test 06] invalid_registration CLI")
    import subprocess
    # test ledger 상태: 임시 ledger entry 추가 → invalid-registration 처리
    # 이번 세션 ledger 를 직접 조작하지 않고, cmd_invalid_registration 로직만 import 확인
    sys.path.insert(0, str(ROOT / ".claude" / "scripts"))
    try:
        import importlib.util as _u
        spec = _u.spec_from_file_location("_rl", ROOT / ".claude" / "scripts" / "request-ledger.py")
        rl = _u.module_from_spec(spec); spec.loader.exec_module(rl)
    except Exception as e:
        r.rec("import request-ledger failed", False, note=str(e))
        return
    r.rec("cmd_invalid_registration exists",
          hasattr(rl, "cmd_invalid_registration"),
          note=f"func={hasattr(rl, 'cmd_invalid_registration')}")
    # Status print 포함 "오등록" 라벨 확인
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        rl.cmd_status()
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    r.rec("status output includes '오등록' header",
          "오등록" in out,
          note=f"header_found={'오등록' in out}")
    r.rec("status output includes INVALID label for R75",
          "INVALID" in out and "R75" in out,
          note=f"R75_invalid={'R75' in out and 'INVALID' in out}")


def test_07_judge_handoff_vs_absorbed(r):
    """handoff 생성만 됐을 때 LLM verdict 없음 · absorb 전 VERIFIED 처리 금지."""
    print("\n[P5 Test 07] handoff vs absorbed state")
    gid = _create_failed_goal("judge-state", "false")
    # evidence 재조립 — stat verdict REPAIRING (1 failed task)
    jh = iv.judge_handoff(gid)
    r.rec("handoff created for failed goal",
          jh.get("ok") and bool(jh.get("handoff_file")),
          note=f"handoff={jh.get('handoff_file')}")
    r.rec("stat REPAIRING blocks requires_llm_judge=True (anti-escalation)",
          jh.get("requires_llm_judge") is False,
          note=f"stat={jh.get('stat_verdict')} req_llm={jh.get('requires_llm_judge')}")
    # handoff file 내 status 확인
    hf = Path(jh.get("handoff_file", ""))
    if hf.exists():
        data = json.loads(hf.read_text(encoding="utf-8"))
        r.rec("handoff file status=stat_verdict_blocking",
              data.get("status") == "stat_verdict_blocking",
              note=f"status={data.get('status')}")


def main(argv):
    print(f"=== Phase 5 Self-Healing E2E · marker={MARKER} ===")
    result = R()
    try:
        test_01_analyze_failure(result)
        test_02_create_repair_goal(result)
        test_03_run_repair_without_specs(result)
        test_04_run_repair_with_specs_auto_approve(result)
        test_05_dangerous_repair_blocked(result)
        test_06_invalid_registration_state(result)
        test_07_judge_handoff_vs_absorbed(result)
    except Exception as e:
        import traceback
        print(f"[FATAL] {type(e).__name__}: {e}")
        traceback.print_exc()
        result.rec("test runner fatal", False, note=str(e))
    finally:
        _cleanup()
    s = result.sum()
    print(f"\n=== Summary: {s['passed']}/{s['total']} PASS · {s['failed']} FAIL ===")
    if s["failed"]:
        print("\nFailed:")
        for c in s["cases"]:
            if not c["ok"]:
                print(f"  - {c['name']}: {c['note']}")
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
