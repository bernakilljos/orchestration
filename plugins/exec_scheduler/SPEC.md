# exec_scheduler — 상세 스펙 (Phase 1)

> **Status**: spec-only — 이 플러그인은 킷에 스펙만 있음. 실구현은 install 후 플랫폼에서.

## 목표

- 크론 잡·워크플로우 스케줄러 (모든 정기 작업의 기반)

## 커맨드 스펙

### `/cron`

크론 잡 등록 (YAML 선언형)

**시그니처 (예정)**:
```
/cron [args] [--flag]
```

### `/workflow`

DAG 워크플로우 정의

**시그니처 (예정)**:
```
/workflow [args] [--flag]
```

### `/run-now`

즉시 실행

**시그니처 (예정)**:
```
/run-now [args] [--flag]
```

### `/status`

실행 중 + 다음 예약

**시그니처 (예정)**:
```
/status [args] [--flag]
```

### `/history`

실행 이력·성공률

**시그니처 (예정)**:
```
/history [args] [--flag]
```

### `/retry-policy`

재시도 정책 (exponential backoff)

**시그니처 (예정)**:
```
/retry-policy [args] [--flag]
```

## 스킬 스펙

### `skill-scheduler-idempotency`

멱등성 보장 — 중복 실행 방지

### `skill-scheduler-distributed`

분산 환경 락 (Redis Redlock)

## 의존성

- **upstream (필수)**: exec_orch

## 구현 가이드라인 (install 후 플랫폼 참조용)

- [ ] 멱등성 보장
- [ ] `--dry-run` 옵션 지원
- [ ] Rate limit 대응 (지수백오프)
- [ ] 에러 복구 (state 파일 기반 재시작)
- [ ] 시크릿 관리 (환경변수·vault)
- [ ] 비용 관측 (토큰·API 호출 로깅)

## 참조

- 로드맵: `docs/2026-04-19/로드맵.md`
- 의존 플러그인: plugins/exec_orch

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
