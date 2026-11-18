---
paths:
  - ".claude/logs/**"
  - ".claude/state/**"
  - "**/*.log"
  - "docs/postmortem/**"
---
# 환경 의존 결함 룰 (Environment-Dependent Bug)

> **전문**: `.claude/rules-ref/environment-dependent-bug.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**"같은 입력 → 같은 출력" 가정 못 하는 결함 = 환경 의존.** 조작자 행동·환경 상태를 조사 변수에 넣어라.
