# ai_rag — 상세 스펙

## 목표
작업 특성에 맞는 8가지 RAG 패턴 선택·실행.

## 8 패턴 비교

| 패턴 | 복잡도 | 정확도 | 레이턴시 | 추천 용도 |
|---|---|---|---|---|
| Naive | 1 | 낮음 | 빠름 | 간단 FAQ |
| Multimodal | 3 | 높음 | 중간 | 이미지 + 텍스트 혼합 DB |
| HyDE | 2 | 중상 | 중간 | 검색어 모호 |
| Corrective | 3 | 높음 | 느림 | 정확도 최우선 |
| Graph | 4 | 매우 높음 | 느림 | 관계형 지식 |
| Hybrid | 4 | 매우 높음 | 느림 | 엔터프라이즈 |
| Adaptive | 4 | 높음 | 가변 | 복잡 추론 |
| Agentic | 5 | 최고 | 가장 느림 | MCP 도구 필요 |

## 공통 스택 (Brij $0 stack 2026 참조)

- Retrieval: **LlamaIndex**
- Storage/Search: **ChromaDB** (default), **Qdrant** (스케일 시)
- LLM: Claude Sonnet 또는 Ollama (로컬)
- Observability: Phoenix (self-hosted)

## 구현 가이드라인

각 `/rag-*` 커맨드 공통:
- `--dry-run` 지원
- 입력: `source.md|pdf|url`, `--top-k=5`, `--threshold=0.7`
- 출력: `data/ai_rag/<date>/` + JSON 로그
- 캐시: 임베딩 재사용 (비용 절감)

## 참조

- `docs/upgrade-analysis-2026-04-19.md` § 이미지 1·2 (8 RAG Architectures)
- `docs/architecture-patterns.md` § 설계 원칙

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 참조

- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
