"""agent_registry.py — Multi-Agent Capability Registry + DAG 실행 (Phase 12 · 2026-10-30).

기존 자산 재사용:
  - Agent 정의 = .claude/agents/*.md frontmatter (name·description·tools·model) + 본문(역할 지시)
  - 실행 = real_repair_chain.dispatch_agent (headless claude -p · invocation=auto)
  - 검증 = runner(pytest) + independent_verifier 는 호출자가 결합

능력(capability)은 Agent 이름을 하드코딩하지 않고 선언된 tools 에서 도출한다:
  read(Read/Grep/Glob) · edit(Edit/Write/MultiEdit) · execute(Bash/PowerShell) · web(WebSearch/WebFetch)
선택 = 필요 능력을 모두 가진 Agent 중 (1) 불필요 권한이 가장 적고 (2) task.skills 와 설명 단어가 많이 겹치는 것.

DAG: depends_on 으로 층(layer) 을 만들고 층 안 작업은 병렬. 실패한 작업의 후속만 skip, 독립 작업은 계속.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
AGENTS_DIR = ROOT / ".claude" / "agents"
LIB = ROOT / ".claude" / "scripts" / "lib"

TOOL_CAPS = {
    "read": {"Read", "Grep", "Glob"},
    "edit": {"Edit", "Write", "MultiEdit"},
    "execute": {"Bash", "PowerShell"},
    "web": {"WebSearch", "WebFetch"},
}
ALL_TOOLS = set().union(*TOOL_CAPS.values())
MODEL_ALIAS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}


def _parse_frontmatter(text: str) -> (Dict[str, str], str):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    meta = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip().strip('"')
    return meta, text[end + 4:].lstrip("-\n")


def load_agents() -> List[Dict[str, Any]]:
    agents = []
    for f in sorted(AGENTS_DIR.glob("*.md")):
        meta, body = _parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
        if not meta.get("name"):
            continue
        tools = ({t.strip() for t in meta["tools"].split(",") if t.strip()}
                 if meta.get("tools") else set(ALL_TOOLS))      # tools 미선언 = 전체 도구
        caps = sorted(c for c, ts in TOOL_CAPS.items() if tools & ts)
        agents.append({"name": meta["name"], "file": f.name, "description": meta.get("description", ""),
                       "tools": sorted(tools), "capabilities": caps,
                       "model": MODEL_ALIAS.get(meta.get("model", ""), meta.get("model") or "claude-opus-5-5"),
                       "body": body.strip()})
    return agents


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9가-힣]+", (text or "").lower()) if len(w) > 1}


def select_agent(needs: List[str], skills: List[str], agents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    cands = [a for a in agents if set(needs) <= set(a["capabilities"])]
    if not cands:
        return None
    want = _words(" ".join(skills))

    def score(a):
        extra = len(set(a["capabilities"]) - set(needs))
        overlap = len(want & _words(a["name"] + " " + a["description"]))
        return (extra, -overlap, a["name"])
    best = sorted(cands, key=score)[0]
    return {**best, "selection": {"extra_caps": score(best)[0], "skill_overlap": -score(best)[1],
                                  "candidates": len(cands)}}


def _layers(tasks: List[Dict[str, Any]]) -> List[List[str]]:
    ids = {t["id"] for t in tasks}
    deps = {t["id"]: set(t.get("depends_on") or []) & ids for t in tasks}
    layers, done = [], set()
    while len(done) < len(ids):
        layer = sorted(i for i in ids - done if deps[i] <= done)
        if not layer:
            raise ValueError(f"cycle in task DAG: {sorted(ids - done)}")
        layers.append(layer)
        done |= set(layer)
    return layers


def _changed_files(cwd: str) -> List[str]:
    import subprocess
    out = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    return [l[3:].strip().strip('"').replace("\\", "/") for l in out.splitlines() if l.strip()]


def run_dag(tasks: List[Dict[str, Any]], cwd: str, max_parallel: int = 3,
            dispatch=None, goal_id: Optional[int] = None) -> Dict[str, Any]:
    """tasks: [{id, needs, skills, depends_on, prompt, allow_paths}] → 결과·선택·병렬 타이밍."""
    sys.path.insert(0, str(LIB))
    if dispatch is None:
        import real_repair_chain as _rc
        dispatch = _rc.dispatch_agent
    agents = load_agents()
    by_id = {t["id"]: t for t in tasks}
    results: Dict[str, Dict[str, Any]] = {}
    before = set(_changed_files(cwd))

    def run_one(tid: str) -> Dict[str, Any]:
        t = by_id[tid]
        failed_deps = [d for d in t.get("depends_on") or [] if results.get(d, {}).get("status") != "ok"]
        if failed_deps:
            return {"status": "skipped", "reason": f"dependency failed: {failed_deps}"}
        ag = select_agent(t.get("needs") or [], t.get("skills") or [], agents)
        if not ag:
            return {"status": "failed", "reason": f"no agent with capabilities {t.get('needs')}"}
        # 권한 = 작업에 필요한 능력의 도구만 (Agent 선언 도구와 교집합) · 셸은 작업이 execute 를 요구할 때만
        tools = sorted(set(ag["tools"]) & set().union(*(TOOL_CAPS[n] for n in t.get("needs") or [])))
        dep_out = "\n".join(f"[{d}] {results[d].get('result', '')[-800:]}" for d in t.get("depends_on") or [])
        prompt = t["prompt"] + (f"\n\nResults of tasks you depend on:\n{dep_out}" if dep_out else "")
        if t.get("allow_paths"):
            prompt += f"\n\nYou may modify only: {', '.join(t['allow_paths'])}."
        started = time.time()
        r = dispatch(prompt, cwd, ag["model"], tools, role=f"dag:{tid}",
                     system_prompt=ag["body"][:6000])
        return {"status": "ok" if r.get("ok") else "failed", "agent": ag["name"],
                "selection": ag["selection"], "tools": tools, "model": ag["model"],
                "agent_session_id": r.get("agent_session_id"), "invocation": r.get("invocation"),
                "cost_usd": r.get("cost_usd"), "started": round(started, 1),
                "ended": round(time.time(), 1), "result": (r.get("result") or "")[-1500:]}

    layers = _layers(tasks)
    for layer in layers:
        with ThreadPoolExecutor(max_workers=max_parallel) as ex:
            futs = {tid: ex.submit(run_one, tid) for tid in layer}
            for tid, f in futs.items():
                try:
                    results[tid] = f.result()
                except Exception as e:
                    results[tid] = {"status": "failed", "reason": f"{type(e).__name__}: {e}"}
    # 작업별 범위 검사 (병렬 작업이 서로의 파일을 건드렸는지)
    changed = sorted(set(_changed_files(cwd)) - before)
    for tid, t in by_id.items():
        if t.get("allow_paths") and results[tid].get("status") == "ok":
            own = [p for p in changed if p in t["allow_paths"]]
            results[tid]["files_changed"] = own
    claimed = {p for t in tasks for p in (t.get("allow_paths") or [])}
    if goal_id:
        _record_tasks(goal_id, tasks, results)
    return {"layers": layers, "results": results, "changed_files": changed,
            "unclaimed_changes": [p for p in changed if p not in claimed]}


def _record_tasks(goal_id: int, tasks: List[Dict[str, Any]], results: Dict[str, Dict[str, Any]]) -> None:
    """DAG 노드를 goal 의 task 로 기록 (선택 Agent·세션·상태 추적)."""
    import sqlite3
    status_map = {"ok": "completed", "failed": "failed", "skipped": "skipped"}
    with sqlite3.connect(str(ROOT / ".claude" / "state" / "orca.db")) as c:
        for seq, t in enumerate(tasks):
            r = results.get(t["id"], {})
            spec = {"kind": "agent", "dag_node": t["id"], "needs": t.get("needs"), "depends_on": t.get("depends_on"),
                    "agent": r.get("agent"), "agent_session_id": r.get("agent_session_id"),
                    "selection": r.get("selection"), "reason": r.get("reason")}
            tid = f"g{goal_id}-dag-{t['id']}"
            c.execute("INSERT OR REPLACE INTO tasks (task_id, task_file, status, created_at, retry_count, worker_id) "
                      "VALUES (?, ?, ?, ?, 0, ?)", (tid, json.dumps(spec, ensure_ascii=False),
                                                    status_map.get(r.get("status"), "failed"), int(time.time()),
                                                    r.get("agent")))
            c.execute("INSERT OR IGNORE INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, ?)",
                      (goal_id, tid, seq))


def _cli(argv):
    if len(argv) >= 2 and argv[1] == "list":
        print(json.dumps([{k: a[k] for k in ("name", "capabilities", "model", "file")} for a in load_agents()],
                         ensure_ascii=False, indent=2))
        return 0
    if len(argv) >= 2 and argv[1] == "select":
        needs = argv[2].split(",") if len(argv) > 2 else []
        skills = argv[3].split(",") if len(argv) > 3 else []
        a = select_agent(needs, skills, load_agents())
        print(json.dumps({k: a[k] for k in ("name", "capabilities", "tools", "selection")} if a else None,
                         ensure_ascii=False, indent=2))
        return 0
    print("usage: agent_registry.py {list|select <needs,csv> [skills,csv]}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv))
