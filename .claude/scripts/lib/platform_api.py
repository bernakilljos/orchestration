"""platform_api.py — 로컬 Platform API 계약 + PoC (Phase 15 · 2026-10-30).

기존 자산을 감싸기만 한다 (재구현 X):
  goal 등록·조회 = supervisor · 승인 = approval-gate / planner / tech_discovery · 지표 = ops_metrics ·
  Agent = agent_registry · evidence = executions·judge-queue·self_heal_events.

안전 계약:
  - API 는 명령을 실행하지 않는다 (goal 은 PENDING 으로만 등록 · 실행은 기존 Supervisor/Scheduler 경로)
  - merge·배포·삭제 같은 운영 작업은 노출하지 않는다
  - 승인/거부는 사람 식별자(by)만 · Agent·자동화 식별자는 거부 → 기존 승인 함수에 그대로 위임
네트워크 서버 없음 (로컬 함수 + CLI JSON).
"""
from __future__ import annotations
import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
LIB = ROOT / ".claude" / "scripts" / "lib"
DB = ROOT / ".claude" / "state" / "orca.db"
sys.path.insert(0, str(LIB))

AUTOMATED_ACTORS = ("agent", "claude", "heal", "self-healing", "supervisor", "scheduler", "auto", "bot")


def _gate():
    spec = importlib.util.spec_from_file_location("_approval_gate", ROOT / ".claude" / "scripts" / "approval-gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def register_goal(description: str, source: str = "platform-api") -> Dict[str, Any]:
    import supervisor
    if not (description or "").strip():
        return {"ok": False, "error": "description required"}
    gid = supervisor.create_goal(description.strip()[:2000], source_ref=f"api:{source}")
    return {"ok": True, "goal_id": gid, "status": "PENDING",
            "note": "등록만 · 실행은 Supervisor/Scheduler 경로 (API 는 실행하지 않음)"}


def goal_status(goal_id: int) -> Dict[str, Any]:
    import supervisor
    g = supervisor.show_goal(int(goal_id))
    return {"ok": bool(g), "goal": g} if g else {"ok": False, "error": "goal not found"}


def evidence(goal_id: int) -> Dict[str, Any]:
    with sqlite3.connect(str(DB)) as c:
        ex = c.execute("SELECT e.exec_id, e.task_id, e.exit_code, e.verified, e.duration_ms, e.cwd FROM executions e "
                       "WHERE e.task_id IN (SELECT task_id FROM goal_tasks WHERE goal_id=?) "
                       "OR e.task_id LIKE ? ORDER BY e.exec_id", (goal_id, f"g{goal_id}-%")).fetchall()
        heal = c.execute("SELECT event_id, status, repair_goal_id, result FROM self_heal_events "
                         "WHERE goal_id=? OR repair_goal_id=?", (goal_id, goal_id)).fetchall()
    jf = ROOT / ".claude" / "state" / "judge-queue" / f"goal-{goal_id}.json"
    judge = None
    if jf.exists():
        j = json.loads(jf.read_text(encoding="utf-8"))
        judge = {"stat": (j.get("stat_verdict") or {}).get("status"),
                 "final": (j.get("final_verdict") or {}).get("status"), "status": j.get("status")}
    return {"ok": True, "goal_id": goal_id,
            "executions": [dict(zip(("exec_id", "task_id", "exit_code", "verified", "duration_ms", "cwd"), r)) for r in ex],
            "self_heal": [{"event_id": h[0], "status": h[1], "repair_goal_id": h[2],
                           "result": json.loads(h[3]) if h[3] else None} for h in heal],
            "judge": judge or "UNKNOWN"}


def approvals() -> Dict[str, Any]:
    import planner
    out: Dict[str, Any] = {"risky_tasks": _gate().list_waiting(),
                           "planner_proposals": planner.list_proposals(status="pending")}
    with sqlite3.connect(str(DB)) as c:
        try:
            out["discovery_candidates"] = [dict(zip(("candidate_id", "title", "priority", "status"), r)) for r in c.execute(
                "SELECT candidate_id, title, priority, status FROM tech_candidates "
                "WHERE status IN ('proposed','investigated_proposal_pending') ORDER BY candidate_id")]
        except sqlite3.Error:
            out["discovery_candidates"] = "UNKNOWN"
        out["self_heal_merge_waiting"] = [dict(zip(("goal_id", "reason"), r)) for r in c.execute(
            "SELECT goal_id, failure_reason FROM goals WHERE status='BLOCKED' AND goal_id IN "
            "(SELECT goal_id FROM self_heal_events WHERE status='repaired')")]
    out["note"] = "self_heal_merge_waiting 은 조회만 · merge 는 API 로 노출하지 않음"
    return out


def decide(kind: str, item_id, decision: str, by: str, reason: str = "") -> Dict[str, Any]:
    """사람의 승인/거부를 기존 승인 함수에 위임. 자동화 식별자·알 수 없는 종류는 거부."""
    by_l = (by or "").strip().lower()
    if not by_l or any(by_l.startswith(a) for a in AUTOMATED_ACTORS):
        return {"ok": False, "error": f"사람 식별자만 승인 가능 (by={by!r})"}
    if decision not in ("approve", "reject"):
        return {"ok": False, "error": "decision must be approve|reject"}
    if kind == "task":
        g = _gate()
        return g.approve(str(item_id), by=by) if decision == "approve" else g.reject(str(item_id), by=by, reason=reason)
    if kind == "proposal":
        import planner
        return planner.approve(int(item_id), approved_by=by) if decision == "approve" else planner.reject(int(item_id), reason)
    if kind == "candidate":
        import tech_discovery
        if decision == "approve":
            return tech_discovery.approve_candidate(int(item_id), by)
        with sqlite3.connect(str(DB)) as c:
            n = c.execute("UPDATE tech_candidates SET status='rejected', decided_at=strftime('%s','now'), decided_by=? "
                          "WHERE candidate_id=? AND status IN ('proposed','investigated_proposal_pending')",
                          (by, int(item_id))).rowcount
        return {"ok": n == 1, "candidate_id": int(item_id), "status": "rejected" if n else "unchanged"}
    return {"ok": False, "error": f"kind {kind!r} 는 API 로 결정할 수 없음 (허용: task·proposal·candidate)"}


def agents() -> Dict[str, Any]:
    import agent_registry
    with sqlite3.connect(str(DB)) as c:
        usage = c.execute("SELECT ai, COUNT(*), SUM(success), SUM(tokens_in), SUM(tokens_out), SUM(cost_usd) "
                          "FROM metrics WHERE ai LIKE 'claude-agent:%' GROUP BY ai").fetchall()
    return {"registry": [{k: a[k] for k in ("name", "capabilities", "model")} for a in agent_registry.load_agents()],
            "usage": {u[0]: {"calls": u[1], "success": u[2], "tokens_in": u[3], "tokens_out": u[4],
                             "cost_usd": round(u[5] or 0, 4)} for u in usage} or "UNKNOWN"}


def resources(window_h: float = 24) -> Dict[str, Any]:
    import ops_metrics
    r = ops_metrics.report(window_h)
    return {"resources": r.get("resources"), "tokens_cost": r.get("tokens_cost"),
            "agent_cost_usd": (r.get("agents") or {}).get("dag_cost_usd")}


OPS = {"register_goal": register_goal, "goal_status": goal_status, "evidence": evidence, "approvals": approvals,
       "decide": decide, "agents": agents, "resources": resources}


def main(argv) -> int:
    if len(argv) < 2 or argv[1] not in OPS:
        print(json.dumps({"ops": sorted(OPS), "usage": "platform_api.py <op> '<json kwargs>'"}, ensure_ascii=False))
        return 2
    kwargs = json.loads(argv[2]) if len(argv) > 2 else {}
    print(json.dumps(OPS[argv[1]](**kwargs), ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
