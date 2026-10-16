"""서브에이전트 진행 추적 -> .claude/state/active-agents.json (상태줄이 등급별 색으로 그린다).

2026-10-16 재작성 — 종전에는 PostToolUse(Agent) 를 «종료» 로 썼다. 그런데 서브에이전트는 기본이
백그라운드라 PostToolUse 가 «실행 직후» (1초) 에 와서, 실제로 몇 분 도는 에이전트가 1초 만에 끝난 것으로
기록됐고 상태줄에 한 번도 보이지 않았다 (ICM 10-16 실측: pre 10:59:10 / post 10:59:11 · duration_s 1).
또 종류 이름(general-purpose)을 키로 써서 같은 종류를 병렬로 띄우면 1개만 남았다.

지금 (디스패처 action):
  pending  PreToolUse Agent       — 설명·모델을 대기열에 적어 둔다 (시작 신호 아님)
  sub      SubagentStart / Stop   — 실제 시작·종료. 키 = agent_id (병렬 같은 종류도 각각)
등급(모델) 은 시작 시점에 정해 기록한다: tool_input.model > .claude/agents/<type>.md 의 model: > 기본표.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from _common import project_guard, project_path

_FMT = "%Y-%m-%dT%H:%M:%SZ"
PENDING_TTL_S = 600      # 대기열(설명) 은 10분 안에 시작 신호가 와야 짝을 짓는다
ENDED_KEEP_S = 30        # 끝난 항목은 30초만 남긴다
STALE_OPEN_S = 3 * 3600  # 종료 신호를 못 받은 항목(강제 종료 등)은 3시간 뒤 버린다

# agent 정의 파일에 model 이 없을 때의 기본 (내장 에이전트) — inherit = 메인 세션 모델
_BUILTIN_MODEL = {"explore": "inherit", "plan": "inherit", "general-purpose": "inherit",
                  "fork": "inherit", "claude": "inherit", "statusline-setup": "sonnet",
                  "claude-code-guide": "inherit", "judge": "haiku"}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ts(dt: datetime) -> str:
    return dt.strftime(_FMT)


def _parse(s) -> datetime | None:
    try:
        return datetime.strptime(s or "", _FMT)
    except Exception:
        return None


def _first(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v:
            return v
    return ""


def _agent_model(ctx, agent_type: str) -> str:
    """에이전트 정의의 model: 값 (프로젝트 -> 사용자 홈). 없으면 기본표 -> inherit."""
    name = (agent_type or "").split(":")[-1]
    for base in (project_path(ctx, ".claude", "agents"), os.path.join(os.path.expanduser("~"), ".claude", "agents")):
        try:
            for fn in os.listdir(base):
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(base, fn)
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    head = f.read(1500)
                m_name = re.search(r"(?m)^name:\s*['\"]?([\w.:-]+)", head)
                if (m_name.group(1) if m_name else fn[:-3]).lower() != name.lower():
                    continue
                m = re.search(r"(?m)^model:\s*['\"]?([\w.-]+)", head)
                if m:
                    return m.group(1).lower()
        except OSError:
            continue
    return _BUILTIN_MODEL.get(name.lower(), "inherit")


def _load(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(path: str, data) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def run_action(ctx, action: str):
    if not project_guard(ctx):
        return None
    state_dir = project_path(ctx, ".claude", "state")
    os.makedirs(state_dir, exist_ok=True)
    state_file = os.path.join(state_dir, "active-agents.json")
    pending_file = os.path.join(state_dir, "agent-pending.json")
    hook = ctx.payload
    now = _now()

    if action == "pending":  # PreToolUse Agent
        if _first(hook, "tool_name", "toolName") != "Agent":
            return None
        ti = hook.get("tool_input") or {}
        atype = _first(ti, "subagent_type", "agent_type") or "general-purpose"
        pend = [p for p in _load(pending_file)
                if (now - (_parse(p.get("ts")) or now)).total_seconds() <= PENDING_TTL_S]
        pend.append({"type": atype, "description": (ti.get("description") or atype)[:80],
                     "model": (ti.get("model") or "").lower(), "ts": _ts(now)})
        _save(pending_file, pend[-50:])
        return None

    if action != "sub":
        return None
    event = _first(hook, "hook_event_name")
    agent_id = str(_first(hook, "agent_id", "subagent_id", "agentId") or "")
    atype = _first(hook, "agent_type", "subagent_type") or "unknown"
    # 진단용 — 실제 페이로드 필드 확인 (1건만 덮어씀)
    try:
        with open(os.path.join(state_dir, "subagent-last-payload.json"), "w", encoding="utf-8") as f:
            json.dump({k: (v if not isinstance(v, str) else v[:200]) for k, v in hook.items()}, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    agents = _load(state_file)

    if event == "SubagentStart":
        pend = _load(pending_file)
        desc, model = atype, ""
        for i, p in enumerate(pend):  # 같은 종류 중 가장 오래된 대기 1건과 짝
            if p.get("type", "").lower() == atype.lower():
                desc, model = p.get("description") or atype, p.get("model") or ""
                del pend[i]
                break
        _save(pending_file, pend)
        # 서브에이전트 기록 파일 = <메인 transcript 폴더>/<session_id>/subagents/agent-<agent_id>.jsonl
        #   상태줄이 여기서 토큰·도구 수·마지막 동작을 읽는다 (실측: ICM ca10a4b1 세션)
        tp, sid = hook.get("transcript_path") or "", hook.get("session_id") or ""
        sub_tp = os.path.join(os.path.dirname(tp), sid, "subagents", f"agent-{agent_id}.jsonl") if tp and sid and agent_id else ""
        agents.append({"id": agent_id or f"{atype}-{_ts(now)}", "type": atype, "description": desc,
                       "model": model or _agent_model(ctx, atype), "transcript": sub_tp,
                       "start_ts": _ts(now), "end_ts": None, "duration_s": 0})
    elif event == "SubagentStop":
        hit = None
        for a in agents:
            if not a.get("end_ts") and agent_id and a.get("id") == agent_id:
                hit = a
                break
        if hit is None:  # id 를 못 받은 경우: 같은 종류 중 가장 오래 열린 것
            opens = [a for a in agents if not a.get("end_ts") and a.get("type", "").lower() == atype.lower()]
            hit = opens[0] if opens else None
        if hit is not None:
            st = _parse(hit.get("start_ts")) or now
            hit["end_ts"] = _ts(now)
            hit["duration_s"] = max(0, int((now - st).total_seconds()))
    else:
        return None

    kept = []
    for a in agents:
        ref = _parse(a.get("end_ts")) if a.get("end_ts") else _parse(a.get("start_ts"))
        age = (now - (ref or now)).total_seconds()
        if a.get("end_ts") and age > ENDED_KEEP_S:
            continue
        if not a.get("end_ts") and age > STALE_OPEN_S:
            continue
        kept.append(a)
    try:
        _save(state_file, kept)
    except Exception as e:
        with open(os.path.join(project_path(ctx, ".claude", "logs"), "track-agent-dispatch.err"), "ab") as ef:
            ef.write(f"{type(e).__name__}: {e}\n".encode("utf-8", "replace"))
    return None


def run(ctx):  # 단독 호출 대비 (디스패처는 run_action)
    return run_action(ctx, "sub")
