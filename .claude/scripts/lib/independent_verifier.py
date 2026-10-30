"""independent_verifier.py — 독립 검증 (2026-10-29 Phase 2-C 완결).

사용자 지시 (391e691 후속):
  "개발 Agent 성공 주장만으로 VERIFIED X · 독립 Verifier 가 요구사항·실제 Diff·테스트 결과 비교"
  "Verifier 실패/미실행 시 VERIFIED 금지 · Judge 성공 주장만으로 테스트 성공 대체 X"

Phase 2-C 완결 (2026-10-29):
  - safe_mode sandbox cwd 기반 git diff 수집 (원본 아닌 격리 공간)
  - scope-lock 통합 (요구사항 외 변경 탐지)
  - executions 테이블의 verified 플래그 재확인 (개발 Agent 보고 재사용 X)
  - 상태 enum: VERIFIED · UNVERIFIED · REPAIRING · FAILED · OUT_OF_SCOPE

evidence 수집 (실 데이터만):
  - goal description (원문 요구사항)
  - task 실제 cmd + exit_code
  - git diff (sandbox 우선 · 없으면 ROOT)
  - verifier 결과 (등록 verifier · executions.verified 재조회)
  - 테스트 결과 (있으면)
  - scope 위반 (allow_paths 외 수정 파일)

판정:
  - verifier 미실행 (verify_type 없음) → UNVERIFIED
  - verifier 실패 (status!="ok") → REPAIRING
  - evidence 부족 → UNVERIFIED
  - scope 위반 → OUT_OF_SCOPE (fail-closed)
  - 전부 완료 AND verifier PASS AND scope OK → VERIFIED

Judge agent 는 **옵션** · LLM 호출 없이도 판정 (안전 default).

사용:
  from independent_verifier import collect_evidence, judge
  evidence = collect_evidence(goal_id, sandbox_cwd="/path/to/sandbox", allow_paths=["src/"])
  verdict = judge(evidence)
  # verdict: {"status": "VERIFIED"|"UNVERIFIED"|"REPAIRING"|"OUT_OF_SCOPE", "reasons": [...]}
"""
from __future__ import annotations
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"


