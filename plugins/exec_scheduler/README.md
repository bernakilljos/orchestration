# exec_scheduler — 크론 잡·워크플로우 스케줄러 (모든 정기 작업의 기반)

> **Status**: spec-only (Phase 1) | **Prefix**: `exec_` | **버전**: 0.1

## ⚠️ 현재 상태

이 플러그인은 **스펙만** 있고 실구현은 없습니다. `install 후 플랫폼`에서 구현.
상세 스펙: [`SPEC.md`](SPEC.md)

## 📋 커맨드 (예정)

- `/cron` — 크론 잡 등록 (YAML 선언형)
- `/workflow` — DAG 워크플로우 정의
- `/run-now` — 즉시 실행
- `/status` — 실행 중 + 다음 예약
- `/history` — 실행 이력·성공률
- `/retry-policy` — 재시도 정책 (exponential backoff)

## 🔗 의존성

- **플러그인**: exec_orch

## 상세 스펙

### 스킬 스펙

#### `skill-scheduler-idempotency`

멱등성 보장 — 중복 실행 방지

#### `skill-scheduler-distributed`

분산 환경 락 (Redis Redlock)

### 구현 가이드라인 (install 후 플랫폼 참조용)

- [ ] 멱등성 보장
- [ ] `--dry-run` 옵션 지원
- [ ] Rate limit 대응 (지수백오프)
- [ ] 에러 복구 (state 파일 기반 재시작)
- [ ] 시크릿 관리 (환경변수·vault)
- [ ] 비용 관측 (토큰·API 호출 로깅)

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 📝 로드맵

- `docs/2026-04-19/로드맵.md` § Phase 1
- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
