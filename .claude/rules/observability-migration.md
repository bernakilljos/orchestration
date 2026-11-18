---
paths:
  - ".claude/scripts/lib/structured_logger.py"
  - ".claude/scripts/lib/trace.py"
---
# Observability + Structured Logging 마이그레이션 가이드

> **전문**: `.claude/rules-ref/observability-migration.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 성능 vs 가독성

**print() 장점**: 즉시 화면에 표시 (버퍼링 X)
**logger.info() 장점**: 구조화 + 필터링 + 추적

→ 단순 디버깅용 한 줄은 print() 유지 가능. 운영 정보는 logger.
