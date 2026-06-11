---
name: route_dispatch
description: |
  태스크를 Claude Opus 4.8 우선으로 자동 라우팅. SQLite 상태 기반으로 Codex/Gemini 대체 경로 선택. 24/7 quota/budget 관리.
---

# route_dispatch — AI 라우팅 · 판단 (v2 Opus 4.8 우선)

> **분류:** `route_` (라우팅/판단 계열)
> **변경점 (4.8 시대)**: Claude Opus 4.8 기본값 + extended thinking + prompt caching + SQLite quota
> **참조 plugin:** `.claude-plugin/plugin.json` → `entry_points.task_route`

## 목적

1M 컨텍스트 + extended thinking + prompt caching으로 Claude Opus 4.8이 단독 최적화 달성.
Codex/Gemini는 특정 조건(quota소진, 1M 초과)에서만 호출. 사용자에게 AI 선택 묻지 않음.

---

## Step 1: 사전 조건 확인 (Budget + Quota)

모든 라우팅 결정 전에 **SQLite 상태 확인**:

```bash
# .claude/state/metrics.db 조회
sqlite3 .claude/state/metrics.db "SELECT * FROM budget WHERE id='daily'"
# Output: breaker_tripped=0 → 정상, 1 → 신규 태스크 대기

sqlite3 .claude/state/metrics.db "SELECT quota_exceeded FROM quota WHERE ai='claude_opus'"
# Output: 0 → 정상, 1 → fallback 경로로
```

**IF breaker_tripped=1**: 신규 태스크 시작 금지 (진행 중 태스크만 마무리).
**IF quota exceeded**: 해당 AI 스킵, 다음 우선순위로.

---

## Step 2: 태스크 특성 판단 (자동 분류)

입력 분석 — 다음 중 하나 이상 포함 시:

| 신호 | 분류 | 라우팅 |
|------|------|--------|
| "설계", "아키텍처", "리팩토링", "왜", "어떻게" | **DESIGN** | Opus 4.8 + thinking |
| 3개 이상 파일 걸친 작업 | **LARGE_SCOPE** | Opus 4.8 + 1M context |
| "애매", "결정", "트레이드오프", "비교" | **DECISION** | Opus 4.8 + thinking |
| 재시도 (retry_count > 0) | **RETRY** | Opus 4.8 재분석 |
| **Opus 4.8 가 같은 task 2회 fail** | **MYTHOS** | **Fable 5 (/effort mythos)** |
| **"fable 5", "mythos", "최고 모델"** | **MYTHOS** | **Fable 5 직통** |
| **Dynamic Workflows orchestrator (수십~수백 subagent)** | **MYTHOS** | **Fable 5** |
| **8h+ long-running autonomy / vision-heavy** | **MYTHOS** | **Fable 5** |
| <200줄 구현, 버그 수정 | **SMALL** | Sonnet 4.6 또는 Haiku 4.5 |
| 검증·리뷰·요약 | **VERIFY** | Haiku 4.5 (기본) |
| 1M+ 문서 리서치 | **RESEARCH** | Gemini 2.0 Flash |

---

## Step 3: 라우팅 결정 (우선순위 순)

```text
IF budget.breaker_tripped:
  WAIT (다음 주기까지)

IF MYTHOS:
  # Path 2 자동 승격 또는 사용자 명시
  result = check_fable_gate()  # route.py --check claude-fable-5
  IF result.ok:
    IF estimated_cost_usd >= 5.0:
      ASK USER (cost critical CLAUDE.md § 7-11)
    CLAUDE_FABLE_5 + /effort mythos
  ELIF result.fable_ok == 0:  # 20% cap 도달
    NOTIFY user (cost critical) → fallback CLAUDE_OPUS_4_8
  ELSE:
    fallback CLAUDE_OPUS_4_8 (quota/budget 차단)

IF DESIGN OR DECISION:
  CLAUDE_OPUS_4_8 + thinking(budget_tokens: 8000)
  + prompt_caching(system + CLAUDE.md + route_dispatch 3줄)

IF LARGE_SCOPE AND token_estimate < 800k:
  CLAUDE_OPUS_4_8 (1M context 활용, thinking 선택)

IF token_estimate >= 800k (프로젝트 분할 필요):
  IF quota.codex_ok:
    task-instruction.md → codex-auto (병렬 4개)
    THEN Opus 4.8 보완
    THEN Haiku 4.5 검증
  ELIF quota.gemini_ok:
    Gemini 2.0 Flash (1M+ 네이티브)
    THEN Opus 4.8 최종 검증
  ELSE:
    WAIT (quota backoff)

IF VERIFY:
  IF quota.haiku_ok:
    CLAUDE_HAIKU_4_5 (검증 기본자)
    IF fail: → Opus 4.8 재검증
  ELIF quota.gemini_ok AND token_estimate >= 500k:
    Gemini (초장문 검증)
  ELSE:
    Opus 4.8 fallback

IF RESEARCH (1M+ 리서치):
  IF quota.gemini_ok:
    Gemini 2.0 Flash (네이티브 1M)
  ELSE:
    Opus 4.8 (800k 제한, 2회 분할)

IF SMALL:
  IF quota.sonnet_ok:
    Claude Sonnet 4.6
  ELSE:
    Haiku 4.5
  THEN Haiku 4.5 기본 검증

DEFAULT (ambiguous):
  CLAUDE_OPUS_4_8 (판단 역할)
```

