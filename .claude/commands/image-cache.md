---
description: "이미지 캐시 관리 — list / stats / clean"
allowed-tools: Bash(python:*)
---

## Context

캐시 통계:
!`PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/lib/pollinations_client.py" --stats`

## Your task

입력 `$ARGUMENTS`:
- 비었거나 `list` → 최근 20개 list
- `stats` → 통계만 (위 Context 에 이미)
- `clean <days>` → N일+ 캐시 삭제

기본 동작:
```bash
PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/lib/pollinations_client.py" --list
```

## 위치

- 이미지: `docs/screens/custom/<keyword>-<hash>.jpg`
- 메타: `.claude/state/image-cache/<keyword>-<hash>.json`
- 자동 정리: cleanup-pollution.sh (image-cache *.json 7일+)
