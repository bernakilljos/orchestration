# bundles_cowork — 상세 스펙 (Phase 2)

**출처**: https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies 'Claude Cowork Essentials')

## 목표

- 업무 자동화 번들 — 이메일·영수증·슬라이드·제안서·계약·브리핑

## 커맨드 스펙

### `/bundles_cowork-email`

이메일 자동 분류·초안·답장 (mcp_collab·Gmail 연계)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-receipt`

영수증 스캔·회계 JSON·세금 분류 (mcp_docs·OCR)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-deck`

슬라이드 빌드 (design_ppt 연계)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-proposal`

제안서 작성 (design_word 연계)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-plan`

주간 계획·할 일 (exec_scheduler 연계)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-contract`

계약 검토·리스크 (design_pdf·legal 체크)

- `--dry-run` 지원
- 구조화 로그

### `/bundles_cowork-briefing`

아침 브리핑 드래프트 (Slack·이메일 요약)

- `--dry-run` 지원
- 구조화 로그

## 스킬 스펙

### `skill-cowork-flow`

여러 플러그인 조합 워크플로우 (체인 패턴)

### `skill-cowork-personal`

개인 비서 수준 컨텍스트 유지 (name·prefs·history)

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 에러 복구
- [ ] 시크릿 `.env`
- [ ] JSON 로그

## 참조

- 출처: https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies 'Claude Cowork Essentials')
- 아키텍처: `docs/architecture-patterns.md`
