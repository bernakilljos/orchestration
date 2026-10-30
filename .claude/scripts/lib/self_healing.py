"""self_healing.py — 실패 분석 → 격리 수정 → 재테스트 scaffold (Phase 4 · 2026-10-30).

사용자 지시 (3307fcd 후속 · "Self-Healing 실전 연결"):
  - 실패 로그 → 실제 원인 분석 → 수정 후보 → 격리 코드 변경 → 재테스트 → 독립 검증 → 안전한 반영
  - 단순 재시도와 코드 수정 성공을 구분
  - 고정된 오류 예시 분기 X · 다양한 오류에 적용 가능한 작업 계약

기존 자산 재사용 (신규 중복 X):
  - supervisor.create_goal / execute_goal / repair_sandbox
  - runner (executions 테이블)
  - planner (proposal + bridge + promote)
  - independent_verifier (judge_handoff + judge_absorb)

흐름 (범용 Self-Healing):
  1. analyze_failure(failed_task_id or failed_goal_id) — 실패 executions·stderr·exit_code 수집
  2. propose_repair(context) — 분석 결과를 **분석 보고서** 로 반환 (SAFE_PATTERNS X · 자동 cmd 생성 X)
     → 사용자/Claude Task tool subagent 가 실제 repair proposal 생성 (planner.bridge)
  3. supervisor.create_goal(repair_desc) + planner.propose + approve + promote
  4. execute_goal (safe_mode sandbox)
  5. independent_verifier.judge_handoff → 메인 Claude 가 judge subagent 호출
  6. 성공 → apply_merge · 실패 → discard + repair goal FAILED

이 모듈은 **분석·orchestration 담당** · 실제 LLM 호출·cmd 생성은 외부 (Claude Task tool 또는 사용자).
"""
from __future__ import annotations
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
LIB = ROOT / ".claude" / "scripts" / "lib"


def _conn():
    return sqlite3.connect(str(DB))


