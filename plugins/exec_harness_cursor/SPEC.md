# exec_harness_cursor (spec-only)

> **목적**: orchestration_v1 task 를 Cursor Composer 에 위임 — Claude Code CLI ↔ Cursor IDE multi-harness.
> **근거**: `docs/2026-06-16/tooling-comparison.md` § ⭐⭐ wshobson/agents multi-harness 패턴.
> **상태**: spec-only — 사용자 진행 결정 후 stable 로 승격.

## 활용 시점

- 사용자가 IDE 안에서 시각적 step-by-step refactor 필요
- Claude Code CLI 가 fail 한 복잡 frontend 작업 (Cursor Composer 의 iterative 강점)
- 사용자가 Cursor 구독 중일 때 비용 효율

## 명령 (예정)

| 명령 | 동작 |
|---|---|
| `/cursor-dispatch <task>` | task-instruction.md → Cursor MCP server 로 전달 |
| `/cursor-review <pr>` | PR diff 를 Cursor 에 띄움 |
| `/cursor-status` | Cursor 세션 활성 여부 |

## 의존성

- `exec_orch` (task-instruction 표준)
- Cursor IDE 설치 + API key (`CURSOR_API_KEY`)
- Cursor MCP server (검증 필요 — 2026-06 기준 공식 X)

## 미해결 (사용자 결정)

1. Cursor 공식 MCP 가 아직 없으면 우리 wrapper 가 file-based bridge 또는 deeplink 사용
2. Cursor API key 비용 정책 (Pro $20/m + 변동 API)
3. 우리 라우팅 표 (CLAUDE.md § 3.2) 에 Cursor 행 추가 여부

## 다음 단계

- 사용자가 활성화 결정 시:
  1. status → `experimental`
  2. commands/ + skills/ 구현
  3. Cursor MCP/API 검증
  4. CLAUDE.md § 3.2 라우팅 표에 행 추가
