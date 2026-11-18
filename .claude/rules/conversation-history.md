---
paths:
  - ".claude/scripts/lib/conversation_logger.py"
  - ".claude/hooks/save-*"
  - ".claude/hooks/load-recent-conversations.sh"
---
# 세션 대화 히스토리 DB 룰

> **전문**: `.claude/rules-ref/conversation-history.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**Claude Code 세션 대화 = `orca.db.conversations` · 세션 요약 = `orca.db.session_summary` · 새 세션 시작 시 최근 3 세션 자동 로드.**

## 금지

1. `memory/*.md` 에 세션 대화 자동 등재 X (도메인 자산 오염)
2. `conversations` 에 명시 memory·rule 저장 X (역할 반대)
3. content 8000 chars 이상 저장 시도 X (SQLite 쓰기 부하)
4. PII·시크릿 마스킹 없이 저장 (Retention 정책 확립 후)
