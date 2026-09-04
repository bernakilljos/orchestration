---
description: "Gemini 로 세션·대화·문서 요약 생성 (저단가·1M 컨텍스트)"
allowed-tools: Bash(bash:*), Read
---

## Context

- 인자: `$ARGUMENTS` (예: `--session <id>`, `--pdf <path>`, `--turns 20`)
- 최근 Gemini 헬스체크: !`bash .claude/scripts/orca-status.sh 2>/dev/null | grep -A1 heartbeat || echo "orca 미초기화"`

## Your task

Gemini 워커에게 요약 위임. **Claude 가 직접 하지 말 것** — 비용 절감 목적.

### 기본 흐름

1. 입력 결정:
   - 인자 없음 → 현재 세션 최근 20턴
   - `--session <id>` → 해당 세션 로그
   - `--pdf <path>` → PDF 내용
   - `--turns <N>` → 최근 N턴
2. task-instruction.md 작성 (요약 요청):
   ```
   target: 요약 대상
   role: Gemini
   format: recap (2-3줄) / detailed (10-15줄) 택 1
   output: .claude/state/recap.jsonl 에 append
   ```
3. `orca-dispatch task.md gemini` 또는 직접 `gemini-a --verify task.md`
4. 결과를 `.claude/state/recap.jsonl` 에 append:
   ```jsonl
   {"ts":"2026-04-19T15:00Z","type":"session","source":"...","summary":"...","tokens":N,"cost_usd":0.01}
   ```
5. 사용자에게 recap 한 줄로 보고

### 언제 Gemini 사용 (경계)

| 작업 | Gemini | Claude 직접 |
|---|:---:|:---:|
| recap 2-3줄 |  |  (오버헤드 > 절감) |
| 세션 전체 요약 |  |  |
| 긴 PDF (>10쪽) |  |  |
| 대화 로그 분석 |  |  |
| 코드 리뷰 요약 |  |  |

### 금지

- Gemini 워커 미가용 시 Claude 대행 금지 (의도와 충돌) — `exec_status` 로 가용성 먼저 확인
- 출력을 Claude 가 재작성 금지 (Gemini 원본 유지)

## 참조

- `plugins/exec_orch/skills/route_dispatch.md § Step 2.5`
- `.claude/scripts/orca-status.sh`
