# bundles_cowork — 업무 자동화 번들 — 이메일·영수증·슬라이드·제안서·계약·브리핑

> **Prefix**: `bundles_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2
> **출처**: https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies 'Claude Cowork Essentials')

## ⚠️ 현재 상태

**spec-only** — 스펙 + 공통 헬퍼만. 실구현은 install 후 플랫폼에서.

## 📋 커맨드

- `/bundles_cowork-email` — 이메일 자동 분류·초안·답장 (mcp_collab·Gmail 연계)
- `/bundles_cowork-receipt` — 영수증 스캔·회계 JSON·세금 분류 (mcp_docs·OCR)
- `/bundles_cowork-deck` — 슬라이드 빌드 (design_ppt 연계)
- `/bundles_cowork-proposal` — 제안서 작성 (design_word 연계)
- `/bundles_cowork-plan` — 주간 계획·할 일 (exec_scheduler 연계)
- `/bundles_cowork-contract` — 계약 검토·리스크 (design_pdf·legal 체크)
- `/bundles_cowork-briefing` ⭐ 기본 — 아침 브리핑 드래프트 (Slack·이메일 요약)

## 🧠 스킬

- `skill-cowork-flow` — 여러 플러그인 조합 워크플로우 (체인 패턴)
- `skill-cowork-personal` — 개인 비서 수준 컨텍스트 유지 (name·prefs·history)

## 🔗 의존성

- **플러그인**: `exec_orch`, `design_ppt`, `design_word`, `design_pdf`, `mcp_collab`, `exec_scheduler`
- **공통 헬퍼**: `scripts/common.sh`

## 📝 참조

- 스펙: `SPEC.md`
- 분석: `docs/upgrade-analysis-2026-04-19.md`
