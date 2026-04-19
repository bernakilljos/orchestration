---
description: "플러그인 도움말 — /help 또는 /help <plugin>"
allowed-tools: Bash(cat:*), Bash(ls:*), Read
---

## Context

- 플러그인 목록: !`ls plugins/ | grep -v "^_"`
- 인자(있으면): `$ARGUMENTS`

## Your task

### 인자 없음 (`/help`)
전체 플러그인 리스트 + 각각의 한 줄 설명 출력.
데이터 소스: `.claude-plugin/plugin.json` 의 `plugins` 섹션 + 각 `plugins/<name>/plugin.json` 의 `display`.

포맷:
```
[Phase 0 완성]
exec_orch          — 멀티AI 오케스트레이션 엔진 (코어)
exec_learning      — 세션 학습·실패 패턴 축적
...

[Phase 1 스펙]
exec_scheduler     — 크론 잡 (spec-only)
...
```

### 인자 있음 (`/help <plugin>`)
해당 플러그인의 README.md 전체 출력. 없으면 plugin.json + 커맨드 목록 fallback.

### 특수 (`/help --roadmap`)
`docs/2026-04-19/로드맵.md` 요약 표시.