---

## Step 4: Extended Thinking 자동 활성화

다음 조건 중 하나라도 맞으면 `budget_tokens: 8000` 설정:

- 태스크 타입 = DESIGN, DECISION, RETRY
- 파일 3개 이상 동시 분석
- 이전 Sonnet/Haiku 시도 실패
- 설명에 "복잡", "엣지케이스", "성능 최적화" 포함

**절대 금지**: 단순 템플릿 채우기, 한 파일 1줄 수정에 thinking 켜기.

---

## Step 5: Prompt Caching 전략

**3단계 캐시**:

1. **System Block** (5분 TTL, ephemeral):
   - System prompt + CLAUDE.md + route_dispatch 이 파일
   - 모든 Claude 호출에서 재사용 (quota 관점 90% 절감)

2. **Project Context** (1시간 TTL):
   - 프로젝트 구조 (plugin.json, SPEC.md, 핵심 파일)
   - DESIGN/LARGE_SCOPE 태스크에서 재사용

3. **Session State** (3시간 TTL):
   - quota 상태, SQLite 메트릭, 워커 heartbeat
   - 모든 라우팅 재계산 전 새로고침

**비용 계산**: cache_hit / cache_write / cache_read 분리 기록 (metrics.db `cache_stats` 테이블).

---

## Step 6: 24/7 자동화 규칙 (Orca Auto)

### Heartbeat (모든 워커)

- 5분마다 `.claude/state/workers.db` → `workers` 테이블 갱신
- `session` 테이블: Claude Code 세션 heartbeat
- Stale 감지 (5분 이상 갱신 없음): 워커 자동 종료 (orphan 방지)

### Quota Backoff (지수 대기)

한도 도달 시:
```text
1차 재시도: 10분 대기
2차: 20분
3차: 40분
4차+: 2시간 cap
```

플래그 파일: `.claude/state/quota-backoff.json` (ai, backoff_until_epoch)

### Budget Breaker

일일 비용 한도 도달 시:
```text
budget.breaker_tripped = 1  → `.claude/state/budget.json`
신규 태스크 시작 금지
진행 중 태스크 마무리 허용
자정 UTC에 자동 reset
```

---

## Step 7: 금지 사항 (4.8 시대 업데이트)

1. **사용자에게 AI 묻지 않기** — 자동 결정
2. **Thinking 낭비** — 단순 작업에 켜기 금지
3. **task-instruction.md 없이 Codex 호출** — 필수 조건
4. **한도 상황에서 task done/ 이동** — 절대 금지 (진도 위장)
5. **SQLite 무시하고 파일 플래그만 보기** — 항상 DB 먼저 확인
6. **Prompt caching 없이 Claude API 호출** — 정책 위반
7. **Codex/Gemini 리뷰 자동 승인** — Claude 승인 필수

---

## Step 8: 기존 호환성 (Fallback)

- `codex-auto.bat`, `gemini-auto.bat` 워커 시스템 유지
- `task-instruction.md` 포맷 그대로
- `.claude/tasks/` 구조 유지
- **변경점 only**: 라우팅 "결정" 먼저 Opus 4.8로 기울임

### 원래 경로 대비 변경

| 상황 | v1 (4.6 이전) | v2 (4.8+) |
|------|-------------|----------|
| SMALL | Claude (Sonnet) | Sonnet 또는 Haiku (Thinking 불필요) |
| LARGE | Codex 4개 병렬 | Opus 1M context (Codex는 800k 초과 또는 Opus quota 소진 시만) |
| DESIGN | Claude (Opus) | **Opus + thinking (자동)** |
| VERIFY | Gemini | **Haiku 기본 → 실패 시 Opus** |

---

## 참조

- Quota 감시: `.claude/state/quota-check.sh`
- Budget 관리: `.claude/state/budget-guard.sh`
- Worker heartbeat: `.claude/scripts/worker-health.py`
- Extended thinking 가이드: `docs/upgrade-analysis-2026-04-19.md`
- Prompt caching 전략: `docs/architecture-patterns.md` § 패턴 3
