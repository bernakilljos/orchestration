# 산출물 신선도 자동 점검 룰 (Artifact Freshness)

> **근거**: 2026-08-18 사용자 지적 — "신기술 업데이트 할 때 문서도 업데이트하고 확인도 해야겠다". Claude Code changelog 는 자동 감지되나 (`.claude/state/changelog-new.md`) 산출물 (pptx·docx·catalog md) 은 사용자가 매번 지적해야 반영. 재발 방지.
> **이유**: 2026 하반기 AI 격변기 — 모델·기술이 소프트웨어 패치처럼 릴리스. 산출물 3주만 안 보면 뒤처짐. `산업_ML_RMS_이식_종합지도.pptx` (7/1) 는 7주 만에 Mem0g·ChatGPT Work·Erdős 등 8개 항목 갭 발생 사례.

## 절대 룰

**SessionStart 마다 주요 산출물 mtime 스캔 → 유통기한 초과 시 systemMessage 알림.** 사용자가 물어봐야 알게 X.

## 유통기한 매트릭스 (SoT)

| 카테고리 | 경로 pattern | 유통기한 | 근거 |
|---|---|---|---|
| **AI 기술 catalog pptx** | `docs/ssj/**/*.pptx`·`docs/AI_*.pptx` | **60일** | AI 격변기, 2달 = 예전 1년치 |
| **AI 기술 catalog md** | `docs/ssj/ai-tech-*.md` | **45일** | 텍스트는 pptx 보다 빠름 |
| **Claude Code 매트릭스** | `CLAUDE.md § 3.2` | **21일** | v2.1.xxx 매주 릴리스 |
| **install 가이드** | `docs/install/README.md` | **30일** | kit 자산 변화 반영 |
| **강의·교재 docx** | `docs/lecture-*.docx` | **90일** | 커리큘럼 단위 |
| **로드맵** | `docs/**/로드맵.md` | **180일** | 분기 단위 |

## 검출 흐름

```bash
# SessionStart hook (매 세션)
python .claude/scripts/artifact-freshness-report.py
# ↓ 초과 시 stdout
# [STALE] docs/ssj/산업_ML_RMS_이식_종합지도.pptx — 47일 (한계 60일 · 13일 남음)
# [OVERDUE] docs/AI_Evolution_Bible_2035.pptx — 78일 (한계 60일 · 18일 초과)
# [WARN] docs/ssj/ai-tech-catalog-50.md — 41일 (한계 45일 · 4일 남음)
```

## 알림 정책 (Zero-touch 크리티컬 5 외)

- **OVERDUE (한계 초과)**: systemMessage 첫 응답 전 노출 · 사용자 결정 유도
- **STALE (한계 임박, 10% 이내)**: 로그만 · 사용자 안 물어보면 침묵
- **FRESH**: 침묵

## 자동 갱신 (사용자 명시 시)

사용자가 "갱신해"·"현행화"·"업데이트" 감지 시:
1. 대상 pptx 의 델타 스크립트 존재 확인 (`update_*.py` · `build_*.py`)
2. 최신 changelog + memory (`reference_ai_tech_gap_*`·`reference_claude_code_changelog_*`) 로부터 새 항목 추출
3. 빌더 편집 (있으면) 또는 python-pptx append (없으면) 실행
4. mtime 갱신 → freshness reset

## 금지

1. **OVERDUE 상태 무시** — 사용자 지적 후 갱신 = 룰 위반 (feedback_official_features_auto_check.md 정합)
2. **유통기한 하드코딩 (각 스크립트마다)** — 이 룰 파일 = SoT
3. **catalog 갱신 후 memory 미등재** — `reference_ai_tech_gap_*` 로 항상 등재
4. **원본 pptx 덮어쓰기 (백업 X)** — `.bak` 필수 (feedback_no_version_suffix.md 정합)
5. **빌더 없이 pptx 재생성 시도** — python-pptx append 방식 (원본 무손상)

## 델타 스크립트 표준 위치

- `docs/update_<name>.py` — python-pptx append (빌더 없는 pptx)
- `docs/ssj/build_<name>.py` — 전체 재빌드 (원본 빌더 있는 경우)
- 실행 후 mtime 갱신 = freshness reset 신호

## 관련

- `.claude/scripts/artifact-freshness-report.py` — 스캔 로직
- `.claude/hooks/detect-artifact-staleness.sh` — SessionStart 발동
- `feedback_official_features_auto_check.md` — Claude Code changelog 자동 반영 (정합)
- `reference_ai_tech_gap_2026_08.md` — 첫 갭 리포트 실사례
- `feedback_verify_before_report.md` — 갱신 후 검증 의무
