---
description: Plan-then-build cycle - Plan 서브에이전트 리서치 → plan.md → 사용자 승인 → 잠긴 build (checkpoints)
allowed-tools: Bash(git:*), Bash(python:*), Read, Edit, Write
---

# /go — Plan-then-build cycle (커뮤니티 표준 2026)

**출처**: WebSearch 2026-09-03 · Effective Claude Code Workflows in 2026 (Medium) · Ayautomate 8 Workflows

## 흐름

1. **Plan 서브에이전트 dispatch** — 사용자 요청을 `Agent(Plan, prompt)` 로 격리 실행
2. **plan.md 생성** — `.claude/state/plans/plan-<slug>.md` 저장 · step-by-step + 영향 파일 + 검증 기준
3. **사용자 승인** — plan.md 요약 → yes/edit/no 받기
4. **잠긴 build** — 승인된 plan 만 실행 · 각 step 완료 시 checkpoint (git commit)
5. **자동 검증** — 최종 step 완료 시 verify-*.py 자동 실행

## 사용

```text
/go 사용자 요구사항 텍스트
```

## 왜 이 명령

- 매 turn 재지시 → 컨텍스트 오염 방지
- 사용자는 plan 만 검토 (구현 세부 X)
- 하루 걸리던 삽질 → 1턴 승인 · 1턴 build

## 관련

- `.claude/rules/subagent-delegation.md`
- `.claude/rules/failure-mode.md` § 전수조사
- WebSearch 룰: `.claude/rules/auto-websearch.md`
