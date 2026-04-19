# skill-token-tracker — 세션별 토큰 소비 추적

> **분류**: `exec_session_guard`
> **의존**: `.claude/state/token-usage.jsonl`
> **기록 주체**: SessionEnd 훅 또는 수동 호출

## Purpose

Claude Code 세션당 토큰 사용량을 영구 로깅해서:
- 어떤 작업이 토큰을 많이 먹었는지 사후 분석
- 모델별 비용 비교 (Opus vs Sonnet vs Haiku)
- 월간 비용 추정 (예산 관리)

## 저장 경로

`.claude/state/token-usage.jsonl` — JSON Lines 형식 (append-only)

```jsonl
{"ts":"2026-04-19T15:30Z","session":"abc123","model":"claude-opus-4-7","input":45000,"output":12000,"cache_read":20000,"cache_write":5000,"est_cost_usd":0.87}
{"ts":"2026-04-19T16:45Z","session":"def456","model":"claude-sonnet-4-6","input":30000,"output":8000,"cache_read":10000,"cache_write":0,"est_cost_usd":0.12}
```

## 기록 방법

Claude Code는 네이티브로 세션 토큰을 export 하지 않음. 수동 방법:

### 옵션 A: `/cost` 커맨드 결과 수집
Claude Code 내장 `/cost` 또는 `/usage` 출력을 SessionEnd 훅이 파싱.

### 옵션 B: API 직접 계산
`.claude/logs/*.jsonl` (대화 기록) 에서 메시지 토큰 근사치 계산:
- input ≈ user prompt + 컨텍스트 (tiktoken)
- output ≈ assistant 응답 (tiktoken)

### 옵션 C: `exec_orch` 훅으로 tool use 단위 추적
각 tool_use 이벤트에서 추정치 append.

## 단가 테이블 (2026-04 기준)

| 모델 | Input ($/M) | Output ($/M) | Cache read | Cache write |
|------|-------------|--------------|------------|-------------|
| claude-opus-4-7 | 15 | 75 | 1.5 | 18.75 |
| claude-sonnet-4-6 | 3 | 15 | 0.3 | 3.75 |
| claude-haiku-4-5 | 1 | 5 | 0.1 | 1.25 |

## 통계 커맨드 (예정)

```
/token-stats            이번 달 총 비용 + 모델별 분포
/token-stats --today    오늘 세션
/token-stats --top      비용 상위 5개 세션
```

구현: `plugins/exec_session_guard/commands/token-stats.md`

## 구현 상태

- ✅ 스펙 정의 (이 파일)
- 📝 `.claude/state/token-usage.jsonl` 파일 초기화
- 📝 SessionEnd 훅에서 `/cost` 파싱 (플랫폼별 차이 있음)
- 📝 `/token-stats` 커맨드

**실구현은 install 후 플랫폼에서 — Claude Code 버전별 /cost 출력 형식이 다를 수 있음.**
