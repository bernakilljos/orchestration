"""log-subagent.sh 이식 — SubagentStart/Stop 을 .claude/logs/subagent.log 에 기록, Stop 은 metrics DB 에도.

종전 .sh 는 jq 로 필드를 읽었는데 이 PC 에 jq 가 없어 10-14 이후 모든 줄이 «? | id=? type=?» 였다.
디스패처 표에서 track_agent_dispatch 다음에 돈다 → 소요 시간은 그 모듈이 적은 active-agents.json 에서 읽는다.
"""
from __future__ import annotations

import json
import os
import subprocess
import time

from _common import project_path


def run(ctx):
    hook = ctx.payload
    event = hook.get("hook_event_name") or "unknown"
    if event not in ("SubagentStart", "SubagentStop"):
        return None
    aid = str(hook.get("agent_id") or hook.get("subagent_id") or "?")
    atype = hook.get("agent_type") or hook.get("subagent_type") or "?"
    dur_ms = 0
    try:
        with open(project_path(ctx, ".claude", "state", "active-agents.json"), "r", encoding="utf-8") as f:
            for a in json.load(f):
                if a.get("id") == aid and a.get("end_ts"):
                    dur_ms = int(a.get("duration_s") or 0) * 1000
    except Exception:
        pass
    logs = project_path(ctx, ".claude", "logs")
    os.makedirs(logs, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(logs, "subagent.log"), "ab") as f:
        f.write(f"[{ts}] {event} | id={aid} type={atype} duration={dur_ms}ms\n".encode("utf-8", "replace"))
    rec = project_path(ctx, ".claude", "scripts", "lib", "record_call.py")
    if event == "SubagentStop" and os.path.isfile(rec):
        kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
        try:  # 기다리지 않는다 (훅 지연 방지) — 원본도 실패를 무시했다
            subprocess.Popen(["python", rec, "--ai", "claude", "--model", f"subagent-{atype}",
                              "--tokens-in", "0", "--tokens-out", "0", "--latency-ms", str(dur_ms),
                              "--success", "1", "--task-id", f"subagent-{aid}"],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
        except Exception:
            pass
    return None
