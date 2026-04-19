# mcp_queue — 상세 스펙 (Phase 2)

## 목표

- 메시지 브로커 MCP — Kafka·RabbitMQ·Redis Pub/Sub·AWS SQS

## 커맨드 스펙

### `/install`

큐 시스템 MCP 설치 (Kafka·RabbitMQ·Redis·SQS)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/topic`

토픽·큐 관리 (생성·삭제·파티션)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/consumer`

컨슈머 그룹 lag·오프셋 모니터링

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/dlq`

DLQ 재처리

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

## 스킬 스펙

### `skill-queue-patterns`

큐 패턴 (fan-out·pub-sub·work-queue·DLQ)

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

## 의존성

- upstream: exec_orch
- 공통 헬퍼: `scripts/common.sh`

## 참조

- `docs/architecture-patterns.md`
- `.claude/rules/file-naming.md`
