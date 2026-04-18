---
description: "Gemini 검증 실행 — 구현 결과 리뷰·보안·품질 체크"
allowed-tools: Bash(where:*), Bash(gemini-a:*)
---

## Context
- gemini-auto 가용: !`where gemini-auto 2>/dev/null && echo YES || echo NO`
- task-instruction: !`type .claude\tasks\task-instruction.md 2>/dev/null | head -20 || echo "(없음)"`
- 완료된 태스크: !`ls .claude/tasks/done/*.md 2>/dev/null | tail -5 || echo "(없음)"`

## Your task

### gemini-auto YES → 워커로 검증
```
start "Gemini-Verifier-1" cmd /c "cd /d %CD% && gemini-auto 2"
```
워커가 `.claude/tasks/` 의 완료 태스크를 자동 검증.

### gemini-auto NO → gemini-a 직접 실행
```
gemini-a --verify
```
task-instruction.md 기준으로 구현 결과 검증.

### 검증 항목 (skill-03-review 기준)
1. 보안 이슈 (OWASP)
2. 코드 품질 (가독성·유지보수성)
3. 성능 문제
4. 누락 기능
5. 개선 권고

### 결과 보고
```
[GEMINI 검증 결과]
MUST:     [반드시 적용]
SHOULD:   [권장]
COULD:    [선택]
SECURITY: [보안 이슈]
```
→ Claude가 최종 채택 여부 결정 (자동 적용 금지)
