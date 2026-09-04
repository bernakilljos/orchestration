#!/usr/bin/env bash
# mcp_queue plugin — 메시지 브로커 체크 (Redis/Kafka/RabbitMQ/SQS)
set -e
echo "[mcp_queue] 브로커 체크:"
[ -n "$REDIS_URL" ] && echo "  [OK] REDIS_URL 설정됨" || echo "  [WARN] REDIS_URL 미설정 (Redis Pub/Sub)"
[ -n "$KAFKA_BROKER" ] && echo "  [OK] KAFKA_BROKER 설정됨" || echo "  [WARN] KAFKA_BROKER 미설정"
[ -n "$RABBITMQ_URL" ] && echo "  [OK] RABBITMQ_URL 설정됨" || echo "  [WARN] RABBITMQ_URL 미설정"
[ -n "$AWS_SQS_URL" ] && echo "  [OK] AWS_SQS_URL 설정됨" || echo "  [WARN] AWS_SQS_URL 미설정"
echo "  권장: 소규모 = Redis Pub/Sub, 대규모 = Kafka"
echo "  로컬 시작: docker run -p 6379:6379 redis"
