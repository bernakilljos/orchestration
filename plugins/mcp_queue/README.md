# mcp_queue — 메시지 브로커 MCP — Kafka·RabbitMQ·Redis Pub/Sub·AWS SQS

> **Prefix**: `mcp_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2

## ⚠️ 현재 상태

**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.

## 📋 커맨드

- `/install` ⭐ 기본 — 큐 시스템 MCP 설치 (Kafka·RabbitMQ·Redis·SQS)
- `/topic` — 토픽·큐 관리 (생성·삭제·파티션)
- `/consumer` — 컨슈머 그룹 lag·오프셋 모니터링
- `/dlq` — DLQ 재처리

## 🧠 스킬

- `skill-queue-patterns` — 큐 패턴 (fan-out·pub-sub·work-queue·DLQ)

## 🔗 의존성

- **플러그인**: `exec_orch`
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env)

## 📝 참조

- 스펙: `SPEC.md`
- 로드맵: `docs/2026-04-19/로드맵.md`
