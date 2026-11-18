---
paths:
  - "docs/ssj/**"
  - "docs/**/*.pptx"
  - "docs/**/*.docx"
  - ".claude/scripts/artifact-freshness*"
  - ".claude/scripts/daily-artifact-refresh*"
---
# 산출물 신선도 자동 점검 룰 (Artifact Freshness)

> **전문**: `.claude/rules-ref/artifact-freshness-check.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**SessionStart 마다 주요 산출물 mtime 스캔 → 유통기한 초과 시 systemMessage 알림.** 사용자가 물어봐야 알게 X.

## 금지

1. **OVERDUE 상태 무시** — 사용자 지적 후 갱신 = 룰 위반 (feedback_official_features_auto_check.md 정합)
2. **유통기한 하드코딩 (각 스크립트마다)** — 이 룰 파일 = SoT
3. **catalog 갱신 후 memory 미등재** — `reference_ai_tech_gap_*` 로 항상 등재
4. **원본 pptx 덮어쓰기 (백업 X)** — `.bak` 필수 (feedback_no_version_suffix.md 정합)
5. **빌더 없이 pptx 재생성 시도** — python-pptx append 방식 (원본 무손상)
