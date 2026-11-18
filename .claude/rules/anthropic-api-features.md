---
paths:
  - "**/*anthropic*"
  - "**/*llm*"
  - "**/*embedding*"
  - "**/*semantic*"
  - "**/*batch*"
  - "plugins/eval_quality/**"
  - "plugins/ai_rag/**"
  - ".claude/scripts/lookup-rule.py"
  - ".claude/scripts/route.py"
  - ".claude/scripts/lib/router.py"
---
# Anthropic API 신기능 활용 룰

> **전문**: `.claude/rules-ref/anthropic-api-features.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 우리 kit 통합 우선

1. **Prompt cache 1h TTL** — CLAUDE.md 시스템 프롬프트 · 90% 절감 극대화
2. **Files API** — 대량 감사 문서 · 재사용
3. **Citations** — 감사 응답 신뢰도
