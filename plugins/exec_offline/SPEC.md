# exec_offline — 상세 스펙 (Phase 2)

**출처**: docs/upgrade § 이미지 3 ($0 AI Stack 2026, Brij Kishore Pandey)

## 목표

- 로컬/오프라인 AI 스택 — Ollama·ChromaDB·Phoenix ($0 운영)

## 커맨드 스펙

### `/exec_offline-setup`

로컬 스택 설치 (Ollama + ChromaDB + Phoenix)

- `--dry-run` 지원
- 구조화 로그

### `/exec_offline-model`

로컬 모델 다운로드·실행 (Llama·Gemma·Mistral)

- `--dry-run` 지원
- 구조화 로그

### `/exec_offline-vector`

ChromaDB 로컬 벡터DB 관리

- `--dry-run` 지원
- 구조화 로그

### `/exec_offline-observe`

Phoenix self-hosted 관측 대시보드

- `--dry-run` 지원
- 구조화 로그

### `/exec_offline-route`

API vs 로컬 라우팅 결정 (비용·품질)

- `--dry-run` 지원
- 구조화 로그

## 스킬 스펙

### `skill-local-llm`

Ollama 모델 선택 가이드 (VRAM·품질 매트릭스)

### `skill-cost-zero`

완전 오프라인 파이프라인 설계 (no external API)

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 에러 복구
- [ ] 시크릿 `.env`
- [ ] JSON 로그

## 참조

- 출처: docs/upgrade § 이미지 3 ($0 AI Stack 2026, Brij Kishore Pandey)
- 아키텍처: `docs/architecture-patterns.md`
