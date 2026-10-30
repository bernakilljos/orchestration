"""ops_metrics.py — 운영 관측성 집계 (Phase 15 · 2026-10-30 · 읽기 전용).

기존 기록만 읽는다 (새 기록 경로 X):
  orca-10min-loop.log (scheduler tick) · goals/goal_transitions · self_heal_events · agent_dag_runs ·
  executions · metrics(비용·토큰) · judge-queue · repair_sandbox state/예약 · 디스크.
측정 근거가 없으면 0 이 아니라 "UNKNOWN" (헌장: 미측정 ≠ 정상).
"""
from __future__ import annotations
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
LOOP_LOG = ROOT / ".claude" / "logs" / "orca-10min-loop.log"
UNKNOWN = "UNKNOWN"


def _rate(num: int, den: int):
    return round(num / den, 3) if den else UNKNOWN


def _q(c, sql, args=()):
    try:
        return c.execute(sql, args).fetchall()
    except sqlite3.Error:
        return None


def scheduler(since: float) -> Dict[str, Any]:
    """loop START 마다 END 가 있는가 (= tick 완주) · self-heal tick rc 분포."""
    if not LOOP_LOG.exists():
        return {"status": UNKNOWN, "reason": "loop log 없음"}
    starts = ends = 0
    start_ts = []
    interval_s = 600            # Orca_10MinLoop 주기
    heal_rc: Dict[str, int] = {}
    pat = re.compile(r"^\[(\d{4}-\d\d-\d\dT[\d:.]+)\]")
    for line in LOOP_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.match(line)
        if not m:
            continue
        try:
            ts = time.mktime(time.strptime(m.group(1)[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            continue
        if ts < since:
            continue
        if "10-Min Loop START" in line:
            starts += 1
            start_ts.append(ts)
        elif "10-Min Loop END" in line:
            ends += 1
        elif "self-heal tick rc=" in line:
            rc = line.split("self-heal tick rc=")[1].split(":")[0]
            heal_rc[rc] = heal_rc.get(rc, 0) + 1
    # 실제 실패 (START 후 END 없음) 와 미실행 공백 (PC 꺼짐·절전 · 주기×1.5 초과 간격) 을 분리
    gaps = [b - a for a, b in zip(start_ts, start_ts[1:]) if b - a > interval_s * 1.5]
    span = (start_ts[-1] - start_ts[0]) if len(start_ts) > 1 else 0
    return {"ticks_started": starts, "ticks_completed": ends, "tick_failures": max(starts - ends, 0),
            "tick_success_rate": _rate(ends, starts),
            "observed_span_h": round(span / 3600, 2) if span else UNKNOWN,
            "expected_ticks_in_span": int(span // interval_s) + 1 if span else UNKNOWN,
            "coverage": _rate(starts, int(span // interval_s) + 1) if span else UNKNOWN,
            "idle_gaps": len(gaps), "idle_gap_max_min": round(max(gaps) / 60) if gaps else 0,
            "self_heal_tick_rc": heal_rc or UNKNOWN}


def report(window_h: float = 24) -> Dict[str, Any]:
    since = time.time() - window_h * 3600
    out: Dict[str, Any] = {"window_h": window_h, "generated_at": int(time.time()), "scheduler": scheduler(since)}
    if not DB.exists():
        out["db"] = UNKNOWN
        return out
    c = sqlite3.connect(str(DB))
    # goals (기간 안 생성) · 상태 분포 · 복구율
    rows = _q(c, "SELECT status, workflow_type, COUNT(*) FROM goals WHERE created_at>=? GROUP BY 1,2", (since,))
    dist: Dict[str, int] = {}
    for st, wf, n in rows or []:
        dist[st] = dist.get(st, 0) + n
    repair = _q(c, "SELECT status, COUNT(*) FROM goals WHERE workflow_type='REPAIR' AND created_at>=? GROUP BY 1", (since,))
    rep = dict(repair or [])
    rep_done = rep.get("VERIFIED", 0) + rep.get("FAILED", 0)
    out["goals"] = {"by_status": dist or UNKNOWN, "repair_goals": rep or UNKNOWN,
                    "repair_success_rate": _rate(rep.get("VERIFIED", 0), rep_done)}
    # self-heal 이벤트
    ev = _q(c, "SELECT status, attempts, trigger_source FROM self_heal_events WHERE created_at>=?", (since,))
    if ev is None or not ev:
        out["self_heal"] = {"events": 0 if ev is not None else UNKNOWN, "success_rate": UNKNOWN}
    else:
        fin = [e for e in ev if e[0] in ("repaired", "failed", "blocked")]
        out["self_heal"] = {"events": len(ev), "by_status": {s: sum(1 for e in ev if e[0] == s) for s in {e[0] for e in ev}},
                            "by_trigger": {t: sum(1 for e in ev if e[2] == t) for t in {e[2] for e in ev}},
                            "success_rate": _rate(sum(1 for e in fin if e[0] == "repaired"), len(fin)),
                            "avg_attempts": round(sum(e[1] or 0 for e in ev) / len(ev), 2)}
    # Agent DAG (Agent 별 성공률은 tasks.worker_id = 선택 Agent)
    dag = _q(c, "SELECT metrics FROM agent_dag_runs WHERE created_at>=?", (since,))
    per_agent = _q(c, "SELECT worker_id, status, COUNT(*) FROM tasks WHERE task_id LIKE 'g%-dag-%' "
                      "AND created_at>=? AND worker_id IS NOT NULL GROUP BY 1,2", (since,))
    agents: Dict[str, Dict[str, int]] = {}
    for w, st, n in per_agent or []:
        agents.setdefault(w, {})[st] = n
    runs = [json.loads(r[0]) for r in dag or []]
    out["agents"] = {"dag_runs": len(runs) if dag is not None else UNKNOWN,
                     "dag_cost_usd": round(sum(r.get("cost_usd", 0) for r in runs), 4) if runs else UNKNOWN,
                     "dag_success_rate": _rate(sum(r.get("ok", 0) for r in runs), sum(r.get("nodes", 0) for r in runs)),
                     "per_agent": {a: {**v, "success_rate": _rate(v.get("completed", 0), sum(v.values()))}
                                   for a, v in agents.items()} or UNKNOWN,
                     "max_parallel_observed": max((r.get("max_wave", 0) for r in runs), default=UNKNOWN)}
    # 실행·검증
    ex = _q(c, "SELECT exit_code, verified, duration_ms FROM executions WHERE started_at>=?", (since,))
    if ex:
        durs = sorted(e[2] for e in ex if e[2] is not None)
        out["executions"] = {"count": len(ex), "exit0_rate": _rate(sum(1 for e in ex if e[0] == 0), len(ex)),
                             "verified": sum(1 for e in ex if e[1]),
                             "p50_ms": durs[len(durs) // 2] if durs else UNKNOWN,
                             "p95_ms": durs[int(len(durs) * 0.95) - 1] if durs else UNKNOWN}
    else:
        out["executions"] = {"count": 0 if ex is not None else UNKNOWN}
    # 토큰·비용 (metrics 기록분만 · Agent headless 비용은 dag_cost/self-heal evidence 에 별도)
    mt = _q(c, "SELECT ai, SUM(tokens_in), SUM(tokens_out), SUM(cost_usd), COUNT(*) FROM metrics "
               "WHERE recorded_at>=? GROUP BY ai", (since,))
    # 호출은 있는데 토큰 합 0 = 기록 안 된 것 → UNKNOWN (0 으로 위장 X)
    out["tokens_cost"] = {r[0]: {"tokens_in": r[1] if (r[1] or r[2]) else UNKNOWN,
                                 "tokens_out": r[2] if (r[1] or r[2]) else UNKNOWN,
                                 "cost_usd": round(r[3], 4) if r[3] else UNKNOWN, "calls": r[4]}
                          for r in mt} if mt else UNKNOWN
    # Judge 결과 (judge-queue 최종 판정)
    jq = ROOT / ".claude" / "state" / "judge-queue"
    finals: Dict[str, int] = {}
    if jq.exists():
        for f in jq.glob("goal-*.json"):
            if f.stat().st_mtime < since:
                continue
            try:
                st = (json.loads(f.read_text(encoding="utf-8")).get("final_verdict") or {}).get("status")
            except Exception:
                st = None
            finals[st or "pending"] = finals.get(st or "pending", 0) + 1
    out["judge"] = finals or UNKNOWN
    # 자원
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    try:
        import repair_sandbox as sb
        st = sb._load_state()
        life: Dict[str, int] = {}
        for e in st.values():
            k = sb.lifecycle(e)
            life[k] = life.get(k, 0) + 1
        act = [e for e in st.values() if sb.lifecycle(e) == "ACTIVE"]
        active_bytes = sum(int(e["est_bytes"]) for e in act if e.get("est_bytes")) if act else 0
        unknown_size = sum(1 for e in act if not e.get("est_bytes"))     # 정책 도입 전 생성분
        out["resources"] = {"disk_free_gb": round(shutil.disk_usage(str(ROOT)).free / 1024 ** 3, 2),
                            "sandbox_lifecycle": life or UNKNOWN,
                            "active_sandbox_est_gb": round(active_bytes / 1024 ** 3, 3) if not unknown_size
                            else f"{round(active_bytes / 1024 ** 3, 3)} + UNKNOWN×{unknown_size}",
                            "reservations_live": len(sb._live_reservations()),
                            "policy": {k: v for k, v in sb._policy().items() if not k.startswith("_")}}
    except Exception as e:
        out["resources"] = {"status": UNKNOWN, "reason": str(e)[:120]}
    # 추적 ID: 최근 실패·복구 연결 (원 goal → event → repair goal → agent/judge 세션)
    tr = _q(c, "SELECT event_id, goal_id, status, repair_goal_id, result FROM self_heal_events "
               "WHERE created_at>=? ORDER BY event_id DESC LIMIT 5", (since,))
    out["recent_recovery_traces"] = [
        {"event_id": t[0], "goal_id": t[1], "status": t[2], "repair_goal_id": t[3],
         **{k: (json.loads(t[4]) if t[4] else {}).get(k) for k in ("agent_sessions", "judge_session", "final_verdict")}}
        for t in tr or []] or UNKNOWN
    return out


if __name__ == "__main__":
    h = float(sys.argv[sys.argv.index("--window-h") + 1]) if "--window-h" in sys.argv else 24
    print(json.dumps(report(h), ensure_ascii=False, indent=2))
