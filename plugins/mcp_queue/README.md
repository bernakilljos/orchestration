# mcp_queue — 메시지 브로커 MCP — Kafka·RabbitMQ·Redis Pub/Sub·AWS SQS

> **Prefix**: `mcp_` | **버전**: 0.1 | **Status**: spec-only (Phase 2 예정) | **현황**: 스펙 정의만 완료

## ⚠️ 현재 상태

**spec-only** — 이 플러그인은 킷에 **스펙만** 있습니다. 실제 구현은 설치 후 플랫폼에서 진행.

공식/커뮤니티 MCP:
- ❌ **Kafka MCP**: 공식 없음 → `kafkajs` (Node) 또는 `kafka-python` 직접 호출
- ❌ **RabbitMQ MCP**: 공식 없음 → `amqplib` (Node) 직접 호출
- ❌ **Redis MCP**: 공식 없음 → `redis` CLI 또는 `ioredis` (Node) 직접 호출
- ❌ **AWS SQS MCP**: 공식 없음 → `aws-sdk` v3 직접 호출

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

## 📚 참조

- 상세 스펙: `SPEC.md`
- 로드맵: `docs/2026-04-19/로드맵.md` § Phase 2
- 공식 MCP 레지스트리: `modelcontextprotocol.io`
