# mcp_queue — 메시지 브로커 MCP — Kafka·RabbitMQ·Redis Pub/Sub·AWS SQS

> **Prefix**: `mcp_` | **버전**: 0.1 | **Status**: spec-only (Phase 2 예정) | **현황**: 스펙 정의만 완료

##  현재 상태

**spec-only** — 이 플러그인은 킷에 **스펙만** 있습니다. 실제 구현은 설치 후 플랫폼에서 진행.

공식/커뮤니티 MCP:
-  **Kafka MCP**: 공식 없음 → `kafkajs` (Node) 또는 `kafka-python` 직접 호출
-  **RabbitMQ MCP**: 공식 없음 → `amqplib` (Node) 직접 호출
-  **Redis MCP**: 공식 없음 → `redis` CLI 또는 `ioredis` (Node) 직접 호출
-  **AWS SQS MCP**: 공식 없음 → `aws-sdk` v3 직접 호출

## 📋 커맨드 (예정)

- `/install` — 큐 시스템 선택 설치 (Kafka|RabbitMQ|Redis|SQS)
- `/topic` — 토픽·큐 관리 (생성·삭제·파티션)
- `/consumer` — 컨슈머 그룹 lag·오프셋 모니터링
- `/dlq` — DLQ(Dead Letter Queue) 재처리

## 🧠 스킬 (예정)

- `skill-queue-patterns` — 큐 패턴 아키텍처 (fan-out·pub-sub·work-queue·DLQ)

## 🔗 의존성

- **플러그인**: `exec_orch` (필수)
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env 로드)
- **구현 시 선택**: kafkajs|kafka-python, amqplib, redis-cli, aws-sdk

## 📝 다음 단계

1. 각 큐 시스템별 공식 MCP 출시 감지 (npm registry 모니터)
2. 또는 커뮤니티 MCP 통합 (`github.com/modelcontextprotocol/...`)
3. 스펙 완성 후 Phase 2 진입, 실장 시작

## 상세 스펙

### 스킬 스펙

#### `skill-queue-patterns`

큐 아키텍처 패턴:
- **fan-out**: 1:N 메시지 분배 (Kafka topic, RabbitMQ fanout)
- **pub-sub**: 발행-구독 (Redis channels, RabbitMQ topic exchange)
- **work-queue**: 작업 분산 (FIFO queue pattern)
- **DLQ**: 실패 처리 (재시도·보관·분석)

### MCP 상태 조회 (Phase 계획)

#### Kafka
- **상태**:  공식 MCP 없음
- **대안**: `kafkajs` (Node) 또는 `kafka-python` (Python) 직접 호출
- **MCP 가능성**: 2026년 중 Confluent 또는 커뮤니티 출시 예상

#### RabbitMQ
- **상태**:  공식 MCP 없음
- **대안**: `amqplib` (Node) 또는 `pika` (Python)
- **MCP 가능성**: 낮음 (상용 지원 필요)

#### Redis
- **상태**:  공식 MCP 없음
- **대안**: `redis-cli` 또는 `ioredis` (Node), `redis-py` (Python)
- **MCP 가능성**: Redis 공식 검토 중

#### AWS SQS
- **상태**:  공식 MCP 없음 (AWS SDK로 제공)
- **대안**: `@aws-sdk/client-sqs` (v3) 또는 `boto3` (Python)
- **MCP 가능성**: AWS의 다른 MCP 정책에 따름

### 구현 체크리스트 (플랫폼 설치 후)

- [ ] 멱등성 (재실행 안전)
- [ ] `--dry-run` 옵션 동작
- [ ] 입력 검증 (broker, topic, queue 이름)
- [ ] 에러 복구 (재연결, 타임아웃)
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 관리 (`.env`: KAFKA_HOST, RABBITMQ_URL, REDIS_URL, AWS_ACCESS_KEY_ID 등)
- [ ] JSON 구조화 로그 (타임스탬프, 레벨, 메시지)

### 다음 단계 (Phase 진입 조건)

**Phase 2 진입**:
1. Kafka/RabbitMQ/Redis/SQS 공식 또는 커뮤니티 MCP 1개 이상 출시
2. 또는 각 대안 라이브러리 통합 테스트 완료
3. 스펙 완성도 70% 이상

**Phase 2 구현**:
- 각 브로커별 완전 구현 (멱등성·재시도·로깅)
- 다중 환경 지원 (local, dev, prod)
- 모니터링·알람 통합

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 broker 설정값 입력 |
| 연결 실패 | broker 주소/포트 오류 | `netstat -an \| grep LISTEN` (로컬 포트 확인) |
| Rate limit | 과도한 요청 | 지수백오프 구현 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 확인 |
| 드라이런 실패 | `--dry-run` 미지원 | `is_dry_run "$@"` 헬퍼 추가 |

##  참조

- 로드맵: `docs/2026-04-19/로드맵.md` § Phase 2
- 공식 MCP 레지스트리: `modelcontextprotocol.io`
- `docs/architecture-patterns.md` § 메시지 큐 패턴
- `.claude/rules/skill-design.md` (Anthropic 스킬 표준)
- `.claude/rules/plugin-structure.md`
- Kafka: `kafka.apache.org`, `kafkajs.io`
- RabbitMQ: `rabbitmq.com`
- Redis: `redis.io`
- AWS SQS: `docs.aws.amazon.com`
