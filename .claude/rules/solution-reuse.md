---
paths:
  - ".claude/scripts/save_solution.py"
  - ".claude/hooks/save-*"
  - ".claude/hooks/lookup-history.sh"
---
# 해결책 재사용 룰 (Solution Reuse · 양방향 초최고)

> **전문**: `.claude/rules-ref/solution-reuse.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**모든 세션 종료 시 문제·해결·파일·명령 자동 캡처 · 다음 세션 UserPromptSubmit 시 관련 solution 자동 조회 · systemMessage 주입.**

## 금지

1. verified=0 solution 을 자동 적용 X (사용자 확인 필요)
2. reusable_score < 3 자동 재사용 X
3. problem_hash 없이 저장 X (중복 폭주)
4. 개인정보·시크릿 포함 저장 X (마스킹 예정)
5. 대량 저장 후 index 없이 검색 X (성능 저하)