def analyze_failure(goal_id: Optional[int] = None,
                    task_id: Optional[str] = None) -> Dict[str, Any]:
    """실패 goal 또는 task 의 executions 로그·stderr·exit_code 수집.

    SAFE_PATTERNS 추가 X · 분석 보고서만 반환.
    실제 수정 proposal 생성은 외부 (Claude Task tool subagent).
    """
    if not DB.exists():
        return {"error": "orca.db not found"}
    if not goal_id and not task_id:
        return {"error": "goal_id or task_id required"}

    failed_executions = []
    goal_info = None
    tasks_info = []

    with _conn() as c:
        if goal_id:
            row = c.execute(
                "SELECT goal_id, description, status, failure_reason FROM goals WHERE goal_id=?",
                (goal_id,),
            ).fetchone()
            if not row:
                return {"error": f"goal {goal_id} not found"}
            goal_info = {"goal_id": row[0], "description": row[1][:300],
                         "status": row[2], "failure_reason": row[3]}
            task_rows = c.execute(
                "SELECT task_id, task_file, status FROM tasks "
                "WHERE task_id IN (SELECT task_id FROM goal_tasks WHERE goal_id=?)",
                (goal_id,),
            ).fetchall()
            for tid, tfile, tstatus in task_rows:
                try:
                    spec = json.loads(tfile) if tfile else {}
                except Exception:
                    spec = {}
                tasks_info.append({
                    "task_id": tid, "status": tstatus,
                    "cmd": (spec.get("cmd") or "")[:120],
                    "verify": (spec.get("verify") or "")[:80],
                })
                # 실패한 execution 들
                for ex in c.execute(
                    "SELECT exec_id, exit_code, timed_out, stdout_tail, stderr_tail, "
                    "duration_ms, started_at FROM executions "
                    "WHERE task_id=? AND (exit_code != 0 OR verified=0) "
                    "ORDER BY exec_id DESC LIMIT 3",
                    (tid,),
                ).fetchall():
                    failed_executions.append({
                        "exec_id": ex[0], "task_id": tid,
                        "exit_code": ex[1], "timed_out": bool(ex[2]),
                        "stdout_tail": (ex[3] or "")[-500:],
                        "stderr_tail": (ex[4] or "")[-500:],
                        "duration_ms": ex[5],
                    })
        else:
            # task_id 만
            row = c.execute(
                "SELECT task_id, task_file, status FROM tasks WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if not row:
                return {"error": f"task {task_id} not found"}
            try:
                spec = json.loads(row[1]) if row[1] else {}
            except Exception:
                spec = {}
            tasks_info = [{"task_id": row[0], "status": row[2],
                           "cmd": (spec.get("cmd") or "")[:120],
                           "verify": (spec.get("verify") or "")[:80]}]
            for ex in c.execute(
                "SELECT exec_id, exit_code, timed_out, stdout_tail, stderr_tail "
                "FROM executions WHERE task_id=? ORDER BY exec_id DESC LIMIT 3",
                (task_id,),
            ).fetchall():
                failed_executions.append({
                    "exec_id": ex[0], "task_id": task_id,
                    "exit_code": ex[1], "timed_out": bool(ex[2]),
                    "stdout_tail": (ex[3] or "")[-500:],
                    "stderr_tail": (ex[4] or "")[-500:],
                })

    # 공통 패턴 추출 (어휘 매칭 · 안전 default)
    hints = _extract_failure_hints(failed_executions)

    repair_prompt = _render_repair_prompt(goal_info, tasks_info, failed_executions, hints)

    return {
        "goal": goal_info,
        "tasks": tasks_info,
        "failed_executions": failed_executions,
        "failure_hints": hints,
        "repair_prompt": repair_prompt,
        "note": (
            "이 분석 보고서는 statically 생성 · 자동 cmd 생성 X. "
            "repair proposal 은 Claude Task tool subagent 가 repair_prompt 를 받아 생성 → "
            "planner.bridge <repair_goal_id> 로 저장 후 승인 → promote → execute."
        ),
    }


_HINT_PATTERNS = [
    (re.compile(r"ModuleNotFoundError:.*'([^']+)'"), "missing_module"),
    (re.compile(r"FileNotFoundError.*'([^']+)'|No such file or directory.*'([^']+)'"), "missing_file"),
    (re.compile(r"PermissionError|Permission denied"), "permission"),
    (re.compile(r"TimeoutExpired|timeout"), "timeout"),
    (re.compile(r"SyntaxError|line \d+[^\n]*\n[^\n]*SyntaxError"), "syntax"),
    (re.compile(r"NameError.*name '([^']+)' is not defined"), "undefined_name"),
    (re.compile(r"TypeError.*(takes|got|argument)"), "type_mismatch"),
    (re.compile(r"AttributeError.*'(\w+)'\s*object has no attribute\s*'(\w+)'"), "missing_attribute"),
    (re.compile(r"KeyError:\s*'([^']+)'"), "missing_key"),
    (re.compile(r"sqlite3\.(OperationalError|IntegrityError)"), "db_error"),
    (re.compile(r"UnicodeDecodeError|UnicodeEncodeError"), "encoding"),
    (re.compile(r"git.*(conflict|rejected|non-fast-forward)"), "git_conflict"),
    (re.compile(r"connection refused|timed out|unreachable"), "network"),
]


def _extract_failure_hints(executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """stderr/stdout 에서 공통 실패 패턴 추출 (분석 · cmd 생성 X)."""
    hints = []
    seen = set()
    for ex in executions:
        combined = (ex.get("stderr_tail") or "") + "\n" + (ex.get("stdout_tail") or "")
        for pat, kind in _HINT_PATTERNS:
            m = pat.search(combined)
            if not m:
                continue
            key = (kind, m.group(0)[:50])
            if key in seen:
                continue
            seen.add(key)
            hints.append({
                "kind": kind,
                "match": m.group(0)[:120],
                "exec_id": ex.get("exec_id"),
                "exit_code": ex.get("exit_code"),
            })
    return hints


def _render_repair_prompt(goal_info, tasks_info, executions, hints) -> str:
    """Claude Task tool subagent 호출용 repair prompt (SAFE_PATTERNS X)."""
    hint_lines = "\n".join(
        f"  - {h['kind']}: {h['match']}" for h in hints[:10]
    ) or "  (패턴 매치 없음 · stderr/stdout 직접 분석 필요)"
    exec_lines = "\n".join(
        f"  - exec#{ex['exec_id']} task={ex['task_id']} exit={ex['exit_code']} "
        f"stderr_tail={ex['stderr_tail'][:200]!r}"
        for ex in executions[:5]
    )
    goal_block = ""
    if goal_info:
        goal_block = (
            f"\n## 원 goal\n"
            f"- id: {goal_info['goal_id']}\n"
            f"- status: {goal_info['status']}\n"
            f"- description: {goal_info['description'][:300]}\n"
            f"- failure_reason: {goal_info.get('failure_reason') or '(none)'}\n"
        )
    return (
        f"# Self-Healing Repair Proposal Request\n{goal_block}\n"
        f"## 실패 task 들\n"
        + "\n".join(f"  - {t['task_id']}: status={t['status']} cmd={t['cmd']!r}"
                    for t in tasks_info[:10])
        + f"\n\n## 실패 execution 들\n{exec_lines}\n\n"
        f"## 공통 패턴 hint (어휘 매칭 · 참고용)\n{hint_lines}\n\n"
        f"## 요청\n"
        f"위 실패 증거를 분석해 **repair Task 계약 (JSON array)** 을 반환해라.\n"
        f"각 Task 는 planner.bridge 가 받는 스키마를 따른다:\n"
        f"  {{\n"
        f"    \"kind\": \"cmd\",\n"
        f"    \"cmd\": \"<실행 명령 · 허용된 명령 범위 내만>\",\n"
        f"    \"verify\": \"<검증 명령>\",\n"
        f"    \"verify_type\": \"shell|python\",\n"
        f"    \"safe_mode\": true,\n"
        f"    \"risk\": \"low|medium|high\",\n"
        f"    \"requires_user_approval\": true,\n"
        f"    \"rationale\": \"<이 수정이 왜 실패를 해결하는가>\",\n"
        f"    \"files\": [\"<수정 예상 파일>\"],\n"
        f"    \"allow_paths\": [\"<scope-lock>\"]\n"
        f"  }}\n\n"
        f"반드시 지켜라:\n"
        f"  - 단순 재시도 X · 실패 원인을 코드로 수정하는 작업 계약\n"
        f"  - 비가역 명령 (rm -rf·force push·DROP TABLE) 생성 X\n"
        f"  - 각 cmd 는 승인 정책 (approval-gate) 을 통과하도록\n"
        f"  - safe_mode=true 유지 (sandbox 격리)\n"
        f"  - 이 분석 보고서는 어휘 매칭 hint 참고용 · 실제 원인 코드 Read 로 재검증\n\n"
        f"결과 저장:\n"
        f"  python .claude/scripts/lib/planner.py bridge <repair_goal_id>  (stdin: JSON array)\n"
    )


def create_repair_goal(original_goal_id: int,
                       repair_description: str = "") -> Dict[str, Any]:
    """repair goal 생성 (원 goal 참조 · source_ref 추적)."""
    sys.path.insert(0, str(LIB))
    try:
        import supervisor  # noqa: F401
    except Exception as e:
        return {"error": f"supervisor import: {e}"}
    desc = repair_description or f"Self-Healing: goal #{original_goal_id} 실패 복구"
    gid = supervisor.create_goal(desc, max_retry=1, timeout_h=4)
    with _conn() as c:
        c.execute(
            "UPDATE goals SET source_ref=?, workflow_type='REPAIR' WHERE goal_id=?",
            (f"repair:orig_goal={original_goal_id}", gid),
        )
    return {"ok": True, "repair_goal_id": gid, "original_goal_id": original_goal_id}


def _count_repair_attempts(original_goal_id: int) -> int:
    """해당 orig goal 대상 과거 repair goal 개수 (무한 루프 방지 · 2026-10-30 P6-R4)."""
    if not DB.exists():
        return 0
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT COUNT(*) FROM goals WHERE source_ref LIKE ?",
                (f"repair:orig_goal={original_goal_id}%",),
            ).fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def run_repair(original_goal_id: int, repair_specs: Optional[List[Dict]] = None,
               auto_approve: bool = False, max_attempts: int = 3,
               agent_fix: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Self-Healing 전체 chain orchestration (2026-10-30 P5-R2).

    사용자 지시: "Scaffold 상태 → 실제 자동복구 성공과 다르다 · 기존 자산 활용 종단 연결"

    흐름 (기존 자산 재사용 · 중복 X):
      1. analyze_failure(original_goal_id) — 분석 보고서 (이미 scaffold)
      2. create_repair_goal — repair goal 등재 (workflow_type=REPAIR)
      3. repair_specs 가 주어지면 planner.bridge 로 proposal 등재
         (주어지지 않으면 Claude Task tool subagent 호출 유도 systemMessage 반환)
      4. auto_approve=True 면 approve · 아니면 사용자 승인 대기 상태
      5. planner.promote → tasks 등재 (safe_mode=True 강제)
      6. supervisor.execute_goal → sandbox 격리 실행 → apply/discard
      7. independent_verifier.judge_handoff → final verdict

    반환: 각 단계 결과·goal_id·판정·다음 단계 안내.

    안전 원칙:
      - repair_specs 가 없으면 execute 까지 가지 않음 (Task tool subagent 호출 유도만)
      - auto_approve=False 가 default (HITL)
      - 승인 정책·_is_allowed_cmd 는 promote 단계에서 이미 재확인
      - 실패 시 discard 로 원본 보호 (supervisor.execute_goal 안 이미 통합됨)
    """
    sys.path.insert(0, str(LIB))
    try:
        import supervisor as _sup  # noqa: F401
        import planner as _pl  # noqa: F401
        import independent_verifier as _iv  # noqa: F401
    except Exception as e:
        return {"ok": False, "stage": "import", "error": str(e)}

    # 2026-10-30 P6-R4: 무한 재시도 방지 — 같은 orig goal 대상 repair 횟수 상한
    attempts = _count_repair_attempts(original_goal_id)
    if attempts >= max_attempts:
        return {
            "ok": False,
            "stage": "retry_cap",
            "error": f"max_attempts ({max_attempts}) exceeded · {attempts} previous repair goals · 수동 조사 필요",
            "original_goal_id": original_goal_id,
            "attempts": attempts,
            "hint": "repair chain 반복 실패 · 사용자 리뷰 또는 max_attempts 명시 증가",
        }

    chain = {"original_goal_id": original_goal_id, "stages": [],
             "attempts_before": attempts, "max_attempts": max_attempts}

    # Stage 1: analyze
    analysis = analyze_failure(goal_id=original_goal_id)
    if "error" in analysis:
        return {"ok": False, "stage": "analyze", "error": analysis["error"]}
    chain["stages"].append({"stage": "analyze",
                            "failure_hints": analysis.get("failure_hints"),
                            "failed_execs": len(analysis.get("failed_executions") or [])})

    # Stage 2: create repair goal
    rg = create_repair_goal(original_goal_id,
                            f"Self-Healing: goal #{original_goal_id} 복구")
    if not rg.get("ok"):
        return {"ok": False, "stage": "create_repair", **rg}
    repair_gid = rg["repair_goal_id"]
    chain["stages"].append({"stage": "create_repair", "repair_goal_id": repair_gid})

    # Stage 3a (2026-10-30 Phase 10-R2): agent_fix 지정 시 headless Agent 가 자동 수정
    #   agent_fix = {sandbox_id, test_cmd, allow_paths, protected_paths, apply_target[, fix_model, judge_model]}
    if agent_fix and not repair_specs:
        import real_repair_chain as _rc
        hints = "; ".join(f"{h['kind']}: {h['match']}" for h in (analysis.get("failure_hints") or [])[:5])
        ac = _rc.agent_repair_chain(
            repair_gid,
            sandbox_id=agent_fix["sandbox_id"],
            test_cmd=agent_fix["test_cmd"],
            allow_paths=agent_fix["allow_paths"],
            protected_paths=agent_fix.get("protected_paths") or [],
            apply_target=agent_fix["apply_target"],
            failure_summary=f"Failure hints from goal #{original_goal_id}: {hints}" if hints else "",
            **{k: agent_fix[k] for k in ("fix_model", "judge_model", "max_fix_rounds") if k in agent_fix},
        )
        chain["stages"].append({"stage": "agent_repair_chain", "ok": ac.get("ok"),
                                "failed_stage": ac.get("failed_stage"),
                                "stages": ac.get("stages")})
        return {"ok": bool(ac.get("ok")), "stage_completed": "agent_repair_chain",
                "repair_goal_id": repair_gid, "original_goal_id": original_goal_id,
                "invocation": (ac.get("agent_fix") or {}).get("invocation", "auto"),
                "chain": chain, "agent_repair": ac}

    # Stage 3: proposal 등재 (repair_specs 주어진 경우만)
    if not repair_specs:
        # Task tool subagent 호출 유도만
        chain["stages"].append({
            "stage": "propose", "status": "pending_task_tool",
            "note": "repair_specs 미제공 · Claude Task tool subagent 가 analysis.repair_prompt 로 "
                    f"spec 생성 후 'planner.py bridge {repair_gid}' 로 등재해야.",
            "repair_prompt_head": (analysis.get("repair_prompt") or "")[:400],
        })
        return {"ok": True, "stage_completed": "create_repair",
                "repair_goal_id": repair_gid, "chain": chain,
                "next_action": (
                    f"Claude Task tool general-purpose subagent 호출 → "
                    f"analyze_failure.repair_prompt 받아 spec 생성 → "
                    f"'python .claude/scripts/lib/planner.py bridge {repair_gid}' pipe"
                )}

    # repair_specs 주어진 경우 — bridge 로 proposal 저장
    import json as _json
    bridge_r = _pl.bridge(repair_gid, _json.dumps(repair_specs),
                          origin="self-healing-run_repair")
    if not bridge_r.get("ok"):
        return {"ok": False, "stage": "bridge", **bridge_r,
                "repair_goal_id": repair_gid}
    chain["stages"].append({"stage": "bridge",
                            "proposed": bridge_r.get("proposed")})

    # Stage 4: approve (auto_approve=True 만)
    if not auto_approve:
        chain["stages"].append({"stage": "approve", "status": "pending_user_approval",
                                "note": "auto_approve=False · 사용자 승인 대기 · "
                                        f"'planner.py approve <pid>' 후 promote"})
        return {"ok": True, "stage_completed": "bridge",
                "repair_goal_id": repair_gid, "chain": chain,
                "proposals": bridge_r.get("proposals"),
                "next_action": (
                    f"사용자 승인: 'python .claude/scripts/lib/planner.py approve <pid>' "
                    f"× {bridge_r.get('proposed')} → promote {repair_gid}"
                )}

    approved_ids = []
    for p in (bridge_r.get("proposals") or []):
        ar = _pl.approve(p["proposal_id"], approved_by="self-healing-auto")
        if ar.get("status") == "approved":
            approved_ids.append(p["proposal_id"])
    chain["stages"].append({"stage": "approve", "approved": len(approved_ids)})

    # Stage 5: promote
    pr = _pl.promote(repair_gid)
    chain["stages"].append({"stage": "promote", "promoted": pr.get("promoted"),
                            "rejected_at_promote": pr.get("rejected")})
    if pr.get("promoted", 0) == 0:
        return {"ok": False, "stage": "promote",
                "note": "0 proposals promoted (approval-gate 또는 _is_allowed_cmd 차단)",
                "repair_goal_id": repair_gid, "chain": chain}

    # Stage 6: execute (sandbox 자동)
    ex_r = _sup.execute_goal(repair_gid)
    chain["stages"].append({"stage": "execute",
                            "executed": ex_r.get("executed"),
                            "verified": ex_r.get("verified"),
                            "failed": ex_r.get("failed"),
                            "sandbox_apply": ex_r.get("sandbox_apply"),
                            "sandbox_discard": ex_r.get("sandbox_discard")})

    # Stage 7: judge_handoff
    sandbox_cwd = None
    for sb in (ex_r.get("sandboxes") or []):
        sandbox_cwd = sb.get("path")
        break
    jh = _iv.judge_handoff(repair_gid, sandbox_cwd=sandbox_cwd)
    chain["stages"].append({"stage": "judge_handoff",
                            "stat_verdict": jh.get("stat_verdict"),
                            "requires_llm_judge": jh.get("requires_llm_judge"),
                            "handoff_file": jh.get("handoff_file")})

    success = (ex_r.get("failed", 0) == 0
               and ex_r.get("verified", 0) >= 1
               and jh.get("stat_verdict", {}).get("status") == "VERIFIED")

    return {
        "ok": success,
        "stage_completed": "judge_handoff",
        "repair_goal_id": repair_gid,
        "original_goal_id": original_goal_id,
        "chain": chain,
        "result_summary": {
            "executed": ex_r.get("executed", 0),
            "verified": ex_r.get("verified", 0),
            "failed": ex_r.get("failed", 0),
            "stat_verdict": jh.get("stat_verdict", {}).get("status"),
            "applied": bool(ex_r.get("sandbox_apply")),
            "discarded": bool(ex_r.get("sandbox_discard")),
        },
        "next_action": (
            "메인 Claude turn 에서 Task tool agent-01-judge subagent 호출 → "
            f"judge_absorb {repair_gid} 로 최종 verdict 저장"
            if jh.get("requires_llm_judge")
            else "stat verdict 가 VERIFIED 아님 · LLM judge 로 승격 X (안전 default)"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Phase 12 (2026-10-30): 무인 운영 연결.
#   supervisor 가 실패를 감지하면 enqueue_failure_event() 로 이벤트만 영속화 (빠름).
#   Task Scheduler(Orca_10MinLoop) 가 heal-tick --trigger scheduler 로 process_events() 실행.
#   opt-in: 실패 task spec 에 "self_heal" 설정이 있는 goal 만 대상 (임의 goal 자동 수정 X).
#   이벤트 = 원자적 claim + lease · 중단된 claim 은 다음 tick 에서 복구.
# ─────────────────────────────────────────────────────────────────────────────

HEAL_ACTIVE = ("pending", "claimed")


def _ensure_heal_schema() -> None:
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS self_heal_events ("
            " event_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " goal_id INTEGER NOT NULL, task_id TEXT, config TEXT NOT NULL,"
            " status TEXT NOT NULL DEFAULT 'pending',"
            " claimed_by TEXT, claimed_at INTEGER DEFAULT 0, attempts INTEGER DEFAULT 0,"
            " repair_goal_id INTEGER, sandbox_id TEXT, trigger_source TEXT,"
            " result TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_heal_goal ON self_heal_events(goal_id, status)")


def has_active_event(goal_id: int) -> bool:
    if not DB.exists():
        return False
    _ensure_heal_schema()
    with _conn() as c:
        row = c.execute("SELECT 1 FROM self_heal_events WHERE goal_id=? AND status IN (?, ?)",
                        (goal_id, *HEAL_ACTIVE)).fetchone()
    return bool(row)


def enqueue_failure_event(goal_id: int) -> Dict[str, Any]:
    """실패 goal 중 self_heal opt-in task 가 있으면 이벤트 1건 영속화 (goal 당 활성 1건 · 멱등)."""
    _ensure_heal_schema()
    now = int(time.time())
    with _conn() as c:
        if c.execute("SELECT 1 FROM self_heal_events WHERE goal_id=? AND status IN (?, ?)",
                     (goal_id, *HEAL_ACTIVE)).fetchone():
            return {"enqueued": False, "reason": "active event exists"}
        rows = c.execute(
            "SELECT t.task_id, t.task_file FROM tasks t JOIN goal_tasks gt ON gt.task_id=t.task_id "
            "WHERE gt.goal_id=? AND t.status IN ('failed','executed_unverified')", (goal_id,)).fetchall()
        for tid, tfile in rows:
            try:
                spec = json.loads(tfile) if tfile else {}
            except Exception:
                continue
            cfg = spec.get("self_heal")
            if not isinstance(cfg, dict) or not cfg.get("test_cmd") or not cfg.get("allow_paths"):
                continue
            cfg = {**cfg, "base_ref": cfg.get("base_ref") or spec.get("sandbox_base") or "HEAD"}
            cur = c.execute(
                "INSERT INTO self_heal_events (goal_id, task_id, config, status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?)", (goal_id, tid, json.dumps(cfg), now, now))
            return {"enqueued": True, "event_id": cur.lastrowid, "task_id": tid}
    return {"enqueued": False, "reason": "no self_heal opt-in task"}


def _claim_event(worker: str, lease_s: int, event_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """pending 또는 lease 만료된 claimed 1건을 원자적으로 claim (event_id 지정 시 그 건만)."""
    now = int(time.time())
    with sqlite3.connect(str(DB), timeout=10, isolation_level="IMMEDIATE") as c:
        row = c.execute(
            "SELECT event_id, goal_id, task_id, config, status, repair_goal_id, attempts "
            "FROM self_heal_events WHERE (status='pending' OR (status='claimed' AND claimed_at < ?)) "
            "AND (? IS NULL OR event_id=?) ORDER BY event_id LIMIT 1",
            (now - lease_s, event_id, event_id)).fetchone()
        if not row:
            return None
        cur = c.execute(
            "UPDATE self_heal_events SET status='claimed', claimed_by=?, claimed_at=?, "
            "attempts=attempts+1, updated_at=? WHERE event_id=? AND status=?",
            (worker, now, now, row[0], row[4]))
        if cur.rowcount != 1:
            return None
    return {"event_id": row[0], "goal_id": row[1], "task_id": row[2], "config": json.loads(row[3]),
            "recovered_from": row[4] if row[4] == "claimed" else None,
            "stale_repair_goal_id": row[5], "attempts": row[6] + 1}


def _finish_event(event_id: int, status: str, **fields) -> None:
    sets = ["status=?", "updated_at=?"]
    vals: List[Any] = [status, int(time.time())]
    for k, v in fields.items():
        sets.append(f"{k}=?")
        vals.append(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    with _conn() as c:
        c.execute(f"UPDATE self_heal_events SET {', '.join(sets)} WHERE event_id=?", (*vals, event_id))


def close_stale_repair_goals(orig_goal_id: int, actor: str) -> List[int]:
    sys.path.insert(0, str(LIB))
    import supervisor as _sup
    with _conn() as c:
        rows = c.execute("SELECT goal_id FROM goals WHERE source_ref LIKE ? AND status NOT IN "
                         "('VERIFIED','FAILED','BLOCKED')", (f"repair:orig_goal={orig_goal_id}%",)).fetchall()
    closed = []
    for (rg,) in rows:
        if _sup.advance(rg, "FAILED", "interrupted · heal worker died · recovered by next tick", actor=actor):
            closed.append(rg)
    return closed


def process_events(trigger_source: str, lease_s: int = 1800, max_events: int = 1,
                   max_event_attempts: int = 2) -> Dict[str, Any]:
    """이벤트 → sandbox(base_ref) → run_repair(agent_fix) → 원 goal BLOCKED(사유) · 다른 goal·Ledger 무관."""
    if not DB.exists():
        return {"processed": 0, "error": "orca.db not found"}
    _ensure_heal_schema()
    sys.path.insert(0, str(LIB))
    import supervisor as _sup
    import repair_sandbox as _sb
    worker = f"heal:{trigger_source}:{os.getpid()}"
    results = []
    for _ in range(max_events):
        ev = _claim_event(worker, lease_s)
        if not ev:
            break
        eid, gid, cfg = ev["event_id"], ev["goal_id"], ev["config"]
        rec: Dict[str, Any] = {"event_id": eid, "goal_id": gid, "trigger_source": trigger_source,
                               "attempt": ev["attempts"], "recovered_from": ev["recovered_from"]}
        with _conn() as c:
            c.execute("UPDATE self_heal_events SET trigger_source=? WHERE event_id=?", (trigger_source, eid))
        # 재시작 복원: 중단된 이전 시도의 repair goal 은 FAILED(interrupted) 로 닫는다.
        # repair_goal_id 는 시도 끝에야 기록되므로, 원 goal 의 미종결 repair goal 을 직접 찾는다
        # (goal 당 활성 이벤트는 1건이라 이 goal 들은 모두 죽은 시도의 것).
        if ev["recovered_from"]:
            rec["closed_stale_repair_goals"] = close_stale_repair_goals(gid, worker)
        if ev["attempts"] > max_event_attempts:
            _sup.advance(gid, "BLOCKED", f"self-heal event {eid}: attempts exhausted", actor=worker)
            _finish_event(eid, "blocked", result={"reason": "attempts exhausted"})
            rec["status"] = "blocked"
            results.append(rec)
            continue
        sid = f"heal-e{eid}-a{ev['attempts']}"
        sbr = _sb.create(sid, base_ref=cfg.get("base_ref", "HEAD"))
        if not sbr.get("ok"):
            _finish_event(eid, "pending", result={"sandbox_error": sbr.get("reason")})
            rec.update(status="pending", error=sbr.get("reason"))
            results.append(rec)
            continue
        base_sha = _sb._git("rev-parse", cfg.get("base_ref", "HEAD")).stdout.strip()
        target = cfg.get("apply_target") or f"self-heal/g{gid}-e{eid}"
        if _sb._git("rev-parse", "--verify", "-q", f"refs/heads/{target}").returncode != 0:
            _sb._git("branch", target, base_sha)
        with _conn() as c:
            c.execute("UPDATE self_heal_events SET sandbox_id=? WHERE event_id=?", (sid, eid))
        rr = run_repair(gid, agent_fix={
            "sandbox_id": sid, "test_cmd": cfg["test_cmd"], "allow_paths": cfg["allow_paths"],
            "protected_paths": cfg.get("protected_paths") or [], "apply_target": target,
            **{k: cfg[k] for k in ("fix_model", "judge_model", "max_fix_rounds") if k in cfg}})
        repair_gid = rr.get("repair_goal_id")
        ar = rr.get("agent_repair") or {}
        summary = {"ok": rr.get("ok"), "stage": rr.get("stage"), "failed_stage": ar.get("failed_stage"),
                   "repair_goal_id": repair_gid, "apply_target": target,
                   "applied_sha": (ar.get("apply") or {}).get("to_sha"),
                   "agent_sessions": [r.get("agent_session_id") for r in ar.get("agent_fix_rounds") or []],
                   "judge_session": (ar.get("agent_judge") or {}).get("agent_session_id"),
                   "final_verdict": ((ar.get("judge") or {}).get("final_verdict") or {}).get("status")}
        if rr.get("ok"):
            _sup.advance(gid, "BLOCKED", f"self-heal e{eid}: repair goal #{repair_gid} VERIFIED · "
                                         f"fix on {target}@{(summary['applied_sha'] or '')[:7]} · merge 승인 대기",
                         actor=worker)
            _finish_event(eid, "repaired", repair_goal_id=repair_gid, result=summary)
            rec["status"] = "repaired"
        else:
            _sup.advance(gid, "BLOCKED", f"self-heal e{eid}: repair failed at "
                                         f"{summary['failed_stage'] or summary['stage']} · 수동 조사 필요",
                         actor=worker)
            _finish_event(eid, "failed", repair_goal_id=repair_gid, result=summary)
            rec["status"] = "failed"
        rec.update(summary)
        results.append(rec)
    return {"processed": len(results), "trigger_source": trigger_source, "events": results}


def list_events(limit: int = 20) -> List[Dict[str, Any]]:
    _ensure_heal_schema()
    with _conn() as c:
        rows = c.execute("SELECT event_id, goal_id, status, attempts, repair_goal_id, sandbox_id, "
                         "trigger_source, claimed_by, result FROM self_heal_events "
                         "ORDER BY event_id DESC LIMIT ?", (limit,)).fetchall()
    keys = ("event_id", "goal_id", "status", "attempts", "repair_goal_id", "sandbox_id",
            "trigger_source", "claimed_by", "result")
    return [dict(zip(keys, r)) for r in rows]


def _cli_main(argv):
    if len(argv) >= 2 and argv[1] == "heal-tick":
        trig = argv[argv.index("--trigger") + 1] if "--trigger" in argv else "manual"
        lease = int(argv[argv.index("--lease-s") + 1]) if "--lease-s" in argv else 1800
        print(json.dumps(process_events(trig, lease_s=lease), ensure_ascii=False, indent=2))
        return 0
    if len(argv) >= 2 and argv[1] == "heal-events":
        print(json.dumps(list_events(), ensure_ascii=False, indent=2))
        return 0
    if len(argv) < 2:
        print("usage: self_healing.py {analyze|create-repair|run-repair} [args]")
        print("  analyze --goal <id> | --task <task_id>")
        print("  create-repair <original_goal_id> [description]")
        print("  run-repair <original_goal_id> [--auto-approve] [--specs-stdin]")
        return 2
    cmd = argv[1]
    if cmd == "analyze":
        goal_id = None
        task_id = None
        for i, a in enumerate(argv):
            if a == "--goal" and i + 1 < len(argv):
                goal_id = int(argv[i + 1])
            elif a == "--task" and i + 1 < len(argv):
                task_id = argv[i + 1]
        r = analyze_failure(goal_id=goal_id, task_id=task_id)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if "error" not in r else 1
    if cmd == "create-repair":
        if len(argv) < 3:
            print("usage: self_healing.py create-repair <orig_goal_id> [desc]")
            return 2
        orig = int(argv[2])
        desc = argv[3] if len(argv) > 3 else ""
        r = create_repair_goal(orig, desc)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if cmd == "run-repair":
        if len(argv) < 3:
            print("usage: self_healing.py run-repair <orig_goal_id> [--auto-approve] [--specs-stdin] [--max-attempts N]")
            return 2
        orig = int(argv[2])
        auto_approve = "--auto-approve" in argv
        max_attempts = 3
        if "--max-attempts" in argv:
            i = argv.index("--max-attempts")
            if i + 1 < len(argv):
                try:
                    max_attempts = int(argv[i + 1])
                except Exception:
                    pass
        repair_specs = None
        if "--specs-stdin" in argv:
            try:
                repair_specs = json.loads(sys.stdin.read())
            except Exception as e:
                print(json.dumps({"error": f"stdin json parse: {e}"}))
                return 2
        agent_fix = None
        if "--agent-fix-json" in argv:
            i = argv.index("--agent-fix-json")
            try:
                agent_fix = json.loads(Path(argv[i + 1]).read_text(encoding="utf-8"))
            except Exception as e:
                print(json.dumps({"error": f"agent-fix json: {e}"}))
                return 2
        r = run_repair(orig, repair_specs=repair_specs, auto_approve=auto_approve,
                       max_attempts=max_attempts, agent_fix=agent_fix)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
