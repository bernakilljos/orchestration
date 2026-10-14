"""track-agent-dispatch.sh 이식 — Agent 도구 호출 시작/종료를 .claude/state/active-agents.json 에 기록.

settings: PreToolUse Agent -> action=start / PostToolUse Agent -> action=end.
디스패처가 event 로 action 을 정해 module.run(ctx) 가 아니라 module.run_action(ctx, action) 을 호출한다.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from _common import Result, project_guard, project_path

AGENT_MODEL_MAP = """{
  "explore": "inherit",
  "plan": "inherit",
  "judge": "claude-haiku-4-5",
  "general-purpose": "inherit",
  "code-reviewer": "inherit",
  "test-runner": "inherit",
  "brainstorming-partner": "inherit",
  "claude": "inherit"
}
"""

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _utcnow() -> datetime:
    # datetime.utcnow() 와 같은 값 (3.12+ 의 DeprecationWarning 회피)
    from datetime import timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


def run_action(ctx, action: str):
    if not project_guard(ctx):
        return None
    state_dir = project_path(ctx, ".claude", "state")
    log_dir = project_path(ctx, ".claude", "logs")
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    state_file = os.path.join(state_dir, "active-agents.json")
    model_map = os.path.join(state_dir, "agent-model-map.json")
    if not os.path.isfile(model_map):
        with open(model_map, "wb") as f:
            f.write(AGENT_MODEL_MAP.encode("utf-8"))
    if not os.path.isfile(state_file):
        with open(state_file, "wb") as f:
            f.write(b"[]\n")

    err_path = os.path.join(log_dir, "track-agent-dispatch.err")

    def _err(msg: str) -> None:
        with open(err_path, "ab") as ef:
            ef.write(msg.encode("utf-8", "replace"))

    # 원본 python 은 HOOK_STDIN 환경변수($(cat) — 끝 개행 제거) 로 입력을 받는다
    raw = ctx.raw.rstrip("\n") or "{}"
    try:
        hook = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        _err(f"[track] json parse: {e}\n")
        return None
    if not isinstance(hook, dict):
        return None
    tool_name = hook.get("tool_name") or hook.get("toolName") or ""
    if tool_name != "Agent":
        return None
    tool_input = hook.get("tool_input") or hook.get("toolInput") or {}
    agent_id = tool_input.get("subagent_type") or tool_input.get("agent_type") or "unknown"
    desc = (tool_input.get("description") or agent_id)[:80]
    ts = _utcnow().strftime(_FMT)

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            agents = json.load(f)
        if not isinstance(agents, list):
            agents = []
    except Exception:
        agents = []

    if action == "start":
        agents = [a for a in agents if not (a.get("id") == agent_id and not a.get("end_ts"))]
        agents.append({"id": agent_id, "description": desc, "start_ts": ts, "end_ts": None, "duration_s": 0})
    elif action == "end":
        for a in agents:
            if a.get("id") == agent_id and not a.get("end_ts"):
                try:
                    start = datetime.strptime(a["start_ts"], _FMT)
                    end = datetime.strptime(ts, _FMT)
                    a["duration_s"] = max(0, int((end - start).total_seconds()))
                except Exception:
                    a["duration_s"] = 0
                a["end_ts"] = ts
                break
        now = datetime.strptime(ts, _FMT)
        kept = []
        for a in agents:
            if a.get("end_ts"):
                try:
                    e = datetime.strptime(a["end_ts"], _FMT)
                    if (now - e).total_seconds() <= 30:
                        kept.append(a)
                except Exception:
                    kept.append(a)
            else:
                kept.append(a)
        agents = kept

    try:
        with open(state_file, "w", encoding="utf-8") as f:  # 텍스트 모드 - 원본과 같은 개행 변환
            json.dump(agents, f, indent=2, ensure_ascii=False)
    except Exception as e:  # 원본: python 예외 -> .err 에 traceback, 훅은 || true
        _err(f"{type(e).__name__}: {e}\n")
    return None


def run(ctx):  # 디스패처는 run_action 을 쓴다 (이 함수는 단독 호출 대비)
    return run_action(ctx, "start")
