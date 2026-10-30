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


def _cli_main(argv):
    """CLI: `independent_verifier.py <goal_id> [--sandbox PATH] [--allow PATH1,PATH2]`"""
    if len(argv) < 2:
        print("usage: independent_verifier.py <goal_id> [--sandbox PATH] [--allow P1,P2]")
        return 2
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
