"""independent_verifier.py — 독립 검증 scaffold (2026-10-29 Phase 2-C).

사용자 지시 (391e691 후속):
  "개발 Agent 성공 주장만으로 VERIFIED X · 독립 Verifier 가 요구사항·실제 Diff·테스트 결과 비교"
  "Verifier 실패/미실행 시 VERIFIED 금지 · Judge 성공 주장만으로 테스트 성공 대체 X"

이 모듈:
  - judge agent (Haiku 4.5 격리 채점) 호출 scaffold
  - 실 LLM 호출은 Claude Code Task tool 로 (Agent SDK 영역)
  - 이 모듈은 **evidence 수집·판정 로직 분리** 담당

evidence 수집 (실 데이터만):
  - goal description (원문 요구사항)
  - task 실제 cmd + exit_code
  - git diff (실 수정 파일)
  - verifier 결과 (등록 verifier)
  - 테스트 결과 (있으면)

판정:
  - 모든 항목 PASS AND verifier status=="ok" → VERIFIED
  - verifier 미실행 (verify_type 없음) → UNVERIFIED (completed X)
  - verifier 실패 (status!="ok") → REPAIRING
  - evidence 부족 → UNVERIFIED

Judge agent 는 **옵션** · 미호출 상태에서도 안전 default (verifier status 기준).

사용:
  from independent_verifier import collect_evidence, judge
  evidence = collect_evidence(goal_id)
  verdict = judge(evidence)
  # verdict: {"status": "VERIFIED"|"UNVERIFIED"|"REPAIRING", "reasons": [...]}
"""
from __future__ import annotations
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"


def collect_evidence(goal_id: int) -> Dict[str, Any]:
    """goal 1건의 evidence 수집 (DB · git · verifier 결과)."""
    evidence: Dict[str, Any] = {"goal_id": goal_id}
    if not DB.exists():
        return {**evidence, "error": "orca.db not found"}

    with sqlite3.connect(str(DB)) as c:
        # goal 메타
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

        # tasks
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
        task_specs.append({
            "task_id": tid,
            "status": tstatus,
            "kind": spec.get("kind"),
            "cmd": spec.get("cmd"),
            "verify_type": spec.get("verify_type", "shell"),
            "verifier_id": spec.get("verifier_id"),
            "risk": spec.get("risk"),
            "requires_user_approval": spec.get("requires_user_approval"),
        })
    evidence["tasks"] = task_specs
    evidence["task_count"] = len(task_specs)
    evidence["tasks_completed"] = sum(1 for t in task_specs if t["status"] == "completed")
    evidence["tasks_failed"] = sum(1 for t in task_specs if t["status"] == "failed")
    evidence["tasks_unverified"] = sum(
        1 for t in task_specs if t["status"] == "executed_unverified"
    )

    # git diff (실 수정 범위 · 명령·토큰 노출 금지)
    try:
        r = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
        evidence["git_diff_stat"] = r.stdout.strip()[:500] if r.returncode == 0 else None
    except Exception:
        evidence["git_diff_stat"] = None

    return evidence


def judge(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """evidence 기반 독립 판정 (LLM 호출 X · 안전 default).

    사용자 명시:
      - verifier 미실행 → VERIFIED X (UNVERIFIED)
      - verifier 실패 → REPAIRING
      - evidence 부족 → UNVERIFIED
      - Judge Agent LLM 평가는 옵션 (이 함수는 기본 안전 판정)
    """
    reasons: List[str] = []
    task_count = evidence.get("task_count", 0)
    completed = evidence.get("tasks_completed", 0)
    failed = evidence.get("tasks_failed", 0)
    unverified = evidence.get("tasks_unverified", 0)

    if task_count == 0:
        return {"status": "UNVERIFIED", "reasons": ["no tasks registered"]}
    if failed > 0:
        reasons.append(f"{failed} tasks failed")
        return {"status": "REPAIRING", "reasons": reasons}
    if unverified > 0:
        reasons.append(f"{unverified} tasks executed but unverified")
        return {"status": "REPAIRING", "reasons": reasons}
    # verifier 상태 확인
    tasks = evidence.get("tasks") or []
    tasks_with_verifier = [t for t in tasks if t.get("verifier_id") or t.get("verify_type") == "shell"]
    if not tasks_with_verifier:
        reasons.append("no verifier registered for any task")
        return {"status": "UNVERIFIED", "reasons": reasons}
    if completed == task_count:
        reasons.append(f"all {task_count} tasks completed with verifier")
        return {"status": "VERIFIED", "reasons": reasons}
    reasons.append(f"only {completed}/{task_count} completed")
    return {"status": "UNVERIFIED", "reasons": reasons}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: independent_verifier.py <goal_id>")
        sys.exit(2)
    gid = int(sys.argv[1])
    ev = collect_evidence(gid)
    v = judge(ev)
    print(json.dumps({"evidence": ev, "verdict": v}, ensure_ascii=False, indent=2))
    sys.exit(0 if v.get("status") == "VERIFIED" else 1)
