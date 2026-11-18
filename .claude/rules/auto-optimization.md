---
paths:
  - ".claude/scripts/*optimiz*"
  - ".claude/scripts/nightly*"
  - ".claude/scripts/weekly*"
  - ".claude/scripts/hook-profile.py"
---
# 자동 최적화 룰 (Auto Optimization)

> **전문**: `.claude/rules-ref/auto-optimization.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**모든 최적화는 자동 hook 또는 스케줄 실행 · 사용자 수동 요청 X.**

## 금지

1. 최적화를 사용자에게 요청 X (Zero-touch)
2. 백업 없이 압축·삭제 X (rollback 가능해야)
3. 실전 산출물 자동 삭제 X (archive 만)
4. hook 실행 시간 무시 X (500ms+ 프로파일 필수)
5. 최적화 실패 → 크리티컬 5 아닌 이상 조용 (Zero-touch)
