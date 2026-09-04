---
description: Mythos-class 모드 활성 — Claude Fable 5 직통 (Opus 4.8 2배 비용·일일 budget 20% 게이트)
allowed-tools: Bash(python:*), Read, Edit
---

# /effort mythos — Fable 5 Mythos-class 모드

> **근거**: `~/.claude/projects/.../memory/project_fable_5_usage_strategy.md` · CLAUDE.md § 3.2 Mythos-class 행.
> **비용 주의**: Fable 5 = $10/$50 per MTok (Opus 4.8 **2배**). 단발 $5+ 예상 시 사전 알림 필수.

## 트리거

다음 한 경우만 실행:
- 사용자가 `/effort mythos` 명시
- 사용자가 "fable 5 로 해줘" / "mythos 로" / "최고 모델로" 명시
- Opus 4.8 가 동일 task 2회 fail (post-codex-verify hallucination 또는 INCONCLUSIVE) → auto-planner Path 2 자동 승격

## 동작

```bash
# 1. 예산·quota 게이트 확인 (route.py)
python .claude/scripts/route.py --check claude-fable-5
# Output: quota_ok=1 budget_ok=1 fable_ok=1 fable_spent=$X.XX fable_cap=$Y.YY
# exit 0 = OK / exit 1 = 차단

# 2. 차단 시 자동 fallback
#  - quota_ok=0 → Opus 4.8 로 자동 fallback
#  - fable_ok=0 (일일 20% cap 도달) → Opus 4.8 로 자동 fallback + 사용자 알림 (cost critical)
#  - budget_ok=0 → 일일 budget 초과 → 모든 호출 차단

# 3. OK 시 Fable 5 호출
#  model = claude-fable-5
#  context = 1M (Opus 동일)
#  output max = 128k
#  단가 = $10 in / $50 out per MTok

# 4. 자동 차단 영역 (Anthropic side)
#  cybersecurity / biology / chemistry / distillation 키워드 → Opus 4.8 자동 fallback
#  → 우리 kit 에서 별도 처리 X, 결과만 받음
#  → 로그 (.claude/logs/mythos-fallback.log) 에 기록
```

## 적용 대상 (Yes / No)

| 작업 | Mythos 사용? | 이유 |
|---|---|---|
| 초난도 시스템 redesign |  | Opus 4.8 가 fail 한 경우 |
| Dynamic Workflows orchestrator (수십~수백 subagent) |  | Fable 5 의 강점 |
| 8h+ long-running autonomy |  | hallucination 위험 감소 |
| Vision-heavy 산출물 검증 |  | SOTA vision |
| 일반 설계 / 추론 |  | Opus 4.8 충분 |
| 단순 구현 <200줄 |  | Sonnet 4.6 |
| 코드 500줄+ 병렬 |  | Codex ×4 |
| 검증 / 리뷰 |  | Haiku 4.5 ×2 |
| 보안 / 생물 / 화학 |  | 자동 Opus fallback |

## 사전 알림 (cost critical — CLAUDE.md § 7-11)

단발 호출 예상 비용 ≥ $5 → 사용자 승인 필요:
```text
[MYTHOS COST ALERT]
예상 입력 토큰: 50,000 → $0.50
예상 출력 토큰: 80,000 → $4.00
총 예상: $4.50
승인하시겠습니까? (y/n)
```

≥ $5 시 무조건 사용자 승인. Zero-touch 예외 (cost = critical 5 중 하나).

## Fall back 자동 동작

| 조건 | fall back |
|---|---|
| quota 초과 | Opus 4.8 |
| 일일 fable 20% cap | Opus 4.8 + 사용자 알림 (cost critical) |
| 일일 budget 초과 | 모든 호출 차단 (CLAUDE.md § 3.3) |
| 보안/생물/화학 키워드 | Opus 4.8 (Anthropic 자동) |
| Fable 5 API fail | Opus 4.8 + 재시도 (지수 backoff) |

## 참조

- `~/.claude/projects/C--pjt-orchestration-v1/memory/project_fable_5_usage_strategy.md` (전체 전략)
- `~/.claude/projects/C--pjt-orchestration-v1/memory/reference_fable_5_launch.md` (사실)
- CLAUDE.md § 3.2 (Mythos-class 행)
- CLAUDE.md § 3.3 (budget fallback)
- `plugins/exec_orch/skills/route_dispatch.md` (라우팅 매트릭스)
- `plugins/exec_orch/skills/auto-planner.md` § Path 2 (자동 승격)
