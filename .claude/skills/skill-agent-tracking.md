---
name: skill-agent-tracking
description: Agent tool 호출 실시간 추적 · subagent dispatch 시 PreToolUse 가 start, PostToolUse 가 end 를 active-agents.json 에 기록. statusline 색표시 (🟢<30s 🟡30-60s 🟠60-180s 🔴180s+). 긴 작업 격리 가시화.
---

# Agent Tracking Skill

## 목적
Subagent (Explore·Plan·general-purpose·code-reviewer 등) dispatch 상태를 statusline 에 실시간 노출.

## 발동
- **PreToolUse Agent** → `.claude/hooks/track-agent-dispatch.sh start` → active-agents.json 에 항목 추가
- **PostToolUse Agent** → `.claude/hooks/track-agent-dispatch.sh end` → end_ts + duration_s 기록

## 색표시 매트릭스 (statusline_context.py)

| duration | 색 | 아이콘 | 의미 |
|---|---|---|---|
| 0~30s | 녹색 | 🟢 | 정상 |
| 30~60s | 노랑 | 🟡 | 보통 |
| 60~180s | 주황 | 🟠 | 긴 작업 |
| 180s+ | 빨강 | 🔴 | 매우 긴 작업 · codex-auto 대체 검토 |

## 입력 JSON 포맷 (hook stdin)

```json
{
  "tool_name": "Agent",
  "tool_input": {
    "subagent_type": "general-purpose",
    "description": "test dispatch"
  }
}
```

## 저장 포맷 (active-agents.json)

```json
[
  {
    "id": "general-purpose",
    "description": "test dispatch",
    "start_ts": "2026-10-13T06:26:11Z",
    "end_ts": null,
    "duration_s": 0
  }
]
```

30초 이상 지난 완료 항목은 hook end 에서 자동 정리.

## 관련
- `.claude/hooks/track-agent-dispatch.sh` (hook · stdin JSON 파싱 + 상태 저장)
- `.claude/scripts/statusline_context.py` L524+ (색표시 로직)
- `.claude/state/active-agents.json` (SoT)
- `.claude/state/agent-model-map.json` (agent → 모델 매핑)
- `.claude/rules/subagent-delegation.md` (dispatch 룰)
