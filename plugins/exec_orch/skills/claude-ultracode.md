---
name: claude-ultracode
description: |
  Claude Code Dynamic Workflows (ultracode) 자동 활용. 초난도 task — codebase-wide bug hunt, profiler-guided optimization, security audit, multi-angle verification — 감지 시 /effort ultracode 라우팅.
  사용자가 "전수조사", "다각 검증", "전체 코드베이스", "버그 헌트", "audit", "프로파일링", "보안 감사" 언급 시 활성화.
---

# claude-ultracode — Dynamic Workflows 자동 라우팅

> **출처**: Claude Code Week 22 (2026-05-25~29), Opus 4.8 출시와 함께 공개.
> **요구**: Claude Code v2.1.154+, Opus 4.8 (xhigh effort 지원 모델만).

## 무엇

`/effort ultracode` 또는 prompt 안 `ultracode` keyword 사용 시 Claude 가 task 를 **여러 sub-workflow 로 자동 분해** → 수십~수백 subagent 병렬 실행 → 독립 검증 → 최종 종합.

## 트리거 (자동 감지)

다음 표현·신호 중 하나라도 입력에 있으면 ultracode 라우팅:

| 신호 | 예시 |
|---|---|
| "전수조사" | 사용자 명시 |
| "다각 검증" | "여러 각도로", "교차 확인" |
| "전체 코드베이스" | "프로젝트 전체", "codebase-wide" |
| "버그 헌트" | "bug hunt", "취약점 모두 찾기" |
| "audit" | "감사", "보안 감사" |
| "프로파일링 + 최적화" | "성능 분석 후 모두 고치기" |
| 3+ 영역 동시 작업 | 여러 부서 데이터 동시 분석 |

## 사용 패턴

### 패턴 1 — 세션 전체 활성
```text
/effort ultracode
# 이후 모든 task 가 dynamic workflow 로 처리
```

### 패턴 2 — 단일 task 만
```text
ultracode 모드로 전체 plugins/ 보안 감사 실행해줘
```
prompt 안에 `ultracode` keyword → 해당 task 만 dynamic workflow.

### 패턴 3 — 일반 작업 복귀
```text
/effort high
```
지수적 비용 폭증 방지 — routine 으로 돌아갈 때 의무.

## 우리 라우팅 정책 연동 (route_dispatch)

```text
IF input.contains(ultracode 신호) AND quota.opus_ok AND budget_ok:
  Opus 4.8 + /effort ultracode
  (자동 subagent 분해, 비용 모니터링 강화)

IF budget.tier > 80%:
  WARN — ultracode 비용 위험. /effort xhigh 로 다운그레이드 제안
```

## 비용·시간 고려

- **토큰 소비**: 일반 대화의 5~50배 가능 (수십 subagent 병렬)
- **시간**: 일반 5분 → ultracode 30~120분
- **품질**: 단순 task 에는 과잉. 정말 다각 검증 필요할 때만.

## 실제 활용 예 (Anthropic 공개)

| 시나리오 | subagent 수 | 결과 |
|---|---|---|
| Codebase-wide bug hunt | ~80 | 누락 보안 패치 12건 |
| Profiler-guided optimization | ~150 | 30개 hot path 자동 fix |
| Security audit | ~50 | OWASP Top 10 전수 + 패치 |

## 우리 솔루션 매핑

| 우리 시스템 | ultracode 와 관계 |
|---|---|
| codex-auto ×4 병렬 | 외부 worker. ultracode 는 Claude 내부 subagent. 둘 다 사용 가능 |
| haiku-auto ×2 검증 | ultracode 가 subagent 로 검증 포함 → haiku 보완 X |
| approval-gate | ultracode 가 위험 명령 생성 시 gate 통과 의무 (정합) |
| budget breaker | ultracode 활성 시 80% threshold 도달 빨라짐 → 모니터링 강화 |

## 금지

1. routine task 에 ultracode 사용 — 비용 폭증
2. `/effort high` 로 복귀 안 하고 세션 지속 — 모든 작업 비싸짐
3. budget 80% 초과 후 ultracode 진행 — breaker 즉시 발동
4. 사용자에게 ultracode 결정 강요 — 신호 기반 자동 판단

## 참조

- 공식: https://code.claude.com/docs/en/workflows
- Anthropic blog Week 22: claude.com/blog/introducing-dynamic-workflows-in-claude-code
- 우리 라우팅: `route_dispatch.md`
- 우리 budget: `.claude/state/orca.db` budget 테이블
- 관련 task-instruction template: `plugins/exec_orch/codex/task-instruction-template.md`
