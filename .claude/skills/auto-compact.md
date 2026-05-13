---
name: auto-compact
description: |
  세션 컨텍스트가 무거워지면 자동으로 /compact 를 권장.
  LV12 토큰 절약(이미지 #2 의 LEVEL 12) 자동화.
  Stop hook 마다 턴 카운트·guard.log 라인 수 체크해 임계치 초과 시 알림.
---

# Auto-compact (LV12 토큰 절약 자동 트리거)

## 트리거 조건 (둘 중 하나)

| 신호 | 임계치 (기본) | 의미 |
|---|---|---|
| 턴 수 | `COMPACT_TURN_THRESHOLD` (25) | 대화 길어짐 |
| guard.log 라인 | `COMPACT_GUARD_LINES` (600) | 누적 메타 무거움 |

쿨다운: `COMPACT_COOLDOWN_TURNS` (10) — 한 번 권장 후 N턴 동안 재알림 안 함.

## 동작

1. Stop hook 매번 → `auto-compact-check.sh` 실행
2. 턴 카운터 (`.claude/state/session-turns`) +1
3. 임계치 검사 → 초과 시
   - `.claude/context-cache/auto-compact-recommended` 마커 생성
   - stdout 으로 "/compact 권장" 메시지 (Claude transcript 에 표시)
   - 쿨다운 카운터 갱신

## 환경변수 튜닝

```bash
# 턴 30회마다 권장 (기본 25)
export COMPACT_TURN_THRESHOLD=30

# guard.log 1000줄까지 허용 (기본 600)
export COMPACT_GUARD_LINES=1000

# 쿨다운 5턴 (기본 10)
export COMPACT_COOLDOWN_TURNS=5
```

## 리셋

새 세션 시작이나 `/compact` 직후 카운터 리셋:
```bash
rm -f .claude/state/session-turns .claude/state/auto-compact-cooldown
rm -f .claude/context-cache/auto-compact-recommended
```

(자동 리셋은 SessionStart hook 에 추가하면 됨 — TODO)

## 왜 토큰 기반이 아닌 턴 기반인가

Claude Code 는 hook 의 stdin 으로 토큰 수치를 제공하지 않음 (`token-usage.jsonl` 의 input/output 이 모두 `null` — `hook-token-log.sh:35` 주석 참조). 따라서 turn count 와 guard.log 라인 수를 proxy 로 사용.

토큰 수치가 필요하면:
- `/cost` 출력을 별도 파싱 (수동)
- Anthropic SDK 호출 시 `usage` 응답 직접 누적 (`record_call.py` 활용)

## 이미지 #2 LV12 와의 매핑

LV12 권장사항 → 우리 구현:
- "Plan in chat" → 사용자 책임
- "Build in Cowork" → exec_orch + plugins
- "Batch tasks into one message" → 사용자 책임
- "Restart conversation around message 20" → **이 스킬이 자동화** ✓
- "Trim your context files" → guard.log 자동 tail (stop-snapshot.sh:33)

## 참조

- 호출 hook: `plugins/exec_session_guard/hooks/auto-compact-check.sh`
- 등록: `.claude/settings.json` 의 `Stop` 단계
- 스냅샷 동작: `plugins/exec_session_guard/skills/guard_snapshot.md`
