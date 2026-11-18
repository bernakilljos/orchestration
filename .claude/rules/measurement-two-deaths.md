---
paths:
  - ".claude/logs/**"
  - ".claude/state/**"
  - "**/*.log"
  - "docs/postmortem/**"
---
# 계측 두 가지 죽음 룰 (Measurement Two Deaths)

> **전문**: `.claude/rules-ref/measurement-two-deaths.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**계측은 세 축을 모두 지켜야 살아있다.** ① 즉시 보고 (시점) ② 파일 append (보존) ③ 증분 비교 (측정 축).