def _run_git_in(cwd: Path, args: list, timeout: int = 10) -> Optional[str]:
    """git 명령 실행 · 실패 시 None."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    return None


def _collect_diff_paths(cwd: Path) -> List[str]:
    """git diff --name-only · 커밋 안 된 변경 파일 목록."""
    out = _run_git_in(cwd, ["diff", "--name-only"])
    if not out:
        return []
    paths = [p.strip() for p in out.splitlines() if p.strip()]
    return paths


def _check_scope(diff_paths: List[str], allow_paths: Optional[List[str]]) -> Dict[str, Any]:
    """scope-lock 통합 — allow_paths glob/prefix 외 수정 파일 탐지.

    allow_paths 가 None 이거나 빈 리스트 → 검사 skip (기존 호환).
    예: allow_paths=["src/", ".claude/scripts/"] → 둘 중 하나로 시작하는 파일만 허용.
    """
    if not allow_paths:
        return {"enforced": False, "violations": []}
    violations = []
    for p in diff_paths:
        matched = any(p == a or p.startswith(a.rstrip("/") + "/") or p.startswith(a)
                      for a in allow_paths)
        if not matched:
            violations.append(p)
    return {"enforced": True, "violations": violations,
            "allow_paths": list(allow_paths)}


def _executions_verified(task_id: str) -> Optional[bool]:
    """executions 테이블에서 해당 task 의 verified 플래그 재조회.
    - 독립 Verifier 는 개발 Agent 보고 (tasks.status) 를 그대로 안 믿고
      runner 가 mark_verified() 한 실제 플래그 확인.
    - 레코드 없음 → None (미실행 신호)
    - 마지막 execution 기준 (여러 번 재시도 가능)
    """
    if not DB.exists():
        return None
    try:
        with sqlite3.connect(str(DB)) as c:
            row = c.execute(
                "SELECT verified FROM executions WHERE task_id=? "
                "ORDER BY exec_id DESC LIMIT 1",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return bool(row[0])
    except Exception:
        return None


def collect_evidence(goal_id: int,
                     sandbox_cwd: Optional[str] = None,
                     allow_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """goal 1건의 evidence 수집 (DB · git · verifier 결과 · scope).

    Phase 2-C 완결 (2026-10-29):
      - sandbox_cwd 전달 시 git diff 를 sandbox 에서 수행
      - allow_paths 전달 시 scope-lock 검사 포함
      - executions.verified 재조회 (tasks.status 그대로 안 믿음)
    """
    evidence: Dict[str, Any] = {"goal_id": goal_id}
    if not DB.exists():
        return {**evidence, "error": "orca.db not found"}

    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT description, status, workflow_type, source_ref, failure_reason "
            "FROM goals WHERE goal_id=?",
            (goal_id,),
        ).fetchone()
        if not row:
            return {**evidence, "error": "goal not found"}
        evidence["description"] = row[0]
        evidence["status"] = row[1]
        evidence["workflow_type"] = row[2]
        evidence["source_ref"] = row[3]
        evidence["failure_reason"] = row[4]

        tasks = c.execute(
            "SELECT task_id, task_file, status FROM tasks "
            "WHERE task_id IN (SELECT task_id FROM goal_tasks WHERE goal_id=?)",
            (goal_id,),
        ).fetchall()

    task_specs: List[Dict] = []
    for tid, tfile, tstatus in tasks:
        try:
            spec = json.loads(tfile) if tfile else {}
        except Exception:
            spec = {}
        # 독립 재조회: executions.verified
        exec_verified = _executions_verified(tid)
        task_specs.append({
            "task_id": tid,
            "status": tstatus,
            "kind": spec.get("kind"),
            "cmd": spec.get("cmd"),
            "verify_type": spec.get("verify_type", "shell"),
            "verifier_id": spec.get("verifier_id"),
            "verify": spec.get("verify"),
            "risk": spec.get("risk"),
            "requires_user_approval": spec.get("requires_user_approval"),
            "executions_verified": exec_verified,  # None = 실행 기록 없음
        })
    evidence["tasks"] = task_specs
    evidence["task_count"] = len(task_specs)
    evidence["tasks_completed"] = sum(1 for t in task_specs if t["status"] == "completed")
    evidence["tasks_failed"] = sum(1 for t in task_specs if t["status"] == "failed")
    evidence["tasks_unverified"] = sum(
        1 for t in task_specs if t["status"] == "executed_unverified"
    )
    evidence["tasks_exec_verified"] = sum(
        1 for t in task_specs if t["executions_verified"] is True
    )
    evidence["tasks_exec_unverified_or_missing"] = sum(
        1 for t in task_specs if t["executions_verified"] is not True
    )

    # git diff · sandbox 우선 · 없으면 ROOT
    diff_cwd = Path(sandbox_cwd) if sandbox_cwd and Path(sandbox_cwd).exists() else ROOT
    evidence["diff_cwd"] = str(diff_cwd)
    evidence["diff_source"] = "sandbox" if sandbox_cwd and diff_cwd != ROOT else "root"
    diff_stat = _run_git_in(diff_cwd, ["diff", "--stat"])
    evidence["git_diff_stat"] = (diff_stat or "").strip()[:500] if diff_stat else None
    diff_paths = _collect_diff_paths(diff_cwd)
    evidence["git_diff_paths"] = diff_paths
    evidence["git_diff_file_count"] = len(diff_paths)

    # scope 검사
    evidence["scope"] = _check_scope(diff_paths, allow_paths)

    return evidence


def judge(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """evidence 기반 독립 판정 (LLM 호출 X · 안전 default).

    Phase 2-C 완결 상태:
      - no tasks → UNVERIFIED
      - failed > 0 → REPAIRING
      - scope violation → OUT_OF_SCOPE (fail-closed)
      - executions 재조회 verified != task_count → UNVERIFIED
      - verifier 미등록 (verifier_id 없음) → UNVERIFIED
      - 모두 통과 → VERIFIED
    """
    reasons: List[str] = []
    task_count = evidence.get("task_count", 0)
    completed = evidence.get("tasks_completed", 0)
    failed = evidence.get("tasks_failed", 0)
    unverified = evidence.get("tasks_unverified", 0)
    exec_verified = evidence.get("tasks_exec_verified", 0)
    exec_unverified = evidence.get("tasks_exec_unverified_or_missing", 0)
    scope = evidence.get("scope") or {}
    tasks = evidence.get("tasks") or []

    if task_count == 0:
        return {"status": "UNVERIFIED", "reasons": ["no tasks registered"]}

    # scope 위반 — fail-closed · 다른 판정보다 우선
    if scope.get("enforced") and scope.get("violations"):
        v = scope.get("violations", [])
        reasons.append(f"scope violations ({len(v)} files outside allow_paths)")
        return {"status": "OUT_OF_SCOPE", "reasons": reasons,
                "violations": v[:20]}

    if failed > 0:
        reasons.append(f"{failed} tasks failed (per tasks.status)")
        return {"status": "REPAIRING", "reasons": reasons}
    if unverified > 0:
        reasons.append(f"{unverified} tasks executed but unverified (per tasks.status)")
        return {"status": "REPAIRING", "reasons": reasons}

    # 독립 재조회: executions.verified 가 task_count 와 일치해야.
    # 개발 Agent 가 tasks.status='completed' 로 바꿔도 executions.verified=0 이면 인정 X.
    if exec_unverified > 0:
        reasons.append(
            f"{exec_unverified}/{task_count} tasks lack verified executions "
            f"(executions.verified != 1 or missing)"
        )
        return {"status": "UNVERIFIED", "reasons": reasons}

    # verifier 등록 여부
    tasks_with_verifier = [t for t in tasks
                           if t.get("verifier_id") or t.get("verify_type") == "shell"]
    if not tasks_with_verifier:
        reasons.append("no verifier registered for any task")
        return {"status": "UNVERIFIED", "reasons": reasons}

    if completed == task_count and exec_verified == task_count:
        reasons.append(
            f"all {task_count} tasks completed · {exec_verified} executions verified "
            f"· scope {'OK' if scope.get('enforced') else 'unchecked'}"
        )
        return {"status": "VERIFIED", "reasons": reasons}

    reasons.append(f"only {completed}/{task_count} completed · exec_verified={exec_verified}")
    return {"status": "UNVERIFIED", "reasons": reasons}


JUDGE_QUEUE = ROOT / ".claude" / "state" / "judge-queue"


def judge_handoff(goal_id: int,
                  sandbox_cwd: Optional[str] = None,
                  allow_paths: Optional[List[str]] = None,
                  judge_notes: str = "") -> Dict[str, Any]:
    """agent-01-judge subagent 호출용 context 생성 + judge-queue 저장.

    Phase 3-R5 (사용자 지시 3307fcd 후속):
      - Independent Judge 보완 · agent-01-judge 재사용
      - 통계·evidence 기반 judge() 는 유지 · 그 위에 LLM 평가 연결
      - LLM 결과가 PASS 라도 테스트 실패 시 VERIFIED 금지 (judge() 가 선 판정)
      - Judge 미실행·근거 부족 → UNVERIFIED (안전 default)

    사용 흐름:
      1. supervisor.execute_goal 완료 후 이 함수 호출
      2. judge-queue 에 goal 별 context JSON 저장 (handoff file)
      3. 메인 Claude 가 Task tool 로 agent-01-judge subagent 호출 유도 (systemMessage)
      4. subagent 결과 (JSON score) 를 judge_absorb() 로 저장
      5. 최종 verdict = combine(statistical_judge, llm_judge, test_results)

    반환:
      - evidence · verdict (통계) · judge_prompt (subagent 호출용) · handoff_file 경로
    """
    JUDGE_QUEUE.mkdir(parents=True, exist_ok=True)
    evidence = collect_evidence(goal_id, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
    stat_verdict = judge(evidence)

    # 통계 verdict 가 이미 VERIFIED 가 아니면 LLM judge 로도 뒤집히지 않음 (안전 우선)
    requires_llm = (stat_verdict.get("status") == "VERIFIED")

    desc = evidence.get("description") or ""
    tasks = evidence.get("tasks") or []
    diff_stat = evidence.get("git_diff_stat") or "(no diff)"
    diff_paths = evidence.get("git_diff_paths") or []
    scope = evidence.get("scope") or {}

    judge_prompt = (
        f"# agent-01-judge · goal #{goal_id}\n\n"
        f"## 요구사항 원문 (사용자 요청)\n{desc[:600]}\n\n"
        f"## 실제 변경 (git diff)\n{diff_stat}\n\n"
        f"변경 파일 ({len(diff_paths)}): {', '.join(diff_paths[:10])}\n\n"
        f"## tasks 실행 결과\n"
        + "\n".join(
            f"  - {t['task_id']}: status={t['status']} verify={t.get('verify_type')} "
            f"exec_verified={t.get('executions_verified')}"
            for t in tasks
        )
        + f"\n\n## scope\n enforced={scope.get('enforced')} violations={scope.get('violations', [])[:5]}\n\n"
        f"## 통계 판정 (사전)\n{json.dumps(stat_verdict, ensure_ascii=False)}\n\n"
        f"## 요청\n"
        f"다음을 평가해 JSON 으로 반환해라:\n"
        f"  {{\n"
        f"    \"satisfies_requirement\": true|false,  // 요구사항 충족\n"
        f"    \"missing_requirements\": [\"<요구 사항 누락 목록>\"],\n"
        f"    \"unexpected_side_effects\": [\"<예상 밖 부작용>\"],\n"
        f"    \"scope_adequacy\": \"ok|too_narrow|too_broad\",\n"
        f"    \"confidence\": 0-10,\n"
        f"    \"recommendation\": \"VERIFIED|UNVERIFIED|REPAIRING|OUT_OF_SCOPE\",\n"
        f"    \"reasoning\": \"<한 단락>\"\n"
        f"  }}\n\n"
        f"지켜라:\n"
        f"  - 통계 판정이 VERIFIED 가 아니면 LLM 평가로 VERIFIED 승격 X (안전 우선)\n"
        f"  - 테스트 실패·exec_verified!=task_count 는 VERIFIED 금지\n"
        f"  - 근거 부족 (diff 비어있거나 요구사항 모호) → UNVERIFIED\n"
        f"  - 범위 외 수정 발견 → OUT_OF_SCOPE\n"
    )
    if judge_notes:
        judge_prompt += f"\n## 추가 노트\n{judge_notes}\n"

    handoff_file = JUDGE_QUEUE / f"goal-{goal_id}.json"
    handoff_data = {
        "goal_id": goal_id,
        "created_at": __import__("time").time(),
        "stat_verdict": stat_verdict,
        "evidence_summary": {
            "task_count": evidence.get("task_count"),
            "tasks_completed": evidence.get("tasks_completed"),
            "tasks_exec_verified": evidence.get("tasks_exec_verified"),
            "diff_file_count": evidence.get("git_diff_file_count"),
            "scope_enforced": scope.get("enforced"),
            "scope_violations": scope.get("violations", [])[:10],
        },
        "judge_prompt": judge_prompt,
        "requires_llm_judge": requires_llm,
        "status": "pending_llm_judge" if requires_llm else "stat_verdict_blocking",
    }
    handoff_file.write_text(json.dumps(handoff_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {
        "ok": True,
        "goal_id": goal_id,
        "handoff_file": str(handoff_file),
        "stat_verdict": stat_verdict,
        "requires_llm_judge": requires_llm,
        "judge_prompt_head": judge_prompt[:600],
    }


def judge_absorb(goal_id: int, judge_result_json: str) -> Dict[str, Any]:
    """agent-01-judge subagent 결과를 받아 최종 verdict 결합.

    사용자 지시: "Judge 가 승인하더라도 필수 테스트 실패 시 VERIFIED 금지"
                "Judge 미실행·근거 부족 → UNVERIFIED"
    """
    try:
        llm_verdict = json.loads(judge_result_json)
    except Exception as e:
        return {"ok": False, "error": f"json parse: {e}"}
    handoff_file = JUDGE_QUEUE / f"goal-{goal_id}.json"
    if not handoff_file.exists():
        return {"ok": False, "error": f"handoff file not found: {handoff_file}"}
    try:
        data = json.loads(handoff_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"handoff read: {e}"}
    stat = data.get("stat_verdict") or {}
    # 안전 결합 규칙:
    #   - stat != VERIFIED → final = stat (LLM 으로 승격 X)
    #   - stat == VERIFIED AND llm.satisfies AND llm.confidence>=7 → VERIFIED
    #   - stat == VERIFIED AND NOT llm.satisfies → REPAIRING
    #   - llm 결과 파싱 실패·confidence 부족 → UNVERIFIED
    stat_status = stat.get("status")
    reasons = list(stat.get("reasons") or [])
    if stat_status != "VERIFIED":
        final = {"status": stat_status, "reasons": reasons + ["statistical judgment blocks VERIFIED"]}
    else:
        satisfies = bool(llm_verdict.get("satisfies_requirement"))
        confidence = int(llm_verdict.get("confidence", 0) or 0)
        rec = llm_verdict.get("recommendation", "")
        missing = llm_verdict.get("missing_requirements") or []
        unexpected = llm_verdict.get("unexpected_side_effects") or []
        if not satisfies:
            final = {"status": "REPAIRING",
                     "reasons": reasons + [f"llm judge: not satisfied ({len(missing)} missing)"]}
        elif confidence < 7:
            final = {"status": "UNVERIFIED",
                     "reasons": reasons + [f"llm judge confidence {confidence} < 7"]}
        elif rec == "OUT_OF_SCOPE":
            final = {"status": "OUT_OF_SCOPE",
                     "reasons": reasons + ["llm judge detected scope violation"]}
        elif unexpected:
            final = {"status": "REPAIRING",
                     "reasons": reasons + [f"llm judge: {len(unexpected)} unexpected side effects"]}
        else:
            final = {"status": "VERIFIED",
                     "reasons": reasons + [
                         f"llm judge confirms (conf={confidence})",
                         f"missing={len(missing)} unexpected={len(unexpected)}"]}
    data["llm_verdict"] = llm_verdict
    data["final_verdict"] = final
    data["status"] = "completed"
    handoff_file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {"ok": True, "goal_id": goal_id, "final_verdict": final,
            "stat_verdict": stat, "llm_verdict": llm_verdict}


def _cli_main(argv):
    """CLI: `independent_verifier.py <goal_id> [--sandbox PATH] [--allow PATH1,PATH2]`"""
    if len(argv) < 2:
        print("usage: independent_verifier.py <goal_id> [--sandbox PATH] [--allow P1,P2]")
        print("       independent_verifier.py judge-handoff <goal_id> [--sandbox PATH] [--allow P1,P2]")
        print("       independent_verifier.py judge-absorb <goal_id>  (stdin: LLM result JSON)")
        return 2
    if argv[1] == "judge-handoff":
        if len(argv) < 3:
            print("usage: judge-handoff <goal_id> [--sandbox PATH] [--allow P1,P2]")
            return 2
        gid = int(argv[2])
        sandbox_cwd = None
        allow_paths = None
        for i, a in enumerate(argv):
            if a == "--sandbox" and i + 1 < len(argv):
                sandbox_cwd = argv[i + 1]
            elif a == "--allow" and i + 1 < len(argv):
                allow_paths = [p.strip() for p in argv[i + 1].split(",") if p.strip()]
        r = judge_handoff(gid, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if argv[1] == "judge-absorb":
        if len(argv) < 3:
            print("usage: judge-absorb <goal_id>  (stdin: LLM JSON)")
            return 2
        gid = int(argv[2])
        stdin_data = sys.stdin.read()
        r = judge_absorb(gid, stdin_data)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    try:
        gid = int(argv[1])
    except ValueError:
        print(f"invalid goal_id: {argv[1]}")
        return 2

    sandbox_cwd = None
    allow_paths = None
    for i, a in enumerate(argv):
        if a == "--sandbox" and i + 1 < len(argv):
            sandbox_cwd = argv[i + 1]
        elif a == "--allow" and i + 1 < len(argv):
            allow_paths = [p.strip() for p in argv[i + 1].split(",") if p.strip()]

    ev = collect_evidence(gid, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
    v = judge(ev)
    print(json.dumps({"evidence": ev, "verdict": v}, ensure_ascii=False, indent=2))
    return 0 if v.get("status") == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
